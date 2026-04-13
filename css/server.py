import sys
import os
import json
import tempfile

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests

from flask import Flask, request, Response, send_file, jsonify
try:
    from auth import (login, logout, verify_token, record_action,
                     add_user, remove_user, toggle_user,
                     reset_password, get_dashboard_data)
    AUTH_ENABLED = True
    print("[*] Auth system loaded")
except ImportError:
    AUTH_ENABLED = False
    print("[!] auth.py not found - running without auth")

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GROQ_URL         = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GEMINI_URL       = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

try:
    from config import GROQ_KEYS, GEMINI_KEY
    print(f"[*] Loaded {len(GROQ_KEYS)} Groq key(s)")
except ImportError:
    print("[!] config.py not found!")
    GROQ_KEYS  = []
    GEMINI_KEY = ""

_groq_key_index = 0
_groq_exhausted = set()
_last_reset_day = None

def _get_next_groq_key():
    global _groq_key_index, _groq_exhausted, _last_reset_day
    import datetime
    today = datetime.date.today().isoformat()
    if _last_reset_day != today:
        _groq_exhausted = set()
        _groq_key_index = 0
        _last_reset_day = today
    available = [k for i, k in enumerate(GROQ_KEYS) if i not in _groq_exhausted]
    if not available:
        return None
    key = available[_groq_key_index % len(available)]
    _groq_key_index = (_groq_key_index + 1) % len(available)
    return key

def _mark_key_exhausted(key):
    global _groq_exhausted
    try:
        idx = GROQ_KEYS.index(key)
        _groq_exhausted.add(idx)
        print(f"[!] Key #{idx+1} exhausted.")
    except ValueError:
        pass

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

SYSTEM_PROMPT = """Speech annotation AI - DesicrewAI Spoken English Assessment (Jan 2026).

YOU ARE AN ANNOTATOR, NOT A TRANSLATOR. NEVER CONVERT ENGLISH TO HINDI.

GOLDEN RULE: Whisper gives you English words. If it is a real English word pronounced recognisably, KEEP IN ENGLISH.

ALWAYS KEEP IN ENGLISH: a, an, the, I, you, he, she, it, we, they, me, him, her, us, them, my, his, its, our, their, is, are, was, were, be, been, have, has, had, do, does, did, will, would, shall, should, may, might, can, could, must, and, or, but, so, if, as, at, by, for, from, in, into, of, on, out, to, up, with, about, after, before, through, this, that, these, those, here, there, what, which, who, when, where, why, how, today, take, safety, piston, use, post, allow, keep, your, hands, go, get, give, come, make, know, think, see, look, want, find, tell, ask, say, said, went, came, told, work, help, good, great, new, old, long, time, day, year, people, way, man, woman, child, world, life, hand, place, home, water, name, word

CORE PRINCIPLES:
1. Transcribe the WHOLE audio as heard including words not in reference text.
2. Accent variations tolerated if word is still recognisable as English.
3. UK, US, Indian English all valid.
4. Correct pronunciation means keep reference word. Incorrect means transcribe as heard.

3 DECISIONS:
D1 KEEP ENGLISH (90%+ of words): Real English word + recognisable pronunciation.
D2 SUBSTITUTE ENGLISH (rare): Mispronunciation sounds like a DIFFERENT English word. colon heard as kuh-lr means colour. man heard as main means main.
D3 DEVANAGARI (only 4 cases): a) Proper noun always Devanagari. b) Mispronunciation sounds like NO English word. c) Non-English sound. d) Special: filler, mumble, letter-spelling, stretched word.

RULES:
g) PROPER NOUNS always Devanagari: Karthik means kartik, England means inglend, Mumbai means mumbai
e) SUB-LEXICAL PAUSES: evaluate each part independently.
f) SUB-LEXICAL STRETCH: full word in Devanagari + ONE extra vowel. coming as co..ming.. means kaamingaa
h) FALSE STARTS / REPETITIONS: transcribe verbatim.
i) PUNCTUATION WITHIN WORDS: include as heard.
c) INSERTED WORDS: English if valid word, else Devanagari.
d) LETTER NAMES: LN tag per letter, content in Devanagari. A=E, B=BI, C=SI, D=DI, E=I, F=EF, G=JI, H=ECH, I=AI, J=JE, K=KE, L=EL, M=EM, N=EN, O=O, P=PI, Q=KYU, R=AAR, S=ES, T=TI, U=YU, V=VI, W=DABLU, X=EX, Y=VAI, Z=ZED

5 TAGS (all need open and close):
MB: completely unintelligible. Use empty MB tags.
NOISE: background noise. Only noise gets empty NOISE tags. Speech with noise gets word inside NOISE tags.
LN: letter-by-letter spelling. One tag per letter. Content in Devanagari.
FIL: ONLY genuine hesitation sounds NOT the article a or pronoun I. uh/uhh=FIL a FIL. um/umm=FIL am FIL. hmm=FIL hm FIL.
SIL: silence more than 2 seconds. Must include exact timestamps. Each SIL is its own annotation entry.

DEVANAGARI: a=a aa=aa i=i ee=ii u=u oo=uu e=e ai=ai o=o au=au. k=k kh=kh g=g ch=ch j=j t=t th=th d=d n=n T=T D=D p=p ph=ph b=b m=m r=r l=l v=v sh=sh s=s h=h y=y. Abrupt end uses halant. Nasal uses anusvara.

OUTPUT FORMAT - ONLY valid JSON no markdown:
{"transcript":"full annotated transcript","annotations":[{"original":"whisper word","annotated":"English OR Devanagari OR TAG","start":"0:00:00.000000","end":"0:00:00.000000","rule":"D1-English/D2-SubstituteEnglish/D3-Devanagari/ProperNoun/FIL/MB/NOISE/SIL/LN"}],"explanation":"2-3 sentences","annotic_json":{"file_name":"filename.wav","annotations":[{"start":"0:00:00.000000","end":"0:00:00.000000","Transcription":["annotated word"]}]}}

SELF-CHECK every word:
1. Genuine hesitation sound NOT article a or pronoun I? Use FIL tag.
2. Completely unintelligible? Use MB tag.
3. Background noise? Use NOISE tag.
4. Silence more than 2s? Use SIL tag with exact timestamps.
5. Letters being spelled out? Use LN tag per letter.
6. Proper noun person place animal? Use Devanagari.
7. Stretched syllables? Full word Devanagari plus extra vowel.
8. False start or stutter? Verbatim.
9. Intra-word pause? Evaluate each part independently.
10. REAL ENGLISH WORD? KEEP IN ENGLISH. DO NOT CONVERT.
11. Mispronunciation equals different English word? Write that word.
12. Nothing matched? Write in Devanagari.

Step 10 covers 90% of words. YOU ARE AN ANNOTATOR NOT A TRANSLATOR."""


# ── Auth helper ──
def get_token():
    auth = request.headers.get('Authorization','')
    if auth.startswith('Bearer '):
        return auth[7:]
    return request.cookies.get('annoto_token','')

def require_auth():
    if not AUTH_ENABLED:
        return None
    token = get_token()
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return None

def require_admin():
    if not AUTH_ENABLED:
        return None
    token = get_token()
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user.get('role') != 'admin':
        return jsonify({"error": "Admin access required"}), 403
    return None

# ── Auth routes ──
@app.route('/login', methods=['GET','POST','OPTIONS'])
def login_route():
    if request.method == 'GET':
        return send_file(os.path.join(BASE_DIR, 'login.html'))
    if request.method == 'OPTIONS':
        return jsonify({"status":"ok"})
    data = request.get_json()
    result = login(data.get('username',''), data.get('password',''))
    return jsonify(result)

@app.route('/logout', methods=['POST','OPTIONS'])
def logout_route():
    if request.method == 'OPTIONS':
        return jsonify({"status":"ok"})
    data  = request.get_json()
    token = data.get('token','') or get_token()
    if AUTH_ENABLED:
        logout(token)
    return jsonify({"status":"ok"})

@app.route('/verify-token', methods=['POST','OPTIONS'])
def verify_token_route():
    if request.method == 'OPTIONS':
        return jsonify({"status":"ok"})
    data  = request.get_json()
    token = data.get('token','')
    if not AUTH_ENABLED:
        return jsonify({"valid": True, "role": "admin"})
    user = verify_token(token)
    if user:
        return jsonify({"valid": True, "role": user.get('role','student'), "name": user.get('name','')})
    return jsonify({"valid": False})

@app.route('/admin', methods=['GET'])
def admin_route():
    return send_file(os.path.join(BASE_DIR, 'admin.html'))

@app.route('/admin/dashboard')
def admin_dashboard():
    err = require_admin()
    if err: return err
    return jsonify(get_dashboard_data())

@app.route('/admin/add-user', methods=['POST','OPTIONS'])
def admin_add_user():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"})
    err = require_admin()
    if err: return err
    data = request.get_json()
    result = add_user(data.get('username',''), data.get('password',''),
                      data.get('name',''), data.get('role','student'))
    return jsonify(result)

@app.route('/admin/remove-user', methods=['POST','OPTIONS'])
def admin_remove_user():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"})
    err = require_admin()
    if err: return err
    data = request.get_json()
    return jsonify(remove_user(data.get('username','')))

@app.route('/admin/toggle-user', methods=['POST','OPTIONS'])
def admin_toggle_user():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"})
    err = require_admin()
    if err: return err
    data = request.get_json()
    return jsonify(toggle_user(data.get('username',''), data.get('active', True)))

@app.route('/admin/reset-password', methods=['POST','OPTIONS'])
def admin_reset_password():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"})
    err = require_admin()
    if err: return err
    data = request.get_json()
    return jsonify(reset_password(data.get('username',''), data.get('new_password','')))

@app.route('/tool')
def tool_route():
    if AUTH_ENABLED:
        token = get_token()
        if not verify_token(token):
            return send_file(os.path.join(BASE_DIR, 'login.html'))
    return send_file(os.path.join(BASE_DIR, 'annotation_tool.html'))

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'annotation_tool.html'))

@app.route('/view')
def view():
    return send_file(os.path.join(BASE_DIR, 'view_annotations.html'))

@app.route('/check')
def check():
    return jsonify({"status": "ok", "keys": len(GROQ_KEYS)})

@app.route('/set-key', methods=['POST', 'OPTIONS'])
def set_key():
    return jsonify({"status": "ok"})

@app.route('/test-keys')
def test_keys():
    results = []
    for i, key in enumerate(GROQ_KEYS):
        masked = key[:8] + "..." + key[-4:]
        try:
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "user", "content": "Say OK"}],
                      "max_tokens": 5},
                timeout=15
            )
            if resp.status_code == 200:   status = "WORKING"
            elif resp.status_code == 429: status = "RATE LIMITED"
            elif resp.status_code == 401: status = "INVALID KEY"
            else:                         status = f"ERROR {resp.status_code}"
        except Exception as e:
            status = f"FAILED: {str(e)[:50]}"
        results.append({"key_number": i+1, "key_masked": masked, "status": status})
    working = sum(1 for r in results if "WORKING" in r["status"])
    return jsonify({
        "summary": {"total_keys": len(GROQ_KEYS), "working": working,
                    "daily_capacity": f"{working*100000:,} tokens/day"},
        "keys": results
    })

@app.route('/transcribe', methods=['POST', 'OPTIONS'])
def transcribe():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"})
        file     = request.files['audio']
        filename = file.filename or 'audio.wav'
        ext      = os.path.splitext(filename)[1] or '.wav'
        tmp      = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tempfile.gettempdir())
        file.save(tmp.name)
        tmp.close()
        result = run_groq_whisper(tmp.name, filename)
        try: os.unlink(tmp.name)
        except: pass
        # Record action
        if AUTH_ENABLED:
            record_action(get_token(), 'transcription')
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/transcribe-url', methods=['POST', 'OPTIONS'])
def transcribe_url():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    try:
        body = request.get_json()
        url  = body.get('url', '')
        resp = requests.get(url, timeout=60, stream=True)
        if resp.status_code != 200:
            return jsonify({"error": f"Could not download: {resp.status_code}"})
        ext = '.mp3' if 'mp3' in url else '.wav'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tempfile.gettempdir())
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()
        filename = url.split('/')[-1].split('?')[0] or 'audio.wav'
        result   = run_groq_whisper(tmp.name, filename)
        try: os.unlink(tmp.name)
        except: pass
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/annotate', methods=['POST', 'OPTIONS'])
def annotate():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    try:
        payload = request.get_json()
        result  = call_groq_annotate(payload)
        # Record action
        if AUTH_ENABLED and result.get('status') == 'ok':
            record_action(get_token(), 'annotation')
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


def run_groq_whisper(audio_path, original_filename):
    print(f"[*] Transcribing: {original_filename}")
    key = _get_next_groq_key()
    if not key:
        return {"error": "No Groq API keys available."}

    file_size = os.path.getsize(audio_path)
    if file_size > 25 * 1024 * 1024:
        return {"error": "Audio too large. Max 25MB."}

    ext       = os.path.splitext(original_filename)[1].lower() or '.wav'
    mime_map  = {'.wav':'audio/wav','.mp3':'audio/mpeg','.mp4':'audio/mp4',
                 '.m4a':'audio/mp4','.ogg':'audio/ogg','.flac':'audio/flac','.webm':'audio/webm'}
    mime_type = mime_map.get(ext, 'audio/wav')

    def do_request(k):
        with open(audio_path, 'rb') as f:
            return requests.post(
                GROQ_WHISPER_URL,
                headers={"Authorization": f"Bearer {k}"},
                files={"file": (original_filename, f, mime_type)},
                data={"model": "whisper-large-v3", "response_format": "verbose_json",
                      "timestamp_granularities[]": "word", "language": "en", "temperature": "0"},
                timeout=300
            )

    try:
        resp = do_request(key)
        if resp.status_code == 429:
            _mark_key_exhausted(key)
            key2 = _get_next_groq_key()
            if key2:
                resp = do_request(key2)
            else:
                return {"error": "All keys rate limited."}

        if resp.status_code != 200:
            return {"error": f"Groq Whisper Error {resp.status_code}: {resp.text[:300]}"}

        result          = resp.json()
        full_transcript = result.get("text", "").strip()
        raw_words       = result.get("words", [])

        def fmt(secs):
            secs = max(0.0, float(secs))
            h = int(secs // 3600); m = int((secs % 3600) // 60); s = int(secs % 60)
            us = int(round((secs - int(secs)) * 1_000_000))
            return f"{h}:{m:02d}:{s:02d}.{us:06d}"

        def classify(word):
            w = word.lower().strip(".,!?()")
            fillers = {'uh','uhh','uhhh','um','umm','ummm','ah','ahh','aah','aaah',
                       'hmm','hm','hmmm','eh','ehh','er','erm','haan','han','oh','ohh','mm','mmm'}
            if w in fillers: return 'LIKELY_FILLER'
            if any('\u0900' <= c <= '\u097F' for c in word): return 'LIKELY_DEVANAGARI'
            if len(w) > 3 and sum(1 for c in w if c in 'aeiou') == 0: return 'LIKELY_MB'
            safe = {'the','a','an','i','in','on','at','to','of','is','was','are','were','and','or','but'}
            if word and word[0].isupper() and w not in safe: return 'LIKELY_PROPER_NOUN'
            return 'NORMAL'

        words = []
        for w in raw_words:
            word = w.get("word","").strip()
            if not word: continue
            start = float(w.get("start", 0)); end = float(w.get("end", 0))
            words.append({"word": word, "start": fmt(start), "end": fmt(end),
                          "start_seconds": round(start,6), "end_seconds": round(end,6),
                          "hint": classify(word), "is_english": True})

        silence_gaps = []
        for i in range(len(words)-1):
            gap = words[i+1]["start_seconds"] - words[i]["end_seconds"]
            if gap > 2.0:
                silence_gaps.append({"after_word": words[i]["word"], "before_word": words[i+1]["word"],
                                     "gap_seconds": round(gap,6), "sil_start": words[i]["end"],
                                     "sil_end": words[i+1]["start"]})

        leading_silence = None
        if words and words[0]["start_seconds"] > 2.0:
            leading_silence = {"gap_seconds": round(words[0]["start_seconds"],6),
                               "sil_start": fmt(0), "sil_end": words[0]["start"], "type": "leading"}
            silence_gaps.insert(0, leading_silence)

        print(f"[*] Done! {len(words)} words")
        return {"status": "ok", "result": {
            "audio_file": original_filename, "full_transcript": full_transcript,
            "words": words, "silence_gaps": silence_gaps,
            "leading_silence": leading_silence, "sublex_pauses": [], "hint_summary": {}
        }}
    except Exception as e:
        return {"error": f"Transcription failed: {str(e)}"}


def call_groq_annotate(payload):
    ref        = payload.get("reference","")
    words      = payload.get("words",[])
    transcript = payload.get("transcript","")
    filename   = payload.get("filename","audio.wav")
    silence_gaps = payload.get("silence_gaps",[])

    words_fmt = "\n".join([
        f'"{w["word"]}" [{w["start"]} -> {w["end"]}] HINT:{w.get("hint","NORMAL")}'
        for w in words
    ])

    def to_secs(t):
        try:
            p = t.split(":"); return int(p[0])*3600 + int(p[1])*60 + float(p[2])
        except: return 0

    if not silence_gaps:
        for i in range(len(words)-1):
            gap = to_secs(words[i+1]["start"]) - to_secs(words[i]["end"])
            if gap > 2.0:
                silence_gaps.append({"after_word": words[i]["word"], "before_word": words[i+1]["word"],
                                     "gap_seconds": round(gap,2), "sil_start": words[i]["end"],
                                     "sil_end": words[i+1]["start"]})

    silence_notes = "\n".join([
        f"[SIL] {s.get('gap_seconds',0)}s between '{s.get('after_word','')}' and '{s.get('before_word','')}' | START:{s.get('sil_start','')} END:{s.get('sil_end','')}"
        for s in silence_gaps
    ]) or "None"

    optional = ""
    fw = [w["word"] for w in words if w.get("hint")=="LIKELY_FILLER"]
    pw = [w["word"] for w in words if w.get("hint")=="LIKELY_PROPER_NOUN"]
    if fw: optional += f"FILLERS: {', '.join(fw)}\n"
    if pw: optional += f"PROPER NOUNS: {', '.join(pw)}\n"

    user_msg = (
        f"File: {filename}\nReference: {ref or 'Not provided'}\nWords: {len(words)}\n\n"
        f"SILENCES:\n{silence_notes}\n\n{optional}"
        f"WORDS:\n{words_fmt}\n\nTranscript: {transcript}\n\n"
        f"Keep ALL real English words in English. JSON only. Annotate ALL {len(words)} words."
    )

    print(f"[*] Annotating {len(words)} words...")
    attempted = set()

    while True:
        key = _get_next_groq_key()
        if key is None or key in attempted:
            if GEMINI_KEY:
                return call_gemini_annotate(user_msg)
            return {"error": "All Groq keys exhausted."}
        attempted.add(key)

        try:
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile",
                      "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                   {"role": "user",   "content": user_msg}],
                      "max_tokens": 32000, "temperature": 0.0},
                timeout=180
            )
            if resp.status_code == 429:
                _mark_key_exhausted(key); continue
            if resp.status_code != 200:
                return {"error": f"Groq Error {resp.status_code}: {resp.text[:300]}"}
            raw = resp.json()["choices"][0]["message"]["content"]
            return parse_ai_response(raw)
        except Exception as e:
            return {"error": str(e)}

def call_gemini_annotate(user_msg):
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": SYSTEM_PROMPT+"\n\n"+user_msg}]}],
                  "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8000}},
            timeout=180
        )
        if resp.status_code != 200:
            return {"error": f"Gemini Error {resp.status_code}"}
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return parse_ai_response(raw)
    except Exception as e:
        return {"error": f"Gemini error: {str(e)}"}

def parse_ai_response(raw):
    import re, random
    cleaned = raw.replace("```json","").replace("```","").strip()
    for attempt in [
        lambda: json.loads(cleaned),
        lambda: json.loads(re.search(r'\{[\s\S]*\}', cleaned).group()),
        lambda: json.loads(re.sub(r',\s*([}\]])', r'\1', cleaned)),
    ]:
        try:
            parsed = attempt()
            if "annotic_json" in parsed:
                parsed["annotic_json"]["id"] = random.randint(10000,99999)
            print(f"[*] Done! {len(parsed.get('annotations',[]))} annotations")
            return {"status": "ok", "result": parsed}
        except: pass
    return {"error": "Could not parse AI response", "raw": raw[:300]}


if __name__ == '__main__':
    import threading, webbrowser, time

    PORT = int(os.environ.get("PORT", 7842))

    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{PORT}')

    print("=" * 55)
    print("  AnnotoAI — Full Pipeline")
    print("=" * 55)
    print(f"  URL    : http://localhost:{PORT}")
    print(f"  Keys   : {len(GROQ_KEYS)} Groq key(s) loaded")
    print(f"  Whisper: Groq API (fast, online)")
    print(f"  Auth   : {'Enabled' if AUTH_ENABLED else 'Disabled'}")
    print()
    print("  ✓ English words stay English")
    print("  ✓ Key rotation + Gemini fallback")
    print("  ✓ Login system + Admin dashboard")
    print()
    print("  DO NOT CLOSE THIS WINDOW!")
    print("=" * 55)

    threading.Thread(target=open_browser, daemon=True).start()

    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', PORT, app)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped!")

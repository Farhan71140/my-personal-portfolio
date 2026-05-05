/* ==============================
   PORTFOLIO - UPGRADED main.js
   Particles · Cursor · Typewriter
   Counters · Loader · Scroll FX
============================== */

// ── LOADER ──────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  if (!loader) return;
  setTimeout(() => {
    loader.classList.add('hidden');
    document.body.style.overflow = '';
    startCounters();
  }, 1500);
});
document.body.style.overflow = 'hidden';

// ── CUSTOM CURSOR ────────────────────────────────────────────────────────────
const cursor      = document.getElementById('cursor');
const cursorTrail = document.getElementById('cursor-trail');

if (cursor && cursorTrail && window.matchMedia('(pointer: fine)').matches) {
  let trailX = 0, trailY = 0;
  let cursorX = 0, cursorY = 0;

  document.addEventListener('mousemove', e => {
    cursorX = e.clientX;
    cursorY = e.clientY;
    cursor.style.left = cursorX + 'px';
    cursor.style.top  = cursorY + 'px';
  });

  // Smooth trail
  const animateTrail = () => {
    trailX += (cursorX - trailX) * 0.15;
    trailY += (cursorY - trailY) * 0.15;
    cursorTrail.style.left = trailX + 'px';
    cursorTrail.style.top  = trailY + 'px';
    requestAnimationFrame(animateTrail);
  };
  animateTrail();

  // Scale on interactive elements
  const interactables = document.querySelectorAll('a, button, .skill-card, .project-card, .cert-card, .ftag');
  interactables.forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.width  = '18px';
      cursor.style.height = '18px';
      cursorTrail.style.width  = '55px';
      cursorTrail.style.height = '55px';
      cursorTrail.style.borderColor = 'rgba(224,64,251,0.6)';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.width  = '10px';
      cursor.style.height = '10px';
      cursorTrail.style.width  = '36px';
      cursorTrail.style.height = '36px';
      cursorTrail.style.borderColor = 'rgba(255,107,53,0.5)';
    });
  });
}

// ── PARTICLES ────────────────────────────────────────────────────────────────
const canvas = document.getElementById('particles-canvas');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let W = canvas.width  = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  const COLORS = ['rgba(255,107,53,', 'rgba(224,64,251,', 'rgba(124,77,255,', 'rgba(0,229,255,'];
  const NUM = Math.min(80, Math.floor((W * H) / 18000));

  class Particle {
    constructor() { this.reset(true); }
    reset(init) {
      this.x  = Math.random() * W;
      this.y  = init ? Math.random() * H : H + 10;
      this.r  = Math.random() * 1.5 + 0.5;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = -(Math.random() * 0.5 + 0.2);
      this.alpha = Math.random() * 0.5 + 0.2;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.life = 0;
      this.maxLife = Math.random() * 200 + 100;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.life++;
      if (this.life > this.maxLife || this.y < -10) this.reset(false);
    }
    draw() {
      const fade = Math.min(1, Math.min(this.life / 30, (this.maxLife - this.life) / 30));
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = this.color + (this.alpha * fade) + ')';
      ctx.fill();
    }
  }

  const particles = Array.from({ length: NUM }, () => new Particle());

  // Connect nearby particles
  const connect = () => {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(255,107,53,${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  };

  const animParticles = () => {
    ctx.clearRect(0, 0, W, H);
    connect();
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animParticles);
  };
  animParticles();
}

// ── NAVBAR ────────────────────────────────────────────────────────────────────
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 60) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // Close mobile menu
    navLinks.classList.remove('open');
    hamburger.classList.remove('active');
  });
});

// Hamburger
const hamburger = document.getElementById('hamburger');
const navLinks  = document.querySelector('.nav-links');
hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('open');
  hamburger.classList.toggle('active');
});

// Active link highlight
const sections = document.querySelectorAll('section[id], div[id]');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 120)
      current = section.getAttribute('id');
  });
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === `#${current}`) link.classList.add('active');
  });
});

// ── TYPEWRITER ────────────────────────────────────────────────────────────────
const roleEl = document.querySelector('.hero-role');
if (roleEl) {
  const roles = [
    'Python Full-Stack Developer',
    'FastAPI & Django Expert',
    'ML & AI Engineer',
    'Backend Systems Builder',
  ];
  let roleIdx = 0, charIdx = 0, deleting = false;
  const cursor2 = document.createElement('span');
  cursor2.className = 'typewriter-cursor';
  roleEl.textContent = '';
  roleEl.appendChild(cursor2);

  const type = () => {
    const current = roles[roleIdx];
    if (!deleting) {
      roleEl.firstChild.textContent = current.substring(0, charIdx + 1);
      charIdx++;
      if (charIdx === current.length) { deleting = true; setTimeout(type, 2200); return; }
      setTimeout(type, 80);
    } else {
      roleEl.firstChild.textContent = current.substring(0, charIdx - 1);
      charIdx--;
      if (charIdx === 0) { deleting = false; roleIdx = (roleIdx + 1) % roles.length; }
      setTimeout(type, 45);
    }
  };
  // Need to insert text node before cursor
  const textNode = document.createTextNode('');
  roleEl.insertBefore(textNode, cursor2);
  roleEl.firstChild.textContent = '';
  setTimeout(type, 1800);
}

// ── COUNTER ANIMATION ─────────────────────────────────────────────────────────
function startCounters() {
  const statEls = document.querySelectorAll('.stat-num');
  statEls.forEach(el => {
    const raw    = el.textContent.trim();
    const suffix = raw.replace(/[\d.]/g, '');
    const num    = parseFloat(raw);
    if (isNaN(num)) return;
    let start = 0;
    const duration = 2000;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed  = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3);
      const current  = start + (num - start) * eased;
      el.textContent = (Number.isInteger(num) ? Math.floor(current) : current.toFixed(0)) + suffix;
      if (progress < 1) requestAnimationFrame(animate);
      else el.textContent = raw;
    };
    requestAnimationFrame(animate);
  });
}

// ── SCROLL REVEAL ──────────────────────────────────────────────────────────────
const revealEls = document.querySelectorAll('.skill-card, .project-card, .cert-card, .section-header, .contact-wrapper');
revealEls.forEach(el => el.classList.add('reveal'));

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 70);
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.08 });

revealEls.forEach(el => revealObserver.observe(el));

// ── SKILL BAR ANIMATION ───────────────────────────────────────────────────────
const skillFills = document.querySelectorAll('.skill-fill');
const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const target = entry.target.getAttribute('data-width');
      setTimeout(() => { entry.target.style.width = target; }, 200);
      skillObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });

skillFills.forEach(fill => {
  const w = fill.style.width;
  fill.setAttribute('data-width', w);
  fill.style.width = '0';
  skillObserver.observe(fill);
});

// ── CARD MAGNETIC HOVER ───────────────────────────────────────────────────────
if (window.matchMedia('(pointer: fine)').matches) {
  document.querySelectorAll('.project-card, .cert-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect   = card.getBoundingClientRect();
      const x      = ((e.clientX - rect.left) / rect.width  - 0.5) * 8;
      const y      = ((e.clientY - rect.top)  / rect.height - 0.5) * 8;
      card.style.transform = `translateY(-7px) rotateX(${-y}deg) rotateY(${x}deg)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.transition = 'all 0.5s cubic-bezier(0.4,0,0.2,1)';
    });
    card.addEventListener('mouseenter', () => {
      card.style.transition = 'border-color 0.4s, box-shadow 0.4s';
    });
  });
}

// ── CONTACT FORM ─────────────────────────────────────────────────────────────
const form      = document.getElementById('contactForm');
const statusMsg = document.getElementById('form-status');

if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

    const templateParams = {
      from_name:  form.querySelector('[name="name"]').value.trim(),
      from_email: form.querySelector('[name="email"]').value.trim(),
      message:    form.querySelector('[name="message"]').value.trim(),
      to_email:   'mohdfarhanuddin002@gmail.com',
      reply_to:   form.querySelector('[name="email"]').value.trim(),
      time:       timeStr,
    };

    btn.textContent = 'Sending…';
    btn.disabled    = true;
    statusMsg.textContent = '';

    emailjs.send('ycpa svjm ylvc sfck', 'template_cntfagb', templateParams)
      .then(() => {
        btn.textContent      = 'Message Sent ✓';
        btn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
        statusMsg.textContent = "Thanks! I'll get back to you soon.";
        statusMsg.style.color = '#22c55e';
        btn.disabled = false;
        form.reset();
        setTimeout(() => {
          btn.textContent       = 'Send Message';
          btn.style.background  = '';
          statusMsg.textContent = '';
        }, 4000);
      })
      .catch((err) => {
        const code = err?.status || err?.text || JSON.stringify(err);
        statusMsg.textContent = `Failed to send (${code}). Please email me directly.`;
        statusMsg.style.color = '#ef4444';
        btn.textContent      = 'Failed — Try Again';
        btn.style.background = 'linear-gradient(135deg, #ef4444, #b91c1c)';
        btn.disabled         = false;
        setTimeout(() => {
          btn.textContent       = 'Send Message';
          btn.style.background  = '';
          statusMsg.textContent = '';
        }, 5000);
      });
  });
}

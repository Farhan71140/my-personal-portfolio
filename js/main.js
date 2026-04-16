// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.style.background = window.scrollY > 50
    ? 'rgba(8,8,16,0.98)'
    : 'rgba(8,8,16,0.85)';
});

// Smooth scroll for nav links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// Hamburger menu
const hamburger = document.getElementById('hamburger');
const navLinks  = document.querySelector('.nav-links');
hamburger.addEventListener('click', () => {
  const open = navLinks.style.display === 'flex';
  Object.assign(navLinks.style, {
    display:         open ? 'none' : 'flex',
    flexDirection:   'column',
    position:        'absolute',
    top:             '60px',
    left:            '0',
    right:           '0',
    background:      'rgba(8,8,16,0.98)',
    padding:         '1rem 2rem',
    borderBottom:    '1px solid #1e1e2e',
  });
});

// Scroll reveal animation
const revealElements = document.querySelectorAll('.skill-card, .project-card, .cert-card');
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.style.opacity   = '1';
        entry.target.style.transform = 'translateY(0)';
      }, i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

revealElements.forEach(el => {
  el.style.opacity    = '0';
  el.style.transform  = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// Contact form — EmailJS
const form       = document.getElementById('contactForm');
const statusMsg  = document.getElementById('form-status');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = form.querySelector('button[type="submit"]');

  btn.textContent = 'Sending...';
  btn.disabled    = true;
  statusMsg.textContent = '';
  statusMsg.style.color = 'var(--muted)';

  // ── IMPORTANT ──────────────────────────────────────────────────────────────
  // Make sure these three values match your EmailJS dashboard exactly:
  //   Service ID  → https://dashboard.emailjs.com/admin
  //   Template ID → https://dashboard.emailjs.com/admin/templates
  //   Public Key  → https://dashboard.emailjs.com/admin/account
  // ───────────────────────────────────────────────────────────────────────────
  emailjs.sendForm('service_gi8d2jb', 'template_cntfagb', form)
    .then(() => {
      btn.textContent       = 'Message Sent! ✓';
      btn.style.background  = 'linear-gradient(135deg, #22c55e, #16a34a)';
      statusMsg.textContent = 'Thanks! I\'ll get back to you soon.';
      statusMsg.style.color = '#22c55e';
      btn.disabled          = false;
      form.reset();
      setTimeout(() => {
        btn.textContent      = 'Send Message';
        btn.style.background = '';
        statusMsg.textContent = '';
      }, 4000);
    })
    .catch((error) => {
      console.error('EmailJS error:', error);

      // Show a user-friendly error with a hint
      const errCode = error?.status || error?.text || JSON.stringify(error);
      statusMsg.textContent = `Failed to send (${errCode}). Please try emailing directly.`;
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

// Active nav link highlight
const sections = document.querySelectorAll('section[id], div[id]');
window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    if (window.scrollY >= section.offsetTop - 100)
      current = section.getAttribute('id');
  });
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.style.color = link.getAttribute('href') === `#${current}` ? '#f97316' : '';
  });
});
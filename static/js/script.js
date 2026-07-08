(function() {
    'use strict';

    // ---- Nav Toggle ----
    const navToggle = document.getElementById('navToggle');
    const nav = document.getElementById('nav');

    if (navToggle && nav) {
        navToggle.addEventListener('click', function() {
            nav.classList.toggle('open');
            this.classList.toggle('active');
        });

        // Close nav on link click (mobile)
        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('open');
                navToggle.classList.remove('active');
            });
        });
    }

    // ---- Header scroll shadow ----
    const header = document.getElementById('header');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        if (currentScroll > 40) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        lastScroll = currentScroll;
    });

    // ---- Active nav link on scroll ----
    const sections = document.querySelectorAll('section[id]');
    const navLinks = nav ? nav.querySelectorAll('a:not([target="_blank"])') : [];

    function updateActiveLink() {
        let current = '';
        const scrollY = window.pageYOffset + 120;

        sections.forEach(section => {
            const offsetTop = section.offsetTop;
            const height = section.offsetHeight;
            if (scrollY >= offsetTop && scrollY < offsetTop + height) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href && href.replace('#', '') === current) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveLink);
    window.addEventListener('load', updateActiveLink);

    // ---- Smooth scroll for nav links ----
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                e.preventDefault();
                targetEl.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // ---- Project card hover tilt ----
    document.querySelectorAll('.project-card').forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            this.style.transform =
                `perspective(600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(600px) rotateX(0) rotateY(0) translateY(0)';
        });
    });

    // ---- Stat counter animation ----
    const statNumbers = document.querySelectorAll('.stat-number');
    let counted = false;

    function animateStats() {
        if (counted) return;
        const heroSection = document.getElementById('hero');
        if (!heroSection) return;
        const rect = heroSection.getBoundingClientRect();
        if (rect.bottom < 0) return;

        statNumbers.forEach(el => {
            const text = el.textContent;
            const num = parseFloat(text);
            if (isNaN(num)) return;
            const suffix = text.replace(/[0-9.]/g, '');
            let current = 0;
            const duration = 1200;
            const stepTime = 20;
            const steps = duration / stepTime;
            const increment = num / steps;
            const timer = setInterval(() => {
                current += increment;
                if (current >= num) {
                    current = num;
                    clearInterval(timer);
                }
                el.textContent = Math.floor(current) + suffix;
            }, stepTime);
        });
        counted = true;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !counted) {
                animateStats();
            }
        });
    }, { threshold: 0.3 });

    const heroSection = document.getElementById('hero');
    if (heroSection) observer.observe(heroSection);

    // ---- Keyboard shortcut: press 'M' to toggle menu ----
    document.addEventListener('keydown', (e) => {
        if (e.key === 'm' || e.key === 'M') {
            if (!e.ctrlKey && !e.altKey && !e.metaKey && navToggle) {
                navToggle.click();
            }
        }
    });

    console.log('🚀 Manish.dev — pipelines that don\'t drop packets.');
})();

// ---- Theme Toggle ----
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    const icon = themeToggle.querySelector('i');

    // Check localStorage for saved theme
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
        icon.className = 'fas fa-sun';
    } else {
        icon.className = 'fas fa-moon';
    }

    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');
        icon.className = isLight ? 'fas fa-sun' : 'fas fa-moon';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });
});

// ---- Contact Form Submission ----
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    if (!form) return;
    const feedback = document.getElementById('formFeedback');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const name = form.querySelector('input[name="name"]').value.trim();
        const email = form.querySelector('input[name="email"]').value.trim();
        const message = form.querySelector('textarea[name="message"]').value.trim();

        if (!name || !email || !message) {
            feedback.textContent = 'Please fill in all fields.';
            feedback.style.color = 'var(--red-warn)';
            return;
        }

        feedback.textContent = 'Sending...';
        feedback.style.color = 'var(--text-secondary)';

        try {
            const response = await fetch('/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, message })
            });

            const result = await response.json();

            if (response.ok) {
                feedback.textContent = result.message || 'Thank you for reaching out!';
                feedback.style.color = 'var(--accent)';
                form.reset();
            } else {
                feedback.textContent = result.message || 'Something went wrong. Please try again.';
                feedback.style.color = 'var(--red-warn)';
            }
        } catch (error) {
            feedback.textContent = 'Error connecting to server. Please try again.';
            feedback.style.color = 'var(--red-warn)';
            console.error('Fetch error:', error);
        }
    });
});
// Scroll‑to‑top button (minimal)
const scrollBtn = document.getElementById('scrollTopBtn');
if (scrollBtn) {
    scrollBtn.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}
// Neshama Website — Minimal Interaction JS
// No frameworks. No animations. Just what's needed.

(function() {
  'use strict';

  // Mobile nav toggle
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', function() {
      links.classList.toggle('open');
    });

    // Close nav when clicking a link on mobile
    links.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        links.classList.remove('open');
      });
    });
  }

  // FAQ toggle (pricing page)
  window.toggleFaq = function(btn) {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    const answer = btn.nextElementSibling;

    btn.setAttribute('aria-expanded', !expanded);
    answer.setAttribute('aria-hidden', expanded);
  };

  // Docs sidebar: highlight active link based on scroll
  if (document.querySelector('.docs-sidebar')) {
    const sections = document.querySelectorAll('.docs-content h2[id]');
    const navLinks = document.querySelectorAll('.docs-nav-group a');

    function updateActiveLink() {
      let current = '';
      sections.forEach(function(section) {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 120) {
          current = section.id;
        }
      });

      navLinks.forEach(function(link) {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
          link.classList.add('active');
        }
      });
    }

    window.addEventListener('scroll', updateActiveLink, { passive: true });
    updateActiveLink();
  }

  // Docs search: filter nav items
  const searchInput = document.getElementById('docs-search');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const query = this.value.toLowerCase().trim();
      const navGroups = document.querySelectorAll('.docs-nav-group');

      navGroups.forEach(function(group) {
        const links = group.querySelectorAll('a');
        let anyVisible = false;

        links.forEach(function(link) {
          const text = link.textContent.toLowerCase();
          if (!query || text.includes(query)) {
            link.style.display = '';
            anyVisible = true;
          } else {
            link.style.display = 'none';
          }
        });

        // Hide group title if no links visible
        const title = group.querySelector('.docs-nav-group__title');
        if (title) {
          title.style.display = anyVisible ? '' : 'none';
        }
      });
    });
  }

})();

/* =========================================================
   Brew's Ko — main.js
   Scroll reveal animation (Intersection Observer) + small UX helpers
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll('.reveal-fade, .reveal-card');

  if ('IntersectionObserver' in window && revealEls.length) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // stagger cards slightly for a nicer cascade effect
          const delay = entry.target.dataset.revealDelay || 0;
          setTimeout(() => entry.target.classList.add('in-view'), delay);
          obs.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      rootMargin: '0px 0px -60px 0px',
      threshold: 0.1,
    });

    revealEls.forEach((el, index) => {
      // small stagger for elements that share a row (product/testimonial cards)
      if (el.classList.contains('reveal-card')) {
        el.dataset.revealDelay = (index % 3) * 80;
      }
      observer.observe(el);
    });
  } else {
    // Fallback: no IntersectionObserver support — just show everything
    revealEls.forEach((el) => el.classList.add('in-view'));
  }

  /* ---------- Auto-dismiss alerts ---------- */
  document.querySelectorAll('.alert').forEach((alert) => {
    setTimeout(() => {
      if (window.bootstrap && bootstrap.Alert) {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
      } else {
        alert.remove();
      }
    }, 4500);
  });

  /* ---------- Smooth scroll for on-page anchors (e.g. #location) ---------- */
  document.querySelectorAll('a[href*="#"]').forEach((link) => {
    link.addEventListener('click', function (e) {
      const url = new URL(this.href, window.location.origin);
      if (url.pathname === window.location.pathname && url.hash) {
        const target = document.querySelector(url.hash);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });

  /* ---------- Quantity stepper on product detail page ---------- */
  const qtyInput = document.getElementById('id_quantity');
  if (qtyInput) {
    qtyInput.setAttribute('inputmode', 'numeric');
  }

});

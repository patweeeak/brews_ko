/* =========================================================
   Brew's Ko — Admin Dashboard JS
   Sidebar toggle + small UX helpers. Chart.js instances are
   initialized inline on each template so they have access to
   the server-rendered JSON context.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Mobile sidebar toggle ---------- */
  const sidebar = document.querySelector('.dash-sidebar');
  const toggleBtn = document.querySelector('.dash-sidebar-toggle');
  const overlay = document.querySelector('.dash-sidebar-overlay');

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    overlay && overlay.classList.add('show');
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    overlay && overlay.classList.remove('show');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      sidebar && sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
    });
  }
  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  /* ---------- Auto-dismiss alerts ---------- */
  document.querySelectorAll('.dash-content .alert').forEach((alert) => {
    setTimeout(() => {
      if (window.bootstrap && bootstrap.Alert) {
        bootstrap.Alert.getOrCreateInstance(alert).close();
      } else {
        alert.remove();
      }
    }, 5000);
  });

  /* ---------- Shared Chart.js color palette (coffee theme) ---------- */
  window.BREWSKO_CHART_COLORS = {
    coffee: '#6F4E37',
    coffeeDark: '#4A3323',
    accent: '#C0785A',
    amber: '#E0A458',
    blue: '#5B8FB9',
    teal: '#4E9E8C',
    green: '#6B8E5A',
    red: '#C0574A',
    beige: '#EDE3D3',
  };

});

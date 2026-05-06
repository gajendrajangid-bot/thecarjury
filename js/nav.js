// The Car Jury — nav behaviour
// Handles active-link marking and hamburger toggle ONLY.
// All nav HTML (links, hamburger button, mobile panel) lives in the page HTML.
// To change nav items: edit agents/carjury/tcj_header.py, then re-generate pages.
(function () {
  var PANEL_ID = 'tcj-mobile-nav';
  var HAM_ID   = 'tcj-hamburger';

  function markActive() {
    var path = location.pathname.replace(/\/$/, '') + '/';
    document.querySelectorAll('#tcj-nav a, #' + PANEL_ID + ' a').forEach(function (a) {
      var href = (a.getAttribute('href') || '').replace(/\/$/, '') + '/';
      if (href === '//' ) return;
      if (path === href || (href !== '//' && path.indexOf(href) === 0)) {
        a.classList.add('active');
      }
    });
  }

  function init() {
    var ham   = document.getElementById(HAM_ID);
    var panel = document.getElementById(PANEL_ID);

    if (ham && panel) {
      ham.addEventListener('click', function () {
        var open = panel.classList.toggle('open');
        ham.setAttribute('aria-expanded', String(open));
      });

      // close on outside click
      document.addEventListener('click', function (e) {
        if (!panel.classList.contains('open')) return;
        if (!panel.contains(e.target) && e.target !== ham && !ham.contains(e.target)) {
          panel.classList.remove('open');
          ham.setAttribute('aria-expanded', 'false');
        }
      });

      // close panel link that has tcj-panel-close class
      var closeBtn = panel.querySelector('.tcj-panel-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function () {
          panel.classList.remove('open');
          ham.setAttribute('aria-expanded', 'false');
        });
      }
    }

    markActive();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());

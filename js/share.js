// The Car Jury — Share buttons: native share + click tracking.
// Click tracking POSTs to the SAME Google Apps Script as feedback.js, using the
// existing schema (vote='share', feedback=<platform>), so shares append to the
// same Feedback sheet exactly like the existing vote='click' rows — no Apps
// Script change needed. Also fires a GA4 'share' event. Best-effort: never
// blocks the actual share action.
(function () {
  'use strict';

  // Same backend as feedback.js. Prefer the page's own data-feedback-endpoint
  // (set on <body> by the generators) so share rows always log to whatever sheet
  // the page is wired to; fall back to the window var, then the shared default.
  var ENDPOINT =
    (document.body && document.body.getAttribute('data-feedback-endpoint')) ||
    window.TCJ_FEEDBACK_ENDPOINT ||
    'https://script.google.com/macros/s/AKfycbyddgIXufUp2fEY8vZjtCyiLGXseB1MPN7tEv41WZ4iIOO2BCDUqUPvFqRBvc76HEkjuA/exec';

  function pagePath() { return window.location.pathname.replace(/\/$/, '') || '/'; }

  function track(platform) {
    // 1) log to the feedback sheet (same backend), fire-and-forget
    try {
      var fd = new FormData();
      fd.append('page', pagePath());
      fd.append('vote', 'share');       // type discriminator (mirrors vote='click')
      fd.append('feedback', platform);  // whatsapp | x | native
      if (navigator.sendBeacon) {
        navigator.sendBeacon(ENDPOINT, fd);
      } else {
        fetch(ENDPOINT, { method: 'POST', body: fd, mode: 'no-cors' }).catch(function () {});
      }
    } catch (e) { /* ignore */ }
    // 2) GA4 share event (shows in reading-insights)
    try {
      if (window.gtag) { gtag('event', 'share', { method: platform, item_id: pagePath() }); }
    } catch (e) { /* ignore */ }
  }

  document.addEventListener('click', function (ev) {
    var el = ev.target.closest ? ev.target.closest('[data-share]') : null;
    if (!el) return;
    var net = el.getAttribute('data-share');
    track(net);
    if (net === 'native') {
      ev.preventDefault();
      var u = window.location.href.split('?')[0];
      if (navigator.share) {
        navigator.share({ title: document.title, url: u }).catch(function () {});
      } else if (navigator.clipboard) {
        // desktop fallback: copy the link
        navigator.clipboard.writeText(u);
        el.setAttribute('aria-label', 'Link copied');
      }
    }
    // WhatsApp / X anchors proceed normally (open in a new tab)
  }, true);
}());

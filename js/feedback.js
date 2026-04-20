// The Car Jury — Floating Feedback Widget
// Backend: Google Apps Script (set FEEDBACK_ENDPOINT in .env)
(function () {
  'use strict';

  var ENDPOINT = window.TCJ_FEEDBACK_ENDPOINT || 'https://script.google.com/macros/s/AKfycbyddgIXufUp2fEY8vZjtCyiLGXseB1MPN7tEv41WZ4iIOO2BCDUqUPvFqRBvc76HEkjuA/exec';

  var page = window.location.pathname.replace(/\/$/, '') || '/';
  var storageKey = 'tcj_vote_' + page;
  if (localStorage.getItem(storageKey)) return;

  var score   = document.body.getAttribute('data-score')   || '';
  var verdict = document.body.getAttribute('data-verdict') || '';
  if (!score || !verdict) return;

  // ── Styles ────────────────────────────────────────────────
  var s = document.createElement('style');
  s.textContent =
    // Desktop: bottom of screen, right edge aligned with article column
    '#tcj-fp{position:fixed;bottom:40px;' +
    'right:max(20px,calc((100vw - 808px) / 2 - 20px));' +
    'z-index:9999;background:#fff;border:1px solid #E5E2DC;border-radius:100px;' +
    'padding:10px 14px;display:flex;align-items:center;gap:8px;' +
    'box-shadow:0 2px 16px rgba(0,0,0,.10);' +
    'font-family:"Inter",-apple-system,sans-serif;font-size:13px;' +
    'transition:opacity .3s,border-radius .2s,padding .2s;}' +

    // Idle state
    '#tcj-fp-idle{display:flex;align-items:center;gap:8px;}' +
    '.tcj-btn-vote{background:none;border:1px solid #E5E2DC;border-radius:6px;' +
    'width:36px;height:36px;cursor:pointer;font-size:18px;line-height:1;' +
    'display:flex;align-items:center;justify-content:center;' +
    'transition:border-color .15s,background .15s;}' +
    '.tcj-btn-vote:hover{border-color:#C8102E;background:#FBE8EB;}' +

    // Expand form state
    '#tcj-fp-form{display:none;flex-direction:column;gap:10px;width:220px;}' +
    '#tcj-fp-label{font-size:12px;font-weight:600;color:#1A1A1A;}' +
    '#tcj-fp-text{width:100%;border:1px solid #E5E2DC;border-radius:6px;' +
    'padding:9px;font-family:inherit;font-size:13px;line-height:1.5;' +
    'resize:none;outline:none;color:#1A1A1A;}' +
    '#tcj-fp-text:focus{border-color:#C8102E;}' +
    '#tcj-fp-text::placeholder{color:#9E9A93;}' +
    '#tcj-fp-btns{display:flex;gap:8px;}' +
    '#tcj-fp-send{flex:1;background:#C8102E;color:#fff;border:none;' +
    'border-radius:6px;padding:8px 14px;font-size:13px;font-weight:500;' +
    'cursor:pointer;font-family:inherit;transition:background .15s;}' +
    '#tcj-fp-send:hover{background:#A30C24;}' +
    '#tcj-fp-skip{background:none;border:1px solid #E5E2DC;border-radius:6px;' +
    'padding:8px 12px;font-size:13px;color:#6B6B6B;cursor:pointer;' +
    'font-family:inherit;transition:border-color .15s;}' +
    '#tcj-fp-skip:hover{border-color:#9E9A93;}' +

    // Done state
    '#tcj-fp-done{display:none;color:#0E6B3C;font-weight:500;font-size:13px;}' +

    // Mobile: small floating pill, bottom-center, overlays content
    '@media(max-width:639px){' +
    '#tcj-fp{bottom:24px;left:50%;right:auto;' +
    'transform:translateX(-50%);' +
    'border-radius:100px;padding:10px 16px;' +
    'box-shadow:0 4px 20px rgba(0,0,0,.18);}' +
    '#tcj-fp.expanded{border-radius:16px;padding:14px 16px;' +
    'transform:translateX(-50%);width:280px;}' +
    '#tcj-fp-form{width:100%;}' +
    '}';
  document.head.appendChild(s);

  // ── DOM ───────────────────────────────────────────────────
  var pill = document.createElement('div');
  pill.id = 'tcj-fp';
  pill.setAttribute('role', 'complementary');
  pill.setAttribute('aria-label', 'Rate this review');
  pill.innerHTML =
    '<div id="tcj-fp-idle">' +
      '<button class="tcj-btn-vote" id="tcj-up" title="Helpful" aria-label="Helpful">\uD83D\uDC4D</button>' +
      '<button class="tcj-btn-vote" id="tcj-dn" title="Not helpful" aria-label="Not helpful">\uD83D\uDC4E</button>' +
    '</div>' +
    '<div id="tcj-fp-form">' +
      '<span id="tcj-fp-label">What could be better?</span>' +
      '<textarea id="tcj-fp-text" rows="3" maxlength="300" placeholder="Optional \u2014 any feedback helps"></textarea>' +
      '<div id="tcj-fp-btns">' +
        '<button id="tcj-fp-send">Send</button>' +
        '<button id="tcj-fp-skip">Skip</button>' +
      '</div>' +
    '</div>' +
    '<span id="tcj-fp-done">Thanks \u2713</span>';
  document.body.appendChild(pill);

  // ── Helpers ───────────────────────────────────────────────
  function sanitize(str) {
    // Strip leading formula chars to prevent spreadsheet formula injection
    return str.replace(/^[=+\-@\t\r]+/, '').slice(0, 500);
  }

  function submit(vote, text) {
    localStorage.setItem(storageKey, vote);
    var fd = new FormData();
    fd.append('page', sanitize(page));
    fd.append('vote', vote === 'up' || vote === 'down' ? vote : 'down');
    fd.append('score', score);
    fd.append('verdict', verdict);
    if (text) fd.append('feedback', sanitize(text));
    fetch(ENDPOINT, { method: 'POST', body: fd, mode: 'no-cors' }).catch(function(e){
      console.warn('[TCJ] feedback submit failed', e);
    });
  }

  function expand() {
    document.getElementById('tcj-fp-idle').style.display = 'none';
    document.getElementById('tcj-fp-form').style.display = 'flex';
    pill.classList.add('expanded');
    pill.style.borderRadius = '12px';
    setTimeout(function(){ document.getElementById('tcj-fp-text').focus(); }, 50);
  }

  function done() {
    document.getElementById('tcj-fp-idle').style.display = 'none';
    document.getElementById('tcj-fp-form').style.display = 'none';
    document.getElementById('tcj-fp-done').style.display = 'inline';
    pill.style.borderRadius = '100px';
    pill.classList.remove('expanded');
    setTimeout(function(){
      pill.style.opacity = '0';
      setTimeout(function(){ pill.remove(); }, 320);
    }, 2000);
  }

  document.getElementById('tcj-up').addEventListener('click', function(){ submit('up',''); done(); });
  document.getElementById('tcj-dn').addEventListener('click', function(){ expand(); });
  document.getElementById('tcj-fp-send').addEventListener('click', function(){
    submit('down', document.getElementById('tcj-fp-text').value.trim()); done();
  });
  document.getElementById('tcj-fp-skip').addEventListener('click', function(){ submit('down',''); done(); });

}());

// The Car Jury — header search widget.
// Lazy-loads /js/search-index.json on first focus, ranks free-text matches,
// renders a dropdown. Enter (or "See all results") goes to /search/?q=...
(function () {
  var INPUT_ID    = 'tcj-search';
  var DROPDOWN_ID = 'tcj-search-results';
  var INDEX_URL   = '/js/search-index.json';
  var MAX_RESULTS = 6;

  var indexCache = null;
  var indexLoading = null;

  function loadIndex() {
    if (indexCache) return Promise.resolve(indexCache);
    if (indexLoading) return indexLoading;
    indexLoading = fetch(INDEX_URL, { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) { indexCache = data || []; return indexCache; })
      .catch(function () { indexCache = []; return indexCache; });
    return indexLoading;
  }

  function normalize(s) {
    return (s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }

  // Synonym map: a typed token also matches any of its aliases.
  var SYNONYMS = {
    'ev': ['electric'], 'electric': ['ev'],
    'suv': ['suv'],
    'auto': ['automatic'], 'automatic': ['auto'],
  };

  // Word-aware match: token matches a haystack word if the token (or any of its
  // synonyms) is a prefix of any word, OR is the whole word. Avoids 'ev'
  // matching 'review'.
  function tokenHits(token, hayWords) {
    var variants = [token].concat(SYNONYMS[token] || []);
    for (var i = 0; i < hayWords.length; i++) {
      for (var v = 0; v < variants.length; v++) {
        if (hayWords[i] === variants[v]) return 2;          // exact word
        if (hayWords[i].indexOf(variants[v]) === 0) return 1; // prefix
      }
    }
    return 0;
  }

  function score(entry, q, tokens) {
    var hayTitle = normalize(entry.title);
    var hayBrand = normalize(entry.brand);
    var hayModels = normalize((entry.models || []).join(' '));
    var titleWords  = hayTitle.split(' ').filter(Boolean);
    var brandWords  = hayBrand.split(' ').filter(Boolean);
    var modelWords  = hayModels.split(' ').filter(Boolean);
    var allWords    = titleWords.concat(brandWords).concat(modelWords);
    if (!allWords.length) return 0;

    // Every token must hit somewhere
    for (var i = 0; i < tokens.length; i++) {
      if (!tokenHits(tokens[i], allWords)) return 0;
    }

    var s = 0;
    if (q && hayTitle.indexOf(q) !== -1) s += 30;
    if (titleWords.length && titleWords[0].indexOf(tokens[0]) === 0) s += 15;
    for (var j = 0; j < tokens.length; j++) {
      var t = tokens[j];
      var inTitle = tokenHits(t, titleWords);
      if (inTitle) { s += inTitle === 2 ? 8 : 6; continue; }
      var inBrand = tokenHits(t, brandWords);
      if (inBrand) { s += 3; continue; }
      s += 1;
    }
    var wantsCompare = q.indexOf(' vs ') !== -1 || tokens.indexOf('vs') !== -1;
    if (wantsCompare && entry.t === 'compare') s += 12;
    if (!wantsCompare && entry.t === 'review')  s += 2;
    return s;
  }

  function rank(index, raw) {
    var q = normalize(raw);
    if (!q) return [];
    var tokens = q.split(' ').filter(Boolean);
    var scored = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], q, tokens);
      if (s > 0) scored.push({ e: index[i], s: s });
    }
    scored.sort(function (a, b) {
      if (b.s !== a.s) return b.s - a.s;
      return (b.e.date || '').localeCompare(a.e.date || '');
    });
    return scored.slice(0, MAX_RESULTS).map(function (r) { return r.e; });
  }

  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, function (c) {
      return ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' })[c];
    });
  }

  function highlightTitle(title, tokens) {
    if (!tokens.length) return escapeHtml(title);
    // Build a regex of tokens (longest first so 'creta' isn't shadowed by 'cre')
    var sorted = tokens.slice().sort(function (a, b) { return b.length - a.length; });
    var re = new RegExp('(' + sorted.map(function (t) {
      return t.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    }).join('|') + ')', 'gi');
    return escapeHtml(title).replace(re, '<mark>$1</mark>');
  }

  function render(results, raw) {
    var dropdown = document.getElementById(DROPDOWN_ID);
    if (!dropdown) return;
    var q = normalize(raw);
    var tokens = q.split(' ').filter(Boolean);

    if (!q) { dropdown.classList.remove('open'); dropdown.innerHTML = ''; return; }

    var html = '';
    if (results.length === 0) {
      html = '<div class="tcj-search-empty">No matches. Press Enter to search anyway.</div>';
    } else {
      html = '<ul class="tcj-search-list">';
      for (var i = 0; i < results.length; i++) {
        var r = results[i];
        var badge = r.t === 'compare' ? 'COMPARE' : 'REVIEW';
        html += '<li><a href="' + escapeHtml(r.url) + '">' +
                '<span class="tcj-search-badge tcj-search-badge--' + r.t + '">' + badge + '</span>' +
                '<span class="tcj-search-title">' + highlightTitle(r.title, tokens) + '</span>' +
                '</a></li>';
      }
      html += '</ul>';
    }
    html += '<a class="tcj-search-all" href="/search/?q=' + encodeURIComponent(raw) + '">' +
            'See all results for &ldquo;' + escapeHtml(raw) + '&rdquo;</a>';
    dropdown.innerHTML = html;
    dropdown.classList.add('open');
  }

  function init() {
    var input = document.getElementById(INPUT_ID);
    if (!input) return;
    var dropdown = document.getElementById(DROPDOWN_ID);

    function update() {
      var v = input.value || '';
      if (!v.trim()) { render([], ''); return; }
      loadIndex().then(function (idx) { render(rank(idx, v), v); });
    }

    input.addEventListener('focus', function () { loadIndex().then(update); });
    input.addEventListener('input', update);

    // Enter submits to results page
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var v = (input.value || '').trim();
        if (v) {
          e.preventDefault();
          location.href = '/search/?q=' + encodeURIComponent(v);
        }
      } else if (e.key === 'Escape') {
        input.blur();
        if (dropdown) { dropdown.classList.remove('open'); dropdown.innerHTML = ''; }
      }
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!dropdown) return;
      if (e.target === input || (dropdown.contains && dropdown.contains(e.target))) return;
      dropdown.classList.remove('open');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());

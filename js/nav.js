// The Car Jury — shared nav widget
// Single source of truth for nav across all pages.
// Add <nav class="site-nav" id="tcj-nav"></nav> as placeholder; this script fills it.
(function () {
  var ITEMS = [
    { label: 'Reviews',   href: '/reviews/' },
    { label: 'Compare',   href: '/compare/' },
    { label: 'The Jury',  href: '/the-jury/' },
    { label: 'About',     href: '/about/' },
  ];

  function buildNav() {
    var nav = document.getElementById('tcj-nav');
    if (!nav) return;
    var path = window.location.pathname.replace(/\/$/, '') + '/';
    nav.innerHTML = ITEMS.map(function (item) {
      var active = path === item.href || (item.href !== '/' && path.indexOf(item.href) === 0);
      return '<a href="' + item.href + '"' + (active ? ' class="active"' : '') + '>' + item.label + '</a>';
    }).join('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildNav);
  } else {
    buildNav();
  }
}());

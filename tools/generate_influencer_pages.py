#!/usr/bin/env python3
"""
Generate /influencers/ index + individual influencer sub-pages from influencers.json
Called by carjury_manager.py and after every new review.
"""

from __future__ import annotations
import json, re
from pathlib import Path
from datetime import date

CARJURY = Path(__file__).parent.parent
INFLUENCERS_JSON = CARJURY / "influencers/influencers.json"
SEGMENTS_JSON    = CARJURY / "tools/segments.json"
TODAY_YEAR = date.today().year


def _load_segments() -> dict:
    if SEGMENTS_JSON.exists():
        return json.loads(SEGMENTS_JSON.read_text())
    return {}


def _jury_scores(segments: dict) -> dict:
    """Return {car_key: {score, verdict}} from segments.json."""
    return segments.get("jury_scores", {})


def _verdict_stats(articles: list[str], scores: dict) -> dict:
    """Return buy/wait/skip counts, avg score, top score + car for an influencer."""
    buy = wait = skip = 0
    total = 0.0
    counted = 0
    top_score = 0.0
    top_car = ""
    for slug in articles:
        s = scores.get(slug, {})
        v = s.get("verdict", "")
        sc = float(s.get("score") or 0)
        if v == "BUY":   buy  += 1
        elif v == "WAIT": wait += 1
        elif v == "SKIP": skip += 1
        if sc:
            total   += sc
            counted += 1
            if sc > top_score:
                top_score = sc
                top_car   = slug
    avg = round(total / counted, 1) if counted else 0.0
    return {"buy": buy, "wait": wait, "skip": skip,
            "avg": avg, "top_score": top_score, "top_car": top_car}

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyddgIXufUp2fEY8vZjtCyiLGXseB1MPN7tEv41WZ4iIOO2BCDUqUPvFqRBvc76HEkjuA/exec"

_YT_SVG = '<svg width="26" height="18" viewBox="0 0 26 18" fill="currentColor"><path d="M25.4 2.8a3.2 3.2 0 0 0-2.3-2.3C21.1 0 13 0 13 0S4.9 0 2.9.5A3.2 3.2 0 0 0 .6 2.8C0 4.8 0 9 0 9s0 4.2.6 6.2a3.2 3.2 0 0 0 2.3 2.3C4.9 18 13 18 13 18s8.1 0 10.1-.5a3.2 3.2 0 0 0 2.3-2.3C26 13.2 26 9 26 9s0-4.2-.6-6.2zM10.4 12.9V5.1L17.1 9l-6.7 3.9z"/></svg>'
_YT_SVG_SM = '<svg width="15" height="11" viewBox="0 0 26 18" fill="currentColor"><path d="M25.4 2.8a3.2 3.2 0 0 0-2.3-2.3C21.1 0 13 0 13 0S4.9 0 2.9.5A3.2 3.2 0 0 0 .6 2.8C0 4.8 0 9 0 9s0 4.2.6 6.2a3.2 3.2 0 0 0 2.3 2.3C4.9 18 13 18 13 18s8.1 0 10.1-.5a3.2 3.2 0 0 0 2.3-2.3C26 13.2 26 9 26 9s0-4.2-.6-6.2zM10.4 12.9V5.1L17.1 9l-6.7 3.9z"/></svg>'

GA4_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0LV8GN0CD5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-0LV8GN0CD5');
</script>"""


def load_influencers() -> list[dict]:
    if not INFLUENCERS_JSON.exists():
        return []
    return json.loads(INFLUENCERS_JSON.read_text())


def article_display(article_slug: str) -> tuple[str, str]:
    """Returns (display title, url) for an article slug like 'tata/sierra'."""
    parts = article_slug.split("/")
    brand = parts[0].capitalize() if parts else ""
    model = " ".join(p.replace("-", " ").title() for p in parts[1:]) if len(parts) > 1 else ""
    display = f"{brand} {model}".strip()
    url = f"/reviews/{article_slug}/"
    page = CARJURY / "reviews" / article_slug / "index.html"
    if page.exists():
        html = page.read_text()
        m = re.search(r'og:title["\s]+content="([^"]+)"', html)
        if m:
            display = re.sub(r"\s*[|—-].*The Car Jury.*$", "", m.group(1)).strip()
    return display, url


# Shared CSS tokens and base styles (used as a string value, not an f-string)
SHARED_CSS = """
    :root {
      --font-display: "Fraunces", "Playfair Display", Georgia, serif;
      --font-body:    "Source Serif 4", "Source Serif Pro", Charter, Georgia, serif;
      --font-ui:      "Inter", -apple-system, "Helvetica Neue", Arial, sans-serif;
      --red:          #C8102E;
      --red-dark:     #A30C24;
      --paper:        #FAF8F5;
      --white:        #FFFFFF;
      --hairline:     #E5E2DC;
      --stone-200:    #D6D2CC;
      --stone-400:    #9E9A93;
      --stone-600:    #6B6B6B;
      --stone-800:    #3D3D3D;
      --ink:          #1A1A1A;
      --green:        #0E6B3C;
      --green-tint:   #E6F2EC;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 16px; }
    body { background: var(--paper); color: var(--ink); font-family: var(--font-ui); -webkit-font-smoothing: antialiased; line-height: 1.7; }
    a { color: var(--red); text-decoration: none; }
    a:hover { color: var(--red-dark); }
    .site-header { background: var(--white); border-bottom: 1px solid var(--hairline); position: sticky; top: 0; z-index: 100; }
    .site-header__inner { max-width: 1100px; margin: 0 auto; padding: 0 32px; height: 64px; display: flex; align-items: center; justify-content: space-between; }
    .tcj-mast { display: inline-flex; align-items: baseline; gap: 6px; text-decoration: none; }
    .tcj-mast__the { font: 700 italic 16px/1 var(--font-display); color: var(--red); letter-spacing: -0.01em; }
    .tcj-mast__name { font: 700 24px/1 var(--font-display); color: var(--ink); letter-spacing: -0.02em; }
    .site-nav { display: flex; align-items: center; gap: 28px; }
    .site-nav a { font: 500 14px/1 var(--font-ui); color: var(--stone-600); transition: color 0.15s; }
    .site-nav a:hover { color: var(--ink); }
    .site-nav a.active { color: var(--ink); font-weight: 600; }
    .wrap { max-width: 900px; margin: 0 auto; padding: 56px 32px 100px; }
    .site-footer { background: var(--white); border-top: 1px solid var(--hairline); padding: 48px 32px; }
    .site-footer__inner { max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
    .site-footer__top { display: flex; align-items: flex-start; justify-content: space-between; gap: 32px; }
    .site-footer__tagline { font: 500 13px/1.5 var(--font-ui); color: var(--stone-600); margin-top: 8px; max-width: 280px; }
    .site-footer__links { display: flex; gap: 24px; flex-wrap: wrap; }
    .site-footer__links a { font: 500 13px/1 var(--font-ui); color: var(--stone-600); }
    .site-footer__links a:hover { color: var(--red); }
    .site-footer__bottom { font: 500 12px/1.5 var(--font-ui); color: var(--stone-400); border-top: 1px solid var(--hairline); padding-top: 24px; }
    @media (max-width: 768px) {
      .site-header__inner { padding: 0 20px; }
      .site-nav a:not(.active) { display: none; }
      .wrap { padding: 32px 20px 80px; }
      .site-footer { padding: 32px 20px; }
      .site-footer__top { flex-direction: column; }
    }
"""

FONTS_LINK = '<link rel="preconnect" href="https://fonts.googleapis.com" />\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />'

SITE_HEADER = """<header class="site-header">
  <div class="site-header__inner">
    <a href="/" class="tcj-mast">
      <span class="tcj-mast__the">The</span>
      <span class="tcj-mast__name">Car Jury</span>
    </a>
    <nav class="site-nav" id="tcj-nav"></nav>
  </div>
</header>"""

NAV_SCRIPT = '<script src="/js/nav.js"></script>'


def site_footer() -> str:
    return f"""<footer class="site-footer">
  <div class="site-footer__inner">
    <div class="site-footer__top">
      <div>
        <a href="/" class="tcj-mast">
          <span class="tcj-mast__the">The</span>
          <span class="tcj-mast__name">Car Jury</span>
        </a>
        <p class="site-footer__tagline">We watch every expert so you don't have to — one clear verdict on every car.</p>
      </div>
      <div class="site-footer__links">
        <a href="/reviews/">Reviews</a>
        <a href="/compare/">Compare</a>
        <a href="/best/">Best Lists</a>
        <a href="/influencers/">Influencers</a>
        <a href="/about/">About</a>
      </div>
    </div>
    <div class="site-footer__bottom">
      © {TODAY_YEAR} The Car Jury · No sponsored reviews · No manufacturer relationships · India's aggregated car reviews
    </div>
  </div>
</footer>"""


def generate_index(influencers: list[dict]) -> str:
    cards = ""
    for inf in influencers:
        article_count = len(inf.get("articles", []))
        yt_handle = inf.get("youtube_handle", "")
        ig_handle = inf.get("instagram_handle", "")
        yt_link = f'<a href="{inf["youtube_url"]}" target="_blank" rel="noopener noreferrer">YouTube @{yt_handle}</a>' if inf.get("youtube_url") else ""
        ig_link = f' &nbsp;·&nbsp; <a href="{inf["instagram_url"]}" target="_blank" rel="noopener noreferrer">Instagram @{ig_handle}</a>' if inf.get("instagram_url") else ""
        cards += f"""
    <a href="/influencers/{inf['slug']}/" class="inf-card">
      <div class="inf-avatar">{inf['name'][0]}</div>
      <div class="inf-body">
        <div class="inf-name">{inf['name']}</div>
        <div class="inf-tagline">{inf['tagline']}</div>
        <div class="inf-links">{yt_link}{ig_link}</div>
        <div class="inf-count">{article_count} review{'s' if article_count != 1 else ''} analysed</div>
      </div>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA4_SNIPPET}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>India's Top Independent Car Reviewers — The Car Jury</title>
  <meta name="description" content="The 5 independent YouTube creators whose reviews The Car Jury synthesises into one verdict. No media outlets. No manufacturer relationships." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "India's Top Independent Car Reviewers — The Car Jury",
    "description": "The independent YouTube creators whose reviews The Car Jury synthesises into one verdict. No media outlets. No manufacturer relationships.",
    "url": "https://www.thecarjury.com/influencers/",
    "publisher": {{"@type": "Organization", "name": "The Car Jury", "url": "https://www.thecarjury.com"}}
  }}
  </script>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  {FONTS_LINK}
  <style>
    {SHARED_CSS}
    .page-title {{ font: 700 40px/1.15 var(--font-display); color: var(--ink); letter-spacing: -0.02em; margin-bottom: 10px; }}
    .page-sub {{ font: 400 17px/1.6 var(--font-body); color: var(--stone-600); margin-bottom: 48px; }}
    .inf-grid {{ display: grid; gap: 16px; }}
    .inf-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 24px; display: flex; gap: 20px; align-items: flex-start; transition: border-color 0.15s; }}
    .inf-card:hover {{ border-color: var(--stone-200); text-decoration: none; }}
    .inf-avatar {{ width: 52px; height: 52px; border-radius: 50%; background: var(--red); color: var(--white); font: 700 22px/1 var(--font-display); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .inf-name {{ font: 700 20px/1.2 var(--font-display); color: var(--ink); margin-bottom: 4px; }}
    .inf-tagline {{ font: 400 14px/1.5 var(--font-ui); color: var(--stone-600); margin-bottom: 10px; }}
    .inf-links {{ font: 500 13px/1 var(--font-ui); margin-bottom: 10px; }}
    .inf-links a {{ color: var(--red); }}
    .inf-count {{ display: inline-block; font: 600 11px/1 var(--font-ui); letter-spacing: 0.08em; text-transform: uppercase; color: var(--green); background: var(--green-tint); padding: 4px 10px; border-radius: 3px; }}
    @media (max-width: 600px) {{
      .inf-card {{ flex-direction: column; gap: 12px; }}
      .page-title {{ font-size: 28px; }}
    }}
  </style>
{NAV_SCRIPT}
</head>
<body>
{SITE_HEADER}
<div class="wrap">
  <h1 class="page-title">The Jury</h1>
  <p class="page-sub">{len(influencers)} independent YouTube creators whose reviews we analyse. No media outlets. No manufacturer relationships.</p>
  <div class="inf-grid">{cards}
  </div>
</div>
{site_footer()}
</body>
</html>"""


def generate_influencer_page(inf: dict, all_influencers: list[dict] | None = None) -> str:  # noqa: C901
    # Verdict counts, scores, and badges are always derived live from segments.json —
    # never stored in influencers.json. Rerunning this script after a verdict change
    # automatically reflects the new verdicts on every influencer page.
    segments  = _load_segments()
    scores    = _jury_scores(segments)
    articles  = inf.get("articles", [])
    article_count = len(articles)
    slug      = inf["slug"]
    name      = inf["name"]
    initial   = name[0].upper()

    # ── Verdict stats ────────────────────────────────────────────────────────
    vstats = _verdict_stats(articles, scores)

    # ── Portrait / avatar ────────────────────────────────────────────────────
    # CSS layering: initial span always rendered behind; img sits on top when loaded.
    # Avoids onerror-in-double-quoted-attribute HTML parsing issues entirely.
    photo_url = inf.get("photo_url", "")
    img_tag = (
        f'<img class="portrait-img" src="{photo_url}" alt="{name}" />'
        if photo_url else ""
    )
    portrait_inner = f'<span class="portrait-init">{initial}</span>{img_tag}'

    # ── Subscriber badge (YouTube only) ──────────────────────────────────────
    sub_count   = inf.get("subscriber_count", "")
    sub_fetched = inf.get("subscribers_fetched", "")
    yt_url      = inf.get("youtube_url", "")
    yt_handle   = inf.get("youtube_handle", "")

    if sub_count and yt_url:
        sub_fetched_str = ""
        if sub_fetched:
            from datetime import datetime
            try:
                d = datetime.strptime(sub_fetched, "%Y-%m-%d")
                sub_fetched_str = d.strftime("%b %-d, %Y")
            except Exception:
                sub_fetched_str = sub_fetched
        sub_badge = f"""<div class="platform-sub">
          <div class="platform-sub__icon yt-icon">{_YT_SVG}</div>
          <div>
            <div class="platform-sub__count">{sub_count}</div>
            <div class="platform-sub__meta">YouTube subscribers{f'<br>Fetched {sub_fetched_str}' if sub_fetched_str else ''}</div>
          </div>
        </div>"""
    else:
        sub_badge = ""

    # ── Watch button ─────────────────────────────────────────────────────────
    yt_btn = ""
    if yt_url:
        handle_display = f"@{yt_handle}" if yt_handle else yt_url
        yt_btn = (
            f'<a href="{yt_url}" class="btn-yt" target="_blank" rel="noopener noreferrer" '
            f"onclick=\"trackClick('{slug}','youtube','{handle_display}')\">"
            f"{_YT_SVG_SM} Watch on YouTube</a>"
        )

    # ── Style + language pills ────────────────────────────────────────────────
    style_pills = "".join(f'<span class="pill pill-style">{t}</span>' for t in inf.get("style_tags", []))
    lang_pills  = "".join(f'<span class="pill pill-lang">&#128483; {l}</span>' for l in inf.get("languages", []))

    # ── Car types ─────────────────────────────────────────────────────────────
    ICONS = {"Electric Vehicles": "⚡", "Premium & Luxury": "🏎", "SUVs & Crossovers": "🚙",
             "Hatchbacks": "🚗", "Indian Market Cars": "🇮🇳"}
    car_types_html = "".join(
        f'<div class="cartype-pill"><span>{ICONS.get(t,"🚘")}</span> {t}</div>'
        for t in inf.get("car_types", [])
    )

    # ── About paragraphs ──────────────────────────────────────────────────────
    about_html = "".join(f"<p>{p}</p>" for p in inf.get("about", []))
    if not about_html:
        about_html = f"<p>{inf.get('tagline','')}</p>"

    # ── Why on the jury ───────────────────────────────────────────────────────
    why_html = inf.get("why", "")

    # ── Bias assessment ───────────────────────────────────────────────────────
    bias = inf.get("bias_assessment", {})
    bias_score  = bias.get("score", "Low")
    bias_badge_cls = "bias-badge-low" if bias_score == "Low" else "bias-badge-med" if bias_score == "Medium" else "bias-badge-high"
    bias_method = bias.get("methodology", "")
    bias_findings_html = "".join(
        f'<div class="bias-finding"><div class="bias-dot"></div>'
        f'<div class="bias-finding__text">{e}</div></div>'
        for e in bias.get("evidence", [])
    )
    bias_date = bias.get("last_assessed", "")

    # ── Articles list — sorted by score desc ─────────────────────────────────
    def sort_key(s):
        return -float(scores.get(s, {}).get("score") or 0)

    sorted_articles = sorted(articles, key=sort_key)
    articles_html = ""
    for s in sorted_articles:
        display, url = article_display(s)
        sc = scores.get(s, {})
        score_val = sc.get("score", "")
        verdict   = sc.get("verdict", "")
        badge = f'<span class="verdict-badge verdict-{verdict.lower()}">{verdict}</span>' if verdict else ""
        score_str = f'<span class="article-score">{score_val}/10</span>' if score_val else ""
        articles_html += (
            f'<a href="{url}" class="article-item">'
            f'<span class="article-name">{display}</span>'
            f'<div class="article-right">{badge}{score_str}'
            f'<span class="article-arrow">&#8594;</span></div></a>\n'
        )

    # ── Sidebar quick stats ───────────────────────────────────────────────────
    since_year = inf.get("reviewing_since", "")
    years_active = f"{TODAY_YEAR - since_year}+" if since_year else ""

    top_car_display = ""
    if vstats["top_car"]:
        disp, _ = article_display(vstats["top_car"])
        top_car_display = disp

    platforms_str = ", ".join(inf.get("platforms", ["YouTube"]))
    langs_str     = ", ".join(inf.get("languages", []))
    focus_str     = (inf.get("style_tags", []) + ["Independent"])[0]

    # ── Other jurors (up to 4, most reviews, excluding self) ─────────────────
    others_html = ""
    if all_influencers:
        others = sorted(
            [x for x in all_influencers if x["slug"] != slug and x.get("articles")],
            key=lambda x: -len(x.get("articles", []))
        )[:4]
        for o in others:
            o_initial = o["name"][0].upper()
            o_photo   = o.get("photo_url", "")
            if o_photo:
                o_avatar = (
                    f'<div class="juror-avatar">'
                    f'<img src="{o_photo}" alt="{o["name"]}" '
                    f'onerror="this.style.display=\'none\';this.parentElement.innerHTML=\'{o_initial}\'" />'
                    f'</div>'
                )
            else:
                o_avatar = f'<div class="juror-avatar">{o_initial}</div>'
            n_reviews = len(o.get("articles", []))
            others_html += (
                f'<a href="/influencers/{o["slug"]}/" class="juror-card">'
                f'{o_avatar}'
                f'<div class="juror-name">{o["name"]}</div>'
                f'<div class="juror-tagline">{o.get("tagline","")[:72]}</div>'
                f'<div class="juror-reviews">{n_reviews} verdict{"s" if n_reviews != 1 else ""} &#8594;</div>'
                f'</a>'
            )

    other_jurors_section = ""
    if others_html:
        other_jurors_section = f"""
  <div class="other-jurors">
    <div class="other-jurors__heading">Meet the rest of The Jury</div>
    <div class="other-jurors__sub">Independent reviewers. One verdict per car.</div>
    <div class="jurors-grid">{others_html}</div>
  </div>"""

    # ── Schema ────────────────────────────────────────────────────────────────
    same_as = f',"sameAs":"{yt_url}"' if yt_url else ""
    schema_image = f',"image":"{photo_url}"' if photo_url else ""

    # ── Click tracking script ─────────────────────────────────────────────────
    click_script = (
        '<script>\n'
        f'var _TCJ_EP="{APPS_SCRIPT_URL}";\n'
        'function trackClick(j,p,h){'
        'var fd=new FormData();fd.append(\'page\',j);fd.append(\'vote\',\'click\');'
        'fd.append(\'score\',\'\');fd.append(\'verdict\',\'\');'
        'fd.append(\'feedback\',p+\'::\'+ h);'
        'fetch(_TCJ_EP,{method:\'POST\',body:fd,mode:\'no-cors\'});}\n'
        '</script>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA4_SNIPPET}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name} — Independent Car Reviewer | The Car Jury</title>
  <meta name="description" content="{name} is one of India's top independent car reviewers. The Car Jury has synthesised their analysis across {article_count} car review{'s' if article_count != 1 else ''}." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/{slug}/" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    "name": "{name} — Independent Car Reviewer | The Car Jury",
    "url": "https://www.thecarjury.com/influencers/{slug}/",
    "mainEntity": {{
      "@type": "Person",
      "name": "{name}",
      "description": "{inf.get('tagline','').replace(chr(34), '')}"
      {same_as}{schema_image}
    }}
  }}
  </script>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  {FONTS_LINK}
  <style>
    {SHARED_CSS}
    :root {{
      --amber: #92400E; --amber-tint: #FEF3C7;
      --blue:  #1D4ED8; --blue-tint:  #EFF6FF;
      --stone-100: #F0EDE8;
    }}
    .wrap {{ max-width: 980px; }}
    .breadcrumb {{ font: 500 12px/1 var(--font-ui); color: var(--stone-400); margin-bottom: 36px; display: flex; gap: 8px; align-items: center; }}
    .breadcrumb a {{ color: var(--stone-600); }} .breadcrumb a:hover {{ color: var(--red); }}
    .breadcrumb__sep {{ color: var(--stone-200); }}

    /* portrait — layered: initial always behind, img floats on top when loaded */
    .profile-hero {{ display: flex; gap: 36px; align-items: flex-start; margin-bottom: 36px; flex-wrap: wrap; }}
    .profile-portrait {{ position: relative; flex-shrink: 0; width: 148px; height: 192px; border-radius: 12px;
      overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,.14); background: var(--red); }}
    .portrait-init {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
      font: 700 56px/1 var(--font-display); color: var(--white); background: var(--red); z-index: 1; }}
    .portrait-img {{ position: absolute; inset: 0; width: 100%; height: 100%;
      object-fit: cover; object-position: 62% 6%; display: block; z-index: 2; }}
    .profile-meta {{ flex: 1; min-width: 0; }}
    .profile-name {{ font: 700 clamp(1.8rem,4vw,2.5rem)/1.1 var(--font-display); color: var(--ink); letter-spacing: -0.025em; margin-bottom: 8px; }}
    .profile-tagline {{ font: 400 italic 15px/1.65 var(--font-body); color: var(--stone-600); margin-bottom: 14px; max-width: 560px; }}

    /* pills */
    .pill-row {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 11px; }}
    .pill {{ font: 600 10px/1 var(--font-ui); letter-spacing: .08em; text-transform: uppercase; padding: 5px 11px; border-radius: 20px; }}
    .pill-style {{ color: var(--stone-600); background: var(--white); border: 1px solid var(--hairline); }}
    .pill-lang  {{ color: var(--blue); background: var(--blue-tint); border: 1px solid #BFDBFE; }}

    /* subscriber badge */
    .platform-subs {{ margin-bottom: 16px; }}
    .platform-sub {{ display: inline-flex; align-items: center; gap: 10px; background: var(--white);
      border: 1px solid var(--hairline); border-radius: 8px; padding: 10px 16px; }}
    .platform-sub__icon {{ flex-shrink: 0; }}
    .yt-icon {{ color: #FF0000; }}
    .platform-sub__count {{ font: 700 18px/1 var(--font-ui); color: var(--ink); letter-spacing: -0.02em; }}
    .platform-sub__meta {{ font: 400 10px/1.4 var(--font-ui); color: var(--stone-400); margin-top: 2px; }}

    /* watch btn */
    .btn-yt {{ display: inline-flex; align-items: center; gap: 7px; padding: 9px 18px; border-radius: 5px;
      font: 600 13px/1 var(--font-ui); background: #C8102E; color: #fff; }}
    .btn-yt:hover {{ background: #a30c24; color: #fff; }}

    /* stats */
    .stat-row {{ display: flex; gap: 12px; margin-bottom: 48px; flex-wrap: wrap; }}
    .stat {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 10px; padding: 18px 22px; text-align: center; flex: 1; min-width: 110px; }}
    .stat-num {{ font: 700 32px/1 var(--font-ui); color: var(--red); letter-spacing: -0.03em; }}
    .stat-label {{ font: 500 10px/1.4 var(--font-ui); letter-spacing: .1em; text-transform: uppercase; color: var(--stone-600); margin-top: 6px; }}
    .stat-note  {{ font: 400 10px/1.3 var(--font-ui); color: var(--stone-400); margin-top: 4px; }}

    /* two-column */
    .content-cols {{ display: grid; grid-template-columns: 1fr 296px; gap: 44px; align-items: start; }}
    @media (max-width: 800px) {{ .content-cols {{ grid-template-columns: 1fr; }} }}

    /* sections */
    .section-block {{ margin-bottom: 46px; }}
    .section-label {{ font: 600 11px/1 var(--font-ui); letter-spacing: .14em; text-transform: uppercase; color: var(--red); margin-bottom: 16px; }}
    .about-body p {{ font: 400 16px/1.78 var(--font-body); color: var(--stone-800); margin-bottom: 14px; }}
    .about-body p:last-child {{ margin-bottom: 0; }}

    /* car types */
    .cartypes-block {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .cartype-pill {{ display: inline-flex; align-items: center; gap: 8px; font: 500 13px/1 var(--font-ui);
      color: var(--ink); background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 10px 16px; }}

    /* jury trust */
    .jury-trust {{ background: var(--green-tint); border-left: 3px solid var(--green); border-radius: 0 8px 8px 0; padding: 20px 24px; }}
    .jury-trust__label {{ font: 700 10px/1 var(--font-ui); letter-spacing: .15em; text-transform: uppercase; color: var(--green); margin-bottom: 10px; }}
    .jury-trust__text  {{ font: 400 15px/1.68 var(--font-body); color: var(--ink); }}

    /* bias card */
    .bias-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 10px; overflow: hidden; }}
    .bias-header {{ display: flex; align-items: center; justify-content: space-between; padding: 18px 22px; border-bottom: 1px solid var(--hairline); flex-wrap: wrap; gap: 12px; }}
    .bias-header__title {{ font: 700 14px/1 var(--font-ui); color: var(--ink); margin-bottom: 4px; }}
    .bias-header__sub   {{ font: 400 12px/1.4 var(--font-ui); color: var(--stone-600); }}
    .bias-badge {{ font: 700 11px/1 var(--font-ui); letter-spacing: .08em; padding: 6px 14px; border-radius: 20px; white-space: nowrap; }}
    .bias-badge-low  {{ background: var(--green-tint); color: var(--green); border: 1px solid #A7D9BF; }}
    .bias-badge-med  {{ background: var(--amber-tint); color: var(--amber); border: 1px solid #FDE68A; }}
    .bias-badge-high {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }}
    .bias-body {{ padding: 20px 22px; display: flex; flex-direction: column; gap: 14px; }}
    .bias-method {{ font: 400 13px/1.6 var(--font-ui); color: var(--stone-600); font-style: italic; padding-bottom: 14px; border-bottom: 1px solid var(--hairline); }}
    .bias-finding {{ display: flex; align-items: flex-start; gap: 10px; }}
    .bias-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--green); flex-shrink: 0; margin-top: 7px; }}
    .bias-finding__text {{ font: 400 13px/1.6 var(--font-ui); color: var(--stone-800); }}
    .bias-footer {{ padding: 11px 22px; border-top: 1px solid var(--hairline); background: var(--stone-100); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
    .bias-footer span {{ font: 400 11px/1.4 var(--font-ui); color: var(--stone-600); }}
    .bias-footer strong {{ font-weight: 600; }}

    /* articles */
    .articles-list {{ display: grid; gap: 8px; }}
    .article-item {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 13px 18px;
      display: flex; justify-content: space-between; align-items: center; gap: 12px; transition: border-color .15s, box-shadow .15s; }}
    .article-item:hover {{ border-color: var(--stone-200); box-shadow: 0 2px 8px rgba(0,0,0,.05); text-decoration: none; }}
    .article-name {{ font: 500 14px/1.3 var(--font-ui); color: var(--ink); }}
    .article-right {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
    .verdict-badge {{ font: 700 10px/1 var(--font-ui); letter-spacing: .1em; padding: 4px 8px; border-radius: 4px; }}
    .verdict-buy  {{ background: var(--green-tint); color: var(--green); }}
    .verdict-wait {{ background: var(--amber-tint); color: var(--amber); }}
    .verdict-skip {{ background: #FEE2E2; color: #B91C1C; }}
    .article-score {{ font: 700 12px/1 var(--font-ui); color: var(--stone-600); }}
    .article-arrow {{ font-size: 14px; color: var(--red); }}

    /* sidebar */
    .sidebar {{ display: flex; flex-direction: column; gap: 18px; }}
    .sidebar-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 10px; padding: 20px; }}
    .sidebar-card__title {{ font: 700 10px/1 var(--font-ui); letter-spacing: .14em; text-transform: uppercase; color: var(--stone-600); margin-bottom: 14px; }}
    .sidebar-row {{ display: flex; justify-content: space-between; align-items: flex-start; padding: 9px 0; border-bottom: 1px solid var(--hairline); gap: 8px; }}
    .sidebar-row:last-child {{ border-bottom: none; padding-bottom: 0; }}
    .sidebar-row__key {{ font: 400 13px/1.3 var(--font-ui); color: var(--stone-600); }}
    .sidebar-row__val {{ font: 600 13px/1.3 var(--font-ui); color: var(--ink); text-align: right; }}
    .sidebar-row__sub {{ font: 400 10px/1.3 var(--font-ui); color: var(--stone-400); text-align: right; margin-top: 2px; }}
    .col-green {{ color: var(--green) !important; }}
    .col-amber {{ color: var(--amber) !important; }}
    .col-red   {{ color: var(--red)   !important; }}

    /* other jurors */
    .other-jurors {{ margin-top: 56px; padding-top: 44px; border-top: 1px solid var(--hairline); }}
    .other-jurors__heading {{ font: 700 1.3rem/1.2 var(--font-display); color: var(--ink); margin-bottom: 6px; }}
    .other-jurors__sub {{ font: 400 14px/1.5 var(--font-ui); color: var(--stone-600); margin-bottom: 22px; }}
    .jurors-grid {{ display: grid; grid-template-columns: repeat(auto-fill,minmax(196px,1fr)); gap: 12px; }}
    .juror-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 10px; padding: 18px;
      display: flex; flex-direction: column; gap: 5px; transition: border-color .15s, box-shadow .15s; }}
    .juror-card:hover {{ border-color: var(--stone-200); box-shadow: 0 2px 8px rgba(0,0,0,.06); text-decoration: none; }}
    .juror-avatar {{ width: 40px; height: 40px; border-radius: 50%; overflow: hidden; background: var(--red); color: var(--white);
      font: 700 16px/1 var(--font-display); display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }}
    .juror-avatar img {{ width: 100%; height: 100%; object-fit: cover; object-position: 50% 5%; display: block; }}
    .juror-name {{ font: 600 14px/1.2 var(--font-ui); color: var(--ink); }}
    .juror-tagline {{ font: 400 11px/1.5 var(--font-ui); color: var(--stone-600); }}
    .juror-reviews {{ font: 600 11px/1 var(--font-ui); color: var(--red); margin-top: 5px; }}

    .back-link {{ margin-top: 40px; font: 500 13px/1 var(--font-ui); }}
    .back-link a {{ color: var(--stone-600); }} .back-link a:hover {{ color: var(--red); }}

    @media (max-width: 768px) {{
      .profile-portrait {{ width: 120px; height: 156px; }}
      .stat-num {{ font-size: 26px; }} .stat {{ padding: 14px 16px; }}
    }}
    @media (max-width: 520px) {{ .profile-hero {{ flex-direction: column; }} }}
  </style>
{NAV_SCRIPT}
</head>
<body>
{SITE_HEADER}
<div class="wrap">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Home</a><span class="breadcrumb__sep">›</span>
    <a href="/influencers/">The Jury</a><span class="breadcrumb__sep">›</span>
    <span>{name}</span>
  </nav>

  <!-- HERO -->
  <div class="profile-hero">
    <div class="profile-portrait">{portrait_inner}</div>
    <div class="profile-meta">
      <div class="profile-name">{name}</div>
      <div class="profile-tagline">{inf.get('tagline','')}</div>
      <div class="pill-row">{style_pills}</div>
      <div class="pill-row">{lang_pills}</div>
      {'<div class="platform-subs">' + sub_badge + '</div>' if sub_badge else ''}
      <div>{yt_btn}</div>
    </div>
  </div>

  <!-- STATS -->
  <div class="stat-row">
    <div class="stat">
      <div class="stat-num">{article_count}</div>
      <div class="stat-label">Verdicts analysed</div>
    </div>
    <div class="stat">
      <div class="stat-num">{years_active or "—"}</div>
      <div class="stat-label">Years reviewing</div>
      {'<div class="stat-note">Active since ' + str(since_year) + '</div>' if since_year else ''}
    </div>
    <div class="stat">
      <div class="stat-num">{vstats['top_score'] or "—"}</div>
      <div class="stat-label">Top jury score</div>
      {'<div class="stat-note">' + top_car_display + '</div>' if top_car_display else ''}
    </div>
    <div class="stat">
      <div class="stat-num">{vstats['avg'] or "—"}</div>
      <div class="stat-label">Avg jury score</div>
      {'<div class="stat-note">Across ' + str(article_count) + ' reviews</div>' if article_count else ''}
    </div>
  </div>

  <!-- MAIN + SIDEBAR -->
  <div class="content-cols">
    <div>

      {'<div class="section-block"><p class="section-label">About this reviewer</p><div class="about-body">' + about_html + '</div></div>' if about_html else ''}

      {'<div class="section-block"><p class="section-label">Car types reviewed</p><div class="cartypes-block">' + car_types_html + '</div></div>' if car_types_html else ''}

      {'<div class="section-block"><p class="section-label">Why on The Jury</p><div class="jury-trust"><div class="jury-trust__label">Our editorial rationale</div><div class="jury-trust__text">' + why_html + '</div></div></div>' if why_html else ''}

      <div class="section-block">
        <p class="section-label">Independence &amp; bias check</p>
        <div class="bias-card">
          <div class="bias-header">
            <div>
              <div class="bias-header__title">Bias risk assessment</div>
              <div class="bias-header__sub">We read comments and analyse engagement across platforms — not declared conflicts alone.</div>
            </div>
            <span class="bias-badge {bias_badge_cls}">{bias_score.upper()} BIAS RISK</span>
          </div>
          <div class="bias-body">
            {'<div class="bias-method">' + bias_method + '</div>' if bias_method else ''}
            <div class="bias-findings">{bias_findings_html}</div>
          </div>
          <div class="bias-footer">
            <span>Based on YouTube comment and engagement analysis. Not a guarantee of independence.</span>
            {'<span><strong>Last assessed:</strong> ' + bias_date + '</span>' if bias_date else ''}
          </div>
        </div>
      </div>

      <div class="section-block">
        <p class="section-label">{article_count} verdict{"s" if article_count != 1 else ""} featuring {name}</p>
        <div class="articles-list">
          {articles_html if articles_html else '<p style="color:var(--stone-400);font-size:14px;padding:16px 0">Reviews coming soon.</p>'}
        </div>
      </div>

    </div>

    <!-- SIDEBAR -->
    <div class="sidebar">
      <div class="sidebar-card">
        <div class="sidebar-card__title">Quick Profile</div>
        <div class="sidebar-row">
          <span class="sidebar-row__key">Platform</span>
          <span class="sidebar-row__val">{platforms_str}</span>
        </div>
        <div class="sidebar-row">
          <span class="sidebar-row__key">Language{'s' if len(inf.get('languages',[])) > 1 else ''}</span>
          <span class="sidebar-row__val">{langs_str}</span>
        </div>
        {'<div class="sidebar-row"><span class="sidebar-row__key">Active since</span><span class="sidebar-row__val">' + str(since_year) + '</span></div>' if since_year else ''}
        {'<div class="sidebar-row"><div><div class="sidebar-row__key">YT subscribers</div><div class="sidebar-row__sub">Fetched ' + (sub_fetched or '') + '</div></div><div class="sidebar-row__val">' + sub_count + '</div></div>' if sub_count else ''}
        <div class="sidebar-row">
          <span class="sidebar-row__key">Focus</span>
          <span class="sidebar-row__val">{focus_str}</span>
        </div>
      </div>

      {'<div class="sidebar-card"><div class="sidebar-card__title">Verdict breakdown</div><div class="sidebar-row"><span class="sidebar-row__key">BUY</span><span class="sidebar-row__val col-green">' + str(vstats["buy"]) + ' of ' + str(article_count) + '</span></div><div class="sidebar-row"><span class="sidebar-row__key">WAIT</span><span class="sidebar-row__val col-amber">' + str(vstats["wait"]) + ' of ' + str(article_count) + '</span></div><div class="sidebar-row"><span class="sidebar-row__key">SKIP</span><span class="sidebar-row__val">' + str(vstats["skip"]) + ' of ' + str(article_count) + '</span></div><div class="sidebar-row"><span class="sidebar-row__key">Avg score</span><span class="sidebar-row__val col-red">' + str(vstats["avg"]) + '/10</span></div>' + ('<div class="sidebar-row"><span class="sidebar-row__key">Top score</span><span class="sidebar-row__val col-red">' + str(vstats["top_score"]) + ' — ' + top_car_display + '</span></div>' if top_car_display else '') + '</div>' if article_count else ''}

      <div class="sidebar-card">
        <div class="sidebar-card__title">Jury standing</div>
        <div class="sidebar-row">
          <span class="sidebar-row__key">Status</span>
          <span class="sidebar-row__val col-green">&#10003; Trusted</span>
        </div>
        <div class="sidebar-row">
          <span class="sidebar-row__key">Bias risk</span>
          <span class="sidebar-row__val col-green">{bias_score}</span>
        </div>
        <div class="sidebar-row">
          <span class="sidebar-row__key">Sponsored</span>
          <span class="sidebar-row__val">None declared</span>
        </div>
      </div>
    </div>
  </div>

  {other_jurors_section}

  <p class="back-link"><a href="/influencers/">&#8592; All Jurors</a></p>
</div>
{site_footer()}
{click_script}
</body>
</html>"""


def _avatar(name: str) -> str:
    """Return 1-2 uppercase initials from a name."""
    words = [w for w in re.split(r"[\s\-]+", name) if w and w[0].isalpha()]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return name[:2].upper()

def _pill(platform: str) -> str:
    cls = {"YouTube": "pill-yt", "Instagram": "pill-ig", "Forum": "pill-mix",
           "Website": "pill-web"}.get(platform, "pill-mix")
    return f'<span class="pill {cls}">{platform}</span>'

def generate_the_jury_page(influencers: list[dict]) -> str:
    # Only show influencers who have actually contributed to at least one article
    sorted_infs = sorted(
        [i for i in influencers if i.get("articles")],
        key=lambda x: -len(x.get("articles", []))
    )
    count = len(sorted_infs)

    cards = ""
    for inf in sorted_infs:
        articles = inf.get("articles", [])
        verdict_n = len(articles)
        name = inf["name"]
        handle = inf.get("youtube_handle", "")
        yt_url = inf.get("youtube_url", "")
        handle_display = f"youtube.com/@{handle}" if handle else ""
        platforms = inf.get("platforms", ["YouTube"])
        pills = "".join(_pill(p) for p in platforms)
        tagline = inf.get("tagline", "Independent car reviewer on YouTube")
        tags = inf.get("style_tags", [])
        tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags[:4])
        slug = inf["slug"]

        cards += f"""
    <a class="creator-card" href="/influencers/{slug}/">
      <div class="card-top">
        <div class="avatar">{_avatar(name)}</div>
        <div class="card-meta">
          <div class="creator-name">{name}</div>
          <div class="creator-handle">{handle_display}</div>
          <div class="platform-pills">{pills}</div>
        </div>
      </div>
      <p class="card-bio">{tagline}</p>
      <div class="card-stats">
        <div class="stat-item"><div class="stat-n">{verdict_n}</div><div class="stat-l">Verdicts used</div></div>
        <div class="stat-item"><div class="stat-n">{platforms[0]}</div><div class="stat-l">Platform</div></div>
        <div class="stat-item"><div class="stat-n">{tags[0] if tags else 'Independent'}</div><div class="stat-l">Focus</div></div>
      </div>
      <div class="card-tags">{tag_html}</div>
      <div class="card-footer">
        <span class="red-dot"></span>
        Contributed to {verdict_n} verdict{'s' if verdict_n != 1 else ''} on The Car Jury
      </div>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Jury Panel | The Car Jury</title>
<meta name="description" content="{count} independent YouTube creators whose reviews The Car Jury synthesises into one verdict. No media outlets. No manufacturer relationships.">
<link rel="canonical" href="https://www.thecarjury.com/the-jury/">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebPage","name":"The Jury Panel | The Car Jury","description":"{count} independent YouTube creators whose reviews The Car Jury synthesises into one verdict. No media outlets. No manufacturer relationships.","url":"https://www.thecarjury.com/the-jury/","publisher":{{"@type":"Organization","name":"The Car Jury","url":"https://www.thecarjury.com"}}}}
</script>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{GA4_SNIPPET}
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;1,400;1,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --red:#C8102E;
  --red-dark:#8B0A1F;
  --red-tint:#FBE8EB;
  --ink:#1A1A1A;
  --stone:#6B6B6B;
  --paper:#FAF8F5;
  --white:#FFFFFF;
  --hairline:#E5E2DC;
  --green:#0E6B3C;
  --green-tint:#E6F2EC;
  --amber:#B8860B;
  --amber-tint:#FBF3DF;
  --fd:'Playfair Display',Georgia,serif;
  --fs:'Source Serif 4',Georgia,serif;
  --fu:'Inter',-apple-system,sans-serif;
}}
body{{font-family:var(--fu);background:var(--paper);color:var(--ink);-webkit-font-smoothing:antialiased}}
.nav{{background:var(--white);border-bottom:1px solid var(--hairline);padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:58px;position:sticky;top:0;z-index:100}}
.mast{{display:flex;align-items:baseline;gap:5px;text-decoration:none}}
.mast-the{{font:700 italic 15px/1 var(--fd);color:var(--red)}}
.mast-name{{font:800 22px/1 var(--fd);color:var(--ink);letter-spacing:-0.02em}}
.nav-links{{display:flex;gap:28px;list-style:none}}
.nav-links a{{font:500 13px/1 var(--fu);color:var(--stone);text-decoration:none;letter-spacing:.01em}}
.nav-links a.active{{color:var(--red)}}
.nav-links a:hover{{color:var(--ink)}}
.breadcrumb{{padding:14px 48px;display:flex;align-items:center;gap:6px;font:400 12px/1 var(--fu);color:var(--stone);border-bottom:1px solid var(--hairline);background:var(--white)}}
.breadcrumb a{{color:var(--stone);text-decoration:none}}
.breadcrumb a:hover{{color:var(--red)}}
.breadcrumb-sep{{color:var(--hairline)}}
.breadcrumb-current{{color:var(--ink)}}
.hero{{background:var(--ink);padding:80px 48px 64px;text-align:center}}
.hero-eyebrow{{font:600 11px/1 var(--fu);color:var(--red);letter-spacing:.14em;text-transform:uppercase;margin-bottom:18px}}
.hero-title{{font:800 54px/1.05 var(--fd);color:var(--white);letter-spacing:-0.025em;margin-bottom:22px}}
.hero-title em{{font-style:italic;color:var(--red)}}
.hero-body{{font:400 18px/1.75 var(--fs);color:rgba(255,255,255,.62);max-width:580px;margin:0 auto 44px}}
.hero-stats{{display:flex;justify-content:center;gap:56px;flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.1);padding-top:40px}}
.hero-stat-n{{font:700 36px/1 var(--fu);color:var(--white)}}
.hero-stat-l{{font:500 12px/1 var(--fu);color:rgba(255,255,255,.4);margin-top:6px;letter-spacing:.02em}}
.page-body{{max-width:1160px;margin:0 auto;padding:52px 48px 96px}}
.section-header{{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:18px;border-bottom:1px solid var(--hairline);margin-bottom:36px}}
.section-label{{font:700 24px/1 var(--fd);color:var(--ink)}}
.section-meta{{font:400 13px/1 var(--fu);color:var(--stone)}}
.living-jury-note{{display:flex;align-items:flex-start;gap:10px;font:400 13px/1.6 var(--fs);color:var(--stone);background:var(--white);border:1px solid var(--hairline);border-left:3px solid var(--red);border-radius:0 6px 6px 0;padding:14px 18px;margin-bottom:28px}}
.creator-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:1px;background:var(--hairline);border:1px solid var(--hairline);border-radius:8px;overflow:hidden;margin-bottom:72px}}
.creator-card{{background:var(--white);padding:32px;transition:background .15s;cursor:pointer;text-decoration:none;color:inherit;display:block}}
.creator-card:hover{{background:var(--paper)}}
.card-top{{display:flex;align-items:flex-start;gap:16px;margin-bottom:18px}}
.avatar{{width:52px;height:52px;border-radius:50%;border:2px solid var(--hairline);background:var(--red-tint);display:flex;align-items:center;justify-content:center;font:700 18px/1 var(--fd);color:var(--red);flex-shrink:0}}
.card-meta{{flex:1}}
.creator-name{{font:700 18px/1.2 var(--fd);color:var(--ink);margin-bottom:3px}}
.creator-handle{{font:400 13px/1 var(--fu);color:var(--stone);margin-bottom:8px}}
.platform-pills{{display:flex;gap:6px;flex-wrap:wrap}}
.pill{{display:inline-flex;align-items:center;font:600 10px/1 var(--fu);letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:3px}}
.pill-yt{{background:#fff0f0;color:#C8102E;border:1px solid #f5d5d8}}
.pill-web{{background:var(--green-tint);color:var(--green);border:1px solid #c3dfc8}}
.pill-mix{{background:var(--paper);color:var(--stone);border:1px solid var(--hairline)}}
.pill-ig{{background:#f0f0ff;color:#5b4de0;border:1px solid #dddaff}}
.card-bio{{font:400 14px/1.7 var(--fs);color:#444;margin-bottom:22px;border-left:2px solid var(--hairline);padding-left:14px}}
.card-stats{{display:grid;grid-template-columns:1fr 1fr 1fr;border-top:1px solid var(--hairline);padding-top:18px;margin-bottom:18px}}
.stat-item{{text-align:center}}
.stat-item+.stat-item{{border-left:1px solid var(--hairline)}}
.stat-n{{font:700 16px/1 var(--fu);color:var(--ink);margin-bottom:4px}}
.stat-l{{font:500 11px/1.3 var(--fu);color:var(--stone)}}
.card-tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px}}
.tag{{font:500 11px/1 var(--fu);padding:4px 10px;border-radius:12px;background:var(--paper);color:var(--stone);border:1px solid var(--hairline)}}
.tag.red{{background:var(--red-tint);color:var(--red);border-color:#f5d5d8}}
.tag.green{{background:var(--green-tint);color:var(--green);border-color:#c3dfc8}}
.tag.amber{{background:var(--amber-tint);color:var(--amber);border-color:#e8d9a0}}
.card-footer{{display:flex;align-items:center;gap:8px;padding-top:14px;border-top:1px solid var(--hairline);font:500 12px/1 var(--fu);color:var(--stone)}}
.red-dot{{width:6px;height:6px;border-radius:50%;background:var(--red);flex-shrink:0}}
.how-section{{background:var(--ink);padding:80px 48px;text-align:center;margin:0 -48px}}
.how-eyebrow{{font:600 11px/1 var(--fu);color:var(--red);letter-spacing:.14em;text-transform:uppercase;margin-bottom:16px}}
.how-title{{font:700 38px/1.1 var(--fd);color:var(--white);margin-bottom:52px;letter-spacing:-0.02em}}
.how-steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:48px;max-width:860px;margin:0 auto}}
.step-num{{width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font:700 15px/1 var(--fu);color:var(--red);margin:0 auto 18px}}
.step-title{{font:700 18px/1.2 var(--fd);color:var(--white);margin-bottom:10px}}
.step-body{{font:400 14px/1.7 var(--fs);color:rgba(255,255,255,.5)}}
.trust-bar{{background:var(--red);padding:22px 48px;display:flex;justify-content:center;gap:36px;flex-wrap:wrap;margin:0 -48px}}
.trust-item{{font:600 13px/1 var(--fu);color:#fff;letter-spacing:.02em;display:inline-flex;align-items:center;gap:6px}}
.trust-item::before{{content:'';display:inline-block;width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.7);flex-shrink:0}}
footer{{background:var(--ink);padding:40px 48px;display:flex;align-items:center;justify-content:space-between;margin:0 -48px}}
.footer-mast{{display:flex;align-items:baseline;gap:5px;text-decoration:none}}
.footer-mast-the{{font:700 italic 13px/1 var(--fd);color:var(--red)}}
.footer-mast-name{{font:800 19px/1 var(--fd);color:var(--white)}}
.footer-note{{font:400 13px/1 var(--fu);color:rgba(255,255,255,.3)}}
@media(max-width:768px){{
  .hero-title{{font-size:38px}}
  .hero-stats{{gap:32px}}
  .how-steps{{grid-template-columns:1fr}}
  .creator-grid{{grid-template-columns:1fr}}
  .page-body{{padding:40px 24px 80px}}
  .breadcrumb{{padding-left:24px;padding-right:24px}}
  .how-section{{margin:0 -24px;padding:60px 24px}}
  .trust-bar{{margin:0 -24px;padding:22px 24px}}
  footer{{margin:0 -24px;padding:32px 24px;flex-direction:column;gap:12px}}
}}
</style>
<script src="/js/nav.js"></script>
</head>
<body>
<header class="site-header"><div class="site-header__inner"><a href="/" class="tcj-mast"><span class="tcj-mast__the">The</span><span class="tcj-mast__name">Car Jury</span></a><nav class="site-nav" id="tcj-nav"></nav></div></header>
<div class="breadcrumb">
  <a href="/">Home</a><span class="breadcrumb-sep">›</span><span class="breadcrumb-current">The Jury Panel</span>
</div>
<section class="hero">
  <div class="hero-eyebrow">The Jury Panel</div>
  <h1 class="hero-title">We don't have one opinion.<br><em>We have {count}.</em></h1>
  <p class="hero-body">Every verdict on The Car Jury is built from multiple independent creators, not one. Because no single reviewer is free of blind spots, preferences, or biases. The more voices we bring together, the closer we get to the truth about a car.</p>
  <div class="hero-stats">
    <div class="hero-stat"><div class="hero-stat-n">{count}</div><div class="hero-stat-l">Jury members</div></div>
    <div class="hero-stat"><div class="hero-stat-n">5M+</div><div class="hero-stat-l">Combined subscribers</div></div>
    <div class="hero-stat"><div class="hero-stat-n">40+</div><div class="hero-stat-l">Cars reviewed collectively</div></div>
    <div class="hero-stat"><div class="hero-stat-n">0</div><div class="hero-stat-l">Sponsored reviews included</div></div>
  </div>
</section>
<div class="page-body">
  <div class="section-header">
    <span class="section-label">Jury members</span>
    <span class="section-meta">{count} independent creators, sorted by verdicts contributed</span>
  </div>
  <div class="living-jury-note">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="flex-shrink:0;margin-top:1px"><circle cx="8" cy="8" r="7" stroke="#C8102E" stroke-width="1.5"/><path d="M8 5v3.5l2.5 1.5" stroke="#C8102E" stroke-width="1.5" stroke-linecap="round"/></svg>
    <span>The jury panel is a living list. We continuously gather feedback, evaluate new voices, and revisit existing ones, so that our verdicts stay balanced, current, and free from over-reliance on any single perspective.</span>
  </div>
  <div class="creator-grid">{cards}
  </div>
  <div class="how-section">
    <div class="how-eyebrow">Our methodology</div>
    <h2 class="how-title">How the jury reaches its verdict</h2>
    <div class="how-steps">
      <div class="step"><div class="step-num">1</div><div class="step-title">We identify the jury</div><p class="step-body">For each car, we identify every independent creator who published a substantive review, excluding press-trip content, brand-commissioned pieces, and spec-sheet summaries.</p></div>
      <div class="step"><div class="step-num">2</div><div class="step-title">We balance across many voices</div><p class="step-body">Each review is read in full and scored across five dimensions. No single reviewer dominates the verdict: scores are weighted by each creator's documented strengths. Where creators disagree, the split is shown, not smoothed over.</p></div>
      <div class="step"><div class="step-num">3</div><div class="step-title">The verdict is rendered</div><p class="step-body">The aggregate findings become the verdict: a score, a Buy, Wait, or Skip recommendation, and the decisive factors a buyer should actually weigh. The jury speaks. You decide.</p></div>
    </div>
  </div>
  <div class="trust-bar">
    <span class="trust-item">No sponsored reviews</span>
    <span class="trust-item">No manufacturer relationships</span>
    <span class="trust-item">Many voices, one verdict</span>
    <span class="trust-item">Splits shown, not hidden</span>
    <span class="trust-item">Methodology published</span>
  </div>
</div>
<footer>
  <a class="footer-mast" href="/"><span class="footer-mast-the">The</span><span class="footer-mast-name">Car Jury</span></a>
  <span class="footer-note">India's aggregated car verdict platform, no sponsored reviews</span>
</footer>
</body>
</html>"""


def build_all(log_fn=print):
    influencers = load_influencers()
    if not influencers:
        log_fn("No influencers.json found — skipping")
        return 0

    index_path = CARJURY / "influencers/index.html"
    index_path.write_text(generate_index(influencers))

    jury_path = CARJURY / "the-jury/index.html"
    jury_path.write_text(generate_the_jury_page(influencers))

    for inf in influencers:
        out_dir = CARJURY / "influencers" / inf["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(generate_influencer_page(inf, all_influencers=influencers))

    log_fn(f"Influencer pages built: {len(influencers)} jurors")
    return len(influencers)


if __name__ == "__main__":
    build_all()
    print("Done.")

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
TODAY_YEAR = date.today().year

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyddgIXufUp2fEY8vZjtCyiLGXseB1MPN7tEv41WZ4iIOO2BCDUqUPvFqRBvc76HEkjuA/exec"

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


def generate_influencer_page(inf: dict) -> str:
    articles = inf.get("articles", [])
    article_count = len(articles)

    articles_html = ""
    for slug in articles:
        display, url = article_display(slug)
        articles_html += f"""
      <a href="{url}" class="article-item">
        <span class="article-name">{display}</span>
        <span class="article-arrow">→</span>
      </a>"""

    slug = inf["slug"]
    yt_btn = (
        f'<a href="{inf["youtube_url"]}" class="btn-yt" target="_blank" rel="noopener noreferrer"'
        f" onclick=\"trackClick('{slug}','youtube','@{inf['youtube_handle']}')\""
        f'>YouTube @{inf["youtube_handle"]}</a>'
    ) if inf.get("youtube_url") else ""
    ig_btn = (
        f'<a href="{inf["instagram_url"]}" class="btn-ig" target="_blank" rel="noopener noreferrer"'
        f" onclick=\"trackClick('{slug}','instagram','@{inf['instagram_handle']}')\""
        f'>Instagram @{inf["instagram_handle"]}</a>'
    ) if inf.get("instagram_url") else ""

    click_script = (
        '<script>\n'
        f'var _TCJ_EP="{APPS_SCRIPT_URL}";\n'
        'function trackClick(j,p,h){'
        'var fd=new FormData();'
        "fd.append('page',j);fd.append('vote','click');"
        "fd.append('score','');fd.append('verdict','');"
        "fd.append('feedback',p+'::'+h);"
        "fetch(_TCJ_EP,{method:'POST',body:fd,mode:'no-cors'});"
        '}\n'
        '</script>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA4_SNIPPET}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{inf['name']} — Independent Car Reviewer | The Car Jury</title>
  <meta name="description" content="{inf['name']} is one of India's top independent car reviewers. The Car Jury has synthesised their analysis across {article_count} car review{'s' if article_count != 1 else ''}." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/{inf['slug']}/" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    "name": "{inf['name']} — Independent Car Reviewer | The Car Jury",
    "url": "https://www.thecarjury.com/influencers/{inf['slug']}/",
    "mainEntity": {{
      "@type": "Person",
      "name": "{inf['name']}",
      "description": "{inf.get('tagline', '')}",
      "url": "https://www.thecarjury.com/influencers/{inf['slug']}/"
    }}
  }}
  </script>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  {FONTS_LINK}
  <style>
    {SHARED_CSS}
    .breadcrumb {{ font: 500 12px/1 var(--font-ui); color: var(--stone-400); margin-bottom: 32px; display: flex; gap: 8px; align-items: center; }}
    .breadcrumb a {{ color: var(--stone-600); }}
    .breadcrumb a:hover {{ color: var(--red); }}
    .breadcrumb__sep {{ color: var(--stone-200); }}
    .profile-header {{ display: flex; gap: 28px; align-items: flex-start; margin-bottom: 40px; flex-wrap: wrap; }}
    .profile-avatar {{ width: 80px; height: 80px; border-radius: 50%; background: var(--red); color: var(--white); font: 700 32px/1 var(--font-display); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .profile-name {{ font: 700 clamp(1.6rem,4vw,2.4rem)/1.15 var(--font-display); color: var(--ink); letter-spacing: -0.02em; margin-bottom: 6px; }}
    .profile-tagline {{ font: 400 15px/1.5 var(--font-body); color: var(--stone-600); margin-bottom: 16px; font-style: italic; }}
    .btn-yt, .btn-ig {{ display: inline-block; padding: 8px 16px; border-radius: 4px; font: 600 13px/1 var(--font-ui); margin-right: 8px; margin-bottom: 8px; }}
    .btn-yt {{ background: #C8102E; color: #fff; }}
    .btn-yt:hover {{ background: #a30c24; color: #fff; }}
    .btn-ig {{ background: var(--ink); color: var(--white); }}
    .btn-ig:hover {{ background: var(--stone-800); color: var(--white); }}
    .stat-row {{ display: flex; gap: 16px; margin-bottom: 48px; flex-wrap: wrap; }}
    .stat {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 20px 28px; text-align: center; }}
    .stat-num {{ font: 700 36px/1 var(--font-ui); color: var(--red); letter-spacing: -0.02em; }}
    .stat-label {{ font: 500 11px/1 var(--font-ui); letter-spacing: 0.1em; text-transform: uppercase; color: var(--stone-600); margin-top: 6px; }}
    .section-label {{ font: 600 11px/1 var(--font-ui); letter-spacing: 0.14em; text-transform: uppercase; color: var(--red); margin-bottom: 16px; }}
    .articles-list {{ display: grid; gap: 10px; }}
    .article-item {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 6px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; transition: border-color 0.15s; }}
    .article-item:hover {{ border-color: var(--stone-200); text-decoration: none; }}
    .article-name {{ font: 500 15px/1.4 var(--font-ui); color: var(--ink); }}
    .article-arrow {{ font: 400 16px/1 var(--font-ui); color: var(--red); flex-shrink: 0; }}
    .back-link {{ margin-top: 40px; font: 500 13px/1 var(--font-ui); }}
    .back-link a {{ color: var(--stone-600); }}
    .back-link a:hover {{ color: var(--red); }}
    @media (max-width: 600px) {{
      .profile-header {{ flex-direction: column; gap: 16px; }}
    }}
  </style>
{NAV_SCRIPT}
</head>
<body>
{SITE_HEADER}
<div class="wrap">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Home</a>
    <span class="breadcrumb__sep">›</span>
    <a href="/influencers/">The Jury</a>
    <span class="breadcrumb__sep">›</span>
    <span>{inf['name']}</span>
  </nav>

  <div class="profile-header">
    <div class="profile-avatar">{inf['name'][0]}</div>
    <div>
      <div class="profile-name">{inf['name']}</div>
      <div class="profile-tagline">{inf['tagline']}</div>
      <div>{yt_btn}{ig_btn}</div>
    </div>
  </div>

  <div class="stat-row">
    <div class="stat">
      <div class="stat-num">{article_count}</div>
      <div class="stat-label">Review{'s' if article_count != 1 else ''} Analysed</div>
    </div>
  </div>

  <p class="section-label">Reviews featuring {inf['name']}</p>
  <div class="articles-list">{articles_html if articles_html else '<p style="color:var(--stone-400);font-size:14px;padding:16px 0">Reviews coming soon — check back after the next verdict is published.</p>'}
  </div>

  <p class="back-link"><a href="/influencers/">← All Jurors</a></p>
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
        (out_dir / "index.html").write_text(generate_influencer_page(inf))

    log_fn(f"Influencer pages built: {len(influencers)} jurors")
    return len(influencers)


if __name__ == "__main__":
    build_all()
    print("Done.")

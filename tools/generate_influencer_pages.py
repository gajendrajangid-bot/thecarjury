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
    <nav class="site-nav">
      <a href="/reviews/">Reviews</a>
      <a href="/compare/">Compare</a>
      <a href="/best/">Best Lists</a>
      <a href="/influencers/" class="active">Influencers</a>
      <a href="/about/">About</a>
    </nav>
  </div>
</header>"""


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

    yt_btn = f'<a href="{inf["youtube_url"]}" class="btn-yt" target="_blank" rel="noopener noreferrer">YouTube @{inf["youtube_handle"]}</a>' if inf.get("youtube_url") else ""
    ig_btn = f'<a href="{inf["instagram_url"]}" class="btn-ig" target="_blank" rel="noopener noreferrer">Instagram @{inf["instagram_handle"]}</a>' if inf.get("instagram_url") else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA4_SNIPPET}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{inf['name']} — Independent Car Reviewer | The Car Jury</title>
  <meta name="description" content="{inf['name']} is one of India's top independent car reviewers. The Car Jury has synthesised their analysis across {article_count} car review{'s' if article_count != 1 else ''}." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/{inf['slug']}/" />
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
</body>
</html>"""


def build_all(log_fn=print):
    influencers = load_influencers()
    if not influencers:
        log_fn("No influencers.json found — skipping")
        return 0

    index_path = CARJURY / "influencers/index.html"
    index_path.write_text(generate_index(influencers))

    for inf in influencers:
        out_dir = CARJURY / "influencers" / inf["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(generate_influencer_page(inf))

    log_fn(f"Influencer pages built: {len(influencers)} jurors")
    return len(influencers)


if __name__ == "__main__":
    build_all()
    print("Done.")

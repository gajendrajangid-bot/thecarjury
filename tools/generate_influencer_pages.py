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
    # Try to get real title from HTML
    page = CARJURY / "reviews" / article_slug / "index.html"
    if page.exists():
        html = page.read_text()
        m = re.search(r'og:title["\s]+content="([^"]+)"', html)
        if m:
            display = re.sub(r"\s*[|—-].*The Car Jury.*$", "", m.group(1)).strip()
    return display, url


NAV = """<nav>
  <a class="nav-logo" href="/">The Car Jury</a>
  <div class="nav-links">
    <a href="/reviews/">Reviews</a>
    <a href="/compare/">Compare</a>
    <a href="/best/">Best Lists</a>
    <a href="/influencers/">Influencers</a>
    <a href="/about/">About</a>
  </div>
</nav>"""

BASE_STYLE = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e8e8e8; line-height: 1.7; }
    a { color: #D4A017; text-decoration: none; }
    a:hover { text-decoration: underline; }
    nav { background: #111; border-bottom: 1px solid #222; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 56px; position: sticky; top: 0; z-index: 100; }
    .nav-logo { font-family: Georgia, serif; font-size: 1.1rem; font-weight: bold; color: #D4A017; }
    .nav-links { display: flex; gap: 24px; font-size: 0.85rem; }
    .nav-links a { color: #999; }
    .wrap { max-width: 860px; margin: 0 auto; padding: 48px 24px 80px; }
    footer { border-top: 1px solid #1e1e1e; padding: 24px; text-align: center; color: #555; font-size: 0.8rem; }
"""


def generate_index(influencers: list[dict]) -> str:
    cards = ""
    for inf in influencers:
        article_count = len(inf.get("articles", []))
        yt_link = f'<a href="{inf["youtube_url"]}" target="_blank" rel="noopener noreferrer">@{inf["youtube_handle"]}</a>' if inf.get("youtube_url") else ""
        ig_link = f' · <a href="{inf["instagram_url"]}" target="_blank" rel="noopener noreferrer">@{inf["instagram_handle"]}</a>' if inf.get("instagram_url") else ""
        cards += f"""
    <a href="/influencers/{inf['slug']}/" class="inf-card">
      <div class="inf-avatar">{inf['name'][0]}</div>
      <div class="inf-body">
        <div class="inf-name">{inf['name']}</div>
        <div class="inf-tagline">{inf['tagline']}</div>
        <div class="inf-meta">{yt_link}{ig_link}</div>
        <div class="inf-count">{article_count} review{'s' if article_count != 1 else ''} analysed</div>
      </div>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>India's Top Car Reviewers — The Car Jury</title>
  <meta name="description" content="The independent YouTube creators whose reviews The Car Jury synthesises. No media outlets. No manufacturer relationships." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <style>
    {BASE_STYLE}
    h1 {{ font-family: Georgia, serif; font-size: clamp(1.6rem, 4vw, 2.2rem); color: #fff; margin-bottom: 8px; }}
    .subtitle {{ color: #777; margin-bottom: 40px; font-size: 0.95rem; }}
    .inf-grid {{ display: grid; gap: 16px; }}
    .inf-card {{ background: #141414; border: 1px solid #222; border-radius: 10px; padding: 24px; display: flex; gap: 20px; align-items: flex-start; transition: border-color 0.2s; }}
    .inf-card:hover {{ border-color: #D4A017; text-decoration: none; }}
    .inf-avatar {{ width: 52px; height: 52px; border-radius: 50%; background: #D4A017; color: #000; font-family: Georgia, serif; font-size: 1.4rem; font-weight: bold; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .inf-name {{ font-family: Georgia, serif; font-size: 1.1rem; color: #fff; margin-bottom: 4px; }}
    .inf-tagline {{ color: #999; font-size: 0.88rem; margin-bottom: 8px; }}
    .inf-meta {{ font-size: 0.82rem; color: #D4A017; margin-bottom: 6px; }}
    .inf-count {{ font-size: 0.78rem; color: #555; background: #1a1a1a; display: inline-block; padding: 2px 10px; border-radius: 20px; }}
  </style>
</head>
<body>
{NAV}
<div class="wrap">
  <h1>The Jury</h1>
  <p class="subtitle">{len(influencers)} independent YouTube creators whose reviews we analyse. No media outlets. No manufacturer relationships.</p>
  <div class="inf-grid">{cards}
  </div>
</div>
<footer>© {TODAY_YEAR} The Car Jury · <a href="/">Home</a> · <a href="/reviews/">All Reviews</a></footer>
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
        <span class="article-title">{display}</span>
        <span class="article-arrow">→</span>
      </a>"""

    yt_btn = f'<a href="{inf["youtube_url"]}" class="btn-yt" target="_blank" rel="noopener noreferrer">YouTube @{inf["youtube_handle"]}</a>' if inf.get("youtube_url") else ""
    ig_btn = f'<a href="{inf["instagram_url"]}" class="btn-ig" target="_blank" rel="noopener noreferrer">Instagram @{inf["instagram_handle"]}</a>' if inf.get("instagram_url") else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{inf['name']} — The Car Jury</title>
  <meta name="description" content="{inf['name']} is one of India's top independent car reviewers. The Car Jury has synthesised their analysis across {article_count} car review{'s' if article_count != 1 else ''}." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/{inf['slug']}/" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <style>
    {BASE_STYLE}
    .profile-header {{ display: flex; gap: 28px; align-items: center; margin-bottom: 40px; flex-wrap: wrap; }}
    .profile-avatar {{ width: 80px; height: 80px; border-radius: 50%; background: #D4A017; color: #000; font-family: Georgia, serif; font-size: 2rem; font-weight: bold; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .profile-name {{ font-family: Georgia, serif; font-size: clamp(1.6rem, 4vw, 2.2rem); color: #fff; margin-bottom: 6px; }}
    .profile-tagline {{ color: #999; font-size: 0.95rem; margin-bottom: 14px; }}
    .btn-yt, .btn-ig {{ display: inline-block; padding: 8px 18px; border-radius: 4px; font-size: 0.82rem; font-weight: 600; margin-right: 10px; margin-bottom: 8px; }}
    .btn-yt {{ background: #ff0000; color: #fff; }}
    .btn-ig {{ background: #c13584; color: #fff; }}
    .stat-row {{ display: flex; gap: 24px; margin-bottom: 48px; flex-wrap: wrap; }}
    .stat {{ background: #141414; border: 1px solid #222; border-radius: 8px; padding: 16px 24px; text-align: center; }}
    .stat-num {{ font-family: Georgia, serif; font-size: 2rem; color: #D4A017; font-weight: bold; line-height: 1; }}
    .stat-label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }}
    h2 {{ font-family: Georgia, serif; font-size: 1.3rem; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #D4A017; display: inline-block; }}
    .articles-list {{ display: grid; gap: 12px; }}
    .article-item {{ background: #141414; border: 1px solid #222; border-radius: 8px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; transition: border-color 0.2s; }}
    .article-item:hover {{ border-color: #D4A017; text-decoration: none; }}
    .article-title {{ color: #e8e8e8; font-size: 0.95rem; }}
    .article-arrow {{ color: #D4A017; }}
    .breadcrumb {{ font-size: 0.8rem; color: #555; margin-bottom: 32px; }}
    .breadcrumb a {{ color: #666; }}
  </style>
</head>
<body>
{NAV}
<div class="wrap">
  <div class="breadcrumb"><a href="/">Home</a> → <a href="/influencers/">The Jury</a> → {inf['name']}</div>

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

  <h2>Reviews Featuring {inf['name']}</h2>
  <div class="articles-list">{articles_html}
  </div>

  <p style="margin-top:48px;color:#555;font-size:0.85rem"><a href="/influencers/">← All Jurors</a></p>
</div>
<footer>© {TODAY_YEAR} The Car Jury · <a href="/">Home</a> · <a href="/reviews/">All Reviews</a> · <a href="/influencers/">The Jury</a></footer>
</body>
</html>"""


def build_all(log_fn=print):
    influencers = load_influencers()
    if not influencers:
        log_fn("No influencers.json found — skipping")
        return 0

    # Main index
    index_path = CARJURY / "influencers/index.html"
    index_path.write_text(generate_index(influencers))

    # Individual pages
    for inf in influencers:
        out_dir = CARJURY / "influencers" / inf["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(generate_influencer_page(inf))

    log_fn(f"Influencer pages built: {len(influencers)} jurors")
    return len(influencers)


if __name__ == "__main__":
    build_all()
    print("Done.")

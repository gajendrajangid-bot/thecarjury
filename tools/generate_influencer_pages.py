#!/usr/bin/env python3
"""
Generate /influencers/ index + individual influencer profile pages from influencers.json.
Called by carjury_manager.py after every new review.
"""

from __future__ import annotations
import json, re
from pathlib import Path
from datetime import date

CARJURY = Path(__file__).parent.parent
INFLUENCERS_JSON = CARJURY / "influencers/influencers.json"
TODAY_YEAR = date.today().year

REVIEWS = {
    "tata/sierra":  {"title": "Tata Sierra 2025",  "score": "7.8", "verdict": "WAIT", "juror_count": 5, "url": "/reviews/tata/sierra/"},
    "mahindra/be6": {"title": "Mahindra BE6",       "score": "8.0", "verdict": "BUY",  "juror_count": 6, "url": "/reviews/mahindra/be6/"},
}


def load_influencers() -> list[dict]:
    if not INFLUENCERS_JSON.exists():
        return []
    return json.loads(INFLUENCERS_JSON.read_text())


FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,400&'
    'family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&'
    'family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet" />'
)

TOKENS = """
    :root {
      --red:        #C8102E;
      --red-dark:   #8B0A1F;
      --red-light:  #FBE8EB;
      --ink:        #1A1A1A;
      --paper:      #FAF8F5;
      --white:      #FFFFFF;
      --stone:      #6B6B6B;
      --hairline:   #E5E2DC;
      --green:      #0E6B3C;
      --amber:      #B8860B;
      --slate:      #3D3D3D;
      --display:    'Fraunces', Georgia, serif;
      --serif:      'Source Serif 4', Georgia, serif;
      --sans:       'Inter', -apple-system, 'Helvetica Neue', sans-serif;
    }"""

BASE_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    img { display: block; max-width: 100%; }
    a { color: inherit; text-decoration: none; }
    html { font-size: 16px; }
    body { background: var(--paper); color: var(--ink); font-family: var(--sans); line-height: 1.6; -webkit-font-smoothing: antialiased; }

    .nav { border-bottom: 1px solid var(--hairline); background: var(--white); position: sticky; top: 0; z-index: 100; }
    .nav__inner { max-width: 1120px; margin: 0 auto; padding: 0 24px; height: 60px; display: flex; align-items: center; justify-content: space-between; }
    .nav__logo { font-family: var(--display); font-weight: 700; font-size: 20px; color: var(--ink); letter-spacing: -0.02em; display: inline-flex; align-items: baseline; gap: 5px; }
    .nav__logo__the { color: var(--red); font-style: italic; font-size: 15px; font-weight: 400; }
    .nav__links { display: flex; gap: 28px; list-style: none; }
    .nav__links a { font-size: 13px; font-weight: 500; letter-spacing: 0.02em; color: var(--stone); text-transform: uppercase; transition: color 0.15s; }
    .nav__links a:hover { color: var(--ink); }
    .nav__links a.active { color: var(--red); }

    .page { max-width: 1120px; margin: 0 auto; padding: 0 24px; }

    .footer { border-top: 1px solid var(--hairline); padding: 40px 0; }
    .footer__inner { max-width: 1120px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: flex-start; gap: 32px; flex-wrap: wrap; }
    .footer__name { font-family: var(--display); font-size: 17px; font-weight: 700; color: var(--ink); margin-bottom: 6px; letter-spacing: -0.01em; }
    .footer__tagline { font-size: 13px; color: var(--stone); max-width: 360px; line-height: 1.6; }
    .footer__links { display: flex; gap: 24px; list-style: none; align-items: center; }
    .footer__links a { font-size: 13px; color: var(--stone); transition: color 0.15s; }
    .footer__links a:hover { color: var(--ink); }
    .footer__copy { font-size: 12px; color: #BBBAB5; margin-top: 10px; }
    .footer__bottom { max-width: 1120px; margin: 16px auto 0; padding: 0 24px; border-top: 1px solid var(--hairline); padding-top: 16px; }"""

NAV_HTML = """<nav class="nav">
  <div class="nav__inner">
    <a href="/" class="nav__logo">
      <span class="nav__logo__the">The</span>Car Jury
    </a>
    <ul class="nav__links">
      <li><a href="/reviews/">Reviews</a></li>
      <li><a href="/compare/">Compare</a></li>
      <li><a href="/best/">Best Lists</a></li>
      <li><a href="/influencers/" class="active">The Jury</a></li>
      <li><a href="/about/">About</a></li>
    </ul>
  </div>
</nav>"""


def footer_html() -> str:
    return f"""<footer class="footer">
  <div class="footer__inner">
    <div>
      <p class="footer__name">The Car Jury</p>
      <p class="footer__tagline">We watch every expert so you don't have to — one clear verdict on every car.</p>
      <p class="footer__copy">No sponsored reviews · No manufacturer relationships · India's aggregated car reviews</p>
    </div>
    <ul class="footer__links">
      <li><a href="/reviews/">Reviews</a></li>
      <li><a href="/compare/">Compare</a></li>
      <li><a href="/best/">Best Lists</a></li>
      <li><a href="/influencers/">The Jury</a></li>
      <li><a href="/about/">About</a></li>
    </ul>
  </div>
  <div class="footer__bottom">
    <p style="font-size:12px;color:#BBBAB5;">© {TODAY_YEAR} The Car Jury</p>
  </div>
</footer>"""


def platform_tags_html(platforms: list[str]) -> str:
    return "".join(f'<span class="platform-tag">{p}</span>' for p in platforms)


def verdict_pill_class(verdict: str) -> str:
    return {"BUY": "verdict-pill--buy", "WAIT": "verdict-pill--wait", "SKIP": "verdict-pill--skip"}.get(verdict, "verdict-pill--skip")


def verdict_pill_label(verdict: str) -> str:
    return {"BUY": "● Buy", "WAIT": "● Wait", "SKIP": "● Skip"}.get(verdict, verdict)


def generate_index(influencers: list[dict]) -> str:
    juror_count = len(influencers)
    total_reviews = sum(len(inf.get("articles", [])) for inf in influencers)

    cards_html = ""
    for inf in influencers:
        article_count = len(inf.get("articles", []))
        platforms = inf.get("platforms", ["YouTube"])
        slug = inf["slug"]
        initial = inf["name"][0].upper()
        cards_html += f"""
    <a href="/influencers/{slug}/" class="juror-card">
      <div class="juror-card__top">
        <div class="juror-avatar">{initial}</div>
        <div class="juror-card__header">
          <div class="juror-card__platforms">{platform_tags_html(platforms)}</div>
          <h3 class="juror-card__name">{inf['name']}</h3>
          <span class="juror-card__handle">@{inf['youtube_handle']}</span>
        </div>
      </div>
      <p class="juror-card__tagline">{inf['tagline']}</p>
      <div class="juror-card__footer">
        <span class="juror-badge">
          <span class="juror-badge__dot"></span>
          {article_count} review{'s' if article_count != 1 else ''} analysed
        </span>
        <span class="juror-card__arrow">→</span>
      </div>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The Jury — The Car Jury</title>
  <meta name="description" content="{juror_count} independent creators whose reviews The Car Jury synthesises into one verdict. No media outlets. No manufacturer relationships." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  {FONTS_LINK}
  <style>
    {TOKENS}
    {BASE_CSS}

    .hero {{ padding: 72px 0 52px; border-bottom: 1px solid var(--hairline); }}
    .hero__eyebrow {{ font-size: 11px; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: var(--red); margin-bottom: 16px; }}
    .hero__title {{ font-family: var(--display); font-size: 52px; font-weight: 700; line-height: 1.05; letter-spacing: -0.02em; color: var(--ink); margin-bottom: 20px; }}
    .hero__lead {{ font-family: var(--serif); font-size: 19px; line-height: 1.65; color: var(--ink); max-width: 640px; margin-bottom: 28px; }}
    .hero__meta {{ display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }}
    .hero__stat {{ display: flex; align-items: baseline; gap: 6px; }}
    .hero__stat-num {{ font-size: 28px; font-weight: 600; color: var(--ink); letter-spacing: -0.02em; }}
    .hero__stat-label {{ font-size: 13px; color: var(--stone); }}
    .hero__divider {{ width: 1px; height: 28px; background: var(--hairline); }}
    .hero__trust {{ font-size: 13px; color: var(--stone); font-style: italic; }}

    .callout {{ background: var(--white); border: 1px solid var(--hairline); border-left: 3px solid var(--red); border-radius: 0 8px 8px 0; padding: 24px 28px; margin: 48px 0; max-width: 720px; }}
    .callout__heading {{ font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--red); margin-bottom: 10px; }}
    .callout__body {{ font-family: var(--serif); font-size: 16px; line-height: 1.7; color: var(--ink); }}

    .grid-header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 28px; }}
    .grid-header__title {{ font-family: var(--display); font-size: 22px; font-weight: 700; color: var(--ink); }}
    .grid-header__count {{ font-size: 13px; color: var(--stone); }}

    .jurors-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--hairline); border: 1px solid var(--hairline); border-radius: 8px; overflow: hidden; margin-bottom: 64px; }}
    .juror-card {{ background: var(--white); padding: 32px 28px 28px; display: flex; flex-direction: column; transition: background 0.15s; position: relative; }}
    .juror-card:hover {{ background: var(--paper); }}
    .juror-card__top {{ display: flex; align-items: flex-start; gap: 16px; margin-bottom: 20px; }}
    .juror-avatar {{ width: 52px; height: 52px; border-radius: 50%; background: var(--red-light); color: var(--red); font-family: var(--display); font-size: 22px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .juror-card__header {{ flex: 1; }}
    .juror-card__platforms {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }}
    .platform-tag {{ font-size: 11px; font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; color: var(--stone); background: var(--paper); border: 1px solid var(--hairline); border-radius: 4px; padding: 2px 7px; }}
    .juror-card__name {{ font-family: var(--display); font-size: 18px; font-weight: 700; color: var(--ink); line-height: 1.2; margin-bottom: 3px; }}
    .juror-card__handle {{ font-size: 12px; color: var(--red); font-weight: 500; }}
    .juror-card__tagline {{ font-family: var(--serif); font-size: 14.5px; line-height: 1.6; color: var(--stone); flex: 1; margin-bottom: 24px; }}
    .juror-card__footer {{ display: flex; align-items: center; justify-content: space-between; padding-top: 18px; border-top: 1px solid var(--hairline); }}
    .juror-badge {{ display: inline-flex; align-items: center; gap: 6px; background: var(--paper); border: 1px solid var(--hairline); border-radius: 20px; padding: 4px 10px 4px 6px; font-size: 12px; font-weight: 500; color: var(--stone); }}
    .juror-badge__dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--red); flex-shrink: 0; }}
    .juror-card__arrow {{ font-size: 16px; color: var(--hairline); transition: color 0.15s, transform 0.15s; }}
    .juror-card:hover .juror-card__arrow {{ color: var(--red); transform: translateX(3px); }}

    .philosophy {{ border-top: 1px solid var(--hairline); border-bottom: 1px solid var(--hairline); padding: 52px 0; margin-bottom: 64px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 48px; }}
    .philosophy__icon {{ width: 32px; height: 32px; margin-bottom: 14px; }}
    .philosophy__title {{ font-family: var(--display); font-size: 17px; font-weight: 700; color: var(--ink); margin-bottom: 8px; }}
    .philosophy__body {{ font-size: 14px; line-height: 1.65; color: var(--stone); }}

    @media (max-width: 900px) {{
      .jurors-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .philosophy {{ grid-template-columns: 1fr 1fr; }}
      .hero__title {{ font-size: 40px; }}
    }}
    @media (max-width: 600px) {{
      .jurors-grid {{ grid-template-columns: 1fr; }}
      .philosophy {{ grid-template-columns: 1fr; gap: 32px; }}
      .hero__title {{ font-size: 32px; }}
      .hero {{ padding: 48px 0 36px; }}
      .nav__links {{ display: none; }}
      .footer__inner {{ flex-direction: column; gap: 24px; }}
    }}
  </style>
</head>
<body>
{NAV_HTML}

<div class="page">
  <header class="hero">
    <p class="hero__eyebrow">The Car Jury · The Jurors</p>
    <h1 class="hero__title">Meet The Jury</h1>
    <p class="hero__lead">
      {juror_count} independent creators whose reviews we analyse — no media outlets,
      no manufacturer relationships, no sponsored takes. Just honest voices, weighed.
    </p>
    <div class="hero__meta">
      <div class="hero__stat">
        <span class="hero__stat-num">{juror_count}</span>
        <span class="hero__stat-label">independent jurors</span>
      </div>
      <div class="hero__divider"></div>
      <div class="hero__stat">
        <span class="hero__stat-num">{total_reviews}</span>
        <span class="hero__stat-label">reviews analysed</span>
      </div>
      <div class="hero__divider"></div>
      <span class="hero__trust">No sponsored reviews · No manufacturer relationships</span>
    </div>
  </header>

  <div class="callout">
    <p class="callout__heading">How The Jury works</p>
    <p class="callout__body">
      Every verdict on The Car Jury is built from the independent views of these creators.
      We watch their reviews, weigh their reasoning, and synthesise a single, honest verdict —
      Buy, Wait, or Skip. No creator is paid to review on our behalf. Their independence is
      the whole point.
    </p>
  </div>

  <div class="grid-header">
    <h2 class="grid-header__title">The Jurors</h2>
    <span class="grid-header__count">{juror_count} independent creators</span>
  </div>

  <div class="jurors-grid">{cards_html}
  </div>

  <div class="philosophy">
    <div>
      <svg class="philosophy__icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="14" stroke="#C8102E" stroke-width="1.5"/>
        <path d="M10 16l4 4 8-8" stroke="#C8102E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <h3 class="philosophy__title">Truly independent</h3>
      <p class="philosophy__body">Every juror is a self-funded creator. No manufacturer sponsorships, no media affiliations, no press-trip free cars. What they say is what they believe.</p>
    </div>
    <div>
      <svg class="philosophy__icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="8" width="20" height="16" rx="2" stroke="#C8102E" stroke-width="1.5"/>
        <path d="M11 16h10M11 12h6" stroke="#C8102E" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <h3 class="philosophy__title">Depth over flash</h3>
      <p class="philosophy__body">We select jurors who go beyond the press launch — who measure, test, and hold cars to account. Review length matters less than reasoning quality.</p>
    </div>
    <div>
      <svg class="philosophy__icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 6v4M16 22v4M6 16h4M22 16h4" stroke="#C8102E" stroke-width="1.5" stroke-linecap="round"/>
        <circle cx="16" cy="16" r="6" stroke="#C8102E" stroke-width="1.5"/>
      </svg>
      <h3 class="philosophy__title">The jury decides</h3>
      <p class="philosophy__body">No single juror has the final word. Verdicts are synthesised across all available reviews — agreement strengthens the verdict, disagreement is noted and reported.</p>
    </div>
  </div>

</div>
{footer_html()}
</body>
</html>"""


def generate_influencer_page(inf: dict, all_influencers: list[dict]) -> str:
    articles = inf.get("articles", [])
    article_count = len(articles)
    slug = inf["slug"]
    name = inf["name"]
    initial = name[0].upper()
    platforms = inf.get("platforms", ["YouTube"])
    about_paras = inf.get("about", [inf.get("tagline", "")])
    style_tags = inf.get("style_tags", [])
    why_text = inf.get("why", "")

    platform_labels = " · ".join(platforms)

    # Platform link buttons — data-platform/data-handle used by click tracker
    links_html = ""
    if inf.get("youtube_url"):
        links_html += f'''<a href="{inf['youtube_url']}" target="_blank" rel="noopener" class="profile-link" data-platform="YouTube" data-handle="{inf['youtube_handle']}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46A2.78 2.78 0 0 0 1.46 6.42 29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.95 1.96C5.12 20 12 20 12 20s6.88 0 8.59-.46a2.78 2.78 0 0 0 1.96-1.96A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z"/><polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02"/></svg>
          @{inf['youtube_handle']}
        </a>'''
    if inf.get("instagram_url"):
        links_html += f'''<a href="{inf['instagram_url']}" target="_blank" rel="noopener" class="profile-link" data-platform="Instagram" data-handle="{inf['instagram_handle']}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
          @{inf['instagram_handle']}
        </a>'''

    # About paragraphs
    about_html = "".join(f"<p>{p}</p>" for p in about_paras)

    # Style tags
    style_tags_html = "".join(f'<span class="style-tag">{t}</span>' for t in style_tags)

    # Verdict cards
    verdict_cards_html = ""
    for article_slug in articles:
        rev = REVIEWS.get(article_slug)
        if not rev:
            continue
        pill_cls = verdict_pill_class(rev["verdict"])
        pill_lbl = verdict_pill_label(rev["verdict"])
        verdict_cards_html += f"""
          <article class="verdict-card">
            <div class="verdict-card__stamp">The Verdict</div>
            <div class="verdict-card__body">
              <h3 class="verdict-card__car">{rev['title']}</h3>
              <div class="verdict-card__row">
                <div class="verdict-score">{rev['score']}<span class="verdict-score__denom">/10</span></div>
                <span class="verdict-pill {pill_cls}">{pill_lbl}</span>
              </div>
            </div>
            <div class="verdict-card__footer">
              <span class="verdict-card__jury-line">Based on {rev['juror_count']} independent creators</span>
              <a href="{rev['url']}" class="verdict-card__link">Read verdict →</a>
            </div>
          </article>"""

    if not verdict_cards_html:
        verdict_cards_html = '<p style="color:var(--stone);font-family:var(--serif);font-size:15px;padding:16px 0">Reviews coming soon — check back after the next verdict is published.</p>'

    # Other jurors sidebar rows
    other_jurors_html = ""
    for other in all_influencers:
        if other["slug"] == slug:
            continue
        other_initial = other["name"][0].upper()
        other_jurors_html += f"""
        <a href="/influencers/{other['slug']}/" class="other-juror-row">
          <div class="other-juror-row__avatar">{other_initial}</div>
          <span class="other-juror-row__name">{other['name']}</span>
          <span class="other-juror-row__arrow">→</span>
        </a>"""
    other_jurors_html += """
        <a href="/influencers/" class="other-juror-row" style="color:var(--red);">
          <div class="other-juror-row__avatar" style="background:var(--paper);color:var(--stone);">↑</div>
          <span class="other-juror-row__name" style="color:var(--red);">View all jurors</span>
          <span class="other-juror-row__arrow" style="color:var(--red);">→</span>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name} — The Car Jury</title>
  <meta name="description" content="{name}: {inf['tagline']} The Car Jury has analysed their reviews across {article_count} car{'s' if article_count != 1 else ''}." />
  <link rel="canonical" href="https://www.thecarjury.com/influencers/{slug}/" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  {FONTS_LINK}
  <style>
    {TOKENS}
    {BASE_CSS}

    .breadcrumb {{ padding: 20px 0 0; display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--stone); }}
    .breadcrumb a {{ transition: color 0.15s; }}
    .breadcrumb a:hover {{ color: var(--red); }}
    .breadcrumb__sep {{ color: var(--hairline); }}
    .breadcrumb__current {{ color: var(--ink); }}

    .profile-hero {{ padding: 40px 0 48px; border-bottom: 1px solid var(--hairline); display: grid; grid-template-columns: 1fr auto; gap: 32px; align-items: start; }}
    .profile-avatar {{ width: 72px; height: 72px; border-radius: 50%; background: var(--red-light); color: var(--red); font-family: var(--display); font-size: 30px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .profile-hero__meta {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }}
    .profile-hero__eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--red); margin-bottom: 6px; }}
    .profile-hero__name {{ font-family: var(--display); font-size: 44px; font-weight: 700; line-height: 1.05; letter-spacing: -0.02em; color: var(--ink); margin-bottom: 14px; }}
    .profile-hero__tagline {{ font-family: var(--serif); font-size: 19px; line-height: 1.6; color: var(--stone); max-width: 600px; margin-bottom: 28px; font-style: italic; }}
    .profile-hero__links {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .profile-link {{ display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 500; color: var(--stone); border: 1px solid var(--hairline); border-radius: 6px; padding: 7px 12px; background: var(--white); transition: all 0.15s; }}
    .profile-link:hover {{ color: var(--red); border-color: var(--red-light); background: var(--red-light); }}
    .profile-link svg {{ flex-shrink: 0; }}

    .profile-hero__stats {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 24px; min-width: 200px; }}
    .profile-hero__stats-title {{ font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--stone); margin-bottom: 20px; }}
    .stat-row {{ display: flex; flex-direction: column; margin-bottom: 20px; }}
    .stat-row:last-child {{ margin-bottom: 0; }}
    .stat-row__num {{ font-size: 32px; font-weight: 600; color: var(--ink); letter-spacing: -0.03em; line-height: 1; margin-bottom: 4px; }}
    .stat-row__label {{ font-size: 12px; color: var(--stone); }}
    .stat-row__divider {{ border: none; border-top: 1px solid var(--hairline); margin: 16px 0; }}

    .content-layout {{ display: grid; grid-template-columns: 1fr 300px; gap: 48px; padding: 48px 0 72px; align-items: start; }}
    .section-heading {{ font-family: var(--display); font-size: 22px; font-weight: 700; color: var(--ink); margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--hairline); }}

    .about-body {{ font-family: var(--serif); font-size: 16px; line-height: 1.75; color: var(--ink); margin-bottom: 20px; }}
    .about-body p {{ margin-bottom: 16px; }}
    .about-body p:last-child {{ margin-bottom: 0; }}
    .style-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 40px; }}
    .style-tag {{ font-size: 12px; font-weight: 500; color: var(--stone); background: var(--white); border: 1px solid var(--hairline); border-radius: 20px; padding: 5px 12px; }}

    .verdict-list {{ display: flex; flex-direction: column; gap: 12px; }}
    .verdict-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; overflow: hidden; transition: border-color 0.15s; }}
    .verdict-card:hover {{ border-color: var(--stone); }}
    .verdict-card__stamp {{ background: var(--red); padding: 6px 16px; font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--white); }}
    .verdict-card__body {{ padding: 20px 20px 16px; }}
    .verdict-card__car {{ font-family: var(--display); font-size: 20px; font-weight: 700; color: var(--ink); margin-bottom: 12px; line-height: 1.2; }}
    .verdict-card__row {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .verdict-score {{ font-size: 28px; font-weight: 600; color: var(--ink); letter-spacing: -0.02em; line-height: 1; }}
    .verdict-score__denom {{ font-size: 14px; color: var(--stone); font-weight: 400; }}
    .verdict-pill {{ display: inline-flex; align-items: center; gap: 6px; border-radius: 20px; padding: 5px 12px; font-size: 12px; font-weight: 600; letter-spacing: 0.02em; }}
    .verdict-pill--buy  {{ background: #E8F5EE; color: var(--green); }}
    .verdict-pill--wait {{ background: #FBF5E0; color: var(--amber); }}
    .verdict-pill--skip {{ background: #EEEEED; color: var(--slate); }}
    .verdict-card__footer {{ padding: 12px 20px; border-top: 1px solid var(--hairline); display: flex; align-items: center; justify-content: space-between; }}
    .verdict-card__jury-line {{ font-size: 12px; color: var(--stone); }}
    .verdict-card__link {{ font-size: 13px; font-weight: 500; color: var(--red); display: flex; align-items: center; gap: 4px; transition: gap 0.15s; }}
    .verdict-card:hover .verdict-card__link {{ gap: 7px; }}

    .trust-block {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 24px; margin-bottom: 24px; }}
    .trust-block__heading {{ font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--red); margin-bottom: 14px; }}
    .trust-block__body {{ font-family: var(--serif); font-size: 14px; line-height: 1.65; color: var(--stone); }}

    .other-jurors-block {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; overflow: hidden; }}
    .other-jurors-block__heading {{ padding: 16px 20px; font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--stone); border-bottom: 1px solid var(--hairline); }}
    .other-juror-row {{ display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid var(--hairline); transition: background 0.15s; }}
    .other-juror-row:last-child {{ border-bottom: none; }}
    .other-juror-row:hover {{ background: var(--paper); }}
    .other-juror-row__avatar {{ width: 32px; height: 32px; border-radius: 50%; background: var(--red-light); color: var(--red); font-family: var(--display); font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .other-juror-row__name {{ font-size: 13px; font-weight: 500; color: var(--ink); flex: 1; }}
    .other-juror-row__arrow {{ font-size: 14px; color: var(--hairline); transition: color 0.15s; }}
    .other-juror-row:hover .other-juror-row__arrow {{ color: var(--red); }}

    .back-link {{ display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: var(--stone); padding: 8px 0; margin-bottom: 28px; transition: color 0.15s; }}
    .back-link:hover {{ color: var(--red); }}

    @media (max-width: 960px) {{
      .content-layout {{ grid-template-columns: 1fr; }}
      .content-sidebar {{ display: none; }}
      .profile-hero {{ grid-template-columns: 1fr; }}
      .profile-hero__stats {{ display: flex; gap: 32px; flex-wrap: wrap; }}
      .stat-row {{ margin-bottom: 0; }}
      .stat-row__divider {{ display: none; }}
    }}
    @media (max-width: 600px) {{
      .profile-hero__name {{ font-size: 32px; }}
      .nav__links {{ display: none; }}
      .profile-hero {{ padding: 28px 0 36px; }}
      .footer__inner {{ flex-direction: column; gap: 24px; }}
    }}
  </style>
</head>
<body>
{NAV_HTML}

<div class="page">
  <nav class="breadcrumb" aria-label="breadcrumb">
    <a href="/">Home</a>
    <span class="breadcrumb__sep">›</span>
    <a href="/influencers/">The Jury</a>
    <span class="breadcrumb__sep">›</span>
    <span class="breadcrumb__current">{name}</span>
  </nav>

  <div class="profile-hero">
    <div class="profile-hero__left">
      <div class="profile-hero__meta">
        <div class="profile-avatar">{initial}</div>
        <div>
          <p class="profile-hero__eyebrow">Independent Juror · {platform_labels}</p>
        </div>
      </div>
      <h1 class="profile-hero__name">{name}</h1>
      <p class="profile-hero__tagline">"{inf['tagline']}"</p>
      <div class="profile-hero__links">
        {links_html}
      </div>
    </div>

    <div class="profile-hero__stats">
      <p class="profile-hero__stats-title">On The Jury</p>
      <div class="stat-row">
        <span class="stat-row__num">{article_count}</span>
        <span class="stat-row__label">review{'s' if article_count != 1 else ''} analysed</span>
      </div>
      <hr class="stat-row__divider" />
      <div class="stat-row">
        <span class="stat-row__num">{article_count}</span>
        <span class="stat-row__label">verdict{'s' if article_count != 1 else ''} contributed to</span>
      </div>
      <hr class="stat-row__divider" />
      <div class="stat-row">
        <span class="stat-row__num">Since</span>
        <span class="stat-row__label">2026 · Active juror</span>
      </div>
    </div>
  </div>

  <div class="content-layout">
    <main class="content-main">
      <section style="margin-bottom:40px;">
        <h2 class="section-heading">About this juror</h2>
        <div class="about-body">{about_html}</div>
        <div class="style-tags">{style_tags_html}</div>
      </section>
      <section>
        <h2 class="section-heading">Reviews we've analysed</h2>
        <div class="verdict-list">{verdict_cards_html}
        </div>
      </section>
    </main>

    <aside class="content-sidebar">
      <div class="trust-block">
        <p class="trust-block__heading">Why this juror</p>
        <p class="trust-block__body">{why_text}</p>
      </div>
      <div class="other-jurors-block">
        <p class="other-jurors-block__heading">Other jurors</p>
        {other_jurors_html}
      </div>
    </aside>
  </div>

  <a href="/influencers/" class="back-link">← Back to all jurors</a>
</div>

{footer_html()}
<script>
(function(){{
  var GAS = 'https://script.google.com/macros/s/AKfycbyddgIXufUp2fEY8vZjtCyiLGXseB1MPN7tEv41WZ4iIOO2BCDUqUPvFqRBvc76HEkjuA/exec';
  var juror = window.location.pathname.replace(/\\/+$/,'').split('/').pop() || '';
  document.querySelectorAll('.profile-link[data-platform]').forEach(function(link){{
    link.addEventListener('click', function(){{
      var fd = new FormData();
      fd.append('type', 'click');
      fd.append('juror', juror);
      fd.append('platform', this.getAttribute('data-platform') || '');
      fd.append('handle', this.getAttribute('data-handle') || '');
      fetch(GAS, {{method:'POST', body:fd, mode:'no-cors'}}).catch(function(){{}});
    }});
  }});
}})();
</script>
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
        (out_dir / "index.html").write_text(
            generate_influencer_page(inf, influencers)
        )

    log_fn(f"Influencer pages built: {len(influencers)} jurors")
    return len(influencers)


if __name__ == "__main__":
    build_all()
    print("Done.")

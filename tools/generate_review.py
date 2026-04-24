#!/usr/bin/env python3
"""
The Car Jury — Review Generator
Usage:
  python3 generate_review.py --brand tata --model nexon-ev --name "Tata Nexon EV" --year 2025 --videos ID1 ID2 ...
  python3 generate_review.py --from-research /path/to/mahindra_be6_research.json
"""

from __future__ import annotations
import argparse, os, sys, json, re, subprocess
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
CARJURY = ROOT / "carjury"

GA4_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0LV8GN0CD5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-0LV8GN0CD5');
</script>"""
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
env = {}
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
os.environ.update(env)

ANTHROPIC_API_KEY = env.get("ANTHROPIC_API_KEY", "")


# ── YouTube Transcript ─────────────────────────────────────────────────────────

def fetch_transcript(video_id: str) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        # Try English first, then Hindi (common for Indian channels)
        for lang in [["en"], ["hi"], None]:
            try:
                transcript = api.fetch(video_id, languages=lang) if lang else api.fetch(video_id)
                return " ".join(t.text for t in transcript)
            except Exception:
                continue
        return ""
    except Exception as e:
        print(f"  [warn] Transcript failed for {video_id}: {e}")
        return ""


def fetch_video_title(video_id: str) -> tuple[str, str]:
    try:
        import urllib.request
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("title", ""), data.get("author_name", "")
    except Exception:
        return "", ""


# ── Claude Synthesis ───────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are the editorial engine for The Car Jury — India's most trusted, neutral car review synthesis platform.

Your job: synthesise the transcripts from multiple independent reviewers into a single, comprehensive, structured car review article.

RULES:
- Be completely neutral. No manufacturer bias.
- Use specific facts, quotes, and numbers from the transcripts.
- Identify CONSENSUS (what most reviewers agree on) and DISAGREEMENTS.
- Use Indian context: prices in INR, Indian road conditions, Indian buyers' concerns.
- Write for both human readers AND AI search engines (GEO-optimised).
- Every claim must be supportable from the source transcripts.
- Never make up specs or prices. Only use what's in the transcripts.
- NEVER use em-dashes (—) anywhere in the output. Use commas, colons, semicolons, or full stops instead.
- TeamBHP is a trusted 20-year-old independent forum with expert owners and journalists. Weight their observations alongside the YouTube reviewers.
- WORD LIMIT: The total combined words across all text fields (hero_summary, verdict_reason, all *_review fields, teambhp_take, reviewer_takes, pros, cons, consensus_points, disagreement_points, faqs) must not exceed 1700 words. Keep each section tight. Prefer one precise sentence over two vague ones.

CAR: {car_name} ({year})
REVIEWERS: {reviewer_list}

YOUTUBE REVIEW TRANSCRIPTS:
{transcripts}

{teambhp_section}

Generate a JSON object with these exact fields:
{{
  "jury_score": 7.5,
  "verdict": "BUY | WAIT | SKIP",
  "verdict_reason": "one sentence why",
  "scores": {{
    "design": 8.0,
    "interior": 7.5,
    "performance": 7.0,
    "ride": 8.0,
    "build_quality": 7.5,
    "value": 7.0
  }},
  "hero_summary": "2-3 sentence punchy summary of the car",
  "consensus_points": ["point1", "point2", "point3", "point4", "point5"],
  "disagreement_points": ["disagreement1", "disagreement2"],
  "pros": ["pro1", "pro2", "pro3", "pro4", "pro5"],
  "cons": ["con1", "con2", "con3", "con4"],
  "design_review": "150-200 word paragraph on design",
  "interior_review": "150-200 word paragraph on interior",
  "performance_review": "150-200 word paragraph on performance and powertrain",
  "ride_review": "150-200 word paragraph on ride quality and handling",
  "build_quality_review": "150-200 word paragraph on build quality and features",
  "value_review": "150-200 word paragraph on pricing and value",
  "teambhp_take": "2-3 sentences summarising what TeamBHP's community/reviewers said, highlighting any owner perspectives or long-term findings",
  "reviewer_takes": [
    {{"name": "Reviewer Name", "channel": "Channel Name", "take": "Their specific stance in 1-2 sentences"}}
  ],
  "faqs": [
    {{"q": "Should I buy the {car_name}?", "a": "Direct answer with specifics"}},
    {{"q": "What is the {car_name} price in India?", "a": "..."}},
    {{"q": "What are the main problems with the {car_name}?", "a": "..."}},
    {{"q": "How is the {car_name} mileage?", "a": "..."}},
    {{"q": "Is {car_name} good for highway driving?", "a": "..."}},
    {{"q": "How does {car_name} compare to rivals?", "a": "..."}},
    {{"q": "What is the boot space of {car_name}?", "a": "..."}},
    {{"q": "Is {car_name} safe?", "a": "..."}},
    {{"q": "What is the waiting period for {car_name}?", "a": "..."}},
    {{"q": "Which variant of {car_name} should I buy?", "a": "..."}}
  ],
  "meta_description": "155 char max SEO meta description",
  "og_title": "SEO-optimised article title under 60 chars"
}}

Return ONLY the JSON object. No markdown fences. No explanation."""


def synthesise_with_claude(car_name: str, year: int,
                           transcripts: dict[str, str],
                           teambhp_content: str = "") -> dict:
    import anthropic

    reviewer_list = ", ".join(transcripts.keys())
    combined = "\n\n---\n\n".join(
        f"REVIEWER: {name}\n{text}"
        for name, text in transcripts.items()
        if text
    )

    if teambhp_content:
        teambhp_section = f"TEAMBHP FORUM REVIEW:\n{teambhp_content}"
    else:
        teambhp_section = ""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": SYNTHESIS_PROMPT.format(
                car_name=car_name,
                year=year,
                reviewer_list=reviewer_list,
                transcripts=combined,
                teambhp_section=teambhp_section,
            )
        }]
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ── Influencer Registry Sync ───────────────────────────────────────────────────

def sync_influencers(brand: str, model: str, reviewer_takes: list[dict]) -> bool:
    """
    After a review is published, ensure every cited reviewer exists in influencers.json.
    - New reviewer → add entry with basic info derived from synthesis output
    - Existing reviewer → append this article to their articles[] if missing
    Also appends new entries to master_list.md under an "Unranked / New" section.
    Returns True if influencers.json was modified.
    """
    json_path = CARJURY / "influencers/influencers.json"
    master_list_path = CARJURY / "influencers/master_list.md"
    article_slug = f"{brand}/{model}"

    influencers = json.loads(json_path.read_text()) if json_path.exists() else []
    by_name = {inf["name"].lower(): inf for inf in influencers}

    changed = False
    newly_added = []

    for r in reviewer_takes:
        name = r.get("name", "").strip()
        channel = r.get("channel", "").strip()
        if not name:
            continue

        key = name.lower()
        if key in by_name:
            inf = by_name[key]
            if article_slug not in inf.get("articles", []):
                inf.setdefault("articles", []).append(article_slug)
                changed = True
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            handle = channel.replace(" ", "") if channel and channel != name else name.replace(" ", "")
            new_inf = {
                "slug": slug,
                "name": name,
                "tagline": f"Independent car reviewer — {channel}" if channel and channel != name else "Independent car reviewer on YouTube",
                "youtube_handle": handle,
                "youtube_url": f"https://www.youtube.com/@{handle}",
                "instagram_url": "",
                "instagram_handle": "",
                "subscriber_count": "",
                "articles": [article_slug],
            }
            influencers.append(new_inf)
            by_name[key] = new_inf
            newly_added.append(name)
            changed = True

    if changed:
        json_path.write_text(json.dumps(influencers, indent=2) + "\n")
        print(f"  influencers.json updated ({len(newly_added)} new, article synced)")

    if newly_added and master_list_path.exists():
        current = master_list_path.read_text()
        marker = "\n---\n*Last updated"
        section_header = "\n\n---\n\n## Unranked / New (subscriber count to be filled)\n\n"
        new_rows = "\n".join(
            f"| — | **{n}** | TBC | TBC | TBC | TBC | Auto-added from article |"
            for n in newly_added
        )
        if "## Unranked / New" in current:
            current = current.replace(
                "## Unranked / New (subscriber count to be filled)\n\n",
                f"## Unranked / New (subscriber count to be filled)\n\n{new_rows}\n"
            )
        else:
            insert_at = current.find(marker) if marker in current else len(current)
            current = current[:insert_at] + section_header + new_rows + "\n" + current[insert_at:]
        master_list_path.write_text(current)
        print(f"  master_list.md updated: added {newly_added}")

    return changed


# ── HTML Generator ─────────────────────────────────────────────────────────────

def score_color(score: float) -> str:
    if score >= 8.0:
        return "#0E6B3C"
    if score >= 7.0:
        return "#B45309"
    return "#C8102E"


def verdict_color(verdict: str) -> str:
    return {"BUY": "#0E6B3C", "WAIT": "#B45309", "SKIP": "#C8102E"}.get(verdict, "#6B6B6B")


def verdict_bg(verdict: str) -> str:
    return {"BUY": "#E6F2EC", "WAIT": "#FEF3C7", "SKIP": "#FEE2E2"}.get(verdict, "#F3F4F6")


def estimate_content_words(data: dict) -> tuple[int, int]:
    """Returns (word_count, reading_time_minutes) from synthesis data."""
    text_fields = [
        data.get("hero_summary", ""),
        data.get("verdict_reason", ""),
        data.get("design_review", ""),
        data.get("interior_review", ""),
        data.get("performance_review", ""),
        data.get("ride_review", ""),
        data.get("build_quality_review", ""),
        data.get("value_review", ""),
        data.get("teambhp_take", ""),
        " ".join(data.get("pros", [])),
        " ".join(data.get("cons", [])),
        " ".join(data.get("consensus_points", [])),
        " ".join(data.get("disagreement_points", [])),
        " ".join(r.get("take", "") for r in data.get("reviewer_takes", [])),
        " ".join(f["q"] + " " + f["a"] for f in data.get("faqs", [])),
    ]
    words = len(" ".join(text_fields).split())
    return words, max(1, round(words / 238))


def generate_html(brand: str, model: str, car_name: str, year: int,
                  data: dict, video_ids: list[str],
                  teambhp_url: str = "", teambhp_title: str = "",
                  hero_image: str = "") -> str:
    today = date.today().isoformat()
    scores = data["scores"]
    jury_score = data["jury_score"]
    verdict = data["verdict"]
    brand_display = brand.capitalize()
    canonical_url = f"https://www.thecarjury.com/reviews/{brand}/{model}/"
    vc = verdict_color(verdict)
    vbg = verdict_bg(verdict)

    def score_bar(label: str, score: float) -> str:
        pct = int(score * 10)
        color = score_color(score)
        return f"""
          <div class="score-row">
            <span class="score-label">{label}</span>
            <div class="score-bar-wrap"><div class="score-bar" style="width:{pct}%;background:{color}"></div></div>
            <span class="score-num" style="color:{color}">{score}</span>
          </div>"""

    score_bars = (
        score_bar("Design", scores["design"]) +
        score_bar("Interior", scores["interior"]) +
        score_bar("Performance", scores["performance"]) +
        score_bar("Ride Quality", scores["ride"]) +
        score_bar("Build Quality", scores["build_quality"]) +
        score_bar("Value for Money", scores["value"])
    )

    pros_html = "\n".join(f'          <li class="pro-item">{p}</li>' for p in data["pros"])
    cons_html = "\n".join(f'          <li class="con-item">{c}</li>' for c in data["cons"])
    consensus_html = "\n".join(f'          <li>{p}</li>' for p in data["consensus_points"])
    disagree_html = "\n".join(f'          <li>{p}</li>' for p in data.get("disagreement_points", []))

    reviewer_cards = "\n".join(
        f'''          <div class="reviewer-card">
            <div class="reviewer-name">{r["name"]}</div>
            <div class="reviewer-channel">{r["channel"]}</div>
            <p class="reviewer-take">"{r["take"]}"</p>
          </div>'''
        for r in data.get("reviewer_takes", [])
    )

    teambhp_take = data.get("teambhp_take", "")
    if teambhp_take and teambhp_url:
        teambhp_block = f"""
  <div class="section">
    <h2>TeamBHP's Take</h2>
    <div class="teambhp-box">
      <div class="teambhp-logo">TeamBHP</div>
      <p class="teambhp-text">{teambhp_take}</p>
      <a class="teambhp-link" href="{teambhp_url}" target="_blank" rel="noopener">Read full forum review →</a>
    </div>
  </div>"""
    elif teambhp_take:
        teambhp_block = f"""
  <div class="section">
    <h2>TeamBHP's Take</h2>
    <div class="teambhp-box">
      <div class="teambhp-logo">TeamBHP</div>
      <p class="teambhp-text">{teambhp_take}</p>
    </div>
  </div>"""
    else:
        teambhp_block = ""

    faq_schema_items = ",\n".join(
        f'{{"@type":"Question","name":{json.dumps(f["q"])},"acceptedAnswer":{{"@type":"Answer","text":{json.dumps(f["a"])}}}}}'
        for f in data["faqs"]
    )
    faq_html = "\n".join(
        f'''          <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
            <div class="faq-q" itemprop="name">{f["q"]}</div>
            <div class="faq-a" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
              <span itemprop="text">{f["a"]}</span>
            </div>
          </div>'''
        for f in data["faqs"]
    )

    video_embeds = "\n".join(
        f'          <iframe class="yt-embed" src="https://www.youtube.com/embed/{vid}" loading="lazy" allowfullscreen title="{car_name} review"></iframe>'
        for vid in video_ids[:3]
        if vid
    )

    meta_description = data.get("meta_description", f"The Car Jury's verdict on the {year} {car_name}.")
    og_title = data.get("og_title", f"{car_name} Review {year} — The Car Jury")
    num_reviewers = len(data.get("reviewer_takes", []))
    if teambhp_take:
        num_reviewers += 1
    sources_label = f"{num_reviewers} independent sources"
    word_count, reading_time = estimate_content_words(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{GA4_SNIPPET}
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{og_title} | The Car Jury</title>
  <meta name="description" content="{meta_description}" />
  <link rel="canonical" href="{canonical_url}" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="The Car Jury" />
  <meta property="og:title" content="{og_title}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:locale" content="en_IN" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{og_title}" />
  <meta name="twitter:description" content="{meta_description}" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "Review",
        "name": "{og_title}",
        "reviewBody": "{data['hero_summary']}",
        "reviewRating": {{"@type": "Rating", "ratingValue": "{jury_score}", "bestRating": "10", "worstRating": "1"}},
        "author": {{"@type": "Organization", "name": "The Car Jury"}},
        "publisher": {{"@type": "Organization", "name": "The Car Jury", "url": "https://www.thecarjury.com"}},
        "datePublished": "{today}",
        "url": "{canonical_url}",
        "itemReviewed": {{
          "@type": "Car",
          "name": "{car_name}",
          "brand": {{"@type": "Brand", "name": "{brand_display}"}},
          "vehicleModelDate": "{year}"
        }}
      }},
      {{
        "@type": "BreadcrumbList",
        "itemListElement": [
          {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.thecarjury.com/"}},
          {{"@type": "ListItem", "position": 2, "name": "Reviews", "item": "https://www.thecarjury.com/reviews/"}},
          {{"@type": "ListItem", "position": 3, "name": "{brand_display}", "item": "https://www.thecarjury.com/reviews/{brand}/"}},
          {{"@type": "ListItem", "position": 4, "name": "{car_name}", "item": "{canonical_url}"}}
        ]
      }},
      {{
        "@type": "FAQPage",
        "mainEntity": [{faq_schema_items}]
      }}
    ]
  }}
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --font-display: "Fraunces", Georgia, serif;
      --font-body:    "Source Serif 4", Charter, Georgia, serif;
      --font-ui:      "Inter", -apple-system, Arial, sans-serif;
      --red:          #C8102E;
      --red-dark:     #A30C24;
      --paper:        #FAF8F5;
      --white:        #FFFFFF;
      --hairline:     #E5E2DC;
      --stone-400:    #9E9A93;
      --stone-600:    #6B6B6B;
      --stone-800:    #3D3D3D;
      --ink:          #1A1A1A;
      --green:        #0E6B3C;
      --green-tint:   #E6F2EC;
      --amber:        #B45309;
      --amber-tint:   #FEF3C7;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--paper); color: var(--ink); font-family: var(--font-ui); -webkit-font-smoothing: antialiased; line-height: 1.7; }}
    a {{ color: var(--red); text-decoration: none; }}
    a:hover {{ color: var(--red-dark); }}

    /* Site Header */
    .site-header {{ background: var(--white); border-bottom: 1px solid var(--hairline); position: sticky; top: 0; z-index: 100; }}
    .site-header__inner {{ max-width: 1100px; margin: 0 auto; padding: 0 32px; height: 64px; display: flex; align-items: center; justify-content: space-between; }}
    .tcj-mast {{ display: inline-flex; align-items: baseline; gap: 6px; text-decoration: none; }}
    .tcj-mast__the {{ font: 700 italic 16px/1 var(--font-display); color: var(--red); }}
    .tcj-mast__name {{ font: 700 24px/1 var(--font-display); color: var(--ink); letter-spacing: -0.02em; }}
    .site-nav {{ display: flex; align-items: center; gap: 28px; }}
    .site-nav a {{ font: 500 14px/1 var(--font-ui); color: var(--stone-600); transition: color 0.15s; }}
    .site-nav a:hover {{ color: var(--ink); }}

    /* Hero banner */
    .hero-banner {{ position: relative; overflow: hidden; background: #EDEDEB; }}
    .hero-banner__img {{ width: 100%; height: 58vh; max-height: 620px; min-height: 280px; object-fit: contain; display: block; }}
    .hero-banner__credit {{ position: absolute; bottom: 8px; right: 12px; font: 500 10px/1 var(--font-ui); color: var(--stone-400); padding: 3px 8px; }}

    /* Verdict header */
    .verdict-header {{ background: var(--white); border-bottom: 1px solid var(--hairline); }}
    .verdict-header__inner {{ max-width: 1100px; margin: 0 auto; padding: 28px 40px 32px; }}
    .verdict-header__kicker {{ font: 600 11px/1 var(--font-ui); letter-spacing: 0.14em; color: var(--red); text-transform: uppercase; margin-bottom: 14px; }}
    .verdict-header__row {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 40px; margin-bottom: 20px; }}
    .verdict-header__title {{ font: 700 clamp(1.7rem,2.8vw,2.6rem)/1.15 var(--font-display); color: var(--ink); letter-spacing: -0.02em; flex: 1; margin-top: 4px; }}
    .verdict-header__score {{ flex-shrink: 0; text-align: center; min-width: 110px; }}
    .verdict-header__score .verdict-badge {{ display: block; margin-bottom: 10px; }}
    .verdict-header__score .jury-score-big {{ display: block; }}
    .verdict-header__score .jury-score-label {{ margin-top: 4px; }}
    .verdict-header__reason {{ font: 400 18px/1.65 var(--font-body); color: var(--stone-800); font-style: italic; border-top: 1px solid var(--hairline); padding-top: 18px; max-width: 820px; margin: 0; }}
    .verdict-badge {{ display: inline-block; padding: 10px 28px; border-radius: 4px; font: 800 14px/1 var(--font-ui); letter-spacing: 0.12em; text-transform: uppercase; color: {vc}; background: {vbg}; border: 1.5px solid {vc}; margin-bottom: 20px; }}
    .jury-score-big {{ font: 700 56px/1 var(--font-display); color: {score_color(jury_score)}; }}
    .jury-score-label {{ font: 600 11px/1 var(--font-ui); color: var(--stone-400); text-transform: uppercase; letter-spacing: 0.12em; margin-top: 6px; }}
    .hero-summary {{ margin: 24px auto 0; font: 400 17px/1.65 var(--font-body); color: var(--stone-800); }}

    /* Article wrap */
    .article-wrap {{ max-width: 760px; margin: 0 auto; padding: 0 24px 100px; }}

    /* Byline */
    .byline {{ padding: 20px 0; border-bottom: 1px solid var(--hairline); color: var(--stone-400); font: 500 12px/1.5 var(--font-ui); display: flex; gap: 20px; flex-wrap: wrap; }}

    /* Scores */
    .scores-section {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 28px 32px; margin: 40px 0; }}
    .scores-section h2 {{ font: 700 18px/1.2 var(--font-display); color: var(--ink); margin-bottom: 24px; }}
    .score-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
    .score-label {{ width: 140px; font: 500 13px/1 var(--font-ui); color: var(--stone-600); flex-shrink: 0; }}
    .score-bar-wrap {{ flex: 1; background: var(--hairline); border-radius: 2px; height: 5px; }}
    .score-bar {{ height: 5px; border-radius: 2px; }}
    .score-num {{ width: 36px; text-align: right; font: 700 14px/1 var(--font-ui); }}

    /* Pros/Cons */
    .pros-cons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 40px 0; }}
    @media (max-width: 600px) {{ .pros-cons {{ grid-template-columns: 1fr; }} }}
    .pros-box, .cons-box {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 24px; }}
    .pros-box h3 {{ font: 700 11px/1 var(--font-ui); color: var(--green); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 16px; }}
    .cons-box h3 {{ font: 700 11px/1 var(--font-ui); color: var(--red); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 16px; }}
    .pro-item, .con-item {{ font: 400 14px/1.5 var(--font-ui); margin-bottom: 10px; padding-left: 22px; position: relative; color: var(--stone-800); }}
    .pro-item::before {{ content: "✓"; position: absolute; left: 0; color: var(--green); font-weight: 700; }}
    .con-item::before {{ content: "✗"; position: absolute; left: 0; color: var(--red); font-weight: 700; }}

    /* Section prose */
    .section {{ margin: 52px 0; }}
    .section h2 {{ font: 700 26px/1.2 var(--font-display); color: var(--ink); letter-spacing: -0.01em; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid var(--red); display: inline-block; }}
    .section p {{ font: 400 17px/1.75 var(--font-body); color: var(--stone-800); margin-bottom: 16px; }}

    /* Consensus */
    .consensus-box {{ background: var(--white); border-left: 3px solid var(--red); padding: 20px 24px; border-radius: 0 8px 8px 0; margin: 24px 0; }}
    .consensus-box h3 {{ font: 700 11px/1 var(--font-ui); color: var(--red); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 12px; }}
    .consensus-box ul {{ list-style: none; }}
    .consensus-box li {{ padding: 6px 0 6px 20px; position: relative; font: 400 15px/1.5 var(--font-body); color: var(--stone-800); }}
    .consensus-box li::before {{ content: "→"; position: absolute; left: 0; color: var(--red); font-weight: 600; }}
    .disagree-box {{ border-left-color: var(--stone-400); }}
    .disagree-box h3 {{ color: var(--stone-600); }}
    .disagree-box li::before {{ color: var(--stone-400); }}

    /* TeamBHP box */
    .teambhp-box {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 24px; }}
    .teambhp-logo {{ font: 700 13px/1 var(--font-ui); color: var(--stone-600); background: var(--hairline); display: inline-block; padding: 4px 10px; border-radius: 3px; margin-bottom: 14px; letter-spacing: 0.05em; }}
    .teambhp-text {{ font: 400 16px/1.65 var(--font-body); color: var(--stone-800); margin-bottom: 14px; font-style: italic; }}
    .teambhp-link {{ font: 600 13px/1 var(--font-ui); color: var(--red); }}

    /* Reviewer cards */
    .reviewer-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin: 24px 0; }}
    .reviewer-card {{ background: var(--white); border: 1px solid var(--hairline); border-radius: 8px; padding: 18px 20px; }}
    .reviewer-name {{ font: 700 14px/1.3 var(--font-ui); color: var(--ink); margin-bottom: 2px; }}
    .reviewer-channel {{ font: 500 12px/1 var(--font-ui); color: var(--red); margin-bottom: 10px; }}
    .reviewer-take {{ font: 400 13px/1.55 var(--font-body); color: var(--stone-600); font-style: italic; }}

    /* FAQ */
    .faq-section {{ margin: 52px 0; }}
    .faq-section h2 {{ font: 700 26px/1.2 var(--font-display); color: var(--ink); letter-spacing: -0.01em; margin-bottom: 24px; }}
    .faq-item {{ border-bottom: 1px solid var(--hairline); padding: 16px 0; }}
    .faq-q {{ font: 600 15px/1.4 var(--font-ui); color: var(--ink); margin-bottom: 8px; }}
    .faq-a {{ font: 400 14px/1.6 var(--font-body); color: var(--stone-600); }}

    /* YouTube embeds */
    .yt-embed {{ width: 100%; aspect-ratio: 16/9; border: none; border-radius: 8px; margin-bottom: 16px; }}

    /* Breadcrumb */
    .breadcrumb {{ margin-top: 48px; font: 500 12px/1.5 var(--font-ui); color: var(--stone-400); }}
    .breadcrumb a {{ color: var(--stone-400); }}
    .breadcrumb a:hover {{ color: var(--red); }}

    /* Site Footer */
    .site-footer {{ background: var(--white); border-top: 1px solid var(--hairline); padding: 48px 32px; margin-top: 60px; }}
    .site-footer__inner {{ max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }}
    .site-footer__top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 32px; }}
    .site-footer__tagline {{ font: 500 13px/1.5 var(--font-ui); color: var(--stone-600); margin-top: 8px; max-width: 280px; }}
    .site-footer__links {{ display: flex; gap: 24px; flex-wrap: wrap; }}
    .site-footer__links a {{ font: 500 13px/1 var(--font-ui); color: var(--stone-600); }}
    .site-footer__links a:hover {{ color: var(--red); }}
    .site-footer__bottom {{ font: 500 12px/1.5 var(--font-ui); color: var(--stone-400); border-top: 1px solid var(--hairline); padding-top: 24px; }}

    @media (max-width: 900px) {{
      .hero-banner__img {{ height: 54vw; max-height: 420px; }}
      .verdict-header__inner {{ padding: 24px 20px 28px; }}
      .verdict-header__row {{ gap: 20px; }}
    }}
    @media (max-width: 600px) {{
      .verdict-header__row {{ flex-direction: column; gap: 12px; }}
      .verdict-header__score {{ text-align: left; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
      .verdict-header__score .verdict-badge {{ margin-bottom: 0; }}
      .verdict-header__score .jury-score-big {{ font-size: 38px; }}
      .verdict-header__score .jury-score-label {{ font-size: 10px; }}
      .verdict-header__reason {{ font-size: 16px; }}
    }}
    @media (max-width: 768px) {{
      .site-header__inner {{ padding: 0 20px; }}
      .site-nav a {{ display: none; }}
      .article-wrap {{ padding: 0 20px 80px; }}
      .scores-section {{ padding: 20px; }}
      .score-label {{ width: 110px; font-size: 12px; }}
      .site-footer {{ padding: 32px 20px; }}
      .site-footer__top {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>

<header class="site-header">
  <div class="site-header__inner">
    <a href="/" class="tcj-mast">
      <span class="tcj-mast__the">The</span>
      <span class="tcj-mast__name">Car Jury</span>
    </a>
    <nav class="site-nav">
      <a href="/reviews/" style="color:var(--ink);font-weight:600">Reviews</a>
      <a href="/compare/">Compare</a>
      <a href="/best/">Best Lists</a>
      <a href="/influencers/">Influencers</a>
      <a href="/about/">About</a>
    </nav>
  </div>
</header>

{f'''<div class="hero-banner">
<img class="hero-banner__img" src="{hero_image}" alt="{car_name} official press image" width="1529" height="911" loading="eager" />
<span class="hero-banner__credit">Image: {brand_display} press kit</span>
</div>''' if hero_image else ''}
<div class="verdict-header">
<div class="verdict-header__inner">
  <div class="verdict-header__kicker">The Car Jury Verdict · {year}</div>
  <div class="verdict-header__row">
    <h1 class="verdict-header__title">{car_name}: The Jury's Verdict</h1>
    <div class="verdict-header__score">
      <div class="verdict-badge">{verdict}</div>
      <div class="jury-score-big">{jury_score}</div>
      <div class="jury-score-label">Jury Score / 10</div>
    </div>
  </div>
  <p class="verdict-header__reason">{data['verdict_reason']}</p>
</div>
</div>

<div class="article-wrap">

  <div class="byline">
    <span>By The Car Jury Editorial</span>
    <span>Published {today}</span>
    <span>Synthesis of {sources_label}</span>
    <span>{word_count:,} words · {reading_time} min read</span>
  </div>
  <p class="hero-summary">{data['hero_summary']}</p>

  <div class="scores-section">
    <h2>Jury Score Breakdown</h2>
    {score_bars}
  </div>

  <div class="pros-cons">
    <div class="pros-box">
      <h3>What Works</h3>
      <ul>{pros_html}</ul>
    </div>
    <div class="cons-box">
      <h3>Watch Out For</h3>
      <ul>{cons_html}</ul>
    </div>
  </div>

  <div class="section">
    <h2>Design</h2>
    <p>{data['design_review']}</p>
  </div>

  <div class="section">
    <h2>Interior &amp; Features</h2>
    <p>{data['interior_review']}</p>
  </div>

  <div class="section">
    <h2>Performance &amp; Powertrain</h2>
    <p>{data['performance_review']}</p>
  </div>

  <div class="section">
    <h2>Ride Quality &amp; Handling</h2>
    <p>{data['ride_review']}</p>
  </div>

  <div class="section">
    <h2>Build Quality &amp; Technology</h2>
    <p>{data['build_quality_review']}</p>
  </div>

  <div class="section">
    <h2>Price &amp; Value</h2>
    <p>{data['value_review']}</p>
  </div>

  <div class="section">
    <h2>What India's Reviewers Agree On</h2>
    <div class="consensus-box">
      <h3>Consensus</h3>
      <ul>{consensus_html}</ul>
    </div>
    {f'<div class="consensus-box disagree-box" style="margin-top:16px"><h3>Points of Disagreement</h3><ul>{disagree_html}</ul></div>' if disagree_html.strip() else ''}
  </div>

{teambhp_block}

  <div class="section">
    <h2>Individual Reviewer Verdicts</h2>
    <div class="reviewer-grid">
      {reviewer_cards}
    </div>
  </div>

  {f'<div class="section"><h2>Watch the Reviews</h2>{video_embeds}</div>' if video_embeds else ''}

  <div class="faq-section" itemscope itemtype="https://schema.org/FAQPage">
    <h2>Frequently Asked Questions</h2>
    {faq_html}
  </div>

  <nav class="breadcrumb" aria-label="breadcrumb">
    <a href="/">Home</a> → <a href="/reviews/">Reviews</a> → <a href="/reviews/{brand}/">{brand_display}</a> → {car_name}
  </nav>

</div>

<footer class="site-footer">
  <div class="site-footer__inner">
    <div class="site-footer__top">
      <div>
        <a href="/" class="tcj-mast">
          <span class="tcj-mast__the">The</span>
          <span class="tcj-mast__name">Car Jury</span>
        </a>
        <p class="site-footer__tagline">We watch every expert so you don't have to. One clear verdict on every car.</p>
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
      © {date.today().year} The Car Jury · No sponsored reviews · No manufacturer relationships · India's aggregated car reviews
    </div>
  </div>
</footer>

</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a Car Jury review article")
    parser.add_argument("--brand", help="Brand slug e.g. tata")
    parser.add_argument("--model", help="Model slug e.g. nexon-ev")
    parser.add_argument("--name", help="Display name e.g. 'Tata Nexon EV'")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--videos", nargs="+", default=[], help="YouTube video IDs")
    parser.add_argument("--from-research", metavar="JSON_PATH",
                        help="Load video IDs and TeamBHP from a research_agent state JSON")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files or push")
    args = parser.parse_args()

    teambhp_content = ""
    teambhp_url = ""
    teambhp_title = ""

    if args.from_research:
        research = json.loads(Path(args.from_research).read_text())
        if not args.brand:
            args.brand = research["brand"]
        if not args.model:
            args.model = research["model"]
        if not args.name:
            args.name = research["car_name"]
        if not args.year:
            args.year = research.get("year", 2025)
        if not args.videos:
            args.videos = [
                v["id"] for v in research.get("videos", [])
                if v.get("transcript_available", True)
            ]
        tb = research.get("teambhp", {})
        if tb.get("found"):
            teambhp_content = tb.get("first_post", "")
            teambhp_url = tb.get("url", "")
            teambhp_title = tb.get("title", "")

    if not args.brand or not args.model or not args.name:
        parser.error("Provide --brand, --model, --name (or --from-research)")

    print(f"\n The Car Jury — Generating review for {args.name} ({args.year})")
    print(f"  Videos: {args.videos or 'none'}")
    if teambhp_url:
        print(f"  TeamBHP: {teambhp_url}")

    # 1. Fetch transcripts
    transcripts = {}
    for vid in args.videos:
        print(f"\n  Fetching transcript: {vid}")
        title, author = fetch_video_title(vid)
        text = fetch_transcript(vid)
        if text:
            key = author or vid
            transcripts[key] = text
            print(f"    {len(text):,} chars from {author or vid}")
        else:
            print(f"    No transcript available")

    if not transcripts:
        print("  No transcripts found. Aborting — need at least one transcript.")
        sys.exit(1)

    # 2. Synthesise
    print(f"\n  Synthesising with Claude ({len(transcripts)} reviewers{' + TeamBHP' if teambhp_content else ''})...")
    data = synthesise_with_claude(args.name, args.year, transcripts, teambhp_content)
    print(f"  Jury score: {data['jury_score']} | Verdict: {data['verdict']}")

    # 3. Generate HTML — check for hero image in review folder
    out_dir = CARJURY / "reviews" / args.brand / args.model
    hero_image = ""
    for ext in ["hero.jpg", "hero.png", "hero.webp"]:
        if (out_dir / ext).exists():
            hero_image = f"/reviews/{args.brand}/{args.model}/{ext}"
            break

    html = generate_html(
        args.brand, args.model, args.name, args.year,
        data, args.videos, teambhp_url, teambhp_title, hero_image
    )

    if args.dry_run:
        print("\n  [dry-run] Skipping file write and push.")
        return

    # 4. Write file
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html)
    print(f"\n  Written: {out_file}")
    # Word count guard
    import re as _re
    _text = _re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=_re.DOTALL)
    _text = _re.sub(r'<script[^>]*>.*?</script>', ' ', _text, flags=_re.DOTALL)
    _text = _re.sub(r'<[^>]+>', ' ', _text)
    _wc = len([w for w in _text.split() if len(w) > 1])
    if _wc > 2000:
        print(f"  ⚠️  Word count {_wc} exceeds 2000 limit — review the content or tighten the prompt.")
    else:
        print(f"  ✓  Word count: {_wc} words (under 2000 limit)")

    # 5. Sync new reviewers into influencers.json + master_list.md
    sync_influencers(args.brand, args.model, data.get("reviewer_takes", []))

    # 6. Update sitemap + llms.txt + influencer pages
    sys.path.insert(0, str(ROOT / "agents"))
    import carjury_manager
    carjury_manager.update_sitemap()
    carjury_manager.update_llms_txt()
    carjury_manager.update_reviews_index()
    sys.path.insert(0, str(ROOT / "carjury/tools"))
    import generate_influencer_pages
    generate_influencer_pages.build_all()

    # 7. Git push
    pushed = carjury_manager.git_push(
        f"review: {args.name} ({args.year}) — jury score {data['jury_score']}"
    )
    if pushed:
        print(f"  Deployed to Cloudflare Pages via GitHub push.")

    print(f"\n  Done! Live at: https://www.thecarjury.com/reviews/{args.brand}/{args.model}/\n")

    # 8. Record publish date for Analytics Agent tracking
    try:
        sys.path.insert(0, str(ROOT / "agents" / "carjury"))
        from analytics_agent import record_publish
        record_publish(args.brand, args.model)
    except Exception as e:
        print(f"  [warn] Could not record publish date: {e}")

    # 9. Auto-run all agents after publish
    print("  Running agent suite...\n")
    try:
        from run_agents import run_all
        run_all(args.brand, args.model)
    except Exception as e:
        print(f"  [warn] Agent suite failed: {e}")


if __name__ == "__main__":
    main()

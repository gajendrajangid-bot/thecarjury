#!/usr/bin/env python3
"""
The Car Jury — Review Generator
Usage: python3 generate_review.py --brand tata --model nexon-ev --name "Tata Nexon EV" --year 2025 --videos VIDEO_ID1 VIDEO_ID2 ...
Fetches YouTube transcripts, synthesises via Claude, generates review HTML, updates sitemap + llms.txt.
"""

from __future__ import annotations
import argparse, os, sys, json, re, subprocess
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
CARJURY = ROOT / "carjury"
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
        transcript = api.fetch(video_id)
        return " ".join(t.text for t in transcript)
    except Exception as e:
        print(f"  [warn] Transcript failed for {video_id}: {e}")
        return ""


def fetch_video_title(video_id: str) -> str:
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

Your job: synthesise the transcripts from multiple YouTube reviewers into a single, comprehensive, structured car review article.

RULES:
- Be completely neutral. No manufacturer bias.
- Use specific facts, quotes, and numbers from the transcripts.
- Identify CONSENSUS (what most reviewers agree on) and DISAGREEMENTS.
- Use Indian context: prices in INR, Indian road conditions, Indian buyers' concerns.
- Write for both human readers AND AI search engines (GEO-optimised).
- Every claim must be supportable from the transcripts.
- Never make up specs or prices — only use what's in the transcripts.

CAR: {car_name} ({year})
REVIEWERS: {reviewer_list}

TRANSCRIPTS:
{transcripts}

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


def synthesise_with_claude(car_name: str, year: int, transcripts: dict[str, str]) -> dict:
    import anthropic

    reviewer_list = ", ".join(transcripts.keys())
    combined = "\n\n---\n\n".join(
        f"REVIEWER: {name}\n{text[:15000]}"  # cap per reviewer
        for name, text in transcripts.items()
        if text
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": SYNTHESIS_PROMPT.format(
                car_name=car_name,
                year=year,
                reviewer_list=reviewer_list,
                transcripts=combined,
            )
        }]
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ── HTML Generator ─────────────────────────────────────────────────────────────

def score_color(score: float) -> str:
    if score >= 8.0:
        return "#27ae60"
    if score >= 7.0:
        return "#f39c12"
    return "#e74c3c"


def verdict_color(verdict: str) -> str:
    return {"BUY": "#27ae60", "WAIT": "#f39c12", "SKIP": "#e74c3c"}.get(verdict, "#666")


def generate_html(brand: str, model: str, car_name: str, year: int,
                  data: dict, video_ids: list[str]) -> str:
    today = date.today().isoformat()
    scores = data["scores"]
    jury_score = data["jury_score"]
    verdict = data["verdict"]
    brand_display = brand.capitalize()
    canonical_url = f"https://www.thecarjury.com/reviews/{brand}/{model}/"

    # Score bars
    def score_bar(label: str, score: float) -> str:
        pct = int(score * 10)
        color = score_color(score)
        return f"""
          <div class="score-row">
            <span class="score-label">{label}</span>
            <div class="score-bar-wrap">
              <div class="score-bar" style="width:{pct}%;background:{color}"></div>
            </div>
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

    # Pros / cons
    pros_html = "\n".join(f'          <li class="pro-item">{p}</li>' for p in data["pros"])
    cons_html = "\n".join(f'          <li class="con-item">{c}</li>' for c in data["cons"])

    # Consensus
    consensus_html = "\n".join(f'          <li>{p}</li>' for p in data["consensus_points"])
    disagree_html = "\n".join(f'          <li>{p}</li>' for p in data.get("disagreement_points", []))

    # Reviewer takes
    reviewer_cards = "\n".join(
        f'''          <div class="reviewer-card">
            <div class="reviewer-name">{r["name"]}</div>
            <div class="reviewer-channel">{r["channel"]}</div>
            <p class="reviewer-take">"{r["take"]}"</p>
          </div>'''
        for r in data.get("reviewer_takes", [])
    )

    # FAQ schema + HTML
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

    # Video embeds
    video_embeds = "\n".join(
        f'          <iframe class="yt-embed" src="https://www.youtube.com/embed/{vid}" loading="lazy" allowfullscreen title="{car_name} review"></iframe>'
        for vid in video_ids[:3]
        if vid
    )

    meta_description = data.get("meta_description", f"Read The Car Jury's verdict on the {year} {car_name}.")
    og_title = data.get("og_title", f"{car_name} Review {year} — The Car Jury")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{og_title} | The Car Jury</title>
  <meta name="description" content="{meta_description}" />
  <link rel="canonical" href="{canonical_url}" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />

  <!-- Open Graph -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="The Car Jury" />
  <meta property="og:title" content="{og_title}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:locale" content="en_IN" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{og_title}" />
  <meta name="twitter:description" content="{meta_description}" />

  <!-- Schema: Review + Car + BreadcrumbList + FAQ -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "Review",
        "name": "{og_title}",
        "reviewBody": "{data['hero_summary']}",
        "reviewRating": {{
          "@type": "Rating",
          "ratingValue": "{jury_score}",
          "bestRating": "10",
          "worstRating": "1"
        }},
        "author": {{"@type": "Organization", "name": "The Car Jury"}},
        "publisher": {{"@type": "Organization", "name": "The Car Jury", "url": "https://www.thecarjury.com"}},
        "datePublished": "{today}",
        "url": "{canonical_url}",
        "itemReviewed": {{
          "@type": "Car",
          "name": "{car_name}",
          "brand": {{"@type": "Brand", "name": "{brand_display}"}},
          "model": "{car_name}",
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
        "mainEntity": [
          {faq_schema_items}
        ]
      }}
    ]
  }}
  </script>

  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e8e8e8; line-height: 1.7; }}
    a {{ color: #D4A017; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* Nav */
    nav {{ background: #111; border-bottom: 1px solid #222; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 56px; position: sticky; top: 0; z-index: 100; }}
    .nav-logo {{ font-family: Georgia, serif; font-size: 1.1rem; font-weight: bold; color: #D4A017; }}
    .nav-links {{ display: flex; gap: 24px; font-size: 0.85rem; color: #999; }}
    .nav-links a {{ color: #999; }}

    /* Hero verdict */
    .verdict-hero {{ background: linear-gradient(135deg, #111 0%, #1a1a1a 100%); border-bottom: 3px solid #D4A017; padding: 48px 24px 40px; text-align: center; }}
    .verdict-hero .car-label {{ font-size: 0.8rem; color: #D4A017; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 12px; }}
    .verdict-hero h1 {{ font-family: Georgia, serif; font-size: clamp(1.8rem, 5vw, 2.8rem); color: #fff; margin-bottom: 16px; max-width: 700px; margin-left: auto; margin-right: auto; }}
    .verdict-badge {{ display: inline-block; padding: 10px 28px; border-radius: 4px; font-weight: 800; font-size: 1.1rem; letter-spacing: 0.1em; color: #fff; background: {verdict_color(verdict)}; margin-bottom: 20px; }}
    .verdict-reason {{ color: #bbb; max-width: 560px; margin: 0 auto 24px; font-size: 1rem; }}
    .jury-score-big {{ font-family: Georgia, serif; font-size: 4rem; font-weight: bold; color: {score_color(jury_score)}; line-height: 1; }}
    .jury-score-label {{ font-size: 0.75rem; color: #777; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }}
    .hero-summary {{ max-width: 680px; margin: 24px auto 0; color: #ccc; font-size: 1.05rem; }}

    /* Content wrapper */
    .article-wrap {{ max-width: 760px; margin: 0 auto; padding: 0 20px 80px; }}

    /* Byline */
    .byline {{ padding: 20px 0; border-bottom: 1px solid #222; color: #666; font-size: 0.82rem; display: flex; gap: 16px; flex-wrap: wrap; }}

    /* Scores */
    .scores-section {{ background: #141414; border: 1px solid #222; border-radius: 8px; padding: 28px; margin: 40px 0; }}
    .scores-section h2 {{ font-family: Georgia, serif; color: #D4A017; font-size: 1.1rem; margin-bottom: 24px; }}
    .score-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
    .score-label {{ width: 130px; font-size: 0.85rem; color: #999; flex-shrink: 0; }}
    .score-bar-wrap {{ flex: 1; background: #222; border-radius: 2px; height: 6px; }}
    .score-bar {{ height: 6px; border-radius: 2px; transition: width 0.3s; }}
    .score-num {{ width: 32px; text-align: right; font-weight: 700; font-size: 0.9rem; }}

    /* Pros/Cons */
    .pros-cons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 40px 0; }}
    @media (max-width: 600px) {{ .pros-cons {{ grid-template-columns: 1fr; }} }}
    .pros-box, .cons-box {{ background: #141414; border: 1px solid #222; border-radius: 8px; padding: 24px; }}
    .pros-box h3 {{ color: #27ae60; margin-bottom: 16px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .cons-box h3 {{ color: #e74c3c; margin-bottom: 16px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .pro-item, .con-item {{ font-size: 0.9rem; margin-bottom: 10px; padding-left: 20px; position: relative; color: #ccc; }}
    .pro-item::before {{ content: "✓"; position: absolute; left: 0; color: #27ae60; font-weight: bold; }}
    .con-item::before {{ content: "✗"; position: absolute; left: 0; color: #e74c3c; font-weight: bold; }}

    /* Sections */
    .section {{ margin: 48px 0; }}
    .section h2 {{ font-family: Georgia, serif; font-size: 1.5rem; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #D4A017; display: inline-block; }}
    .section p {{ color: #ccc; margin-bottom: 16px; }}

    /* Consensus */
    .consensus-box {{ background: #141414; border-left: 3px solid #D4A017; padding: 20px 24px; border-radius: 0 8px 8px 0; margin: 24px 0; }}
    .consensus-box h3 {{ color: #D4A017; margin-bottom: 12px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .consensus-box ul {{ list-style: none; }}
    .consensus-box li {{ padding: 6px 0 6px 20px; position: relative; color: #ccc; font-size: 0.92rem; }}
    .consensus-box li::before {{ content: "→"; position: absolute; left: 0; color: #D4A017; }}

    /* Reviewer takes */
    .reviewer-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; margin: 24px 0; }}
    .reviewer-card {{ background: #141414; border: 1px solid #222; border-radius: 8px; padding: 20px; }}
    .reviewer-name {{ font-weight: 700; color: #fff; font-size: 0.9rem; }}
    .reviewer-channel {{ color: #D4A017; font-size: 0.75rem; margin-bottom: 10px; }}
    .reviewer-take {{ color: #bbb; font-size: 0.85rem; font-style: italic; line-height: 1.5; }}

    /* FAQ */
    .faq-section {{ margin: 48px 0; }}
    .faq-section h2 {{ font-family: Georgia, serif; font-size: 1.5rem; color: #fff; margin-bottom: 24px; }}
    .faq-item {{ border-bottom: 1px solid #1e1e1e; padding: 16px 0; }}
    .faq-q {{ font-weight: 600; color: #e8e8e8; margin-bottom: 8px; cursor: pointer; }}
    .faq-a {{ color: #aaa; font-size: 0.92rem; }}

    /* YT embeds */
    .yt-embed {{ width: 100%; aspect-ratio: 16/9; border: none; border-radius: 8px; margin-bottom: 16px; }}

    /* Footer */
    footer {{ background: #0d0d0d; border-top: 1px solid #1e1e1e; padding: 32px 24px; text-align: center; color: #555; font-size: 0.8rem; }}
    footer a {{ color: #666; }}

    @media (max-width: 480px) {{
      .score-label {{ width: 100px; font-size: 0.78rem; }}
      .nav-links {{ display: none; }}
    }}
  </style>
</head>
<body>

<nav>
  <a class="nav-logo" href="/">The Car Jury</a>
  <div class="nav-links">
    <a href="/reviews/">Reviews</a>
    <a href="/compare/">Compare</a>
    <a href="/best/">Best Lists</a>
  </div>
</nav>

<div class="verdict-hero">
  <div class="car-label">The Car Jury Verdict · {year}</div>
  <h1>{car_name} Review — Should You Buy It?</h1>
  <div class="verdict-badge">{verdict}</div>
  <p class="verdict-reason">{data['verdict_reason']}</p>
  <div class="jury-score-big">{jury_score}</div>
  <div class="jury-score-label">Jury Score / 10</div>
  <p class="hero-summary">{data['hero_summary']}</p>
</div>

<div class="article-wrap">

  <div class="byline">
    <span>By The Car Jury Editorial</span>
    <span>Published {today}</span>
    <span>Synthesis of {len(data.get('reviewer_takes', []))} independent reviewers</span>
  </div>

  <!-- Jury Scores -->
  <div class="scores-section">
    <h2>Jury Score Breakdown</h2>
    {score_bars}
  </div>

  <!-- Pros & Cons -->
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

  <!-- Design -->
  <div class="section">
    <h2>Design</h2>
    <p>{data['design_review']}</p>
  </div>

  <!-- Interior -->
  <div class="section">
    <h2>Interior & Features</h2>
    <p>{data['interior_review']}</p>
  </div>

  <!-- Performance -->
  <div class="section">
    <h2>Performance & Powertrain</h2>
    <p>{data['performance_review']}</p>
  </div>

  <!-- Ride -->
  <div class="section">
    <h2>Ride Quality & Handling</h2>
    <p>{data['ride_review']}</p>
  </div>

  <!-- Build Quality -->
  <div class="section">
    <h2>Build Quality & Technology</h2>
    <p>{data['build_quality_review']}</p>
  </div>

  <!-- Value -->
  <div class="section">
    <h2>Price & Value</h2>
    <p>{data['value_review']}</p>
  </div>

  <!-- Consensus -->
  <div class="section">
    <h2>What India's Reviewers Agree On</h2>
    <div class="consensus-box">
      <h3>Consensus</h3>
      <ul>{consensus_html}</ul>
    </div>
    {f'<div class="consensus-box" style="border-color:#e74c3c;margin-top:16px"><h3 style="color:#e74c3c">Points of Disagreement</h3><ul>{disagree_html}</ul></div>' if disagree_html.strip() else ''}
  </div>

  <!-- Reviewer Takes -->
  <div class="section">
    <h2>Individual Reviewer Verdicts</h2>
    <div class="reviewer-grid">
      {reviewer_cards}
    </div>
  </div>

  <!-- Videos -->
  {f'<div class="section"><h2>Watch the Reviews</h2>{video_embeds}</div>' if video_embeds else ''}

  <!-- FAQ -->
  <div class="faq-section" itemscope itemtype="https://schema.org/FAQPage">
    <h2>Frequently Asked Questions</h2>
    {faq_html}
  </div>

  <!-- Breadcrumb nav -->
  <nav aria-label="breadcrumb" style="margin-top:48px;font-size:0.8rem;color:#555">
    <a href="/">Home</a> → <a href="/reviews/">Reviews</a> → <a href="/reviews/{brand}/">{brand_display}</a> → {car_name}
  </nav>

</div>

<footer>
  <p>© {date.today().year} The Car Jury · <a href="/">Home</a> · <a href="/reviews/">All Reviews</a> · <a href="mailto:hello@thecarjury.com">Contact</a></p>
  <p style="margin-top:8px">No manufacturer relationships. No sponsored content. Just the jury's verdict.</p>
</footer>

</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a Car Jury review article")
    parser.add_argument("--brand", required=True, help="Brand slug e.g. tata")
    parser.add_argument("--model", required=True, help="Model slug e.g. nexon-ev")
    parser.add_argument("--name", required=True, help="Display name e.g. 'Tata Nexon EV'")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--videos", nargs="+", default=[], help="YouTube video IDs")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    args = parser.parse_args()

    print(f"\n The Car Jury — Generating review for {args.name} ({args.year})")
    print(f"  Videos: {args.videos or 'none'}\n")

    # 1. Fetch transcripts
    transcripts = {}
    for vid in args.videos:
        print(f"  Fetching transcript: {vid}")
        title, author = fetch_video_title(vid)
        text = fetch_transcript(vid)
        if text:
            key = author or vid
            transcripts[key] = text
            print(f"    Got {len(text):,} chars from {author or vid}")

    if not transcripts:
        print("  No transcripts found. Using placeholder synthesis.")
        transcripts["Sample Reviewer"] = f"This is the {args.name}, one of the most anticipated cars of {args.year} in India."

    # 2. Synthesise
    print("\n  Synthesising with Claude...")
    data = synthesise_with_claude(args.name, args.year, transcripts)
    print(f"  Jury score: {data['jury_score']} | Verdict: {data['verdict']}")

    # 3. Generate HTML
    html = generate_html(args.brand, args.model, args.name, args.year, data, args.videos)

    if args.dry_run:
        print("\n  [dry-run] Would write HTML. Skipping file write.")
        return

    # 4. Write file
    out_dir = CARJURY / "reviews" / args.brand / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html)
    print(f"\n  Written: {out_file}")

    # 5. Update sitemap + llms.txt via manager
    sys.path.insert(0, str(ROOT / "agents"))
    import carjury_manager
    carjury_manager.update_sitemap()
    carjury_manager.update_llms_txt()
    carjury_manager.update_reviews_index()

    # 6. Git push
    pushed = carjury_manager.git_push(
        f"review: {args.name} ({args.year}) — jury score {data['jury_score']}"
    )
    if pushed:
        print(f"  Deployed to Netlify via GitHub push.")

    print(f"\n  Done! Live at: https://www.thecarjury.com/reviews/{args.brand}/{args.model}/\n")


if __name__ == "__main__":
    main()

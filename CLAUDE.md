# The Car Jury — Claude Code Instructions
> Claude Code reads this file automatically on every session. Keep it as the single source of truth for how to work on this repo.

---

## ⚡ ON SESSION START — implement these changes automatically

When Claude Code opens this project, check whether the following 5 interlinking changes have been implemented. For each one that is missing, implement it immediately without asking for confirmation. Work through them in order.

### Check 1 — `tools/generate_review.py`

Look for a function called `get_link_context`. If it does not exist:
1. Add the `get_link_context(brand, model)` function from the "Agent modification guide" section below
2. Find the line where `SYNTHESIS_PROMPT` is constructed or where the Claude API is called
3. Call `get_link_context(brand, model)` before that call, and inject the result as a JSON block into the prompt with this instruction appended to the system prompt:

```
You have been given an interlinking context JSON block above. You MUST render the "Also in the running" HTML component immediately before the jury credits section. Use the exact HTML structure from the CLAUDE.md template. Use the display names, scores, and verdicts from the JSON. Include all segment_peers and brand_siblings as related-card entries. Include all compare_pages as related-compare links.
```

### Check 2 — `tools/qa_agent.py` (or `run_agents.py`)

Look for a function called `check_interlinking`. If it does not exist:
1. Add the `check_interlinking(html_content, brand_slug, model_slug)` function from `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 2`
2. Call it after the existing content QA checks
3. If it returns False, raise an exception or return a failure status that prevents publishing

### Check 3 — `tools/tech_seo_agent.py`

Look for a function called `detect_orphan_pages`. If it does not exist:
1. Add the `detect_orphan_pages(site_root)` function from `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 4`
2. Call it at the end of the existing tech SEO pass
3. Log any orphan findings as warnings to Slack (do not block publishing)

### Check 4 — `tools/editorial_agent.py`

Look for an "Update Sweep" block or a function that identifies existing pages needing to link to a newly published car. If it does not exist:
1. Add the Update Sweep task from `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 3`
2. Run it after the existing cluster analysis
3. Post the list of pages needing updates to Slack alongside the existing report

### Check 5 — `tools/carjury_manager.py`

Look for a function called `refresh_compare_pages_in_segments`. If it does not exist:
1. Add the function from `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 5`
2. Call it as Step 4b — after content rebuilds, before the sitemap regeneration step

### Check 6 — Inline contextual links (Type D) on existing pages

Look for `inject_inline_links` in `tools/generate_review.py`. If it exists (already wired for future articles), also run a one-time back-fill pass on all existing review pages:

For each `reviews/[brand]/[model]/index.html`:
1. Load `tools/segments.json → display_names` to get all car name → URL mappings
2. Scan `.section p` tags and `.faq-a` divs for the first mention of each rival car name that is NOT already inside an `<a>` tag
3. Wrap that first mention with `<a href="/reviews/brand/model/">Car Name</a>`
4. Never link the same car twice per page, never link in headings, never self-link

### Check 7 — Influencer first-mention links (Type E) on all pages

Look for `check_duplicate_influencer_links` in `agents/carjury/qa_agent.py`. If it does not exist, add it (see Interlinking Strategy → Type E rule above). Then run a site-wide dedup pass:

1. For each review page: verify `seo_agent.py → _add_interlinking()` pre-populates `linked_urls` from existing article links before the paragraph scan (already implemented — confirm the pre-population block exists).
2. For each compare page: verify `generate_compare.py → render_sources_col()` accepts a `seen` set and threads it across both car columns (already implemented — confirm).
3. For any page where an influencer URL appears more than once as a `<a href="/influencers/...">`, strip all but the first occurrence (keep the first link, replace subsequent ones with plain text).

After implementing all 7 checks, report a summary: which files were modified, what was added, and confirm that `get_link_context` and `inject_inline_links` are both wired into `generate_review.py` correctly by running a dry-run import check.

---

## ⚡ ON SESSION START — fix existing HTML pages (one-time pass)

After completing the 5 Python agent checks above, run this second pass on the existing HTML pages. These are known interlinking gaps from the site audit. Each fix is **additive only** — only add `<a>` tags, never touch scores, schema, copy, or canonicals.

Work through all checks below. For each one, read the relevant HTML file(s) first, then apply the fix.

### HTML Check 1 — Homepage (`index.html`)

The homepage currently has zero followed links to any content page. This is the single biggest structural gap.

Add a minimum of 8 followed internal links to the homepage. Specifically:
- Link to the 3 highest-scored reviews: `/reviews/mahindra/thar-roxx/`, `/reviews/mahindra/be6/`, `/reviews/mahindra/scorpio-n/`
- Link to the 3 most-searched segments using the segment index pattern: one EV review, one mid-SUV review, one premium SUV review — pick the highest-scoring car from `tools/segments.json → jury_scores` in each segment
- Link to 2 compare pages: `/compare/creta-vs-seltos/` and `/compare/be6-vs-nexon-ev/`

Place these links inside existing content sections (hero, featured, or editorial section) — do not create a new section if a natural placement exists. If the homepage has no content section suitable for editorial links, add a minimal `<div class="featured-verdicts">` section before the closing `</main>` tag.

### HTML Check 2 — Rescue orphan compare page

`/compare/creta-electric-vs-e-vitara/` currently has zero inbound links — it is a complete orphan.

Fix by adding a Type C compare link to it in two review pages:
1. `reviews/hyundai/creta-electric/index.html` — add a link to `/compare/creta-electric-vs-e-vitara/` inside the existing `related-compares` block, or immediately before the jury credits section if no such block exists
2. `reviews/maruti/e-vitara/index.html` — same as above

Link text format: `Creta Electric vs e-Vitara →`

### HTML Check 3 — 301 redirect for duplicate compare page

`/compare/creta-vs-duster/index-v2.html` is a duplicate. Add a meta redirect at the top of its `<head>`:

```html
<meta http-equiv="refresh" content="0; url=/compare/creta-vs-duster/">
```

Also add inside `<head>`:
```html
<link rel="canonical" href="https://www.thecarjury.com/compare/creta-vs-duster/">
```

### HTML Check 4 — Add "Also in the running" to under-linked review pages

The following 8 review pages have zero links to other specific reviews. For each one, read the file, build the "Also in the running" component using data from `tools/segments.json`, and insert it immediately before the jury credits section.

Pages to fix and their segment peers (from segments.json):

| Review page | Segment | Segment peers to link | Brand siblings to link | Compare pages |
|---|---|---|---|---|
| `reviews/tata/harrier-ev/index.html` | premium-ev | mahindra/be6, mahindra/xev-9e | tata/nexon-ev, tata/curvv-ev | (none in segments.json) |
| `reviews/mahindra/xev-9e/index.html` | premium-ev | mahindra/be6, tata/harrier-ev | mahindra/scorpio-n, mahindra/thar-roxx | (none) |
| `reviews/mahindra/xuv700/index.html` | premium-suv | tata/sierra, mahindra/scorpio-n, mahindra/thar-roxx | mahindra/be6, mahindra/xev-9e | (none) |
| `reviews/mahindra/scorpio-n/index.html` | premium-suv | tata/sierra, mahindra/xuv700, mahindra/thar-roxx | mahindra/be6, mahindra/xev-9e | (none) |
| `reviews/mahindra/thar-roxx/index.html` | premium-suv | tata/sierra, mahindra/scorpio-n, mahindra/xuv700 | mahindra/be6, mahindra/xev-9e | (none) |
| `reviews/maruti/brezza/index.html` | compact-suv | tata/punch | (none in same segment) | (none) |
| `reviews/tata/punch/index.html` | compact-suv | maruti/brezza | tata/nexon-ev, tata/punch-ev | (none) |
| `reviews/mg/windsor-ev/index.html` | entry-ev | tata/punch-ev, tata/tiago-ev | (none) | (none) |

Use the exact "Also in the running" HTML component structure:

```html
<div class="related-cars">
  <div class="eyebrow">Also in the running</div>
  <div class="related-grid">
    <a href="/reviews/[brand]/[model]/" class="related-card">
      <div class="rc-name">[Display name from segments.json → display_names]</div>
      <div class="rc-score">[Score from segments.json → jury_scores]/10</div>
      <div class="rc-verdict">[Verdict from segments.json → jury_scores]</div>
    </a>
    <!-- repeat for each segment peer and brand sibling, max 4 cards total -->
  </div>
  <div class="related-compares">
    <!-- only render this block if compare_pages is non-empty for this car -->
    <span class="eyebrow-sm">Head-to-head:</span>
    <a href="/compare/[slug]/">[Car A] vs [Car B] →</a>
  </div>
</div>
```

### HTML Check 5 — Top up remaining review pages to 4-link minimum

After fixing Check 4, verify all remaining review pages (those not in the list above) each have at least 4 specific internal links to `/reviews/` or `/compare/` pages. Links to index pages (`/reviews/`, `/compare/`) do not count.

For any page below the 4-link minimum, add the missing Type A/B/C links using segments.json as the data source. Do not add duplicate links to pages that already have sufficient interlinking.

---

After completing all HTML checks, output a final report:
- How many HTML files were modified
- Which pages had the "Also in the running" component added
- Whether the homepage, orphan, and 301 fixes were applied
- Any pages that could not be fixed (with reasons)

---

## What this repo is

`carjury/` is the production HTML site for **thecarjury.com** — a static, plain-HTML site hosted on Cloudflare Pages. No framework, no CMS. All agents live in `tools/` and run locally via macOS launchd. Full architecture: `THE_CAR_JURY_AGENT_ARCHITECTURE.md`.

---

## HARD RULES — Read before touching anything

### 1. Never change existing URL slugs

Every URL in the four sitemaps is locked. Do not rename, move, or restructure any existing file path.

**Locked URL patterns (from sitemap — do not alter):**
```
/reviews/[brand]/[model]/          e.g. /reviews/tata/nexon-ev/
/compare/[model-a]-vs-[model-b]/   e.g. /compare/creta-vs-seltos/
/influencers/[slug]/               e.g. /influencers/motoroctane/
/the-jury/
/about/
/advice/
/best/
/reviews/
/compare/
/influencers/
```

**New pages** may only be created using these patterns — they are additive, never replacements. When adding a new review slug, it must follow `reviews/[brand]/[model]/` exactly matching the brand and model already used elsewhere in the repo.

**One known duplicate to 301-redirect (do not create content for):**
`/compare/creta-vs-duster/index-v2.html` → redirect to `/compare/creta-vs-duster/`

### 2. `tools/segments.json` is the interlinking source of truth

All decisions about which cars to link to — segment rivals, brand siblings, compare pages — come from `tools/segments.json`. Do not hardcode car slugs in agent logic. Read from segments.json at runtime.

When a new review is added to the site, **update segments.json first**, then run generate_review.

### 3. Interlinking is additive only

When fixing interlinking on existing pages (adding missing links to reviews), only add `<a>` tags. Never modify the car's scoring data, verdict badge, jury score, section copy, schema markup, canonical tag, meta description, or any other content. Links only.

### 4. The sitemap is managed by `carjury_manager.py`

Do not manually edit sitemap XML files. The manager regenerates them on each run using content-hash-based `lastmod`. New pages added correctly to the directory will be picked up automatically.

**Sitemap priority levels (for reference when building new page types):**
- Homepage: `1.0`
- `/reviews/` index, `/compare/` index: `0.8` and `0.7`
- Individual reviews: `0.9`
- Individual compare pages: `0.7`
- Influencer profiles: `0.5`
- Future: news articles `0.6`, best-list pages `0.8`, advice pages `0.7`

---

## Interlinking Strategy — Summary

Full strategy: `INTERLINKING_STRATEGY.md`
Agent integration code: `INTERLINKING_AGENT_INTEGRATION.md`
Benchmarking vs CarDekho/CarWale: `INTERLINKING_BENCHMARK.md`

### The three link types every review page must carry

**Type A — Segment rivals** (2–3 links): cars in the same price band and body type. Source: `segments.json → segments[segment].cars`

**Type B — Brand siblings** (1–2 links): other cars from the same manufacturer. Source: `segments.json → brands[brand]`

**Type C — Compare handoff** (all applicable): every compare page that features this car. Source: `segments.json → compare_pages[brand/model]`

**Type D — Inline contextual links** (first mention per rival): wherever a rival car's name appears in the article body prose (`.section p`, `.faq-a` content), wrap the **first mention only** with `<a href="/reviews/brand/model/">Car Name</a>`. Never link the same car twice. Never link in headings or inside existing anchors. Source: `segments.json → display_names`. This is handled automatically by `inject_inline_links()` in `generate_review.py`.

**Type E — Influencer first-mention links** (applies to ALL page types): wherever a reviewer/creator name appears — in review prose, FAQ sections, compare page sources columns, or any landing page body — wrap the **first mention only** with `<a href="/influencers/[slug]/">Name</a>`. Never link the same influencer twice per page. The source of truth for name→URL mapping is `INFLUENCER_MAP` in `seo_agent.py` (and `_INFLUENCER_URLS` in `generate_compare.py`). Enforced by:
- **Reviews** (prose): `seo_agent.py → _add_interlinking()` — pre-populates `linked_urls` from existing article links before scanning, preventing duplicates across runs.
- **Compare pages** (sources columns): `generate_compare.py → render_sources_col()` — threads a shared `seen` set across both car columns at generation time.
- **Landing pages**: When creating any new landing page that mentions reviewer/creator names, manually link the first mention to `/influencers/[slug]/`. QA agent will flag any duplicate links.
- **QA gate**: `qa_agent.py → check_duplicate_influencer_links()` runs on reviews, compare pages, and all other pages during `run_site_qa()` — FAILs if any influencer URL appears more than once as a link.

**Minimum standard:** Every review page must have at least 4 specific internal links to `/reviews/` or `/compare/` pages. Links to index pages (`/reviews/`, `/compare/`) do not count toward this minimum.

### The "Also in the running" component

Every review page must include this section immediately before the jury credits:

```html
<div class="related-cars">
  <div class="eyebrow">Also in the running</div>
  <div class="related-grid">
    <a href="/reviews/[brand]/[model]/" class="related-card">
      <div class="rc-name">[Display name]</div>
      <div class="rc-score">[X.X]/10</div>
      <div class="rc-verdict">[BUY / WAIT / SKIP]</div>
    </a>
    <!-- repeat for 2–3 rivals -->
  </div>
  <div class="related-compares">
    <span class="eyebrow-sm">Head-to-head:</span>
    <a href="/compare/[slug]/">[Car A] vs [Car B] →</a>
    <!-- repeat for each compare page in compare_pages[this_car] -->
  </div>
</div>
```

Display names, scores, and verdicts come from `segments.json → display_names` and `segments.json → jury_scores`.

---

## Agent modification guide

### `tools/generate_review.py` — Primary change needed

Before calling Claude's SYNTHESIS_PROMPT, load the interlinking context:

```python
import json
from pathlib import Path

def get_link_context(brand: str, model: str) -> dict:
    seg_path = Path(__file__).parent / "segments.json"
    data = json.loads(seg_path.read_text())
    car_key = f"{brand}/{model}"
    
    # Segment peers
    segment_peers, car_segment = [], None
    for slug, info in data["segments"].items():
        if car_key in info["cars"]:
            car_segment = slug
            segment_peers = [c for c in info["cars"] if c != car_key][:3]
            break
    
    # Brand siblings
    siblings = [f"{brand}/{m}" for m in data["brands"].get(brand, []) if m != model][:2]
    
    # Compare pages
    compares = data["compare_pages"].get(car_key, [])
    
    # Enrich with display names and scores
    def enrich(key):
        return {
            "key": key,
            "url": f"/reviews/{key}/",
            "name": data["display_names"].get(key, key),
            "score": data["jury_scores"].get(key, {}).get("score", ""),
            "verdict": data["jury_scores"].get(key, {}).get("verdict", ""),
        }
    
    return {
        "segment": car_segment,
        "segment_peers": [enrich(k) for k in segment_peers],
        "brand_siblings": [enrich(k) for k in siblings],
        "compare_pages": [{"url": f"/{c}/", "slug": c} for c in compares],
    }
```

Pass `get_link_context(brand, model)` into the prompt as a JSON block and instruct Claude to render the "Also in the running" component. See `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 1` for the exact system prompt addition.

### `run_agents.py` → `qa_agent.py` — Add interlinking check

After content QA, parse the HTML and fail if fewer than 4 specific internal content links are present. See `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 2` for the `check_interlinking()` function.

### `run_agents.py` → `editorial_agent.py` — Add Update Sweep

After content cluster analysis, output a list of existing pages that need to link back to the newly published car. Post to Slack alongside the existing report. See `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 3` for the full task definition.

### `tech_seo_agent.py` — Add orphan detection

Add `detect_orphan_pages()` to the existing tech SEO pass. Flag any review or compare page with fewer than 3 inbound links. See `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 4`.

### `carjury_manager.py` — Add Step 4b

After Step 4 (content rebuilds), refresh `compare_pages` in `segments.json` by scanning the live `/compare/` directory. See `INTERLINKING_AGENT_INTEGRATION.md → PROMPT 5`.

---

## Agent hierarchy — where interlinking lives in the pipeline

**No new standalone agent is created.** Interlinking is not a separate agent — it is a skill absorbed into four existing agents. The reasoning: most interlinking decisions are deterministic Python lookups against `segments.json` and require no AI reasoning. Only the Update Sweep (identifying which *existing* pages need to link to a newly published car) requires judgment, and that belongs in the already-AI-powered `editorial_agent.py`.

### The pipeline and where each interlinking skill is injected

```
carjury_manager.py  (orchestrator — runs the full pipeline)
│
├── Step 1: Content trigger detected (new video / manual run)
│
├── Step 2: generate_review.py  ◀── INTERLINKING SKILL 1
│   └── Loads get_link_context() from segments.json before calling Claude
│       Passes segment rivals, brand siblings, compare pages into SYNTHESIS_PROMPT
│       Claude renders "Also in the running" component in the output HTML
│
├── Step 3: run_agents.py  (sequential agent runner)
│   │
│   ├── qa_agent.py  ◀── INTERLINKING SKILL 2
│   │   └── check_interlinking() — hard-fails if < 4 specific content links
│   │       or no related-cars component found in the HTML
│   │
│   ├── seo_agent.py  (no change — no interlinking role)
│   │
│   ├── tech_seo_agent.py  ◀── INTERLINKING SKILL 3
│   │   └── detect_orphan_pages() — flags review/compare pages with < 3 inbound links
│   │       Runs on full site, not just the new page
│   │
│   ├── editorial_agent.py  ◀── INTERLINKING SKILL 4
│   │   └── Update Sweep — Claude identifies existing pages that should now link
│   │       to the newly published car; posts update list to Slack
│   │
│   ├── eeat_agent.py  (no change)
│   ├── social_agent.py  (no change)
│   └── analytics_agent.py  (no change)
│
└── Step 4b: carjury_manager.py  ◀── INTERLINKING SKILL 5
    └── refresh_compare_pages_in_segments() — scans /compare/ directory after
        any new compare page is published and updates segments.json automatically
```

### Reporting chain

The interlinking skills do not change who reports to whom. The existing hierarchy stands:

- `carjury_manager.py` orchestrates everything
- `run_agents.py` runs the per-publish agent sequence and is called by the manager
- Individual agents (`qa_agent.py`, `tech_seo_agent.py`, `editorial_agent.py`) each report back to `run_agents.py` via return status / Slack messages
- `generate_review.py` is called directly by the manager (not via `run_agents.py`)

### Failure behaviour

- If `qa_agent.py → check_interlinking()` fails: the review is **not published**. The manager stops and alerts via Slack. The fix is to update `segments.json` and re-run.
- If `tech_seo_agent.py → detect_orphan_pages()` flags a page: it is logged as a warning in Slack but does **not** block publishing. It is an audit signal, not a gate.
- If the Update Sweep returns existing pages to fix: those are manual actions for Gajendra. The agent does not auto-edit existing pages.

---

## URL patterns for future content types

When building new page types, always use these slugs. Do not invent new patterns.

| Type | Pattern | Example |
|------|---------|---------|
| News article | `/news/[slug]/` (flat — no brand/topic prefix) | `/news/tata-sierra-ev-launch-q2-fy27/` |
| Best list | `/best/[segment-or-use-case]/` | `/best/evs/` |
| Advice guide | `/advice/[topic]/` | `/advice/ev-guide/` |
| Brand hub | `/[brand]/` | `/tata/` |

New slugs are added to the appropriate sub-sitemap by `carjury_manager.py` automatically. Never add them manually to sitemap XML.

---

## Adding a new review — the checklist

1. Update `tools/segments.json`:
   - Add `brand/model` to the correct `segments[x].cars` array
   - Add model to `brands[brand]` array
   - Add `display_names` entry
   - Add `jury_scores` entry (populated after generation)
   - Add `compare_pages` entry (empty list initially; update when compare pages are built)

2. Run `generate_review.py` — it will now pick up the interlinking context automatically

3. Run `run_agents.py` — QA will check interlinking before passing

4. Check the editorial agent's Update Sweep output in Slack — update the listed existing pages

5. If adding a compare page for this car later, update `compare_pages` in `segments.json` and link from the review

---

## What Claude should never do in this repo

- Change any `href`, `canonical`, or `<loc>` URL that already exists in the sitemaps
- Create a new `index.html` at any path that already has one, without explicit instruction
- Add `index-v2.html` or any variant file alongside a canonical page
- Modify `SYNTHESIS_PROMPT` in `generate_review.py` to remove existing rules (word limit, no em-dashes, reviewer name rule, etc.)
- Edit `influencers/influencers.json` without also updating the influencer's profile page and `master_list.md`
- Touch `sitemap*.xml` files directly
- Add `noindex` to any page
- Change the `priority` value of any existing sitemap entry

---

## Key file locations

| File | Purpose |
|------|---------|
| `tools/generate_review.py` | Review HTML generator + Claude synthesis |
| `tools/segments.json` | Interlinking data registry (segment map, scores, compare pages) |
| `influencers/influencers.json` | Influencer registry |
| `influencers/master_list.md` | Ranked influencer list (ordered by subscriber count) |
| `index_watchdog.py` | Live URL health checker |
| `INTERLINKING_STRATEGY.md` | Full interlinking strategy (Parts 1–13) |
| `INTERLINKING_AGENT_INTEGRATION.md` | Agent-specific prompts and code |
| `INTERLINKING_BENCHMARK.md` | CarDekho/CarWale comparison |
| `THE_CAR_JURY_AGENT_ARCHITECTURE.md` | Full system architecture |
| `GOAL.md` | Mission, content strategy, KPIs |

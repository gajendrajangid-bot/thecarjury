# Interlinking Strategy — Agent Integration Guide
**How INTERLINKING_STRATEGY.md maps to the existing agent architecture**
*Read alongside: THE_CAR_JURY_AGENT_ARCHITECTURE.md and INTERLINKING_STRATEGY.md*

---

## The Core Problem in One Sentence

The agent architecture builds and deploys content automatically. But it has no step that says "before publishing, what should this page link to, and after publishing, which existing pages need to link back to it?" That missing step is why 8 reviews launch with zero rival links and why two compare pages became orphans.

---

## How the Interlinking Strategy Maps to Each Agent

### Agent 1: `generate_review.py` — THE MOST CRITICAL GAP

**Current behaviour:** Generates review HTML from YouTube transcripts via Claude. Has no awareness of what other pages exist on the site or what links should be present.

**What needs to change:** The generator must look up the segment map at generation time and automatically populate the "Also in the running" section and prose links. This is a data lookup + template injection problem, not an AI reasoning problem.

**The fix:** Before Claude writes the HTML, the generator must load a `segments.json` file (see below) and pass the segment peers, brand siblings, and compare pages for the target car as context. Claude then places those links in the right spots in the HTML.

**Impact:** This single change eliminates the root cause of every orphan review page.

---

### Agent 2: `run_agents.py` → `qa_agent.py` — ADD AN INTERLINKING CHECK

**Current behaviour:** Checks word count, accuracy, readability, no em-dashes, completeness.

**What needs to change:** Add a check: does the generated HTML contain at least 4 specific internal links (not counting nav/footer/index links)? If not, flag it as a QA fail. This is a cheap regex/HTML-parse check that takes milliseconds.

**Impact:** Acts as a hard gate — a review cannot pass QA if it doesn't meet the minimum link standard.

---

### Agent 3: `run_agents.py` → `editorial_agent.py` — EXTEND TO RUN UPDATE SWEEP

**Current behaviour:** Does site-wide content cluster analysis, identifies content gaps, recommends next cars to review, suggests compare/best/advice pages needed. Posts to Slack.

**What needs to change:** Add a second responsibility: when a new review is published, identify which *existing* pages need to be updated to link to it. Specifically: (a) segment peers that don't yet link to the new car, (b) brand siblings that don't yet link to the new car, (c) any best-list pages that should now include it. Output a Slack message listing these update tasks.

**Impact:** Closes the reciprocal linking gap. Right now a new review gets zero inbound links from existing pages because no agent notifies anyone to update them.

---

### Agent 4: `tech_seo_agent.py` — ADD ORPHAN DETECTION

**Current behaviour:** PageSpeed Insights, LCP/INP/CLS, broken links, canonical health.

**What needs to change:** Add orphan page detection. Parse all HTML files, build the inbound link count for each page, and flag any page with fewer than 3 inbound links from non-nav/non-footer sources.

**Impact:** Catches orphan pages before they become a permanent SEO liability. The index_watchdog.py already fetches live URLs — orphan detection is a complementary local-file check.

---

### Agent 5: `carjury_manager.py` — ADD A SEGMENTS REGISTRY STEP

**Current behaviour:** Steps 0–6: publish → SEO check → index watchdog → robots → sitemap → rebuilds → deploy.

**What needs to change:** After Step 4 (content rebuilds), add a Step 4b: regenerate `segments.json` from the current set of live review pages. This keeps the segment registry always in sync with what's actually published so the generator always has accurate link targets.

**Impact:** Makes the whole system self-maintaining — as new reviews go live, the segment map updates automatically and the next generated review has the correct pool of link targets.

---

### Agent 6: `seo_agent.py` — MINOR ADDITION

**Current behaviour:** On-page SEO, schema, keyword presence, GEO readiness.

**What needs to change:** Add a check for compare page links specifically. If a compare page exists for this car (derivable from the compare/ directory listing), verify that it is linked from the review. This is a gap between what the compare page covers and what the review links to.

---

### Agents NOT affected

- `image_agent.py` — not relevant to interlinking
- `analytics_agent.py` — not relevant
- `social_agent.py` — not relevant (social links are external)
- `eeat_agent.py` — not directly relevant; E-E-A-T scores may improve as a downstream effect of better interlinking but the agent itself doesn't change
- `carjury_gate.py` — not relevant (staging QA is deployment-focused)

---

## The Missing Piece: `segments.json`

No agent can do intelligent interlinking without a data file that maps each car to its segment, rivals, and compare pages. This file doesn't currently exist. It needs to be created and maintained.

### Structure

```json
{
  "version": "1.0",
  "last_updated": "2026-05-02",
  "segments": {
    "entry-ev": {
      "label": "Entry EVs (under ₹15L)",
      "cars": ["tata/punch-ev", "tata/tiago-ev", "mg/windsor-ev"]
    },
    "mid-ev": {
      "label": "Mid EVs (₹15–22L)",
      "cars": ["tata/nexon-ev", "tata/curvv-ev", "hyundai/creta-electric", "maruti/e-vitara"]
    },
    "premium-ev": {
      "label": "Premium EVs (₹22–35L)",
      "cars": ["mahindra/be6", "mahindra/xev-9e", "tata/harrier-ev"]
    },
    "compact-suv": {
      "label": "Compact ICE SUVs (₹8–15L)",
      "cars": ["maruti/brezza", "tata/punch"]
    },
    "mid-suv": {
      "label": "Mid-Size ICE SUVs (₹12–22L)",
      "cars": ["hyundai/creta", "kia/seltos", "skoda/kushaq", "renault/duster"]
    },
    "premium-suv": {
      "label": "Premium Full-Size SUVs (₹20–35L)",
      "cars": ["tata/sierra", "mahindra/scorpio-n", "mahindra/xuv700", "mahindra/thar-roxx"]
    }
  },
  "brands": {
    "tata": ["sierra", "harrier-ev", "curvv-ev", "nexon-ev", "punch-ev", "punch", "tiago-ev"],
    "mahindra": ["be6", "xev-9e", "scorpio-n", "thar-roxx", "xuv700"],
    "hyundai": ["creta", "creta-electric"],
    "maruti": ["e-vitara", "brezza"],
    "kia": ["seltos"],
    "skoda": ["kushaq"],
    "renault": ["duster"],
    "mg": ["windsor-ev"]
  },
  "compare_pages": {
    "tata/nexon-ev": [
      "compare/creta-electric-vs-nexon-ev",
      "compare/nexon-ev-vs-e-vitara",
      "compare/be6-vs-nexon-ev"
    ],
    "hyundai/creta-electric": [
      "compare/creta-electric-vs-nexon-ev",
      "compare/creta-electric-vs-e-vitara"
    ],
    "hyundai/creta": [
      "compare/creta-vs-seltos",
      "compare/creta-vs-kushaq",
      "compare/creta-vs-duster"
    ],
    "maruti/e-vitara": [
      "compare/creta-electric-vs-e-vitara",
      "compare/nexon-ev-vs-e-vitara"
    ],
    "kia/seltos": ["compare/creta-vs-seltos"],
    "skoda/kushaq": ["compare/creta-vs-kushaq", "compare/kushaq-vs-duster"],
    "renault/duster": ["compare/creta-vs-duster", "compare/kushaq-vs-duster"],
    "mahindra/be6": ["compare/be6-vs-nexon-ev"],
    "tata/punch-ev": [],
    "tata/punch": [],
    "tata/sierra": [],
    "mahindra/scorpio-n": [],
    "mahindra/xuv700": [],
    "mahindra/thar-roxx": [],
    "mahindra/xev-9e": [],
    "tata/curvv-ev": [],
    "tata/harrier-ev": [],
    "tata/tiago-ev": [],
    "mg/windsor-ev": [],
    "maruti/brezza": []
  }
}
```

Save this as `/tools/segments.json`. Both `generate_review.py` and `editorial_agent.py` load it at runtime.

---

## The Prompts — Copy and Paste These

### PROMPT 1: For `generate_review.py` — Embed in the Claude system prompt used to generate review HTML

Add this block to the system prompt that currently instructs Claude to write the review HTML:

```
INTERNAL LINKING RULES (mandatory — apply before writing any HTML)

You will be given a `segments_data` object containing:
- `segment`: the segment this car belongs to (e.g. "mid-ev")
- `segment_peers`: list of brand/model slugs for direct rivals in the same segment
- `brand_siblings`: list of brand/model slugs for other cars from the same brand
- `compare_pages`: list of compare page slugs where this car appears

Before generating the HTML, reason through the following and apply the links:

TYPE A — SEGMENT RIVALS (mandatory: include 2–3)
Link to each car in `segment_peers`. These go in the "Also in the running" component
at the bottom of the article (before the jury credits section) AND as natural prose
links where the rival is first mentioned in the article body.

TYPE B — BRAND SIBLINGS (mandatory if siblings exist: include 1–2)
Link to the 1–2 most relevant cars in `brand_siblings` — prioritise same segment,
then closest price. These go in the "Also in the running" component and as prose
links where relevant (e.g. "Tata also makes the Nexon EV, which sits one segment below").

TYPE C — COMPARE PAGES (mandatory: include all)
For every slug in `compare_pages`, include a link in the "Also in the running"
component under a "Head-to-head:" label. Format: [Car A] vs [Car B] →

MINIMUM STANDARD: The generated HTML must contain at least 4 specific internal links
to /reviews/ or /compare/ pages. Links to /reviews/ (the index) do not count toward
this minimum.

"ALSO IN THE RUNNING" COMPONENT — use this HTML structure:
<div class="related-cars">
  <div class="eyebrow">Also in the running</div>
  <div class="related-grid">
    <!-- one card per segment peer, format: -->
    <a href="/reviews/[brand]/[model]/" class="related-card">
      <div class="rc-name">[Car display name]</div>
      <div class="rc-score">[score]/10</div>
      <div class="rc-verdict">[BUY / WAIT / SKIP]</div>
    </a>
  </div>
  <div class="related-compares">
    <span class="eyebrow-sm">Head-to-head:</span>
    <!-- one link per compare page -->
    <a href="/compare/[slug]/">[Car A] vs [Car B] →</a>
  </div>
</div>

Place this component immediately before the <div class="jury-credits"> section.
Do not add this section if segment_peers is empty.
```

Additionally, add this Python code to `generate_review.py` to load segments data and pass it to Claude:

```python
# --- INTERLINKING CONTEXT INJECTION ---
# Load segments registry
import json, os

segments_path = os.path.join(os.path.dirname(__file__), 'segments.json')
with open(segments_path) as f:
    seg_data = json.load(f)

def get_link_context(brand_slug, model_slug):
    """Return segment peers, brand siblings, and compare pages for a car."""
    car_key = f"{brand_slug}/{model_slug}"

    # Find segment
    car_segment = None
    segment_peers = []
    for seg_slug, seg_info in seg_data['segments'].items():
        if car_key in seg_info['cars']:
            car_segment = seg_slug
            segment_peers = [c for c in seg_info['cars'] if c != car_key]
            break

    # Brand siblings
    brand_siblings = [
        f"{brand_slug}/{m}" for m in seg_data['brands'].get(brand_slug, [])
        if m != model_slug
    ]

    # Compare pages
    compare_pages = seg_data['compare_pages'].get(car_key, [])

    return {
        'segment': car_segment,
        'segment_peers': segment_peers[:3],   # max 3
        'brand_siblings': brand_siblings[:2],  # max 2
        'compare_pages': compare_pages,
    }

# Then pass get_link_context(brand, model) into the Claude prompt as:
# segments_data = get_link_context(brand_slug, model_slug)
# Include in the user message to Claude as a JSON block before the transcript content
```

---

### PROMPT 2: For `qa_agent.py` — Add interlinking check to the QA pass

Add this check to the existing QA agent logic, run against the generated HTML file:

```python
# --- INTERLINKING QA CHECK ---
from bs4 import BeautifulSoup
import re

def check_interlinking(html_content, brand_slug, model_slug):
    """
    Verify minimum interlinking standards.
    Returns: (passed: bool, issues: list[str])
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    issues = []

    # Collect all internal links (href starts with /)
    all_links = [a.get('href', '') for a in soup.find_all('a', href=True)]
    internal_links = [l for l in all_links if l.startswith('/') and not l.startswith('//')]

    # Exclude nav, footer, and index-only links
    index_patterns = ['/reviews/', '/compare/', '/influencers/', '/best/', '/advice/', '/about/', '/the-jury/', '/']
    content_links = [
        l for l in internal_links
        if l not in index_patterns
        and not l == '/'
        and (l.startswith('/reviews/') or l.startswith('/compare/'))
        and l.count('/') >= 3  # excludes /reviews/ and /compare/ index
    ]

    # Rule 1: minimum 4 specific content links
    if len(content_links) < 4:
        issues.append(
            f"INTERLINKING FAIL: Only {len(content_links)} specific internal content links found. "
            f"Minimum required: 4. Found: {content_links}"
        )

    # Rule 2: must not link to self
    self_links = [l for l in content_links if f'/{brand_slug}/{model_slug}/' in l]
    if self_links:
        issues.append(f"INTERLINKING FAIL: Page links to itself: {self_links}")

    # Rule 3: check for "Also in the running" component
    related_section = soup.find(class_='related-cars')
    if not related_section:
        issues.append(
            "INTERLINKING WARN: No 'related-cars' component found. "
            "Add 'Also in the running' section before jury credits."
        )

    passed = len([i for i in issues if 'FAIL' in i]) == 0
    return passed, issues
```

If `passed` is False, the QA agent should raise a hard fail and block the publish pipeline (same behaviour as other QA failures currently).

---

### PROMPT 3: For `editorial_agent.py` — Add Update Sweep responsibility

Add this as a second section of the editorial agent's task, run after the existing content gap analysis. This section runs every time a new review is published (not daily — only on new publish events):

```
UPDATE SWEEP TASK (run after every new review publish)

You are given:
- `new_car_key`: the brand/model slug of the newly published review (e.g. "honda/elevate")
- `new_car_display`: human-readable name (e.g. "Honda Elevate")
- `new_car_score`: the jury score (e.g. "7.6")
- `new_car_verdict`: BUY / WAIT / SKIP
- `segments_data`: the full segments.json content
- `existing_pages`: list of all currently published review page slugs

Your job is to identify which existing pages need to be updated to link to the new review,
and output a specific, actionable update list.

Step 1 — Identify the new car's segment and find its peers from `segments_data`.

Step 2 — For each segment peer, check if it already links to the new car by searching
the HTML of that review page for href="/reviews/[new_car_key]/". If it does not,
add it to the update list.

Step 3 — Identify brand siblings from `segments_data['brands']`. For each sibling
that does not already link to the new car, add it to the update list.

Step 4 — Check all best-list pages (/best/*) and advice pages (/advice/*) to see if
they mention the relevant segment. If so, add them to the update list with a note
that the new car should be considered for inclusion.

Output format (post to Slack):
---
🔗 UPDATE SWEEP — [New Car Display Name] is now live

The following existing pages need to link to /reviews/[new_car_key]/:

REVIEWS TO UPDATE:
• /reviews/[peer-1]/ — add Type A (rival) link
• /reviews/[peer-2]/ — add Type A (rival) link
• /reviews/[sibling-1]/ — add Type B (brand) link

BEST LISTS TO REVIEW:
• /best/[segment]/ — consider adding [new car name] (jury score: [X.X], verdict: [V])

Run: python tools/update_interlinking.py --new-car [new_car_key]
to apply these changes automatically.
---

Do not include pages that already link to the new car.
Do not suggest updating compare pages — those are a separate workflow.
```

---

### PROMPT 4: For `tech_seo_agent.py` — Add orphan page detection

Add this check to the existing tech SEO pass:

```python
# --- ORPHAN PAGE DETECTION ---
import os
from bs4 import BeautifulSoup
from collections import defaultdict

def detect_orphan_pages(site_root):
    """
    Build inbound link map for all review and compare pages.
    Flag pages with fewer than 3 inbound links from content pages
    (excluding nav/footer/sitemap sources).
    """
    inbound = defaultdict(set)
    nav_footer_patterns = ['/about/', '/the-jury/', '/influencers/', '/']

    # Walk all HTML files
    for root, dirs, files in os.walk(site_root):
        dirs[:] = [d for d in dirs if d != '.git']
        for fname in files:
            if not fname.endswith('.html'):
                continue
            fpath = os.path.join(root, fname)
            rel = fpath.replace(site_root, '').replace('/index.html', '/').replace('.html', '')

            with open(fpath, 'r', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                if (href.startswith('/reviews/') or href.startswith('/compare/')):
                    # Normalise
                    if not href.endswith('/'):
                        href += '/'
                    if href not in nav_footer_patterns and href != rel:
                        inbound[href].add(rel)

    # Flag orphans
    orphans = []
    for path, sources in inbound.items():
        if len(sources) < 3:
            orphans.append((path, len(sources), list(sources)))

    # Also flag pages with NO entry in inbound at all
    all_content_pages = []
    for root, dirs, files in os.walk(site_root):
        dirs[:] = [d for d in dirs if d != '.git']
        for fname in files:
            if fname == 'index.html':
                fpath = os.path.join(root, fname)
                rel = fpath.replace(site_root, '').replace('/index.html', '/')
                if '/reviews/' in rel or '/compare/' in rel:
                    all_content_pages.append(rel)

    for page in all_content_pages:
        if page not in inbound:
            orphans.append((page, 0, []))

    return orphans

# In the agent's report, include:
# orphans = detect_orphan_pages(SITE_ROOT)
# if orphans:
#     for path, count, sources in sorted(orphans, key=lambda x: x[1]):
#         report.append(f"⚠️ ORPHAN ({count} inbound): {path}")
```

---

### PROMPT 5: For `carjury_manager.py` — Add segments.json refresh to Step 4

After the existing Step 4 (content rebuilds), add this step:

```python
# Step 4b: SEGMENTS REGISTRY REFRESH
# Scans all live review pages and updates segments.json compare_pages entries
# to ensure they reflect the current /compare/ directory.

def refresh_compare_pages_in_segments(site_root, segments_path):
    """
    Scans /compare/ directory for all compare pages and updates
    the compare_pages mapping in segments.json.
    """
    import json, os, re

    compare_dir = os.path.join(site_root, 'compare')
    with open(segments_path) as f:
        seg_data = json.load(f)

    # Reset compare_pages
    new_compare_map = {k: [] for k in seg_data['compare_pages'].keys()}

    # Walk compare pages
    for slug in os.listdir(compare_dir):
        compare_path = os.path.join(compare_dir, slug, 'index.html')
        if not os.path.exists(compare_path):
            continue

        with open(compare_path) as f:
            html = f.read()

        # Find the two review links in the compare page
        review_links = re.findall(r'href="/reviews/([^/"]+/[^/"]+)/"', html)
        for car_key in review_links:
            if car_key in new_compare_map:
                new_compare_map[car_key].append(f'compare/{slug}')

    seg_data['compare_pages'] = new_compare_map
    seg_data['last_updated'] = datetime.date.today().isoformat()

    with open(segments_path, 'w') as f:
        json.dump(seg_data, f, indent=2)

    print(f"[Step 4b] segments.json refreshed.")
```

---

## Implementation Order

Do these in this order. Each step builds on the previous one.

**First** — Create `tools/segments.json` (the JSON in this document). This is the data foundation everything else reads from. Takes 10 minutes.

**Second** — Add the interlinking QA check to `qa_agent.py`. This is a cheap HTML parse, low risk, catches future problems immediately. Takes 30 minutes.

**Third** — Add the Claude prompt addition to `generate_review.py` along with the `get_link_context()` function. This is the highest-impact change. Takes 1–2 hours. Test on one car before rolling out.

**Fourth** — Add the Update Sweep output to `editorial_agent.py`. This is additive — it does not change existing logic, just adds a second output section. Takes 1 hour.

**Fifth** — Add orphan detection to `tech_seo_agent.py`. Takes 30 minutes.

**Sixth** — Add `refresh_compare_pages_in_segments()` to `carjury_manager.py` Step 4b. Takes 30 minutes.

---

## What Stays the Same

The gate workflow, staging/production promotion, the social agent, the image agent, the analytics agent, and the E-E-A-T agent all stay exactly as they are. None of them touch interlinking.

The deployment rule (staging → production requires explicit owner approval) stays hardcoded. Interlinking fixes do not bypass the gate.

The influencer sync rule (any new influencer cited must be added to influencers.json + master_list.md + profile page) stays unchanged.

---

## One-Line Summary per Agent

| Agent | Change |
|-------|--------|
| `generate_review.py` | Load `segments.json` → pass link context to Claude → render "Also in the running" component |
| `qa_agent.py` | Add `check_interlinking()` — hard fail if fewer than 4 specific internal links |
| `editorial_agent.py` | Add Update Sweep — post list of pages that need updating after each new publish |
| `tech_seo_agent.py` | Add `detect_orphan_pages()` — flag in daily report |
| `carjury_manager.py` | Add Step 4b `refresh_compare_pages_in_segments()` |
| `seo_agent.py` | Add compare-link check: if compare page exists for this car, verify it is linked |
| `tools/segments.json` | **Create new** — the data registry all agents read from |

---

*This document is the bridge between INTERLINKING_STRATEGY.md and THE_CAR_JURY_AGENT_ARCHITECTURE.md. Implement in the order above. Once done, every new review that passes QA will be born with its full interlinking in place.*

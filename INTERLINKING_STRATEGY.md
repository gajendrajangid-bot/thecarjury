# The Car Jury — Interlinking Audit & Strategy
**Audit date:** May 2026 | **Pages audited:** 76 (20 reviews, 9 compares, 37 influencers, 10 core)

---

## Part 1: Audit Findings

### The Single Biggest Problem

Every page on thecarjury.com has one job it does well: it links back to the homepage. That's it. The reviews, compare pages, and core pages are essentially a collection of islands — a user who lands on the Tata Nexon EV review has no editorial path forward unless they scroll to find specific links buried in prose.

The structure today is a **hub-and-spoke** model where the homepage is the hub, but the homepage itself has **zero outbound links** to any review or compare page. That means there is no functional hub at all. Users arrive, read, and leave. Google crawls a page and finds almost nothing to follow.

---

### Audit Summary Table

| Page | Outbound (reviews/compares) | Inbound (all sources) | Status |
|------|------|------|------|
| **Homepage (/)** | 0 | — | 🔴 Critical — links to nothing |
| **Advice page** | 1 (Sierra only) | — | 🔴 Severely under-linked |
| **Best page** | 1 (Sierra only) | — | 🔴 Severely under-linked |
| `/reviews/tata/sierra/` | 7 review + 1 compare | 13 inbound | ✅ Best-linked page |
| `/reviews/renault/duster/` | 5 review + 3 compare | 11 inbound | ✅ Well-linked |
| `/reviews/skoda/kushaq/` | 4 review + 3 compare | 13 inbound | ✅ Well-linked |
| `/reviews/hyundai/creta/` | 3 review + 3 compare | 18 inbound | ✅ Well-linked |
| `/reviews/hyundai/creta-electric/` | 2 review + 2 compare | 11 inbound | 🟡 Adequate |
| `/reviews/tata/nexon-ev/` | 1 review + 3 compare | 10 inbound | 🟡 Adequate (compare-heavy) |
| `/reviews/maruti/e-vitara/` | 3 review + 2 compare | 15 inbound | 🟡 Adequate |
| `/reviews/tata/punch-ev/` | 3 review + 1 compare | 5 inbound | 🟡 Thin |
| `/reviews/tata/curvv-ev/` | 3 review + 1 compare | 5 inbound | 🟡 Thin |
| `/reviews/tata/sierra/` (inbound) | — | 13 | ✅ |
| `/reviews/kia/seltos/` | 3 review + 1 compare | 10 inbound | 🔴 Missing rival links |
| `/reviews/mahindra/be6/` | 3 review + 1 compare | 9 inbound | 🔴 Wrong rivals linked |
| `/reviews/tata/harrier-ev/` | 0 review + 1 compare | 6 inbound | 🔴 Isolated |
| `/reviews/mahindra/xev-9e/` | 0 review + 1 compare | 5 inbound | 🔴 Isolated |
| `/reviews/mahindra/xuv700/` | 0 review + 1 compare | 5 inbound | 🔴 Isolated |
| `/reviews/mahindra/scorpio-n/` | 0 review + 1 compare | 7 inbound | 🔴 Isolated |
| `/reviews/mahindra/thar-roxx/` | 0 review + 1 compare | 5 inbound | 🔴 Isolated |
| `/reviews/maruti/brezza/` | 0 review + 1 compare | 5 inbound | 🔴 Isolated |
| `/reviews/tata/punch/` | 0 review + 1 compare | 9 inbound | 🔴 Isolated |
| `/reviews/tata/tiago-ev/` | 1 review + 1 compare | 10 inbound | 🔴 Wrong rival linked |
| `/reviews/mg/windsor-ev/` | 0 review + 1 compare | 8 inbound | 🔴 Isolated |
| `/compare/creta-electric-vs-e-vitara/` | — | **0 inbound** | 🔴 Complete orphan |
| `/compare/creta-vs-duster/index-v2.html` | — | **0 inbound** | 🔴 Complete orphan (duplicate) |

---

### Critical Issues

**1. The homepage links to nothing.**
The homepage has 0 outbound links to reviews, compare pages, influencers, or editorial content. For a site whose purpose is to send buyers to verdicts, this is the most important structural fix. Google's crawl budget lands on the homepage, finds no followed links to content, and moves on.

**2. Two complete orphans.**
`/compare/creta-electric-vs-e-vitara/` has zero inbound links from any page on the site. It exists in the sitemap but is unreachable by navigation or editorial link. The `/compare/creta-vs-duster/index-v2.html` is a duplicate of the canonical compare page and should be redirected or removed.

**3. Eight reviews link to zero other reviews.**
Harrier EV, XEV 9E, XUV700, Scorpio N, Thar Roxx, Brezza, Punch (ICE), and Windsor EV all link only to the `/reviews/` index and not to a single specific car review. These are content dead-ends for readers and crawlers alike.

**4. No EV cluster.**
The 9 EV reviews on the site (Creta Electric, Nexon EV, BE6, XEV 9E, Harrier EV, Curvv EV, Punch EV, Tiago EV, Windsor EV) are barely connected to each other. A reader researching EVs has to navigate backwards and then dig through the index to find related EV content. This is the single biggest editorial gap.

**5. Inconsistent compare-linking from reviews.**
Some reviews (Nexon EV, Duster, Kushaq) do an excellent job linking to their specific comparison pages. Others in identical situations (Harrier EV vs. any other EV, Brezza vs. Punch) link to nothing. There is no standard.

**6. The advice and best pages only link to one car (Sierra).**
Two editorial hub pages that could drive traffic across the entire review catalog are pointing at a single car each.

---

## Part 2: The Interlinking Strategy

### The Mental Model — Three Link Types

Every outbound internal link on thecarjury.com should belong to one of three categories. Writing teams and developers should think in these terms:

**Type A — Same Segment (rivalry links)**
Links to cars in the same price band and body type. These exist to serve a buyer who is actively comparing options. If a reader is on the Hyundai Creta page, they are almost certainly also considering the Kia Seltos and Skoda Kushaq. Every review page must link to its primary rivals.

**Type B — Same Brand (brand cluster links)**
Links to other reviews of cars from the same manufacturer. Tata has 7 reviews; a reader on the Punch EV page who's a Tata buyer should be able to reach the Nexon EV and Curvv EV easily. These links also signal topical authority to search engines.

**Type C — Compare (handoff links)**
Every time a review page mentions a head-to-head situation covered by a compare page, it should link directly to that compare page. The compare page in turn must always link back to both review pages it features. This creates a triangle: review A → compare A vs B → review B → review A.

---

### Rule Set for All Pages

**Rule 1 — Review pages must carry at minimum:**
- 2 Type A (segment rival) links
- 1–2 Type B (same-brand) links if siblings exist
- All relevant Type C (compare) links where a compare page exists

**Rule 2 — Compare pages must link back to:**
- The two review pages being compared (already done — maintain this)
- 3–5 related compare pages (already done — maintain this)
- The review pages should reciprocally link to the compare page (currently missing in most cases)

**Rule 3 — Editorial hub pages (advice, best) must link to at least 6–8 reviews each, spanning segments.**

**Rule 4 — The homepage must have at least 8 followed links to content pages** — a mix of featured reviews, compare pages, and editorial pages.

**Rule 5 — New pages at launch must include all applicable Type A, B, and C links before publishing.** This is the most impactful preventive rule. The orphan problem grows only when pages launch without links.

**Rule 6 — No review page may launch with fewer than 4 specific internal links** (not counting navigation, footer, or the /reviews/ index link).

---

## Part 3: The Segment Map

Segment groupings for building Type A (rival) links. When writing or updating a review, link to the 2–3 most directly competing pages in the same segment.

### Segment 1: Entry EVs (₹8–14L)
- Tata Punch EV → `/reviews/tata/punch-ev/`
- Tata Tiago EV → `/reviews/tata/tiago-ev/`
- MG Windsor EV → `/reviews/mg/windsor-ev/`

Every entry EV review should link to both others in this cluster.

### Segment 2: Mid EVs (₹15–22L)
- Tata Nexon EV → `/reviews/tata/nexon-ev/`
- Tata Curvv EV → `/reviews/tata/curvv-ev/`
- Hyundai Creta Electric → `/reviews/hyundai/creta-electric/`
- Maruti E-Vitara → `/reviews/maruti/e-vitara/`

Core rivals in this cluster: Nexon EV ↔ Creta Electric ↔ E-Vitara ↔ Curvv EV.

### Segment 3: Premium EVs (₹22–30L)
- Mahindra BE6 → `/reviews/mahindra/be6/`
- Mahindra XEV 9E → `/reviews/mahindra/xev-9e/`
- Tata Harrier EV → `/reviews/tata/harrier-ev/`

BE6 and XEV 9E are siblings — always cross-link. Harrier EV is the Tata rival.

### Segment 4: Compact ICE SUVs (₹8–15L)
- Maruti Brezza → `/reviews/maruti/brezza/`
- Tata Punch → `/reviews/tata/punch/`

Both should link to each other and to their EV variants.

### Segment 5: Mid-Size ICE SUVs (₹12–22L)
- Hyundai Creta → `/reviews/hyundai/creta/`
- Kia Seltos → `/reviews/kia/seltos/`
- Skoda Kushaq → `/reviews/skoda/kushaq/`
- Renault Duster → `/reviews/renault/duster/`

All four are direct rivals. The compare pages already cover most pairs — ensure every review links to relevant compare pages.

### Segment 6: Premium Full-Size SUVs (₹20–35L)
- Tata Sierra → `/reviews/tata/sierra/`
- Mahindra Scorpio N → `/reviews/mahindra/scorpio-n/`
- Mahindra XUV700 → `/reviews/mahindra/xuv700/`
- Mahindra Thar Roxx → `/reviews/mahindra/thar-roxx/`

All four should cross-link. Thar Roxx is lifestyle/off-road but buyers compare it with Scorpio N.

### Brand Clusters (Type B links)

**Tata cluster (7 reviews):** Sierra, Harrier EV, Curvv EV, Nexon EV, Punch EV, Punch, Tiago EV
- Every Tata review should link to 2–3 Tata siblings, prioritising same segment first.

**Mahindra cluster (5 reviews):** BE6, XEV 9E, Scorpio N, Thar Roxx, XUV700
- BE6 ↔ XEV 9E always. Scorpio N ↔ XUV700 ↔ Thar Roxx always.

**Maruti cluster (2 reviews):** E-Vitara, Brezza
- Always link to each other. E-Vitara is the EV upgrade path from Brezza.

**Hyundai cluster (2 reviews):** Creta, Creta Electric
- Always link to each other. Creta Electric is the EV upgrade path.

---

## Part 4: Page-by-Page Fix List

The following table defines the minimum required links for each review page going forward. Links already present are marked ✅. Missing links are marked as **add**.

### Hyundai Creta Electric (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/hyundai/creta/` | Brand B | ✅ Present |
| `/reviews/tata/nexon-ev/` | Segment A | **Add** |
| `/reviews/maruti/e-vitara/` | Segment A | **Add** |
| `/reviews/tata/curvv-ev/` | Segment A | **Add** |
| `/compare/creta-electric-vs-nexon-ev/` | Type C | ✅ Present |
| `/compare/creta-electric-vs-e-vitara/` | Type C | **Add** — this is the orphan; this link fixes it |

### Hyundai Creta (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/kia/seltos/` | Segment A | **Add** — top rival, inexplicably missing |
| `/reviews/skoda/kushaq/` | Segment A | ✅ Present |
| `/reviews/renault/duster/` | Segment A | ✅ (via compare) |
| `/reviews/hyundai/creta-electric/` | Brand B | **Add** |
| `/compare/creta-vs-seltos/` | Type C | **Add** |
| `/compare/creta-vs-kushaq/` | Type C | ✅ Present |
| `/compare/creta-vs-duster/` | Type C | ✅ Present |

### Kia Seltos (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/hyundai/creta/` | Segment A | **Add** — the top rival is missing |
| `/reviews/skoda/kushaq/` | Segment A | **Add** |
| `/reviews/renault/duster/` | Segment A | **Add** |
| `/compare/creta-vs-seltos/` | Type C | **Add** |

### Mahindra BE6 (BUY 8.0)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/xev-9e/` | Brand B | **Add** — direct sibling, inexplicably absent |
| `/reviews/tata/harrier-ev/` | Segment A | **Add** |
| `/reviews/tata/nexon-ev/` | Segment A | **Add** (currently links to Creta instead) |
| `/reviews/hyundai/creta-electric/` | Segment A | ✅ Present (but this is one segment below) |
| `/compare/be6-vs-nexon-ev/` | Type C | **Add** |

### Mahindra Scorpio N (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/xuv700/` | Brand B | **Add** |
| `/reviews/mahindra/thar-roxx/` | Brand B | **Add** |
| `/reviews/tata/sierra/` | Segment A | **Add** |

### Mahindra Thar Roxx (BUY 8.0)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/scorpio-n/` | Brand B + Segment A | **Add** |
| `/reviews/mahindra/xuv700/` | Brand B | **Add** |
| `/reviews/tata/sierra/` | Segment A | **Add** |

### Mahindra XEV 9E (WAIT 7.5)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/be6/` | Brand B | **Add** — sibling, always required |
| `/reviews/tata/harrier-ev/` | Segment A | **Add** |
| `/reviews/hyundai/creta-electric/` | Segment A (one below) | **Add** |
| `/reviews/tata/nexon-ev/` | Segment A | **Add** |

### Mahindra XUV700 (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/scorpio-n/` | Brand B + Segment A | **Add** |
| `/reviews/mahindra/thar-roxx/` | Brand B | **Add** |
| `/reviews/tata/sierra/` | Segment A | **Add** |

### Maruti Brezza (BUY 7.4)
| Link | Type | Status |
|------|------|--------|
| `/reviews/maruti/e-vitara/` | Brand B | **Add** — Maruti sibling, always required |
| `/reviews/tata/punch/` | Segment A | **Add** |
| `/reviews/tata/nexon-ev/` | Segment A (EV alternative) | **Add** |

### Maruti E-Vitara (WAIT 6.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/maruti/brezza/` | Brand B | **Add** |
| `/reviews/tata/nexon-ev/` | Segment A | **Add** |
| `/reviews/hyundai/creta-electric/` | Segment A | ✅ Present |
| `/compare/creta-electric-vs-e-vitara/` | Type C | **Add** — helps rescue orphan |
| `/compare/nexon-ev-vs-e-vitara/` | Type C | ✅ Present |

### MG Windsor EV (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/nexon-ev/` | Segment A | **Add** |
| `/reviews/tata/punch-ev/` | Segment A (step down) | **Add** |
| `/reviews/hyundai/creta-electric/` | Segment A (step up) | **Add** |

### Renault Duster (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/kia/seltos/` | Segment A | **Add** |
| `/reviews/hyundai/creta/` | Segment A | ✅ Present |
| `/reviews/skoda/kushaq/` | Segment A | ✅ Present |
| `/compare/creta-vs-duster/` | Type C | ✅ Present |
| `/compare/kushaq-vs-duster/` | Type C | ✅ Present |

### Skoda Kushaq (BUY 7.6)
| Link | Type | Status |
|------|------|--------|
| `/reviews/kia/seltos/` | Segment A | **Add** |
| `/reviews/hyundai/creta/` | Segment A | ✅ Present |
| `/reviews/renault/duster/` | Segment A | ✅ Present |
| `/compare/creta-vs-kushaq/` | Type C | ✅ Present |
| `/compare/kushaq-vs-duster/` | Type C | ✅ Present |

### Tata Curvv EV (BUY 7.4)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/nexon-ev/` | Brand B + Segment A | ✅ Present |
| `/reviews/tata/harrier-ev/` | Brand B (step up) | **Add** |
| `/reviews/hyundai/creta-electric/` | Segment A | **Add** |
| `/reviews/maruti/e-vitara/` | Segment A | **Add** |

### Tata Harrier EV (BUY 7.5)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/curvv-ev/` | Brand B (step down) | **Add** |
| `/reviews/tata/nexon-ev/` | Brand B | **Add** |
| `/reviews/mahindra/be6/` | Segment A | **Add** |
| `/reviews/mahindra/xev-9e/` | Segment A | **Add** |

### Tata Nexon EV (BUY 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/curvv-ev/` | Brand B (step up) | **Add** |
| `/reviews/tata/punch-ev/` | Brand B (step down) | ✅ (via punch-ev page linking back) **Add here** |
| `/reviews/hyundai/creta-electric/` | Segment A | **Add** |
| `/reviews/mg/windsor-ev/` | Segment A | **Add** |
| `/compare/creta-electric-vs-nexon-ev/` | Type C | ✅ Present |
| `/compare/nexon-ev-vs-e-vitara/` | Type C | ✅ Present |
| `/compare/be6-vs-nexon-ev/` | Type C | **Add** |

### Tata Punch EV (BUY 7.4)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/nexon-ev/` | Brand B (step up) | ✅ Present |
| `/reviews/tata/punch/` | Brand B (ICE sibling) | ✅ Present |
| `/reviews/tata/tiago-ev/` | Brand B (step down) | **Add** |
| `/reviews/mg/windsor-ev/` | Segment A | **Add** |

### Tata Punch ICE (BUY 7.6)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/punch-ev/` | Brand B (EV sibling) | **Add** |
| `/reviews/maruti/brezza/` | Segment A | **Add** |
| `/reviews/tata/nexon-ev/` | Brand B (step up) | **Add** |

### Tata Sierra (WAIT 7.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/mahindra/scorpio-n/` | Segment A | **Add** |
| `/reviews/mahindra/xuv700/` | Segment A | **Add** |
| `/reviews/tata/harrier-ev/` | Brand B (EV sibling) | **Add** |
| `/reviews/hyundai/creta/` | ✅ Present | — |
| `/reviews/renault/duster/` | ✅ Present | — |
| `/reviews/skoda/kushaq/` | ✅ Present | — |

### Tata Tiago EV (WAIT 6.8)
| Link | Type | Status |
|------|------|--------|
| `/reviews/tata/punch-ev/` | Brand B (step up) | **Add** |
| `/reviews/tata/nexon-ev/` | Brand B (aspirational) | **Add** |
| `/reviews/mg/windsor-ev/` | Segment A | **Add** |
| Note: current link to `/reviews/maruti/e-vitara/` is wrong segment — **remove** |

---

## Part 5: Compare Page — Orphan Fix

### `/compare/creta-electric-vs-e-vitara/` — Rescue Plan
This is the only compare page with zero inbound links. It needs to be linked from:
1. `/reviews/hyundai/creta-electric/` — **Add Type C link**
2. `/reviews/maruti/e-vitara/` — **Add Type C link**
3. `/compare/creta-electric-vs-nexon-ev/` — already in its sidebar, but the reverse is missing; **add** `/compare/creta-electric-vs-e-vitara/` to the related compares on that page

### `/compare/creta-vs-duster/index-v2.html` — Action Required
This page is a duplicate of `/compare/creta-vs-duster/`. It has different internal compare links (pointing to nexon-ev-vs-e-vitara instead of be6-vs-nexon-ev) suggesting it was an experimental version. **Redirect 301 to canonical** `/compare/creta-vs-duster/` and remove from sitemap.

---

## Part 6: Homepage & Hub Pages

### Homepage (`/`)
The homepage currently has zero outbound links to any content. Minimum viable fix:

Recommended featured links for the homepage (to be placed in featured/hero sections):
- Featured reviews: Sierra, BE6, Duster, Creta Electric, Nexon EV, Seltos, XUV700
- Featured compare: Creta vs Seltos, Creta Electric vs Nexon EV, BE6 vs Nexon EV
- Editorial: Advice page, Best page, The Jury page

**Minimum: 8 followed links from homepage to content pages.**

### Advice page (`/advice/`)
Currently only links to Sierra. Should link to at minimum:
- 2–3 segment-specific advice trails (e.g., "Which EV should I buy?", "Best SUV under ₹20L")
- 5–6 review pages spanning different segments

### Best page (`/best/`)
Currently only links to Sierra. Should link to:
- Top picks across segments: BE6, Duster, Creta, Thar Roxx, Nexon EV, Tiago EV (for context)
- The compare index (`/compare/`)

---

## Part 7: The "Related Cars" Component — Standard for Future Pages

Every review page published going forward must include a **"Also in the running"** section near the bottom, before the jury credits. This section is a standardised component, not ad hoc prose links.

### Structure

```html
<!-- RELATED CARS — standard section for all review pages -->
<div class="related-cars">
  <div class="eyebrow">Also in the running</div>
  <div class="related-grid">
    <!-- 2–4 cards, each with: car name, jury score, verdict badge, link to review -->
    <a href="/reviews/[brand]/[model]/" class="related-card">
      <div class="rc-name">[Car Name]</div>
      <div class="rc-score">[X.X]/10</div>
      <div class="rc-verdict">[BUY / WAIT / SKIP]</div>
    </a>
  </div>
  <!-- If a compare page exists between this car and any listed above -->
  <div class="related-compares">
    <span class="eyebrow-sm">Head-to-head:</span>
    <a href="/compare/[slug]/">[Car A] vs [Car B] →</a>
  </div>
</div>
```

### Which cars to include
Use the segment map in Part 3. Pick the 2–4 most direct rivals. Do not include aspirational or irrelevant cars to pad the section. The rule is: a buyer actively considering this car would genuinely also consider the listed cars.

---

## Part 8: Priority Action Order

Work through this in sequence. The highest-SEO-impact changes come first.

**Week 1 — Structural**
1. Add followed links from the homepage to 8+ content pages
2. 301 redirect `/compare/creta-vs-duster/index-v2.html` → `/compare/creta-vs-duster/`
3. Add links to `/compare/creta-electric-vs-e-vitara/` from Creta Electric review and E-Vitara review

**Week 2 — Isolated reviews**
4. Add rival links to Scorpio N, Thar Roxx, XUV700 (Mahindra family is the biggest gap)
5. Add rival links to BE6 and XEV 9E (EV premium cluster)
6. Add rival links to Harrier EV, Windsor EV, Tiago EV (entry/mid EV cluster)

**Week 3 — Refinement**
7. Fix Kia Seltos (missing Creta link is embarrassing for a compare-focused site)
8. Fix Maruti Brezza (missing E-Vitara sibling link)
9. Fix Tata Punch ICE (missing EV sibling and rival links)
10. Update Advice and Best pages to link across the full catalog

**Ongoing — New pages**
11. Implement the "Also in the running" component as a standard template element
12. Before publishing any new review, populate all Type A/B/C links in the editorial checklist

---

## Quick Reference — Complete Link Matrix

### Who links to whom (minimum standard)

| Page | Must link to (Type A rivals) | Must link to (Type B brand) | Must link to (Type C compare) |
|------|------|------|------|
| Creta Electric | Nexon EV, E-Vitara, Curvv EV | Creta | creta-electric-vs-nexon-ev, **creta-electric-vs-e-vitara** |
| Creta | **Seltos**, Kushaq, Duster | Creta Electric | creta-vs-seltos, creta-vs-kushaq, creta-vs-duster |
| Seltos | **Creta, Kushaq, Duster** | — | creta-vs-seltos |
| BE6 | **Harrier EV, Nexon EV** | **XEV 9E** | be6-vs-nexon-ev |
| XEV 9E | **Harrier EV, Creta Electric** | **BE6** | — |
| Scorpio N | **XUV700, Sierra** | **Thar Roxx** | — |
| Thar Roxx | **Scorpio N, Sierra** | **XUV700** | — |
| XUV700 | **Scorpio N, Sierra** | **Thar Roxx** | — |
| Brezza | **Punch, Nexon EV** | **E-Vitara** | — |
| E-Vitara | Nexon EV, Creta Electric | **Brezza** | nexon-ev-vs-e-vitara, **creta-electric-vs-e-vitara** |
| Windsor EV | **Nexon EV, Punch EV** | — | — |
| Duster | Seltos, Creta, Kushaq | — | creta-vs-duster, kushaq-vs-duster |
| Kushaq | **Seltos**, Creta, Duster | — | creta-vs-kushaq, kushaq-vs-duster |
| Curvv EV | Nexon EV, **Harrier EV, Creta Electric** | — | — |
| Harrier EV | **Curvv EV, Nexon EV, BE6, XEV 9E** | — | — |
| Nexon EV | **Creta Electric, Curvv EV, Windsor EV** | Punch EV | creta-electric-vs-nexon-ev, nexon-ev-vs-e-vitara, be6-vs-nexon-ev |
| Punch EV | **Windsor EV** | Nexon EV, Punch, **Tiago EV** | — |
| Punch ICE | **Brezza** | Punch EV, **Nexon EV** | — |
| Sierra | **Scorpio N, XUV700** | **Harrier EV** | — |
| Tiago EV | **Punch EV, Windsor EV** | Nexon EV | — |

*Bold = currently missing, needs to be added*

---

*This document should be reviewed and updated each time a new review or compare page is added. The segment map in Part 3 is the primary reference — classify the new car, add it to its cluster, and update the matrix accordingly.*

---

# Part 9: The Scalable Architecture — Growing Beyond Reviews

Parts 1–8 cover the current site. This section is the forward-looking playbook. It defines how interlinking should work as thecarjury expands into news, best lists, advice guides, brand pages, and new car segments. The rules here are designed so they work whether you have 20 pages or 2,000.

---

## 9.1 The Taxonomy — The Foundation of Everything

Before any content type can interlink intelligently, you need a consistent tagging system. Every piece of content on thecarjury should carry the following attributes. These are not visible labels — they are the metadata that powers "related content" logic and editorial decisions about what to link to.

### The Five Axes

**Axis 1 — Brand**
`tata` · `hyundai` · `kia` · `mahindra` · `maruti` · `mg` · `renault` · `skoda` · `honda` · `toyota` · `volkswagen` · `bmw` · `mercedes` · `jeep` · etc.

**Axis 2 — Segment**
Use these exact slugs consistently across all content types, URL patterns, and labels:

| Slug | What it means |
|------|---------------|
| `entry-ev` | EVs priced under ₹15L |
| `mid-ev` | EVs ₹15–22L |
| `premium-ev` | EVs ₹22–35L |
| `luxury-ev` | EVs above ₹35L |
| `compact-suv` | ICE SUVs under ₹15L (Brezza, Punch, Venue, Sonet) |
| `mid-suv` | ICE SUVs ₹12–22L (Creta, Seltos, Kushaq, Duster) |
| `premium-suv` | ICE SUVs ₹20–35L (Sierra, Scorpio N, XUV700, Thar) |
| `luxury-suv` | ICE SUVs above ₹35L |
| `compact-sedan` | Sedans under ₹15L |
| `mid-sedan` | Sedans ₹15–25L |
| `hatchback` | Hatchbacks (Altroz, i20, Baleno, Glanza) |
| `pickup` | Trucks (Hilux, Gladiator) |
| `mpv` | MPVs (Innova, Ertiga, Carens) |

**Axis 3 — Fuel/Powertrain**
`petrol` · `diesel` · `ev` · `mild-hybrid` · `strong-hybrid` · `cng`

**Axis 4 — Content Type**
`review` · `compare` · `best-list` · `news` · `advice` · `brand-page` · `influencer-profile`

**Axis 5 — Budget Band**
`under-10L` · `10L-15L` · `15L-20L` · `20L-25L` · `25L-35L` · `above-35L`

### Why this matters for interlinking

When a page is tagged on these five axes, the answer to "what should this page link to?" becomes a lookup, not a judgement call. A news story tagged `[tata, nexon-ev, ev, mid-ev, 15L-20L]` should automatically surface links to the Nexon EV review, the Creta Electric review (same segment), any compare page featuring the Nexon EV, and any best-list that includes the mid-EV segment. The taxonomy is what makes interlinking systematic rather than ad hoc.

---

## 9.2 The Pillar-Cluster Model

As thecarjury grows, the site architecture should evolve from a flat collection of pages into a **pillar-cluster structure**. This is the most search-engine-friendly and reader-friendly way to organise a content-rich site.

### What a pillar page is

A pillar page is a comprehensive hub that covers a broad topic and links to every cluster page (individual piece of content) related to it. It does not go deep on any one thing — it maps the terrain and distributes the reader.

### What a cluster page is

A cluster page goes deep on one specific subtopic and links back to its pillar. The pillar + all its clusters form a topical web that tells Google: this site has authority on this subject.

### thecarjury's pillar structure (recommended)

| Pillar page | URL | Clusters it links to |
|-------------|-----|----------------------|
| **EV Buyer's Guide** | `/advice/ev-guide/` | All EV reviews, all EV compares, EV news, EV best lists |
| **Best EVs in India** | `/best/evs/` | Top-ranked EV reviews, EV compare pages |
| **Mid-Size SUV Guide** | `/advice/mid-size-suv/` | Creta, Seltos, Kushaq, Duster reviews + all their compares |
| **Best SUVs under ₹20L** | `/best/suv-under-20l/` | Compact + mid-SUV reviews |
| **Mahindra Buyer's Guide** | `/mahindra/` | All Mahindra reviews, Mahindra news, Mahindra compares |
| **Tata Buyer's Guide** | `/tata/` | All Tata reviews, Tata news, Tata compares |

Each of these pillar pages should eventually exist. When they do, every cluster page (review, compare, news, best-list) that belongs to that topic should link back to the pillar, and the pillar should link to the cluster.

The rule: **every cluster page should belong to exactly one primary pillar and link to it.** Secondary pillar links are fine but optional.

---

## 9.3 New Content Type: News (`/news/`)

### URL pattern
```
/news/[brand-or-topic]/[slug]/
e.g. /news/tata/nexon-ev-facelift-2026/
     /news/ev-industry/charging-infrastructure-india/
     /news/mahindra/be-series-price-update/
```

### What every news article must link to

| Link | Requirement |
|------|-------------|
| The review of the car(s) mentioned | **Mandatory** if a Car Jury review exists for that car |
| The compare page if relevant | **Mandatory** if a compare page exists featuring that car |
| 1–2 related news stories (same brand or same segment) | Strongly recommended once you have enough news volume |
| The relevant pillar/advice page | Recommended (e.g., an EV news story links to `/advice/ev-guide/`) |
| The relevant best-list page | Optional (e.g., a pricing update links to the best-list for that segment) |

### What should link to a news article

| Source | When |
|--------|------|
| The car's review page | Add a "Latest news" section at the bottom of reviews listing recent news for that car. This keeps reviews evergreen while surface fresh signals. |
| The pillar/advice page | The EV guide should have a "Recent EV news" block linking to latest news articles. |
| Other news stories | Cross-link news stories that cover the same car or launch event. |

### News that is not about a specific car
Some news is category-level (e.g., "India EV sales hit 1 million"). These articles should link to the relevant segment pillar page and to 2–3 of the most prominent reviews in that segment. They should not link to unrelated cars just to pad links.

### Anti-pattern to avoid
Do not link from a news article about a brand launch to reviews of competing brands. A Tata Sierra update story should not link to the Mahindra Scorpio N — that is not natural and Google treats it as low-quality.

---

## 9.4 New Content Type: Best Lists (`/best/`)

Best lists are among the highest-value SEO pages on any car site. A page like "Best EVs in India 2026" can rank for thousands of buyer-intent queries and funnel readers directly into review pages. They are also the most natural internal linking opportunity on the site.

### URL pattern
```
/best/[segment-or-use-case]/
e.g. /best/evs/
     /best/suv-under-20l/
     /best/family-suv/
     /best/first-car/
     /best/ev-under-15l/
     /best/mahindra/
```

### What every best-list must link to

| Link | Requirement |
|------|-------------|
| Full review page for every car mentioned | **Mandatory**. A best-list without review links is a dead end. |
| Compare pages between cars listed | **Mandatory** if a compare exists between any two cars on the list |
| Related best-lists (by segment overlap or budget overlap) | Strongly recommended once multiple lists exist |
| Relevant advice/guide page | Recommended |

### What should link to a best-list

| Source | When |
|--------|------|
| Homepage | Featured best-lists should be linked from the homepage |
| Review pages | At the bottom of every review: "This car appears in our [Best EVs in India] list" |
| News articles | When a price drop or launch is relevant: "See our updated Best EV list" |
| Advice/guide pages | The EV guide links to the EV best-list; the mid-SUV guide links to the SUV best-list |

### Best-list update rule
When you add a new review (e.g., a new EV), revisit every relevant best-list and decide whether that car earns a place. If it does, add it and update the list's publish date. This keeps the list evergreen and creates a natural reason to add a new internal link.

### Example best-list structure and its required links

A `/best/evs/` page listing: BE6, Nexon EV, Creta Electric, Punch EV, Windsor EV must link to:
- `/reviews/mahindra/be6/`
- `/reviews/tata/nexon-ev/`
- `/reviews/hyundai/creta-electric/`
- `/reviews/tata/punch-ev/`
- `/reviews/mg/windsor-ev/`
- `/compare/be6-vs-nexon-ev/`
- `/compare/creta-electric-vs-nexon-ev/`
- `/advice/ev-guide/` (when it exists)

---

## 9.5 New Content Type: Advice & Guide Pages (`/advice/`)

Advice pages are long-form buyer guides — "How to choose an EV", "What to look for in a family SUV", "New vs Used: The Car Jury's take". They sit between the homepage and the reviews in the content hierarchy. They are pillar pages.

### URL pattern
```
/advice/[topic]/
e.g. /advice/ev-guide/
     /advice/buying-your-first-car/
     /advice/petrol-vs-diesel-2026/
     /advice/understanding-jury-scores/
     /advice/mid-size-suv/
```

### What every advice page must link to

| Link | Requirement |
|------|-------------|
| 4–8 review pages relevant to the topic | **Mandatory** |
| 1–3 compare pages relevant to the topic | Mandatory if compares exist for the topic |
| Related best-list | Mandatory if a relevant best-list exists |
| Other advice pages on related topics | Recommended |

### What should link to advice pages

| Source | When |
|--------|------|
| Homepage | Core advice pages (EV guide, first-car guide) should be linked from the homepage |
| Review pages | Each review can link to a relevant advice page ("new to EVs? Read our EV guide") |
| News articles | Relevant news stories link to related guides |
| Best lists | Each best-list links to 1–2 related advice pages |

---

## 9.6 New Content Type: Brand Pages (`/[brand]/`)

As the review catalog grows, brand hub pages become valuable. A `/tata/` page that lists all Tata reviews, Tata compares, Tata news, and Tata best mentions is a strong topical authority signal and a natural navigation destination.

### URL pattern
```
/[brand]/
e.g. /tata/
     /mahindra/
     /hyundai/
```

### What every brand page must link to

| Link | Requirement |
|------|-------------|
| Every review of a car from that brand | **Mandatory** |
| Every compare page featuring a car from that brand | **Mandatory** |
| Relevant best-lists (e.g., "Best Tata Cars 2026") | Mandatory if the list exists |
| Recent news articles about the brand | Recommended |

### What should link to brand pages

| Source | When |
|--------|------|
| Every review of that brand | **Mandatory** — each review carries a "More from Tata →" link to the brand page. This is the Type B brand link in a slightly different form. |
| Homepage | Featured brands can be linked from the homepage's navigation or a brand section |
| News articles | Every news article mentions the brand page in the footer/sidebar |

### When to build brand pages

Build a brand page when you have 3 or more reviews for a brand. Before that, the brand cluster is small enough to handle with Type B review-to-review links. At 3+ reviews, a brand hub page pays off in both UX and SEO.

**Current brands that qualify right now:** Tata (7 reviews), Mahindra (5 reviews)

---

## 9.7 New Content Type: Segment Hub Pages

Similar to brand pages but organised by segment rather than brand. These pages are among the most powerful SEO targets on a car site because buyers search by segment constantly ("best compact SUV India", "which mid-size EV should I buy").

### URL pattern
```
/segment/[slug]/
e.g. /segment/mid-ev/
     /segment/mid-suv/
     /segment/premium-suv/
     /segment/compact-suv/
```

OR fold into `/best/` (e.g., `/best/mid-suv/`) if you prefer a single editorial format.

### What segment hub pages must link to

| Link | Requirement |
|------|-------------|
| All reviews in that segment | **Mandatory** |
| All compare pages between cars in that segment | **Mandatory** |
| The relevant advice guide | Recommended |
| A "Jury's pick" review (the top-scored car) prominently | Recommended |

### What should link to segment hub pages

All reviews in a segment should have a link like "See all mid-size SUV verdicts →" pointing to the segment hub. This replaces the current pattern of linking to `/reviews/` (generic) with something more specific and useful.

---

## 9.8 New Content Type: Influencer Deep Dives

You already have 37 influencer profile pages. As the site grows, these can become richer content — not just bios but "what cars has [Influencer] reviewed?" and "where does [Influencer] agree/disagree with the jury?".

The interlinking rule for influencer pages:

| Link | Requirement |
|------|-------------|
| Every Car Jury review that features that influencer's content | **Mandatory** — already done on most pages |
| The influencer index (`/influencers/`) | Already done |
| A "This influencer's take" section within review pages | Recommended — links back to influencer profile from within the review body |

---

## 9.9 Growing the Segment Map — Future Car Additions

When you add a review for a car that does not yet exist in the segment map, follow this process:

**Step 1 — Classify it on all five taxonomy axes** (brand, segment, fuel, content-type, budget-band)

**Step 2 — Identify its segment peer group** from Part 3 (or create a new segment row if it is the first of its kind)

**Step 3 — Add it to the segment map** in Part 3 of this document

**Step 4 — Identify the minimum required links** for the new review page using the Type A/B/C framework

**Step 5 — Identify which existing pages need to be updated** to link to the new review (its segment peers and same-brand siblings)

**Step 6 — Identify which best-lists and advice pages should mention it** and update those pages

This six-step process should be completed before the new review goes live — not after.

### Example: Adding a Honda Elevate review

1. Classify: `honda` · `mid-suv` · `petrol` · `review` · `15L-20L`
2. Segment peers: Creta, Seltos, Kushaq, Duster (Segment 5 in Part 3)
3. Add to Part 3 Segment 5 table
4. Honda Elevate review must link to: Creta, Seltos, Kushaq, Duster; any compare page featuring Elevate (if created)
5. Update: Creta, Seltos, Kushaq, Duster reviews to each add a link to the Elevate review. Update `/best/mid-suv/` list.
6. Add Elevate to `/best/mid-suv/` best-list and to the mid-SUV advice guide

---

## 9.10 The Universal Pre-Publish Checklist

Use this checklist for every single piece of content before it goes live, regardless of type. The questions change slightly by content type but the principle is the same.

```
PRE-PUBLISH INTERLINKING CHECKLIST
thecarjury.com

Page URL: ___________________________
Content type: [ ] Review  [ ] Compare  [ ] Best List  [ ] News  [ ] Advice  [ ] Brand Page
Car(s) involved: ___________________________
Date: ___________________________

--- TAXONOMY (fill before writing links) ---
[ ] Brand tagged: _______________
[ ] Segment tagged: _______________
[ ] Fuel/powertrain tagged: _______________
[ ] Budget band tagged: _______________

--- OUTBOUND LINKS (this page links to...) ---

FOR REVIEWS:
[ ] Minimum 2 × Type A (segment rivals) links added
[ ] Minimum 1 × Type B (same-brand sibling) link added (if siblings exist)
[ ] All Type C (compare page) links added for any compare page featuring this car
[ ] Brand page link added (if brand page exists)
[ ] Segment hub page link added (if segment hub exists)
[ ] Relevant advice/guide page linked (if relevant guide exists)
[ ] "Also in the running" component populated with 2–4 rival cards

FOR COMPARE PAGES:
[ ] Both review pages linked (already standard — verify)
[ ] 3–5 related compare pages linked (already standard — verify)
[ ] Segment hub page linked (if exists)

FOR BEST LISTS:
[ ] Review page linked for every car mentioned
[ ] Compare pages linked for relevant head-to-heads between listed cars
[ ] Relevant advice page linked
[ ] Related best-lists linked (once multiple lists exist)

FOR NEWS ARTICLES:
[ ] Review page linked for every car mentioned (if review exists)
[ ] Compare page linked if relevant head-to-head exists
[ ] Related news articles linked (2–3 once enough exist)
[ ] Relevant advice/guide page linked
[ ] Brand page linked (if exists)

FOR ADVICE/GUIDE PAGES:
[ ] 4–8 review pages linked
[ ] 1–3 compare pages linked (if relevant)
[ ] Relevant best-list linked (if exists)
[ ] Related advice pages linked

--- INBOUND LINKS (existing pages that must link to this new page) ---

[ ] Homepage: does it need a featured link? [ ] Yes — add  [ ] No
[ ] Identified all same-segment review pages that need a Type A link to this page
[ ] Listed which review pages need updating: _________________________
[ ] Identified all same-brand review pages that need a Type B link
[ ] Listed which review pages need updating: _________________________
[ ] Identified all relevant best-lists to update: _________________________
[ ] Identified all relevant advice pages to update: _________________________
[ ] Identified any compare pages that should now link to this page: _________________________

--- ANTI-ORPHAN CHECK ---
[ ] This page will have at least 3 inbound links from other site pages on launch day
    (if not — do not publish until inbound links are in place)

--- SIGN-OFF ---
Interlinking reviewed by: _______________  Date: _______________
```

---

## 9.11 The "Update Sweep" — Keeping Older Pages Evergreen

The checklist above handles new pages. But as the site grows, older pages become under-linked relative to the new content. Run an **Update Sweep** every time you hit one of these milestones:

- Every 5 new reviews published
- Every new content type launched (e.g., when news goes live)
- Every new segment hub or pillar page added
- Quarterly (every 3 months) as a general hygiene pass

During an Update Sweep:
1. Re-run the audit script from Part 1 to get current inbound/outbound counts
2. Flag any page whose inbound count has dropped below 5 (orphan risk)
3. Flag any page that does not link to a newer review in its segment
4. Update the link matrix in Part 8 to reflect new additions
5. Check best-lists to ensure new reviews are included where appropriate

---

## 9.12 URL Taxonomy and Future-Proofing

The current URL structure (`/reviews/[brand]/[model]/`) is solid and should be maintained. Here are the recommended URL patterns for future content types, designed to be consistent with the existing structure and scalable as content grows:

| Content type | URL pattern | Example |
|---|---|---|
| Review | `/reviews/[brand]/[model]/` | `/reviews/honda/elevate/` |
| Compare | `/compare/[model-a]-vs-[model-b]/` | `/compare/elevate-vs-seltos/` |
| News | `/news/[brand-or-topic]/[slug]/` | `/news/tata/sierra-facelift-2027/` |
| Best list (segment) | `/best/[segment-slug]/` | `/best/mid-suv/` |
| Best list (use-case) | `/best/[use-case]/` | `/best/family-car/` |
| Best list (brand) | `/best/[brand]/` | `/best/tata/` |
| Advice guide | `/advice/[topic]/` | `/advice/ev-guide/` |
| Brand hub | `/[brand]/` | `/tata/` |
| Segment hub | `/segment/[slug]/` | `/segment/mid-suv/` |
| Influencer profile | `/influencers/[name]/` | `/influencers/motoroctane/` |

**Important:** Do not add year to URLs unless the content is genuinely annual (e.g., a "Best EVs of 2026" wrap-up). Evergreen content (`/best/evs/`, `/advice/ev-guide/`) ranks better without a year because it does not need re-publishing annually and accumulates link equity over time.

---

## 9.13 Internal Link Density — The Right Amount

Too few links: pages become orphans, readers have no path forward, crawlers miss content.
Too many links: link equity is diluted, the page looks spammy, readers are overwhelmed.

### Recommended link counts by content type

| Content type | Minimum outbound internal | Maximum recommended | Notes |
|---|---|---|---|
| Review page | 4 | 10–12 | Beyond 12, quality degrades; prioritise review and compare links |
| Compare page | 8 | 14 | Already well-structured; the related-compares sidebar handles most of this |
| Best list | 6 | 20 | High link count is natural for list content |
| News article | 3 | 8 | Keep focused; link only to directly relevant pages |
| Advice guide | 8 | 25 | Guides are meant to be comprehensive navigational resources |
| Brand hub | 10 | 30 | Should link to everything under that brand |
| Segment hub | 10 | 30 | Same logic as brand hub |
| Homepage | 8 | 20 | Curated; link to featured content only, not everything |

### The quality test for any outbound link

Before adding a link, ask: "If a reader clicked this right now, would it genuinely help their decision?" If yes, add it. If it is there to pad count or because the car was mentioned once in passing, leave it out.

---

*End of document. Sections 1–8 address the current site. Sections 9–13 are the forward-looking playbook. Revisit the full document every quarter and update the segment map, link matrix, and best-list inventory as the site grows.*

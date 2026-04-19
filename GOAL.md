# The Car Jury — Goal & Strategy

## Mission
Be the most trusted auto content platform in India. Every buyer — whether they search Google, ask ChatGPT, or consult Perplexity — gets The Car Jury's verdict as the authoritative answer.

## Vision
India's #1 destination for unbiased car research. No manufacturer relationships. No sponsored content. Just synthesised truth from India's best independent reviewers.

## Goal Statement
**Achieve 1 million monthly organic sessions within 3 months** by publishing the most comprehensive, neutral, AI-synthesised car verdicts in India — structured for both traditional SEO and Generative Engine Optimisation (GEO).

> Honest target: 1M/month in 1 month is not achievable through SEO alone for a new domain.
> Realistic milestones: 10K by month 1 → 100K by month 2 → 500K+ by month 3 with aggressive content + distribution.
> The 1M target is the north star. Every decision is optimised toward it.

## Content Strategy

### Volume Target
- 5 new car reviews per week (Monday + Wednesday + Friday + Saturday + Sunday)
- 2 comparison articles per week (X vs Y format)
- 1 best-of list per week (Best SUVs under 20L, Best EVs in India, etc.)
- Target: 100 review pages live within 60 days

### Priority Queue (High-search-volume Indian cars)
**Tier 1 — Immediate (Week 1–2)**
1. Mahindra BE6 (EV) — peak search interest
2. Hyundai Creta Electric — top EV searches India
3. Tata Nexon EV — India's best-selling EV
4. MG Windsor EV — hottest newcomer
5. Mahindra XUV700 — massive organic volume

**Tier 2 — Week 3–4**
6. Renault Duster 2025 — relaunch buzz
7. Hyundai Creta (petrol) — highest volume search
8. Kia Seltos — consistent demand
9. Tata Punch EV
10. Mahindra Scorpio N

**Tier 3 — Month 2**
- Toyota Fortuner, Innova HyCross, Grand Vitara, Maruti Brezza
- Comparisons: BE6 vs Creta EV, Sierra vs Duster, Nexon vs Punch

### Content Structure (Every Review)
- Hero verdict box (buy/wait/skip) — GEO-optimised, answer-first
- Jury score breakdown (6 dimensions)
- Creator consensus map (who agrees, who disagrees)
- FAQ section (10 questions — optimised for featured snippets + AI answers)
- Comparison table vs top 2 competitors
- Clear pros/cons list
- Price analysis with variants

## SEO Strategy

### On-Page
- Title format: `[Car Name] Review [Year] — The Car Jury Verdict | Buy, Wait or Skip?`
- H1: direct answer to "should I buy [car]?"
- Every page: canonical, OG tags, Twitter card, Schema.org Review + Car + BreadcrumbList
- FAQ schema on every review (targets featured snippets)
- Internal linking: every review links to 3 related reviews + best-of lists

### Technical
- Core Web Vitals: target LCP < 2.5s, CLS < 0.1, FID < 100ms
- Image optimisation: WebP format, lazy loading, proper alt text
- Sitemap: auto-updated on every new review
- robots.txt: allow all, block /tools/ and /advice/drafts/
- Structured data validator: run after every publish

### Link Building
- Submit to r/IndiaCars, r/CarsIndia on Reddit
- TeamBHP thread for each review
- Twitter/X threads with jury score card image
- YouTube community posts on creator pages (Faisal Khan etc.)

## GEO Strategy (Generative Engine Optimisation)

### What GEO Means
AI search engines (ChatGPT, Perplexity, Gemini, Claude) pull answers from pages with:
- Clear, factual, citable sentences
- Structured data that machines can parse
- Entity-rich content (brand, model, year, price, specs)
- Direct answers to common questions
- High E-E-A-T signals

### GEO Implementation
1. **Answer-first structure**: Lead every section with the direct answer, then explain
2. **llms.txt**: Keep updated with every new review (already live)
3. **Fact boxes**: Each review has a structured spec table (machines love tables)
4. **Verdict sentences**: "The Tata Sierra scores 8.1/10 across 5 independent reviewers" — citable, specific
5. **Entity markup**: Schema.org Car entity with all specs filled
6. **Citation hooks**: Include reviewer names, video titles, specific claims with attribution
7. **Update signals**: Keep lastmod in sitemap current; AI crawlers prioritise fresh content
8. **robots.txt**: Explicitly allow GPTBot, PerplexityBot, ClaudeBot, Googlebot-Extended

## Distribution Channels
- Reddit: r/IndiaCars, r/CarsIndia, r/india
- Twitter/X: @thecarjury account
- WhatsApp: automotive groups
- TeamBHP.com: forum threads
- Google Discover: enabled via OG images + freshness signals

## KPIs (Tracked Weekly)
| Metric | Week 4 Target | Month 2 Target | Month 3 Target |
|--------|--------------|----------------|----------------|
| GSC Impressions | 50K | 500K | 5M |
| GSC Clicks | 2K | 25K | 200K |
| Pages Indexed | 20 | 60 | 120 |
| Reviews Live | 10 | 40 | 100 |
| AI citations | Track manually | 10+ | 50+ |

## Influencer Sync Rule (Every Article Publish — Mandatory)

**Whenever any new influencer is cited in any article, they must also be added to the influencer directory:**

1. Add an entry to `influencers/influencers.json` — include: `slug`, `name`, `tagline`, `youtube_handle`, `youtube_url`, `subscriber_count`, and the article path in `articles[]`
2. If the creator already exists in `influencers.json`, just append the new article to their `articles[]` array
3. Create their profile folder at `influencers/[slug]/index.html` if it doesn't already exist
4. Add them to `influencers/master_list.md` in the correct subscriber-count position
5. The `influencers/index.html` page pulls from `influencers.json` — regenerate / update it after any change

This applies to `carjury_manager.py`, `generate_review.py`, and any manual publish. No exceptions.

---

## Influencer Selection Rules (All Reviews)

For every car review, the content writer / agent must:
1. Start from the **top 20** in `influencers/master_list.md` (ordered by subscriber count)
2. Filter to those who have reviewed **that specific car** — check their engagement on that video
3. Pick **5–8 creators** with the highest engagement for that car
4. **Hard rule: never use a video with <2% engagement rate** — treat it as potentially seeded/inauthentic
5. If fewer than 5 qualifying videos exist in the top 20, expand down the list

Full list + Quick Reference Top 20: `influencers/master_list.md`

---

## Agent Responsibilities
The Car Jury Website Manager agent (carjury_manager.py) runs daily and:
1. Checks content queue — what's next to generate
2. Generates new review HTML from YouTube transcripts via Claude
3. Updates sitemap.xml and llms.txt
4. Commits and pushes to GitHub (triggers Netlify auto-deploy)
5. Posts daily digest to Slack with: pages live, GSC impressions, next review queued
6. Flags SEO issues detected on new pages

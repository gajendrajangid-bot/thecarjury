# The Car Jury — Agentic AI Architecture

**thecarjury.com** | India's aggregated car review platform  
*Last updated: April 2026*

---

## Overview

The Car Jury runs a fully autonomous content + distribution pipeline powered by 12 specialised AI agents. A single article — from YouTube transcripts to live production — requires zero human intervention unless quality gates fail. The system self-heals, self-reports, and asks for approval only at critical promotion decisions.

---

## System Architecture Diagram

```
DAILY SCHEDULE (9AM)
─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │                    CARJURY MANAGER AGENT                           │
  │                  carjury_manager.py  [9AM daily]                   │
  │   Master orchestrator — runs every step below in sequence          │
  └──────┬──────────────────────────────────────────────────────────────┘
         │
         ├─── Step 0: PUBLISH ONE PIECE
         │         ↓
         │    ┌──────────────────────┐    ┌──────────────────────────┐
         │    │  REVIEW GENERATOR    │ or │   COMPARE GENERATOR      │
         │    │  generate_review.py  │    │  generate_compare.py     │
         │    │                      │    │                          │
         │    │  YouTube transcripts │    │  Side-by-side comparison │
         │    │  → Claude synthesis  │    │  of two published cars   │
         │    │  → HTML + Schema     │    │  → HTML + Schema         │
         │    └──────────────────────┘    └──────────────────────────┘
         │
         ├─── Step 1: SEO HEALTH CHECK (local HTML scan)
         │         Checks: title tags, canonical, schema, GSC verification tag
         │
         ├─── Step 1b: INDEX WATCHDOG
         │         ┌─────────────────────────────┐
         │         │   index_watchdog.py          │
         │         │   Fetches all 45+ sitemap    │
         │         │   URLs live — checks for     │
         │         │   noindex, HTTP errors,      │
         │         │   canonical mismatches,      │
         │         │   redirects                  │
         │         │   → WA alert on new issues   │
         │         └─────────────────────────────┘
         │
         ├─── Step 2: ROBOTS.TXT GEO UPDATE
         │         Ensures GPTBot, PerplexityBot, ClaudeBot, anthropic-ai are allowed
         │
         ├─── Step 3: SITEMAP REBUILD + SEARCH ENGINE PINGS
         │         4 sub-sitemaps: core / reviews / compare / influencers
         │         Content-hash-driven lastmod (dates only advance on real changes)
         │         → IndexNow ping (Bing) on new publish
         │         → GSC API sitemap submit
         │
         ├─── Step 4: CONTENT REBUILDS
         │         llms.txt update (AI search engine readable content manifest)
         │         Reviews index page rebuild (/reviews/)
         │         Homepage sidebar regeneration
         │         Influencer profile pages rebuild
         │
         ├─── Step 5: GIT PUSH + STAGING DEPLOY
         │         xbot repo → push to origin/main
         │         rsync carjury/ → ~/thecarjury repo → force push to staging branch
         │         → Cloudflare Pages builds staging preview
         │         → Spawns CARJURY GATE in background ↓
         │
         └─── Step 6: SLACK DIGEST → #carjury
                   Daily report: publish status, content count, SEO issues,
                   deploy status, index watchdog summary


STAGING GATE (event-triggered, after every push)
─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │                      CARJURY GATE                                  │
  │                  carjury_gate.py  [spawned after push]             │
  └──────┬──────────────────────────────────────────────────────────────┘
         │
         ├── Waits for Cloudflare staging build to complete
         ├── Runs QA checks against live staging URL
         ├── On PASS  → promotes staging → main (production)
         │             → Cloudflare auto-deploys production
         └── On FAIL  → WA alert to owner + Slack alert
                        Promotion BLOCKED until owner approves


POST-PUBLISH AGENT SUITE (run_agents.py — called after each new review)
─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │                     RUN AGENTS ORCHESTRATOR                        │
  │                  run_agents.py  [called by manager on new publish] │
  └──────┬──────────────────────────────────────────────────────────────┘
         │
         ├── Phase 0:  IMAGE AGENT          (image_agent.py)
         │             Validates hero image: WebP, right dimensions, <300KB
         │             Claude vision: verifies it's an exterior car shot
         │             If wrong/missing: sources replacement from OEM → auto media → CDN
         │
         ├── Phase 1:  QA AGENT             (qa_agent.py)           ─┐ parallel
         │             Content quality, accuracy, readability,        │
         │             word count (<2000), no em-dashes, completeness │
         │                                                             │
         │             SEO AGENT            (seo_agent.py)           ─┘ parallel
         │             On-page SEO, schema markup, keyword presence,
         │             GEO readiness (AI search engine optimisation)
         │
         ├── Phase 2:  TECH SEO AGENT       (tech_seo_agent.py)
         │             PageSpeed Insights API: LCP, INP, CLS
         │             Mobile + desktop performance scores
         │             Broken link detection, canonical health
         │
         ├── Phase 3:  ANALYTICS AGENT      (analytics_agent.py)
         │             GSC: clicks, impressions, CTR, avg position
         │             Post-publish performance tracking
         │
         └── Phase 4:  EDITORIAL AGENT      (editorial_agent.py)     Claude-powered
                       Site-wide content cluster analysis
                       Identifies gaps, recommends next cars to review
                       Suggests compare/best/advice pages needed
                       → Posts consolidated report to #carjury Slack


SOCIAL MEDIA AGENT (scheduled independently)
─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │                    SOCIAL AGENT (@the_car_jury on X)               │
  │          social_agent.py  [9AM daily scan + 7PM digest]            │
  └──────┬──────────────────────────────────────────────────────────────┘
         │
         ├── 9AM: Scans trending Indian auto topics on X
         │        Replies to relevant tweets (max 5/day)
         │        Posts original tweets (max 2/day)
         │        Auto-follows relevant accounts
         │        Rules: authority voice only, no hashtags in replies
         │
         └── 7PM: Evening digest → WhatsApp + Slack


QUALITY SCORING AGENT (on-demand)
─────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │                  E-E-A-T SCORING AGENT                             │
  │               eeat_agent.py  [on-demand / --all mode]             │
  └─────────────────────────────────────────────────────────────────────┘
         Google E-E-A-T framework: Experience, Expertise,
         Authoritativeness, Trustworthiness
         Claude-powered scoring + recommendations
         Can run against a single review or all published reviews


ALWAYS-ON SERVICES
─────────────────────────────────────────────────────────────────────────────

  dashboard.py          → xbot.thecarjury.com (port 8767)
                          CMS | Analytics | Feedback | Influencer clicks
                          Cloudflare Tunnel for public access

  carjury_manager.log   → Full run log for every agent step
  carjury_gate.log      → Gate run log
  carjury_social.log    → Social agent log


CONTENT PIPELINE: YouTube → Production
─────────────────────────────────────────────────────────────────────────────

  1. Research Agent    → Finds 5-8 YouTube videos for target car
                         Scores by engagement rate (hard cutoff: <2% ER rejected)
                         Always starts from top 20 in influencers/master_list.md
                         Posts Option A summary to #carjury Slack for approval

  2. Review Generator  → Fetches YouTube transcripts (youtube-transcript-api)
                         Claude Opus synthesis: 100,000+ words → structured verdict
                         6-dimension jury score: Design / Interior / Performance /
                         Ride / Build Quality / Value
                         Outputs: HTML + Schema.org (Review + Car + FAQ + BreadcrumbList)
                         Auto-converts all images to WebP (quality 82)
                         Enforces: <2000 words, no em-dashes, authority voice

  3. Run Agents        → Image QA → QA + SEO (parallel) → Tech SEO →
                         Analytics → Editorial

  4. Git Push          → Xbot repo (origin/main)
                         Rsync → thecarjury repo (staging branch)

  5. Gate              → Waits for Cloudflare staging build
                         Runs checks on live staging URL
                         Promotes staging → main (production) on pass

  6. Production        → Cloudflare Pages auto-deploys from main branch
                         DNS: Namecheap → 75.2.60.5

  7. Influencer Sync   → New influencer added to: influencers.json +
                         master_list.md + individual profile page at
                         /influencers/[slug]/


DEPLOYMENT RULE (HARDCODED)
─────────────────────────────────────────────────────────────────────────────

  staging → production promotion ALWAYS requires explicit owner approval.

  Gate sends WA status report to owner and waits for "push" reply.
  --promote-only may only run after owner gives explicit approval in session.
  Prior approvals do NOT carry over to future sessions.


TECH STACK
─────────────────────────────────────────────────────────────────────────────

  Site:           Plain HTML/CSS, no framework, no CMS
  Hosting:        Cloudflare Pages (GitHub auto-deploy)
  AI Model:       Claude claude-opus-4-7 (Anthropic API)
  Transcripts:    youtube-transcript-api
  Search:         Google Search Console API (jangid@gmail.com)
  Analytics:      Google Analytics (G-0LV8GN0CD5)
  Indexing:       IndexNow (Bing + engines), GSC sitemap API
  Scheduler:      macOS launchd (all agents)
  Alerts:         WhatsApp (wa_send.py) + Slack bot
  Dashboard:      Flask + Cloudflare Tunnel (xbot.thecarjury.com)
  Domain:         Namecheap (expires Apr 2027)


AGENT SCHEDULE SUMMARY
─────────────────────────────────────────────────────────────────────────────

  9:00 AM   carjury_manager.py       Daily orchestrator (publish + SEO + deploy)
  9:00 AM   social_agent.py          X scan + reply + follow
  7:00 PM   social_agent.py --digest Evening social digest → WA + Slack
  Always    dashboard.py             CMS + analytics web app
  On push   carjury_gate.py          Staging QA + production promotion
  On demand run_agents.py            Full agent suite on a new review
  On demand eeat_agent.py            E-E-A-T scoring (single or all reviews)
  On demand research_agent.py        YouTube source research for next car


CONTENT IN PRODUCTION (April 2026)
─────────────────────────────────────────────────────────────────────────────

  Reviews live:  Tata Sierra, Mahindra BE6, Tata Punch,
                 Hyundai Creta Electric, Tata Nexon EV,
                 Hyundai Creta, Renault Duster,
                 Skoda Kushaq, Maruti e Vitara  (9 reviews)

  Compare pages: Creta Electric vs e Vitara (live)

  Priority queue: MG Windsor EV, Mahindra XUV700, Kia Seltos,
                  Mahindra Scorpio N


URL STRUCTURE (locked)
─────────────────────────────────────────────────────────────────────────────

  /reviews/[brand]/[model]/          Review hub
  /reviews/[brand]/[model-ev]/       EV as separate sibling
  /compare/[car1]-vs-[car2]/         Head-to-head comparisons
  /best/[category-india]/            Best-of lists
  /advice/[topic]/                   Buying guides
  /influencers/[slug]/               Influencer profiles
  /the-jury/                         Full jury roster
```

---

*Architecture document — The Car Jury Agentic OS*  
*Master strategy doc: https://docs.google.com/document/d/1rWrGoEsKDH6fuG5JmPOgeIiCDqdPiD9K4batvSE7ls4*

# TCJ Forum — Setup Guide

## Prerequisites

1. **Cloudflare account** with Workers, D1, KV, and R2 enabled
2. **Node.js 18+** installed (you have 22 — good)
3. **Wrangler** CLI — the deploy script installs it if missing
4. **Resend account** (optional at launch) — free tier at resend.com

---

## Step 1 — Deploy the API

```bash
cd carjury/forum-api
npm install
bash deploy.sh
```

The script:
- Creates the D1 database and patches `wrangler.toml` with the ID
- Creates the KV namespace and patches `wrangler.toml`
- Creates the R2 bucket for avatars
- Runs the SQL schema (creates all tables + seeds 6 categories)
- Prompts for secrets (JWT_SECRET, WEBHOOK_SECRET, optional Resend + Slack)
- Deploys the Worker
- Runs a health check

**Generate a strong JWT_SECRET:**
```bash
openssl rand -base64 48
```

---

## Step 2 — Deploy the frontend pages

The forum HTML pages live in `carjury/forum/`. They need to be deployed
alongside the main site on Cloudflare Pages.

If your Pages project already deploys from the `carjury/` directory, the
`/forum/` folder will be picked up automatically on next deploy.

Copy the shared CSS into place:
```bash
cp carjury/forum-api/src/forum.css carjury/forum/forum.css
```

Then deploy as normal:
```bash
cd carjury && git add forum/ && git commit -m "Add forum frontend" && git push
```

---

## Step 3 — Create your admin account

1. Go to `https://www.thecarjury.com/forum/register/`
2. Register with your email: `gajendra.jangid@cars24.com`
3. Verify your email (check inbox)
4. Promote yourself to admin in D1:

```bash
wrangler d1 execute tcj-forum --command="UPDATE users SET role='admin' WHERE email='gajendra.jangid@cars24.com'"
```

---

## Step 4 — Wire up carjury_manager.py

Add this to `carjury_manager.py` after a review is published:

```python
import requests

def notify_forum_review_published(brand, model, display_name, score, verdict):
    """Tell the forum API to auto-create a verdict discussion thread."""
    webhook_url = "https://tcj-forum.YOUR_SUBDOMAIN.workers.dev/api/forum/webhook/review-published"
    secret = os.environ.get("TCJ_FORUM_WEBHOOK_SECRET")  # same as WEBHOOK_SECRET in wrangler
    try:
        res = requests.post(webhook_url, json={
            "brand": brand,
            "model": model,
            "displayName": display_name,
            "score": score,
            "verdict": verdict,
        }, headers={"X-TCJ-Secret": secret}, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("threadUrl")
    except Exception as e:
        print(f"Forum webhook failed: {e}")
        return None
```

Call it right after `carjury_gate.py --promote-only` succeeds and export
`TCJ_FORUM_WEBHOOK_SECRET` in your environment matching the `WEBHOOK_SECRET`
you set during deploy.

For compare pages, call `/api/forum/webhook/compare-published` with:
```python
{"compareSlug": slug, "carAName": "...", "carBName": "...", "carAScore": 8.1, "carBScore": 7.9}
```

---

## Step 5 — Add `forum-cta` to review pages

In `generate_review.py`, after the HTML is built, add this block immediately
before the jury credits section (`<!-- jury-credits -->`):

```python
forum_thread_url = notify_forum_review_published(brand, model, display_name, score, verdict)
if forum_thread_url:
    forum_cta = f"""
    <div class="forum-cta">
      <div class="eyebrow">Join the debate</div>
      <p>Agree with the jury? Spot something they missed?</p>
      <a href="{forum_thread_url}" class="forum-link">Read the discussion →</a>
    </div>"""
    html = html.replace('<!-- jury-credits -->', forum_cta + '<!-- jury-credits -->')
```

---

## Custom domain (optional)

To serve the API at `api.thecarjury.com/forum/` instead of `*.workers.dev`,
add a route in `wrangler.toml`:

```toml
routes = [
  { pattern = "www.thecarjury.com/api/forum/*", zone_name = "thecarjury.com" }
]
```

---

## Secrets reference

| Secret | Required | Description |
|--------|----------|-------------|
| `JWT_SECRET` | Yes | Long random string for signing JWTs. Never rotate without invalidating KV sessions. |
| `WEBHOOK_SECRET` | Yes | Shared with carjury_manager.py. Match exactly. |
| `RESEND_API_KEY` | Optional | From resend.com — enables verification + digest emails |
| `SLACK_WEBHOOK_URL` | Optional | From Slack app — enables mod alerts + weekly reports |

View/update secrets any time:
```bash
wrangler secret list
wrangler secret put JWT_SECRET
```

---

## Useful D1 queries

```bash
# List all users
wrangler d1 execute tcj-forum --command="SELECT id, username, email, role, created_at FROM users"

# Promote a user to moderator
wrangler d1 execute tcj-forum --command="UPDATE users SET role='moderator' WHERE username='trustworthy_user'"

# See mod queue
wrangler d1 execute tcj-forum --command="SELECT p.id, p.body, u.username FROM posts p JOIN users u ON p.author_id=u.id WHERE p.is_approved=0 AND p.is_deleted=0"

# See recent reports
wrangler d1 execute tcj-forum --command="SELECT * FROM reports WHERE is_resolved=0 ORDER BY created_at DESC LIMIT 10"
```

---

## Troubleshooting

**Health check fails:**
```bash
curl https://tcj-forum.YOUR_SUBDOMAIN.workers.dev/api/forum/health
# Should return: {"ok":true,"version":"1.0.0","ts":...}
```

**Database error on startup:**
- Check D1 ID in `wrangler.toml` matches the created database
- Re-run schema: `wrangler d1 execute tcj-forum --file=./schema.sql`

**Sessions not working:**
- Verify KV namespace ID in `wrangler.toml`
- Check JWT_SECRET is set: `wrangler secret list`

**Emails not sending:**
- Confirm RESEND_API_KEY is set and Resend domain `thecarjury.com` is verified
- Check Resend dashboard for delivery logs

Full troubleshooting playbooks: `FORUM_AGENT_BRIEF.md` → Section 9

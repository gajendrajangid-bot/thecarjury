#!/usr/bin/env bash
# TCJ Forum — one-shot deploy script
# Run from: carjury/forum-api/
# Requires: wrangler installed + authenticated (wrangler login)

set -e
echo ""
echo "=== TCJ Forum Deploy ==="
echo ""

# 1. Install wrangler if missing
if ! command -v wrangler &>/dev/null; then
  echo "→ Installing wrangler..."
  npm install -g wrangler
fi

# 2. Create D1 database
echo "→ Creating D1 database 'tcj-forum'..."
D1_OUTPUT=$(wrangler d1 create tcj-forum 2>&1 || true)
echo "$D1_OUTPUT"
D1_ID=$(echo "$D1_OUTPUT" | grep -o 'database_id = "[^"]*"' | grep -o '"[^"]*"$' | tr -d '"')
if [ -n "$D1_ID" ]; then
  echo "  D1 ID: $D1_ID"
  sed -i.bak "s/REPLACE_WITH_YOUR_D1_ID/$D1_ID/" wrangler.toml
fi

# 3. Create KV namespace
echo "→ Creating KV namespace 'tcj-forum-kv'..."
KV_OUTPUT=$(wrangler kv:namespace create tcj-forum-kv 2>&1 || true)
echo "$KV_OUTPUT"
KV_ID=$(echo "$KV_OUTPUT" | grep -o '"id": "[^"]*"' | grep -o '"[^"]*"$' | tr -d '"')
if [ -n "$KV_ID" ]; then
  echo "  KV ID: $KV_ID"
  sed -i.bak "s/REPLACE_WITH_YOUR_KV_ID/$KV_ID/" wrangler.toml
fi

# 4. Create R2 bucket
echo "→ Creating R2 bucket 'tcj-forum-media'..."
wrangler r2 bucket create tcj-forum-media 2>&1 || true

# 5. Run schema
echo "→ Running database schema..."
wrangler d1 execute tcj-forum --file=./schema.sql

# 6. Set secrets
echo ""
echo "=== Secrets setup ==="
echo "You will be prompted to enter each secret. Press Enter to skip optional ones."
echo ""

echo "→ JWT_SECRET (required — generate a long random string):"
wrangler secret put JWT_SECRET

echo "→ WEBHOOK_SECRET (required — shared with carjury_manager.py):"
wrangler secret put WEBHOOK_SECRET

echo "→ RESEND_API_KEY (optional — skip if not using email yet):"
read -p "  Enter RESEND_API_KEY (or press Enter to skip): " RESEND_KEY
if [ -n "$RESEND_KEY" ]; then
  echo "$RESEND_KEY" | wrangler secret put RESEND_API_KEY
fi

echo "→ SLACK_WEBHOOK_URL (optional — skip if not using Slack yet):"
read -p "  Enter SLACK_WEBHOOK_URL (or press Enter to skip): " SLACK_URL
if [ -n "$SLACK_URL" ]; then
  echo "$SLACK_URL" | wrangler secret put SLACK_WEBHOOK_URL
fi

# 7. Deploy
echo ""
echo "→ Deploying worker..."
wrangler deploy

# 8. Health check
echo ""
echo "→ Running health check..."
sleep 3
WORKER_URL=$(wrangler deploy --dry-run 2>&1 | grep -o 'https://[^ ]*workers.dev' | head -1 || true)
if [ -n "$WORKER_URL" ]; then
  curl -s "${WORKER_URL}/api/forum/health" | python3 -m json.tool
fi

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Next steps:"
echo "  1. Copy forum/ HTML files to your Cloudflare Pages project"
echo "  2. Copy forum.css to forum/ directory"
echo "  3. Create your admin account at: https://www.thecarjury.com/forum/register/"
echo "  4. Verify your email, then update your role in D1:"
echo "     wrangler d1 execute tcj-forum --command=\"UPDATE users SET role='admin' WHERE email='gajendra.jangid@cars24.com'\""
echo "  5. Add the webhook call to carjury_manager.py (see SETUP.md)"
echo ""

// TCJ Forum API — main entry point
// Routes all /api/forum/* requests to the correct worker

import { handleAuth }    from './workers/auth.js';
import { handleForum, notifySlack }   from './workers/forum.js';
import { handleMod }     from './workers/mod.js';
import { handleUser }    from './workers/user.js';
import { handleWebhook } from './workers/webhook.js';
import { handleOptions, json, err } from './utils/response.js';

export default {
  async fetch(request, env, ctx) {
    const url    = new URL(request.url);
    const path   = url.pathname;

    // CORS preflight
    if (request.method === 'OPTIONS') return handleOptions();

    // Health check
    if (path === '/api/forum/health') {
      return json({ ok: true, version: env.FORUM_VERSION || '1.0.0', ts: Date.now() });
    }

    // Route to workers
    try {
      if (path.startsWith('/api/forum/auth/'))    return handleAuth(path.replace('/api/forum/auth', ''), request, env);
      if (path.startsWith('/api/forum/mod/'))     return handleMod(path.replace('/api/forum/mod', ''), request, env);
      if (path.startsWith('/api/forum/user/'))    return handleUser(path.replace('/api/forum/user', ''), request, env);
      if (path.startsWith('/api/forum/me'))       return handleUser(path.replace('/api/forum', ''), request, env);
      if (path.startsWith('/api/forum/webhook/')) return handleWebhook(path.replace('/api/forum/webhook', ''), request, env);
      if (path.startsWith('/api/forum/'))         return handleForum(path.replace('/api/forum', ''), request, env);
    } catch (e) {
      console.error('Unhandled error:', e);
      await notifySlack(env, `🔴 Forum API error: ${e.message} (${path})`).catch(() => {});
      return err('Internal server error', 500);
    }

    return err('Not found', 404);
  },

  // ── Cron scheduler ──────────────────────────────────────────────────────
  async scheduled(event, env, ctx) {
    const cron = event.cron;
    console.log(`Cron fired: ${cron}`);

    // Every 6 hours — mod queue check + spam blocklist refresh
    if (cron === '0 */6 * * *') {
      await runModQueueCheck(env);
      await refreshSpamBlocklist(env);
    }

    // Daily at 03:00 IST (21:30 UTC prev day) — digest emails + orphan thread check
    if (cron === '30 21 * * *') {
      await sendDailyDigests(env);
      await checkOrphanThreads(env);
      await cleanExpiredSessions(env);
    }

    // Weekly Sunday — activity report
    if (cron === '0 0 * * 0') {
      await sendWeeklyReport(env);
    }
  },
};

// ── Cron jobs ──────────────────────────────────────────────────────────────

async function runModQueueCheck(env) {
  const pendingRow = await env.DB.prepare(
    'SELECT COUNT(*) AS n FROM posts WHERE is_approved = 0 AND is_deleted = 0'
  ).first();
  const reportRow = await env.DB.prepare(
    'SELECT COUNT(*) AS n FROM reports WHERE is_resolved = 0'
  ).first();

  const pending = pendingRow?.n || 0;
  const reports = reportRow?.n || 0;

  if (pending > 0 || reports > 0) {
    await notifySlack(env,
      `📋 *Mod queue:* ${pending} post(s) awaiting approval · ${reports} open report(s)\n` +
      `Review at: https://www.thecarjury.com/forum/mod/`
    );
  }

  // Auto-remove posts from known spam domains
  const blocklist = await env.KV.get('spam:domains', 'json') || [];
  if (blocklist.length > 0) {
    for (const domain of blocklist) {
      await env.DB.prepare(`
        UPDATE posts SET is_deleted = 1, delete_reason = 'Auto-removed: spam domain'
        WHERE body LIKE ? AND is_deleted = 0
      `).bind(`%${domain}%`).run();
    }
  }
}

async function refreshSpamBlocklist(env) {
  // Fetch Spamhaus DROP list (plain text, one CIDR per line)
  // For domains we maintain a manual list in KV; auto-refresh could pull from a public feed
  // For now: ensure the KV key exists with at least an empty array
  const existing = await env.KV.get('spam:domains');
  if (!existing) {
    await env.KV.put('spam:domains', JSON.stringify([]), { expirationTtl: 86400 * 7 });
  }
}

async function sendDailyDigests(env) {
  // Find users with unsent notifications who have email_digest = 1
  const { results: users } = await env.DB.prepare(`
    SELECT DISTINCT u.id, u.email, u.username
    FROM notifications n
    JOIN users u ON n.user_id = u.id
    WHERE n.is_sent = 0 AND u.email_digest = 1 AND u.is_verified = 1
    LIMIT 100
  `).all();

  for (const user of (users || [])) {
    const { results: notifs } = await env.DB.prepare(`
      SELECT n.type, t.title, t.slug AS thread_slug
      FROM notifications n
      JOIN threads t ON n.thread_id = t.id
      WHERE n.user_id = ? AND n.is_sent = 0
      LIMIT 10
    `).bind(user.id).all();

    if (!notifs || notifs.length === 0) continue;

    // Send digest email via Resend
    if (env.RESEND_API_KEY) {
      const items = notifs.map(n =>
        `<li><a href="https://www.thecarjury.com/forum/t/${n.thread_slug}/">${n.thread_title}</a></li>`
      ).join('');

      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from: 'The Car Jury Forum <forum@thecarjury.com>',
          to: user.email,
          subject: `${notifs.length} new repl${notifs.length === 1 ? 'y' : 'ies'} in your threads`,
          html: `<div style="font-family:Georgia,serif;max-width:480px;color:#1A1A1A">
            <p style="font-size:11px;color:#C8102E;font-family:Arial,sans-serif;letter-spacing:0.08em;text-transform:uppercase">THE CAR JURY · FORUM DIGEST</p>
            <p style="font-size:17px;line-height:1.7">New activity in threads you've joined, ${user.username}:</p>
            <ul style="font-size:15px;line-height:2">${items}</ul>
            <a href="https://www.thecarjury.com/forum/" style="display:inline-block;background:#C8102E;color:#fff;padding:10px 20px;border-radius:6px;font-family:Arial,sans-serif;font-size:13px;text-decoration:none">Visit the forum →</a>
            <p style="font-size:12px;color:#6B6B6B;margin-top:24px;font-family:Arial,sans-serif">
              <a href="https://www.thecarjury.com/forum/me/" style="color:#6B6B6B">Manage email preferences</a>
            </p>
          </div>`,
        }),
      }).catch(e => console.error('Digest email failed:', e));
    }

    // Mark notifications as sent
    await env.DB.prepare('UPDATE notifications SET is_sent = 1 WHERE user_id = ? AND is_sent = 0')
      .bind(user.id).run();
  }
}

async function checkOrphanThreads(env) {
  // Find review threads where the review_slug exists in DB but thread was never created
  // This is mainly a safety net — webhook handles it on publish
  // We log any is_review_thread = 0 rows that have review_slug set (shouldn't happen)
  const { results } = await env.DB.prepare(`
    SELECT id, slug, review_slug FROM threads
    WHERE review_slug IS NOT NULL AND is_review_thread = 0
    LIMIT 20
  `).all();

  if (results && results.length > 0) {
    await notifySlack(env, `⚠️ Orphan thread check: ${results.length} review threads with inconsistent flags. Check /forum/mod/log`);
  }
}

async function cleanExpiredSessions(env) {
  // D1 sessions table (audit trail) — purge records older than 31 days
  const cutoff = Math.floor(Date.now() / 1000) - (31 * 86400);
  await env.DB.prepare('DELETE FROM sessions WHERE expires_at < ?').bind(cutoff).run();
}

async function sendWeeklyReport(env) {
  const cutoff = Math.floor(Date.now() / 1000) - (7 * 86400);

  const newUsers   = await env.DB.prepare('SELECT COUNT(*) AS n FROM users WHERE created_at > ?').bind(cutoff).first();
  const newPosts   = await env.DB.prepare('SELECT COUNT(*) AS n FROM posts WHERE created_at > ? AND is_approved = 1').bind(cutoff).first();
  const newThreads = await env.DB.prepare('SELECT COUNT(*) AS n FROM threads WHERE created_at > ?').bind(cutoff).first();
  const removed    = await env.DB.prepare('SELECT COUNT(*) AS n FROM posts WHERE is_deleted = 1 AND created_at > ?').bind(cutoff).first();

  const { results: topThreads } = await env.DB.prepare(`
    SELECT title, reply_count, view_count FROM threads
    WHERE created_at > ? ORDER BY reply_count DESC LIMIT 3
  `).bind(cutoff).all();

  const topList = (topThreads || []).map(t =>
    `• "${t.title}" — ${t.reply_count} replies, ${t.view_count} views`
  ).join('\n');

  await notifySlack(env,
    `📊 *TCJ Forum — Weekly summary*\n` +
    `New members: ${newUsers?.n || 0} | New posts: ${newPosts?.n || 0} | New threads: ${newThreads?.n || 0} | Removed posts: ${removed?.n || 0}\n\n` +
    `*Top threads this week:*\n${topList || 'None yet'}`
  );
}

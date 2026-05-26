// Webhook worker — receives publish triggers from carjury_manager.py
// Creates verdict/compare threads automatically on new review/compare publish

import { json, err, ok, now } from '../utils/response.js';
import { notifySlack } from './forum.js';
import { readFileSync } from 'fs';

export async function handleWebhook(path, request, env) {
  // Verify shared secret from carjury_manager.py
  const secret = request.headers.get('X-TCJ-Secret');
  if (!secret || secret !== env.WEBHOOK_SECRET)
    return err('Unauthorized', 401);

  if (request.method === 'POST' && path === '/review-published')
    return onReviewPublished(request, env);
  if (request.method === 'POST' && path === '/compare-published')
    return onComparePublished(request, env);

  return err('Not found', 404);
}

// ── New review published ───────────────────────────────────────────────────

async function onReviewPublished(request, env) {
  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  const { brand, model, displayName, score, verdict } = body;
  if (!brand || !model) return err('brand and model required');

  const reviewSlug  = `${brand}/${model}`;
  const threadSlug  = `verdict-${brand}-${model}`;
  const title       = `Verdict discussion: ${displayName || `${brand} ${model}`}`;

  // Check if thread already exists
  const existing = await env.DB.prepare('SELECT id FROM threads WHERE slug = ?')
    .bind(threadSlug).first();
  if (existing) return ok({ threadSlug, created: false, message: 'Thread already exists' });

  // Get verdicts category
  const category = await env.DB.prepare("SELECT id FROM categories WHERE slug = 'verdicts'").first();
  if (!category) return err('Verdicts category not found', 500);

  // Get or create TCJ system user (author_id = 1, the admin account)
  const adminUser = await env.DB.prepare("SELECT id FROM users WHERE role = 'admin' LIMIT 1").first();
  if (!adminUser) return err('No admin user found — create admin account first', 500);

  const ts = now();

  // Build the opening post body
  const verdictLine = score
    ? `**Jury score: ${score}/10 · ${verdict || 'See verdict'}**`
    : `**Verdict now published.**`;

  const openingPost = `${verdictLine}

The jury has delivered its verdict on the **${displayName || model}**. Read the full analysis, scoring breakdown, and Buy · Wait · Skip recommendation on the review page.

👉 [Read the full verdict](https://www.thecarjury.com/reviews/${reviewSlug}/)

---

**Join the debate:** Do you agree with the jury? Have you driven or owned this car? Share your experience — and cite your source if you're making a factual claim. The jury weighs evidence, and so does this community.`;

  const threadResult = await env.DB.prepare(`
    INSERT INTO threads
      (slug, title, category_id, author_id, is_review_thread, review_slug,
       is_pinned, last_post_at, created_at)
    VALUES (?, ?, ?, ?, 1, ?, 1, ?, ?)
  `).bind(threadSlug, title, category.id, adminUser.id, reviewSlug, ts, ts).run();

  const threadId = threadResult.meta.last_row_id;

  // Create pinned opening post (auto-approved, authored by system)
  await env.DB.prepare(`
    INSERT INTO posts (thread_id, author_id, body, is_approved, created_at)
    VALUES (?, ?, ?, 1, ?)
  `).bind(threadId, adminUser.id, openingPost, ts).run();

  // Update category counters
  await env.DB.prepare('UPDATE categories SET thread_count = thread_count + 1 WHERE id = ?')
    .bind(category.id).run();

  await notifySlack(env, `🏛️ New verdict thread created: *${title}* → https://www.thecarjury.com/forum/t/${threadSlug}/`);

  return ok({
    threadSlug,
    threadUrl: `https://www.thecarjury.com/forum/t/${threadSlug}/`,
    created: true,
  });
}

// ── New compare page published ─────────────────────────────────────────────

async function onComparePublished(request, env) {
  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  const { compareSlug, carAName, carBName, carAScore, carBScore } = body;
  if (!compareSlug || !carAName || !carBName) return err('compareSlug, carAName, carBName required');

  const threadSlug = `compare-${compareSlug}`;
  const title      = `${carAName} vs ${carBName} — what does the jury miss?`;

  const existing = await env.DB.prepare('SELECT id FROM threads WHERE slug = ?')
    .bind(threadSlug).first();
  if (existing) return ok({ threadSlug, created: false });

  const category = await env.DB.prepare("SELECT id FROM categories WHERE slug = 'comparisons'").first();
  if (!category) return err('Comparisons category not found', 500);

  const adminUser = await env.DB.prepare("SELECT id FROM users WHERE role = 'admin' LIMIT 1").first();
  if (!adminUser) return err('No admin user found', 500);

  const ts = now();
  const scoreText = (carAScore && carBScore)
    ? `The jury scores: **${carAName} — ${carAScore}/10** vs **${carBName} — ${carBScore}/10**.`
    : '';

  const openingPost = `The Car Jury has published its head-to-head comparison. ${scoreText}

👉 [Read the full comparison](https://www.thecarjury.com/compare/${compareSlug}/)

---

**The floor is open:** What factors matter most to you in this decision? What does the comparison not cover? Share your take — real ownership experience and cited sources carry extra weight here.`;

  const threadResult = await env.DB.prepare(`
    INSERT INTO threads (slug, title, category_id, author_id, last_post_at, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(threadSlug, title, category.id, adminUser.id, ts, ts).run();

  const threadId = threadResult.meta.last_row_id;

  await env.DB.prepare(`
    INSERT INTO posts (thread_id, author_id, body, is_approved, created_at)
    VALUES (?, ?, ?, 1, ?)
  `).bind(threadId, adminUser.id, openingPost, ts).run();

  await env.DB.prepare('UPDATE categories SET thread_count = thread_count + 1 WHERE id = ?')
    .bind(category.id).run();

  await notifySlack(env, `⚖️ New compare thread: *${title}* → https://www.thecarjury.com/forum/t/${threadSlug}/`);

  return ok({
    threadSlug,
    threadUrl: `https://www.thecarjury.com/forum/t/${threadSlug}/`,
    created: true,
  });
}

// Mod worker — moderation queue, actions, bans, user management

import { requireRole } from '../middleware/auth.js';
import { json, err, ok, now } from '../utils/response.js';
import { notifySlack } from './forum.js';

export async function handleMod(path, request, env) {
  const method = request.method;

  // All mod routes require at least moderator role
  const auth = await requireRole(request, env, 'moderator');
  if (auth.error) return err(auth.error, auth.status);

  if (method === 'GET'  && path === '/queue')               return getQueue(env);
  if (method === 'POST' && path === '/approve-post')        return approvePost(request, env, auth);
  if (method === 'POST' && path === '/delete-post')         return deletePost(request, env, auth);
  if (method === 'POST' && path === '/lock-thread')         return lockThread(request, env, auth);
  if (method === 'POST' && path === '/pin-thread')          return pinThread(request, env, auth);
  if (method === 'POST' && path === '/warn-user')           return warnUser(request, env, auth);
  if (method === 'POST' && path === '/mute-user')           return muteUser(request, env, auth);
  if (method === 'GET'  && path === '/log')                 return getModLog(request, env);

  // Admin-only routes
  if (method === 'POST' && path === '/ban-user') {
    const adminAuth = await requireRole(request, env, 'admin');
    if (adminAuth.error) return err(adminAuth.error, adminAuth.status);
    return banUser(request, env, adminAuth);
  }
  if (method === 'POST' && path === '/promote-moderator') {
    const adminAuth = await requireRole(request, env, 'admin');
    if (adminAuth.error) return err(adminAuth.error, adminAuth.status);
    return promoteModerator(request, env, adminAuth);
  }

  return err('Not found', 404);
}

// ── GET /queue ─────────────────────────────────────────────────────────────

async function getQueue(env) {
  // Unapproved posts awaiting review
  const { results: pendingPosts } = await env.DB.prepare(`
    SELECT p.id, p.body, p.created_at,
           u.username, u.post_count, u.created_at AS user_created_at,
           t.slug AS thread_slug, t.title AS thread_title
    FROM posts p
    JOIN users u ON p.author_id = u.id
    JOIN threads t ON p.thread_id = t.id
    WHERE p.is_approved = 0 AND p.is_deleted = 0
    ORDER BY p.created_at ASC
    LIMIT 50
  `).all();

  // Unresolved reports
  const { results: reports } = await env.DB.prepare(`
    SELECT r.id, r.reason, r.created_at,
           p.id AS post_id, p.body AS post_body,
           reporter.username AS reporter_username,
           author.username AS post_author,
           author.post_count AS author_post_count
    FROM reports r
    JOIN posts p ON r.post_id = p.id
    JOIN users reporter ON r.reporter_id = reporter.id
    JOIN users author ON p.author_id = author.id
    WHERE r.is_resolved = 0
    ORDER BY r.created_at ASC
    LIMIT 50
  `).all();

  return json({ pendingPosts: pendingPosts.results || pendingPosts,
                reports: reports.results || reports });
}

// ── POST /approve-post ─────────────────────────────────────────────────────

async function approvePost(request, env, auth) {
  const { postId } = await request.json().catch(() => ({}));
  if (!postId) return err('postId required');

  await env.DB.prepare('UPDATE posts SET is_approved = 1 WHERE id = ?').bind(postId).run();
  await logMod(env, auth.userId, 'approve_post', 'post', postId, null);
  return ok();
}

// ── POST /delete-post ──────────────────────────────────────────────────────

async function deletePost(request, env, auth) {
  const { postId, reason } = await request.json().catch(() => ({}));
  if (!postId) return err('postId required');

  await env.DB.prepare(`
    UPDATE posts SET is_deleted = 1, delete_reason = ?, deleted_by = ? WHERE id = ?
  `).bind(reason || 'Removed by moderator', auth.userId, postId).run();

  // Resolve any open reports on this post
  await env.DB.prepare(`
    UPDATE reports SET is_resolved = 1, resolved_by = ? WHERE post_id = ? AND is_resolved = 0
  `).bind(auth.userId, postId).run();

  await logMod(env, auth.userId, 'delete_post', 'post', postId, reason);
  return ok();
}

// ── POST /lock-thread ──────────────────────────────────────────────────────

async function lockThread(request, env, auth) {
  const { threadId, lock = true } = await request.json().catch(() => ({}));
  if (!threadId) return err('threadId required');

  await env.DB.prepare('UPDATE threads SET is_locked = ? WHERE id = ?')
    .bind(lock ? 1 : 0, threadId).run();
  await logMod(env, auth.userId, lock ? 'lock_thread' : 'unlock_thread', 'thread', threadId, null);
  return ok({ locked: lock });
}

// ── POST /pin-thread ───────────────────────────────────────────────────────

async function pinThread(request, env, auth) {
  const { threadId, pin = true } = await request.json().catch(() => ({}));
  if (!threadId) return err('threadId required');

  await env.DB.prepare('UPDATE threads SET is_pinned = ? WHERE id = ?')
    .bind(pin ? 1 : 0, threadId).run();
  await logMod(env, auth.userId, pin ? 'pin_thread' : 'unpin_thread', 'thread', threadId, null);
  return ok({ pinned: pin });
}

// ── POST /warn-user ────────────────────────────────────────────────────────

async function warnUser(request, env, auth) {
  const { userId, reason } = await request.json().catch(() => ({}));
  if (!userId || !reason) return err('userId and reason required');

  const user = await env.DB.prepare('SELECT email, username FROM users WHERE id = ?').bind(userId).first();
  if (!user) return err('User not found', 404);

  await logMod(env, auth.userId, 'warn_user', 'user', userId, reason);
  await notifySlack(env, `⚠️ User *${user.username}* warned by mod. Reason: "${reason}"`);
  // Could also send warning email via Resend here
  return ok();
}

// ── POST /mute-user ────────────────────────────────────────────────────────

async function muteUser(request, env, auth) {
  const { userId, days = 7, reason } = await request.json().catch(() => ({}));
  if (!userId) return err('userId required');

  const muteUntil = days > 0 ? now() + days * 86400 : null;
  await env.DB.prepare('UPDATE users SET is_muted = ?, mute_until = ? WHERE id = ?')
    .bind(days > 0 ? 1 : 0, muteUntil, userId).run();

  const user = await env.DB.prepare('SELECT username FROM users WHERE id = ?').bind(userId).first();
  await logMod(env, auth.userId, days > 0 ? 'mute_user' : 'unmute_user', 'user', userId, reason);
  await notifySlack(env, `🔇 User *${user?.username}* muted for ${days} days. Reason: "${reason}"`);
  return ok({ muteUntil });
}

// ── POST /ban-user (admin only) ────────────────────────────────────────────

async function banUser(request, env, auth) {
  const { userId, reason } = await request.json().catch(() => ({}));
  if (!userId || !reason) return err('userId and reason required');

  await env.DB.prepare('UPDATE users SET is_banned = 1 WHERE id = ?').bind(userId).run();
  await logMod(env, auth.userId, 'ban_user', 'user', userId, reason);

  const user = await env.DB.prepare('SELECT username FROM users WHERE id = ?').bind(userId).first();
  await notifySlack(env, `🔨 User *${user?.username}* banned. Reason: "${reason}"`);
  return ok();
}

// ── POST /promote-moderator (admin only) ──────────────────────────────────

async function promoteModerator(request, env, auth) {
  const { userId } = await request.json().catch(() => ({}));
  if (!userId) return err('userId required');

  await env.DB.prepare("UPDATE users SET role = 'moderator' WHERE id = ?").bind(userId).run();
  await logMod(env, auth.userId, 'promote_moderator', 'user', userId, null);

  const user = await env.DB.prepare('SELECT username FROM users WHERE id = ?').bind(userId).first();
  await notifySlack(env, `⭐ *${user?.username}* promoted to moderator`);
  return ok();
}

// ── GET /log ───────────────────────────────────────────────────────────────

async function getModLog(request, env) {
  const url    = new URL(request.url);
  const page   = Math.max(1, parseInt(url.searchParams.get('page') || '1'));
  const limit  = 50;
  const offset = (page - 1) * limit;

  const { results } = await env.DB.prepare(`
    SELECT ml.*, u.username AS moderator_username
    FROM mod_log ml
    JOIN users u ON ml.moderator_id = u.id
    ORDER BY ml.created_at DESC
    LIMIT ? OFFSET ?
  `).bind(limit, offset).all();

  return json({ log: results, page, limit });
}

// ── Mod log helper ─────────────────────────────────────────────────────────

async function logMod(env, modId, action, targetType, targetId, reason) {
  await env.DB.prepare(`
    INSERT INTO mod_log (moderator_id, action, target_type, target_id, reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(modId, action, targetType, targetId, reason, now()).run();
}

// User worker — public profiles, private settings, password change, avatar, account delete

import { requireAuth } from '../middleware/auth.js';
import { hashPassword, verifyPassword, hashToken } from '../middleware/auth.js';
import { json, err, ok, now } from '../utils/response.js';

export async function handleUser(path, request, env) {
  const method = request.method;

  // Public endpoints
  if (method === 'GET' && path.startsWith('/profile/')) return getPublicProfile(path, env);

  // Auth-required
  const auth = await requireAuth(request, env);
  if (auth.error) return err(auth.error, auth.status);

  if (method === 'GET'  && path === '/me')              return getMe(env, auth);
  if (method === 'PUT'  && path === '/me')              return updateMe(request, env, auth);
  if (method === 'PUT'  && path === '/me/password')     return changePassword(request, env, auth);
  if (method === 'POST' && path === '/me/avatar')       return uploadAvatar(request, env, auth);
  if (method === 'DELETE' && path === '/me')            return deleteAccount(request, env, auth);

  return err('Not found', 404);
}

// ── GET /profile/:username ─────────────────────────────────────────────────

async function getPublicProfile(path, env) {
  const username = path.replace('/profile/', '').toLowerCase();

  const user = await env.DB.prepare(`
    SELECT id, username, display_name, bio, avatar_url, role, post_count, created_at, last_seen
    FROM users WHERE username = ? AND is_banned = 0
  `).bind(username).first();

  if (!user) return err('User not found', 404);

  // Recent posts (non-deleted, approved)
  const { results: recentPosts } = await env.DB.prepare(`
    SELECT p.id, p.body, p.upvotes, p.created_at,
           t.slug AS thread_slug, t.title AS thread_title
    FROM posts p
    JOIN threads t ON p.thread_id = t.id
    WHERE p.author_id = ? AND p.is_deleted = 0 AND p.is_approved = 1
    ORDER BY p.created_at DESC
    LIMIT 10
  `).bind(user.id).all();

  // Total upvotes received
  const votesRow = await env.DB.prepare(
    'SELECT SUM(upvotes) AS total FROM posts WHERE author_id = ? AND is_deleted = 0'
  ).bind(user.id).first();

  return json({
    user: { ...user },
    recentPosts,
    totalUpvotes: votesRow?.total || 0,
  });
}

// ── GET /me ────────────────────────────────────────────────────────────────

async function getMe(env, auth) {
  const user = await env.DB.prepare(`
    SELECT id, username, email, display_name, bio, avatar_url, role,
           is_verified, post_count, email_digest, created_at, last_seen
    FROM users WHERE id = ?
  `).bind(auth.userId).first();

  if (!user) return err('User not found', 404);
  return json({ user });
}

// ── PUT /me ────────────────────────────────────────────────────────────────

async function updateMe(request, env, auth) {
  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  // Only these fields are user-editable
  const allowed = ['display_name', 'bio', 'email_digest'];
  const updates = {};
  for (const field of allowed) {
    if (body[field] !== undefined) updates[field] = body[field];
  }

  if (updates.display_name !== undefined) {
    if (updates.display_name.length > 50)
      return err('Display name max 50 characters.');
  }
  if (updates.bio !== undefined) {
    if (updates.bio.length > 160) return err('Bio max 160 characters.');
  }
  if (updates.email_digest !== undefined) {
    updates.email_digest = updates.email_digest ? 1 : 0;
  }

  if (Object.keys(updates).length === 0) return err('Nothing to update.');

  const setClauses = Object.keys(updates).map(k => `${k} = ?`).join(', ');
  const values     = [...Object.values(updates), auth.userId];

  await env.DB.prepare(`UPDATE users SET ${setClauses} WHERE id = ?`).bind(...values).run();
  return ok({ updated: Object.keys(updates) });
}

// ── PUT /me/password ───────────────────────────────────────────────────────

async function changePassword(request, env, auth) {
  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  const { currentPassword, newPassword } = body;
  if (!currentPassword || !newPassword)
    return err('Current and new password required.');
  if (newPassword.length < 8) return err('New password must be at least 8 characters.');
  if (currentPassword === newPassword) return err('New password must differ from current.');

  const user = await env.DB.prepare('SELECT password_hash FROM users WHERE id = ?')
    .bind(auth.userId).first();

  const valid = await verifyPassword(currentPassword, user.password_hash);
  if (!valid) return err('Current password incorrect.', 401);

  const newHash = await hashPassword(newPassword);
  await env.DB.prepare('UPDATE users SET password_hash = ? WHERE id = ?')
    .bind(newHash, auth.userId).run();

  // Invalidate all sessions for this user from KV
  // KV doesn't support prefix scan natively — we invalidate current session only
  // For full invalidation across devices, store session list in D1 sessions table
  const tokenHash = await hashToken(auth.token);
  await env.KV.delete(`session:${tokenHash}`);

  return ok({ message: 'Password changed. Please sign in again.' });
}

// ── POST /me/avatar ────────────────────────────────────────────────────────

async function uploadAvatar(request, env, auth) {
  const contentType = request.headers.get('Content-Type') || '';
  if (!contentType.startsWith('image/')) return err('Image file required.');

  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  const mimeType = contentType.split(';')[0].trim();
  if (!allowed.includes(mimeType)) return err('Only JPEG, PNG, and WebP avatars allowed.');

  const buffer = await request.arrayBuffer();
  if (buffer.byteLength > 1024 * 1024) return err('Avatar must be under 1 MB.');

  // Store in R2
  const ext      = mimeType === 'image/jpeg' ? 'jpg' : mimeType === 'image/png' ? 'png' : 'webp';
  const key      = `avatars/${auth.userId}.${ext}`;
  await env.MEDIA.put(key, buffer, { httpMetadata: { contentType: mimeType } });

  const avatarUrl = `https://media.thecarjury.com/${key}`;

  // Delete old avatar key from R2 if different extension
  const user = await env.DB.prepare('SELECT avatar_url FROM users WHERE id = ?').bind(auth.userId).first();
  if (user?.avatar_url && !user.avatar_url.endsWith(key)) {
    const oldKey = user.avatar_url.split('media.thecarjury.com/')[1];
    if (oldKey) await env.MEDIA.delete(oldKey).catch(() => {});
  }

  await env.DB.prepare('UPDATE users SET avatar_url = ? WHERE id = ?')
    .bind(avatarUrl, auth.userId).run();

  return ok({ avatarUrl });
}

// ── DELETE /me ─────────────────────────────────────────────────────────────

async function deleteAccount(request, env, auth) {
  let body;
  try { body = await request.json(); } catch { body = {}; }

  const { password } = body;
  if (!password) return err('Password confirmation required.');

  const user = await env.DB.prepare('SELECT password_hash, avatar_url FROM users WHERE id = ?')
    .bind(auth.userId).first();
  const valid = await verifyPassword(password, user.password_hash);
  if (!valid) return err('Password incorrect.', 401);

  // Soft-delete: anonymise the account
  await env.DB.prepare(`
    UPDATE users
    SET username = ?, email = ?, password_hash = 'deleted', display_name = '[deleted]',
        bio = NULL, avatar_url = NULL, is_banned = 1
    WHERE id = ?
  `).bind(`deleted_${auth.userId}`, `deleted_${auth.userId}@void`, auth.userId).run();

  // Anonymise posts
  await env.DB.prepare(`
    UPDATE posts SET body = '[account deleted]', is_deleted = 1 WHERE author_id = ?
  `).bind(auth.userId).run();

  // Delete avatar from R2
  if (user.avatar_url) {
    const key = user.avatar_url.split('media.thecarjury.com/')[1];
    if (key) await env.MEDIA.delete(key).catch(() => {});
  }

  // Invalidate session
  const tokenHash = await hashToken(auth.token);
  await env.KV.delete(`session:${tokenHash}`);

  return new Response(JSON.stringify({ ok: true, message: 'Account deleted.' }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': 'tcj_session=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/',
      'Access-Control-Allow-Origin': 'https://www.thecarjury.com',
    },
  });
}

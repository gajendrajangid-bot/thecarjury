// Auth worker — register, login, logout, verify-email

import {
  hashPassword, verifyPassword, signJWT, verifyJWT,
  hashToken, sessionCookie, clearCookie
} from '../middleware/auth.js';
import { json, err, ok, checkRateLimit, now } from '../utils/response.js';

export async function handleAuth(path, request, env) {
  const method = request.method;

  if (method === 'POST' && path === '/register') return register(request, env);
  if (method === 'POST' && path === '/login')    return login(request, env);
  if (method === 'POST' && path === '/logout')   return logout(request, env);
  if (method === 'GET'  && path.startsWith('/verify-email')) return verifyEmail(request, env);

  return err('Not found', 404);
}

// ── Register ───────────────────────────────────────────────────────────────

async function register(request, env) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';

  // Rate limit: 3 registrations per IP per hour
  const allowed = await checkRateLimit(env.KV, `reg:ip:${ip}`, 3, 3600);
  if (!allowed) return err('Too many registration attempts. Try again later.', 429);

  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  const { username, email, password } = body;

  // Validate fields
  if (!username || !/^[a-zA-Z0-9_]{3,30}$/.test(username))
    return err('Username must be 3–30 characters: letters, numbers, underscores only.');
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    return err('Valid email address required.');
  if (!password || password.length < 8)
    return err('Password must be at least 8 characters.');

  // Check uniqueness
  const existing = await env.DB.prepare(
    'SELECT id FROM users WHERE email = ? OR username = ?'
  ).bind(email.toLowerCase(), username.toLowerCase()).first();

  if (existing) return err('Email or username already in use.', 409);

  // Hash password and create user
  const passwordHash = await hashPassword(password);
  const ts = now();

  const result = await env.DB.prepare(`
    INSERT INTO users (username, email, password_hash, display_name, role, is_verified, post_count, created_at)
    VALUES (?, ?, ?, ?, 'member', 0, 0, ?)
  `).bind(username.toLowerCase(), email.toLowerCase(), passwordHash, username, ts).run();

  const userId = result.meta.last_row_id;

  // Create verification token (24h)
  const verifyToken = await signJWT({ user_id: userId, type: 'verify' }, env.JWT_SECRET, 86400);

  // Send verification email via Resend
  await sendVerificationEmail(env, email, username, verifyToken);

  return ok({ message: 'Account created. Check your email to verify before posting.' });
}

// ── Login ──────────────────────────────────────────────────────────────────

async function login(request, env) {
  let body;
  try { body = await request.json(); } catch { return err('Invalid JSON'); }

  const { email, password } = body;
  if (!email || !password) return err('Email and password required.');

  // Fetch user — same error message for not-found vs wrong password (no enumeration)
  const user = await env.DB.prepare(
    'SELECT id, password_hash, role, is_verified, is_banned FROM users WHERE email = ?'
  ).bind(email.toLowerCase()).first();

  if (!user) return err('Invalid email or password.', 401);
  if (user.is_banned) return err('This account has been suspended.', 403);

  const valid = await verifyPassword(password, user.password_hash);
  if (!valid) return err('Invalid email or password.', 401);

  // Sign JWT
  const token = await signJWT({ user_id: user.id, role: user.role }, env.JWT_SECRET);
  const tokenHash = await hashToken(token);

  // Store session in KV (30 days)
  await env.KV.put(`session:${tokenHash}`, String(user.id), { expirationTtl: 2592000 });

  // Update last_seen
  await env.DB.prepare('UPDATE users SET last_seen = ? WHERE id = ?').bind(now(), user.id).run();

  return new Response(JSON.stringify({
    ok: true,
    user: { id: user.id, role: user.role, is_verified: user.is_verified }
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': sessionCookie(token),
      'Access-Control-Allow-Origin': 'https://www.thecarjury.com',
      'Access-Control-Allow-Credentials': 'true',
    },
  });
}

// ── Logout ─────────────────────────────────────────────────────────────────

async function logout(request, env) {
  const cookie = request.headers.get('Cookie') || '';
  const match  = cookie.match(/tcj_session=([^;]*)/);
  if (match) {
    const token = decodeURIComponent(match[1]);
    const tokenHash = await hashToken(token);
    await env.KV.delete(`session:${tokenHash}`);
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie': clearCookie(),
      'Access-Control-Allow-Origin': 'https://www.thecarjury.com',
      'Access-Control-Allow-Credentials': 'true',
    },
  });
}

// ── Verify email ───────────────────────────────────────────────────────────

async function verifyEmail(request, env) {
  const url   = new URL(request.url);
  const token = url.searchParams.get('token');
  if (!token) return err('Verification token missing.');

  const payload = await verifyJWT(token, env.JWT_SECRET);
  if (!payload || payload.type !== 'verify')
    return err('Invalid or expired verification link.', 400);

  await env.DB.prepare('UPDATE users SET is_verified = 1 WHERE id = ?')
    .bind(payload.user_id).run();

  // Redirect to forum with success param
  return Response.redirect('https://www.thecarjury.com/forum/?verified=1', 302);
}

// ── Email sender ───────────────────────────────────────────────────────────

async function sendVerificationEmail(env, email, username, token) {
  if (!env.RESEND_API_KEY) {
    console.log(`[DEV] Verify URL: ${env.SITE_URL}/api/forum/auth/verify-email?token=${token}`);
    return;
  }

  const verifyUrl = `${env.SITE_URL}/api/forum/auth/verify-email?token=${token}`;

  await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'The Car Jury <forum@thecarjury.com>',
      to: email,
      subject: 'Verify your Car Jury forum account',
      html: `
        <div style="font-family:Georgia,serif;max-width:480px;margin:0 auto;color:#1A1A1A">
          <p style="font-size:13px;color:#C8102E;font-family:Arial,sans-serif;letter-spacing:0.08em;text-transform:uppercase">THE CAR JURY · FORUM</p>
          <h1 style="font-size:24px;font-weight:600;margin-bottom:8px">Welcome, ${username}</h1>
          <p style="font-size:17px;line-height:1.7;color:#1A1A1A">
            One click to verify your email — then you're ready to debate verdicts,
            share ownership stories, and help buyers make better decisions.
          </p>
          <a href="${verifyUrl}"
             style="display:inline-block;background:#C8102E;color:#fff;padding:12px 24px;
                    border-radius:6px;font-family:Arial,sans-serif;font-size:14px;
                    font-weight:500;text-decoration:none;margin:16px 0">
            Verify my account →
          </a>
          <p style="font-size:13px;color:#6B6B6B;margin-top:24px;font-family:Arial,sans-serif">
            Link expires in 24 hours. If you didn't create this account, ignore this email.
          </p>
          <hr style="border:none;border-top:1px solid #E5E2DC;margin:24px 0">
          <p style="font-size:12px;color:#6B6B6B;font-family:Arial,sans-serif">
            thecarjury.com · No sponsored reviews. No manufacturer relationships.
          </p>
        </div>
      `,
    }),
  });
}

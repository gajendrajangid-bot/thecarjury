// Auth middleware — verifies JWT cookie and attaches user context to every request

export async function requireAuth(request, env) {
  const cookie = request.headers.get('Cookie') || '';
  const token = parseCookie(cookie, 'tcj_session');
  if (!token) return { error: 'Unauthorized', status: 401 };

  const payload = await verifyJWT(token, env.JWT_SECRET);
  if (!payload) return { error: 'Invalid or expired session', status: 401 };

  // Check KV — token must still be live (enables logout invalidation)
  const sessionKey = `session:${await hashToken(token)}`;
  const kvUserId = await env.KV.get(sessionKey);
  if (!kvUserId) return { error: 'Session expired', status: 401 };

  return { userId: payload.user_id, role: payload.role, token };
}

export async function requireRole(request, env, minRole) {
  const auth = await requireAuth(request, env);
  if (auth.error) return auth;

  const roleLevel = { member: 1, moderator: 2, admin: 3 };
  if ((roleLevel[auth.role] || 0) < (roleLevel[minRole] || 99)) {
    return { error: 'Forbidden', status: 403 };
  }
  return auth;
}

// ── JWT helpers ────────────────────────────────────────────────────────────

export async function signJWT(payload, secret, expiresInSeconds = 2592000) {
  const header = b64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body   = b64url(JSON.stringify({ ...payload, exp: Math.floor(Date.now() / 1000) + expiresInSeconds }));
  const sig    = await hmacSign(`${header}.${body}`, secret);
  return `${header}.${body}.${sig}`;
}

export async function verifyJWT(token, secret) {
  try {
    const [header, body, sig] = token.split('.');
    if (!header || !body || !sig) return null;
    const expected = await hmacSign(`${header}.${body}`, secret);
    if (!safeCompare(sig, expected)) return null;
    const payload = JSON.parse(atob(body.replace(/-/g, '+').replace(/_/g, '/')));
    if (payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}

async function hmacSign(data, secret) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(data));
  return b64url(String.fromCharCode(...new Uint8Array(sig)));
}

function b64url(str) {
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function safeCompare(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function hashToken(token) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// ── Password hashing (pure Web Crypto bcrypt-equivalent via PBKDF2) ────────
// Note: real bcrypt not available in Workers; using PBKDF2-SHA256 with 100k iterations

export async function hashPassword(password) {
  const salt  = crypto.getRandomValues(new Uint8Array(16));
  const key   = await pbkdf2(password, salt, 100000);
  const saltHex = Array.from(salt).map(b => b.toString(16).padStart(2, '0')).join('');
  const keyHex  = Array.from(new Uint8Array(key)).map(b => b.toString(16).padStart(2, '0')).join('');
  return `pbkdf2:${saltHex}:${keyHex}`;
}

export async function verifyPassword(password, stored) {
  const [, saltHex, keyHex] = stored.split(':');
  const salt = new Uint8Array(saltHex.match(/.{2}/g).map(h => parseInt(h, 16)));
  const key  = await pbkdf2(password, salt, 100000);
  const newKeyHex = Array.from(new Uint8Array(key)).map(b => b.toString(16).padStart(2, '0')).join('');
  return safeCompare(keyHex, newKeyHex);
}

async function pbkdf2(password, salt, iterations) {
  const keyMaterial = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']
  );
  return crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    keyMaterial, 256
  );
}

// ── Cookie helpers ─────────────────────────────────────────────────────────

export function parseCookie(cookieHeader, name) {
  const match = cookieHeader.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function sessionCookie(token, maxAge = 2592000) {
  return `tcj_session=${encodeURIComponent(token)}; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}; Path=/`;
}

export function clearCookie() {
  return 'tcj_session=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/';
}

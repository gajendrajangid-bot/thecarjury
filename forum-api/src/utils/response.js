// Shared response helpers

const CORS_HEADERS = {
  'Access-Control-Allow-Origin':  'https://www.thecarjury.com',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Credentials': 'true',
};

export function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS, ...extraHeaders },
  });
}

export function err(message, status = 400) {
  return json({ error: message }, status);
}

export function ok(data = {}) {
  return json({ ok: true, ...data });
}

export function handleOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

// Rate limiting via KV
export async function checkRateLimit(kv, key, limit, windowSeconds) {
  const current = parseInt(await kv.get(key) || '0');
  if (current >= limit) return false;
  await kv.put(key, String(current + 1), { expirationTtl: windowSeconds });
  return true;
}

// Generate a URL-safe slug from a title
export function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 80);
}

// Generate a unique slug by appending a timestamp suffix if needed
export async function uniqueSlug(db, base) {
  const slug = slugify(base);
  const existing = await db.prepare('SELECT id FROM threads WHERE slug = ?').bind(slug).first();
  if (!existing) return slug;
  return `${slug}-${Date.now().toString(36)}`;
}

export function now() {
  return Math.floor(Date.now() / 1000);
}

// Spam signal detection
export function isSpammy(body, user) {
  const linkCount = (body.match(/https?:\/\//g) || []).length;
  if (linkCount >= 3 && user.post_count < 5) return true;
  if (/^[a-z0-9]{13,}$/i.test(user.username)) return true;
  return false;
}

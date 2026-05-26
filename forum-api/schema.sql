-- TCJ Forum — D1 Schema v1.0
-- Run: wrangler d1 execute tcj-forum --file=./schema.sql

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- Users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT    UNIQUE NOT NULL,
  email         TEXT    UNIQUE NOT NULL,
  password_hash TEXT    NOT NULL,
  display_name  TEXT,
  bio           TEXT    CHECK(length(bio) <= 160),
  avatar_url    TEXT,
  role          TEXT    NOT NULL DEFAULT 'member'
                        CHECK(role IN ('member','moderator','admin')),
  is_verified   INTEGER NOT NULL DEFAULT 0,
  is_muted      INTEGER NOT NULL DEFAULT 0,
  mute_until    INTEGER,
  is_banned     INTEGER NOT NULL DEFAULT 0,
  post_count    INTEGER NOT NULL DEFAULT 0,
  email_digest  INTEGER NOT NULL DEFAULT 1,
  created_at    INTEGER NOT NULL,
  last_seen     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ─────────────────────────────────────────────
-- Categories
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  slug          TEXT    UNIQUE NOT NULL,
  name          TEXT    NOT NULL,
  description   TEXT,
  color         TEXT    NOT NULL DEFAULT 'red',
  display_order INTEGER NOT NULL DEFAULT 0,
  thread_count  INTEGER NOT NULL DEFAULT 0,
  post_count    INTEGER NOT NULL DEFAULT 0,
  is_locked     INTEGER NOT NULL DEFAULT 0
);

-- ─────────────────────────────────────────────
-- Threads
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS threads (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  slug             TEXT    UNIQUE NOT NULL,
  title            TEXT    NOT NULL CHECK(length(title) >= 10 AND length(title) <= 200),
  category_id      INTEGER NOT NULL REFERENCES categories(id),
  author_id        INTEGER NOT NULL REFERENCES users(id),
  is_pinned        INTEGER NOT NULL DEFAULT 0,
  is_locked        INTEGER NOT NULL DEFAULT 0,
  is_review_thread INTEGER NOT NULL DEFAULT 0,
  review_slug      TEXT,
  view_count       INTEGER NOT NULL DEFAULT 0,
  reply_count      INTEGER NOT NULL DEFAULT 0,
  last_post_at     INTEGER,
  created_at       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_threads_category  ON threads(category_id, last_post_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_author    ON threads(author_id);
CREATE INDEX IF NOT EXISTS idx_threads_review    ON threads(review_slug);
CREATE INDEX IF NOT EXISTS idx_threads_pinned    ON threads(category_id, is_pinned DESC, last_post_at DESC);

-- ─────────────────────────────────────────────
-- Posts
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id     INTEGER NOT NULL REFERENCES threads(id),
  author_id     INTEGER NOT NULL REFERENCES users(id),
  body          TEXT    NOT NULL CHECK(length(body) >= 20 AND length(body) <= 5000),
  is_deleted    INTEGER NOT NULL DEFAULT 0,
  delete_reason TEXT,
  deleted_by    INTEGER REFERENCES users(id),
  is_approved   INTEGER NOT NULL DEFAULT 0,
  upvotes       INTEGER NOT NULL DEFAULT 0,
  created_at    INTEGER NOT NULL,
  edited_at     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_posts_thread    ON posts(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_author    ON posts(author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_pending   ON posts(is_approved, is_deleted) WHERE is_approved = 0 AND is_deleted = 0;

-- Full-text search on posts
CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
  body,
  content='posts',
  content_rowid='id'
);

-- ─────────────────────────────────────────────
-- Votes (upvotes only)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS votes (
  user_id    INTEGER NOT NULL REFERENCES users(id),
  post_id    INTEGER NOT NULL REFERENCES posts(id),
  created_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_votes_post ON votes(post_id);

-- ─────────────────────────────────────────────
-- Reports
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reports (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id     INTEGER NOT NULL REFERENCES posts(id),
  reporter_id INTEGER NOT NULL REFERENCES users(id),
  reason      TEXT    NOT NULL,
  is_resolved INTEGER NOT NULL DEFAULT 0,
  resolved_by INTEGER REFERENCES users(id),
  created_at  INTEGER NOT NULL,
  UNIQUE(post_id, reporter_id)
);

CREATE INDEX IF NOT EXISTS idx_reports_unresolved ON reports(is_resolved, created_at) WHERE is_resolved = 0;

-- ─────────────────────────────────────────────
-- Moderation log
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mod_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  moderator_id  INTEGER NOT NULL REFERENCES users(id),
  action        TEXT    NOT NULL CHECK(action IN (
                  'delete_post','approve_post','lock_thread','unlock_thread',
                  'pin_thread','unpin_thread','warn_user','mute_user',
                  'unmute_user','ban_user','unban_user','promote_moderator')),
  target_type   TEXT    NOT NULL CHECK(target_type IN ('post','thread','user')),
  target_id     INTEGER NOT NULL,
  reason        TEXT,
  created_at    INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_modlog_target ON mod_log(target_type, target_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_modlog_mod    ON mod_log(moderator_id, created_at DESC);

-- ─────────────────────────────────────────────
-- Notification queue (for digest emails)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id),
  type        TEXT    NOT NULL CHECK(type IN ('reply','mention')),
  thread_id   INTEGER NOT NULL REFERENCES threads(id),
  post_id     INTEGER NOT NULL REFERENCES posts(id),
  is_sent     INTEGER NOT NULL DEFAULT 0,
  created_at  INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notif_unsent ON notifications(user_id, is_sent, created_at) WHERE is_sent = 0;

-- ─────────────────────────────────────────────
-- Seed: launch categories
-- ─────────────────────────────────────────────
INSERT OR IGNORE INTO categories (slug, name, description, color, display_order) VALUES
  ('verdicts',      'Jury Verdicts',   'Debate the verdict. Agree or push back — with evidence.',              'red',   1),
  ('buying-advice', 'Buying Advice',   'Post your shortlist. The community weighs in.',                        'blue',  2),
  ('ev-talk',       'EV Talk',         'Range, charging, ownership. The honest story on EVs.',                 'green', 3),
  ('comparisons',   'Head to Head',    'Which car wins? Bring the data, not the fandom.',                      'amber', 4),
  ('ownership',     'Ownership Stories','Real-world ownership reports from buyers, not reviewers.',             'grey',  5),
  ('general',       'General',         'Everything else. Keep it civil.',                                      'grey',  6);

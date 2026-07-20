CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, salt TEXT NOT NULL, credits INTEGER NOT NULL DEFAULT 0, free_uses INTEGER NOT NULL DEFAULT 1, is_admin INTEGER NOT NULL DEFAULT 0, phone TEXT UNIQUE, created_at TEXT, last_login TEXT, total_analyses INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS resume_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, target_position TEXT, match_score INTEGER, resume_text TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS usage_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, prompt_tokens INTEGER DEFAULT 0, completion_tokens INTEGER DEFAULT 0, credits_charged INTEGER DEFAULT 0, model TEXT, created_at TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS verification_codes (phone TEXT PRIMARY KEY, code TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_history_user ON resume_history(user_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_logs(user_id, id DESC);

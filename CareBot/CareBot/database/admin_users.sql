-- Admin Users Table
-- Stores web passwords for admin users (who have is_admin=1 in warmasters)
-- Admins can use Telegram bot without password, web requires password

CREATE TABLE IF NOT EXISTS admin_users (
    warmaster_id INTEGER PRIMARY KEY NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    FOREIGN KEY (warmaster_id) REFERENCES warmasters(id) ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_admin_last_login ON admin_users(last_login);

-- Admin Users Table
-- Stores authentication information for admin users
-- Linked to warmasters table for user identification

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warmaster_id INTEGER UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (warmaster_id) REFERENCES warmasters(id) ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_admin_warmaster ON admin_users(warmaster_id);
CREATE INDEX IF NOT EXISTS idx_admin_active ON admin_users(is_active);

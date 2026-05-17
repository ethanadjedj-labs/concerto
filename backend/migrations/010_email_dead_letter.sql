-- Migration 010: email dead-letter queue
-- Stores emails that failed all 3 SMTP retry attempts for operator review.
CREATE TABLE IF NOT EXISTS concerto_email_dead_letter (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  to_addr      TEXT    NOT NULL,
  subject      TEXT    NOT NULL,
  body_html    TEXT,
  body_text    TEXT,
  error        TEXT,
  attempted_at INTEGER NOT NULL,
  retries      INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_dead_letter_attempted
    ON concerto_email_dead_letter(attempted_at);

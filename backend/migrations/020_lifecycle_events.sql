CREATE TABLE IF NOT EXISTS concerto_lifecycle_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  buyer_token TEXT NOT NULL,
  vps_id TEXT,
  idle_seconds INTEGER,
  resume_latency_ms INTEGER,
  source TEXT,
  detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_ts ON concerto_lifecycle_events(ts);
CREATE INDEX IF NOT EXISTS idx_lifecycle_events_buyer ON concerto_lifecycle_events(buyer_token);

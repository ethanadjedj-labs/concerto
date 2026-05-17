ALTER TABLE concerto_buyers ADD COLUMN plan TEXT NOT NULL DEFAULT 'byoc' CHECK(plan IN ('hosted', 'byoc'));
ALTER TABLE concerto_buyers ADD COLUMN subscription_id TEXT;
ALTER TABLE concerto_buyers ADD COLUMN subscription_status TEXT;
ALTER TABLE concerto_buyers ADD COLUMN next_renewal_at INTEGER;
CREATE TABLE IF NOT EXISTS concerto_hosted_pool (
  droplet_id TEXT PRIMARY KEY,
  buyer_token TEXT NOT NULL UNIQUE,
  ipv4 TEXT,
  status TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  destroyed_at INTEGER
);

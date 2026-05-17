-- Migration 013: per-customer CF tunnel tracking
-- Stores the Cloudflare tunnel UUID so destroy_droplet can clean up the
-- named tunnel and its DNS record when the droplet is reaped or cancelled.
ALTER TABLE concerto_buyers ADD COLUMN cf_tunnel_id TEXT;

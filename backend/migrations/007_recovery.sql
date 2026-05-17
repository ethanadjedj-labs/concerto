-- Recovery and edge-case handling: refund tracking, suspension, Stripe idempotency
ALTER TABLE concerto_buyers ADD COLUMN refunded_at INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN refund_stripe_id TEXT;
ALTER TABLE concerto_buyers ADD COLUMN suspended_at INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN last_seen_at INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN dashboard_opened_at INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN reminder_24h_sent INTEGER DEFAULT 0;
ALTER TABLE concerto_buyers ADD COLUMN reminder_48h_sent INTEGER DEFAULT 0;
ALTER TABLE concerto_buyers ADD COLUMN failure_reason TEXT;
ALTER TABLE concerto_buyers ADD COLUMN payment_failed_at INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN payment_failed_count INTEGER DEFAULT 0;
CREATE TABLE IF NOT EXISTS stripe_processed_events (
    event_id   TEXT    PRIMARY KEY,
    event_type TEXT    NOT NULL,
    processed_at INTEGER NOT NULL
);

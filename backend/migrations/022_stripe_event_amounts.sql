-- Commit-after-success idempotency state machine + recorded payment amounts.
--
-- status lifecycle for stripe_processed_events:
--   'processing' -> claimed by a handler, side effects not yet committed
--   'done'       -> handler finished successfully (safe to dedupe retries)
-- Legacy rows default to 'done' (they were only ever written post-processing
-- under the old claim-before-process code, so they are effectively complete).
--
-- amount is stored in the smallest currency unit (cents), matching Stripe's
-- amount_total / amount_paid. This is the per-event revenue the ledger sums.
ALTER TABLE stripe_processed_events ADD COLUMN status TEXT NOT NULL DEFAULT 'done';
ALTER TABLE stripe_processed_events ADD COLUMN received_at INTEGER;
ALTER TABLE stripe_processed_events ADD COLUMN claimed_at INTEGER;
ALTER TABLE stripe_processed_events ADD COLUMN amount INTEGER;
ALTER TABLE stripe_processed_events ADD COLUMN currency TEXT;

ALTER TABLE concerto_buyers ADD COLUMN paid_amount INTEGER;
ALTER TABLE concerto_buyers ADD COLUMN paid_currency TEXT;

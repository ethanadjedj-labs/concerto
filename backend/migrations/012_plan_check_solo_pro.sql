-- Migration 012: expand plan CHECK to include 'solo' and 'pro'
CREATE TABLE IF NOT EXISTS concerto_buyers_v3_012 AS SELECT * FROM concerto_buyers WHERE 1=0;
DROP TABLE concerto_buyers_v3_012;

CREATE TABLE concerto_buyers_v3_012 (
    id                       INTEGER PRIMARY KEY,
    token                    TEXT    UNIQUE NOT NULL,
    email                    TEXT,
    stripe_session_id        TEXT,
    provider                 TEXT    DEFAULT 'digitalocean',
    region                   TEXT,
    vps_size                 TEXT,
    vps_id                   TEXT,
    vps_ip                   TEXT,
    mcp_url                  TEXT,
    bearer_token             TEXT,
    ssh_keypair_private_path TEXT,
    status                   TEXT,
    paid_at                  INTEGER,
    provisioned_at           INTEGER,
    installed_at             INTEGER,
    ttyd_password            TEXT,
    ttyd_public_url          TEXT,
    plan                     TEXT NOT NULL DEFAULT 'solo'
                             CHECK(plan IN ('solo', 'pro', 'byoc', 'trial', 'hosted')),
    subscription_id          TEXT,
    subscription_status      TEXT,
    next_renewal_at          INTEGER,
    first_call_at            INTEGER,
    stripe_customer_id       TEXT,
    drip_day_0_sent_at       INTEGER,
    drip_day_1_sent_at       INTEGER,
    drip_day_3_sent_at       INTEGER,
    drip_day_7_sent_at       INTEGER,
    drip_day_14_sent_at      INTEGER,
    drip_day_21_sent_at      INTEGER,
    drip_day_30_sent_at      INTEGER,
    refunded_at              INTEGER,
    refund_stripe_id         TEXT,
    suspended_at             INTEGER,
    last_seen_at             INTEGER,
    dashboard_opened_at      INTEGER,
    reminder_24h_sent        INTEGER DEFAULT 0,
    reminder_48h_sent        INTEGER DEFAULT 0,
    failure_reason           TEXT,
    payment_failed_at        INTEGER,
    payment_failed_count     INTEGER DEFAULT 0,
    expires_at               INTEGER,
    trial_origin_ip          TEXT
);

INSERT INTO concerto_buyers_v3_012 (
    id, token, email, stripe_session_id, provider, region, vps_size, vps_id, vps_ip,
    mcp_url, bearer_token, ssh_keypair_private_path, status, paid_at, provisioned_at,
    installed_at, ttyd_password, ttyd_public_url, plan, subscription_id, subscription_status,
    next_renewal_at, first_call_at, stripe_customer_id, drip_day_0_sent_at, drip_day_1_sent_at,
    drip_day_3_sent_at, drip_day_7_sent_at, drip_day_14_sent_at, drip_day_21_sent_at,
    drip_day_30_sent_at, refunded_at, refund_stripe_id, suspended_at, last_seen_at,
    dashboard_opened_at, reminder_24h_sent, reminder_48h_sent, failure_reason,
    payment_failed_at, payment_failed_count, expires_at, trial_origin_ip
)
SELECT id, token, email, stripe_session_id, provider, region, vps_size, vps_id, vps_ip,
       mcp_url, bearer_token, ssh_keypair_private_path, status, paid_at, provisioned_at,
       installed_at, ttyd_password, ttyd_public_url, plan, subscription_id, subscription_status,
       next_renewal_at, first_call_at, stripe_customer_id, drip_day_0_sent_at, drip_day_1_sent_at,
       drip_day_3_sent_at, drip_day_7_sent_at, drip_day_14_sent_at, drip_day_21_sent_at,
       drip_day_30_sent_at, refunded_at, refund_stripe_id, suspended_at, last_seen_at,
       dashboard_opened_at, reminder_24h_sent, reminder_48h_sent, failure_reason,
       payment_failed_at, payment_failed_count, expires_at, trial_origin_ip
FROM concerto_buyers;

DROP TABLE concerto_buyers;
ALTER TABLE concerto_buyers_v3_012 RENAME TO concerto_buyers;

CREATE INDEX IF NOT EXISTS idx_concerto_buyers_expires_at_v3 ON concerto_buyers(expires_at);
CREATE INDEX IF NOT EXISTS idx_concerto_buyers_email_v3 ON concerto_buyers(email);
CREATE INDEX IF NOT EXISTS idx_concerto_buyers_status_v3 ON concerto_buyers(status);

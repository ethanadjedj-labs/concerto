CREATE TABLE IF NOT EXISTS maestro_buyers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    token                   TEXT    UNIQUE NOT NULL,
    email                   TEXT,
    stripe_session_id       TEXT,
    provider                TEXT    DEFAULT 'digitalocean',
    region                  TEXT,
    vps_size                TEXT,
    vps_id                  TEXT,
    vps_ip                  TEXT,
    mcp_url                 TEXT,
    bearer_token            TEXT,
    ssh_keypair_private_path TEXT,
    status                  TEXT,
    paid_at                 INTEGER,
    provisioned_at          INTEGER,
    installed_at            INTEGER
);

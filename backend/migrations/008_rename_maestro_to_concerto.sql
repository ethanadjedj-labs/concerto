-- Rename tables from maestro_* to concerto_* (brand pivot 2026-05-17).
-- Safe to re-run: db.run_migration silently ignores "no such table" errors,
-- so this is a no-op on fresh installs where 001_init already creates concerto_*.
ALTER TABLE maestro_buyers RENAME TO concerto_buyers;
ALTER TABLE maestro_hosted_pool RENAME TO concerto_hosted_pool;

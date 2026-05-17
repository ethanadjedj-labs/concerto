-- Migration 007: Pricing tiers v2 (solo / pro / byoc)
-- Applied: 2026-05-17
--
-- SQLite's ALTER TABLE is limited (no CHECK constraint changes, no column drops).
-- We rely on Pydantic validation in FastAPI to enforce plan ∈ {solo, pro, byoc}.
-- This migration documents the intent and migrates existing 'hosted' rows to 'solo'
-- (anyone who paid before is grandfathered to 4GB).
--
-- NOTE: The DB column remains TEXT NOT NULL with no CHECK constraint enforced at
-- the SQLite level. Application-level validation (Pydantic) is the authority.

UPDATE concerto_buyers SET plan = 'solo' WHERE plan = 'hosted';

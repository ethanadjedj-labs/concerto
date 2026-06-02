"""F-09 — CONCERTO_EXTRA_ORIGINS must reject obviously bad values
(wildcards, schemeless entries, http:// origins, trailing slashes).
"""
from __future__ import annotations

import importlib

import pytest


def _reload_server(monkeypatch, value: str):
    monkeypatch.setenv("CONCERTO_EXTRA_ORIGINS", value)
    import concerto.server as srv
    return importlib.reload(srv)


@pytest.mark.parametrize("bad_value", [
    "*",
    "https://*.example.com",
    "evil.com",                       # no scheme
    "http://insecure.example",        # http forbidden — credentials are TLS-only
    "https://ok.example/",            # trailing slash breaks CORS spec
    "https://ok.example, *",          # one good + one wildcard
])
def test_f09_invalid_extra_origins_rejected(monkeypatch, bad_value):
    monkeypatch.setenv("CONCERTO_EXTRA_ORIGINS", bad_value)
    with pytest.raises((ValueError, RuntimeError)):
        import concerto.server as srv
        importlib.reload(srv)


def test_f09_valid_extra_origin_accepted(monkeypatch):
    monkeypatch.setenv("CONCERTO_EXTRA_ORIGINS", "https://staging.concerto.run,https://preview.vercel.app")
    import concerto.server as srv
    srv = importlib.reload(srv)
    # Origins are appended to the base list — make sure both made it in.
    assert "https://staging.concerto.run" in srv._CORS_ORIGINS
    assert "https://preview.vercel.app" in srv._CORS_ORIGINS


def test_f09_unset_extra_origin_is_fine(monkeypatch):
    monkeypatch.delenv("CONCERTO_EXTRA_ORIGINS", raising=False)
    import concerto.server as srv
    importlib.reload(srv)

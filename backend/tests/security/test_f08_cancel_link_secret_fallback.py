"""F-08 — Cancel-link HMAC secret must never silently fall back.

The cancel-by-email flow signs links with HMAC(`CONCERTO_CANCEL_LINK_SECRET`).
If the env var is unset, the legacy code did `secrets.token_hex(32)` — every
backend restart silently invalidates every outstanding cancel link AND two
replicas would generate divergent secrets so outstanding links would 50/50
break.

Hardened contract:

  * Importing the module logs a loud WARNING when the env var is missing
    (so journalctl picks it up the moment anyone runs the backend).
  * The fallback secret is still generated (so dev & tests keep working
    without env wiring), but the warning makes the misconfiguration
    impossible to miss in prod.
"""
from __future__ import annotations

import importlib
import logging


def _reload(monkeypatch, env_value):
    if env_value is None:
        monkeypatch.delenv("CONCERTO_CANCEL_LINK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CONCERTO_CANCEL_LINK_SECRET", env_value)
    import concerto.customer_portal as mod
    return importlib.reload(mod)


def test_f08_missing_env_emits_warning(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="concerto.customer_portal")
    _reload(monkeypatch, None)

    matches = [
        r for r in caplog.records
        if "CONCERTO_CANCEL_LINK_SECRET" in r.getMessage()
           and r.levelno >= logging.WARNING
    ]
    assert matches, (
        "F-08: importing customer_portal with CONCERTO_CANCEL_LINK_SECRET "
        "unset must log a WARNING (loud, journalctl-visible) so a "
        "missing env var is not a silent foot-gun.\n"
        f"records seen: {[(r.levelname, r.getMessage()) for r in caplog.records]}"
    )


def test_f08_present_env_silent(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="concerto.customer_portal")
    _reload(monkeypatch, "a" * 64)

    matches = [
        r for r in caplog.records
        if "CONCERTO_CANCEL_LINK_SECRET" in r.getMessage()
    ]
    assert not matches, (
        "F-08: when CONCERTO_CANCEL_LINK_SECRET IS set, the warning must "
        f"NOT fire.  saw: {[(r.levelname, r.getMessage()) for r in matches]}"
    )


def test_f08_links_round_trip(monkeypatch):
    """Sanity: even with the fallback path, signing → verifying still works."""
    mod = _reload(monkeypatch, None)
    link = mod._make_cancel_link("tok_abc")
    # parse it back
    import urllib.parse
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
    assert mod._verify_cancel_link(qs["token"][0], qs["expires"][0], qs["sig"][0])

"""F-06 — admin/ops token comparison must be constant-time.

The risk is low (timing attacks over WAN are noisy), but the fix is one
line.  We assert the implementation uses `hmac.compare_digest` so future
refactors do not regress.
"""
from __future__ import annotations

import inspect


def test_f06_nf_admin_uses_compare_digest():
    from concerto import nf_admin_router as mod
    src = inspect.getsource(mod._check_admin_auth)
    assert "compare_digest" in src, (
        "nf_admin_router._check_admin_auth must use hmac.compare_digest, got:\n" + src
    )
    # And NOT use a bare `!=` against the secret token.
    assert "!= _OPS_TOKEN" not in src, (
        "non-constant-time comparison still present in nf_admin_router"
    )


def test_f06_demand_uses_compare_digest():
    from concerto import demand_router as mod
    src = inspect.getsource(mod._check_auth)
    assert "compare_digest" in src, (
        "demand_router._check_auth must use hmac.compare_digest, got:\n" + src
    )
    assert "!= _OPS_TOKEN" not in src, (
        "non-constant-time comparison still present in demand_router"
    )

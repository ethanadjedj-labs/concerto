"""Tests for the WS3 multi-brand Stripe scaffolding.

Hard constraint: Concerto live payments MUST NOT change shape on the
wire. This test pins that contract: for the `concerto` brand,
`make_stripe_session_kwargs` is the empty dict, so any caller that
spreads it (`stripe.checkout.Session.create(..., **kwargs)`) makes
exactly the same call it does today (no `stripe_account` override).

For the `clickcure` brand the test covers both states:
  * `connected_account_id = ""` (default in shipped config) -> empty
    kwargs and `has_connect == False` (the checkout endpoint will
    refuse on this state — see the clickcure-side test).
  * `connected_account_id = "acct_clickcure_test"` -> kwargs route
    the call through the connected account.

No live Stripe — the test never imports or calls the SDK.
"""
from __future__ import annotations

import os
import textwrap

import pytest

# brand_stripe touches no env vars / DBs; safe to import at module level.
from concerto import brand_stripe


@pytest.fixture()
def fresh_loader():
    """Drop the lru_cache before and after every test."""
    brand_stripe.load_brands.cache_clear()
    yield
    brand_stripe.load_brands.cache_clear()


def _write_toml(tmp_path, body: str) -> str:
    path = os.path.join(tmp_path, "brands.toml")
    with open(path, "w") as fp:
        fp.write(textwrap.dedent(body).strip() + "\n")
    return path


# ── Shipped config: Concerto = default (empty connect), ClickCure = TODO ─────

def test_shipped_concerto_brand_yields_empty_kwargs(fresh_loader):
    """The headline regression guard.

    The concerto brand in the shipped brands.toml has an empty
    connected_account_id. The kwargs returned by
    `make_stripe_session_kwargs` must be `{}` so that every existing
    `stripe.checkout.Session.create(...)` call site behaves
    byte-for-byte identically to today.
    """
    brand = brand_stripe.get_brand("concerto")
    assert brand.connected_account_id == ""
    assert brand.has_connect is False
    assert brand_stripe.make_stripe_session_kwargs(brand) == {}


def test_shipped_clickcure_brand_is_loud_until_configured(fresh_loader):
    """ClickCure ships with no connected_account_id — has_connect must be False
    so the clickcure-side endpoint can detect and refuse the request."""
    brand = brand_stripe.get_brand("clickcure")
    assert brand.connected_account_id == ""
    assert brand.has_connect is False
    assert brand_stripe.make_stripe_session_kwargs(brand) == {}
    assert brand.statement_descriptor == "CLICKCURE.CO"
    assert brand.currency == "gbp"


def test_unknown_brand_raises(fresh_loader):
    with pytest.raises(brand_stripe.BrandNotFoundError):
        brand_stripe.get_brand("does-not-exist")


# ── Configured connect: round-trip kwargs ────────────────────────────────────

def test_configured_brand_emits_stripe_account_kwarg(tmp_path, fresh_loader):
    path = _write_toml(tmp_path, """
        [brands.clickcure]
        display_name = "ClickCure"
        domain = "clickcure.co"
        support_email = "contact@clickcure.co"
        statement_descriptor = "CLICKCURE.CO"
        currency = "gbp"
        connected_account_id = "acct_clickcure_test"
        express_price_id = "price_express_test"
    """)
    brand = brand_stripe.get_brand("clickcure", path=path)
    assert brand.has_connect is True
    assert brand_stripe.make_stripe_session_kwargs(brand) == {
        "stripe_account": "acct_clickcure_test",
    }


# ── Schema validation ────────────────────────────────────────────────────────

def test_missing_required_keys_raise(tmp_path, fresh_loader):
    path = _write_toml(tmp_path, """
        [brands.broken]
        display_name = "Broken"
    """)
    with pytest.raises(brand_stripe.BrandConfigError):
        brand_stripe.load_brands(path)


def test_empty_brands_table_raises(tmp_path, fresh_loader):
    path = _write_toml(tmp_path, """
        # no brands defined at all
    """)
    with pytest.raises(brand_stripe.BrandConfigError):
        brand_stripe.load_brands(path)

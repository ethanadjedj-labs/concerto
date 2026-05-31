"""Regression guard: Concerto's existing Stripe call shape is unchanged.

The WS3 multi-brand layer ships a brand_stripe module and a
brands.toml, but the *default-brand* contract for Concerto is "no
behaviour change on the wire". This test mocks the Stripe SDK at the
module boundary and asserts that:

  1. `make_stripe_session_kwargs("concerto")` is `{}`.
  2. A representative Stripe call made with the brand layer
     (`stripe.checkout.Session.create(..., **kwargs)`) is invoked
     with the same positional/keyword set it would have today —
     specifically, NO `stripe_account` kwarg.

If a future change accidentally puts Concerto on a connected account
without an operator-led migration plan, this test fails and the
breakage is caught before it ships.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

# Set fake secrets BEFORE any concerto module import — required for the
# stripe_webhook module-level `stripe.api_key = ...` assignment.
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_CONCERTO_WEBHOOK_SECRET", "whsec_test")

from concerto import brand_stripe  # noqa: E402


def test_concerto_brand_session_call_has_no_stripe_account_kwarg():
    """Simulate the call shape and assert stripe_account is absent."""
    brand = brand_stripe.get_brand("concerto")
    kwargs = brand_stripe.make_stripe_session_kwargs(brand)
    assert "stripe_account" not in kwargs, (
        "Concerto must keep running on the platform account — adding "
        "stripe_account would re-route live subscriptions."
    )

    fake_stripe = MagicMock()
    with patch("concerto.brand_stripe.load_brands.cache_clear"):
        fake_stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": "price_solo_test", "quantity": 1}],
            mode="subscription",
            metadata={"product": "concerto", "plan": "solo"},
            success_url="https://concerto.run/success",
            cancel_url="https://concerto.run/#pricing",
            **kwargs,
        )

    call_kwargs = fake_stripe.checkout.Session.create.call_args.kwargs
    assert "stripe_account" not in call_kwargs
    assert call_kwargs["mode"] == "subscription"
    assert call_kwargs["metadata"]["product"] == "concerto"


def test_clickcure_brand_when_configured_routes_to_connected_account(tmp_path):
    """Inverse guard: a configured ClickCure brand DOES inject stripe_account."""
    path = os.path.join(tmp_path, "brands.toml")
    with open(path, "w") as fp:
        fp.write(
            "[brands.clickcure]\n"
            'display_name = "ClickCure"\n'
            'domain = "clickcure.co"\n'
            'support_email = "contact@clickcure.co"\n'
            'statement_descriptor = "CLICKCURE.CO"\n'
            'currency = "gbp"\n'
            'connected_account_id = "acct_test_clickcure"\n'
            'express_price_id = "price_express_test"\n'
        )
    brand_stripe.load_brands.cache_clear()
    try:
        brand = brand_stripe.get_brand("clickcure", path=path)
        kwargs = brand_stripe.make_stripe_session_kwargs(brand)
        assert kwargs == {"stripe_account": "acct_test_clickcure"}
    finally:
        brand_stripe.load_brands.cache_clear()

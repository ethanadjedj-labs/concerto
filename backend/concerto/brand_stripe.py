"""Brand-aware Stripe routing — WS3 multi-brand scaffolding.

Today Concerto runs all Stripe calls on the platform account secret
(`STRIPE_SECRET_KEY`) with no `stripe_account` override. WS3 keeps
that behaviour as the default and adds an OPT-IN path that routes a
call through a Connect account (one per brand) so the hosted
checkout, statement_descriptor and payouts inherit the connected
account identity.

The module is intentionally tiny:

* `load_brands()` reads `brands.toml` (alongside this file by
  default) and validates the schema.
* `get_brand(name)` resolves a brand by name.
* `make_stripe_session_kwargs(brand)` returns the kwargs to merge
  into a `stripe.checkout.Session.create(**kwargs)` call. For a brand
  whose `connected_account_id` is empty the result is `{}` — the
  Concerto-default path. For a configured brand the result is
  `{"stripe_account": "<acct_xxx>"}`.

Concerto's existing call sites (frontend `/api/checkout`, backend
refund / cancel) are *not* modified by WS3 because the brand for
those flows is `concerto` and the loader yields an empty
`connected_account_id`. The module is shipped so future migrations
can wire Concerto through the same path without further refactor.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "brands.toml")


@dataclass(frozen=True)
class BrandConfig:
    name: str
    display_name: str
    domain: str
    support_email: str
    statement_descriptor: str
    currency: str
    connected_account_id: str
    express_price_id: str = ""

    @property
    def has_connect(self) -> bool:
        return bool(self.connected_account_id)


class BrandNotFoundError(KeyError):
    """Raised when a caller asks for a brand that isn't in brands.toml."""


class BrandConfigError(ValueError):
    """Raised when brands.toml is malformed or missing required keys."""


def _coerce_brand(name: str, raw: dict[str, Any]) -> BrandConfig:
    required = ("display_name", "domain", "support_email",
                "statement_descriptor", "currency")
    missing = [k for k in required if k not in raw]
    if missing:
        raise BrandConfigError(
            f"brand '{name}' missing required keys: {', '.join(missing)}"
        )
    return BrandConfig(
        name=name,
        display_name=raw["display_name"],
        domain=raw["domain"],
        support_email=raw["support_email"],
        statement_descriptor=raw["statement_descriptor"],
        currency=raw["currency"],
        connected_account_id=raw.get("connected_account_id", "") or "",
        express_price_id=raw.get("express_price_id", "") or "",
    )


@lru_cache(maxsize=4)
def load_brands(path: str | None = None) -> dict[str, BrandConfig]:
    """Parse brands.toml and return {name: BrandConfig}.

    Results are LRU-cached per path; tests that want a fresh load can
    call `load_brands.cache_clear()`.
    """
    target = path or _DEFAULT_PATH
    with open(target, "rb") as fp:
        data = tomllib.load(fp)
    brands_raw = data.get("brands") or {}
    if not brands_raw:
        raise BrandConfigError(f"no [brands.*] tables found in {target}")
    return {name: _coerce_brand(name, raw) for name, raw in brands_raw.items()}


def get_brand(name: str, path: str | None = None) -> BrandConfig:
    brands = load_brands(path)
    try:
        return brands[name]
    except KeyError as exc:
        raise BrandNotFoundError(
            f"unknown brand '{name}'; known: {sorted(brands)}"
        ) from exc


def make_stripe_session_kwargs(brand: BrandConfig) -> dict[str, Any]:
    """Return the kwargs to merge into a `stripe.checkout.Session.create` call.

    For a brand WITHOUT a connected account this is `{}` — the call
    runs on the platform account exactly as today (Concerto's
    behaviour). For a brand WITH a connected account this is
    `{"stripe_account": "<acct_xxx>"}`, which makes Stripe route the
    hosted Checkout, statement_descriptor and payouts through that
    account.
    """
    if not brand.has_connect:
        return {}
    return {"stripe_account": brand.connected_account_id}

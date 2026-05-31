"""Brand-aware Stripe routing for Concerto.

Thin wrapper over arsenal.tools.stripe_business_provisioning.brand so
Concerto's code path is identical to every other product. brands.toml
is duplicated here per CLAUDE.md A.5 (products may not import siblings)
but the schema and semantics live once, in arsenal.

Call shape preserved from the WS3 scaffolding:
    get_brand("concerto")                  -> BrandConfig
    get_brand("clickcure", path="...")     -> BrandConfig
    make_stripe_session_kwargs(brand)      -> dict
    load_brands.cache_clear()              -> reset the per-path LRU
"""
from __future__ import annotations

import os

from arsenal.tools.stripe_business_provisioning.brand import (
    BrandConfig,
    BrandConfigError,
    BrandNotFoundError,
    make_stripe_session_kwargs,
)
from arsenal.tools.stripe_business_provisioning.brand import (
    load_brands as _arsenal_load_brands,
)

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "brands.toml")


def load_brands(path: str | None = None) -> dict[str, BrandConfig]:
    return _arsenal_load_brands(path or _DEFAULT_PATH)


# Expose the underlying lru_cache's cache_clear on the wrapper so call
# sites and tests can do `brand_stripe.load_brands.cache_clear()` exactly
# as they did before this module became a wrapper.
load_brands.cache_clear = _arsenal_load_brands.cache_clear  # type: ignore[attr-defined]


def get_brand(name: str, path: str | None = None) -> BrandConfig:
    brands = load_brands(path)
    try:
        return brands[name]
    except KeyError as exc:
        raise BrandNotFoundError(
            f"unknown brand '{name}'; known: {sorted(brands)}"
        ) from exc


__all__ = [
    "BrandConfig",
    "BrandConfigError",
    "BrandNotFoundError",
    "load_brands",
    "get_brand",
    "make_stripe_session_kwargs",
]

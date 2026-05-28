"""
provider_factory.py — Single switch-point for provider selection.

Set CONCERTO_PROVISIONER=northflank to use Northflank.
Default (unset, empty, or "do") uses DigitalOcean — byte-for-byte identical
to the current provisioner.py behaviour.  No environment variable = no change.

This module is the drop-in replacement for `concerto.provisioner`.
Every file that currently does:
    from concerto import provisioner
should be changed to:
    from concerto import provider_factory as provisioner

Call sites need NO changes — all exported names are identical to provisioner.py.

DEFAULT SAFETY GUARANTEE:
  With no CONCERTO_PROVISIONER env var set, this module imports from
  provider_digitalocean, which delegates directly to the existing provisioner.py.
  The behaviour is byte-for-byte identical to the pre-migration code.

ROLLBACK:
  unset CONCERTO_PROVISIONER && systemctl restart concerto concerto-trial-reaper
"""

from __future__ import annotations

import os

_PROVIDER = os.getenv("CONCERTO_PROVISIONER", "do").lower().strip()

if _PROVIDER == "northflank":
    from .provider_northflank import (  # noqa: F401
        DOAuthError,
        DOCreditError,
        DropletBootError,
        PLAN_TO_SIZE,
        destroy_droplet,
        provision_droplet,
        resume,
        suspend,
    )
else:
    # Default path: DigitalOcean.
    # provider_digitalocean delegates directly to existing provisioner.py.
    # Zero behaviour change when CONCERTO_PROVISIONER is unset or "do".
    from .provider_digitalocean import (  # noqa: F401
        DOAuthError,
        DOCreditError,
        DropletBootError,
        PLAN_TO_SIZE,
        destroy_droplet,
        provision_droplet,
        resume,
        suspend,
    )

__all__ = [
    "provision_droplet",
    "destroy_droplet",
    "suspend",
    "resume",
    "PLAN_TO_SIZE",
    "DOAuthError",
    "DOCreditError",
    "DropletBootError",
]

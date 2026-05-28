"""
provider_base.py — Abstract provider interface for Concerto VPS provisioning.

Defines the STABLE CONTRACT every provider implementation must honour.
Derived from audit-coupling.md §7 and provisioner.py in /root/concerto.

Callers (provision_router.py, stripe_webhook.py, trial_router.py, refunds.py)
depend only on these names — all identical to existing provisioner.py exports:
  - provision_droplet()   — provisions a VM and returns 4-tuple
  - destroy_droplet()     — tears down a VM; must never raise
  - suspend()             — stops compute billing / powers off
  - resume()              — restores compute / powers on
  - PLAN_TO_SIZE          — maps plan names to provider size identifiers
  - DOAuthError           — raised on invalid credentials
  - DOCreditError         — raised on insufficient credit / quota
  - DropletBootError      — raised if VM enters error state during boot
"""

from __future__ import annotations

import asyncio
import os
import re
import secrets
from abc import ABC, abstractmethod
from typing import Literal


# ── Exception hierarchy ────────────────────────────────────────────────────────

class ProvisionError(Exception):
    """Base class for all provider provisioning errors."""


class DOAuthError(ProvisionError):
    """
    Provider returned 401 — API token is invalid or expired.

    Caught by:
      provision_router.py:186–198
      trial_router.py:122–127
    """


class DOCreditError(ProvisionError):
    """
    Provider returned 402 — account has insufficient credit or quota.

    Caught by:
      provision_router.py:186–198
      trial_router.py:122–127
    """


class DropletBootError(ProvisionError):
    """
    VM was created but entered an error state during first boot.

    Caught by:
      provision_router.py:186–198
      trial_router.py:122–127
    """


# ── Plan-to-size convention ────────────────────────────────────────────────────

# Each provider module MUST define its own PLAN_TO_SIZE dict.
# This constant is imported by stripe_webhook.py:218.
# Reference (DO): {"solo": "s-2vcpu-4gb", "pro": "s-2vcpu-8gb"}
PLAN_TO_SIZE: dict[str, str] = {
    "solo": "<provider-small-size-slug>",   # 2 vCPU / 4 GB equivalent
    "pro":  "<provider-large-size-slug>",   # 2 vCPU / 8 GB equivalent
}


# ── SSH keypair helper — shared by all providers ───────────────────────────────

_KEYS_DIR = os.getenv("CONCERTO_KEYS_DIR", "/var/lib/concerto/keys")


async def generate_ssh_keypair(token: str) -> tuple[str, str]:
    """
    Generate an ed25519 SSH keypair keyed to *token*.

    Returns (private_key_path, public_key_string).
    Private key written to _KEYS_DIR/{token}.pem with mode 0o600.
    Path stored in DB.ssh_keypair_private_path.
    """
    os.makedirs(_KEYS_DIR, exist_ok=True)
    os.chmod(_KEYS_DIR, 0o700)
    key_path = os.path.join(_KEYS_DIR, f"{token}.pem")
    pub_path = f"{key_path}.pub"

    proc = await asyncio.create_subprocess_exec(
        "ssh-keygen", "-t", "ed25519", "-f", key_path, "-N", "",
        "-C", f"concerto-{token[:8].replace('_', '-')}",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    os.chmod(key_path, 0o600)

    with open(pub_path) as f:
        pub_key = f.read().strip()

    return key_path, pub_key


def sanitize_email(customer_email: str) -> str:
    """Strip non-safe characters before embedding email in shell env files (Bug #24)."""
    return re.sub(r"[^a-zA-Z0-9.+\-_@]", "", customer_email or "")


# ── Abstract provider base class ───────────────────────────────────────────────

class ProviderBase(ABC):
    """
    Abstract base for all Concerto compute providers.

    Concrete subclasses implement the four async methods below.
    Module-level functions in each provider module delegate to a singleton
    instance so callers use plain `await provisioner.provision_droplet(...)`.

    CONTRACT SEMANTICS (from audit-coupling.md §7):

    provision_droplet
    -----------------
    1. Generate ed25519 SSH keypair; inject public key into VM.
    2. Render cloud_init.yaml.j2 (or equivalent) with standard Jinja kwargs.
    3. Deliver rendered config via user_data or equivalent first-boot mechanism.
    4. Block until VM has a public address AND is reachable, or raise TimeoutError.
    5. For solo/pro/trial modes: call create_named_tunnel(token).
    6. For solo/pro modes: call db.upsert_hosted_pool() at creation and on IP confirm.
    7. Raise DOAuthError (401), DOCreditError (402), DropletBootError on errors.

    destroy_droplet
    ---------------
    1. Delete/terminate the VM identified by vps_id.
    2. Call destroy_named_tunnel(cf_tunnel_id) if non-empty.
    3. NEVER RAISE — swallow all exceptions. Callers do not catch.

    suspend
    -------
    Stop compute billing / power off.  Best-effort; log errors.
    Replaces: stripe_webhook._poweroff_droplet, hosted_lifecycle._do_power_off_droplet

    resume
    ------
    Restore compute / power on.  Best-effort; log errors.
    Replaces: stripe_webhook._poweron_droplet
    """

    @abstractmethod
    async def provision_droplet(
        self,
        api_key: str,
        region: str,
        size: str,
        token: str,
        customer_email: str = "",
        mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
    ) -> tuple[str, str, str, str]:
        """Provision a VM; return (vps_id, public_address, ssh_key_path, ttyd_password)."""
        ...

    @abstractmethod
    async def destroy_droplet(
        self,
        api_key: str,
        vps_id: str,
        cf_tunnel_id: str = "",
    ) -> None:
        """Destroy VM + CF tunnel. Must never raise."""
        ...

    @abstractmethod
    async def suspend(self, api_key: str, vps_id: str) -> None:
        """
        Stop compute billing for vps_id. Best-effort; log but don't raise.

        DO equivalent: POST /droplets/{id}/actions {"type":"power_off"}
        NF equivalent: POST /services/{id}/pause  (sets instances=0)
        """
        ...

    @abstractmethod
    async def resume(self, api_key: str, vps_id: str) -> None:
        """
        Restore compute for vps_id. Best-effort; log but don't raise.

        DO equivalent: POST /droplets/{id}/actions {"type":"power_on"}
        NF equivalent: POST /services/{id}/resume (restores instances=1)
        """
        ...

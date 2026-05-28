"""
provider_northflank.py — Northflank implementation of ProviderBase.

DORMANT BY DEFAULT.  Activated only when CONCERTO_PROVISIONER=northflank.
With no env var set, provider_factory selects DigitalOcean and this module
is never imported.

Proven API facts used (result-persistence.md, result-capabilities.md,
result-billing.md, result-dockerfile.md):

  Stable URL formula (PROVEN):
    https://{portName}--{serviceName}--{clusterNamespace}.code.run
    e.g. https://p01--ctest-persist--w4lp2d6pgkf6.code.run

  Service create endpoint (PROVEN):
    POST /v1/projects/{project}/services/deployment
    Body: {"name", "billing": {"deploymentPlan": ...},
           "deployment": {"instances": 1,
                          "external": {"imagePath": ...},
                          "docker": {"configType": ...}},
           "runtimeEnvironment": {VAR: VALUE, ...},   ← flat dict, NOT {"variables":{}}
           "ports": [{"name","internalPort","public","protocol"}]}

  Volume create (PROVEN):
    POST /v1/projects/{project}/volumes
    Body: {"name", "spec": {"storageSize": 6144, "accessMode": "ReadWriteOnce"}}

  Volume attach (PROVEN):
    POST /v1/projects/{project}/volumes/{id}/attach
    Body: {"nfObject": {"id": "<serviceId>", "type": "service"},
           "mounts": [{"containerMountPath": "/data"}]}
    (PATCH → 405, not supported)

  Pause/Resume (PROVEN, result-billing.md):
    POST /v1/projects/{project}/services/{id}/pause   → instances=0, $0 compute
    POST /v1/projects/{project}/services/{id}/resume  → instances=1

  Resume latency (PROVEN): ~11s consistently.

  configType must be set at CREATE time; changing it requires delete+recreate.
  customCommand must be a STRING (not a list).
  description field rejects "+".
  Volume survives service delete; status stays BOUND when unattached.

CONFIG TODOs (must be resolved before trials-first live test):

  TODO-IMAGE: Set CONCERTO_NF_IMAGE to the real registry/image:tag.
              The image must be the production Concerto container
              (installer/Dockerfile.northflank built and pushed to a registry).
              For private registry: pre-configure credential in NF dashboard,
              then set CONCERTO_NF_IMAGE_CRED_ID to the credential ID shown
              in the NF console (used in deployment.external.credentials).

  Pro plan: nf-compute-200-8 (2vCPU/8GB, $72/mo) — confirmed via GET /v1/plans.
            Override with CONCERTO_NF_PLAN_PRO env var if needed.

  TODO-CLUSTER-NS: Production cluster namespace may differ from eval "w4lp2d6pgkf6".
                   Verify via NF console or GET /v1/teams. Set
                   CONCERTO_NF_CLUSTER_NAMESPACE accordingly.

  TODO-SSH-WATCHER: trial_provision_watcher.py SSH-probes vps_ip + ssh_key.
                    For NF, vps_ip is an HTTPS URL (not an IP). The watcher
                    must be updated to HTTP-probe NF rows instead of SSH.
                    Interim: the watcher will skip NF rows if SSH fails
                    (NF callback populates DB via the same droplet-ready endpoint).

  CLOUDFLARE-VS-NATIVE-URL: NF provides stable HTTPS at p01--{name}--{ns}.code.run.
                              DECISION NEEDED: use NF native URL as mcp_url/ttyd_url,
                              OR still create a named CF tunnel per customer.
                              Native URL (no cloudflared) is the default here.
                              To use CF tunnels instead, set TUNNEL_TOKEN/TUNNEL_HOSTNAME
                              env vars at provision time and update entrypoint.sh to
                              start cloudflared.

  ANTHROPIC_API_KEY: Two supported paths.
    DEFAULT (path b): customer runs `claude login` via the ttyd terminal.
      Matches existing DO behavior. No per-service key injection. Safest.
    OPT-IN (path a): set CONCERTO_NF_INJECT_ANTHROPIC_KEY=1 on the empire
      backend. If ANTHROPIC_API_KEY is also set in the backend env, the
      provider injects it into each new service's runtimeEnvironment.
      The entrypoint writes it into Claude's settings file on startup.
      Risk: key visible in per-customer NF service environment listing.
      Safer alternative: NF project secret group (console → project →
      secret groups) — attach at project level so it never appears in
      per-service env listings, and the container picks it up automatically.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import secrets
import time
from typing import Literal

import httpx

from .provider_base import (
    DOAuthError,
    DOCreditError,
    DropletBootError,
    ProviderBase,
    generate_ssh_keypair,
    sanitize_email,
)

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

_NF_API_BASE = "https://api.northflank.com"

_NF_PROJECT_ID = os.getenv("CONCERTO_NF_PROJECT_ID", "concerto")

# Cluster namespace: drives the stable URL suffix.
# Proven eval value: "w4lp2d6pgkf6" (result-persistence.md).
# TODO-CLUSTER-NS: verify production namespace.
_NF_CLUSTER_NAMESPACE = os.getenv("CONCERTO_NF_CLUSTER_NAMESPACE", "w4lp2d6pgkf6")

# TODO-IMAGE: replace with real registry/image:tag before going live.
# For private registry: also set CONCERTO_NF_IMAGE_CRED_ID to the NF credential ID.
_NF_IMAGE = os.getenv("CONCERTO_NF_IMAGE", "TODO_REPLACE_WITH_REAL_IMAGE_REF")
_NF_IMAGE_CRED_ID = os.getenv("CONCERTO_NF_IMAGE_CRED_ID", "")

# Container port serving the Concerto web terminal (nginx → ttyd on 7681).
_NF_CONTAINER_PORT = int(os.getenv("CONCERTO_NF_PORT", "8080"))

# Port name in Northflank — must be stable (drives URL).
_NF_PORT_NAME = "p01"

# Volume size in MB: 6144 MB = 6 GB @ $0.15/GB/month = $0.90/month (accrues always).
_NF_VOLUME_SIZE_MB = int(os.getenv("CONCERTO_NF_VOLUME_SIZE_MB", "6144"))

# nf-compute-200: 2 vCPU / 4 GB — confirmed $0.067/hr from GET /v1/plans.
_NF_PLAN_SOLO = "nf-compute-200"

# nf-compute-200-8: 2 vCPU / 8 GB — confirmed $0.072/hr from GET /v1/plans (2026-05-20).
_NF_PLAN_PRO = os.getenv("CONCERTO_NF_PLAN_PRO", "nf-compute-200-8")

_CONCERTO_API_BASE = os.getenv("CONCERTO_API_BASE", "https://api.concerto.run")

# Poll until service reaches COMPLETED status.
# Cold start: ~80s first boot (image pull), ~37–40s cached (result-persistence.md).
# 30 polls × 5s = 150s headroom for first-boot image pulls.
_POLL_ATTEMPTS = 30
_POLL_INTERVAL_S = 5

# ── Plan-to-size mapping ───────────────────────────────────────────────────────

PLAN_TO_SIZE: dict[str, str] = {
    "solo":  _NF_PLAN_SOLO,
    "pro":   _NF_PLAN_PRO,   # nf-compute-200-8: 2vCPU/8GB
    "trial": _NF_PLAN_SOLO,  # 48h trial uses Solo-sized environment
    "byoc":  _NF_PLAN_SOLO,  # bring-your-own-cloud also defaults to Solo
}

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


# ── Internal helpers ───────────────────────────────────────────────────────────

def _nf_headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }


def _service_name(token: str) -> str:
    """Derive deterministic, NF-safe service name from buyer token."""
    raw = f"concerto-{token[:8].lower()}"
    safe = re.sub(r"[^a-z0-9-]", "-", raw)
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe[:63] or "concerto-svc"


def _volume_name(token: str) -> str:
    """Deterministic volume name — allows volume reuse on service recreate."""
    raw = f"cvol-{token[:8].lower()}"
    safe = re.sub(r"[^a-z0-9-]", "-", raw)
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe[:63] or "concerto-vol"


def _stable_url(service_name: str) -> str:
    """
    Derive the deterministic public URL.

    Formula PROVEN in result-persistence.md:
      https://{portName}--{serviceName}--{clusterNamespace}.code.run
    """
    return f"https://{_NF_PORT_NAME}--{service_name}--{_NF_CLUSTER_NAMESPACE}.code.run"


def _build_env_vars(
    token: str,
    public_key: str,
    safe_email: str,
    ttyd_password: str,
    bearer_token: str,
    callback_secret: str,
    public_url: str,
    tunnel_info: dict,
    mode: str,
    anthropic_api_key: str = "",
) -> dict[str, str]:
    """
    Build container environment variables replacing cloud_init Jinja2 rendering.

    Correspond 1-to-1 with Jinja kwargs in provisioner.py:292–307.
    BEARER_TOKEN: pre-generated here; container reads it and POSTs it to
    CONCERTO_CALLBACK_URL at startup (bearer-token callback gap, resolved in
    installer/entrypoint.northflank.sh).
    NF_PUBLIC_URL: the stable Northflank service URL computed from service_name
    via _stable_url() BEFORE _create_service is called; container uses this for
    the callback mcp_url and ttyd_url fields.

    ANTHROPIC_API_KEY: omitted by default (customer uses `claude login` via
    ttyd). Injected only when CONCERTO_NF_INJECT_ANTHROPIC_KEY=1 is set on the
    backend and ANTHROPIC_API_KEY is present — see provision_droplet.
    """
    env: dict[str, str] = {
        "CONCERTO_TOKEN":           token,
        "CONCERTO_API_BASE":        _CONCERTO_API_BASE,
        "CONCERTO_CALLBACK_URL":    f"{_CONCERTO_API_BASE}/api/internal/droplet-ready",
        "GIT_CREDS_POLL_URL":       f"{_CONCERTO_API_BASE}/api/buyer/{token}/git-credentials",
        "CONCERTO_TOKEN_PREFIX":    token[:8].replace("_", "-"),
        "CUSTOMER_EMAIL":           safe_email,
        "TTYD_PASSWORD":            ttyd_password,
        "BEARER_TOKEN":             bearer_token,
        "CALLBACK_SECRET":          callback_secret,
        "NF_PUBLIC_URL":            public_url,
        "TUNNEL_TOKEN":             tunnel_info.get("tunnel_token", ""),
        "TUNNEL_HOSTNAME":          tunnel_info.get("hostname", ""),
        "PLAN":                     mode,
        "MAX_PARALLEL_SESSIONS":    str(10 if mode == "pro" else 3),
        "RAM_LABEL":                "8 GB" if mode == "pro" else "4 GB",
        "SSH_PUBLIC_KEY":           public_key,
        "SSH_AUTHORIZED_KEY":       public_key,
    }
    if anthropic_api_key:
        env["ANTHROPIC_API_KEY"] = anthropic_api_key
    return env


async def _create_volume(
    client: httpx.AsyncClient,
    volume_name: str,
    service_name: str,
) -> None:
    """
    Create a 6144 MB NVMe SSD volume with mount configuration. Idempotent: 409 = reuse.

    API (updated 2026-05-20): POST /v1/projects/{project}/volumes now requires
    a "mounts" field with at least one entry specifying the target service.
    The mount is configured at creation time; NF auto-attaches when the named
    service starts.  The separate /attach endpoint is no longer used.

    Body: {"name", "spec": {...}, "mounts": [{"nfObject": {"id": svc, "type": "service"},
                                               "containerMountPath": "/data"}]}
    """
    body = {
        "name": volume_name,
        "spec": {
            "storageSize": _NF_VOLUME_SIZE_MB,
            "accessMode": "ReadWriteOnce",
        },
        "mounts": [
            {
                "nfObject": {"id": service_name, "type": "service"},
                "containerMountPath": "/data",
            }
        ],
    }
    resp = await client.post(
        f"/v1/projects/{_NF_PROJECT_ID}/volumes",
        json=body,
    )
    if resp.status_code in (200, 201):
        logger.info("NF volume created: %s (mount→%s:/data)", volume_name, service_name)
        return
    if resp.status_code == 409 or (
        resp.status_code == 400 and "already exists" in resp.text.lower()
    ):
        # NF API returned 400 (not 409) with body {"error":{"message":"Volume already exists"}}.
        # Observed 2026-05-21: previously documented as 409, but API behaviour drifted.
        # Treat both as the idempotent reuse path.
        logger.info("NF volume already exists (idempotent): %s", volume_name)
        return
    resp.raise_for_status()



async def _attach_volume(
    client: httpx.AsyncClient,
    volume_name: str,
    service_name: str,
) -> None:
    """Explicitly attach the volume to the service after both exist.

    Despite the API docs claiming volume.mounts at create time auto-attaches
    when the service starts, in practice attachedObjects stays empty and
    /data is never mounted in the container. The /attach endpoint reliably
    binds them.

    Idempotent: re-attaching the same service is a no-op.
    """
    body = {
        "nfObject": {"id": service_name, "type": "service"},
        "mounts": [{"containerMountPath": "/data"}],
    }
    resp = await client.post(
        f"/v1/projects/{_NF_PROJECT_ID}/volumes/{volume_name}/attach",
        json=body,
    )
    if resp.status_code not in (200, 201, 204, 409):
        # 409 = already attached → fine. Other errors should at least be
        # visible in logs, but don't abort provisioning — the buyer record
        # is created and the operator can retry attach via the API.
        import logging as _log
        _log.warning(
            "_attach_volume(%s -> %s) returned %s: %s",
            volume_name, service_name, resp.status_code, resp.text[:200],
        )


async def _create_service(
    client: httpx.AsyncClient,
    service_name: str,
    plan: str,
    env_vars: dict[str, str],
    token: str,
) -> None:
    """
    Create the Northflank deployment service.

    API (PROVEN, result-capabilities.md Item 1):
      POST /v1/projects/{project}/services/deployment
      Body structure verified against working curl from result-dockerfile.md.

    configType "default" uses the image's ENTRYPOINT (/entrypoint.northflank.sh).
    customCommand must be a STRING if used (proven in billing test).
    description rejects "+" — use token prefix with "_" → "-" substitution.

    TODO-IMAGE: Replace _NF_IMAGE placeholder with real registry/image:tag.
    TODO-IMAGE: For private registry, add deployment.external.credentials field
                with the NF credential ID (set CONCERTO_NF_IMAGE_CRED_ID).
    """
    token_prefix = token[:8].replace("_", "-").replace("+", "-")

    external = {"imagePath": _NF_IMAGE}
    if _NF_IMAGE_CRED_ID:
        external["credentials"] = _NF_IMAGE_CRED_ID

    body = {
        "name": service_name,
        "description": f"Concerto workspace {token_prefix}",
        "billing": {
            "deploymentPlan": plan,
        },
        "deployment": {
            "instances": 1,
            "external": external,
            "docker": {
                # "default" uses image's ENTRYPOINT (installer/entrypoint.northflank.sh).
                # Change to "customEntrypointCustomCommand" if explicit override needed.
                "configType": "default",
            },
        },
        "ports": [
            {
                "name": _NF_PORT_NAME,
                "internalPort": _NF_CONTAINER_PORT,
                "protocol": "HTTP",
                "public": True,
            }
        ],
        # Flat dict — proven working format (result-capabilities.md Item 1).
        # NOT {"variables": env_vars} which returns 400.
        "runtimeEnvironment": env_vars,
    }
    resp = await client.post(
        f"/v1/projects/{_NF_PROJECT_ID}/services/deployment",
        json=body,
    )
    if resp.status_code == 401:
        raise DOAuthError("Northflank API returned 401 — check CONCERTO_NF_API_TOKEN")
    if resp.status_code == 402:
        raise DOCreditError("Northflank account has insufficient credit or quota")
    resp.raise_for_status()
    logger.info("NF service created: %s (plan=%s)", service_name, plan)


async def _poll_until_running(
    client: httpx.AsyncClient,
    service_name: str,
) -> None:
    """
    Poll until service status.deployment.status == "COMPLETED".

    COMPLETED = deployment finished successfully (service is running and healthy).
    FAILED/ERROR = boot failed → raise DropletBootError.

    Cold start benchmarks (result-persistence.md):
      ~80s first boot (image pull), ~37s cached.
    Timeout: _POLL_ATTEMPTS × _POLL_INTERVAL_S = 150s (headroom for image pull).
    """
    for attempt in range(_POLL_ATTEMPTS):
        await asyncio.sleep(_POLL_INTERVAL_S)
        resp = await client.get(
            f"/v1/projects/{_NF_PROJECT_ID}/services/{service_name}"
        )
        if resp.status_code == 404:
            raise DropletBootError(
                f"NF service {service_name} disappeared during polling"
            )
        resp.raise_for_status()

        svc = resp.json().get("data", {})
        deploy_status = (
            svc.get("status", {})
            .get("deployment", {})
            .get("status", "")
        )
        if deploy_status == "COMPLETED":
            logger.info(
                "NF service %s reached COMPLETED after %ds",
                service_name, (attempt + 1) * _POLL_INTERVAL_S,
            )
            return
        if deploy_status in ("FAILED", "ERROR"):
            raise DropletBootError(
                f"NF service {service_name} entered error state: {deploy_status}"
            )
        logger.debug(
            "NF polling %d/%d: service=%s status=%s",
            attempt + 1, _POLL_ATTEMPTS, service_name, deploy_status,
        )

    raise TimeoutError(
        f"NF service {service_name} did not reach COMPLETED within "
        f"{_POLL_ATTEMPTS * _POLL_INTERVAL_S}s"
    )


# ── Provider class ─────────────────────────────────────────────────────────────

class NorthflankProvider(ProviderBase):
    """
    Northflank implementation of ProviderBase.

    Concept mapping (DO → NF):
      droplet           → NF deployment service (nf-compute-200)
      user_data         → container env vars + pre-built Docker image
      droplet ID        → NF service name (deterministic from token)
      public IPv4       → stable NF URL ({p01}--{name}--{namespace}.code.run)
      snapshot          → Docker image baked with all dependencies
      power_off         → pause (instances=0, $0 compute billing)
      power_on          → resume (instances=1, billing resumes)
      delete droplet    → delete service (volume retained separately)

    Per-customer state:
      Volume cvol-{token[:8]} persists across destroy/recreate (PROVEN).
      URL is stable as long as service name + port name are unchanged (PROVEN).

    Billing (result-billing.md):
      Running:  $0.067/hr compute + $0.90/month volume
      Paused:   $0.00/hr compute + $0.90/month volume
      Resume latency: ~11s (PROVEN, result-capabilities.md Item 2).
    """

    async def provision_droplet(
        self,
        api_key: str,
        region: str,
        size: str,
        token: str,
        customer_email: str = "",
        mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
    ) -> tuple[str, str, str, str]:
        """
        Provision a Northflank service for one Concerto customer.

        Returns (service_name, stable_url, ssh_private_key_path, ttyd_password).

        region: accepted for interface compatibility; NF region is set at
                project/cluster level, not per-service. Parameter ignored.

        size:   used for byoc mode only; solo/pro use PLAN_TO_SIZE.

        ssh_private_key_path: keypair is generated (public key injected via env).
                The private key path is stored in DB.ssh_keypair_private_path
                per contract. trial_provision_watcher.py uses this path for
                SSH probing — for NF rows that probe will fail gracefully;
                the watcher relies on the bearer-token callback populating
                the DB instead. TODO-SSH-WATCHER for full fix.
        """
        if mode == "hosted":
            mode = "solo"

        private_key_path, public_key = await generate_ssh_keypair(token)
        ttyd_password = secrets.token_hex(16)
        bearer_token = secrets.token_hex(32)
        callback_secret = secrets.token_hex(16)

        is_named_tunnel = mode in ("solo", "pro", "trial")
        tunnel_info: dict = {}

        if is_named_tunnel:
            from concerto.cf_tunnel import create_named_tunnel  # type: ignore[import]
            from concerto import db  # type: ignore[import]
            tunnel_info = await create_named_tunnel(token)
            await db.update_buyer(token, cf_tunnel_id=tunnel_info["tunnel_id"])

        safe_email = sanitize_email(customer_email)

        # Plan resolution: always go through PLAN_TO_SIZE (NF slugs), never use the raw `size`
        # parameter which carries DO sizes like "s-2vcpu-4gb" — those are invalid for NF and
        # produce a 404 on POST /services/deployment. Fallback to Solo plan for unknown modes.
        nf_plan = PLAN_TO_SIZE.get(mode, _NF_PLAN_SOLO)

        service_name = _service_name(token)
        volume_name = _volume_name(token)
        # public_url derived from service_name BEFORE _create_service so it can
        # be injected as NF_PUBLIC_URL into the container's runtimeEnvironment.
        public_url = _stable_url(service_name)

        # Opt-in ANTHROPIC_API_KEY injection (path a).
        # Default (path b): customer authenticates via `claude login` in ttyd.
        _inject_key = os.getenv("CONCERTO_NF_INJECT_ANTHROPIC_KEY", "") == "1"
        _anthropic_key = os.getenv("ANTHROPIC_API_KEY", "") if _inject_key else ""

        env_vars = _build_env_vars(
            token=token,
            public_key=public_key,
            safe_email=safe_email,
            ttyd_password=ttyd_password,
            bearer_token=bearer_token,
            callback_secret=callback_secret,
            public_url=public_url,
            tunnel_info=tunnel_info,
            mode=mode,
            anthropic_api_key=_anthropic_key,
        )

        # Store callback_secret AND mark provider='northflank' before service creation
        # so both are in DB when the container calls back.  Without this the provider
        # field stays at its schema default ('digitalocean'), which breaks auto-pause
        # (which queries WHERE provider='northflank') and the proxy URL rewrite in
        # status_router (which checks provider=='northflank').
        from concerto import db  # type: ignore[import]
        await db.update_buyer(token, callback_secret=callback_secret, provider="northflank")

        headers = _nf_headers(api_key)

        try:
            async with httpx.AsyncClient(
                base_url=_NF_API_BASE, headers=headers, timeout=30
            ) as client:
                # 1. Ensure volume exists with mount config (idempotent — safe on reprovision)
                await _create_volume(client, volume_name, service_name)

                # 2. Create deployment service
                await _create_service(
                    client=client,
                    service_name=service_name,
                    plan=nf_plan,
                    env_vars=env_vars,
                    token=token,
                )

                # 2b. Explicitly attach the volume — the auto-attach at create
                # time is unreliable (volume stays PENDING with empty
                # attachedObjects). This call is idempotent.
                await _attach_volume(client, volume_name, service_name)

                # 4. Register in hosted pool (solo/pro) — provisioning state
                if mode in ("solo", "pro"):
                    from concerto import db  # type: ignore[import]
                    await db.upsert_hosted_pool(
                        droplet_id=service_name,
                        buyer_token=token,
                        ipv4=None,
                        status="provisioning",
                        created_at=int(time.time()),
                    )

                # 5. Poll until service reaches COMPLETED (~40–80s)
                await _poll_until_running(client, service_name)

                # 6. Update hosted pool with stable URL in the ipv4 slot
                if mode in ("solo", "pro"):
                    from concerto import db  # type: ignore[import]
                    await db.upsert_hosted_pool(
                        droplet_id=service_name,
                        buyer_token=token,
                        ipv4=public_url,
                        status="active",
                        created_at=int(time.time()),
                    )

        except (DOAuthError, DOCreditError, DropletBootError, TimeoutError):
            if is_named_tunnel and tunnel_info.get("tunnel_id"):
                try:
                    from concerto.cf_tunnel import destroy_named_tunnel  # type: ignore[import]
                    await destroy_named_tunnel(tunnel_info["tunnel_id"])
                except Exception:
                    pass
            raise
        except Exception:
            if is_named_tunnel and tunnel_info.get("tunnel_id"):
                try:
                    from concerto.cf_tunnel import destroy_named_tunnel  # type: ignore[import]
                    await destroy_named_tunnel(tunnel_info["tunnel_id"])
                except Exception:
                    pass
            raise

        # vps_ip column stores public_url for NF (not an IPv4).
        # The callback (from the container via CONCERTO_CALLBACK_URL) populates
        # mcp_url and bearer_token in the DB — same mechanism as DO cloud-init.
        return service_name, public_url, private_key_path, ttyd_password

    async def destroy_droplet(
        self,
        api_key: str,
        vps_id: str,
        cf_tunnel_id: str = "",
    ) -> None:
        """
        Delete NF service identified by service_name (stored in DB.vps_id).

        Volume policy: KEEP volume on destroy so data persists across reprovisions
        (PROVEN in result-persistence.md). Volume deleted only on permanent offboard.

        Must never raise — all errors swallowed per contract.
        """
        if not vps_id:
            return

        try:
            async with httpx.AsyncClient(
                base_url=_NF_API_BASE,
                headers=_nf_headers(api_key),
                timeout=15,
            ) as client:
                resp = await client.delete(
                    f"/v1/projects/{_NF_PROJECT_ID}/services/{vps_id}"
                )
                if resp.status_code not in (200, 404):
                    logger.warning(
                        "NF delete service %s returned HTTP %s",
                        vps_id, resp.status_code,
                    )
                else:
                    logger.info("NF service deleted: %s", vps_id)
        except Exception as exc:
            logger.warning("NF destroy_droplet vps_id=%s failed: %s", vps_id, exc)

        if cf_tunnel_id:
            try:
                from concerto.cf_tunnel import destroy_named_tunnel  # type: ignore[import]
                await destroy_named_tunnel(cf_tunnel_id)
            except Exception as exc:
                logger.warning(
                    "NF destroy CF tunnel %s failed: %s", cf_tunnel_id, exc
                )

    async def suspend(self, api_key: str, vps_id: str) -> None:
        """
        Pause NF service: sets instances=0, stops compute billing (~$0/hr).

        API (PROVEN, result-billing.md):
          POST /v1/projects/{project}/services/{id}/pause → instances=0, servicePaused=True
        Resume latency after pause: ~11s (PROVEN).

        Replaces: stripe_webhook._poweroff_droplet (stripe_webhook.py:116–128)
                  hosted_lifecycle._do_power_off_droplet (hosted_lifecycle.py:29–41)
        """
        if not api_key or not vps_id:
            return
        try:
            async with httpx.AsyncClient(
                base_url=_NF_API_BASE,
                headers=_nf_headers(api_key),
                timeout=15,
            ) as client:
                resp = await client.post(
                    f"/v1/projects/{_NF_PROJECT_ID}/services/{vps_id}/pause"
                )
                if resp.status_code != 200:
                    logger.warning(
                        "NF pause service %s returned HTTP %s",
                        vps_id, resp.status_code,
                    )
                else:
                    logger.info("NF service paused (compute billing stopped): %s", vps_id)
        except Exception as exc:
            logger.warning("NF suspend vps_id=%s failed: %s", vps_id, exc)

    async def resume(self, api_key: str, vps_id: str) -> None:
        """
        Resume NF service: restores instances=1, compute billing resumes.

        API (PROVEN, result-billing.md):
          POST /v1/projects/{project}/services/{id}/resume → instances=1

        Replaces: stripe_webhook._poweron_droplet (stripe_webhook.py:130–143)
        """
        if not api_key or not vps_id:
            return
        try:
            async with httpx.AsyncClient(
                base_url=_NF_API_BASE,
                headers=_nf_headers(api_key),
                timeout=15,
            ) as client:
                resp = await client.post(
                    f"/v1/projects/{_NF_PROJECT_ID}/services/{vps_id}/resume"
                )
                if resp.status_code != 200:
                    logger.warning(
                        "NF resume service %s returned HTTP %s",
                        vps_id, resp.status_code,
                    )
                else:
                    logger.info("NF service resumed: %s", vps_id)
        except Exception as exc:
            logger.warning("NF resume vps_id=%s failed: %s", vps_id, exc)


# ── Singleton + module-level functions — identical signatures to provisioner.py ─

_provider = NorthflankProvider()

# API key from env — NEVER hardcode.
# Prod: set CONCERTO_NF_API_TOKEN in /etc/cortex/env alongside CONCERTO_DO_API_TOKEN.
_NF_API_KEY = os.getenv("CONCERTO_NF_API_TOKEN", "")


async def provision_droplet(
    do_api_key: str,
    region: str,
    size: str,
    token: str,
    customer_email: str = "",
    mode: Literal["byoc", "hosted", "solo", "pro", "trial"] = "byoc",
) -> tuple[str, str, str, str]:
    """
    Module-level wrapper preserving exact provisioner.py signature.
    do_api_key: name kept for call-site compatibility; NF token comes from
    CONCERTO_NF_API_TOKEN env var (do_api_key value ignored for NF).
    """
    return await _provider.provision_droplet(
        api_key=_NF_API_KEY,
        region=region,
        size=size,
        token=token,
        customer_email=customer_email,
        mode=mode,
    )


async def destroy_droplet(
    api_key: str,
    vps_id: str,
    cf_tunnel_id: str = "",
) -> None:
    await _provider.destroy_droplet(
        api_key=_NF_API_KEY,
        vps_id=vps_id,
        cf_tunnel_id=cf_tunnel_id,
    )


async def suspend(api_key: str, vps_id: str) -> None:
    await _provider.suspend(api_key=_NF_API_KEY, vps_id=vps_id)


async def resume(api_key: str, vps_id: str) -> None:
    await _provider.resume(api_key=_NF_API_KEY, vps_id=vps_id)

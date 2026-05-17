"""
Concerto status writer — runs every 5 minutes via systemd timer.
Checks 4 external services and writes /var/www/concerto-status/status.json.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import urllib.request
import urllib.error

OUTPUT_PATH = Path(os.getenv("CONCERTO_STATUS_OUTPUT", "/var/www/concerto-status/status.json"))
TIMEOUT = 10  # seconds per check


def _check(name: str, url: str) -> dict:
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "concerto-status-writer/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            latency_ms = round((time.monotonic() - start) * 1000)
            if resp.status < 500:
                return {"name": name, "status": "operational", "latency_ms": latency_ms}
            return {"name": name, "status": "degraded", "latency_ms": latency_ms}
    except urllib.error.HTTPError as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        if e.code < 500:
            return {"name": name, "status": "operational", "latency_ms": latency_ms}
        return {"name": name, "status": "degraded", "latency_ms": latency_ms}
    except Exception:
        latency_ms = round((time.monotonic() - start) * 1000)
        return {"name": name, "status": "down", "latency_ms": latency_ms}


def collect() -> dict:
    checks = [
        ("Concerto API", "https://api.concerto.run/healthz"),
        ("DigitalOcean API", "https://api.digitalocean.com/v2/"),
        ("Stripe API", "https://api.stripe.com/v1/"),
        ("Resend API", "https://api.resend.com/"),
    ]
    services = [_check(name, url) for name, url in checks]
    return {
        "updated_at": int(time.time()),
        "services": services,
        "incidents": [],
    }


def write() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = collect()
    tmp = OUTPUT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":")))
    tmp.replace(OUTPUT_PATH)


if __name__ == "__main__":
    write()
    print("status.json written")

"""
terminal_router.py — WebSocket proxy to customer ttyd via trycloudflare URL.

Findings applied:
  F1 — subprotocols=['tty'] forwarded on both client-accept and upstream connect
  F2 — Basic Auth injected upstream using per-buyer ttyd_password (transparent to browser)
  F3 — /terminal/{token}/frame HTTP endpoint adds CSP frame-ancestors header; branded HTML
       error pages prevent iOS Safari reader-mode ("Impression élégante") overlay
  F6 — ping_interval keeps idle connections alive; upstream close triggers 1011 to client
"""
import asyncio
import base64
import logging

import httpx
import websockets
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect

from concerto import db

router = APIRouter()
logger = logging.getLogger(__name__)

_WS_PING_INTERVAL = 30
_WS_PING_TIMEOUT = 10
_UPSTREAM_CONNECT_TIMEOUT = 30.0

_CSP_FRAME_ANCESTORS = (
    "frame-ancestors https://concerto.run https://*.vercel.app"
)

_HTML_SETTING_UP = (
    '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
    "<style>body{margin:0;font-family:system-ui;background:#faf9f5;color:#191919;display:flex;"
    "align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px}"
    ".box{max-width:320px}h2{font-size:16px;margin:0 0 8px;font-weight:500}"
    "p{font-size:13px;color:#8a847b;margin:0;line-height:1.5}"
    ".dot{display:inline-block;width:8px;height:8px;background:#cc785c;border-radius:50%;"
    "margin:0 3px;animation:p 1.4s infinite ease-in-out both}"
    ".dot:nth-child(1){animation-delay:-.32s}.dot:nth-child(2){animation-delay:-.16s}"
    "@keyframes p{0%,80%,100%{transform:scale(0);opacity:0}40%{transform:scale(1);opacity:1}}"
    "</style></head><body><div class=\"box\">"
    '<div style="margin-bottom:16px"><span class="dot"></span><span class="dot"></span>'
    '<span class="dot"></span></div>'
    "<h2>Setting up</h2><p>Your environment is initializing.<br>This takes about 3 minutes.</p>"
    "</div></body></html>"
)

_HTML_UNAVAILABLE = (
    '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">'
    "<style>body{margin:0;font-family:system-ui;background:#faf9f5;color:#191919;display:flex;"
    "align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px}"
    ".box{max-width:320px}h2{font-size:16px;margin:0 0 8px;font-weight:500}"
    "p{font-size:13px;color:#8a847b;margin:0;line-height:1.5}"
    "</style></head><body><div class=\"box\">"
    "<h2>Environment unavailable</h2>"
    "<p>This environment is no longer available.<br>"
    "Refresh the page to see your current account status.</p>"
    "</div></body></html>"
)

_PROVISIONING_STATUSES = {"paid_unprovisioned", "provisioning", "installing"}


def _ttyd_ws_url(ttyd_public_url: str) -> str:
    """Convert HTTP ttyd public URL to WebSocket URL (appends /ws)."""
    url = ttyd_public_url.rstrip("/")
    url = url.replace("https://", "wss://").replace("http://", "ws://")
    return url + "/ws"


def _basic_auth_header(ttyd_password: str) -> str:
    cred = base64.b64encode(f"concerto:{ttyd_password}".encode()).decode()
    return f"Basic {cred}"


@router.get("/terminal/{token}/frame")
async def terminal_frame(token: str):
    """Proxy ttyd HTML for iframe embedding; branded error pages prevent iOS reader-mode."""
    buyer = await db.get_buyer(token)
    if not buyer or not buyer.get("ttyd_public_url"):
        if buyer and buyer.get("status") in _PROVISIONING_STATUSES:
            return Response(
                status_code=503,
                content=_HTML_SETTING_UP,
                media_type="text/html; charset=utf-8",
                headers={"Content-Security-Policy": _CSP_FRAME_ANCESTORS},
            )
        return Response(
            status_code=410,
            content=_HTML_UNAVAILABLE,
            media_type="text/html; charset=utf-8",
            headers={"Content-Security-Policy": _CSP_FRAME_ANCESTORS},
        )

    ttyd_url = buyer["ttyd_public_url"].rstrip("/") + "/"
    auth = _basic_auth_header(buyer.get("ttyd_password") or "")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                ttyd_url,
                headers={"Authorization": auth},
                follow_redirects=True,
            )
        return Response(
            content=r.content,
            status_code=r.status_code,
            media_type=r.headers.get("content-type", "text/html"),
            headers={"Content-Security-Policy": _CSP_FRAME_ANCESTORS},
        )
    except httpx.RequestError as exc:
        logger.warning("terminal_frame proxy error: %s", exc)
        return Response(
            status_code=503,
            content=_HTML_UNAVAILABLE,
            media_type="text/html; charset=utf-8",
            headers={"Content-Security-Policy": _CSP_FRAME_ANCESTORS},
        )


@router.websocket("/terminal/{token}")
async def terminal_proxy(websocket: WebSocket, token: str):
    buyer = await db.get_buyer(token)
    if not buyer or not buyer.get("ttyd_public_url"):
        await websocket.close(code=4004)
        return

    ttyd_password = buyer.get("ttyd_password") or ""
    ws_url = _ttyd_ws_url(buyer["ttyd_public_url"])
    auth_header = _basic_auth_header(ttyd_password)

    # F1: Accept with 'tty' subprotocol if the client requested it.
    offered = [
        s.strip()
        for s in websocket.headers.get("sec-websocket-protocol", "").split(",")
    ]
    use_subprotocol = "tty" if "tty" in offered else None
    await websocket.accept(subprotocol=use_subprotocol)

    try:
        # F1: upstream connect with subprotocols=['tty']
        # F2: inject Basic Auth header transparent to browser
        async with websockets.connect(
            ws_url,
            subprotocols=["tty"],
            additional_headers={"Authorization": auth_header},
            ping_interval=_WS_PING_INTERVAL,
            ping_timeout=_WS_PING_TIMEOUT,
            open_timeout=_UPSTREAM_CONNECT_TIMEOUT,
        ) as remote_ws:

            async def to_remote():
                try:
                    async for data in websocket.iter_bytes():
                        await remote_ws.send(data)
                except WebSocketDisconnect:
                    pass

            async def to_client():
                try:
                    async for msg in remote_ws:
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except websockets.exceptions.ConnectionClosed:
                    pass

            tasks = [
                asyncio.create_task(to_remote()),
                asyncio.create_task(to_client()),
            ]
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass

    except websockets.exceptions.InvalidStatusCode as exc:
        logger.warning("ttyd rejected WS connection for token %.8s: %s", token, exc)
    except (websockets.exceptions.WebSocketException, WebSocketDisconnect):
        pass
    except Exception as exc:
        logger.error("terminal_proxy unexpected error for token %.8s: %s", token, exc)
    finally:
        # F6: close client side; code 1011 signals server-side terminal exit
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

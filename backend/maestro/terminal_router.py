"""
terminal_router.py — WebSocket proxy to customer ttyd via trycloudflare URL.

Findings applied:
  F1 — subprotocols=['tty'] forwarded on both client-accept and upstream connect
  F2 — Basic Auth injected upstream using per-buyer ttyd_password (transparent to browser)
  F3 — /terminal/{token}/frame HTTP endpoint adds CSP frame-ancestors for iframe embedding
  F6 — ping_interval keeps idle connections alive; upstream close triggers 1011 to client
"""
import asyncio
import base64
import logging

import httpx
import websockets
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect

from maestro import db

router = APIRouter()
logger = logging.getLogger(__name__)

_WS_PING_INTERVAL = 30
_WS_PING_TIMEOUT = 10
_UPSTREAM_CONNECT_TIMEOUT = 30.0

_CSP_FRAME_ANCESTORS = (
    "frame-ancestors https://maestro.run https://*.vercel.app"
)


def _ttyd_ws_url(ttyd_public_url: str) -> str:
    """Convert HTTP ttyd public URL to WebSocket URL (appends /ws)."""
    url = ttyd_public_url.rstrip("/")
    url = url.replace("https://", "wss://").replace("http://", "ws://")
    return url + "/ws"


def _basic_auth_header(ttyd_password: str) -> str:
    cred = base64.b64encode(f"maestro:{ttyd_password}".encode()).decode()
    return f"Basic {cred}"


@router.get("/terminal/{token}/frame")
async def terminal_frame(token: str):
    """Proxy ttyd HTML for iframe embedding; injects CSP frame-ancestors header."""
    buyer = await db.get_buyer(token)
    if not buyer or not buyer.get("ttyd_public_url"):
        return Response(status_code=503, content="Terminal not yet ready")

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
        return Response(status_code=503, content="Terminal unreachable")


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

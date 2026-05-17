import asyncio
import socket

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from maestro import db

router = APIRouter()

_TTYD_PORT = 7681


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


async def _wait_for_port(port: int, timeout: float = 10.0) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(0.5)
    return False


@router.websocket("/terminal/{token}")
async def terminal_proxy(websocket: WebSocket, token: str):
    buyer = await db.get_buyer(token)
    if (
        not buyer
        or not buyer.get("vps_ip")
        or not buyer.get("ssh_keypair_private_path")
    ):
        await websocket.close(code=4004)
        return

    vps_ip = buyer["vps_ip"]
    key_path = buyer["ssh_keypair_private_path"]
    local_port = _free_port()

    ssh_proc = await asyncio.create_subprocess_exec(
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=15",
        "-N",
        "-L", f"127.0.0.1:{local_port}:127.0.0.1:{_TTYD_PORT}",
        f"root@{vps_ip}",
        "-i", key_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    try:
        ready = await _wait_for_port(local_port, timeout=15.0)
        if not ready:
            await websocket.close(code=4008)
            return

        await websocket.accept()

        async with websockets.connect(
            f"ws://127.0.0.1:{local_port}/ws",
            subprotocols=["tty"],
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

    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
        pass
    finally:
        ssh_proc.terminate()
        try:
            await asyncio.wait_for(ssh_proc.wait(), timeout=3)
        except asyncio.TimeoutError:
            ssh_proc.kill()

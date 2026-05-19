"""
GitHub-style Claude sign-in for Concerto.

Replaces the old embedded-ttyd "paste the code into a terminal" flow with a
clean two-call API that mirrors how Claude's web UI links to GitHub:

  1. POST /api/buyer/{token}/oauth/start
       SSH into the droplet, (re)launch `claude setup-token` inside a detached
       tmux session, scrape the Anthropic authorization URL out of the pane,
       and return it. The frontend opens this URL in a new tab — that is the
       "Authorize with Anthropic" consent screen.

  2. POST /api/buyer/{token}/oauth/submit-code   {"code": "..."}
       Write the pasted authorization code into the waiting tmux pane,
       wait for `claude setup-token` to mint the long-lived OAuth token,
       persist it so every `claude` session on the droplet uses it
       (CLAUDE_CODE_OAUTH_TOKEN in /etc/concerto/claude.env + ~/.claude
       credentials), then promote the buyer.

Completion is still observable via the existing
GET /api/buyer/{token}/oauth-status endpoint (checks credentials on the box),
so the frontend can poll exactly like it polls the GitHub link status.

No cloud-init change is required — this drives the stock `claude` CLI that is
already installed on every droplet, so it works for already-provisioned
droplets too.
"""
import asyncio
import re
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from concerto import db

router = APIRouter()

_TMUX_SESSION = "concerto-oauth"
_SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=8",
    "-o", "BatchMode=yes",
]

# Anthropic auth URLs seen across claude-code versions:
#   https://claude.ai/oauth/authorize?...
#   https://console.anthropic.com/oauth/authorize?...
#   https://platform.claude.com/oauth/authorize?...
_URL_RE = re.compile(
    r"https://(?:claude\.com|claude\.ai|console\.anthropic\.com|platform\.claude\.com)/"
    r"[A-Za-z0-9/_\-]*oauth/authorize\?[A-Za-z0-9%&=_\-\.]+",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"sk-ant-oat01-[A-Za-z0-9_\-]+")


def _extract_token(text: str) -> str | None:
    """Pull the OAuth token out of setup-token output.

    The TUI wraps lines and drops separators, so the word "Store" from the
    following sentence ("Store this token securely") gets glued onto the end
    of the token. Strip that (and any other trailing prose) defensively.
    """
    m = _TOKEN_RE.search(text or "")
    if not m:
        return None
    tok = m.group(0)
    # Known trailing contaminants from the success message, glued on by the
    # terminal having stripped the whitespace between token and next word.
    for suffix in ("Store", "store"):
        if tok.endswith(suffix) and len(tok) > len(suffix) + 20:
            tok = tok[: -len(suffix)]
            break
    return tok

_ANSI_RE = re.compile(r"\x1b\[[0-9;>?]*[A-Za-z]")


def _clean_pane(raw: str) -> str:
    """Strip ANSI escapes and CR noise, then join hard-wrapped URL lines.

    claude setup-token (2.1.x) prints the auth URL wrapped at the terminal
    width with ANSI color codes, so the raw capture has the URL split across
    several lines. We strip escapes, drop CRs, then glue consecutive lines
    that look like a continued URL (no spaces) back together.
    """
    txt = _ANSI_RE.sub("", raw or "")
    txt = txt.replace("\r", "")
    lines = txt.split("\n")
    glued: list[str] = []
    buf = ""
    for ln in lines:
        stripped = ln.strip()
        if buf:
            # still inside a URL run: a continuation has no spaces
            if stripped and " " not in stripped:
                buf += stripped
                continue
            glued.append(buf)
            buf = ""
        if "https://" in stripped and " " not in stripped:
            buf = stripped
        else:
            glued.append(ln)
    if buf:
        glued.append(buf)
    return "\n".join(glued)

# in-memory throttle so a double-click doesn't spawn two setup-token procs
_start_locks: dict[str, float] = {}


class _CodeIn(BaseModel):
    code: str


async def _ssh(vps_ip: str, key_path: str, remote_cmd: str, timeout: int = 25) -> tuple[int, str, str]:
    cmd = ["ssh", "-i", key_path, *_SSH_OPTS, f"root@{vps_ip}", remote_cmd]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "ssh_timeout"
    return (
        proc.returncode or 0,
        out.decode("utf-8", "replace"),
        err.decode("utf-8", "replace"),
    )


async def _buyer_or_404(token: str) -> dict:
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    vps_ip = buyer.get("vps_ip")
    key_path = buyer.get("ssh_keypair_private_path")
    if not vps_ip or not key_path:
        raise HTTPException(status_code=409, detail="Environment is not ready yet")
    return buyer


@router.post("/api/buyer/{token}/oauth/start")
async def oauth_start(token: str):
    buyer = await _buyer_or_404(token)
    vps_ip = buyer["vps_ip"]
    key_path = buyer["ssh_keypair_private_path"]

    now = time.monotonic()
    last = _start_locks.get(token, 0.0)
    fresh_launch = (now - last) > 8.0
    _start_locks[token] = now

    if fresh_launch:
        # Kill any stale session, then launch claude setup-token fresh.
        # `script` gives setup-token a PTY so it prints the URL and waits for
        # the code on stdin (it refuses to run fully non-interactively).
        launch = (
            f"tmux kill-session -t {_TMUX_SESSION} 2>/dev/null; "
            f"tmux new-session -d -s {_TMUX_SESSION} "
            f"\"script -qfc 'claude setup-token' /tmp/concerto-oauth.log\"; "
            "sleep 1; echo launched"
        )
        rc, _, err = await _ssh(vps_ip, key_path, launch, timeout=25)
        if rc != 0:
            raise HTTPException(
                status_code=502,
                detail=f"Could not start sign-in on the environment ({err.strip() or rc})",
            )

    # Poll the pane for the authorization URL (setup-token prints it within a few s).
    auth_url = None
    for _ in range(12):
        rc, out, _ = await _ssh(
            vps_ip,
            key_path,
            f"tmux capture-pane -p -t {_TMUX_SESSION} 2>/dev/null; "
            "echo '---'; cat /tmp/concerto-oauth.log 2>/dev/null",
            timeout=15,
        )
        m = _URL_RE.search(_clean_pane(out))
        if m:
            auth_url = m.group(0).rstrip(").,'\"")
            break
        await asyncio.sleep(1.5)

    if not auth_url:
        raise HTTPException(
            status_code=504,
            detail="Timed out waiting for the Anthropic sign-in link. Please retry.",
        )

    return {"auth_url": auth_url}


async def _finalize_oauth(token: str, vps_ip: str, key_path: str) -> None:
    """Background: wait for setup-token to mint the token, persist it, promote.

    Runs detached from the HTTP request so submit-code can return instantly
    (the SSH wait used to exceed the cloudflared ~60s timeout -> 504 ->
    "Failed to fetch" in the browser). The frontend observes completion via
    the existing /oauth-status poll.
    """
    token_val = None
    for _ in range(20):
        await asyncio.sleep(2)
        rc, out, _ = await _ssh(
            vps_ip,
            key_path,
            "cat /tmp/concerto-oauth.log 2>/dev/null; echo '---'; "
            f"tmux capture-pane -p -t {_TMUX_SESSION} 2>/dev/null",
            timeout=15,
        )
        cleaned = _clean_pane(out)
        tok = _extract_token(cleaned)
        if tok:
            token_val = tok
            break
        low = cleaned.lower()
        # Only treat as a hard failure on explicit rejection wording — the
        # banner art / URL contain stray words, so be specific.
        if (
            "invalid code" in low
            or "expired" in low
            or "authentication failed" in low
            or "rejected" in low
        ):
            # Leave the buyer in awaiting_oauth so they can retry from the UI.
            return

    if not token_val:
        rc, out, _ = await _ssh(
            vps_ip,
            key_path,
            "test -s ~/.claude/.credentials.json && echo HAVE_CREDS || echo NO_CREDS",
            timeout=12,
        )
        if "HAVE_CREDS" not in out:
            return  # give up silently; UI poll keeps waiting / user can retry

    if token_val:
        safe_tok = token_val.replace("'", "'\\''")
        persist = (
            "mkdir -p /etc/concerto && "
            f"printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\\n' '{safe_tok}' > /etc/concerto/claude.env && "
            "chmod 600 /etc/concerto/claude.env && "
            "grep -q CLAUDE_CODE_OAUTH_TOKEN /root/.bashrc 2>/dev/null || "
            "echo 'set -a; [ -f /etc/concerto/claude.env ] && . /etc/concerto/claude.env; set +a' >> /root/.bashrc && "
            "mkdir -p /etc/systemd/system/concerto-mcp.service.d && "
            "printf '[Service]\\nEnvironmentFile=-/etc/concerto/claude.env\\n' "
            "> /etc/systemd/system/concerto-mcp.service.d/oauth.conf && "
            # claude refuses to run with bypassed permissions as root, so the
            # MCP server runs `claude` as the unprivileged `concerto` user.
            # Ensure that user exists and has the Max token in its env + HOME.
            "(id concerto >/dev/null 2>&1 || useradd -m -s /bin/bash concerto) && "
            "mkdir -p /home/concerto/.claude && "
            "(grep -q CLAUDE_CODE_OAUTH_TOKEN /home/concerto/.bashrc 2>/dev/null || "
            f"echo 'export CLAUDE_CODE_OAUTH_TOKEN={safe_tok}' >> /home/concerto/.bashrc) && "
            "chown -R concerto:concerto /home/concerto && chmod 755 /home/concerto && "
            "systemctl daemon-reload && systemctl restart concerto-mcp 2>/dev/null; "
            "echo persisted"
        )
        await _ssh(vps_ip, key_path, persist, timeout=25)

    await _ssh(
        vps_ip, key_path,
        f"tmux kill-session -t {_TMUX_SESSION} 2>/dev/null; rm -f /tmp/concerto-oauth.log; echo done",
        timeout=12,
    )
    await db.update_buyer(token, status="oauth_complete")


@router.post("/api/buyer/{token}/oauth/submit-code")
async def oauth_submit_code(token: str, body: _CodeIn):
    buyer = await _buyer_or_404(token)
    vps_ip = buyer["vps_ip"]
    key_path = buyer["ssh_keypair_private_path"]

    code = body.code.strip()
    # Users sometimes paste the whole redirect URL or "code#state"; take the code.
    if "code=" in code:
        code = re.sub(r".*code=", "", code)
        code = re.split(r"[&\s]", code)[0]
    code = code.strip()
    if not code or len(code) < 8:
        raise HTTPException(status_code=400, detail="That doesn't look like a valid code.")

    safe = code.replace("'", "'\\''")
    # The setup-token prompt is an Ink TUI: tmux "Enter" is NOT honoured and
    # the code never submits. Send the literal text, settle, then C-m
    # (real carriage return), which the TUI does accept.
    send = (
        f"tmux send-keys -t {_TMUX_SESSION} -l '{safe}' 2>/dev/null "
        f"&& sleep 0.4 "
        f"&& tmux send-keys -t {_TMUX_SESSION} C-m 2>/dev/null "
        f"&& echo sent || echo nosession"
    )
    rc, out, err = await _ssh(vps_ip, key_path, send, timeout=15)
    if "nosession" in out or rc != 0:
        raise HTTPException(
            status_code=409,
            detail="Sign-in session expired. Click \"Sign in with Claude\" again.",
        )

    # Finalize in the background; respond immediately so the browser request
    # never sits long enough to hit the tunnel timeout.
    asyncio.create_task(_finalize_oauth(token, vps_ip, key_path))
    return {"accepted": True}

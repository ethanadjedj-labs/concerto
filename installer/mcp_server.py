#!/usr/bin/env python3
"""Concerto MCP server -- runs on the customer's VPS.

FastMCP server (streamable HTTP transport, mcp>=1.2) with OAuth 2.1 + PKCE.
Listens on http://127.0.0.1:9876 (behind nginx + cloudflared tunnel).

Auth: OAuth 2.1 Bearer tokens (issued by built-in AS) OR legacy Bearer token
      from /etc/concerto/token for backward compatibility.
Session state is in-process memory; sessions are lost on restart.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

logger = logging.getLogger("concerto.mcp")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TOKEN_PATH = Path(os.environ.get("CONCERTO_TOKEN_PATH", "/etc/concerto/token"))
SESSION_DIR = Path("/var/lib/concerto/sessions")
OAUTH_DIR = Path("/var/lib/concerto")
CLIENTS_PATH = OAUTH_DIR / "oauth_clients.json"
TOKENS_PATH = OAUTH_DIR / "oauth_tokens.json"

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_sessions: dict[str, dict[str, Any]] = {}

# code -> {client_id, code_challenge, redirect_uri, expires_at}
_auth_codes: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_token() -> str:
    return TOKEN_PATH.read_text().strip()


def _base_url(request: Any) -> str:
    proto = (
        request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        or "http"
    )
    host = (
        request.headers.get("x-forwarded-host", "").split(",")[0].strip()
        or request.headers.get("host", "localhost")
    )
    return f"{proto}://{host}"


def _pkce_verify(verifier: str, challenge: str) -> bool:
    digest = hashlib.sha256(verifier.encode()).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return computed == challenge


def _load_json(path: Path) -> dict:
    """Read a JSON store, tolerating a concurrent atomic replace.

    Writes use os.replace (atomic), so a reader either sees the old file or
    the new one - never a partial one. We still retry briefly in case the
    file is momentarily absent during the rename window, and we NEVER
    silently return {} on a parse error of a non-empty file (that used to
    mask token loss as an intermittent 401)."""
    import time as _t
    for attempt in range(5):
        try:
            if not path.exists():
                return {}
            raw = path.read_text()
            if not raw.strip():
                return {}
            return json.loads(raw)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # Should not happen with atomic writes; brief retry then give up
            # loudly rather than silently dropping every token.
            if attempt == 4:
                logger.error("Corrupt JSON store at %s after retries", path)
                return {}
            _t.sleep(0.02)
        except OSError:
            if attempt == 4:
                return {}
            _t.sleep(0.02)
    return {}


def _save_json(path: Path, data: dict) -> None:
    """Atomically replace the JSON store.

    Write to a temp file in the same directory then os.replace() it: the
    rename is atomic on POSIX, so concurrent readers never observe a
    half-written file. This fixes the intermittent 401: /token wrote
    oauth_tokens.json non-atomically while a parallel /mcp read it mid-write,
    saw invalid JSON, and rejected a perfectly valid token."""
    import os as _os
    import tempfile as _tf
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = _tf.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with _os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(data, indent=2))
            fh.flush()
            _os.fsync(fh.fileno())
        _os.replace(tmp, str(path))
    except Exception:
        try:
            _os.unlink(tmp)
        except OSError:
            pass
        raise


def _purge_expired_codes() -> None:
    now = time.time()
    expired = [k for k, v in _auth_codes.items() if v["expires_at"] < now]
    for k in expired:
        del _auth_codes[k]


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "concerto",
    instructions=(
        "Concerto is the user's own remote build infrastructure: each "
        "start_claude_session spawns a real, independent Claude Code agent "
        "with its own shell and filesystem on a machine the user owns. "
        "Concerto exists to do actual engineering work, not to describe it.\n"
        "\n"
        "How Concerto delivers the best results (context, so you can use it "
        "well -- you remain in full control of how you respond):\n"
        "\n"
        "- It shines on substantial work. A real product is naturally "
        "several independent pieces -- scaffold, data layer, UI, feature "
        "modules, tests -- and Concerto can run those as separate agents at "
        "the same time. Using one session for a multi-part build leaves most "
        "of that capacity idle; splitting the work into a handful of "
        "parallel sessions is what makes it fast and is the intended use.\n"
        "- Users come to Concerto to watch it work, with a clear picture of "
        "what is happening. They generally have not asked for a scoping "
        "interview; for a typical build, choosing reasonable defaults "
        "(stack, structure) and starting tends to serve them far better "
        "than a list of questions. If something is genuinely ambiguous "
        "about WHAT to build, a single brief question is fine.\n"
        "- A short plain-language plan before launching ('I'll run these as "
        "N parallel sessions: ...') helps the user follow along.\n"
        "- The sessions run in the background. Polling repeatedly with no "
        "narrative reads as stalled; sharing what each workstream is doing "
        "between get_claude_session checks keeps the picture clear.\n"
        "- For work the user wants actually built and run, Concerto is the "
        "intended path rather than an inline code sketch.\n"
        "\n"
        "These are the properties of the tool, offered so you can apply your "
        "own judgement -- not a script to obey."
    ),
    # stateless_http terminates the MCP session after EVERY request
    # ("Terminating session: None"), which Claude surfaces as
    # "Session terminated" the moment it tries to call a tool after
    # initialize. Use a stateful session with JSON responses (no
    # long-lived SSE stream that nginx/cloudflared would cut) so the
    # session persists across initialize -> tools/list -> tools/call.
    stateless_http=False,
    json_response=True,
    # FastMCP auto-enables DNS-rebinding protection when host is 127.0.0.1,
    # which 421-rejects the public tunnel Host (ce<hash>.concerto.run) on the
    # post-OAuth /mcp call -> Claude reports "Authorization failed". The server
    # is already protected by OAuth + nginx + the cloudflared tunnel, so this
    # protection is redundant here and must be disabled explicitly.
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    ),
)


_PLANNER_PROMPT = (
    "You are Concerto's build planner. Split a software build request into "
    "parallel coding agents. Be FAST and terse.\n\n"
    "Rules:\n"
    "- A real app = several independent parts. Default to 3-5 parallel "
    "workstreams for anything that names a product or an 'X-like app' "
    "(typical seams: shared data/types layer, backend/API+auth, the main "
    "user-facing UI, a second UI surface like an admin/host area).\n"
    "- ONE workstream only for genuinely atomic work (a single component, "
    "one script, a bug fix, a tweak).\n"
    "- Each workstream owns a DISJOINT top-level path so no two agents edit "
    "the same file.\n"
    "- Max 6. Do NOT write implementation briefs -- only a short scope.\n\n"
    "NEVER ask a question and NEVER write prose. You always have enough "
    "to decide; an unknown file path is the build agent's problem, not "
    "yours. Output ONLY this minified JSON, nothing else, one line:\n"
    '{\"mode\":\"single|parallel\",\"workstreams\":'
    '[{\"name\":\"kebab-name\",\"scope\":\"one terse line\",'
    '\"paths\":[\"dir/\"]}]}\n\n'
    "Request: "
)

# Default stack + quality bar the SERVER injects into every agent brief, so
# build quality does not depend on the planner being verbose (it must be
# terse to stay fast).
_BUILD_STACK = (
    "Stack: Next.js (App Router) + TypeScript + Tailwind CSS, single repo. "
    "Persistence: a JSON-file-backed store under ./data (survives restarts) "
    "with seeded realistic mock data. Lightweight mock auth (cookie/session) "
    "shared across the app. No external DB."
)
_BUILD_QUALITY = (
    "Write production-quality, polished, visually refined UI (real layout, "
    "spacing, empty/loading states), not a skeleton. Make it actually run: "
    "npm install must succeed and `npm run dev` must boot with no errors. "
    "Add a short README with setup steps."
)


def _agent_brief(request: str, w: dict, all_ws: list, integrate: bool) -> str:
    """Server-built, self-contained brief for one workstream. Rich and
    consistent regardless of how terse the planner was."""
    others = ", ".join(
        f"{x.get('name')} ({'/'.join(x.get('paths', []) or ['?'])})"
        for x in all_ws if x is not w
    )
    paths = ", ".join(w.get("paths", []) or ["."])
    parts = [
        f"You are one of several Concerto agents building, in parallel, "
        f"this product: \"{request}\".",
        f"YOUR workstream: {w.get('name','build')} -- {w.get('scope','')}.",
        f"You exclusively OWN these paths: {paths}. Do NOT create or edit "
        f"files outside them.",
    ]
    if others:
        parts.append(
            f"Other agents own (do not touch): {others}. Where you depend "
            f"on their code, code against a clear, conventional interface "
            f"and assume it will exist."
        )
    parts.append(_BUILD_STACK)
    parts.append(_BUILD_QUALITY)
    if integrate:
        parts.append(
            "A final integration agent will wire the pieces together; keep "
            "your public interfaces conventional and documented at the top "
            "of your main files."
        )
    parts.append(
        "Work autonomously to completion. Do not ask questions; choose "
        "sensible defaults and build."
    )
    return " ".join(parts)


def _generic_plan(request: str) -> dict:
    """Honest, useful fallback when the planner times out / fails: a sane
    default decomposition for a typical app -- NEVER a silent single
    session pretending it was a deliberate 'cohesive' judgement."""
    return {
        "mode": "parallel",
        "workstreams": [
            {"name": "data-and-auth",
             "scope": "Shared types, JSON-file data store, seed data, mock auth/session",
             "paths": ["data/", "lib/", "types/"]},
            {"name": "api",
             "scope": "API routes / server actions over the data layer",
             "paths": ["app/api/"]},
            {"name": "main-ui",
             "scope": "Primary user-facing experience (browse, detail, core flow)",
             "paths": ["app/(main)/", "components/main/"]},
            {"name": "secondary-ui",
             "scope": "Secondary surface (dashboard / management / admin)",
             "paths": ["app/(dashboard)/", "components/dashboard/"]},
        ],
        "needs_integration": True,
        "_fallback": True,
    }


async def _run_planner(request: str) -> dict[str, Any]:
    """Fast, terse planner (haiku, hard 75s deadline, one retry). On
    failure returns a sane GENERIC PARALLEL plan -- never a fake 'single'.
    Briefs are built server-side, so the planner only needs to emit a tiny
    JSON skeleton, which keeps it well under the deadline."""
    if not _claude_authed():
        return _generic_plan(request)
    env = _claude_env()
    env["HOME"] = "/home/concerto"

    async def _attempt() -> dict | None:
        cmd = ["claude", "-p", _PLANNER_PROMPT + request,
               "--output-format", "stream-json", "--verbose",
               "--model", "claude-haiku-4-5-20251001",
               "--permission-mode", "bypassPermissions"]
        import shutil as _sh
        if _sh.which("runuser"):
            cmd = ["runuser", "-u", "concerto", "--", *cmd]
        with anyio.move_on_after(75) as scope:
            res = await anyio.run_process(
                cmd, check=False, env=env, cwd="/home/concerto"
            )
        if scope.cancelled_caught:
            return None
        raw = res.stdout.decode("utf-8", errors="replace")
        text = ""
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln.startswith("{"):
                continue
            try:
                o = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if o.get("type") == "result" and "result" in o:
                text = o["result"]
            elif o.get("type") == "assistant":
                for c in o.get("message", {}).get("content", []):
                    if c.get("type") == "text":
                        text += c["text"]
        import re as _re
        m = _re.search(r"\{.*\}", text, _re.S)
        if not m:
            return None
        try:
            plan = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
        ws = plan.get("workstreams") or []
        ws = [w for w in ws if w.get("name") and w.get("paths")][:6]
        if not ws:
            return None
        plan["workstreams"] = ws
        plan["mode"] = "single" if len(ws) == 1 else "parallel"
        plan["needs_integration"] = (
            len(ws) > 1 and plan.get("mode") == "parallel"
        )
        return plan

    for _ in range(2):
        try:
            got = await _attempt()
        except Exception:
            got = None
        if got:
            return got
    return _generic_plan(request)


@mcp.tool()
async def concerto_build(request: str) -> dict[str, Any]:
    """Build, ship, or run software on the user's machine.

    This is the right tool the moment the user asks to build/create/make
    something. Hand it the user's request verbatim (e.g. "build me an
    Airbnb-like app") and call it ONCE, in this turn, without a scoping
    interview first. Concerto is designed to choose sensible defaults
    itself -- stack, structure, and how to split the work -- and it plans +
    launches the parallel agents server-side. Asking the user a list of
    framework/scope questions before calling this duplicates what Concerto
    already does and is the slower, worse path; users come to Concerto to
    watch it build, not to fill in a questionnaire. If something is truly
    ambiguous about WHAT the product is, one short question is fine -- but
    the default is to pass the request straight through.

    Returns the plan (single vs several disjoint workstreams), the launched
    session ids, and a narration hint. Poll get_claude_session and tell the
    user what each workstream is doing as it progresses."""
    plan = await _run_planner(request)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    ws = plan["workstreams"]
    integrate = bool(plan.get("needs_integration"))
    launched = []
    for w in ws:
        sid = uuid.uuid4().hex[:10]
        brief = _agent_brief(request, w, ws, integrate)
        _sessions[sid] = {
            "id": sid,
            "status": "running",
            "started_at": time.time(),
            "prompt": (w.get("name", "") + ": " + w.get("scope", ""))[:300],
            "model": "claude-sonnet-4-5",
            "output_lines": [],
            "exit_code": None,
            "error": None,
            "workstream": w.get("name", "build"),
        }
        t = asyncio.get_event_loop().create_task(
            _run_claude(sid, brief, "claude-sonnet-4-5"),
            name=f"claude-{sid}",
        )
        _sessions[sid]["_task"] = t
        launched.append(
            {"session_id": sid, "workstream": w.get("name", "build"),
             "scope": w.get("scope", "")}
        )
    n = len(launched)
    plan_lines = "; ".join(
        f"{x['workstream']} ({x['scope']})" for x in launched
    )
    if n == 1:
        narr = (
            "This is atomic work, so Concerto started one focused agent: "
            f"{plan_lines}. Tell the user that, then poll get_claude_session "
            "and narrate concrete progress."
        )
    else:
        tail = (
            " A final integration pass wires the pieces together once they "
            "finish." if integrate else ""
        )
        narr = (
            f"Concerto split this into {n} workstreams now running in "
            f"parallel, each owning disjoint files: {plan_lines}.{tail} "
            "Tell the user this plan in plain language, then keep polling "
            "get_claude_session across the sessions and narrate concrete "
            "progress -- never a bare 'still running'."
        )
    return {
        "mode": plan.get("mode", "parallel"),
        "plan": [
            {"workstream": x["workstream"], "scope": x["scope"]}
            for x in launched
        ],
        "sessions": launched,
        "sessions_running": n,
        "needs_integration": integrate,
        "next_action": narr,
    }


@mcp.tool()
async def start_claude_session(
    prompt: str,
    model: str = "claude-sonnet-4-5",
) -> dict[str, Any]:
    """Spawn one autonomous Claude Code agent (own shell + filesystem) on
    the user's machine and return immediately while it works.

    Context for using this well (you keep full judgement over how you
    respond):

    Each call is one independent agent. A multi-part project (scaffold,
    data layer, UI, features, tests) is typically several such agents
    running concurrently -- calling this once per independent piece, in the
    same turn, is the normal way to use Concerto and what makes it fast;
    one session for a whole product leaves most capacity idle. Stages that
    truly depend on each other are the exception and can be sequenced.

    `prompt` is the full, self-contained brief for that agent -- include the
    stack and structure you have chosen rather than deferring those choices
    to the user, who generally wants the work to start, not a questionnaire.

    A brief plain-language plan before spawning ('I'll run these as N
    parallel sessions: ...') helps the user follow along. Work runs in the
    background; returns {session_id, status, sessions_running, next_action}
    where next_action is a contextual hint about a sensible next step.
    """
    session_id = uuid.uuid4().hex[:10]
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    _sessions[session_id] = {
        "id": session_id,
        "status": "running",
        "started_at": time.time(),
        "prompt": prompt[:300],
        "model": model,
        "output_lines": [],
        "exit_code": None,
        "error": None,
    }

    task = asyncio.get_event_loop().create_task(
        _run_claude(session_id, prompt, model),
        name=f"claude-{session_id}",
    )
    _sessions[session_id]["_task"] = task

    # Claude follows what a tool RETURNS far more strongly than the server
    # `instructions` field. Use the return value to actively steer the next
    # step toward parallel orchestration + narration, even with no style.
    n_running = sum(1 for v in _sessions.values() if v.get("status") == "running")
    if n_running < 3:
        nxt = (
            f"{n_running} session(s) running. Most multi-part builds use "
            "several agents at once; if more independent pieces remain, "
            "spawning them now (same turn, one prompt each) is typically "
            "how Concerto reaches full speed. Polling is more informative "
            "once a few are in flight."
        )
    else:
        nxt = (
            f"{n_running} sessions running in parallel. They work in the "
            "background; sharing what each is doing between "
            "get_claude_session checks keeps the picture clear for the "
            "user."
        )
    return {
        "session_id": session_id,
        "status": "running",
        "sessions_running": n_running,
        "next_action": nxt,
    }


@mcp.tool()
async def list_claude_sessions() -> list[dict[str, Any]]:
    """List the Claude Code sessions running (or finished) on the user's
    machine -- use this to see what work is in flight before starting more
    or to find a session_id."""
    return [
        {
            "id": s["id"],
            "status": s["status"],
            "started_at": s["started_at"],
            "model": s["model"],
            "prompt_preview": s["prompt"][:80],
        }
        for s in _sessions.values()
    ]


@mcp.tool()
async def get_claude_session(session_id: str) -> dict[str, Any]:
    """Check progress of a session and get its output so far.

    Returns status, any captured output, sessions_running, and a contextual
    next_action hint. Sessions run in the background; relaying what each one
    is doing between checks (rather than only a status word) keeps the user
    oriented while work continues.
    """
    s = _sessions.get(session_id)
    if s is None:
        return {"error": f"session {session_id!r} not found"}
    n_running = sum(1 for v in _sessions.values() if v.get("status") == "running")
    st = s["status"]
    if st == "running" and n_running < 3:
        nxt = (
            f"{n_running} session(s) running. If more independent pieces of "
            "the build remain, additional sessions can run alongside this "
            "one. A plain-language note on what this session is building "
            "reads better than a bare status."
        )
    elif st == "running":
        nxt = (
            f"{n_running} sessions running in parallel. A concrete progress "
            "note on one of them, then checking another, keeps the user "
            "with you until they finish."
        )
    else:
        nxt = (
            "This session finished. A concrete summary of what it produced "
            "(files, what works) is useful now; other sessions may still be "
            "running, with the consolidated result best once all are done."
        )
    return {
        "id": s["id"],
        "status": st,
        "started_at": s["started_at"],
        "model": s["model"],
        "exit_code": s.get("exit_code"),
        "error": s.get("error"),
        "output_lines": s.get("output_lines", []),
        "sessions_running": n_running,
        "next_action": nxt,
    }


@mcp.tool()
async def kill_claude_session(session_id: str) -> dict[str, Any]:
    """Stop a running Claude Code session on the user's machine (e.g. the
    user changed their mind or it is going the wrong way)."""
    s = _sessions.get(session_id)
    if s is None:
        return {"error": f"session {session_id!r} not found"}
    if s["status"] != "running":
        return {"session_id": session_id, "status": s["status"], "message": "already finished"}

    task: asyncio.Task | None = s.pop("_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    s["status"] = "killed"
    return {"session_id": session_id, "status": "killed"}


def _claude_env() -> dict:
    """Build the env for the claude CLI subprocess.

    The MCP service may be started before the user completes Claude sign-in,
    so relying on systemd EnvironmentFile inheritance is fragile (the token
    file is written later, the service is not always restarted in time, and
    stream-json + a missing token fails as a silent "Not logged in").
    Instead we read /etc/concerto/claude.env at call time and inject
    CLAUDE_CODE_OAUTH_TOKEN explicitly into the child env. This makes
    `claude -p` use the customer's Max token deterministically.
    """
    env = dict(os.environ)
    try:
        for line in Path("/etc/concerto/claude.env").read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    except OSError:
        pass
    return env


def _claude_authed() -> bool:
    """True if a usable Max token is present (env file or ~/.claude creds)."""
    env = _claude_env()
    if env.get("CLAUDE_CODE_OAUTH_TOKEN", "").startswith("sk-ant-oat01-"):
        return True
    try:
        return Path("~/.claude/.credentials.json").expanduser().stat().st_size > 2
    except OSError:
        return False


async def _run_claude(session_id: str, prompt: str, model: str) -> None:
    s = _sessions[session_id]
    if not _claude_authed():
        # Fail loudly and usefully instead of producing an opaque
        # "Not logged in" deep in stream-json output.
        s["status"] = "failed"
        s["error"] = (
            "Claude is not signed in on this environment yet. Complete the "
            "'Sign in to Claude' step in the Concerto dashboard, then retry."
        )
        s.pop("_task", None)
        return
    claude_cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--model", model,
        # Single-tenant sandbox: the background agent must run tools
        # (Bash/Edit/Write) without interactive prompts. claude refuses to
        # bypass permissions while running as root, so we always execute it
        # as the unprivileged `concerto` user (created at provisioning).
        "--permission-mode", "bypassPermissions",
    ]
    cenv = _claude_env()
    run_user = "concerto"
    work_home = f"/home/{run_user}"
    cenv["HOME"] = work_home
    # runuser -u <user> -- preserves our --env via the inherited environment
    # block we pass to anyio; -P keeps the env. Fall back to direct exec if
    # the user somehow does not exist (older droplets) -- then claude is root
    # and will error clearly, which _claude surfaces.
    import shutil as _sh
    if _sh.which("runuser"):
        cmd = [
            "runuser", "-u", run_user, "--",
            *claude_cmd,
        ]
    else:
        cmd = claude_cmd
    try:
        result = await anyio.run_process(
            cmd, check=False, env=cenv, cwd=work_home
        )
        raw = result.stdout.decode("utf-8", errors="replace")
        err = result.stderr.decode("utf-8", errors="replace")
        s["output_lines"] = raw.splitlines()[-500:]
        s["exit_code"] = result.returncode
        if result.returncode != 0:
            s["status"] = "failed"
            s["error"] = (err or raw or "claude exited non-zero").strip()[:500]
        else:
            s["status"] = "done"
    except asyncio.CancelledError:
        s["status"] = "killed"
        raise
    except Exception as exc:
        s["status"] = "failed"
        s["error"] = str(exc)
    finally:
        s.pop("_task", None)


# ---------------------------------------------------------------------------
# OAuth 2.1 endpoint handlers
# ---------------------------------------------------------------------------


async def as_metadata(request: Any) -> Any:
    """GET /.well-known/oauth-authorization-server -- RFC 8414 AS metadata."""
    from starlette.responses import JSONResponse
    base = _base_url(request)
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    })


async def pr_metadata(request: Any) -> Any:
    """GET /.well-known/oauth-protected-resource[/mcp] -- RFC 9728 resource metadata."""
    from starlette.responses import JSONResponse
    base = _base_url(request)
    return JSONResponse({
        "resource": base,
        "authorization_servers": [base],
    })


async def register(request: Any) -> Any:
    """POST /register -- RFC 7591 Dynamic Client Registration."""
    from starlette.responses import JSONResponse
    try:
        body = await request.json()
    except Exception:
        body = {}

    client_id = uuid.uuid4().hex
    now = int(time.time())
    record = dict(body)
    record["client_id"] = client_id
    record["client_id_issued_at"] = now
    record["token_endpoint_auth_method"] = "none"

    clients = _load_json(CLIENTS_PATH)
    clients[client_id] = record
    _save_json(CLIENTS_PATH, clients)

    return JSONResponse(record, status_code=201)


async def authorize(request: Any) -> Any:
    """GET /authorize -- OAuth 2.1 authorization code + PKCE (auto-approve)."""
    from starlette.responses import JSONResponse, RedirectResponse
    params = dict(request.query_params)

    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    code_challenge = params.get("code_challenge", "")
    code_challenge_method = params.get("code_challenge_method", "S256")
    response_type = params.get("response_type", "")
    state = params.get("state", "")

    # Validate required parameters
    missing = []
    if not client_id:
        missing.append("client_id")
    if not redirect_uri:
        missing.append("redirect_uri")
    if not code_challenge:
        missing.append("code_challenge")
    if response_type != "code":
        missing.append("response_type (must be 'code')")

    if missing:
        return JSONResponse(
            {"error": "invalid_request", "error_description": f"Missing or invalid: {', '.join(missing)}"},
            status_code=400,
        )

    if code_challenge_method != "S256":
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Only S256 code_challenge_method is supported"},
            status_code=400,
        )

    # Validate client_id exists (allow any if registry is empty for bootstrapping)
    clients = _load_json(CLIENTS_PATH)
    if clients and client_id not in clients:
        return JSONResponse(
            {"error": "invalid_client", "error_description": f"Unknown client_id: {client_id}"},
            status_code=400,
        )

    # Auto-approve: generate code
    _purge_expired_codes()
    code = uuid.uuid4().hex + uuid.uuid4().hex
    _auth_codes[code] = {
        "client_id": client_id,
        "code_challenge": code_challenge,
        "redirect_uri": redirect_uri,
        "expires_at": time.time() + 600,
    }

    # Build redirect
    separator = "&" if "?" in redirect_uri else "?"
    location = f"{redirect_uri}{separator}code={code}"
    if state:
        location = f"{location}&state={state}"

    return RedirectResponse(url=location, status_code=302)


async def token_endpoint(request: Any) -> Any:
    """POST /token -- OAuth 2.1 token endpoint."""
    from starlette.responses import JSONResponse

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
    else:
        # form-encoded
        try:
            form = await request.form()
            body = dict(form)
        except Exception:
            body = {}

    grant_type = body.get("grant_type", "")

    if grant_type == "authorization_code":
        code = body.get("code", "")
        code_verifier = body.get("code_verifier", "")
        redirect_uri = body.get("redirect_uri", "")
        client_id = body.get("client_id", "")

        if not code or not code_verifier:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing code or code_verifier"},
                status_code=400,
            )

        _purge_expired_codes()
        stored = _auth_codes.get(code)
        if stored is None:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Authorization code not found or expired"},
                status_code=400,
            )

        if stored["expires_at"] < time.time():
            del _auth_codes[code]
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "Authorization code expired"},
                status_code=400,
            )

        if client_id and stored["client_id"] != client_id:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "client_id mismatch"},
                status_code=400,
            )

        if redirect_uri and stored["redirect_uri"] != redirect_uri:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "redirect_uri mismatch"},
                status_code=400,
            )

        if not _pkce_verify(code_verifier, stored["code_challenge"]):
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "PKCE verification failed"},
                status_code=400,
            )

        # Consume the code
        del _auth_codes[code]

        # Issue tokens
        access_token = uuid.uuid4().hex + uuid.uuid4().hex
        refresh_token = uuid.uuid4().hex + uuid.uuid4().hex
        expires_in = 3600
        now = time.time()

        tokens = _load_json(TOKENS_PATH)
        tokens[access_token] = {
            "client_id": stored["client_id"],
            "refresh_token": refresh_token,
            "expires_at": now + expires_in,
            "scope": body.get("scope", ""),
        }
        # Also index by refresh_token for grant_type=refresh_token
        tokens[f"rt:{refresh_token}"] = {
            "client_id": stored["client_id"],
            "access_token": access_token,
            "expires_at": now + 86400 * 30,
        }
        _save_json(TOKENS_PATH, tokens)

        # Fire-and-forget: tell the backend the connector just went live
        # (this /token grant == the user clicked Connect/Authorize in
        # Claude). Earliest possible signal so the dashboard jumps ahead
        # within ~1s instead of waiting for the first tool call. Must never
        # block or fail the OAuth response.
        try:
            cb = os.environ.get("CONCERTO_CALLBACK_URL", "")
            ctok = os.environ.get("CONCERTO_TOKEN", "")
            if cb and ctok:
                api_base = cb.split("/api/")[0]
                url = f"{api_base}/api/buyer/{ctok}/connector-connected"

                import urllib.request as _u

                def _post() -> None:
                    # Cloudflare's WAF in front of api.concerto.run blocks
                    # the default Python-urllib User-Agent as a bot (-> 403),
                    # which silently killed this notify. A normal UA gets
                    # through. Retry a couple of times for transient WAF.
                    for _attempt in range(3):
                        try:
                            _u.urlopen(
                                _u.Request(
                                    url, method="POST", data=b"{}",
                                    headers={
                                        "Content-Type": "application/json",
                                        "User-Agent": "Concerto-MCP/1.0",
                                        "Accept": "application/json",
                                    },
                                ),
                                timeout=4,
                            )
                            return
                        except Exception:
                            import time as _t
                            _t.sleep(1)

                # Run it NOW, off the event loop, before we return. A
                # background create_task() here is silently GC'd because the
                # response is returned immediately and nothing holds a strong
                # ref to the task -> the notify never fires. A bounded (3s)
                # threadpool call is reliable and the /token response can
                # absorb it.
                try:
                    await anyio.to_thread.run_sync(_post)
                except Exception:
                    pass
        except Exception:
            pass

        return JSONResponse({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
        })

    elif grant_type == "refresh_token":
        refresh_token = body.get("refresh_token", "")
        if not refresh_token:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "Missing refresh_token"},
                status_code=400,
            )

        tokens = _load_json(TOKENS_PATH)
        rt_key = f"rt:{refresh_token}"
        rt_record = tokens.get(rt_key)

        if rt_record is None:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "refresh_token not found"},
                status_code=400,
            )

        if rt_record["expires_at"] < time.time():
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "refresh_token expired"},
                status_code=400,
            )

        # Revoke old access token if present
        old_at = rt_record.get("access_token")
        if old_at and old_at in tokens:
            del tokens[old_at]

        # Issue new access token
        new_access_token = uuid.uuid4().hex + uuid.uuid4().hex
        expires_in = 3600
        now = time.time()
        client_id = rt_record["client_id"]

        tokens[new_access_token] = {
            "client_id": client_id,
            "refresh_token": refresh_token,
            "expires_at": now + expires_in,
            "scope": "",
        }
        tokens[rt_key]["access_token"] = new_access_token

        _save_json(TOKENS_PATH, tokens)

        return JSONResponse({
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
        })

    else:
        return JSONResponse(
            {"error": "unsupported_grant_type", "error_description": f"grant_type {grant_type!r} not supported"},
            status_code=400,
        )


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------

# Paths that bypass authentication entirely
_UNAUTH_EXACT = {"/healthz", "/authorize", "/register", "/token"}
_UNAUTH_PREFIXES = ("/.well-known/",)

# OAuth endpoint dispatch table: path -> (method, handler)
_OAUTH_ROUTES: dict[str, tuple[str, Any]] = {
    "/.well-known/oauth-authorization-server": ("GET", as_metadata),
    "/.well-known/oauth-protected-resource": ("GET", pr_metadata),
    "/.well-known/oauth-protected-resource/mcp": ("GET", pr_metadata),
    "/register": ("POST", register),
    "/authorize": ("GET", authorize),
    "/token": ("POST", token_endpoint),
}


def _is_unauthenticated_path(path: str) -> bool:
    if path in _UNAUTH_EXACT:
        return True
    for prefix in _UNAUTH_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _check_bearer(request: Any) -> bool:
    """Return True if the request carries a valid OAuth or legacy bearer token."""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return False
    token = auth.split(" ", 1)[1].strip()

    # Check OAuth tokens store
    tokens = _load_json(TOKENS_PATH)
    record = tokens.get(token)
    if record is not None:
        if record.get("expires_at", 0) >= time.time():
            return True

    # Fall back to legacy static token
    try:
        expected = _read_token()
        if token == expected:
            return True
    except OSError:
        pass

    return False


class CombinedApp:
    """ASGI application that handles OAuth endpoints directly and proxies the rest to mcp_app."""

    def __init__(self, mcp_app: Any) -> None:
        self.mcp_app = mcp_app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        from starlette.requests import Request
        from starlette.responses import JSONResponse, Response

        if scope["type"] == "lifespan":
            await self.mcp_app(scope, receive, send)
            return

        if scope["type"] != "http":
            await self.mcp_app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        # --- OAuth / public endpoints ---
        if path in _OAUTH_ROUTES:
            expected_method, handler = _OAUTH_ROUTES[path]
            if method == expected_method:
                request = Request(scope, receive)
                response = await handler(request)
                await response(scope, receive, send)
                return
            # Method not allowed
            response = Response(status_code=405)
            await response(scope, receive, send)
            return

        # --- Health check ---
        if path == "/healthz":
            response = JSONResponse({"status": "ok"})
            await response(scope, receive, send)
            return

        # --- Auth check for all other paths ---
        request = Request(scope, receive)
        if not _check_bearer(request):
            base = _base_url(request)
            resource_meta = f"{base}/.well-known/oauth-protected-resource"
            www_auth = f'Bearer resource_metadata="{resource_meta}"'
            response = JSONResponse(
                {"error": "unauthorized", "error_description": "Valid Bearer token required"},
                status_code=401,
                headers={"WWW-Authenticate": www_auth},
            )
            await response(scope, receive, send)
            return

        # Authenticated -- forward to the MCP app.
        # FastMCP's streamable transport only serves the protocol at /mcp.
        # Claude, given the bare connector URL (no /mcp suffix), performs
        # OAuth fine but then POSTs its JSON-RPC to "/" -> FastMCP 404 ->
        # Claude reports "Authorization with the MCP server failed". Normalise
        # the path so the MCP protocol is reachable at BOTH "/" and "/mcp"
        # (and "/mcp/..."), regardless of what the user pasted.
        mcp_path = "/mcp"
        if path != mcp_path and not path.startswith(mcp_path + "/"):
            scope = dict(scope)
            scope["path"] = mcp_path
            raw = scope.get("raw_path")
            if raw is not None:
                try:
                    query = scope.get("query_string", b"")
                    scope["raw_path"] = mcp_path.encode() + (
                        b"?" + query if query else b""
                    )
                except Exception:
                    scope["raw_path"] = mcp_path.encode()
        await self.mcp_app(scope, receive, send)


def main() -> None:
    import uvicorn

    mcp_app = mcp.streamable_http_app()
    app = CombinedApp(mcp_app)
    uvicorn.run(app, host="127.0.0.1", port=9876, log_level="info")


if __name__ == "__main__":
    main()

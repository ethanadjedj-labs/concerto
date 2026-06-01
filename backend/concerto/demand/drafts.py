"""Authentic draft-reply generator.

For each high-relevance opportunity, produce a TEMPLATE draft that the
operator (Ethan) edits and posts AS HIMSELF, disclosing he's Concerto's
maker. Drafts are intentionally personal and value-first — the system
does not auto-post them.

Design rules:
  * Disclose maker affiliation in the first paragraph. No covert promo.
  * Lead with value (what the system Concerto would actually do for the
    asker), not pricing or pitch.
  * Only mention Concerto where it would *actually help the asker* — if
    the signals don't justify it, the draft is just a helpful answer
    without a product mention.
  * Include a one-line "personalize this" hint so Ethan knows where to
    inject specifics from the thread.
  * Output is markdown, ready to paste into the operator's editor.

The drafter is template-driven, not LLM-driven, by design: deterministic
outputs are easier to audit, and we don't want hallucinated product
claims.
"""
from __future__ import annotations

from .models import Opportunity


CONCERTO_TLDR = (
    "Concerto is the hosted MCP server I built for exactly this — you "
    "talk to Claude (Desktop / Code / any MCP client), and Claude spawns, "
    "monitors, and kills N Claude Code sessions on a managed VPS. "
    "Sessions persist between chats and devices. $49/mo Solo, $99/mo Pro."
)


# Map matched-signal labels to which "angle" the draft should take.
# The angle controls which template body is used.
_ANGLE_FOR_SIGNAL: dict[str, str] = {
    "parallel-claude-code": "parallel",
    "multiple-claude-code": "parallel",
    "claude-code-parallel": "parallel",
    "tmux-pain": "parallel",
    "juggling-terminals": "parallel",
    "claude-code-orchestration": "orchestration",
    "claude-code-managed": "managed",
    "claude-code-vps": "managed",
    "background-agent": "managed",
    "session-persistence": "managed",
    "context-switch-pain": "managed",
    "mcp-orchestration": "mcp",
    "mcp-server-build": "mcp",
    "multi-agent": "orchestration",
    "agent-orchestration": "orchestration",
}


def _pick_angle(opp: Opportunity) -> str:
    for sig in opp.matched_signals:
        if sig in _ANGLE_FOR_SIGNAL:
            return _ANGLE_FOR_SIGNAL[sig]
    return "generic"


def _platform_disclosure(opp: Opportunity) -> str:
    if opp.source == "hn":
        return (
            "Hey — disclosure first: I'm the maker of Concerto "
            "(concerto.run), so take this with that grain of salt."
        )
    if opp.source == "reddit":
        return (
            "Disclosure: I built Concerto (concerto.run), so I'm biased. "
            "Sharing because it sounds directly relevant to what you're "
            "describing."
        )
    return (
        "Disclosure: I'm the maker of Concerto (concerto.run). "
        "Mentioning it because it lines up with what you're asking."
    )


_TEMPLATES: dict[str, str] = {
    "parallel": """\
{disclosure}

The thing that actually breaks at N>1 Claude Code sessions is not
running them — `claude` can run N times — it's:
  - re-priming context every time you restart
  - tail/-f-ing N terminals to see which one needs your input
  - losing state when your laptop sleeps mid-refactor

{concerto_tldr}
You talk to one Claude and ask it to "spawn 3 sessions: one on the
refactor branch, one on the bug, one on the perf spike." It reports
back, and the sessions survive disconnects.

[Personalize: reference {personal_hook} and offer to share the specific
config / a free trial if it fits.]
""",
    "orchestration": """\
{disclosure}

For multi-agent orchestration with Claude Code specifically, the gap I
kept hitting was: orchestrators that *spawn* agents are easy, but ones
that let the *parent conversation* spawn, inspect, and kill child
sessions through real tool calls (not text scraping) are rare.

{concerto_tldr}
It exposes spawn/list/get_progress/kill as MCP tools, so a Claude in
Desktop or Code can drive a fleet without you ever touching tmux.

[Personalize: connect to {personal_hook}; offer a hands-on if useful.]
""",
    "managed": """\
{disclosure}

For background / managed Claude Code, the things I'd actually look for:
  - sessions survive your laptop sleep / disconnect
  - can re-attach from a different device
  - per-session resource caps so one runaway agent doesn't eat the box
  - access via MCP so your chat client can drive it

{concerto_tldr}
That's exactly the shape — managed VPS, per-session isolation, MCP
control surface. Happy to walk through how it's wired.

[Personalize: tie to {personal_hook}.]
""",
    "mcp": """\
{disclosure}

If you're hitting MCP-server-side orchestration questions, the trick
I'd flag: keep the MCP surface narrow (spawn/list/inspect/kill) and put
the policy (which model, which workspace, which limits) on the *server*
side, not the client. Otherwise every MCP client needs to know the
operational details.

{concerto_tldr}
It's worth a look if only as a worked example of where to draw that
line.

[Personalize: cite {personal_hook}; ask a clarifying question instead
of pitching if the thread is more theoretical than buying-shaped.]
""",
    "generic": """\
{disclosure}

{concerto_tldr}

[Personalize: pull a specific quote from the post ({personal_hook}) and
make the reply actually answer their question — don't lead with the
product. Cut the product mention entirely if it doesn't fit.]
""",
}


def _personal_hook(opp: Opportunity) -> str:
    # Operator-visible breadcrumb — what specific phrase from the thread
    # the reply should call back to. We pick the first ~120 chars of the
    # body or the title.
    seed = (opp.body or opp.title or "").strip().replace("\n", " ")
    if len(seed) > 140:
        seed = seed[:140].rstrip() + "…"
    return f'"{seed}"' if seed else "a specific line from the original post"


def draft_reply(opp: Opportunity) -> str:
    """Return a markdown-formatted draft reply for the operator to edit."""
    angle = _pick_angle(opp)
    tpl = _TEMPLATES.get(angle, _TEMPLATES["generic"])
    return tpl.format(
        disclosure=_platform_disclosure(opp),
        concerto_tldr=CONCERTO_TLDR,
        personal_hook=_personal_hook(opp),
    )


def package(opp: Opportunity) -> dict:
    """Return the full operator hand-off package for one opportunity."""
    return {
        "url": opp.url,
        "platform": opp.source,
        "title": opp.title,
        "author": opp.author,
        "author_context": opp.author_context,
        "score": opp.score,
        "matched_signals": opp.matched_signals,
        "rationale": opp.rationale,
        "why_relevant": opp.rationale,
        "angle": _pick_angle(opp),
        "draft_reply": draft_reply(opp),
    }

"""Hacker News source — uses the public Algolia search API.

API: https://hn.algolia.com/api — explicitly intended for programmatic
access. No auth required. Rate limits are generous; we keep our footprint
small by querying a focused set of terms.

Story / comment text comes from the public site; URLs are stable.
"""
from __future__ import annotations

import logging
import time

import httpx

from ..models import Opportunity
from . import USER_AGENT


_log = logging.getLogger(__name__)

# Terms tuned for Concerto's pain space. Each term is a separate request
# because Algolia's relevance is per-query.
DEFAULT_QUERIES: list[str] = [
    "claude code parallel",
    "claude code orchestration",
    "multiple claude code",
    "mcp orchestration",
    "agent orchestration",
    "claude code session",
    "managed claude code",
    "claude code background",
    "claude code multiple terminal",
    "claude code remote",
]

BASE = "https://hn.algolia.com/api/v1"


def fetch(
    queries: list[str] | None = None,
    *,
    hits_per_page: int = 20,
    tags: str = "(story,comment)",
    client: httpx.Client | None = None,
    now: int | None = None,
) -> list[Opportunity]:
    """Run each query against HN Algolia and return deduplicated Opportunities."""
    queries = queries or DEFAULT_QUERIES
    own_client = client is None
    if own_client:
        client = httpx.Client(
            timeout=15.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True
        )
    fetched_ts = now or int(time.time())
    seen: set[str] = set()
    out: list[Opportunity] = []
    try:
        for q in queries:
            try:
                r = client.get(
                    f"{BASE}/search",
                    params={
                        "query": q,
                        "tags": tags,
                        "hitsPerPage": hits_per_page,
                    },
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:  # network / 5xx — log and continue
                _log.warning("HN query %r failed: %s", q, e)
                continue

            for hit in data.get("hits", []):
                opp = _hit_to_opp(hit, fetched_ts)
                if opp is None:
                    continue
                if opp.dedup_key() in seen:
                    continue
                seen.add(opp.dedup_key())
                out.append(opp)
    finally:
        if own_client:
            client.close()
    return out


def _hit_to_opp(hit: dict, fetched_ts: int) -> Opportunity | None:
    object_id = hit.get("objectID")
    if not object_id:
        return None
    title = hit.get("title") or hit.get("story_title") or ""
    body = hit.get("story_text") or hit.get("comment_text") or ""
    # Strip the most common HN HTML so the scorer sees plain text.
    body = (
        body.replace("&#x27;", "'")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&gt;", ">")
        .replace("&lt;", "<")
    )
    url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    author = hit.get("author") or ""
    points = hit.get("points")
    num_comments = hit.get("num_comments")
    ctx_bits = []
    if points is not None:
        ctx_bits.append(f"{points} points")
    if num_comments is not None:
        ctx_bits.append(f"{num_comments} comments")
    if hit.get("_tags"):
        kind = next((t for t in hit["_tags"] if t in ("story", "comment", "show_hn", "ask_hn")), None)
        if kind:
            ctx_bits.append(kind)
    author_context = ", ".join(ctx_bits)

    created_ts = hit.get("created_at_i") or 0

    # Comments lack their own title; synthesize one from the first line.
    if not title and body:
        first_line = body.strip().splitlines()[0] if body.strip() else ""
        title = first_line[:140] or f"HN comment {object_id}"

    return Opportunity(
        source="hn",
        source_id=str(object_id),
        url=url,
        title=title,
        body=body,
        author=author,
        author_context=author_context,
        created_ts=int(created_ts),
        fetched_ts=fetched_ts,
    )

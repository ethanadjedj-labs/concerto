"""Stack Exchange source — uses the public Stack Exchange 2.3 API.

API docs: https://api.stackexchange.com/docs — explicitly intended for
programmatic access. No auth required for the read endpoints we use,
though a registered app key raises the per-IP quota from 300 to 10,000
calls/day. Set CONCERTO_STACKEXCHANGE_KEY to use one.

We query two sites:
  * stackoverflow — by far the largest dev Q&A site
  * ai.stackexchange — sometimes has Claude / agent-orchestration threads

Concerto-shaped intent terms are run against the search/advanced endpoint
with `?body=...` style filters so we get the question text (the default
filter strips bodies, which would gut the scorer).
"""
from __future__ import annotations

import logging
import os
import re
import time

import httpx

from ..models import Opportunity
from . import USER_AGENT


_log = logging.getLogger(__name__)


# Sites to query. Stack Exchange API uses the "site" param (the
# subdomain). Order matters only for log readability.
DEFAULT_SITES: list[str] = ["stackoverflow", "ai"]

# Each query is run against /search/advanced as the `q=` term. The terms
# are tuned for Concerto's pain space — same shape as the HN queries but
# adapted to how questions are titled on SO/SE.
DEFAULT_QUERIES: list[str] = [
    "claude code parallel",
    "claude code multiple sessions",
    "claude code orchestration",
    "mcp server orchestration",
    "agent orchestration claude",
    "claude code background",
    "claude code remote vps",
    "anthropic claude code session",
]

BASE = "https://api.stackexchange.com/2.3"

# Use a withbody filter so we get the question body (default filter omits it).
# This is the documented stock "withbody" filter id from api.stackexchange.com.
_WITHBODY_FILTER = "withbody"


def fetch(
    queries: list[str] | None = None,
    sites: list[str] | None = None,
    *,
    pagesize: int = 20,
    client: httpx.Client | None = None,
    now: int | None = None,
    api_key: str | None = None,
) -> list[Opportunity]:
    """Search Stack Exchange sites for Concerto-shaped questions."""
    queries = queries or DEFAULT_QUERIES
    sites = sites or DEFAULT_SITES
    api_key = api_key or os.environ.get("CONCERTO_STACKEXCHANGE_KEY") or None
    own_client = client is None
    if own_client:
        client = httpx.Client(
            timeout=15.0,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )
    fetched_ts = now or int(time.time())
    seen: set[str] = set()
    out: list[Opportunity] = []
    try:
        for site in sites:
            for i, q in enumerate(queries):
                if i > 0:
                    # SE allows ~30 req/sec but is strict on burst. 0.5s
                    # cadence keeps us well below the documented throttles.
                    time.sleep(0.5)
                params = {
                    "site": site,
                    "q": q,
                    "pagesize": pagesize,
                    "order": "desc",
                    "sort": "creation",
                    "filter": _WITHBODY_FILTER,
                }
                if api_key:
                    params["key"] = api_key
                try:
                    r = client.get(f"{BASE}/search/advanced", params=params)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:  # network / 4xx / 5xx — log and continue
                    _log.warning("SE %s q=%r failed: %s", site, q, e)
                    continue
                # SE encodes quota / backoff state in the response body.
                backoff = data.get("backoff")
                if backoff:
                    _log.info("SE %s requested backoff=%ss; honoring", site, backoff)
                    try:
                        time.sleep(min(int(backoff), 30))
                    except Exception:
                        pass
                for item in data.get("items", []):
                    opp = _item_to_opp(item, site, fetched_ts)
                    if opp is None:
                        continue
                    if opp.dedup_key() in seen:
                        continue
                    seen.add(opp.dedup_key())
                    out.append(opp)
                if data.get("has_more") is False and not data.get("items"):
                    # No hits for this query on this site; that's fine.
                    pass
    finally:
        if own_client:
            client.close()
    return out


def _strip_html(s: str) -> str:
    """Strip the minimal HTML SE returns inside question bodies."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = (
        s.replace("&amp;", "&")
        .replace("&#39;", "'")
        .replace("&#x27;", "'")
        .replace("&quot;", '"')
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
    )
    return re.sub(r"\s+", " ", s).strip()


def _item_to_opp(item: dict, site: str, fetched_ts: int) -> Opportunity | None:
    qid = item.get("question_id")
    if not qid:
        return None
    title = _strip_html(item.get("title") or "")
    body = _strip_html(item.get("body") or "")
    url = item.get("link") or f"https://{site}.stackexchange.com/q/{qid}"
    owner = item.get("owner") or {}
    author = owner.get("display_name") or ""
    tags = item.get("tags") or []
    bits: list[str] = []
    if site == "stackoverflow":
        bits.append("stackoverflow")
    else:
        bits.append(f"{site}.stackexchange")
    if item.get("score") is not None:
        bits.append(f"{item['score']} score")
    if item.get("answer_count") is not None:
        bits.append(f"{item['answer_count']} answers")
    if item.get("is_answered") is False:
        bits.append("unanswered")
    if tags:
        bits.append("tags: " + ",".join(tags[:5]))
    author_context = " | ".join(bits)
    created_ts = int(item.get("creation_date") or 0)
    # Use stackoverflow:<qid> or se-<site>:<qid> as source_id so duplicate
    # questions across sites don't collide.
    sid_prefix = "so" if site == "stackoverflow" else f"se-{site}"
    return Opportunity(
        source="stackexchange",
        source_id=f"{sid_prefix}:{qid}",
        url=url,
        title=title,
        body=body,
        author=author,
        author_context=author_context,
        created_ts=created_ts,
        fetched_ts=fetched_ts,
    )

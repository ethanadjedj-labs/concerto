"""Reddit source — uses public RSS feeds.

Reddit's RSS endpoints (`https://www.reddit.com/r/<sub>/new/.rss`) are
designed for syndication and remain accessible without OAuth as long as
the client identifies itself and respects rate limits. We send a clear
User-Agent and query each subreddit only once per scan.

For deeper authenticated access (Reddit OAuth, PRAW), the operator can
add credentials later — see docs/demand/README.md. The RSS path is the
minimal, no-credential, ToS-friendly default.
"""
from __future__ import annotations

import logging
import random
import re
import time

import httpx

from ..models import Opportunity
from . import USER_AGENT


_log = logging.getLogger(__name__)


DEFAULT_SUBREDDITS: list[str] = [
    "ClaudeAI",
    "mcp",
    "cursor",
    "LocalLLaMA",
    "SaaS",
    "ChatGPTCoding",
]


BASE = "https://www.reddit.com"


def fetch(
    subreddits: list[str] | None = None,
    *,
    limit: int = 25,
    sort: str = "new",
    client: httpx.Client | None = None,
    now: int | None = None,
) -> list[Opportunity]:
    """Pull the latest posts from each subreddit's RSS feed."""
    subreddits = subreddits or DEFAULT_SUBREDDITS
    own_client = client is None
    if own_client:
        # Reddit prefers a UA that looks like a real client identifier.
        ua = f"Mozilla/5.0 (compatible; {USER_AGENT})"
        client = httpx.Client(
            timeout=15.0,
            headers={"User-Agent": ua, "Accept": "application/atom+xml,text/xml,*/*"},
            follow_redirects=True,
        )
    fetched_ts = now or int(time.time())
    out: list[Opportunity] = []
    try:
        for i, sub in enumerate(subreddits):
            if i > 0:
                # Reddit rate-limits aggressively per IP. Pause ~2-3s between
                # subreddit fetches; this is well under the documented 60
                # req/min limit and consistent with how a normal RSS reader
                # would poll.
                time.sleep(2.0 + random.random())
            url = f"{BASE}/r/{sub}/{sort}/.rss?limit={limit}"
            try:
                r = client.get(url)
                r.raise_for_status()
            except Exception as e:
                _log.warning("Reddit r/%s fetch failed: %s", sub, e)
                continue
            entries = _parse_atom(r.text)
            for e in entries:
                e["subreddit"] = sub
                opp = _entry_to_opp(e, fetched_ts)
                if opp is not None:
                    out.append(opp)
    finally:
        if own_client:
            client.close()
    return out


# ---------------------------------------------------------------------------
# Atom parsing — minimal, dependency-free.
# Reddit's RSS is well-formed Atom; we extract id / title / link / author /
# updated / content. We use regex (good enough; no XML attack surface — we
# only ever read content already fetched ourselves).
# ---------------------------------------------------------------------------


_ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
_TAG_RES = {
    "id": re.compile(r"<id>(.*?)</id>", re.DOTALL),
    "title": re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL),
    "link": re.compile(r'<link\s+href="([^"]+)"'),
    "author_name": re.compile(r"<author>.*?<name>(.*?)</name>.*?</author>", re.DOTALL),
    "updated": re.compile(r"<updated>(.*?)</updated>"),
    "content": re.compile(r'<content[^>]*>(.*?)</content>', re.DOTALL),
}


def _parse_atom(xml: str) -> list[dict]:
    entries: list[dict] = []
    for raw in _ENTRY_RE.findall(xml):
        e: dict = {}
        for k, rx in _TAG_RES.items():
            m = rx.search(raw)
            e[k] = m.group(1).strip() if m else ""
        entries.append(e)
    return entries


def _strip_html(s: str) -> str:
    # Reddit content is CDATA-wrapped HTML. Strip tags, unescape common entities.
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", " ", s)
    s = (
        s.replace("&amp;", "&")
        .replace("&#x27;", "'")
        .replace("&quot;", '"')
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    return re.sub(r"\s+", " ", s).strip()


def _parse_iso8601(s: str) -> int:
    # 2026-06-01T19:38:13+00:00 -> unix
    try:
        # Python 3.12 fromisoformat handles the +00:00 form.
        from datetime import datetime
        return int(datetime.fromisoformat(s).timestamp())
    except Exception:
        return 0


def _entry_to_opp(e: dict, fetched_ts: int) -> Opportunity | None:
    eid = e.get("id") or ""
    if not eid:
        return None
    # IDs look like: t3_1tu29sp  — extract the bit after the underscore as source_id
    source_id = eid.split("/")[-1] if "/" in eid else eid
    if source_id.startswith("t3_"):
        source_id = source_id[3:]
    title = _strip_html(e.get("title") or "")
    body = _strip_html(e.get("content") or "")
    author = e.get("author_name") or ""
    if author.startswith("/u/"):
        author = author[3:]
    url = e.get("link") or ""
    created_ts = _parse_iso8601(e.get("updated") or "")
    subreddit = e.get("subreddit", "")
    return Opportunity(
        source="reddit",
        source_id=source_id,
        url=url,
        title=title,
        body=body,
        author=author,
        author_context=f"r/{subreddit}" if subreddit else "",
        created_ts=created_ts,
        fetched_ts=fetched_ts,
    )

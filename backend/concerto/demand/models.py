"""Data models for the demand radar."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib
import json


@dataclass
class Opportunity:
    """A single detected demand signal — a real public post that may express
    Concerto-shaped demand. All fields point to publicly-observable data;
    no fabricated or inferred identity info."""

    source: str  # "hn", "reddit", "stackoverflow", ...
    source_id: str  # platform-specific ID (HN object_id, reddit post id, SE q_id)
    url: str  # live URL the operator can click and read
    title: str
    body: str  # selftext / question body / story text (may be empty)
    author: str  # public author handle as the platform exposes it
    author_context: str  # subreddit / HN points / SE tags — public metadata only
    created_ts: int  # unix seconds, when the post was made
    fetched_ts: int  # unix seconds, when we observed it
    score: float = 0.0  # relevance score 0..1
    matched_signals: list[str] = field(default_factory=list)
    rationale: str = ""  # human-readable why-this-matters

    def dedup_key(self) -> str:
        return f"{self.source}:{self.source_id}"

    def fingerprint(self) -> str:
        # Used by storage to detect identical re-fetches.
        return hashlib.sha1(
            f"{self.dedup_key()}|{self.title}|{self.url}".encode("utf-8")
        ).hexdigest()

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        d["matched_signals"] = json.dumps(self.matched_signals)
        return d

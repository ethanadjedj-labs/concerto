"""
Concerto Demand Radar.

Scans public, ToS-compliant sources (Hacker News Algolia API, Reddit RSS,
Stack Exchange API) for posts expressing the pain Concerto solves —
parallel Claude Code orchestration, MCP workflow management, agent
fleet coordination — and surfaces ranked opportunities for the operator
to engage with authentically (as himself or as the openly-branded
Concerto account).

The system never posts on behalf of fake humans. It DETECTS demand and
DRAFTS responses; a human reviews and posts. See docs/demand/README.md.
"""

__all__ = ["models", "storage", "scoring", "sources"]

"""Demand radar CLI.

Usage:
    python -m concerto.demand.cli scan        # fetch + score + store
    python -m concerto.demand.cli top [-n 20] # print ranked opportunities

Exit codes:
    0 success, 2 usage, 1 unexpected error.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Sequence

from . import drafts, scoring, storage
from .models import Opportunity
from .sources import hackernews, reddit, stackexchange


def cmd_scan(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("demand.scan")

    fetchers = []
    if "hn" in args.sources:
        fetchers.append(("hn", lambda: hackernews.fetch()))
    if "reddit" in args.sources:
        fetchers.append(("reddit", lambda: reddit.fetch()))
    if "stackexchange" in args.sources:
        fetchers.append(("stackexchange", lambda: stackexchange.fetch()))
    if not fetchers:
        print("no sources selected", file=sys.stderr)
        return 2

    total_fetched = 0
    total_accepted = 0
    with storage.connect(args.db) as conn:
        for name, fn in fetchers:
            run_id = storage.start_run(conn, name)
            try:
                log.info("source=%s fetching...", name)
                opps = fn()
                log.info("source=%s fetched=%d", name, len(opps))
                accepted = 0
                for opp in opps:
                    s = scoring.score_post(opp.title, opp.body, opp.created_ts)
                    opp.score = s.score
                    opp.matched_signals = s.matched_signals
                    opp.rationale = s.rationale
                    if opp.score >= args.min_store:
                        storage.upsert(conn, opp)
                        accepted += 1
                total_fetched += len(opps)
                total_accepted += accepted
                storage.finish_run(conn, run_id, len(opps), accepted)
                log.info("source=%s stored=%d", name, accepted)
            except Exception as e:  # pragma: no cover
                log.exception("source=%s failed", name)
                storage.finish_run(conn, run_id, 0, 0, error=str(e))
                if args.strict:
                    return 1

    print(
        json.dumps(
            {
                "fetched": total_fetched,
                "stored": total_accepted,
                "min_store": args.min_store,
                "sources": args.sources,
            }
        )
    )
    return 0


def cmd_top(args: argparse.Namespace) -> int:
    with storage.connect(args.db) as conn:
        rows = storage.top_opportunities(conn, limit=args.n, min_score=args.min_score)
    if args.format == "json":
        out = []
        for r in rows:
            d = dict(r)
            d["matched_signals"] = json.loads(d.get("matched_signals") or "[]")
            out.append(d)
        print(json.dumps(out, indent=2))
        return 0

    # Human-readable markdown.
    if not rows:
        print("# Concerto Demand Radar — no opportunities at this score threshold")
        return 0
    print(f"# Concerto Demand Radar — top {len(rows)} opportunities")
    print(f"_score ≥ {args.min_score}, sorted by score desc, then freshness_\n")
    for i, r in enumerate(rows, 1):
        signals = ", ".join(json.loads(r["matched_signals"]) or [])
        age_h = (int(time.time()) - r["created_ts"]) / 3600 if r["created_ts"] else None
        age = f"{age_h:.0f}h ago" if age_h is not None else "unknown age"
        print(f"## {i}. [{r['source']}] {r['title']}  — score {r['score']:.2f}")
        print(f"- url: {r['url']}")
        print(f"- author: {r['author']}  ({r['author_context']}, {age})")
        if signals:
            print(f"- signals: {signals}")
        if r["rationale"]:
            print(f"- rationale: {r['rationale']}")
        if r["body"]:
            snippet = r["body"][:280].replace("\n", " ")
            print(f"- excerpt: {snippet}{'…' if len(r['body']) > 280 else ''}")
        print()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="concerto-demand", description=__doc__)
    p.add_argument("--db", help="path to demand.db (default: backend/demand.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="fetch + score + store")
    p_scan.add_argument(
        "--sources",
        nargs="+",
        default=["hn", "reddit", "stackexchange"],
        choices=["hn", "reddit", "stackexchange"],
        help="sources to scan",
    )
    p_scan.add_argument(
        "--min-store",
        type=float,
        default=0.0,
        help="minimum score required to persist (0 keeps all for analysis)",
    )
    p_scan.add_argument(
        "--strict", action="store_true", help="exit non-zero on first source error"
    )
    p_scan.set_defaults(func=cmd_scan)

    p_rescore = sub.add_parser(
        "rescore",
        help="re-apply the scorer to all stored opportunities (no network)",
    )
    p_rescore.set_defaults(func=cmd_rescore)

    p_top = sub.add_parser("top", help="print ranked opportunities")
    p_top.add_argument("-n", type=int, default=20)
    p_top.add_argument("--min-score", type=float, default=0.2)
    p_top.add_argument("--format", choices=["md", "json"], default="md")
    p_top.set_defaults(func=cmd_top)

    p_pkg = sub.add_parser(
        "package", help="print operator hand-off packages with drafted replies"
    )
    p_pkg.add_argument("-n", type=int, default=5)
    p_pkg.add_argument("--min-score", type=float, default=0.4)
    p_pkg.add_argument("--format", choices=["md", "json"], default="md")
    p_pkg.add_argument(
        "--save-drafts",
        action="store_true",
        help="persist generated drafts back into the DB (sets status=drafted)",
    )
    p_pkg.set_defaults(func=cmd_package)

    args = p.parse_args(argv)
    return args.func(args)


def cmd_rescore(args: argparse.Namespace) -> int:
    """Re-apply the current scorer to every stored opportunity.

    Use this after editing scoring rules so the operator-facing ranking
    reflects the new logic without burning API quota on a re-fetch. Touches
    score / matched_signals / rationale only — never URL, body, or status.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("demand.rescore")
    updated = 0
    promoted = 0
    demoted = 0
    with storage.connect(args.db) as conn:
        rows = list(conn.execute(
            "SELECT dedup_key, title, body, created_ts, score FROM opportunities"
        ))
        for r in rows:
            old = r["score"]
            s = scoring.score_post(r["title"] or "", r["body"] or "", r["created_ts"] or 0)
            conn.execute(
                "UPDATE opportunities SET score=?, matched_signals=?, rationale=? WHERE dedup_key=?",
                (s.score, json.dumps(s.matched_signals), s.rationale, r["dedup_key"]),
            )
            updated += 1
            if old < 0.5 <= s.score:
                promoted += 1
            elif s.score < 0.5 <= old:
                demoted += 1
    log.info("rescored=%d promoted_above_0.5=%d demoted_below_0.5=%d", updated, promoted, demoted)
    print(json.dumps({"rescored": updated, "promoted": promoted, "demoted": demoted}))
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    with storage.connect(args.db) as conn:
        rows = storage.top_opportunities(conn, limit=args.n, min_score=args.min_score)
        opps: list[Opportunity] = []
        for r in rows:
            opps.append(
                Opportunity(
                    source=r["source"],
                    source_id=r["source_id"],
                    url=r["url"],
                    title=r["title"],
                    body=r["body"],
                    author=r["author"],
                    author_context=r["author_context"],
                    created_ts=r["created_ts"],
                    fetched_ts=r["fetched_ts"],
                    score=r["score"],
                    matched_signals=json.loads(r["matched_signals"] or "[]"),
                    rationale=r["rationale"],
                )
            )
        if args.save_drafts:
            for opp in opps:
                storage.set_draft(conn, opp.dedup_key(), drafts.draft_reply(opp))

    if args.format == "json":
        print(json.dumps([drafts.package(o) for o in opps], indent=2))
        return 0

    if not opps:
        print("# No opportunities meet the threshold.")
        return 0
    print(f"# Concerto Demand Radar — operator packages (top {len(opps)})\n")
    print(
        "Each package is **a draft for the operator to review**. The system "
        "never auto-posts. Edit the disclosure, personalize the hook, then "
        "post AS yourself.\n"
    )
    for i, opp in enumerate(opps, 1):
        pkg = drafts.package(opp)
        print(f"## {i}. [{pkg['platform']}] {pkg['title']}")
        print(f"- **url:** {pkg['url']}")
        print(f"- **author:** {pkg['author']}  ({pkg['author_context']})")
        print(f"- **score:** {pkg['score']:.2f}  — angle: `{pkg['angle']}`")
        print(f"- **why relevant:** {pkg['why_relevant']}")
        print(f"- **signals:** {', '.join(pkg['matched_signals'])}")
        print()
        print("**Draft reply** (edit before posting):")
        print()
        print("```")
        print(pkg["draft_reply"].rstrip())
        print("```")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

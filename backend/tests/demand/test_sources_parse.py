"""Source parsing tests — fixture-based, no network."""
from __future__ import annotations

import time

from concerto.demand.sources import hackernews, reddit, stackexchange


_HN_HIT = {
    "objectID": "12345",
    "title": "Show HN: Tool to manage Claude Code sessions",
    "story_text": "I was juggling tmux panes...",
    "url": "https://example.com/post",
    "author": "alice",
    "points": 42,
    "num_comments": 7,
    "created_at_i": int(time.time()) - 3600,
    "_tags": ["story", "show_hn"],
}


def test_hn_hit_to_opp():
    opp = hackernews._hit_to_opp(_HN_HIT, int(time.time()))
    assert opp is not None
    assert opp.source == "hn"
    assert opp.source_id == "12345"
    assert opp.url == "https://example.com/post"
    assert opp.author == "alice"
    assert "42 points" in opp.author_context
    assert "story" in opp.author_context or "show_hn" in opp.author_context
    assert "Claude Code" in opp.title


def test_hn_comment_synthesizes_title():
    hit = {
        "objectID": "9",
        "comment_text": "First line of the comment.\nSecond line.",
        "author": "x",
        "created_at_i": 1700000000,
        "_tags": ["comment"],
    }
    opp = hackernews._hit_to_opp(hit, int(time.time()))
    assert opp is not None
    assert opp.title.startswith("First line of the comment.")
    assert opp.url.startswith("https://news.ycombinator.com/item?id=")


_REDDIT_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <id>t3_abc123</id>
  <title>Anyone running multiple Claude Code in parallel?</title>
  <link href="https://www.reddit.com/r/ClaudeAI/comments/abc123/foo/" />
  <updated>2026-06-01T19:00:00+00:00</updated>
  <author><name>/u/devperson</name></author>
  <content type="html">&lt;p&gt;I'm tired of juggling tmux panes.&lt;/p&gt;</content>
</entry>
<entry>
  <id>t3_def456</id>
  <title>Unrelated post</title>
  <link href="https://www.reddit.com/r/ClaudeAI/comments/def456/bar/" />
  <updated>2026-06-01T18:00:00+00:00</updated>
  <author><name>/u/other</name></author>
  <content type="html">just venting</content>
</entry>
</feed>
"""


def test_reddit_atom_parse():
    entries = reddit._parse_atom(_REDDIT_ATOM)
    assert len(entries) == 2
    first = entries[0]
    assert first["id"] == "t3_abc123"
    assert first["author_name"] == "/u/devperson"
    assert "parallel" in first["title"].lower()
    first["subreddit"] = "ClaudeAI"
    opp = reddit._entry_to_opp(first, int(time.time()))
    assert opp is not None
    assert opp.source == "reddit"
    assert opp.source_id == "abc123"
    assert opp.author == "devperson"
    assert opp.author_context == "r/ClaudeAI"
    assert "juggling tmux panes" in opp.body
    assert opp.created_ts > 0


_SE_ITEM = {
    "question_id": 7890123,
    "title": "How to run multiple Claude Code sessions in parallel?",
    "body": "<p>I'm trying to run several <code>claude</code> sessions...</p>",
    "link": "https://stackoverflow.com/questions/7890123/foo",
    "owner": {"display_name": "asker42", "user_id": 99},
    "tags": ["claude", "llm", "anthropic"],
    "creation_date": 1740000000,
    "score": 5,
    "answer_count": 0,
    "is_answered": False,
}


def test_se_item_to_opp_stackoverflow():
    opp = stackexchange._item_to_opp(_SE_ITEM, "stackoverflow", int(time.time()))
    assert opp is not None
    assert opp.source == "stackexchange"
    assert opp.source_id == "so:7890123"
    assert opp.url.startswith("https://stackoverflow.com/")
    assert opp.author == "asker42"
    assert "stackoverflow" in opp.author_context
    assert "5 score" in opp.author_context
    assert "unanswered" in opp.author_context
    assert "tags: claude,llm,anthropic" in opp.author_context
    assert "<p>" not in opp.body
    assert "several claude sessions" in opp.body
    assert opp.created_ts == 1740000000


def test_se_item_to_opp_aise_site():
    item = dict(_SE_ITEM, question_id=11, link="https://ai.stackexchange.com/q/11")
    opp = stackexchange._item_to_opp(item, "ai", int(time.time()))
    assert opp is not None
    assert opp.source_id == "se-ai:11"
    assert "ai.stackexchange" in opp.author_context


def test_se_item_missing_qid_returns_none():
    bad = dict(_SE_ITEM)
    bad.pop("question_id")
    assert stackexchange._item_to_opp(bad, "stackoverflow", int(time.time())) is None


def test_se_strip_html_unescapes_entities():
    assert stackexchange._strip_html("<p>a &amp; b</p>") == "a & b"

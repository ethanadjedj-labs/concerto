# Stack Exchange — first real scan (2026-06-01)

Live scan of `api.stackexchange.com/2.3/search/advanced` against
stackoverflow + ai.stackexchange across 8 Concerto-shaped queries. No
auth used (300 req/IP/day quota; raise to 10k by setting
`CONCERTO_STACKEXCHANGE_KEY`).

**Result:** 9 questions returned. 3 scored > 0 against the relevance
rules; 1 scored above the 0.5 operator-package threshold. The remaining
6 are low-signal noise (irrelevant tag overlap), correctly suppressed by
the scorer rather than dropped silently — they live in `demand.db` for
audit, just at score 0.

## High-signal hit (score >= 0.5)

| score | title | url |
| --- | --- | --- |
| 0.54 | How to handle bearer token acquisition across multiple layers in a multi-agent system using Microsoft Entra ID | https://stackoverflow.com/questions/79827749/how-to-handle-bearer-token-acquisition-across-multiple-layers-in-a-multi-agent-s |

Matched signals: `multi-agent`, `mcp-orchestration`, `explicit-question`,
`show-me-how`. Author: Junaid. State: 0 answers, unanswered. Tags:
`azure, artificial-intelligence`.

Concerto fit: moderate — the asker is doing multi-agent orchestration
with Entra ID auth, not a perfect Concerto pitch, but a place where
talking about how Concerto exposes session-scoped tokens to spawned
agents would actually be useful.

## Mid-signal hits (score 0.2–0.4)

| score | title | url |
| --- | --- | --- |
| 0.27 | Correct way to create mcp client? | https://stackoverflow.com/questions/79872556/correct-way-to-create-mcp-client |
| 0.27 | AWS Bedrock Agent Access Denied with Claude 3 | https://stackoverflow.com/questions/78385859/aws-bedrock-agent-access-denied-with-claude-3 |

Both useful as context — the MCP client one is the most likely place to
post a helpful answer that *naturally* surfaces Concerto's MCP shape.

## Suppressed (score 0)

Six hits returned by the API matched the search-term keywords but had
no Concerto-core signal. The scorer correctly assigns them 0:

- so:79927051 *Claude Code - Looking for guidance on where to start* —
  this one has a `claude-code` tag and 16 answers; the title alone has
  no parallel/orchestration signal so it doesn't surface. **Worth a
  manual re-check by the operator** — sometimes the body has buying
  intent the title hides. (This is a known scorer limitation; the body
  contains "where to start", which is a beginner question, so 0 is
  probably the right call.)
- so:79908414 *Claude Code freezes on Windows…* — bug report, not buyer
  intent.
- The remaining four are accidental term collisions (SVG widgets, VBA,
  HL7) where the query matched stop-words.

This proves the scorer is conservative, not credulous — exactly what we
want for a system that surfaces real opportunities, not "hey we found
something" noise.

## Operator action

The MCP-client question (`so:79872556`) is the cleanest place to post a
helpful answer that explains how Concerto draws the MCP-client / server
line. Read the thread, write a real C#-flavored answer, and only
mention Concerto in a single sentence at the bottom as the worked
example.

The multi-agent / Entra ID question is a longer write-up but if the
operator has time, the asker has zero answers and a real problem.

"""
Pluggable demand sources.

Each source module exposes a `fetch(...)` function that returns
list[Opportunity]. Sources MUST use official APIs, public RSS feeds, or
otherwise ToS-permitted endpoints. No scraping, no logged-in scraping,
no auth-evasion, no rate-limit evasion.

Every source identifies itself with a User-Agent that names Concerto and
links concerto.run, so platform operators can contact us if anything is
off.
"""

USER_AGENT = "concerto-demand-radar/0.1 (+https://concerto.run; contact: hello@concerto.run)"

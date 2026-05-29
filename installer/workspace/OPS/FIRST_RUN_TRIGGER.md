# First-run welcome trigger

The runtime container creates `/opt/concerto-workspace/.first_run` once,
when the GitHub OAuth callback completes for the first time and a home-base
repo has been provisioned. The file contains one line: the user's GitHub
login (e.g. `ethanadjedj`).

SESSION_RULES.md instructs spawned Claude Code agents to detect this file
and, if present, deliver a one-time welcome message before doing anything
else, then delete the marker.

Lifecycle:
1. Backend OAuth callback creates the `concerto` repo on the user's account
   and stores the full_name + login in the buyer row.
2. Backend exposes `concerto_repo` and `github_login` in the
   `/git-credentials` JSON response.
3. Container entrypoint, on the FIRST poll cycle where the response contains
   a non-empty `concerto_repo`, writes:
     - `/home/concerto/.concerto_home_repo` (full_name, e.g. `octocat/concerto`)
     - `/opt/concerto-workspace/.first_run` (one line: login)
   ONLY IF `.concerto_home_repo` did not exist before this poll cycle. If it
   already exists, the marker is NOT recreated (idempotent -- protects from
   welcome-spam on container restart).
4. The first Claude Code session deletes `/opt/concerto-workspace/.first_run`
   after delivering the welcome.

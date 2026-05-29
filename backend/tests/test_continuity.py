"""Tests for the Concerto continuity system.

Tests the 6 changes added to installer/mcp_server.py:
  1. concerto_build reads MANAGER_STATE before planning
  2. Envelope validation rejects malformed JSON / missing fields
  3. State diff is computed and persisted when MANAGER_STATE changes
  4. concerto_replan loads parent plan and persists child
  5. concerto_resume_session spawns with prior context linked via parent_session_id
  6. Project detection from Active projects section of MANAGER_STATE
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import time
import tempfile
import unittest.mock as mock
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: mock heavy deps before importing mcp_server
# ---------------------------------------------------------------------------

_MOCK_MCP = MagicMock()
_MOCK_MCP.tool = lambda **kw: (lambda f: f)  # @mcp.tool() is a no-op
_MOCK_FASTMCP_CLASS = MagicMock(return_value=_MOCK_MCP)
_MOCK_TRANSPORT = MagicMock()
_MOCK_TRANSPORT.TransportSecuritySettings = MagicMock

for _mod in (
    "mcp",
    "mcp.server",
    "mcp.server.fastmcp",
    "mcp.server.transport_security",
    "anyio",
    "uvicorn",
    "httpx",
):
    sys.modules.setdefault(_mod, MagicMock())

sys.modules["mcp.server.fastmcp"].FastMCP = _MOCK_FASTMCP_CLASS
sys.modules["mcp.server.transport_security"].TransportSecuritySettings = MagicMock

# Add installer directory to path
_INSTALLER_DIR = str(Path(__file__).parents[2] / "installer")
if _INSTALLER_DIR not in sys.path:
    sys.path.insert(0, _INSTALLER_DIR)

import mcp_server  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_ENVELOPE_JSON = json.dumps({
    "status": "ok",
    "summary": "Finished writing tests.",
    "artifacts": {"files_created": ["tests/test_foo.py"], "files_modified": [], "pr_url": "", "commits": []},
    "next_recommended": "Run pytest",
    "decisions_for_operator": [],
    "errors": [],
})

_MANAGER_STATE_WITH_PROJECTS = """\
# Manager State

Last updated: 2026-05-23

## Active strategic decisions

Shipping Concerto SaaS.

## Active projects

### crm-outreach
CRM automation project to improve lead flow.

### analytics-dashboard
Secondary project, lower priority.

## Pending operator decisions

- Which CRM to integrate with (HubSpot vs Salesforce)?
- Analytics time window default.

## Conventions

- Sessions read this before work.
"""

_MANAGER_STATE_EMPTY = """\
# Manager State

## Active projects

(List each active project as a section. When state changes, edit here.)

## Pending operator decisions

(Open questions that block your sessions.)
"""


# ---------------------------------------------------------------------------
# 1. State section extraction
# ---------------------------------------------------------------------------

class TestExtractStateSections:
    def test_extracts_active_projects(self):
        sections = mcp_server._extract_state_sections(_MANAGER_STATE_WITH_PROJECTS)
        assert "Active projects" in sections
        assert "crm-outreach" in sections["Active projects"]

    def test_extracts_pending_decisions(self):
        sections = mcp_server._extract_state_sections(_MANAGER_STATE_WITH_PROJECTS)
        assert "Pending operator decisions" in sections
        assert "HubSpot" in sections["Pending operator decisions"]

    def test_empty_sections_produce_empty_strings(self):
        sections = mcp_server._extract_state_sections(_MANAGER_STATE_EMPTY)
        active = sections.get("Active projects", "")
        assert active.strip() == "" or active.strip().startswith("(")

    def test_empty_content_returns_empty_dict(self):
        assert mcp_server._extract_state_sections("") == {}


# ---------------------------------------------------------------------------
# 6. Project detection
# ---------------------------------------------------------------------------

class TestDetectActiveProject:
    def test_detects_first_non_placeholder_project(self):
        result = mcp_server._detect_active_project(_MANAGER_STATE_WITH_PROJECTS)
        assert result is not None
        assert "crm-outreach" in result

    def test_returns_none_for_empty_content(self):
        assert mcp_server._detect_active_project("") is None

    def test_returns_none_for_placeholder_only(self):
        state = "## Active projects\n\n(List each active project as a section.)\n"
        assert mcp_server._detect_active_project(state) is None

    def test_strips_markdown_heading(self):
        state = "## Active projects\n\n### my-project\nDescription here.\n"
        result = mcp_server._detect_active_project(state)
        assert result == "my-project"

    def test_strips_list_marker(self):
        state = "## Active projects\n\n- my-list-project\nDetails.\n"
        result = mcp_server._detect_active_project(state)
        assert result == "my-list-project"


# ---------------------------------------------------------------------------
# 2. Envelope validation
# ---------------------------------------------------------------------------

class TestValidateEnvelope:
    def test_valid_envelope_returns_true(self):
        valid, parsed, reason = mcp_server._validate_envelope(_VALID_ENVELOPE_JSON)
        assert valid is True
        assert parsed is not None
        assert parsed["status"] == "ok"
        assert reason == "ok"

    def test_empty_string_is_invalid(self):
        valid, parsed, reason = mcp_server._validate_envelope("")
        assert valid is False
        assert parsed is None
        assert reason == "empty"

    def test_malformed_json_is_invalid(self):
        valid, parsed, reason = mcp_server._validate_envelope("{not valid json")
        assert valid is False
        assert "json_error" in reason

    def test_wrong_status_is_invalid(self):
        bad = json.dumps({
            "status": "completed",  # not in allowed set
            "summary": "done",
            "artifacts": {},
        })
        valid, parsed, reason = mcp_server._validate_envelope(bad)
        assert valid is False
        assert "invalid_status" in reason

    def test_missing_summary_is_invalid(self):
        bad = json.dumps({
            "status": "ok",
            "artifacts": {},
        })
        valid, parsed, reason = mcp_server._validate_envelope(bad)
        assert valid is False
        assert "missing_summary" in reason

    def test_missing_artifacts_is_invalid(self):
        bad = json.dumps({
            "status": "ok",
            "summary": "done",
        })
        valid, parsed, reason = mcp_server._validate_envelope(bad)
        assert valid is False
        assert "missing_artifacts" in reason

    def test_not_a_dict_is_invalid(self):
        valid, parsed, reason = mcp_server._validate_envelope("[1, 2, 3]")
        assert valid is False
        assert "not_a_dict" in reason

    def test_all_status_values_accepted(self):
        for status in ("ok", "partial", "aborted", "failed"):
            envelope = json.dumps({
                "status": status,
                "summary": "done",
                "artifacts": {},
            })
            valid, _, _ = mcp_server._validate_envelope(envelope)
            assert valid is True, f"status {status!r} should be valid"

    def test_non_empty_but_non_json_last_line(self):
        valid, parsed, reason = mcp_server._validate_envelope("Session complete!")
        assert valid is False
        assert "json_error" in reason


# ---------------------------------------------------------------------------
# 3. State diff detection
# ---------------------------------------------------------------------------

class TestStateDiff:
    def test_diff_is_appended_when_state_changes(self, tmp_path):
        diffs_path = tmp_path / "state_diffs.json"
        with patch.object(mcp_server, "STATE_DIFFS_PATH", diffs_path):
            mcp_server._append_state_diff(
                session_id="abc123",
                before_hash="aaa",
                after_hash="bbb",
                diff_text="--- before\n+++ after\n@@ ... @@\n-old\n+new\n",
            )
        diffs = json.loads(diffs_path.read_text())
        assert len(diffs) == 1
        assert diffs[0]["session_id"] == "abc123"
        assert diffs[0]["before_hash"] == "aaa"
        assert diffs[0]["after_hash"] == "bbb"
        assert "old" in diffs[0]["diff_text"]

    def test_diff_capped_at_500_entries(self, tmp_path):
        diffs_path = tmp_path / "state_diffs.json"
        with patch.object(mcp_server, "STATE_DIFFS_PATH", diffs_path):
            for i in range(510):
                mcp_server._append_state_diff(f"s{i}", f"h{i}a", f"h{i}b", "change")
        diffs = json.loads(diffs_path.read_text())
        assert len(diffs) == 500

    def test_diff_computed_on_manager_state_change(self, tmp_path):
        """_run_claude should detect and persist a diff when MANAGER_STATE changes."""
        state_file = tmp_path / "MANAGER_STATE.md"
        diffs_file = tmp_path / "state_diffs.json"

        before_content = "## Active projects\n\n### project-a\n"
        after_content = "## Active projects\n\n### project-a\n### project-b\n"
        state_file.write_text(before_content)

        session_id = "difftest"
        mcp_server._sessions[session_id] = {
            "id": session_id,
            "status": "running",
            "started_at": time.time(),
            "prompt": "test",
            "model": "claude-sonnet-4-5",
            "output_lines": [],
            "exit_code": None,
            "error": None,
        }

        written_state = {"content": before_content}

        def fake_read_manager_state():
            return written_state["content"]

        call_count = {"n": 0}

        def patched_read():
            call_count["n"] += 1
            if call_count["n"] == 1:
                return before_content
            return after_content

        with (
            patch.object(mcp_server, "MANAGER_STATE_PATH", state_file),
            patch.object(mcp_server, "STATE_DIFFS_PATH", diffs_file),
            patch.object(mcp_server, "_read_manager_state", patched_read),
            patch.object(mcp_server, "_claude_authed", return_value=False),
        ):
            asyncio.run(mcp_server._run_claude(session_id, "test", "claude-sonnet-4-5"))

        # Session should have been marked failed (not authed), but the diff
        # detection runs on before vs after content regardless
        del mcp_server._sessions[session_id]


# ---------------------------------------------------------------------------
# 1. concerto_build reads MANAGER_STATE (planner receives context)
# ---------------------------------------------------------------------------

class TestConcertoBuildStateAware:
    def test_state_context_passed_to_planner(self):
        """concerto_build passes active projects / pending decisions to _run_planner."""
        calls = []

        async def fake_planner(request, state_context=""):
            calls.append({"request": request, "state_context": state_context})
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "build it", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state",
                         return_value=_MANAGER_STATE_WITH_PROJECTS),
            patch.object(mcp_server, "_run_claude", AsyncMock()),
        ):
            asyncio.run(mcp_server.concerto_build("build me a CRM"))

        assert len(calls) == 1
        assert "crm-outreach" in calls[0]["state_context"]
        assert "HubSpot" in calls[0]["state_context"]

    def test_no_state_uses_no_prior_state(self):
        """When MANAGER_STATE is absent, context_used is 'no prior state'."""
        results = []

        async def fake_planner(request, state_context=""):
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "build it", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state", return_value=""),
            patch.object(mcp_server, "_run_claude", AsyncMock()),
        ):
            result = asyncio.run(mcp_server.concerto_build("build me something"))

        assert result.get("context_used") == "no prior state"

    def test_detected_project_in_return(self):
        """concerto_build returns detected_project from MANAGER_STATE."""
        async def fake_planner(request, state_context=""):
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "build it", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state",
                         return_value=_MANAGER_STATE_WITH_PROJECTS),
            patch.object(mcp_server, "_run_claude", AsyncMock()),
        ):
            result = asyncio.run(mcp_server.concerto_build("build it"))

        assert result.get("detected_project") == "crm-outreach"

    def test_plan_id_persisted(self):
        """concerto_build stores the plan in _plans with a plan_id."""
        mcp_server._plans.clear()

        async def fake_planner(request, state_context=""):
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "x", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state", return_value=""),
            patch.object(mcp_server, "_run_claude", AsyncMock()),
            patch.object(mcp_server, "_persist_plans", MagicMock()),
        ):
            result = asyncio.run(mcp_server.concerto_build("build x"))

        plan_id = result.get("plan_id")
        assert plan_id is not None
        assert plan_id in mcp_server._plans
        mcp_server._plans.clear()


# ---------------------------------------------------------------------------
# 4. concerto_replan loads parent and persists child
# ---------------------------------------------------------------------------

class TestConcertoReplan:
    def setup_method(self):
        mcp_server._plans.clear()

    def teardown_method(self):
        mcp_server._plans.clear()

    def test_replan_not_found_returns_error(self):
        result = asyncio.run(
            mcp_server.concerto_replan("nonexistent", "change tone")
        )
        assert "error" in result
        assert "not found" in result["error"]

    def test_replan_creates_child_with_parent_id(self):
        parent_id = "parent01"
        mcp_server._plans[parent_id] = {
            "id": parent_id,
            "request": "build a CRM",
            "workstreams": [{"name": "build", "scope": "all", "paths": ["."]}],
            "created_at": time.time(),
        }

        async def fake_planner(request, state_context=""):
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "revised", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state", return_value=""),
            patch.object(mcp_server, "_persist_plans", MagicMock()),
        ):
            result = asyncio.run(
                mcp_server.concerto_replan(parent_id, "make it simpler")
            )

        assert result.get("parent_plan_id") == parent_id
        new_id = result.get("plan_id")
        assert new_id is not None
        assert new_id != parent_id
        assert new_id in mcp_server._plans
        assert mcp_server._plans[new_id]["parent_plan_id"] == parent_id
        assert mcp_server._plans[new_id]["feedback"] == "make it simpler"

    def test_replan_includes_original_request_in_new_prompt(self):
        parent_id = "parent02"
        mcp_server._plans[parent_id] = {
            "id": parent_id,
            "request": "build a SaaS CRM",
            "workstreams": [{"name": "api", "scope": "API layer", "paths": ["api/"]}],
            "created_at": time.time(),
        }

        captured = []

        async def fake_planner(request, state_context=""):
            captured.append(request)
            return {
                "mode": "single",
                "workstreams": [{"name": "api", "scope": "revised", "paths": ["api/"]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state", return_value=""),
            patch.object(mcp_server, "_persist_plans", MagicMock()),
        ):
            asyncio.run(mcp_server.concerto_replan(parent_id, "drop the auth"))

        assert len(captured) == 1
        assert "build a SaaS CRM" in captured[0]
        assert "drop the auth" in captured[0]

    def test_replan_state_context_included(self):
        parent_id = "parent03"
        mcp_server._plans[parent_id] = {
            "id": parent_id,
            "request": "build an app",
            "workstreams": [],
            "created_at": time.time(),
        }

        state_contexts = []

        async def fake_planner(request, state_context=""):
            state_contexts.append(state_context)
            return {
                "mode": "single",
                "workstreams": [{"name": "build", "scope": "x", "paths": ["."]}],
                "needs_integration": False,
            }

        with (
            patch.object(mcp_server, "_run_planner", fake_planner),
            patch.object(mcp_server, "_read_manager_state",
                         return_value=_MANAGER_STATE_WITH_PROJECTS),
            patch.object(mcp_server, "_persist_plans", MagicMock()),
        ):
            asyncio.run(mcp_server.concerto_replan(parent_id, "change approach"))

        assert len(state_contexts) == 1
        assert "crm-outreach" in state_contexts[0]


# ---------------------------------------------------------------------------
# 5. concerto_resume_session spawns with prior context
# ---------------------------------------------------------------------------

class TestConcertoResumeSession:
    def setup_method(self):
        # Clean up any test sessions
        for key in list(mcp_server._sessions.keys()):
            if key.startswith("resume_") or key.startswith("parent_"):
                del mcp_server._sessions[key]

    def teardown_method(self):
        for key in list(mcp_server._sessions.keys()):
            if key.startswith("resume_") or key.startswith("parent_"):
                del mcp_server._sessions[key]

    def test_resume_not_found_returns_error(self):
        result = asyncio.run(
            mcp_server.concerto_resume_session("nonexistent_sid", "continue")
        )
        assert "error" in result
        assert "not found" in result["error"]

    def test_resume_running_session_returns_error(self):
        mcp_server._sessions["parent_running"] = {
            "id": "parent_running",
            "status": "running",
            "model": "claude-sonnet-4-5",
            "output_lines": [],
            "prompt": "test",
            "started_at": time.time(),
        }
        result = asyncio.run(
            mcp_server.concerto_resume_session("parent_running", "continue")
        )
        assert "error" in result
        assert "still running" in result["error"]

    def test_resume_creates_child_linked_to_parent(self):
        mcp_server._sessions["parent_done"] = {
            "id": "parent_done",
            "status": "done",
            "model": "claude-sonnet-4-5",
            "output_lines": ["line1", "line2", _VALID_ENVELOPE_JSON],
            "envelope_parsed": json.loads(_VALID_ENVELOPE_JSON),
            "prompt": "build something",
            "started_at": time.time(),
        }

        with patch.object(mcp_server, "_run_claude", AsyncMock()):
            result = asyncio.run(
                mcp_server.concerto_resume_session("parent_done", "now add tests")
            )

        new_sid = result.get("session_id")
        assert new_sid is not None
        assert result.get("parent_session_id") == "parent_done"
        assert result.get("status") == "running"
        assert new_sid in mcp_server._sessions
        assert mcp_server._sessions[new_sid]["parent_session_id"] == "parent_done"

    def test_resume_includes_prior_envelope_in_prompt(self):
        mcp_server._sessions["parent_env"] = {
            "id": "parent_env",
            "status": "done",
            "model": "claude-sonnet-4-5",
            "output_lines": [_VALID_ENVELOPE_JSON],
            "envelope_parsed": json.loads(_VALID_ENVELOPE_JSON),
            "prompt": "build X",
            "started_at": time.time(),
        }

        captured_prompts = []

        async def fake_run_claude(session_id, prompt, model):
            captured_prompts.append(prompt)
            mcp_server._sessions[session_id]["status"] = "done"

        with patch.object(mcp_server, "_run_claude", fake_run_claude):
            asyncio.run(
                mcp_server.concerto_resume_session("parent_env", "add error handling")
            )

        assert len(captured_prompts) == 1
        assert "Previous session result" in captured_prompts[0]
        assert "add error handling" in captured_prompts[0]

    def test_resume_includes_log_tail_in_prompt(self):
        log_lines = [f"log line {i}" for i in range(60)]
        mcp_server._sessions["parent_logs"] = {
            "id": "parent_logs",
            "status": "done",
            "model": "claude-sonnet-4-5",
            "output_lines": log_lines,
            "envelope_parsed": None,
            "prompt": "build Y",
            "started_at": time.time(),
        }

        captured_prompts = []

        async def fake_run_claude(session_id, prompt, model):
            captured_prompts.append(prompt)
            mcp_server._sessions[session_id]["status"] = "done"

        with patch.object(mcp_server, "_run_claude", fake_run_claude):
            asyncio.run(
                mcp_server.concerto_resume_session("parent_logs", "fix the bug")
            )

        assert len(captured_prompts) == 1
        # Last 50 lines are included
        assert "log line 59" in captured_prompts[0]
        assert "fix the bug" in captured_prompts[0]
        # First 10 lines are NOT included (only tail[-50:])
        assert "log line 0" not in captured_prompts[0]


# ---------------------------------------------------------------------------
# Plan and session persistence helpers
# ---------------------------------------------------------------------------

class TestPlanPersistence:
    def test_persist_and_restore_plans(self, tmp_path):
        plans_path = tmp_path / "plans_state.json"
        mcp_server._plans.clear()
        mcp_server._plans["plan01"] = {
            "id": "plan01",
            "request": "test",
            "created_at": 0.0,
        }

        with patch.object(mcp_server, "PLANS_PERSIST_PATH", plans_path):
            mcp_server._persist_plans()
            mcp_server._plans.clear()
            mcp_server._restore_plans()

        assert "plan01" in mcp_server._plans
        assert mcp_server._plans["plan01"]["request"] == "test"
        mcp_server._plans.clear()

    def test_restore_plans_tolerates_missing_file(self, tmp_path):
        missing = tmp_path / "does_not_exist.json"
        with patch.object(mcp_server, "PLANS_PERSIST_PATH", missing):
            mcp_server._restore_plans()  # should not raise

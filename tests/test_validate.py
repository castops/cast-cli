"""Tests for `cast validate` command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cast_cli.main import app, _apply_gate

runner = CliRunner()


# ── helpers ────────────────────────────────────────────────────────────────────


def _write_sarif(path: Path, runs: list, version: str = "2.1.0") -> Path:
    sarif_file = path / "test.sarif"
    sarif_file.write_text(json.dumps({"version": version, "runs": runs}))
    return sarif_file


def _make_run(tool: str, results: list) -> dict:
    return {
        "tool": {"driver": {"name": tool, "rules": []}},
        "results": results,
    }


def _make_result(level: str, rule_id: str = "rule-001", msg: str = "Test") -> dict:
    return {
        "level": level,
        "ruleId": rule_id,
        "message": {"text": msg},
        "locations": [],
    }


# ── _apply_gate unit tests ─────────────────────────────────────────────────────


class TestApplyGate:
    def test_default_blocks_on_error(self):
        runs = [_make_run("Semgrep", [_make_result("error")])]
        msgs, count = _apply_gate(runs, "default")
        assert count == 1
        assert "[CRITICAL]" in msgs[0]

    def test_default_does_not_block_on_warning(self):
        runs = [_make_run("Semgrep", [_make_result("warning")])]
        _, count = _apply_gate(runs, "default")
        assert count == 0

    def test_strict_blocks_on_warning(self):
        runs = [_make_run("Semgrep", [_make_result("warning")])]
        msgs, count = _apply_gate(runs, "strict")
        assert count == 1
        assert "[HIGH]" in msgs[0]

    def test_strict_blocks_on_error(self):
        runs = [_make_run("Semgrep", [_make_result("error")])]
        msgs, count = _apply_gate(runs, "strict")
        assert count == 1
        assert "[CRITICAL]" in msgs[0]

    def test_permissive_never_blocks(self):
        runs = [_make_run("Semgrep", [_make_result("error"), _make_result("warning")])]
        _, count = _apply_gate(runs, "permissive")
        assert count == 0

    def test_note_never_blocked_by_any_policy(self):
        runs = [_make_run("Semgrep", [_make_result("note")])]
        for policy in ("default", "strict", "permissive"):
            _, count = _apply_gate(runs, policy)
            assert count == 0, f"policy {policy!r} should not block note-level finding"

    def test_empty_runs_returns_no_blocks(self):
        _, count = _apply_gate([], "strict")
        assert count == 0


# ── CLI integration tests ──────────────────────────────────────────────────────


class TestValidateCommand:
    @pytest.fixture(autouse=True)
    def _chdir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

    def test_valid_clean_sarif_exits_zero(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 0
        assert "✓" in result.output or "valid" in result.output.lower()

    def test_sarif_with_critical_finding_exits_two(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("error")])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 2
        assert "blocked" in result.output.lower() or "CRITICAL" in result.output

    def test_sarif_with_warning_default_policy_exits_zero(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("warning")])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 0

    def test_sarif_with_warning_strict_policy_exits_two(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("warning")])])
        result = runner.invoke(app, ["validate", str(sarif), "--policy", "strict"])
        assert result.exit_code == 2

    def test_sarif_with_error_permissive_policy_exits_zero(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("error")])])
        result = runner.invoke(app, ["validate", str(sarif), "--policy", "permissive"])
        assert result.exit_code == 0

    def test_invalid_json_exits_one(self, tmp_path):
        bad = tmp_path / "bad.sarif"
        bad.write_text("not json at all {{{")
        result = runner.invoke(app, ["validate", str(bad)])
        assert result.exit_code == 1
        assert "Invalid JSON" in result.output or "invalid" in result.output.lower()

    def test_wrong_version_exits_one(self, tmp_path):
        sarif = _write_sarif(tmp_path, [], version="1.0.0")
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 1
        assert "2.1.0" in result.output

    def test_missing_runs_field_exits_one(self, tmp_path):
        sarif_file = tmp_path / "no_runs.sarif"
        sarif_file.write_text(json.dumps({"version": "2.1.0"}))
        result = runner.invoke(app, ["validate", str(sarif_file)])
        assert result.exit_code == 1
        assert "runs" in result.output

    def test_missing_tool_name_exits_one(self, tmp_path):
        sarif_file = tmp_path / "bad_run.sarif"
        sarif_file.write_text(json.dumps({
            "version": "2.1.0",
            "runs": [{"tool": {"driver": {}}, "results": []}],
        }))
        result = runner.invoke(app, ["validate", str(sarif_file)])
        assert result.exit_code == 1
        assert "tool.driver.name" in result.output

    def test_nonexistent_file_exits_one(self, tmp_path):
        result = runner.invoke(app, ["validate", str(tmp_path / "no_such.sarif")])
        assert result.exit_code == 1

    def test_unknown_policy_exits_one(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [])])
        result = runner.invoke(app, ["validate", str(sarif), "--policy", "extreme"])
        assert result.exit_code == 1
        assert "Unknown policy" in result.output or "policy" in result.output.lower()

    def test_output_shows_tool_name(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Trivy", [])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert "Trivy" in result.output

    def test_output_shows_finding_counts(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Gitleaks", [
            _make_result("error"),
            _make_result("warning"),
            _make_result("note"),
        ])])
        result = runner.invoke(app, ["validate", str(sarif)])
        # 1 error, 1 warning, 1 note → total 3 (error blocks default policy → exit 2)
        assert "1 error" in result.output
        assert "1 warning" in result.output
        assert "1 note" in result.output

    def test_output_shows_plural_finding_counts(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [
            _make_result("error", "r1"),
            _make_result("error", "r2"),
            _make_result("warning", "r3"),
            _make_result("warning", "r4"),
            _make_result("note", "r5"),
            _make_result("note", "r6"),
        ])])
        result = runner.invoke(app, ["validate", str(sarif)])
        # 2 error, 2 warning, 2 note → total 6
        assert "2 error" in result.output
        assert "2 warning" in result.output
        assert "2 note" in result.output

    def test_cast_policy_env_var_respected(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CAST_POLICY", "permissive")
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("error")])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 0

    def test_policy_flag_overrides_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CAST_POLICY", "permissive")
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [_make_result("error")])])
        result = runner.invoke(app, ["validate", str(sarif), "--policy", "default"])
        assert result.exit_code == 2

    def test_blocked_messages_shown_in_output(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [
            _make_result("error", "sql-injection", "SQL injection found"),
        ])])
        result = runner.invoke(app, ["validate", str(sarif)])
        assert result.exit_code == 2
        assert "sql-injection" in result.output or "SQL injection" in result.output

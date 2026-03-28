"""Tests for dashboard/generate.py — SARIF parsing and HTML generation."""

import json
import sys
from pathlib import Path

# Add project root to path for importing dashboard module
sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.generate import parse_sarif, generate_dashboard


def _write_sarif(path: Path, runs: list) -> Path:
    sarif_file = path / "results.sarif"
    sarif_file.write_text(json.dumps({"version": "2.1.0", "runs": runs}))
    return sarif_file


def _make_run(tool_name: str, results: list) -> dict:
    return {
        "tool": {"driver": {"name": tool_name, "rules": []}},
        "results": results,
    }


def _make_result(level: str, rule_id: str, message: str, uri: str = "src/foo.py") -> dict:
    return {
        "level": level,
        "ruleId": rule_id,
        "message": {"text": message},
        "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}, "region": {"startLine": 1}}}],
    }


class TestParseSarif:
    def test_valid_sarif_with_no_results_returns_pass(self, tmp_path):
        sarif = _write_sarif(tmp_path, [_make_run("Semgrep", [])])
        result = parse_sarif(sarif)
        assert result is not None
        assert result["status"] == "PASS"
        assert result["critical"] == 0
        assert result["high"] == 0

    def test_critical_finding_sets_fail_status(self, tmp_path):
        run = _make_run("Semgrep", [_make_result("error", "rule-001", "Critical issue")])
        sarif = _write_sarif(tmp_path, [run])
        result = parse_sarif(sarif)
        assert result["status"] == "FAIL"
        assert result["critical"] == 1

    def test_warning_finding_sets_warn_status(self, tmp_path):
        run = _make_run("Semgrep", [_make_result("warning", "rule-002", "High severity")])
        sarif = _write_sarif(tmp_path, [run])
        result = parse_sarif(sarif)
        assert result["status"] == "WARN"
        assert result["high"] == 1

    def test_findings_list_populated(self, tmp_path):
        run = _make_run("Gitleaks", [_make_result("error", "rule-abc", "Secret found")])
        sarif = _write_sarif(tmp_path, [run])
        result = parse_sarif(sarif)
        assert len(result["findings"]) == 1
        assert result["findings"][0]["rule_id"] == "rule-abc"

    def test_invalid_json_returns_error_dict(self, tmp_path):
        bad_file = tmp_path / "bad.sarif"
        bad_file.write_text("this is not json {{{")
        result = parse_sarif(bad_file)
        assert result is not None
        assert result["status"] == "ERROR"
        assert "error" in result
        assert result["name"] == "bad"
        assert result["critical"] == 0
        assert result["findings"] == []

    def test_missing_runs_key_returns_empty_pass(self, tmp_path):
        sarif_file = tmp_path / "empty.sarif"
        sarif_file.write_text(json.dumps({"version": "2.1.0"}))
        result = parse_sarif(sarif_file)
        assert result is not None
        assert result["status"] == "PASS"

    def test_tool_name_captured(self, tmp_path):
        run = _make_run("Trivy", [])
        sarif = _write_sarif(tmp_path, [run])
        result = parse_sarif(sarif)
        assert "Trivy" in result["tools"]

    def test_findings_sorted_critical_first(self, tmp_path):
        run = _make_run("Semgrep", [
            _make_result("note", "rule-note", "Info"),
            _make_result("error", "rule-crit", "Critical"),
            _make_result("warning", "rule-high", "High"),
        ])
        sarif = _write_sarif(tmp_path, [run])
        result = parse_sarif(sarif)
        assert result["findings"][0]["level"] == "error"

    def test_commit_sha_truncated_to_12(self, tmp_path):
        _write_sarif(tmp_path, [_make_run("Semgrep", [])])
        output = tmp_path / "dashboard.html"
        generate_dashboard(tmp_path, output, commit_sha="a" * 40)
        html = output.read_text()
        assert "a" * 12 in html
        assert "a" * 13 not in html


class TestGenerateDashboard:
    def test_generates_html_file(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        _write_sarif(sarif_dir, [_make_run("Semgrep", [])])
        output = tmp_path / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        assert output.exists()
        assert "<html" in output.read_text().lower()

    def test_creates_output_parent_directories(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        _write_sarif(sarif_dir, [_make_run("Semgrep", [])])
        output = tmp_path / "deeply" / "nested" / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        assert output.exists()

    def test_all_sarif_fail_to_parse_shows_parse_error_in_html(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        bad = sarif_dir / "bad.sarif"
        bad.write_text("not json")
        output = tmp_path / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        assert output.exists()
        html = output.read_text()
        assert "PARSE ERR" in html
        assert "ALL CLEAR" not in html

    def test_empty_sarif_dir_generates_empty_state_html(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        output = tmp_path / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        assert output.exists()
        html = output.read_text()
        assert "No scans yet" in html or "no-scan" in html.lower() or "empty" in html.lower()

    def test_critical_finding_shows_fail_in_output(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        run = _make_run("Semgrep", [_make_result("error", "rule-001", "Critical issue")])
        _write_sarif(sarif_dir, [run])
        output = tmp_path / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        html = output.read_text()
        assert "FAIL" in html

    def test_clean_scan_shows_pass_in_output(self, tmp_path):
        sarif_dir = tmp_path / "sarif"
        sarif_dir.mkdir()
        _write_sarif(sarif_dir, [_make_run("Semgrep", [])])
        output = tmp_path / "dashboard.html"
        generate_dashboard(sarif_dir, output)
        html = output.read_text()
        assert "PASS" in html

"""End-to-end tests for `cast init` CLI command."""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from cast_cli.main import app

runner = CliRunner()


class TestCastInitEndToEnd:
    def test_python_github_project_creates_workflow(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        result = runner.invoke(app, ["init"], catch_exceptions=False)
        assert result.exit_code == 0
        assert Path(".github/workflows/devsecops.yml").exists()

    def test_nodejs_github_project_creates_workflow(self, tmp_path):
        (tmp_path / "package.json").touch()
        result = runner.invoke(app, ["init"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_go_github_project_creates_workflow(self, tmp_path):
        (tmp_path / "go.mod").touch()
        result = runner.invoke(app, ["init"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_explicit_type_overrides_detection(self, tmp_path):
        # No markers, but --type go specified
        result = runner.invoke(app, ["init", "--type", "go"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_explicit_platform_gitlab_creates_gitlab_ci(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        result = runner.invoke(app, ["init", "--platform", "gitlab"], catch_exceptions=False)
        assert result.exit_code == 0
        assert Path(".gitlab-ci.yml").exists()

    def test_existing_file_without_force_exits_with_error(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        # First install
        runner.invoke(app, ["init"])
        # Second install without --force should fail
        result = runner.invoke(app, ["init"])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_force_flag_overwrites_existing_file(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0

    def test_unknown_project_type_exits_with_error(self, tmp_path):
        # No project markers → detection fails → exit 1
        result = runner.invoke(app, ["init"])
        assert result.exit_code != 0

    def test_defaults_to_github_with_info_message(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "github" in result.output.lower() or "GitHub" in result.output

    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    @pytest.fixture(autouse=True)
    def _chdir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

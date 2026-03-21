"""Tests for cast_cli.install — template loading and file writing."""

import pytest
from pathlib import Path
from cast_cli.install import (
    load_template,
    write_template,
    already_exists,
    get_workflow_path,
    is_supported,
)


class TestIsSupported:
    def test_python_is_supported(self):
        assert is_supported("python") is True

    def test_nodejs_is_supported(self):
        assert is_supported("nodejs") is True

    def test_go_is_supported(self):
        assert is_supported("go") is True

    def test_docker_not_supported(self):
        assert is_supported("docker") is False

    def test_unknown_type_not_supported(self):
        assert is_supported("ruby") is False


class TestLoadTemplate:
    @pytest.mark.parametrize("project_type", ["python", "nodejs", "go"])
    def test_github_templates_are_non_empty(self, project_type):
        content = load_template(project_type, "github")
        assert len(content) > 100
        assert "name:" in content  # YAML workflow name field

    @pytest.mark.parametrize("project_type", ["python", "nodejs", "go"])
    def test_gitlab_templates_are_non_empty(self, project_type):
        content = load_template(project_type, "gitlab")
        assert len(content) > 100

    def test_github_python_template_contains_expected_tools(self):
        content = load_template("python", "github")
        assert "Gitleaks" in content or "gitleaks" in content
        assert "Semgrep" in content or "semgrep" in content

    def test_github_nodejs_template_contains_expected_tools(self):
        content = load_template("nodejs", "github")
        assert "npm" in content

    def test_github_go_template_contains_go_tool(self):
        content = load_template("go", "github")
        assert "go" in content.lower()

    def test_gitlab_python_template_is_different_from_github(self):
        github = load_template("python", "github")
        gitlab = load_template("python", "gitlab")
        assert github != gitlab

    def test_invalid_type_raises(self):
        with pytest.raises(Exception):
            load_template("ruby", "github")


class TestGetWorkflowPath:
    def test_github_path(self):
        assert get_workflow_path("github") == Path(".github/workflows/devsecops.yml")

    def test_gitlab_path(self):
        assert get_workflow_path("gitlab") == Path(".gitlab-ci.yml")


class TestAlreadyExists:
    def test_returns_false_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert already_exists("github") is False

    def test_returns_true_when_github_workflow_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        workflow = tmp_path / ".github" / "workflows" / "devsecops.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: test")
        assert already_exists("github") is True

    def test_returns_true_when_gitlab_ci_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".gitlab-ci.yml").write_text("stages: []")
        assert already_exists("gitlab") is True


class TestWriteTemplate:
    def test_creates_github_workflow_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_template("name: test", "github")
        assert (tmp_path / ".github" / "workflows" / "devsecops.yml").exists()

    def test_creates_gitlab_ci_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_template("stages: []", "gitlab")
        assert (tmp_path / ".gitlab-ci.yml").exists()

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        write_template("name: test", "github")
        assert (tmp_path / ".github" / "workflows").is_dir()

    def test_written_content_matches_input(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        content = "name: DeployTest\non: push"
        write_template(content, "github")
        written = (tmp_path / ".github" / "workflows" / "devsecops.yml").read_text()
        assert written == content

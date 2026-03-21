"""Tests for cast_cli.detect — project type and platform detection."""

from cast_cli.detect import detect_project, detect_platform


class TestDetectProject:
    def test_pyproject_toml_detected_as_python(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        assert detect_project(tmp_path) == "python"

    def test_requirements_txt_detected_as_python(self, tmp_path):
        (tmp_path / "requirements.txt").touch()
        assert detect_project(tmp_path) == "python"

    def test_setup_py_detected_as_python(self, tmp_path):
        (tmp_path / "setup.py").touch()
        assert detect_project(tmp_path) == "python"

    def test_setup_cfg_detected_as_python(self, tmp_path):
        (tmp_path / "setup.cfg").touch()
        assert detect_project(tmp_path) == "python"

    def test_package_json_detected_as_nodejs(self, tmp_path):
        (tmp_path / "package.json").touch()
        assert detect_project(tmp_path) == "nodejs"

    def test_go_mod_detected_as_go(self, tmp_path):
        (tmp_path / "go.mod").touch()
        assert detect_project(tmp_path) == "go"

    def test_no_markers_returns_none(self, tmp_path):
        assert detect_project(tmp_path) is None

    def test_empty_directory_returns_none(self, tmp_path):
        assert detect_project(tmp_path) is None

    def test_nodejs_wins_over_python_in_monorepo(self, tmp_path):
        # package.json + pyproject.toml: nodejs wins — pyproject.toml is used for tooling
        # in many non-Python repos (ruff, pre-commit, etc.).
        (tmp_path / "package.json").touch()
        (tmp_path / "pyproject.toml").touch()
        assert detect_project(tmp_path) == "nodejs"

    def test_go_wins_over_python_in_monorepo(self, tmp_path):
        # go.mod + pyproject.toml: Go project with Python tooling — must detect as Go.
        (tmp_path / "go.mod").touch()
        (tmp_path / "pyproject.toml").touch()
        assert detect_project(tmp_path) == "go"


class TestDetectPlatform:
    def test_gitlab_ci_yml_detected_as_gitlab(self, tmp_path):
        (tmp_path / ".gitlab-ci.yml").touch()
        assert detect_platform(tmp_path) == "gitlab"

    def test_github_workflows_dir_detected_as_github(self, tmp_path):
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        assert detect_platform(tmp_path) == "github"

    def test_github_dir_detected_as_github(self, tmp_path):
        (tmp_path / ".github").mkdir()
        assert detect_platform(tmp_path) == "github"

    def test_no_markers_defaults_to_github(self, tmp_path):
        assert detect_platform(tmp_path) == "github"

    def test_new_gitlab_project_without_ci_file_defaults_to_github(self, tmp_path):
        # Regression: a fresh GitLab project has no .gitlab-ci.yml yet.
        # Users must pass --platform gitlab explicitly.
        (tmp_path / "go.mod").touch()
        assert detect_platform(tmp_path) == "github"

"""Detect project type and CI platform from the current directory."""

from pathlib import Path


MARKERS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "nodejs": ["package.json"],
    "go":     ["go.mod"],
}

CI_MARKERS: dict[str, list[str]] = {
    "gitlab": [".gitlab-ci.yml"],
    "github": [".github/workflows", ".github"],
}


def detect_project(path: Path = Path(".")) -> str | None:
    """Return the detected project type, or None if unknown."""
    for project_type, files in MARKERS.items():
        if any((path / f).exists() for f in files):
            return project_type
    return None


def detect_platform(path: Path = Path(".")) -> str:
    """Return the detected CI platform, defaulting to 'github'."""
    for platform, markers in CI_MARKERS.items():
        if any((path / m).exists() for m in markers):
            return platform
    return "github"

"""Detect project type from the current directory."""

from pathlib import Path


MARKERS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "nodejs": ["package.json"],
    "go":     ["go.mod"],
}


def detect_project(path: Path = Path(".")) -> str | None:
    """Return the detected project type, or None if unknown."""
    for project_type, files in MARKERS.items():
        if any((path / f).exists() for f in files):
            return project_type
    return None

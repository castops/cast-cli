"""Download and install a CAST workflow template."""

from importlib.resources import files
from pathlib import Path

SUPPORTED: set[str] = {"python"}

WORKFLOW_PATH = Path(".github/workflows/devsecops.yml")


def is_supported(project_type: str) -> bool:
    return project_type in SUPPORTED


def fetch_template(project_type: str) -> str:
    resource = files("cast_cli.templates") / project_type / "devsecops.yml"
    return resource.read_text(encoding="utf-8")


def write_template(content: str) -> None:
    WORKFLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_PATH.write_text(content, encoding="utf-8")


def already_exists() -> bool:
    return WORKFLOW_PATH.exists()

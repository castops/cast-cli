"""Download and install a CAST workflow template."""

from importlib.resources import files
from pathlib import Path

SUPPORTED: set[str] = {"python", "nodejs", "go"}

WORKFLOW_PATHS: dict[str, Path] = {
    "github": Path(".github/workflows/devsecops.yml"),
    "gitlab": Path(".gitlab-ci.yml"),
}


def get_workflow_path(platform: str = "github") -> Path:
    return WORKFLOW_PATHS.get(platform, WORKFLOW_PATHS["github"])


def is_supported(project_type: str) -> bool:
    return project_type in SUPPORTED


def fetch_template(project_type: str, platform: str = "github") -> str:
    if platform == "gitlab":
        resource = (
            files("cast_cli.templates") / "gitlab" / project_type / "devsecops.yml"
        )
    else:
        resource = files("cast_cli.templates") / project_type / "devsecops.yml"
    return resource.read_text(encoding="utf-8")


def write_template(content: str, platform: str = "github") -> None:
    path = get_workflow_path(platform)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def already_exists(platform: str = "github") -> bool:
    return get_workflow_path(platform).exists()

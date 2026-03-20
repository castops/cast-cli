"""Download and install a CAST workflow template."""

from pathlib import Path

import httpx

TEMPLATE_BASE_URL = (
    "https://raw.githubusercontent.com/castops/cast/main/templates"
)

SUPPORTED: dict[str, str] = {
    "python": f"{TEMPLATE_BASE_URL}/python/devsecops.yml",
}

WORKFLOW_PATH = Path(".github/workflows/devsecops.yml")


def is_supported(project_type: str) -> bool:
    return project_type in SUPPORTED


def fetch_template(project_type: str) -> str:
    url = SUPPORTED[project_type]
    response = httpx.get(url, follow_redirects=True, timeout=15)
    response.raise_for_status()
    return response.text


def write_template(content: str) -> None:
    WORKFLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_PATH.write_text(content, encoding="utf-8")


def already_exists() -> bool:
    return WORKFLOW_PATH.exists()

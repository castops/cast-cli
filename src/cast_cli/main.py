"""CAST CLI — entry point."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from cast_cli.detect import detect_project
from cast_cli.install import (
    already_exists,
    fetch_template,
    is_supported,
    write_template,
    WORKFLOW_PATH,
)

app = typer.Typer(
    name="cast",
    help="CAST — CI/CD Automation & Security Toolkit",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()

SUPPORTED_TYPES = {
    "python": "Python (Gitleaks + Semgrep + pip-audit + Trivy + Ruff)",
}

COMING_SOON = ["nodejs", "go", "docker"]


@app.command()
def version() -> None:
    """Show CAST version."""
    from importlib.metadata import version as pkg_version
    try:
        v = pkg_version("cast-cli")
    except Exception:
        v = "dev"
    console.print(f"cast [bold cyan]{v}[/bold cyan]")


@app.command()
def init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing workflow file."
    ),
    project_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Project type to use (python). Auto-detected if omitted.",
    ),
) -> None:
    """Initialize a DevSecOps pipeline for your project."""

    console.print(Panel.fit(
        "[bold cyan]CAST[/bold cyan] — CI/CD Automation & Security Toolkit",
        border_style="cyan",
    ))

    # ── detect ────────────────────────────────────────────────────────────────
    detected = project_type or detect_project(Path("."))

    if detected is None:
        console.print("[yellow]Could not detect project type.[/yellow]")
        console.print("Use [bold]--type[/bold] to specify one:")
        for t, desc in SUPPORTED_TYPES.items():
            console.print(f"  cast init --type {t}  ({desc})")
        raise typer.Exit(1)

    if detected in COMING_SOON:
        console.print(
            f"[yellow]{detected}[/yellow] support is coming soon. "
            "Only [bold]python[/bold] is available today."
        )
        raise typer.Exit(1)

    if not is_supported(detected):
        console.print(f"[red]Unsupported project type:[/red] {detected}")
        raise typer.Exit(1)

    console.print(f"Detected project type: [bold green]{detected}[/bold green]")

    # ── check existing ────────────────────────────────────────────────────────
    if already_exists() and not force:
        console.print(
            f"[yellow]Workflow already exists:[/yellow] {WORKFLOW_PATH}\n"
            "Use [bold]--force[/bold] to overwrite."
        )
        raise typer.Exit(1)

    # ── fetch + write ─────────────────────────────────────────────────────────
    console.print("Downloading template...", end=" ")

    try:
        content = fetch_template(detected)
    except Exception as e:
        console.print(f"\n[red]Failed to download template:[/red] {e}")
        raise typer.Exit(1)

    write_template(content)

    console.print("[green]done[/green]")
    console.print(f"\n[bold green]✓[/bold green] Created [cyan]{WORKFLOW_PATH}[/cyan]")
    console.print(
        "\nCommit and push to activate your DevSecOps pipeline:\n"
        "  [bold]git add .github/workflows/devsecops.yml[/bold]\n"
        "  [bold]git commit -m 'ci: add CAST DevSecOps pipeline'[/bold]\n"
        "  [bold]git push[/bold]"
    )

"""CAST CLI — entry point."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from cast_cli.detect import detect_platform, detect_project
from cast_cli.install import (
    already_exists,
    load_template,
    get_workflow_path,
    is_supported,
    write_template,
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
    "nodejs": "Node.js (Gitleaks + Semgrep + npm audit + Trivy + ESLint)",
    "go":     "Go (Gitleaks + Semgrep + govulncheck + Trivy + staticcheck)",
}

COMING_SOON = ["docker"]


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
        help="Project type (python/nodejs/go). Auto-detected if omitted.",
    ),
    platform: Optional[str] = typer.Option(
        None, "--platform", "-p",
        help="CI platform (github/gitlab). Auto-detected if omitted.",
    ),
) -> None:
    """Initialize a DevSecOps pipeline for your project."""

    console.print(Panel.fit(
        "[bold cyan]CAST[/bold cyan] — CI/CD Automation & Security Toolkit",
        border_style="cyan",
    ))

    # ── detect project type ────────────────────────────────────────────────────
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
            "Available types: " + ", ".join(f"[bold]{t}[/bold]" for t in SUPPORTED_TYPES)
        )
        raise typer.Exit(1)

    if not is_supported(detected):
        console.print(f"[red]Unsupported project type:[/red] {detected}")
        raise typer.Exit(1)

    console.print(f"Detected project type: [bold green]{detected}[/bold green]")

    # ── detect CI platform ─────────────────────────────────────────────────────
    if platform:
        resolved_platform = platform
    else:
        resolved_platform = detect_platform(Path("."))
        if resolved_platform == "github":
            console.print(
                "[dim]No CI config detected — defaulting to GitHub Actions. "
                "Use [bold]--platform gitlab[/bold] to override.[/dim]"
            )

    if resolved_platform not in ("github", "gitlab"):
        console.print(f"[red]Unsupported platform:[/red] {resolved_platform} (use github or gitlab)")
        raise typer.Exit(1)

    console.print(f"Target platform:      [bold green]{resolved_platform}[/bold green]")

    # ── check existing ────────────────────────────────────────────────────────
    workflow_path = get_workflow_path(resolved_platform)
    if already_exists(resolved_platform) and not force:
        console.print(
            f"[yellow]Workflow already exists:[/yellow] {workflow_path}\n"
            "Use [bold]--force[/bold] to overwrite."
        )
        raise typer.Exit(1)

    # ── fetch + write ─────────────────────────────────────────────────────────
    console.print("Installing template...", end=" ")

    try:
        content = load_template(detected, resolved_platform)
    except Exception as e:
        console.print(f"\n[red]Failed to load template:[/red] {e}")
        raise typer.Exit(1)

    write_template(content, resolved_platform)

    console.print("[green]done[/green]")
    console.print(f"\n[bold green]✓[/bold green] Created [cyan]{workflow_path}[/cyan]")

    if resolved_platform == "gitlab":
        console.print(
            "\nCommit and push to activate your DevSecOps pipeline:\n"
            "  [bold]git add .gitlab-ci.yml[/bold]\n"
            "  [bold]git commit -m 'ci: add CAST DevSecOps pipeline'[/bold]\n"
            "  [bold]git push[/bold]"
        )
    else:
        console.print(
            "\nCommit and push to activate your DevSecOps pipeline:\n"
            f"  [bold]git add {workflow_path}[/bold]\n"
            "  [bold]git commit -m 'ci: add CAST DevSecOps pipeline'[/bold]\n"
            "  [bold]git push[/bold]"
        )

"""CAST CLI — entry point."""

import json
import os
import sys
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


def _prompt_type_selection(console: Console) -> str:
    """Show a numbered menu and return the chosen project type."""
    console.print("[yellow]Could not detect project type.[/yellow]")
    console.print("\nSelect a project type:\n")
    choices = list(SUPPORTED_TYPES.items())
    for i, (t, desc) in enumerate(choices, 1):
        console.print(f"  [{i}] {t} — {desc}")
    console.print()
    while True:
        raw = input(f"Enter number [1-{len(choices)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1][0]
        console.print("[red]Invalid choice. Please enter a number from the list.[/red]")


@app.command()
def version() -> None:
    """Show CAST version."""
    from importlib.metadata import version as pkg_version, PackageNotFoundError
    try:
        v = pkg_version("castops")
    except PackageNotFoundError:
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
        if sys.stdin.isatty():
            detected = _prompt_type_selection(console)
        else:
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


# ── Gate policy logic (mirrors policy/*.rego, no OPA dependency) ──────────────

_VALID_POLICIES = ("default", "strict", "permissive")

# Truncate long finding messages in validate output to keep lines readable.
_MAX_MESSAGE_LENGTH = 120


def _apply_gate(runs: list, policy: str) -> tuple[list[str], int]:
    """Return (blocked_messages, blocked_count) for the given policy."""
    blocked: list[str] = []
    for run in runs:
        tool = run.get("tool", {}).get("driver", {}).get("name", "unknown")
        for result in run.get("results", []):
            level = result.get("level", "note")
            rule_id = result.get("ruleId", "")
            msg = result.get("message", {}).get("text", "")[:_MAX_MESSAGE_LENGTH]
            if policy == "default" and level == "error":
                blocked.append(f"[CRITICAL] {tool} — {msg} (rule: {rule_id})")
            elif policy == "strict" and level in ("error", "warning"):
                label = "CRITICAL" if level == "error" else "HIGH"
                blocked.append(f"[{label}] {tool} — {msg} (rule: {rule_id})")
            # permissive: never blocked
    return blocked, len(blocked)


@app.command()
def validate(
    sarif_file: Path = typer.Argument(..., help="Path to a SARIF file to validate."),
    policy: Optional[str] = typer.Option(
        None,
        "--policy",
        help="Gate policy: default / strict / permissive. "
             "Falls back to CAST_POLICY env var, then 'default'.",
    ),
) -> None:
    """Validate a SARIF file and preview cast-gate blocking behavior.

    Exit codes:
      0 — SARIF valid and gate would allow
      1 — SARIF format error (invalid JSON or missing required fields)
      2 — SARIF valid but gate would block
    """
    effective_policy = policy or os.environ.get("CAST_POLICY", "default")

    if effective_policy not in _VALID_POLICIES:
        console.print(
            f"[red]Unknown policy:[/red] {effective_policy!r} "
            f"(valid: {', '.join(_VALID_POLICIES)})"
        )
        raise typer.Exit(1)

    # ── load file ─────────────────────────────────────────────────────────────
    try:
        text = sarif_file.read_text(encoding="utf-8")
    except OSError as e:
        console.print(f"[red]Cannot read file:[/red] {e}")
        raise typer.Exit(1)

    # ── parse JSON ────────────────────────────────────────────────────────────
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON:[/red] {e}")
        raise typer.Exit(1)

    # ── structural validation ─────────────────────────────────────────────────
    format_errors: list[str] = []
    if not isinstance(data, dict):
        format_errors.append("Top-level value must be a JSON object")
    else:
        version = data.get("version")
        if version != "2.1.0":
            format_errors.append(f'version must be "2.1.0", got: {version!r}')
        runs = data.get("runs")
        if runs is None:
            format_errors.append('Missing required field: "runs"')
        elif not isinstance(runs, list):
            format_errors.append('"runs" must be an array')
        else:
            for i, run in enumerate(runs):
                if not isinstance(run, dict):
                    format_errors.append(f"runs[{i}] must be an object")
                    continue
                driver = run.get("tool", {}).get("driver", {})
                if not driver.get("name"):
                    format_errors.append(f"runs[{i}].tool.driver.name is missing or empty")

    if format_errors:
        console.print("[red]✗ SARIF format errors:[/red]")
        for err in format_errors:
            console.print(f"  • {err}")
        raise typer.Exit(1)

    # ── count findings ────────────────────────────────────────────────────────
    runs = data.get("runs", [])
    tools: set[str] = set()
    error_count = warning_count = note_count = 0

    for run in runs:
        tools.add(run.get("tool", {}).get("driver", {}).get("name", "unknown"))
        for result in run.get("results", []):
            level = result.get("level", "note")
            if level == "error":
                error_count += 1
            elif level == "warning":
                warning_count += 1
            else:
                note_count += 1

    total = error_count + warning_count + note_count
    tools_str = ", ".join(sorted(tools)) or "none"

    # ── gate evaluation ───────────────────────────────────────────────────────
    blocked_msgs, blocked_count = _apply_gate(runs, effective_policy)
    gate_blocked = blocked_count > 0

    # ── output ────────────────────────────────────────────────────────────────
    console.print("[bold green]✓[/bold green] SARIF valid")
    console.print(f"  Tool(s):   {tools_str}")
    console.print(
        f"  Findings:  {total} "
        f"({error_count} error, {warning_count} warning, {note_count} note)"
    )
    console.print(f"  Policy:    {effective_policy}")

    if gate_blocked:
        console.print(
            f"  Gate:      [red]❌ {blocked_count} finding(s) would be blocked[/red]"
        )
        console.print()
        for bm in blocked_msgs[:10]:
            console.print(f"  [red]•[/red] {bm}")
        if len(blocked_msgs) > 10:
            console.print(f"  ... and {len(blocked_msgs) - 10} more")
        raise typer.Exit(2)

    console.print(f"  Gate:      [green]✓ would allow (policy: {effective_policy})[/green]")


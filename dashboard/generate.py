#!/usr/bin/env python3
"""
CAST Dashboard Generator
Parses SARIF JSON files and generates a single-page HTML compliance dashboard.

Usage:
    python dashboard/generate.py [--sarif-dir DIR] [--output FILE] [--commit SHA]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template


def parse_sarif(sarif_path: Path) -> dict:
    """Parse a SARIF file and return a scan result dict."""
    try:
        data = json.loads(sarif_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not parse {sarif_path}: {e}", file=sys.stderr)
        return None

    findings = []
    tools = set()
    critical = high = medium = low = 0

    for run in data.get("runs", []):
        tool_name = (
            run.get("tool", {}).get("driver", {}).get("name", "unknown")
        )
        tools.add(tool_name)

        # Build a rule-id → severity map from the rules section
        rule_severity: dict[str, str] = {}
        for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
            rule_id = rule.get("id", "")
            # Some tools embed severity in defaultConfiguration
            severity = (
                rule.get("defaultConfiguration", {}).get("level", "")
                or rule.get("properties", {}).get("precision", "")
            )
            rule_severity[rule_id] = severity

        for result in run.get("results", []):
            level = result.get("level", "note")
            rule_id = result.get("ruleId", "")
            message = result.get("message", {}).get("text", "")[:200]

            # Extract first location
            location = ""
            locations = result.get("locations", [])
            if locations:
                phys = locations[0].get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri", "")
                region = phys.get("region", {})
                line = region.get("startLine", "")
                location = f"{uri}:{line}" if line else uri

            findings.append({
                "level": level,
                "rule_id": rule_id,
                "message": message,
                "location": location,
            })

            if level == "error":
                critical += 1
            elif level == "warning":
                high += 1
            else:
                medium += 1

    # Determine status
    if critical > 0:
        status = "FAIL"
    elif high > 0:
        status = "WARN"
    else:
        status = "PASS"

    # Sort: critical first, then high, then others
    level_order = {"error": 0, "warning": 1, "note": 2}
    findings.sort(key=lambda f: (level_order.get(f["level"], 9), f["rule_id"]))

    return {
        "name": sarif_path.stem,
        "tools": sorted(tools),
        "status": status,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "findings": findings,
    }


def render_findings_html(findings: list[dict]) -> str:
    if not findings:
        return '<span style="color:var(--muted);font-size:12px">No findings</span>'

    level_label = {"error": "CRITICAL", "warning": "HIGH", "note": "INFO"}

    items = []
    for f in findings:
        level = f["level"]
        label = level_label.get(level, level.upper())
        loc = f'<div class="location">{f["location"]}</div>' if f["location"] else ""
        items.append(
            f'<div class="finding">'
            f'<span class="severity {level}">{label}</span>'
            f'<span class="rule">{f["rule_id"]}</span>'
            f'<span class="message">{_escape(f["message"])}</span>'
            f"{loc}"
            f"</div>"
        )

    count = len(findings)
    inner = "\n".join(items)
    return (
        f"<details>"
        f'<summary>{count} finding(s)</summary>'
        f'<div class="findings-list">{inner}</div>'
        f"</details>"
    )


def render_tools_html(tools: list[str]) -> str:
    return "".join(f'<span class="tool-tag">{t}</span>' for t in tools)


def render_badge(status: str) -> str:
    if status == "PASS":
        return '<span class="badge pass">&#10003; PASS</span>'
    if status == "FAIL":
        return '<span class="badge fail">&#10007; FAIL</span>'
    return '<span class="badge warn">&#9888; WARN</span>'


def render_count(n: int, css_class: str) -> str:
    if n > 0:
        return f'<span class="count {css_class}">{n}</span>'
    return '<span class="count ok">—</span>'


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_dashboard(
    sarif_dir: Path,
    output_path: Path,
    commit_sha: str = "unknown",
) -> None:
    sarif_files = sorted(sarif_dir.glob("**/*.sarif"))
    if not sarif_files:
        print(f"No .sarif files found in {sarif_dir}", file=sys.stderr)

    scans = [r for f in sarif_files if (r := parse_sarif(f)) is not None]

    total_critical = sum(s["critical"] for s in scans)
    total_high = sum(s["high"] for s in scans)
    total_findings = sum(len(s["findings"]) for s in scans)
    passing = sum(1 for s in scans if s["status"] == "PASS")
    failing = sum(1 for s in scans if s["status"] == "FAIL")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build rows HTML
    rows_html = []
    for scan in scans:
        row = (
            f"<tr>"
            f"<td>"
            f'<div style="font-weight:600">{_escape(scan["name"])}</div>'
            f'<div style="margin-top:4px">{render_tools_html(scan["tools"])}</div>'
            f"</td>"
            f"<td>{render_badge(scan['status'])}</td>"
            f"<td>{render_count(scan['critical'], 'critical')}</td>"
            f"<td>{render_count(scan['high'], 'high')}</td>"
            f"<td>{render_count(scan['medium'], '')}</td>"
            f"<td>{render_findings_html(scan['findings'])}</td>"
            f"</tr>"
        )
        rows_html.append(row)

    template_path = Path(__file__).parent / "template.html"
    template_text = template_path.read_text(encoding="utf-8")

    # Simple Jinja2-style substitution without requiring Jinja2 dependency.
    # We replace template placeholders manually for zero-dependency operation.
    html = template_text
    replacements = {
        "{{ generated_at }}": generated_at,
        "{{ commit_sha }}": commit_sha[:12] if len(commit_sha) > 12 else commit_sha,
        "{{ summary.passing }}": str(passing),
        "{{ summary.failing }}": str(failing),
        "{{ summary.total_critical }}": str(total_critical),
        "{{ summary.total_high }}": str(total_high),
        "{{ summary.total_findings }}": str(total_findings),
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # Replace the scans loop block
    loop_start = "    {% for scan in scans %}"
    loop_end = "    {% endfor %}"
    start_idx = html.find(loop_start)
    end_idx = html.find(loop_end)
    if start_idx != -1 and end_idx != -1:
        html = html[:start_idx] + "\n".join(rows_html) + html[end_idx + len(loop_end):]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {output_path}")
    print(f"  Scans: {len(scans)} | Critical: {total_critical} | High: {total_high} | Findings: {total_findings}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CAST security dashboard")
    parser.add_argument(
        "--sarif-dir",
        default="sarif-results",
        help="Directory containing .sarif files (default: sarif-results)",
    )
    parser.add_argument(
        "--output",
        default="dashboard/index.html",
        help="Output HTML file path (default: dashboard/index.html)",
    )
    parser.add_argument(
        "--commit",
        default="unknown",
        help="Commit SHA to display in the dashboard",
    )
    args = parser.parse_args()

    generate_dashboard(
        sarif_dir=Path(args.sarif_dir),
        output_path=Path(args.output),
        commit_sha=args.commit,
    )


if __name__ == "__main__":
    main()

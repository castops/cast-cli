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


def render_compliance_banner(failing: int, total_critical: int, total_scans: int) -> str:
    if total_scans == 0:
        return ""
    if failing == 0 and total_critical == 0:
        sub = f"All {total_scans} scan{'s' if total_scans != 1 else ''} passed. No critical issues."
        return (
            '<div class="compliance-banner all-clear" role="status" aria-live="polite">'
            '<span class="icon" aria-hidden="true">✅</span>'
            '<div><div class="verdict">ALL CLEAR</div>'
            f'<div class="sub">{sub}</div></div>'
            "</div>"
        )
    else:
        desc = f"{failing} of {total_scans} scan{'s' if total_scans != 1 else ''} require attention."
        crit_label = f"{total_critical} critical issue{'s' if total_critical != 1 else ''}."
        return (
            '<div class="compliance-banner has-issues" role="alert">'
            '<span class="icon" aria-hidden="true">❌</span>'
            '<div><div class="verdict">'
            f'{total_critical} CRITICAL {"ISSUES" if total_critical != 1 else "ISSUE"}'
            "</div>"
            f'<div class="sub">{desc}</div></div>'
            "</div>"
        )


def render_empty_state() -> str:
    return (
        '<div class="empty-state" role="status">'
        '<div class="empty-icon" aria-hidden="true">🛡️</div>'
        "<h2>No scans yet</h2>"
        "<p>No SARIF results found. Make sure your CAST pipeline has run at least once "
        "and that SARIF artifacts have been collected.</p>"
        '<a href="https://github.com/castops/cast/blob/main/docs/dashboard-guide.md">'
        "View pipeline setup guide →</a>"
        "</div>"
    )


def render_table(scans: list[dict]) -> str:
    rows_html = []
    for scan in scans:
        row_class = ' class="row-fail"' if scan["status"] == "FAIL" else ""
        row = (
            f"<tr{row_class}>"
            f"<td>{render_badge(scan['status'])}</td>"
            f"<td>"
            f'<div style="font-weight:600">{_escape(scan["name"])}</div>'
            f'<div style="margin-top:4px">{render_tools_html(scan["tools"])}</div>'
            f"</td>"
            f"<td>{render_count(scan['critical'], 'critical')}</td>"
            f"<td>{render_count(scan['high'], 'high')}</td>"
            f"<td>{render_count(scan['medium'], '')}</td>"
            f"<td>{render_findings_html(scan['findings'])}</td>"
            f"</tr>"
        )
        rows_html.append(row)

    rows = "\n".join(rows_html)
    return (
        '<div class="table-wrap">'
        '<table role="table" aria-label="Security scan results">'
        "<thead><tr>"
        '<th scope="col">Status</th>'
        '<th scope="col">Project / Tool</th>'
        '<th scope="col">Critical</th>'
        '<th scope="col">High</th>'
        '<th scope="col">Medium</th>'
        '<th scope="col">Details</th>'
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


def generate_dashboard(
    sarif_dir: Path,
    output_path: Path,
    commit_sha: str = "unknown",
    project_name: str = "",
) -> None:
    sarif_files = sorted(sarif_dir.glob("**/*.sarif"))
    if not sarif_files:
        print(f"No .sarif files found in {sarif_dir}", file=sys.stderr)

    scans = [r for f in sarif_files if (r := parse_sarif(f)) is not None]

    if sarif_files and not scans:
        print(
            f"Error: found {len(sarif_files)} SARIF file(s) but all failed to parse. "
            "Dashboard not generated to avoid false 'ALL CLEAR' output.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Override the scan name with project_name if only one SARIF file
    if project_name and len(scans) == 1:
        scans[0]["name"] = project_name

    total_critical = sum(s["critical"] for s in scans)
    total_high = sum(s["high"] for s in scans)
    passing = sum(1 for s in scans if s["status"] == "PASS")
    failing = sum(1 for s in scans if s["status"] == "FAIL")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha_short = commit_sha[:12] if len(commit_sha) > 12 else commit_sha

    compliance_banner = render_compliance_banner(failing, total_critical, len(scans))
    table_or_empty = render_table(scans) if scans else render_empty_state()

    template_path = Path(__file__).parent / "template.html"
    html = template_path.read_text(encoding="utf-8")

    replacements = {
        "{{ generated_at }}": generated_at,
        "{{ commit_sha }}": sha_short,
        "{{ summary.failing }}": str(failing),
        "{{ summary.total_critical }}": str(total_critical),
        "{{ summary.total_high }}": str(total_high),
        "{{ compliance_banner }}": compliance_banner,
        "{{ table_or_empty }}": table_or_empty,
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    status = "ALL CLEAR" if failing == 0 and total_critical == 0 else f"{failing} FAILING"
    print(f"Dashboard written to {output_path}")
    print(f"  Status: {status} | Critical: {total_critical} | High: {total_high} | Scans: {len(scans)}")


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
    parser.add_argument(
        "--project",
        default="",
        help="Project display name (overrides SARIF filename when there is one scan)",
    )
    args = parser.parse_args()

    generate_dashboard(
        sarif_dir=Path(args.sarif_dir),
        output_path=Path(args.output),
        commit_sha=args.commit,
        project_name=args.project,
    )


if __name__ == "__main__":
    main()

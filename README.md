# CAST — CI/CD Automation & Security Toolkit

<div align="center">

**Copy. Paste. Production-grade DevSecOps pipeline.**

[![PyPI version](https://img.shields.io/pypi/v/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![Python](https://img.shields.io/pypi/pyversions/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-ready-2088FF?logo=github-actions&logoColor=white)](https://github.com/castops/cast/actions)

</div>

---

CAST is a collection of battle-tested GitHub Actions workflow templates — so you can get a
complete, security-hardened CI/CD pipeline on day one, without being a DevSecOps expert.

## Table of Contents

- [Why CAST](#why-cast)
- [What You Get](#what-you-get)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Templates](#templates)
- [Pipeline Architecture](#pipeline-architecture)
- [Contributing](#contributing)
- [License](#license)

---

## Why CAST

Most teams use 6–20 security tools but have no unified pipeline. Setting up DevSecOps from
scratch means days of research, configuration, and debugging — for every project, every time.

CAST packages the best practices into ready-to-use GitHub Actions workflows, so you get a
production-grade pipeline on day one.

- **Zero configuration** — auto-detects your stack, writes the workflow file
- **Security-first** — secrets scanning, SAST, SCA, and container scanning out of the box
- **GitHub-native** — all findings surface in GitHub's Security tab, no external dashboards
- **Opinionated** — maintained by people who run these pipelines every day

---

## What You Get

Each CAST template configures your repository with a full security stack:

| Layer | Tool | What It Does |
|-------|------|--------------|
| Secrets Detection | [Gitleaks](https://github.com/gitleaks/gitleaks) | Scans entire git history for leaked credentials |
| SAST | [Semgrep](https://semgrep.dev) | Finds security bugs and anti-patterns in source code |
| SCA | [pip-audit](https://pypi.org/project/pip-audit/) | Detects known vulnerabilities in dependencies |
| Container Security | [Trivy](https://trivy.dev) | Scans Docker images for CVEs (skipped if no Dockerfile) |
| Code Quality | [Ruff](https://docs.astral.sh/ruff/) | Enforces code style and quality standards |
| Security Gate | Built-in | Blocks merges if any critical security check fails |

All findings surface directly in GitHub's **Security tab**. No external dashboards, no extra
accounts, no SaaS dependencies.

---

## Quick Start

### Option A — CLI (Recommended)

```bash
pip install cast-cli
cast init
```

CAST auto-detects your project type and writes the workflow file. One command. Done.

### Option B — Manual

1. Copy the template for your stack:

```bash
curl -O https://raw.githubusercontent.com/castops/cast/main/templates/python/devsecops.yml
```

2. Move it to your repository:

```bash
mkdir -p .github/workflows
mv devsecops.yml .github/workflows/
```

3. Commit and push:

```bash
git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

Your pipeline is live. GitHub Actions will run all security checks on every push and pull request.

---

## CLI Reference

The `cast` CLI is the fastest way to add a DevSecOps pipeline to any project.

### Installation

```bash
pip install cast-cli
```

### Commands

#### `cast init`

Initialize a DevSecOps pipeline in the current directory.

```
Usage: cast init [OPTIONS]

  Initialize a DevSecOps pipeline for your project.

Options:
  -f, --force        Overwrite existing workflow file.
  -t, --type TEXT    Project type to use (python). Auto-detected if omitted.
  --help             Show this message and exit.
```

**Examples:**

```bash
# Auto-detect project type
cast init

# Specify project type explicitly
cast init --type python

# Overwrite an existing workflow
cast init --force
```

**Auto-detection logic:**

CAST detects your project type by looking for marker files in the current directory:

| Project Type | Marker Files |
|--------------|-------------|
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg` |
| Node.js | `package.json` *(coming soon)* |
| Go | `go.mod` *(coming soon)* |

#### `cast version`

Display the installed version of `cast-cli`.

```bash
cast version
# cast 0.1.0
```

---

## Templates

CAST ships with production-tested workflow templates for multiple stacks.

### Available Now

| Stack | Security Tools | Status |
|-------|---------------|--------|
| **Python** | Gitleaks + Semgrep + pip-audit + Trivy + Ruff | ✅ Available |

### Coming Soon

| Stack | Planned Tools | Status |
|-------|--------------|--------|
| **Node.js** | npm audit + Semgrep + ESLint + Trivy | 🔜 In progress |
| **Go** | govulncheck + Semgrep + staticcheck + Trivy | 🔜 Planned |
| **Docker** | Trivy + Hadolint + Dockle | 🔜 Planned |

---

## Pipeline Architecture

The CAST Python pipeline runs **5 parallel security jobs** followed by **1 gate job** that
controls whether a pull request can be merged.

```
┌─────────────────────────────────────────────────────────────┐
│                  CAST DevSecOps Pipeline                    │
│                                                             │
│  ┌──────────────┐  ┌──────┐  ┌─────┐  ┌───────────┐       │
│  │   Secrets    │  │ SAST │  │ SCA │  │ Container │       │
│  │  (Gitleaks)  │  │(Semgrep)│  │(pip-│  │  (Trivy)  │       │
│  │              │  │      │  │audit│  │           │       │
│  └──────┬───────┘  └──┬───┘  └──┬──┘  └─────┬─────┘       │
│         │             │         │            │             │
│         └─────────────┴────┬────┴────────────┘             │
│                            │                               │
│                    ┌───────▼────────┐                      │
│                    │ Security Gate  │                      │
│                    │ (blocks merge) │                      │
│                    └───────────────┘                      │
│                                                             │
│  ┌─────────────┐                                           │
│  │    Ruff     │  (runs independently, informational)      │
│  │  (Quality)  │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### Trigger Conditions

The pipeline runs on:

| Event | Branches |
|-------|----------|
| `push` | `main`, `master` |
| `pull_request` | `main`, `master` |
| `workflow_dispatch` | Any (manual trigger) |

### Security Gate Logic

The gate job runs after all security checks complete, regardless of individual job results:

```
IF secrets == "failure" OR sast == "failure" OR sca == "failure"
  → Block merge (exit 1)
ELSE
  → Allow merge (exit 0)
```

> Code quality failures (Ruff) do **not** block merges by default. Adjust the gate
> job's `needs` array in the workflow to change this behavior.

### SARIF Integration

All security findings (Semgrep, Trivy) are uploaded to GitHub's Security tab via SARIF.
This means:

- All vulnerabilities are tracked as GitHub Security alerts
- Developers see findings inline on pull request diffs
- Security history is retained without any external tools

---

## Requirements

- **GitHub repository** with GitHub Actions enabled
- **Python 3.9+** (for CLI usage)
- No additional accounts, tokens, or external services required

> **Optional:** Set `SEMGREP_APP_TOKEN` as a GitHub secret to enable Semgrep's cloud
> dashboard and additional rulesets.

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Development setup
- Adding new language templates
- Running tests
- Submitting pull requests

---

## Security

To report a security vulnerability in CAST itself, see [SECURITY.md](SECURITY.md).

---

## Philosophy

> Make non-experts immediately professional.

CAST is not a tutorial. It is the executable version of DevSecOps best practices —
opinionated, production-ready, and maintained by people who run these pipelines every day.

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

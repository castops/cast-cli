# CAST — CI/CD Automation & Security Toolkit

<div align="center">

**One engineer's standards. Every team's pipeline.**

[![PyPI version](https://img.shields.io/pypi/v/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![Python](https://img.shields.io/pypi/pyversions/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-ready-2088FF?logo=github-actions&logoColor=white)](https://github.com/castops/cast/actions)

English | [中文](README.zh.md)

</div>

---

CAST is a DevSecOps governance toolkit for GitHub Actions and GitLab CI —
so a single DevOps engineer can enforce pipeline standards across every team,
without personally reviewing every repository.

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

The problem isn't that teams lack security tools. It's that **one DevOps engineer's standards
can't reach every team's pipeline**.

The typical situation: a DevOps engineer defines a secure, policy-compliant pipeline for one
project. Other teams write their own — often AI-generated, often untested against security
standards, always "good enough to push." The DevOps engineer can't review every PR across
every repository. Pipeline quality varies. Security gaps accumulate silently.

CAST is the governance layer that changes this. It's not "DevSecOps for teams with no DevOps
expertise." It's "DevSecOps standards that enforce themselves — without your personal attention
on every repository."

- **Zero configuration** — auto-detects your stack and CI platform, writes the workflow file
- **Security-first** — secrets scanning, SAST, SCA, and container scanning out of the box
- **Policy as Code** — OPA/conftest gate replaces fragile shell logic; policies are versioned
- **Compliance dashboard** — static HTML red/green board deployable to GitHub Pages
- **Multi-platform** — GitHub Actions and GitLab CI supported with identical security coverage

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
| Security Gate | [conftest](https://conftest.dev) + OPA Rego | Policy-as-code gate; blocks merges on critical findings |

All findings surface in GitHub's **Security tab** or GitLab's **Security dashboard**. No external
accounts, no SaaS dependencies.

---

## Quick Start

### Option A — CLI (Recommended)

```bash
pip install cast-cli
cast init
```

CAST auto-detects your project type and CI platform. One command. Done.

For GitLab CI:

```bash
cast init --platform gitlab
```

### Option B — Manual

1. Copy the template for your stack:

```bash
curl -O https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/python/devsecops.yml
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
  -f, --force           Overwrite existing workflow file.
  -t, --type TEXT       Project type (python/nodejs/go). Auto-detected if omitted.
  -p, --platform TEXT   CI platform (github/gitlab). Auto-detected if omitted.
  --help                Show this message and exit.
```

**Examples:**

```bash
# Auto-detect project type and platform
cast init

# Specify project type explicitly
cast init --type nodejs

# Generate a GitLab CI pipeline
cast init --platform gitlab

# Go project on GitLab
cast init --type go --platform gitlab

# Overwrite an existing workflow
cast init --force
```

**Auto-detection logic:**

CAST detects your project type and CI platform by looking for marker files:

| Project Type | Marker Files |
|--------------|-------------|
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg` |
| Node.js | `package.json` |
| Go | `go.mod` |

| CI Platform | Detected by |
|-------------|-------------|
| GitLab | `.gitlab-ci.yml` exists |
| GitHub | `.github/` directory exists (default) |

#### `cast version`

Display the installed version of `cast-cli`.

```bash
cast version
# cast 0.1.0
```

---

## Templates

CAST ships with production-tested workflow templates for multiple stacks.

### GitHub Actions

| Stack | Security Tools | Status |
|-------|---------------|--------|
| **Python** | Gitleaks + Semgrep + pip-audit + Trivy + Ruff | ✅ Available |
| **Node.js** | Gitleaks + Semgrep + npm audit + Trivy + ESLint | ✅ Available |
| **Go** | Gitleaks + Semgrep + govulncheck + Trivy + staticcheck | ✅ Available |

### GitLab CI

| Stack | Security Tools | Status |
|-------|---------------|--------|
| **Python** | Gitleaks + Semgrep + pip-audit + Trivy + Ruff | ✅ Available |
| **Node.js** | Gitleaks + Semgrep + npm audit + Trivy + ESLint | ✅ Available |
| **Go** | Gitleaks + Semgrep + govulncheck + Trivy + staticcheck | ✅ Available |

### Security Gate Policies

| Policy | Blocks on | Activate via |
|--------|-----------|--------------|
| `default` | CRITICAL findings | *(default)* |
| `strict` | HIGH + CRITICAL | `CAST_POLICY=strict` |
| `permissive` | Never (audit only) | `CAST_POLICY=permissive` |

See [docs/policy-reference.md](docs/policy-reference.md) for custom policy authoring.

---

## Pipeline Architecture

Each CAST pipeline runs **5 parallel security jobs** followed by **1 gate job** that
controls whether a pull request can be merged. The example below shows the Python pipeline;
Node.js and Go pipelines follow the same structure with stack-appropriate tools.

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

- **GitHub** or **GitLab** repository with CI/CD enabled
- **Python 3.9+** (for CLI usage)
- No additional accounts, tokens, or external services required

> **Optional:** Set `SEMGREP_APP_TOKEN` as a secret to enable Semgrep's cloud
> dashboard and additional rulesets.

---

## Security Dashboard

CAST can generate a static HTML compliance dashboard — red/green status per
project, collapsible finding details, zero JavaScript dependencies.

```bash
python dashboard/generate.py --sarif-dir sarif-results --output index.html
```

Deploy to GitHub Pages with the included workflow:
```
templates/github/publish-dashboard.yml → .github/workflows/publish-dashboard.yml
```

See [docs/dashboard-guide.md](docs/dashboard-guide.md) for setup instructions.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Step-by-step setup for your first pipeline |
| [CLI Reference](docs/cli-reference.md) | Full `cast` command reference |
| [Pipeline Reference](docs/pipeline-reference.md) | How each pipeline job works |
| [GitLab Guide](docs/gitlab-guide.md) | GitLab CI setup and configuration |
| [Policy Reference](docs/policy-reference.md) | Writing custom OPA/conftest policies |
| [Plugin Guide](docs/plugin-guide.md) | Extending CAST with custom security tools |
| [Dashboard Guide](docs/dashboard-guide.md) | Security dashboard setup and GitHub Pages deployment |

Chinese documentation: [docs/zh/](docs/zh/)

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

> One engineer's standards. Every team's pipeline.

CAST is the answer to a scaling problem: a single DevOps engineer cannot personally review
every CI/CD pipeline across every team. CAST packages expert-validated standards as executable
templates and policy gates — so the standard is enforced by the pipeline itself, not by PR review.

AI can generate a pipeline that runs. CAST enforces a pipeline that complies.

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

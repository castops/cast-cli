# CAST — CI/CD Automation & Security Toolkit

**Copy. Paste. Production-grade DevSecOps pipeline.**

CAST is a collection of battle-tested GitHub Actions workflow templates —
so you can get a complete, security-hardened CI/CD pipeline on day one,
without being a DevSecOps expert.

---

## Why CAST

Most teams use 6–20 security tools but have no unified pipeline. Setting up DevSecOps
from scratch means days of research, configuration, and debugging — for every project.

CAST packages the best practices into ready-to-use GitHub Actions workflows, so you
get a production-grade pipeline on day one.

---

## What You Get

Each CAST template configures your repository with:

| Layer | Tool | What It Does |
|-------|------|--------------|
| Secrets Detection | Gitleaks | Catches credentials before they reach GitHub |
| SAST | Semgrep / CodeQL | Finds security bugs in your code |
| SCA | pip-audit / Dependabot | Detects vulnerable dependencies |
| Container Security | Trivy | Scans Docker images for CVEs |
| Code Quality | Ruff | Enforces code standards |
| Security Gate | Built-in | Blocks merges if critical issues are found |

All findings surface directly in GitHub's Security tab. No external dashboards needed.

---

## Quick Start

### Requirements

- GitHub repository
- GitHub Actions enabled

### Usage

1. Copy the template for your stack:

```bash
curl -O https://raw.githubusercontent.com/castops/cast/main/templates/python/devsecops.yml
```

2. Move it to your repository:

```bash
mkdir -p .github/workflows
mv devsecops.yml .github/workflows/
```

3. Commit and push. That's it.

> **`cast` CLI coming soon** — `cast init` will automate steps 1–3 automatically.

---

## Templates

CAST ships with battle-tested workflow templates for:

- **Python** — pip-audit, Semgrep, Ruff, Trivy
- **Node.js** — npm audit, Semgrep, ESLint, Trivy *(coming soon)*
- **Go** — govulncheck, Semgrep, staticcheck, Trivy *(coming soon)*
- **Docker** — Trivy, Hadolint, Dockle *(coming soon)*

---

## Philosophy

> Make non-experts immediately professional.

CAST is not a tutorial. It is the executable version of DevSecOps best practices —
opinionated, production-ready, and maintained by people who run these pipelines
every day.

---

## License

Apache 2.0

# Changelog

All notable changes to CAST are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **Node.js and Go GitHub Actions templates** — production-ready pipelines for both stacks:
  - Node.js: Gitleaks + Semgrep + npm audit + Trivy + ESLint + conftest gate
  - Go: Gitleaks + Semgrep + govulncheck + Trivy + staticcheck + conftest gate
- **GitLab CI templates** — full security parity with GitHub Actions for Python, Node.js, and Go:
  - Use `cast init --platform gitlab` to generate a `.gitlab-ci.yml`
  - Findings appear in GitLab's Security dashboard via SARIF artifact reports
- **Policy as Code (OPA/conftest)** — the security gate now evaluates SARIF findings using
  Rego policies instead of hardcoded shell logic:
  - `policy/default.rego` — blocks on CRITICAL findings (default)
  - `policy/strict.rego` — blocks on HIGH + CRITICAL
  - `policy/permissive.rego` — audit only, never blocks merges
  - Custom policies can be placed in a `policy/` directory alongside the workflow
- **Static HTML security dashboard** — generate a compliance overview from SARIF results:
  - `dashboard/generate.py`: parses SARIF files and renders a zero-dependency HTML page
  - Red/green status per scan, collapsible finding details, commit SHA and timestamp
  - Deploy to GitHub Pages with `templates/github/publish-dashboard.yml`
- **`cast init --platform gitlab`** — the CLI now supports GitLab CI as a target platform
- **Auto-detection of CI platform** — `cast init` detects `.gitlab-ci.yml` and `.github/`
  to determine the platform automatically
- **Chinese documentation** — full Chinese translation under `docs/zh/` and `README.zh.md`
- **Test suite** — 65 tests covering project detection, template installation, dashboard
  generation, and CLI behavior

### Fixed

- **Gitleaks in org repositories** — replaced the GitHub Action (requires paid org license)
  with direct CLI installation from GitHub releases; works on all repositories for free
- **SARIF upload without GitHub Advanced Security** — upload steps now use `continue-on-error`
  so the pipeline does not fail when GHAS is not enabled on the repository
- **Semgrep SARIF fallback** — added an "Ensure SARIF exists" step so the upload action
  never fails when Semgrep exits non-zero without creating a SARIF file
- **Auto-detection priority** — Go and Node.js are now detected before Python, so repositories
  that use `pyproject.toml` only for tooling (Ruff, pre-commit) are not misidentified

---

## [0.1.0] — 2024-01-01

### Added

- **`cast` CLI** — new `cast-cli` Python package installable via `pip install cast-cli`
  - `cast init` command: writes a DevSecOps workflow to `.github/workflows/devsecops.yml`
  - `cast version` command: displays the installed package version
  - Auto-detection of project type from marker files (`pyproject.toml`, `requirements.txt`, etc.)
  - `--force` flag to overwrite existing workflow files
  - `--type` flag to override auto-detection
  - Rich terminal output with color-coded status messages
- **Python DevSecOps template** — production-ready GitHub Actions workflow including:
  - Secrets Detection via [Gitleaks](https://github.com/gitleaks/gitleaks) (full git history scan)
  - SAST via [Semgrep](https://semgrep.dev) with SARIF upload to GitHub Security tab
  - SCA via [pip-audit](https://pypi.org/project/pip-audit/) for vulnerable dependency detection
  - Container Security via [Trivy](https://trivy.dev) (conditional on Dockerfile presence)
  - Code Quality via [Ruff](https://docs.astral.sh/ruff/)
  - Security Gate job that blocks merges on critical security failures
- **Manual installation** support via `curl` for teams that prefer not to install the CLI

### Technical Details

- Python 3.9+ support
- Templates embedded in the package via `importlib.resources` for offline use
- MIT-compatible dependencies: [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- Build system: `setuptools` + `setuptools-scm` (version from git tags)

---

## [0.0.1] — Initial Commit

- Project scaffolding and initial Python workflow template
- Apache 2.0 license

---

[Unreleased]: https://github.com/castops/cast/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/castops/cast/releases/tag/v0.1.0

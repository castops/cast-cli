# Changelog

All notable changes to CAST are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_No unreleased changes._

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

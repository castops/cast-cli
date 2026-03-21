# Contributing to CAST

Thank you for your interest in contributing to CAST. This document outlines the process
for contributing code, templates, and documentation to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New Template](#adding-a-new-template)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Release Process](#release-process)

---

## Code of Conduct

This project follows a standard open-source code of conduct. Be respectful, constructive,
and collaborative. Harassment of any kind will not be tolerated.

---

## Getting Started

Before contributing, please:

1. **Search existing issues** to avoid duplicates
2. **Open an issue** for non-trivial changes to discuss the approach before writing code
3. **Fork the repository** and create a feature branch from `main`

---

## Development Setup

### Prerequisites

- Python 3.9 or higher
- `git`

### Install in Editable Mode

```bash
# Clone your fork
git clone https://github.com/<your-username>/cast.git
cd cast

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

> If there is no `[dev]` extras group yet, install the base package with:
> ```bash
> pip install -e .
> ```

### Verify Installation

```bash
cast version
```

---

## Project Structure

```
cast/
├── src/
│   └── cast_cli/
│       ├── __init__.py
│       ├── main.py          # CLI entry point — Typer app, all commands
│       ├── detect.py        # Project type auto-detection
│       ├── install.py       # Template fetching and writing
│       └── templates/
│           └── python/
│               └── devsecops.yml   # Embedded Python workflow template
├── templates/
│   └── python/
│       └── devsecops.yml   # Source template (must stay in sync with embedded copy)
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── SECURITY.md
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Templates are **embedded** in the package (`src/cast_cli/templates/`) | Ensures `cast init` works offline and without network calls at install time |
| Templates also exist at **top-level** (`templates/`) | Allows direct `curl` access for manual installation without the CLI |
| **Auto-detection** before explicit `--type` | Reduces friction for the happy path |
| **`--force` flag** required to overwrite | Prevents accidental overwrites of customized workflows |

---

## Adding a New Template

To add support for a new language or framework, follow these steps:

### 1. Create the workflow template

Create the file at both paths (they must be identical):

```
templates/<stack>/devsecops.yml
src/cast_cli/templates/<stack>/devsecops.yml
```

A template must:

- Follow the CAST naming convention (`name: CAST DevSecOps`)
- Run on `push` and `pull_request` to `main`/`master`
- Include at minimum: secrets detection, SAST, and SCA
- Upload all SARIF results to GitHub Security tab
- Include a `gate` job that blocks merges on critical failures

Use the existing `templates/python/devsecops.yml` as a reference implementation.

### 2. Register the marker files

In `src/cast_cli/detect.py`, add your stack's marker files to the `MARKERS` dict:

```python
MARKERS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "nodejs": ["package.json"],   # example
    "go":     ["go.mod"],         # example
    "<stack>": ["<marker-file>"],  # add your stack here
}
```

### 3. Register the supported type

In `src/cast_cli/install.py`, add your stack to the `SUPPORTED` set:

```python
SUPPORTED: set[str] = {"python", "<stack>"}
```

Also remove it from `COMING_SOON` in `src/cast_cli/main.py` if it was listed there.

### 4. Update documentation

- Add the new stack to the **Templates** table in `README.md`
- Add an entry in `CHANGELOG.md` under the appropriate version
- Add the stack description to `SUPPORTED_TYPES` in `main.py`

### 5. Test manually

```bash
# Create a temporary test directory with a marker file
mkdir /tmp/test-<stack> && cd /tmp/test-<stack>
touch <marker-file>

# Run cast init and verify the workflow is created
cast init
cat .github/workflows/devsecops.yml
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cast_cli
```

> The test suite is currently minimal. New contributions should include tests for
> any new detection logic or CLI behavior.

---

## Code Style

CAST uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for lint issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

All code must pass `ruff check` with no errors before a pull request can be merged.

---

## Submitting a Pull Request

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/nodejs-template
   ```

2. **Make your changes** following the guidelines in this document

3. **Test your changes** manually and with the test suite

4. **Update the changelog** in `CHANGELOG.md` under `[Unreleased]`

5. **Push and open a PR** against `main`:
   ```bash
   git push origin feat/nodejs-template
   ```

### Pull Request Checklist

- [ ] Changes are limited to a single concern
- [ ] Code passes `ruff check` with no errors
- [ ] Manual testing completed
- [ ] `CHANGELOG.md` updated
- [ ] Documentation updated (README, docstrings)

---

## Release Process

Releases are managed by maintainers. The process:

1. Update `CHANGELOG.md` — move items from `[Unreleased]` to a new version section
2. Create and push a version tag: `git tag v0.x.0 && git push origin v0.x.0`
3. `setuptools-scm` reads the tag to set the package version automatically
4. The package is built and published to PyPI via CI

---

## Questions?

Open a [GitHub Discussion](https://github.com/castops/cast/discussions) or file an
[issue](https://github.com/castops/cast/issues).

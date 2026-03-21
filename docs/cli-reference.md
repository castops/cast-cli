# CLI Reference

Complete reference for the `cast` command-line interface.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Commands](#commands)
  - [cast init](#cast-init)
  - [cast version](#cast-version)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)

---

## Installation

```bash
pip install cast-cli
```

**Requirements:** Python 3.9 or higher.

After installation, the `cast` command is available in your PATH.

```bash
cast --help
```

---

## Global Options

```
Options:
  --help    Show help message and exit.
```

Running `cast` with no arguments displays the help message.

---

## Commands

### cast init

Initialize a DevSecOps pipeline in the current directory.

#### Synopsis

```
cast init [OPTIONS]
```

#### Description

Writes a production-ready GitHub Actions workflow to `.github/workflows/devsecops.yml`.

The command:

1. Detects your project type from marker files (or uses `--type` if provided)
2. Checks if a workflow file already exists
3. Reads the embedded template for your project type
4. Creates `.github/workflows/` if it does not exist
5. Writes the workflow file

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--force` | `-f` | flag | `false` | Overwrite an existing workflow file |
| `--type` | `-t` | string | (auto-detect) | Project type: `python` |
| `--help` | | | | Show help and exit |

#### Examples

**Auto-detect project type:**

```bash
cd my-python-project
cast init
```

Output:
```
╭──────────────────────────────────────────────────╮
│ CAST — CI/CD Automation & Security Toolkit        │
╰──────────────────────────────────────────────────╯
Detected project type: python
Downloading template... done

✓ Created .github/workflows/devsecops.yml

Commit and push to activate your DevSecOps pipeline:
  git add .github/workflows/devsecops.yml
  git commit -m 'ci: add CAST DevSecOps pipeline'
  git push
```

**Specify project type explicitly:**

```bash
cast init --type python
```

**Overwrite an existing workflow:**

```bash
cast init --force
# or
cast init -f
```

#### Auto-detection Logic

CAST scans the current directory for the following marker files:

| Project Type | Marker Files | Status |
|--------------|-------------|--------|
| `python` | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg` | ✅ Available |
| `nodejs` | `package.json` | 🔜 Coming soon |
| `go` | `go.mod` | 🔜 Coming soon |

The first matching project type wins. If no marker files are found, `cast init`
exits with an error and prompts you to use `--type`.

#### Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `Could not detect project type.` | No marker files found | Use `--type python` |
| `Workflow already exists` | `.github/workflows/devsecops.yml` exists | Use `--force` to overwrite |
| `Unsupported project type` | Type not recognized | Use a supported type |
| `nodejs support is coming soon` | Stack not yet available | Use `python` for now |

---

### cast version

Display the installed version of `cast-cli`.

#### Synopsis

```
cast version
```

#### Description

Reads the version from the installed package metadata and prints it.

#### Example

```bash
cast version
# cast 0.1.0
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (detection failed, unsupported type, existing file, template error) |

---

## Environment Variables

The `cast` CLI does not read any environment variables directly. Environment
variables relevant to the generated workflow (e.g., `SEMGREP_APP_TOKEN`) are
configured as GitHub Actions secrets, not in your local environment.

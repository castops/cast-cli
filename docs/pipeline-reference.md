# Pipeline Reference

This document provides a complete technical reference for the CAST DevSecOps pipeline.

## Table of Contents

- [Overview](#overview)
- [Job Reference](#job-reference)
  - [1. Secrets Detection](#1-secrets-detection)
  - [2. SAST](#2-sast)
  - [3. SCA](#3-sca)
  - [4. Container Security](#4-container-security)
  - [5. Code Quality](#5-code-quality)
  - [6. Security Gate](#6-security-gate)
- [Permissions](#permissions)
- [Trigger Configuration](#trigger-configuration)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CAST DevSecOps pipeline is a GitHub Actions workflow that runs six jobs on every push
and pull request to your main branch.

```
Trigger: push / pull_request / workflow_dispatch
│
├── Job 1: secrets        (Gitleaks)       ─┐
├── Job 2: sast           (Semgrep)         │ Run in parallel
├── Job 3: sca            (pip-audit)       │
├── Job 4: container      (Trivy)          ─┘
├── Job 5: quality        (Ruff)
│
└── Job 6: gate           (Security Gate)  ← waits for 1, 2, 3, 5
```

---

## Job Reference

### 1. Secrets Detection

**Job ID:** `secrets`
**Runner:** `ubuntu-latest`
**Tool:** [Gitleaks v2](https://github.com/gitleaks/gitleaks)

#### What it does

Scans the **complete git history** of the repository for hardcoded secrets, API keys,
tokens, passwords, and other credentials. Gitleaks uses a comprehensive set of regex
patterns to detect over 150 types of secrets.

#### Configuration

```yaml
secrets:
  name: Secrets Detection
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0   # Full history — critical for catching old commits
    - name: Gitleaks
      uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### Key settings

| Setting | Value | Why |
|---------|-------|-----|
| `fetch-depth: 0` | Full history | Gitleaks scans all commits, not just the latest |
| `GITHUB_TOKEN` | Auto-provided | Used for rate limit avoidance on public repos |

#### Failure behavior

- Fails if any secret is detected in any commit
- **Blocks merge** via the Security Gate

#### Suppressing false positives

Add a `.gitleaks.toml` to your repository root:

```toml
[allowlist]
  description = "Allowlist"
  regexes = [
    '''false-positive-pattern''',
  ]
  paths = [
    '''path/to/test/fixtures''',
  ]
```

---

### 2. SAST

**Job ID:** `sast`
**Runner:** `ubuntu-latest` (containerized)
**Tool:** [Semgrep](https://semgrep.dev)

#### What it does

Performs Static Application Security Testing (SAST) — analyzing source code for
security vulnerabilities, insecure patterns, and common coding mistakes without
executing the code.

#### Configuration

```yaml
sast:
  name: SAST
  runs-on: ubuntu-latest
  container:
    image: semgrep/semgrep
  steps:
    - uses: actions/checkout@v4
    - name: Semgrep scan
      run: semgrep ci --sarif --output=semgrep.sarif || true
      env:
        SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
    - name: Upload to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: semgrep.sarif
```

#### Key settings

| Setting | Value | Why |
|---------|-------|-----|
| `semgrep/semgrep` container | Official image | Ensures correct Semgrep version |
| `|| true` | Always exit 0 | Findings are surfaced via SARIF, not exit code |
| `SEMGREP_APP_TOKEN` | Optional secret | Enables cloud rules; falls back to open-source rules |
| `if: always()` on upload | Always upload | Ensures SARIF is uploaded even if scan has findings |

#### SARIF Integration

Findings are uploaded to the GitHub Security tab and appear as:
- Code scanning alerts on the repository
- Inline annotations on pull request diffs

#### Optional: Semgrep Cloud

Set `SEMGREP_APP_TOKEN` as a GitHub Actions secret to enable:
- Additional proprietary rulesets
- Historical tracking in Semgrep's dashboard
- Team-wide finding management

---

### 3. SCA

**Job ID:** `sca`
**Runner:** `ubuntu-latest`
**Tool:** [pip-audit](https://pypi.org/project/pip-audit/)

#### What it does

Performs Software Composition Analysis (SCA) — checking your Python dependencies
against known vulnerability databases (PyPI Advisory Database, OSV).

#### Configuration

```yaml
sca:
  name: SCA
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.x"
        cache: pip
    - name: pip-audit
      uses: pypa/gh-action-pip-audit@v1
      with:
        inputs: requirements*.txt
```

#### Key settings

| Setting | Value | Why |
|---------|-------|-----|
| `cache: pip` | Enabled | Speeds up subsequent runs |
| `inputs: requirements*.txt` | Glob pattern | Scans all requirements files |

#### Failure behavior

- Fails if any dependency has a known CVE
- **Blocks merge** via the Security Gate

#### Customization

To scan `pyproject.toml` dependencies instead of requirements files:

```yaml
- uses: pypa/gh-action-pip-audit@v1
  with:
    inputs: pyproject.toml
```

---

### 4. Container Security

**Job ID:** `container`
**Runner:** `ubuntu-latest`
**Tool:** [Trivy](https://trivy.dev)

#### What it does

Scans your Docker image for known CVEs in OS packages and application dependencies.
The job is **automatically skipped** if no `Dockerfile` is present in the repository.

#### Configuration

```yaml
container:
  name: Container Security
  runs-on: ubuntu-latest
  if: hashFiles('Dockerfile') != ''
  steps:
    - uses: actions/checkout@v4
    - name: Build image
      run: docker build -t cast-scan:${{ github.sha }} .
    - name: Trivy scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: cast-scan:${{ github.sha }}
        format: sarif
        output: trivy.sarif
        severity: CRITICAL,HIGH
        exit-code: "0"
    - name: Upload to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: trivy.sarif
```

#### Key settings

| Setting | Value | Why |
|---------|-------|-----|
| `hashFiles('Dockerfile') != ''` | Conditional | Skips gracefully if no Dockerfile exists |
| `severity: CRITICAL,HIGH` | Filter | Focuses on actionable findings |
| `exit-code: "0"` | No exit | Gate job handles blocking logic |
| `github.sha` tag | Unique tag | Prevents collision between concurrent runs |

#### Failure behavior

- Does **not** directly block merges — findings are surfaced via SARIF
- To add blocking behavior, add `container` to the gate job's `needs` array

---

### 5. Code Quality

**Job ID:** `quality`
**Runner:** `ubuntu-latest`
**Tool:** [Ruff](https://docs.astral.sh/ruff/)

#### What it does

Runs Ruff — an extremely fast Python linter and formatter — to enforce code style
and catch common mistakes.

#### Configuration

```yaml
quality:
  name: Code Quality
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/ruff-action@v1
```

#### Customization

Ruff reads configuration from `pyproject.toml` or `ruff.toml`:

```toml
# pyproject.toml
[tool.ruff]
target-version = "py39"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

#### Failure behavior

- Fails if any lint errors are found
- **Does not block merges** by default (not in gate's `needs` array)
- To block on quality failures, add `quality` to the gate's blocking condition

---

### 6. Security Gate

**Job ID:** `gate`
**Runner:** `ubuntu-latest`
**Dependencies:** `secrets`, `sast`, `sca`, `quality`

#### What it does

Aggregates the results of all security jobs and makes a single pass/fail decision.
This is the job that GitHub branch protection rules should target.

#### Configuration

```yaml
gate:
  name: Security Gate
  runs-on: ubuntu-latest
  needs: [secrets, sast, sca, quality]
  if: always()
  steps:
    - name: Evaluate results
      run: |
        echo "secrets : ${{ needs.secrets.result }}"
        echo "sast    : ${{ needs.sast.result }}"
        echo "sca     : ${{ needs.sca.result }}"
        echo "quality : ${{ needs.quality.result }}"

        if [[ "${{ needs.secrets.result }}" == "failure" ||
              "${{ needs.sast.result }}"    == "failure" ||
              "${{ needs.sca.result }}"     == "failure" ]]; then
          echo "❌ Security gate failed — merge blocked"
          exit 1
        fi

        echo "✅ All checks passed — safe to merge"
```

#### Gate decision matrix

| Secrets | SAST | SCA | Gate Result |
|---------|------|-----|-------------|
| ✅ pass | ✅ pass | ✅ pass | ✅ Allow merge |
| ❌ fail | ✅ pass | ✅ pass | ❌ Block merge |
| ✅ pass | ❌ fail | ✅ pass | ❌ Block merge |
| ✅ pass | ✅ pass | ❌ fail | ❌ Block merge |
| any | any | any | ❌ Block merge (if any of the above fail) |

> Note: Code quality (Ruff) failures are reported but do not block merges in the
> default configuration.

#### Enforcing the gate with branch protection

To make the Security Gate mandatory for pull requests:

1. Go to **Settings → Branches → Branch protection rules**
2. Add a rule for `main` (or `master`)
3. Enable **"Require status checks to pass before merging"**
4. Search for and add **"Security Gate"**
5. Optionally enable **"Require branches to be up to date before merging"**

---

## Permissions

The workflow requests the minimum permissions needed:

```yaml
permissions:
  contents: read          # checkout code
  security-events: write  # upload SARIF to Security tab
  actions: read           # read workflow status for gate
```

No write access to repository contents is granted.

---

## Trigger Configuration

The default triggers cover the most common workflow:

```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:        # manual trigger from GitHub UI
```

### Running only on pull requests

To reduce Actions minutes, remove the `push` trigger:

```yaml
on:
  pull_request:
    branches: [main, master]
  workflow_dispatch:
```

### Adding schedule-based scanning

To run a full scan daily (e.g., to catch newly disclosed CVEs):

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC daily
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
```

---

## Customization Guide

### Changing severity thresholds

In the Trivy job, change the `severity` input:

```yaml
severity: CRITICAL,HIGH,MEDIUM   # report medium and above
```

### Adding email notifications on gate failure

```yaml
gate:
  # ... existing config ...
  steps:
    - name: Evaluate results
      # ... existing step ...
    - name: Notify on failure
      if: failure()
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.example.com
        to: security-team@example.com
        subject: "CAST Security Gate Failed — ${{ github.repository }}"
        body: "Security gate failed on ${{ github.ref }}"
```

### Skipping checks on specific paths

```yaml
on:
  push:
    branches: [main, master]
    paths-ignore:
      - "docs/**"
      - "*.md"
```

---

## Troubleshooting

### Gitleaks fails on legitimate test fixtures

Add a `.gitleaks.toml` allowlist (see [Secrets Detection](#1-secrets-detection) section).

### Semgrep SARIF upload fails

Ensure `security-events: write` is set in `permissions`. This is required for the
`github/codeql-action/upload-sarif` action.

### pip-audit finds no requirements file

If you use only `pyproject.toml`, change the `inputs` parameter:

```yaml
with:
  inputs: pyproject.toml
```

Or install your package and audit the environment:

```yaml
- run: pip install -e .
- uses: pypa/gh-action-pip-audit@v1
```

### Container job is skipped unexpectedly

The `hashFiles('Dockerfile')` condition evaluates to empty string if the file is in
a subdirectory. Change the condition to match your path:

```yaml
if: hashFiles('**/Dockerfile') != ''
```

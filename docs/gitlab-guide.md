# GitLab CI Integration Guide

CAST supports GitLab CI alongside GitHub Actions. Use `cast init --platform gitlab` to
generate a `.gitlab-ci.yml`, or include a remote template directly.

## Quick Start

### Option A — CLI

```bash
pip install cast-cli
cast init --platform gitlab
```

CAST auto-detects your project type and writes `.gitlab-ci.yml`.

### Option B — Remote include (zero-install)

Add to your `.gitlab-ci.yml`:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/templates/gitlab/python/devsecops.yml'
```

Replace `python` with `nodejs` or `go` to match your stack.

---

## What Gets Installed

The pipeline adds six jobs across two stages:

| Stage | Job | Tool | Blocks pipeline? |
|-------|-----|------|-----------------|
| `cast-scan` | `cast-secrets` | Gitleaks | Yes |
| `cast-scan` | `cast-sast` | Semgrep | No (gate evaluates) |
| `cast-scan` | `cast-sca` | pip-audit / npm audit / govulncheck | Yes |
| `cast-scan` | `cast-container` | Trivy | No (gate evaluates) |
| `cast-scan` | `cast-quality` | Ruff / ESLint / staticcheck | No (informational) |
| `cast-gate` | `cast-gate` | conftest | Yes |

---

## GitLab Security Dashboard Integration

Semgrep results are reported via the `sast` artifact report type — they appear
automatically in GitLab's **Security & Compliance → Security dashboard**.

Trivy results are reported via `container_scanning` — they appear in the
**Container Scanning** report in merge requests.

---

## Policy Customization

The gate job uses [conftest](https://conftest.dev) to evaluate SARIF findings
against an OPA Rego policy.

**Default behavior:** block if any CRITICAL finding (SARIF level `error`) is found.

**Override the policy** by creating a `policy/` directory in your repo:

```
policy/
  default.rego   ← CAST looks here first
```

Or set the `CAST_POLICY` CI/CD variable to `default`, `strict`, or `permissive`:

```yaml
variables:
  CAST_POLICY: strict   # block on HIGH + CRITICAL
```

See [policy-reference.md](policy-reference.md) for policy details.

---

## Merge Request Integration

When triggered on a merge request, the pipeline:

1. Runs all security scans in parallel
2. Reports Semgrep findings inline on the diff
3. Posts container scanning results to the MR security widget
4. Blocks the MR from merging if the gate job fails

---

## Extending the Pipeline

Since the template uses `cast-` prefixed stage names (`cast-scan`, `cast-gate`),
you can add your own stages without conflict:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/templates/gitlab/python/devsecops.yml'

stages:
  - cast-scan
  - cast-gate
  - test       # your own stage
  - deploy

my-tests:
  stage: test
  script: pytest
```

---

## Troubleshooting

**`cast-sca` fails with "no requirements file"**

pip-audit looks for `requirements*.txt`. If you use `pyproject.toml` only, add:

```yaml
cast-sca:
  script:
    - pip install --quiet pip-audit
    - pip install -e .
    - pip-audit
```

**`cast-container` runs but Dockerfile is present**

The job uses `trivy fs` (filesystem scan) rather than building and scanning the
image, so no Docker daemon is required. To scan a built image, override the job
with Docker-in-Docker configuration.

**Gate passes but I see findings in the Security dashboard**

The gate only blocks on **CRITICAL** findings by default. Set `CAST_POLICY: strict`
to also block on HIGH findings.

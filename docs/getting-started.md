# Getting Started with CAST

This guide walks you through adding a production-grade DevSecOps pipeline to your
repository in under five minutes.

## Prerequisites

- A GitHub repository with GitHub Actions enabled
- Python 3.9+ (only required for the `cast` CLI)

No external accounts, tokens, or SaaS subscriptions are required.

---

## Step 1 — Install the CLI

```bash
pip install cast-cli
```

Verify the installation:

```bash
cast --help
```

---

## Step 2 — Initialize Your Pipeline

Navigate to your project root and run:

```bash
cast init
```

CAST will auto-detect your project type and write the workflow file:

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

If auto-detection fails (no `pyproject.toml`, `requirements.txt`, etc.), specify the
type explicitly:

```bash
cast init --type python
```

---

## Step 3 — Commit and Push

```bash
git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

GitHub Actions will pick up the workflow and run your first pipeline immediately.

---

## Step 4 — Review Your First Run

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. You should see **"CAST DevSecOps"** running

The pipeline runs six jobs:

| Job | Tool | What to Expect |
|-----|------|---------------|
| Secrets Detection | Gitleaks | Pass if no secrets in git history |
| SAST | Semgrep | Pass with open-source rules; configure cloud token for more |
| SCA | pip-audit | Pass if no CVEs in your dependencies |
| Container Security | Trivy | Skipped if no Dockerfile |
| Code Quality | Ruff | Pass if code meets style rules |
| Security Gate | Built-in | Passes if all critical checks pass |

---

## Step 5 — View Security Findings

All findings from Semgrep and Trivy are uploaded to GitHub's **Security tab**:

1. Go to your repository → **Security** tab
2. Click **"Code scanning alerts"**
3. Review any findings

New findings will also appear as inline comments on future pull requests.

---

## Step 6 — Enforce the Gate (Optional but Recommended)

To prevent merging pull requests that fail the Security Gate:

1. Go to **Settings → Branches**
2. Click **"Add branch protection rule"**
3. Set **Branch name pattern** to `main`
4. Enable **"Require status checks to pass before merging"**
5. Search for and select **"Security Gate"**
6. Save the rule

From now on, any pull request with security failures will be blocked from merging.

---

## Optional: Enable Semgrep Cloud

For additional security rules and a centralized findings dashboard:

1. Sign up at [semgrep.dev](https://semgrep.dev) (free tier available)
2. Go to **Settings → Tokens** and create a CI token
3. In your GitHub repository, go to **Settings → Secrets and variables → Actions**
4. Add a secret named `SEMGREP_APP_TOKEN` with your token value

The pipeline will automatically use your cloud token on the next run.

---

## Manual Installation (No CLI)

If you prefer not to install the CLI, copy the template directly:

```bash
# Create the workflows directory
mkdir -p .github/workflows

# Download the Python template
curl -o .github/workflows/devsecops.yml \
  https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/python/devsecops.yml

# Commit and push
git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

---

## Next Steps

- Read the [Pipeline Reference](pipeline-reference.md) for a full technical breakdown
  of each job, how to customize thresholds, and how to suppress false positives
- Read the [CLI Reference](cli-reference.md) for all available options
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to add support for a new language stack

# Security Dashboard Guide

CAST can generate a static HTML compliance dashboard from SARIF scan results
and publish it to GitHub Pages — no external services, no SaaS accounts.

## What the Dashboard Shows

Each SARIF file becomes one row in the dashboard:

| Column | Description |
|--------|-------------|
| Project / Tool | SARIF filename + tools that produced it |
| Status | 🟢 PASS / 🔴 FAIL / 🟡 WARN |
| Critical | Count of SARIF `error`-level findings |
| High | Count of SARIF `warning`-level findings |
| Medium | Count of SARIF `note`-level findings |
| Details | Expandable list of individual findings |

The header shows total counts and the commit SHA of the last scanned run.

---

## Setup

### Step 1 — Enable GitHub Pages

In your repository: **Settings → Pages → Source: GitHub Actions**

### Step 2 — Add the publish workflow

```bash
mkdir -p .github/workflows
curl -o .github/workflows/publish-dashboard.yml \
  https://raw.githubusercontent.com/castops/cast/main/templates/github/publish-dashboard.yml
```

Or copy it from the CAST repo:
```
templates/github/publish-dashboard.yml → .github/workflows/publish-dashboard.yml
```

### Step 3 — Copy the dashboard scripts

```bash
mkdir -p dashboard
curl -o dashboard/generate.py \
  https://raw.githubusercontent.com/castops/cast/main/dashboard/generate.py
curl -o dashboard/template.html \
  https://raw.githubusercontent.com/castops/cast/main/dashboard/template.html
```

### Step 4 — Commit and push

```bash
git add .github/workflows/publish-dashboard.yml dashboard/
git commit -m "ci: add CAST security dashboard"
git push
```

The dashboard publishes automatically after each CAST DevSecOps pipeline run.

---

## How It Works

```
CAST DevSecOps pipeline
  ├── sast job     → uploads cast-sarif-sast artifact (semgrep.sarif)
  └── container job → uploads cast-sarif-container artifact (trivy.sarif)

publish-dashboard workflow (triggered on workflow_run: completed)
  ├── downloads all cast-sarif-* artifacts
  ├── runs python dashboard/generate.py
  └── deploys _site/index.html to GitHub Pages
```

The `workflow_run` trigger ensures the dashboard only publishes after a
complete pipeline run, not on every push.

---

## Generating the Dashboard Locally

```bash
# Place your SARIF files in sarif-results/
mkdir -p sarif-results
cp path/to/semgrep.sarif sarif-results/
cp path/to/trivy.sarif sarif-results/

# Generate
python dashboard/generate.py

# Open
open dashboard/index.html
```

**Options:**

```
python dashboard/generate.py --help

  --sarif-dir DIR    Directory containing .sarif files (default: sarif-results)
  --output FILE      Output HTML path (default: dashboard/index.html)
  --commit SHA       Commit SHA to display in header
```

---

## Customizing the Dashboard

The template lives in `dashboard/template.html`. It uses plain HTML and
inline CSS — no build step, no npm, no webpack.

To customize colors, edit the CSS variables in `:root`:

```css
:root {
  --green: #3fb950;   /* PASS badge color */
  --red: #f85149;     /* FAIL badge color */
  --yellow: #d29922;  /* WARN badge color */
}
```

To add columns (e.g., scanner version), extend `generate.py` and the
matching `<th>`/`<td>` in the template.

---

## Multi-repo Dashboards

To aggregate findings from multiple repositories into one dashboard:

1. Have each repo upload its SARIF artifacts with a unique prefix:
   ```yaml
   - uses: actions/upload-artifact@v4
     with:
       name: cast-sarif-myrepo-sast
       path: semgrep.sarif
   ```

2. In a central `dashboard` repository, download artifacts from all repos
   using `gh run download` or the GitHub API, then run `generate.py`.

This approach requires a GitHub token with `actions:read` access to each repo.

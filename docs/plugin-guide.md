# Plugin Guide — Extending CAST

CAST is designed to be extended. Every security tool that can produce a SARIF file
can plug into the CAST gate — no fork required.

## How Plugins Work

CAST's gate evaluates **all artifacts** whose name matches `cast-sarif-*`. Any job
in your workflow that uploads an artifact with this naming convention is automatically
included in the security gate evaluation.

```
Your workflow
│
├── cast-sast       → uploads cast-sarif-sast      ─┐
├── cast-sca        → uploads cast-sarif-sca         │ Gate evaluates
├── cast-secrets    → uploads cast-sarif-secrets      │ ALL of these
│                                                    │
└── my-custom-tool  → uploads cast-sarif-custom    ──┘  ← plugin!
```

The gate job (`cast-gate`) downloads everything matching `cast-sarif-*` and passes
each file through the active OPA/conftest policy. Your custom tool's findings are
treated identically to built-in findings.

---

## Adding a Custom Tool (GitHub Actions)

### Step 1 — Run your tool and produce a SARIF file

Any tool that can output SARIF works. If your tool doesn't support SARIF natively,
you can write a small wrapper (see [Writing a SARIF Wrapper](#writing-a-sarif-wrapper)).

```yaml
jobs:
  my-custom-scan:
    name: Custom Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run my tool
        run: |
          my-security-tool --output=results.sarif --format=sarif .

      - name: Upload as CAST plugin
        uses: actions/upload-artifact@v4
        with:
          name: cast-sarif-custom   # ← must start with cast-sarif-
          path: results.sarif
```

### Step 2 — That's it

The CAST gate job automatically picks up `cast-sarif-custom` on its next run.
No changes to the gate job are needed.

---

## Adding a Custom Tool (GitLab CI)

```yaml
my-custom-scan:
  stage: cast-scan
  script:
    - my-security-tool --output=results.sarif --format=sarif .
  artifacts:
    name: cast-sarif-custom        # ← must start with cast-sarif-
    paths:
      - results.sarif
    when: always
```

---

## Writing a SARIF Wrapper

If your tool doesn't output SARIF, wrap it with a small Python script:

```python
#!/usr/bin/env python3
"""Convert custom tool output to SARIF 2.1.0."""

import json
import subprocess
import sys

def run_tool():
    result = subprocess.run(
        ["my-tool", "--json", "."],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def to_sarif(findings):
    results = []
    for f in findings:
        level = "error" if f["severity"] == "CRITICAL" else "warning"
        results.append({
            "ruleId": f["rule_id"],
            "level": level,           # "error" → CAST gate blocks on this
            "message": {"text": f["message"]},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f["file"]},
                    "region": {"startLine": f["line"]}
                }
            }]
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "my-tool",
                    "version": "1.0.0",
                    "rules": []
                }
            },
            "results": results
        }]
    }

if __name__ == "__main__":
    findings = run_tool()
    sarif = to_sarif(findings)
    with open("custom.sarif", "w") as f:
        json.dump(sarif, f, indent=2)
    print(f"Wrote {len(findings)} findings to custom.sarif")
```

### SARIF severity → gate behavior

| SARIF `level` | `default` policy | `strict` policy |
|---------------|-----------------|-----------------|
| `error`       | ❌ Blocks gate   | ❌ Blocks gate   |
| `warning`     | ✅ Passes gate   | ❌ Blocks gate   |
| `note`        | ✅ Passes gate   | ✅ Passes gate   |

Set `level: "error"` for findings you want to block merges. Set `level: "warning"`
for findings you want to surface without blocking.

---

## Naming Convention

Plugin artifact names must follow this pattern:

```
cast-sarif-<tool-name>
```

Examples:
- `cast-sarif-bandit` — Bandit Python security linter
- `cast-sarif-eslint-security` — ESLint security plugin
- `cast-sarif-checkov` — Terraform/IaC scanner
- `cast-sarif-osv-scanner` — OSV dependency scanner
- `cast-sarif-custom` — anything you build

The `<tool-name>` portion appears in gate logs to identify which tool produced findings.

---

## Policy Customization for Plugins

You can write an OPA policy that treats your plugin's findings differently from
built-in findings. The gate passes the full SARIF file to conftest, so you can
inspect `input.runs[_].tool.driver.name`.

```rego
package main

import future.keywords.if
import future.keywords.in

# Block on CRITICAL from any tool
deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.level == "error"
    msg := sprintf("[%s] CRITICAL: %s", [run.tool.driver.name, result.message.text])
}

# Block on HIGH from built-in tools only (not custom scanners)
deny[msg] if {
    run := input.runs[_]
    run.tool.driver.name in {"Semgrep", "Trivy"}
    result := run.results[_]
    result.level == "warning"
    msg := sprintf("[%s] HIGH: %s", [run.tool.driver.name, result.message.text])
}
```

See the [Policy Reference](policy-reference.md) for full policy authoring documentation.

---

## Example: Adding Bandit (Python Security Linter)

[Bandit](https://bandit.readthedocs.io) produces SARIF natively. Add it as a CAST plugin:

```yaml
bandit:
  name: Bandit (Python Security)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.x"
    - name: Install Bandit
      run: pip install bandit[sarif]
    - name: Run Bandit
      run: bandit -r . -f sarif -o bandit.sarif || true
    - name: Upload as CAST plugin
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: cast-sarif-bandit
        path: bandit.sarif
```

## Example: Adding Checkov (Infrastructure-as-Code Scanner)

```yaml
checkov:
  name: Checkov (IaC Security)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run Checkov
      uses: bridgecrewio/checkov-action@master
      with:
        output_format: sarif
        output_file_path: checkov.sarif
        soft_fail: true
    - name: Upload as CAST plugin
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: cast-sarif-checkov
        path: checkov.sarif
```

---

## Troubleshooting

**Gate doesn't see my plugin's findings**

Check the artifact name. It must start with `cast-sarif-` exactly (case-sensitive).
Verify in the Actions run under "Artifacts" that the artifact was uploaded.

**Plugin findings don't block the gate**

Check that your SARIF uses `level: "error"` for findings you want to block.
`level: "warning"` passes the `default` policy. Switch to `CAST_POLICY=strict`
to block on warnings, or write a custom policy.

**SARIF validation errors in conftest**

Your SARIF must conform to the SARIF 2.1.0 schema. Validate with:
```bash
pip install sarif-tools
sarif summary results.sarif
```

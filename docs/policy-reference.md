# Policy Reference — CAST Security Gate

CAST uses [conftest](https://conftest.dev) with OPA Rego policies to evaluate
SARIF security findings. This approach replaces hard-coded shell logic with
version-controlled, auditable policies.

## Built-in Policies

Three policies ship with CAST, selectable via the `CAST_POLICY` variable:

| Policy | File | Blocks on | Use case |
|--------|------|-----------|----------|
| `default` | `policy/default.rego` | CRITICAL only | Production pipelines |
| `strict` | `policy/strict.rego` | CRITICAL + HIGH | High-security projects |
| `permissive` | `policy/permissive.rego` | Never | Audit / onboarding |

### Selecting a policy

**GitHub Actions** — set a repository variable:

```
Settings → Secrets and variables → Actions → Variables → New variable
Name: CAST_POLICY
Value: strict
```

**GitLab CI** — set a CI/CD variable:

```
Settings → CI/CD → Variables → Add variable
Key: CAST_POLICY
Value: strict
```

If `CAST_POLICY` is unset, the `default` policy is used.

---

## How the Gate Works

1. SARIF-generating jobs (Semgrep, Trivy) upload their output as artifacts.
2. The `gate` / `cast-gate` job downloads all `cast-sarif-*` artifacts.
3. conftest evaluates each SARIF file against the active policy.
4. If any `deny` rule fires, the gate job exits 1, blocking the merge/MR.

SARIF severity → conftest level mapping:

| Tool severity | SARIF `level` | `default` | `strict` |
|---------------|--------------|-----------|----------|
| CRITICAL | `error` | ❌ BLOCK | ❌ BLOCK |
| HIGH | `warning` | ✅ PASS | ❌ BLOCK |
| MEDIUM | `warning` | ✅ PASS | ❌ BLOCK |
| LOW | `note` | ✅ PASS | ✅ PASS |

> Note: Semgrep maps ERROR→`error`, WARNING→`warning`. Trivy maps CRITICAL→`error`,
> HIGH→`error` (when `--severity CRITICAL,HIGH` flag is used in the scan).

---

## Writing a Custom Policy

To override the CAST policy, create a `policy/` directory in your repository
with at least one `.rego` file. The gate job detects this directory and uses
it instead of fetching from the CAST repo.

```
your-repo/
├── policy/
│   └── my-policy.rego   ← gates evaluate this
├── .github/workflows/
│   └── devsecops.yml
```

**Example: block only on specific rule IDs**

```rego
package main

import future.keywords.if
import future.keywords.in

BLOCKED_RULES := {"sql-injection", "hardcoded-secret", "eval-injection"}

deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.ruleId in BLOCKED_RULES
    msg := sprintf("Blocked rule %s: %s", [result.ruleId, result.message.text])
}
```

**Example: block only findings in specific paths**

```rego
package main

import future.keywords.if

deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.level == "error"
    location := result.locations[_]
    path := location.physicalLocation.artifactLocation.uri
    not startswith(path, "test/")   # ignore findings in test code
    msg := sprintf("CRITICAL in %s: %s", [path, result.message.text])
}
```

---

## Testing Policies Locally

Install conftest:

```bash
brew install conftest           # macOS
# or
curl -Lo conftest.tar.gz \
  https://github.com/open-policy-agent/conftest/releases/download/v0.50.0/conftest_0.50.0_Linux_x86_64.tar.gz
tar xzf conftest.tar.gz && sudo mv conftest /usr/local/bin/
```

Run against a SARIF file:

```bash
# Test with default policy (blocks CRITICAL)
conftest test path/to/semgrep.sarif --policy policy/default.rego

# Test with strict policy (blocks HIGH + CRITICAL)
conftest test path/to/trivy.sarif --policy policy/strict.rego

# Test with all policies in directory
conftest test path/to/*.sarif --policy policy/
```

A non-zero exit code means the policy blocked — the same result as in CI.

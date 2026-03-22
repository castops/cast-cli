# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

---

## Reporting a Vulnerability

If you discover a security vulnerability in CAST — whether in the CLI, a workflow template,
or the documentation — please **do not open a public GitHub issue**.

Instead, report it privately:

1. Go to the [Security Advisories](https://github.com/castops/cast/security/advisories) page
2. Click **"Report a vulnerability"**
3. Provide a clear description, reproduction steps, and the potential impact

You can expect:

- **Acknowledgement** within 48 hours
- **Status update** within 7 days
- **CVE assignment** (if applicable) and coordinated disclosure once a fix is available

---

## Scope

### In scope

- Vulnerabilities in `castops` source code
- Security misconfigurations in the workflow templates that could expose secrets or
  bypass security checks
- Supply-chain issues with pinned third-party actions used in templates

### Out of scope

- Security issues in third-party tools integrated by the templates (Gitleaks, Semgrep,
  pip-audit, Trivy, Ruff) — please report these to their respective maintainers
- Issues that require an attacker to have write access to the target repository

---

## Template Security Notes

### GitHub Actions Permissions

The CAST workflow templates follow the principle of least privilege:

```yaml
permissions:
  contents: read          # read-only checkout
  security-events: write  # required for SARIF upload to Security tab
  actions: read           # required for workflow status checks
```

No write access to repository contents is granted.

### Secrets Handling

- `GITHUB_TOKEN` is used only by Gitleaks for GitHub API rate limit avoidance
- `SEMGREP_APP_TOKEN` is optional and used only to enable cloud rulesets
- No credentials are ever printed in logs or stored as artifacts

### Action Pinning

All third-party actions in CAST templates reference **immutable tags** (e.g., `@v4`, `@v2`).
For production deployments requiring maximum supply-chain security, we recommend pinning
actions to their full commit SHA. See GitHub's
[security hardening guide](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
for details.

---

## Acknowledgements

We thank the security researchers and contributors who responsibly disclose vulnerabilities
and help make CAST more secure.

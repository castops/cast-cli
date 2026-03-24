# 插件指南 — 扩展 CAST

CAST 专为可扩展性而设计。任何能生成 SARIF 文件的安全工具都可以接入 CAST 门禁——无需 Fork 仓库。

## 插件工作原理

CAST 的门禁会评估**所有**名称匹配 `cast-sarif-*` 的制品。工作流中任何上传此命名规范制品的作业都会被自动纳入安全门禁评估。

```
Your workflow
│
├── cast-sast       → uploads cast-sarif-sast      ─┐
├── cast-sca        → uploads cast-sarif-sca         │ Gate evaluates
├── cast-secrets    → uploads cast-sarif-secrets      │ ALL of these
│                                                    │
└── my-custom-tool  → uploads cast-sarif-custom    ──┘  ← plugin!
```

门禁作业（`cast-gate`）下载所有匹配 `cast-sarif-*` 的制品，并将每个文件传递给当前活跃的 OPA/conftest 策略进行评估。您的自定义工具发现结果与内置工具的发现结果处理方式完全相同。

---

## 添加自定义工具（GitHub Actions）

### 第一步 — 运行工具并生成 SARIF 文件

任何能输出 SARIF 的工具均可使用。如果您的工具不原生支持 SARIF，可以编写一个简单的包装器（参见[编写 SARIF 包装器](#sarif-wrapper)）。

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

### 第二步 — 完成

CAST 门禁作业将在下次运行时自动识别 `cast-sarif-custom`，无需修改门禁作业。

---

## 添加自定义工具（GitLab CI）

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

## 编写 SARIF 包装器 {#sarif-wrapper}

如果您的工具不输出 SARIF，可以用一个简单的 Python 脚本进行封装：

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

### SARIF 严重性与门禁行为的对应关系

| SARIF `level` | `default` 策略 | `strict` 策略 |
|---------------|----------------|---------------|
| `error`       | ❌ 阻断门禁     | ❌ 阻断门禁    |
| `warning`     | ✅ 通过门禁     | ❌ 阻断门禁    |
| `note`        | ✅ 通过门禁     | ✅ 通过门禁    |

对于希望阻断合并的发现，将 `level` 设为 `"error"`；对于希望上报但不阻断的发现，将 `level` 设为 `"warning"`。

---

## 命名规范

插件制品名称必须遵循以下模式：

```
cast-sarif-<tool-name>
```

示例：

- `cast-sarif-bandit` — Bandit Python 安全检查器
- `cast-sarif-eslint-security` — ESLint 安全插件
- `cast-sarif-checkov` — Terraform/IaC 扫描器
- `cast-sarif-osv-scanner` — OSV 依赖扫描器
- `cast-sarif-custom` — 任何您自建的工具

`<tool-name>` 部分将出现在门禁日志中，用于标识产生发现的工具。

---

## 针对插件的策略自定义

您可以编写 OPA 策略，对插件发现与内置工具发现采取不同处理方式。门禁将完整的 SARIF 文件传递给 conftest，因此您可以检查 `input.runs[_].tool.driver.name`。

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

完整的策略编写文档请参阅[策略参考](policy-reference.md)。

---

## 示例：添加 Bandit（Python 安全检查器）

[Bandit](https://bandit.readthedocs.io) 原生支持 SARIF 输出。将其作为 CAST 插件添加：

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

## 示例：添加 Checkov（基础设施即代码扫描器）

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

## 故障排查

### 门禁未识别到插件的发现结果

检查制品名称。名称必须以 `cast-sarif-` 开头（区分大小写）。在 Actions 运行的"Artifacts"部分确认制品已成功上传。

### 插件发现未阻断门禁

检查您的 SARIF 是否对希望阻断的发现使用了 `level: "error"`。`level: "warning"` 在 `default` 策略下会通过。切换至 `CAST_POLICY=strict` 可对 warning 级别也进行阻断，或编写自定义策略。

### conftest 中出现 SARIF 验证错误

您的 SARIF 必须符合 SARIF 2.1.0 规范。使用以下命令进行验证：

```bash
pip install sarif-tools
sarif summary results.sarif
```

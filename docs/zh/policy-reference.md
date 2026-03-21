# 策略参考 — CAST 安全门禁

CAST 使用 [conftest](https://conftest.dev) 配合 OPA Rego 策略评估 SARIF 安全发现。
该方案将硬编码的 Shell 逻辑替换为版本化、可审计的策略文件。

## 内置策略

CAST 附带三种策略，通过 `CAST_POLICY` 变量切换：

| 策略 | 文件 | 阻断条件 | 适用场景 |
|------|------|---------|---------|
| `default` | `policy/default.rego` | 仅 CRITICAL | 生产流水线 |
| `strict` | `policy/strict.rego` | CRITICAL + HIGH | 高安全要求项目 |
| `permissive` | `policy/permissive.rego` | 从不阻断 | 审计 / 接入期 |

### 选择策略

**GitHub Actions** — 设置 Repository Variable：

```
Settings → Secrets and variables → Actions → Variables → New variable
Name: CAST_POLICY
Value: strict
```

**GitLab CI** — 设置 CI/CD Variable：

```
Settings → CI/CD → Variables → Add variable
Key: CAST_POLICY
Value: strict
```

未设置 `CAST_POLICY` 时，默认使用 `default` 策略。

---

## 门禁工作原理

1. SARIF 生成 Job（Semgrep、Trivy）将输出作为 artifact 上传
2. `gate` / `cast-gate` Job 下载所有 `cast-sarif-*` artifact
3. conftest 对每个 SARIF 文件执行策略评估
4. 任意 `deny` 规则触发 → 门禁 Job 以退出码 1 失败，阻断合并 / MR

### SARIF 严重级别映射

| 工具严重级别 | SARIF `level` | `default` | `strict` |
|-------------|--------------|-----------|----------|
| CRITICAL | `"error"` | ❌ 阻断 | ❌ 阻断 |
| HIGH | `"warning"` | ✅ 放行 | ❌ 阻断 |
| MEDIUM | `"warning"` | ✅ 放行 | ❌ 阻断 |
| LOW | `"note"` | ✅ 放行 | ✅ 放行 |

> 注：Semgrep 映射 ERROR→`"error"`，WARNING→`"warning"`。
> Trivy 使用 `--severity CRITICAL,HIGH` 参数时，CRITICAL 和 HIGH 均映射为 `"error"`。

---

## 编写自定义策略

在仓库中创建 `policy/` 目录，放入至少一个 `.rego` 文件，
门禁 Job 会优先使用本地策略而不从 CAST repo 下载：

```
your-repo/
├── policy/
│   └── my-policy.rego   ← 门禁使用此文件
├── .github/workflows/
│   └── devsecops.yml
```

### 示例：仅阻断特定规则 ID

```rego
package main

import future.keywords.if
import future.keywords.in

# 高危规则白名单——命中时必须阻断
BLOCKED_RULES := {"sql-injection", "hardcoded-secret", "eval-injection"}

deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.ruleId in BLOCKED_RULES
    msg := sprintf("高危规则 %s: %s", [result.ruleId, result.message.text])
}
```

### 示例：跳过测试代码中的发现

```rego
package main

import future.keywords.if

deny[msg] if {
    run := input.runs[_]
    result := run.results[_]
    result.level == "error"
    location := result.locations[_]
    path := location.physicalLocation.artifactLocation.uri
    not startswith(path, "tests/")   # 忽略测试目录的发现
    msg := sprintf("生产代码存在 CRITICAL: %s — %s", [path, result.message.text])
}
```

### 示例：按工具区分阻断策略

```rego
package main

import future.keywords.if

# Semgrep 发现：阻断所有 error 级别
deny[msg] if {
    run := input.runs[_]
    run.tool.driver.name == "Semgrep"
    result := run.results[_]
    result.level == "error"
    msg := sprintf("[Semgrep CRITICAL] %s: %s", [result.ruleId, result.message.text])
}

# Trivy 发现：仅阻断 CVSS 评分 >= 9.0 的漏洞
deny[msg] if {
    run := input.runs[_]
    run.tool.driver.name == "Trivy"
    result := run.results[_]
    result.level == "error"
    # 从 rule 元数据读取 CVSS 分数
    rule := run.tool.driver.rules[_]
    rule.id == result.ruleId
    score := rule.properties["security-severity"]
    score >= 9.0
    msg := sprintf("[Trivy CVSS %.1f] %s: %s", [score, result.ruleId, result.message.text])
}
```

---

## 本地测试策略

**安装 conftest：**

```bash
# macOS
brew install conftest

# Linux
curl -fsSL -o conftest.tar.gz \
  https://github.com/open-policy-agent/conftest/releases/download/v0.50.0/conftest_0.50.0_Linux_x86_64.tar.gz
tar xzf conftest.tar.gz && sudo mv conftest /usr/local/bin/
```

**对 SARIF 文件评估：**

```bash
# 使用默认策略（阻断 CRITICAL）
conftest test path/to/semgrep.sarif --policy policy/default.rego

# 使用严格策略（阻断 HIGH + CRITICAL）
conftest test path/to/trivy.sarif --policy policy/strict.rego

# 对目录中所有策略文件评估
conftest test path/to/*.sarif --policy policy/

# 使用宽松策略（仅展示，不阻断）
conftest test path/to/semgrep.sarif --policy policy/permissive.rego
```

退出码非零代表策略阻断——与 CI 中的行为完全一致。

---

## 理解 Rego 策略语法

CAST 策略使用 OPA Rego 语言。关键概念：

```rego
package main          # 包名（conftest 默认查找 main 包）

import future.keywords.if    # 启用 if 关键字（OPA 1.0+ 语法）
import future.keywords.in    # 启用 in 关键字

# deny 规则：触发时阻断（exit 1）
deny[msg] if {
    # 在 SARIF JSON 中遍历
    run := input.runs[_]          # input 是解析后的 SARIF 对象
    result := run.results[_]      # _ 表示"任意元素"
    result.level == "error"       # 条件：所有条件都满足时规则触发
    msg := sprintf("...")          # msg 是错误消息
}

# warn 规则：触发时仅输出警告（exit 0）
warn[msg] if {
    # ...
}
```

详细文档见 [OPA Rego 参考](https://www.openpolicyagent.org/docs/latest/policy-language/)。

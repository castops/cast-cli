# 流水线参考

CAST DevSecOps 流水线完整技术参考手册。

## 目录

- [总览](#总览)
- [Job 参考](#job-参考)
  - [1. 秘密检测](#1-秘密检测)
  - [2. SAST](#2-sast)
  - [3. SCA](#3-sca)
  - [4. 容器安全](#4-容器安全)
  - [5. 代码质量](#5-代码质量)
  - [6. 安全门禁](#6-安全门禁)
- [权限配置](#权限配置)
- [触发条件](#触发条件)
- [自定义指南](#自定义指南)
- [故障排查](#故障排查)

---

## 总览

CAST DevSecOps 流水线在每次推送和 Pull Request 时并行运行五个安全扫描 Job，
最后由一个门禁 Job 做出统一的放行 / 阻断决策。

```
触发器: push / pull_request / workflow_dispatch
│
├── Job 1: secrets     (Gitleaks)        ─┐
├── Job 2: sast        (Semgrep)          │ 并行运行
├── Job 3: sca         (pip-audit 等)     │
├── Job 4: container   (Trivy)           ─┘
├── Job 5: quality     (Ruff 等)
│
└── Job 6: gate        (conftest 门禁)  ← 等待 1、2、3、5 完成
```

### 各语言技术栈对比

| 检测层 | Python | Node.js | Go |
|--------|--------|---------|-----|
| 秘密检测 | Gitleaks | Gitleaks | Gitleaks |
| SAST | Semgrep | Semgrep | Semgrep |
| SCA | pip-audit | npm audit | govulncheck |
| 容器安全 | Trivy | Trivy | Trivy |
| 代码质量 | Ruff | ESLint | staticcheck |
| 门禁 | conftest | conftest | conftest |

---

## Job 参考

### 1. 秘密检测

**Job ID：** `secrets`
**运行环境：** `ubuntu-latest`
**工具：** [Gitleaks v2](https://github.com/gitleaks/gitleaks)

#### 作用

扫描仓库**完整 git 历史**，检测硬编码的秘密：API Key、Token、密码、私钥等凭证。
Gitleaks 内置 150+ 种正则规则，覆盖主流云服务商和常见凭证格式。

#### 关键配置

| 配置项 | 值 | 原因 |
|--------|-----|------|
| `fetch-depth: 0` | 完整历史 | Gitleaks 需要扫描所有提交，不只是最新 |
| `GITHUB_TOKEN` | 自动提供 | 避免公开仓库的 API 限流 |

#### 失败行为

- 任意提交中发现秘密即失败
- 通过安全门禁**阻断合并**

#### 抑制误报

在仓库根目录创建 `.gitleaks.toml`：

```toml
[allowlist]
  description = "已知误报"
  regexes = [
    '''test-api-key-pattern''',
  ]
  paths = [
    '''tests/fixtures/''',
  ]
```

---

### 2. SAST

**Job ID：** `sast`
**运行环境：** `ubuntu-latest`（容器化）
**工具：** [Semgrep](https://semgrep.dev)

#### 作用

静态应用安全测试（SAST）——不执行代码，直接分析源码中的安全漏洞、不安全模式和常见编码错误。

#### 关键配置

| 配置项 | 值 | 原因 |
|--------|-----|------|
| `semgrep/semgrep` 容器 | 官方镜像 | 确保 Semgrep 版本固定 |
| `\|\| true` | 始终退出 0 | 发现项通过 SARIF 上报，不用退出码 |
| `SEMGREP_APP_TOKEN` | 可选 Secret | 启用云端规则；缺省时回退到开源规则集 |
| `if: always()` | 始终上传 | 即使有发现也保证 SARIF 上传成功 |

#### SARIF 集成

发现项上传到 GitHub Security 标签页，以：
- 代码扫描告警形式展示
- 在 Pull Request diff 上内联标注

#### 可选：启用 Semgrep 云端

将 `SEMGREP_APP_TOKEN` 添加为仓库 Secret，可解锁：
- 更多专有规则集
- Semgrep 云端 Dashboard 的历史追踪
- 团队级发现管理

---

### 3. SCA

**Job ID：** `sca`
**运行环境：** `ubuntu-latest`

#### 作用

软件成分分析（SCA）——对照已知漏洞数据库检查项目依赖。

| 语言 | 工具 | 数据库 |
|------|------|--------|
| Python | [pip-audit](https://pypi.org/project/pip-audit/) | PyPI Advisory DB、OSV |
| Node.js | npm audit | npm Advisory DB |
| Go | [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) | Go Vulnerability DB |

#### 失败行为

- 依赖中存在已知 CVE 即失败
- 通过安全门禁**阻断合并**

#### Python 自定义：扫描 pyproject.toml

如果只用 `pyproject.toml` 而没有 `requirements.txt`：

```yaml
- uses: pypa/gh-action-pip-audit@v1
  with:
    inputs: pyproject.toml
```

或先安装再审计：

```yaml
- run: pip install -e .
- uses: pypa/gh-action-pip-audit@v1
```

---

### 4. 容器安全

**Job ID：** `container`
**运行环境：** `ubuntu-latest`
**工具：** [Trivy](https://trivy.dev)

#### 作用

扫描 Docker 镜像中操作系统包和应用依赖的已知 CVE。
仓库中**无 `Dockerfile` 时自动跳过**。

**GitHub Actions** 构建并扫描实际镜像；
**GitLab CI** 使用 `trivy fs` 文件系统扫描（无需 Docker 守护进程）。

#### 关键配置

| 配置项 | 值 | 原因 |
|--------|-----|------|
| `hashFiles('Dockerfile') != ''` | 条件判断 | 无 Dockerfile 时优雅跳过 |
| `severity: CRITICAL,HIGH` | 过滤级别 | 聚焦可操作的高危发现 |
| `exit-code: "0"` | 不直接报错 | 由门禁 Job 统一做阻断决策 |

#### 修改扫描路径

如果 Dockerfile 不在根目录：

```yaml
if: hashFiles('**/Dockerfile') != ''
```

---

### 5. 代码质量

**Job ID：** `quality`
**运行环境：** `ubuntu-latest`

#### 作用

| 语言 | 工具 | 检查内容 |
|------|------|---------|
| Python | [Ruff](https://docs.astral.sh/ruff/) | 代码风格、常见错误、import 排序 |
| Node.js | [ESLint](https://eslint.org) | JS/TS 语法与最佳实践 |
| Go | [staticcheck](https://staticcheck.dev) | 静态分析、废弃 API、性能问题 |

#### 失败行为

- 发现 lint 错误即失败
- **默认不阻断合并**（未加入门禁 `needs` 的阻断条件）
- 如需阻断，将 `quality` 加入门禁的判断条件

#### Python Ruff 自定义

```toml
# pyproject.toml
[tool.ruff]
target-version = "py39"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

---

### 6. 安全门禁

**Job ID：** `gate` / `cast-gate`（GitLab）
**运行环境：** `ubuntu-latest`
**依赖：** `secrets`、`sast`、`sca`、`quality`

#### 作用

聚合所有安全 Job 的结果，通过 [conftest](https://conftest.dev) 对 SARIF 发现项
执行策略评估，做出统一的放行 / 阻断决策。

这是分支保护规则应当指向的 Job。

#### 执行流程

```
1. 下载所有 cast-sarif-* artifact（Semgrep、Trivy 输出）
2. 安装 conftest
3. 获取策略文件（本地 policy/ 目录优先，否则从 CAST repo 下载）
4. conftest 对 SARIF 文件执行策略评估
5. 检查非 SARIF 工具（Gitleaks、SCA）的 Job 状态
6. 任意检查失败 → exit 1，阻断合并
```

#### 策略选择

| `CAST_POLICY` 变量值 | 阻断条件 |
|---------------------|---------|
| `default`（默认） | CRITICAL（SARIF `"error"` 级别） |
| `strict` | CRITICAL + HIGH（`"error"` + `"warning"`） |
| `permissive` | 从不阻断（仅输出警告） |

详见 [策略参考](policy-reference.md)。

#### 门禁决策矩阵

| 秘密检测 | SAST（conftest） | SCA | 门禁结果 |
|---------|----------------|-----|---------|
| ✅ 通过 | ✅ 通过 | ✅ 通过 | ✅ 允许合并 |
| ❌ 失败 | 任意 | 任意 | ❌ 阻断合并 |
| 任意 | ❌ 策略违规 | 任意 | ❌ 阻断合并 |
| 任意 | 任意 | ❌ 失败 | ❌ 阻断合并 |

> 代码质量失败默认不阻断合并。

#### 配置分支保护

1. **Settings → Branches → Branch protection rules**
2. 添加 `main`（或 `master`）分支规则
3. 勾选 **"Require status checks to pass before merging"**
4. 搜索并添加 **"Security Gate"**
5. 可选：勾选 **"Require branches to be up to date before merging"**

---

## 权限配置

工作流申请最小所需权限：

```yaml
permissions:
  contents: read          # 拉取代码
  security-events: write  # 上传 SARIF 到 Security 标签页
  actions: read           # 读取工作流状态供门禁使用
```

不会授予对仓库内容的写入权限。

---

## 触发条件

默认触发器覆盖最常见场景：

```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:        # 可从 GitHub UI 手动触发
```

### 仅在 PR 时触发（节省 Actions 用量）

```yaml
on:
  pull_request:
    branches: [main, master]
  workflow_dispatch:
```

### 添加定时扫描（捕获新披露的 CVE）

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # 每天 UTC 06:00
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
```

---

## 自定义指南

### 修改 Trivy 扫描严重级别

```yaml
severity: CRITICAL,HIGH,MEDIUM   # 同时扫描 MEDIUM 及以上
```

### 跳过特定路径

```yaml
on:
  push:
    branches: [main, master]
    paths-ignore:
      - "docs/**"
      - "*.md"
```

### 门禁失败时发邮件通知

```yaml
gate:
  steps:
    # ... 现有步骤 ...
    - name: 失败通知
      if: failure()
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.example.com
        to: security-team@example.com
        subject: "CAST 安全门禁失败 — ${{ github.repository }}"
        body: "安全门禁在 ${{ github.ref }} 上失败"
```

### 使用严格策略（阻断 HIGH + CRITICAL）

在仓库 Variables 中设置：

```
CAST_POLICY=strict
```

---

## 故障排查

### Gitleaks 在测试夹具上误报

在仓库根目录添加 `.gitleaks.toml` 白名单（参见[秘密检测](#1-秘密检测)章节）。

### Semgrep SARIF 上传失败

确认 `permissions` 中设置了 `security-events: write`。这是 `github/codeql-action/upload-sarif` 的必要权限。

### pip-audit 找不到 requirements 文件

修改 SCA Job 的 `inputs` 参数：

```yaml
with:
  inputs: pyproject.toml
```

### 容器 Job 意外跳过

`hashFiles('Dockerfile')` 在文件不在根目录时返回空字符串。修改条件以匹配实际路径：

```yaml
if: hashFiles('**/Dockerfile') != ''
```

### conftest 门禁报告策略违规但不理解原因

本地复现：

```bash
# 安装 conftest
brew install conftest

# 下载默认策略
curl -o default.rego \
  https://raw.githubusercontent.com/castops/cast/main/policy/default.rego

# 对 SARIF 文件执行评估
conftest test your-scan.sarif --policy default.rego
```

详见 [策略参考](policy-reference.md)。

# CAST — CI/CD 自动化与安全工具包

<div align="center">

**复制。粘贴。生产级 DevSecOps 流水线。**

[![PyPI version](https://img.shields.io/pypi/v/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![Python](https://img.shields.io/pypi/pyversions/cast-cli.svg)](https://pypi.org/project/cast-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-ready-2088FF?logo=github-actions&logoColor=white)](https://github.com/castops/cast/actions)

[English](README.md) | 中文

</div>

---

CAST 是一套经过生产验证的 CI/CD 工作流模板集合，同时支持 **GitHub Actions** 和 **GitLab CI**。
一行命令，开箱即用，无需成为 DevSecOps 专家。

## 目录

- [为什么选择 CAST](#为什么选择-cast)
- [你能获得什么](#你能获得什么)
- [快速开始](#快速开始)
- [CLI 参考](#cli-参考)
- [模板矩阵](#模板矩阵)
- [流水线架构](#流水线架构)
- [安全看板](#安全看板)
- [参与贡献](#参与贡献)
- [许可证](#许可证)

---

## 为什么选择 CAST

大多数团队使用 6～20 个安全工具，却没有统一的流水线。
从零搭建 DevSecOps 意味着每个项目都要花几天时间研究、配置和调试。

CAST 将最佳实践打包成即用的工作流模板，第一天就能拥有生产级流水线。

- **零配置** — 自动检测技术栈和 CI 平台，一键写入工作流文件
- **安全优先** — 开箱即含秘密扫描、SAST、SCA 和容器扫描
- **策略即代码** — OPA/conftest 门禁替代脆弱的 Shell 逻辑，策略随仓库版本化
- **合规看板** — 静态 HTML 红绿灯看板，可部署到 GitHub Pages，零依赖
- **多平台** — GitHub Actions 与 GitLab CI 安全覆盖面完全一致

---

## 你能获得什么

每套 CAST 模板为你的仓库配置完整的安全技术栈：

| 检测层 | 工具 | 作用 |
|--------|------|------|
| 秘密检测 | [Gitleaks](https://github.com/gitleaks/gitleaks) | 扫描全量 git 历史，检测泄露的凭证 |
| SAST | [Semgrep](https://semgrep.dev) | 静态分析源码安全漏洞和不安全模式 |
| SCA | pip-audit / npm audit / govulncheck | 检测依赖中的已知 CVE |
| 容器安全 | [Trivy](https://trivy.dev) | 扫描 Docker 镜像 CVE（无 Dockerfile 时自动跳过） |
| 代码质量 | Ruff / ESLint / staticcheck | 代码规范与质量检查 |
| 安全门禁 | [conftest](https://conftest.dev) + OPA Rego | 策略驱动的门禁，阻断不合格的合并 |

所有发现直接呈现在 GitHub **Security 标签页**或 GitLab **安全仪表板**。
无需外部账号、无 SaaS 依赖。

---

## 快速开始

### 方式 A — CLI（推荐）

```bash
pip install cast-cli
cast init
```

CAST 自动检测项目类型和 CI 平台，一条命令搞定。

**GitLab 用户：**

```bash
cast init --platform gitlab
```

### 方式 B — 手动安装

```bash
# 创建工作流目录
mkdir -p .github/workflows

# 下载 Python 模板（替换 python 为 nodejs 或 go）
curl -o .github/workflows/devsecops.yml \
  https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/python/devsecops.yml

# 提交并推送
git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

**GitLab 用户（远程 include）：**

```yaml
# .gitlab-ci.yml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/gitlab/python/devsecops.yml'
```

---

## CLI 参考

### 安装

```bash
pip install cast-cli
```

### 命令

#### `cast init`

在当前目录初始化 DevSecOps 流水线。

```
使用方式: cast init [OPTIONS]

选项:
  -f, --force           强制覆盖已有工作流文件
  -t, --type TEXT       项目类型 (python/nodejs/go)，未指定时自动检测
  -p, --platform TEXT   CI 平台 (github/gitlab)，未指定时自动检测
  --help                显示帮助信息
```

**示例：**

```bash
# 自动检测项目类型和平台
cast init

# 指定 Node.js 项目
cast init --type nodejs

# 生成 GitLab CI 配置
cast init --platform gitlab

# Go 项目 + GitLab
cast init --type go --platform gitlab

# 覆盖已有工作流
cast init --force
```

**自动检测逻辑：**

| 项目类型 | 标记文件 |
|---------|---------|
| Python | `pyproject.toml`、`requirements.txt`、`setup.py`、`setup.cfg` |
| Node.js | `package.json` |
| Go | `go.mod` |

| CI 平台 | 检测依据 |
|---------|---------|
| GitLab | `.gitlab-ci.yml` 文件存在 |
| GitHub | `.github/` 目录存在（默认回退） |

#### `cast version`

显示已安装的 `cast-cli` 版本。

```bash
cast version
# cast 0.1.0
```

---

## 模板矩阵

### GitHub Actions

| 技术栈 | 安全工具 | 状态 |
|--------|---------|------|
| **Python** | Gitleaks + Semgrep + pip-audit + Trivy + Ruff | ✅ 可用 |
| **Node.js** | Gitleaks + Semgrep + npm audit + Trivy + ESLint | ✅ 可用 |
| **Go** | Gitleaks + Semgrep + govulncheck + Trivy + staticcheck | ✅ 可用 |

### GitLab CI

| 技术栈 | 安全工具 | 状态 |
|--------|---------|------|
| **Python** | Gitleaks + Semgrep + pip-audit + Trivy + Ruff | ✅ 可用 |
| **Node.js** | Gitleaks + Semgrep + npm audit + Trivy + ESLint | ✅ 可用 |
| **Go** | Gitleaks + Semgrep + govulncheck + Trivy + staticcheck | ✅ 可用 |

### 安全门禁策略

| 策略 | 阻断条件 | 启用方式 |
|------|---------|---------|
| `default` | CRITICAL 发现 | （默认） |
| `strict` | HIGH + CRITICAL | `CAST_POLICY=strict` |
| `permissive` | 从不阻断（仅审计） | `CAST_POLICY=permissive` |

详见 [策略参考](docs/zh/policy-reference.md)。

---

## 流水线架构

CAST 流水线并行运行五个安全扫描 Job，最后由门禁 Job 做出统一决策：

```
触发: push / pull_request / workflow_dispatch
│
├── 秘密检测  (Gitleaks)     ─┐
├── SAST      (Semgrep)       │ 并行运行
├── SCA       (pip-audit 等)  │
├── 容器安全  (Trivy)        ─┘
├── 代码质量  (Ruff 等)
│
└── 安全门禁  (conftest)     ← 等待以上 Job 完成
```

### 触发条件

| 事件 | 分支 |
|------|------|
| `push` | `main`、`master` |
| `pull_request` | `main`、`master` |
| `workflow_dispatch` | 任意（手动触发） |

### 门禁决策逻辑

```
IF conftest 检测到策略违规（默认：CRITICAL 发现）
  OR 秘密检测失败
  OR SCA 失败
→ 阻断合并（exit 1）
ELSE
→ 放行合并（exit 0）
```

> 代码质量失败（Ruff / ESLint / staticcheck）默认不阻断合并。

### SARIF 集成

Semgrep 和 Trivy 发现通过 SARIF 上传：

- 在 GitHub Security 标签页显示为代码扫描告警
- 在 Pull Request diff 上内联标注
- 跨 PR 保留历史记录，无需外部工具

---

## 安全看板

CAST 可生成静态 HTML 合规看板，管理层一眼看懂红绿灯状态：

```bash
python dashboard/generate.py --sarif-dir sarif-results --output index.html
```

通过内置工作流部署到 GitHub Pages：

```
templates/github/publish-dashboard.yml → .github/workflows/publish-dashboard.yml
```

详见 [看板指南](docs/zh/dashboard-guide.md)。

---

## 系统要求

- **GitHub** 或 **GitLab** 仓库，且 CI/CD 已启用
- **Python 3.9+**（使用 CLI 时需要）
- 无需其他账号、Token 或外部服务

> **可选：** 将 `SEMGREP_APP_TOKEN` 添加为仓库 Secret，以启用 Semgrep 云端
> Dashboard 和额外的规则集。

---

## 中文文档

| 文档 | 说明 |
|------|------|
| [快速开始](docs/zh/getting-started.md) | 五分钟接入指南 |
| [CLI 参考](docs/zh/cli-reference.md) | 命令行完整参考 |
| [流水线参考](docs/zh/pipeline-reference.md) | 各 Job 技术细节与自定义 |
| [GitLab 集成指南](docs/zh/gitlab-guide.md) | GitLab CI 专项说明 |
| [策略参考](docs/zh/policy-reference.md) | 自定义安全门禁策略 |
| [插件指南](docs/plugin-guide.md) | 接入自定义安全工具（英文） |
| [看板指南](docs/zh/dashboard-guide.md) | 静态 HTML 合规看板 |

---

## 参与贡献

欢迎贡献。详见 [CONTRIBUTING.md](CONTRIBUTING.md)：

- 开发环境搭建
- 添加新语言模板
- 运行测试
- 提交 Pull Request

---

## 安全

报告 CAST 自身的安全漏洞，请见 [SECURITY.md](SECURITY.md)。

---

## 设计理念

> 让非专家立即专业。

CAST 不是教程，而是 DevSecOps 最佳实践的可执行形式——
有主见、生产就绪，由每天运行这些流水线的人维护。

---

## 许可证

Apache 2.0 — 详见 [LICENSE](LICENSE)。

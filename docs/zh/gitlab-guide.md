# GitLab CI 集成指南

CAST 同时支持 GitLab CI 和 GitHub Actions，安全覆盖面完全一致。
使用 `cast init --platform gitlab` 生成 `.gitlab-ci.yml`，或通过 `include:` 一行引入整套流水线。

## 快速开始

### 方式 A — CLI

```bash
pip install castops
cast init --platform gitlab
```

CAST 自动检测项目类型并写入 `.gitlab-ci.yml`。

### 方式 B — 远程 include（零安装）

在你的 `.gitlab-ci.yml` 中添加：

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/gitlab/python/devsecops.yml'
```

将 `python` 替换为 `nodejs` 或 `go` 以匹配你的技术栈。

---

## 安装内容

流水线分两个 Stage 运行六个 Job：

| Stage | Job | 工具 | 是否阻断流水线 |
|-------|-----|------|--------------|
| `cast-scan` | `cast-secrets` | Gitleaks | 是（Job 失败即阻断） |
| `cast-scan` | `cast-sast` | Semgrep | 否（门禁评估） |
| `cast-scan` | `cast-sca` | pip-audit / npm audit / govulncheck | 是 |
| `cast-scan` | `cast-container` | Trivy | 否（门禁评估） |
| `cast-scan` | `cast-quality` | Ruff / ESLint / staticcheck | 否（仅提示） |
| `cast-gate` | `cast-gate` | conftest | 是 |

---

## GitLab 安全仪表板集成

Semgrep 结果通过 `reports.sast` artifact 类型上报——自动出现在
GitLab 的 **Security & Compliance → Security dashboard**。

Trivy 结果通过 `reports.container_scanning` 上报——在 Merge Request
的 **Container Scanning** 部件中展示。

---

## 策略自定义

门禁 Job 使用 [conftest](https://conftest.dev) 配合 OPA Rego 策略评估 SARIF 发现项。

**默认行为：** 发现任意 CRITICAL（SARIF `"error"` 级别）时阻断。

**覆盖策略**：在仓库中创建 `policy/` 目录：

```
policy/
  default.rego   ← CAST 优先使用本地策略
```

或在 GitLab CI/CD Variables 中设置 `CAST_POLICY`：

| 变量值 | 阻断条件 |
|--------|---------|
| `default`（默认） | 仅 CRITICAL |
| `strict` | CRITICAL + HIGH |
| `permissive` | 从不阻断 |

设置路径：**Settings → CI/CD → Variables → 添加变量**，Key: `CAST_POLICY`，Value: `strict`。

详见 [策略参考](policy-reference.md)。

---

## Merge Request 集成

在 Merge Request 触发时，流水线会：

1. 并行运行所有安全扫描
2. 将 Semgrep 发现内联显示在代码 diff 上
3. 在 MR 安全组件中展示容器扫描结果
4. 门禁 Job 失败时阻止 MR 合并

---

## 扩展流水线

由于模板使用了 `cast-` 前缀的 Stage 名（`cast-scan`、`cast-gate`），
你可以添加自己的 Stage 而不产生冲突：

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/gitlab/python/devsecops.yml'

stages:
  - cast-scan
  - cast-gate
  - test       # 你自己的 Stage
  - deploy

unit-tests:
  stage: test
  script: pytest

deploy-staging:
  stage: deploy
  script: ./deploy.sh
  environment: staging
```

---

## 与 GitHub Actions 的关键差异

| 特性 | GitHub Actions | GitLab CI |
|------|---------------|----------|
| 容器扫描 | 构建并扫描实际 Docker 镜像 | `trivy fs` 文件系统扫描（无需 Docker） |
| SARIF 上报 | GitHub Security 标签页 | GitLab 安全仪表板 |
| 策略变量 | Repository Variables | CI/CD Variables |
| 门禁触发 | `if: always()` | `when: always` |
| artifact 传递 | `actions/download-artifact` | `needs:` + `artifacts: true` |

---

## 故障排查

**`cast-sca` 失败：找不到 requirements 文件**

pip-audit 查找 `requirements*.txt`。如果只使用 `pyproject.toml`，可以覆盖该 Job：

```yaml
cast-sca:
  script:
    - pip install --quiet pip-audit
    - pip install -e .
    - pip-audit
```

**`cast-container` 运行但存在 Dockerfile**

该 Job 使用 `trivy fs`（文件系统扫描）而非构建并扫描镜像，因此不需要 Docker 守护进程。
如需扫描构建后的实际镜像，请使用 Docker-in-Docker 配置覆盖该 Job。

**门禁通过但安全仪表板有发现**

默认策略仅阻断 **CRITICAL**。设置 `CAST_POLICY: strict` 可同时阻断 HIGH 级别发现。

**想在本地测试策略**

```bash
brew install conftest

# 下载默认策略
curl -o default.rego \
  https://raw.githubusercontent.com/castops/cast/main/policy/default.rego

# 对 SARIF 文件评估
conftest test semgrep.sarif --policy default.rego
```

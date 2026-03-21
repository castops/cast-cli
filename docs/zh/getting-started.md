# CAST 快速开始

本指南带你在五分钟内为项目接入生产级 DevSecOps 流水线。

## 前置条件

- GitHub 或 GitLab 仓库，且 CI/CD 功能已启用
- Python 3.9+（仅使用 `cast` CLI 时需要）

无需外部账号、Token 或 SaaS 订阅。

---

## 第一步 — 安装 CLI

```bash
pip install cast-cli
```

验证安装：

```bash
cast --help
```

---

## 第二步 — 初始化流水线

进入项目根目录，执行：

```bash
cast init
```

CAST 自动检测项目类型和 CI 平台，然后写入工作流文件：

```
╭──────────────────────────────────────────────────╮
│ CAST — CI/CD Automation & Security Toolkit        │
╰──────────────────────────────────────────────────╯
Detected project type: python
Target platform:      github
Installing template... done

✓ Created .github/workflows/devsecops.yml

Commit and push to activate your DevSecOps pipeline:
  git add .github/workflows/devsecops.yml
  git commit -m 'ci: add CAST DevSecOps pipeline'
  git push
```

如果自动检测失败，可以手动指定：

```bash
# 指定项目类型
cast init --type nodejs

# 指定 CI 平台
cast init --platform gitlab

# 同时指定两者
cast init --type go --platform gitlab
```

---

## 第三步 — 提交并推送

```bash
git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

GitHub Actions 会立即拾取该工作流并运行首次流水线。

---

## 第四步 — 查看首次运行结果

1. 在 GitHub 打开你的仓库
2. 点击 **Actions** 标签页
3. 找到 **"CAST DevSecOps"** 运行记录

流水线并行运行六个 Job：

| Job | 工具 | 预期结果 |
|-----|------|---------|
| 秘密检测 | Gitleaks | 如 git 历史中无凭证则通过 |
| SAST | Semgrep | 使用开源规则；配置云端 Token 可获更多规则 |
| SCA | pip-audit / npm audit / govulncheck | 依赖无已知 CVE 则通过 |
| 容器安全 | Trivy | 无 Dockerfile 时跳过 |
| 代码质量 | Ruff / ESLint / staticcheck | 符合代码规范则通过 |
| 安全门禁 | conftest | 所有关键检查通过时放行 |

---

## 第五步 — 查看安全发现

Semgrep 和 Trivy 的发现会上传到 GitHub **Security 标签页**：

1. 仓库主页 → **Security** 标签
2. 点击 **"Code scanning alerts"**
3. 查看并处理各项发现

后续 Pull Request 上会有内联代码注释，指出具体问题行。

---

## 第六步 — 配置分支保护（推荐）

让安全门禁强制阻止不合格的 PR 合并：

1. **Settings → Branches → Add branch protection rule**
2. Branch name pattern 填写 `main`
3. 勾选 **"Require status checks to pass before merging"**
4. 搜索并添加 **"Security Gate"**
5. 保存规则

此后所有安全检查不合格的 PR 均无法合并。

---

## GitLab 用户

### 方式 A — CLI

```bash
cast init --platform gitlab
```

生成 `.gitlab-ci.yml` 文件，提交即可激活。

### 方式 B — 远程 include（零安装）

在你的 `.gitlab-ci.yml` 中添加一行：

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/gitlab/python/devsecops.yml'
```

将 `python` 替换为 `nodejs` 或 `go`。

详细说明见 [GitLab 集成指南](gitlab-guide.md)。

---

## 可选：调整安全策略

默认策略：**CRITICAL 漏洞 → 阻断合并**。

通过 `CAST_POLICY` 变量切换策略：

| 策略值 | 阻断条件 |
|--------|---------|
| `default` | 仅 CRITICAL（默认） |
| `strict` | CRITICAL + HIGH |
| `permissive` | 从不阻断（仅展示） |

**GitHub** 设置方式：Settings → Secrets and variables → Actions → Variables，新增 `CAST_POLICY=strict`。

**GitLab** 设置方式：Settings → CI/CD → Variables，新增 `CAST_POLICY=strict`。

详细说明见 [策略参考](policy-reference.md)。

---

## 可选：启用 Semgrep 云端

获取更多安全规则和集中化发现管理：

1. 注册 [semgrep.dev](https://semgrep.dev)（有免费套餐）
2. **Settings → Tokens** 创建 CI Token
3. 在仓库 Secrets 中添加 `SEMGREP_APP_TOKEN`

下次运行时流水线会自动使用云端 Token。

---

## 手动安装（无 CLI）

```bash
mkdir -p .github/workflows

# Python 项目
curl -o .github/workflows/devsecops.yml \
  https://raw.githubusercontent.com/castops/cast/main/src/cast_cli/templates/python/devsecops.yml

git add .github/workflows/devsecops.yml
git commit -m "ci: add CAST DevSecOps pipeline"
git push
```

将 `python` 替换为 `nodejs` 或 `go` 对应你的技术栈。

---

## 下一步

- [CLI 参考](cli-reference.md) — 全部命令选项
- [流水线参考](pipeline-reference.md) — 每个 Job 的技术细节与自定义方法
- [GitLab 集成指南](gitlab-guide.md) — GitLab CI 专项说明
- [策略参考](policy-reference.md) — 自定义安全门禁策略
- [看板指南](dashboard-guide.md) — 静态 HTML 合规看板

# 安全看板指南

CAST 能从 SARIF 扫描结果生成静态 HTML 合规看板，并发布到 GitHub Pages——
无需外部服务、无 SaaS 账号。

## 看板内容

每个 SARIF 文件在看板中占一行：

| 列 | 说明 |
|----|------|
| 项目 / 工具 | SARIF 文件名 + 生成该文件的工具 |
| 状态 | 🟢 PASS / 🔴 FAIL / 🟡 WARN |
| CRITICAL | SARIF `"error"` 级别发现数量 |
| HIGH | SARIF `"warning"` 级别发现数量 |
| MEDIUM | SARIF `"note"` 级别发现数量 |
| 明细 | 可展开的漏洞列表 |

页眉显示汇总统计和最后扫描的 commit SHA。

---

## 部署步骤

### 第一步 — 启用 GitHub Pages

仓库设置：**Settings → Pages → Source: GitHub Actions**

### 第二步 — 添加发布工作流

```bash
mkdir -p .github/workflows
curl -o .github/workflows/publish-dashboard.yml \
  https://raw.githubusercontent.com/castops/cast/main/templates/github/publish-dashboard.yml
```

或将 CAST 仓库中的文件复制过来：
```
templates/github/publish-dashboard.yml → .github/workflows/publish-dashboard.yml
```

### 第三步 — 复制看板脚本

```bash
mkdir -p dashboard
curl -o dashboard/generate.py \
  https://raw.githubusercontent.com/castops/cast/main/dashboard/generate.py
curl -o dashboard/template.html \
  https://raw.githubusercontent.com/castops/cast/main/dashboard/template.html
```

### 第四步 — 提交并推送

```bash
git add .github/workflows/publish-dashboard.yml dashboard/
git commit -m "ci: add CAST security dashboard"
git push
```

每次 CAST DevSecOps 流水线运行后，看板会自动发布。

---

## 工作原理

```
CAST DevSecOps 流水线
  ├── sast job      → 上传 cast-sarif-sast artifact     (semgrep.sarif)
  └── container job → 上传 cast-sarif-container artifact (trivy.sarif)

publish-dashboard 工作流（由 workflow_run 触发）
  ├── 下载所有 cast-sarif-* artifact
  ├── 执行 python dashboard/generate.py
  └── 将 _site/index.html 部署到 GitHub Pages
```

`workflow_run` 触发器确保看板只在完整流水线运行结束后发布，而非每次推送都触发。

---

## 本地生成看板

```bash
# 将 SARIF 文件放入 sarif-results/
mkdir -p sarif-results
cp path/to/semgrep.sarif sarif-results/
cp path/to/trivy.sarif sarif-results/

# 生成
python dashboard/generate.py

# 打开
open dashboard/index.html        # macOS
xdg-open dashboard/index.html    # Linux
```

**命令行选项：**

```
python dashboard/generate.py --help

  --sarif-dir DIR    包含 .sarif 文件的目录（默认：sarif-results）
  --output FILE      输出 HTML 路径（默认：dashboard/index.html）
  --commit SHA       在页眉中显示的 commit SHA
```

---

## 自定义看板外观

模板文件是 `dashboard/template.html`，纯 HTML + inline CSS，无需构建步骤。

修改颜色，编辑 `:root` 中的 CSS 变量：

```css
:root {
  --green: #3fb950;   /* PASS 状态颜色 */
  --red: #f85149;     /* FAIL 状态颜色 */
  --yellow: #d29922;  /* WARN 状态颜色 */
  --bg: #0d1117;      /* 背景色（深色主题） */
}
```

增加列（如扫描工具版本）：在 `generate.py` 中扩展数据结构，在模板的 `<th>` / `<td>` 中对应添加。

---

## 多仓库汇总看板

将多个仓库的发现汇总到一张看板：

1. 每个仓库上传 SARIF artifact 时使用唯一前缀：

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: cast-sarif-myrepo-sast
    path: semgrep.sarif
```

2. 在独立的 `dashboard` 仓库中，用 `gh run download` 或 GitHub API 下载各仓库的 artifact，
   然后统一运行 `generate.py`。

此方案需要持有各仓库 `actions:read` 权限的 GitHub Token。

---

## 状态说明

| 状态 | 条件 |
|------|------|
| 🔴 FAIL | 存在 CRITICAL 发现（SARIF `"error"` 级别） |
| 🟡 WARN | 存在 HIGH 发现（SARIF `"warning"` 级别），无 CRITICAL |
| 🟢 PASS | 无 CRITICAL 或 HIGH 发现 |

这与 `default` 策略的阻断逻辑保持对齐：FAIL → 门禁阻断，WARN 和 PASS → 门禁放行。
如启用 `strict` 策略，WARN 状态的扫描同样会阻断门禁。

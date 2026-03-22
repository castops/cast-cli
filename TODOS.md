# TODOS

## Design

### Create DESIGN.md
**What:** Run `/design-consultation` to document the dashboard's design system.
**Why:** `dashboard/template.html` uses GitHub-dark CSS tokens (`#0d1117`, `#58a6ff`, etc.) but this palette is implicit and undocumented. Without a reference, future contributors may introduce inconsistent colors.
**Pros:** Prevents design drift; gives future contributors a reference for new UI additions (e.g., multi-repo dashboard, dark/light toggle).
**Cons:** Minor time investment (~15 min).
**Context:** Design tokens live in the `:root` block of `dashboard/template.html`. The implicit system already has semantic naming (--critical-bg, --pass-bg, --high-bg) — DESIGN.md would formalize and explain these choices.
**Depends on:** None.

## Accessibility

### Verify color contrast ratios meet WCAG AA
**What:** Run a contrast checker on the muted text color (`#8b949e` on `#0d1117`).
**Why:** The computed contrast ratio is ~4.3:1, just below the WCAG AA threshold of 4.5:1 for normal text. Currently unverified.
**Pros:** Ensures the dashboard is legally and ethically accessible.
**Cons:** May require lightening `--muted` slightly, which could affect the visual balance.
**Context:** Affects all muted text: column headers, tool tags, timestamps, location paths in findings.
**Depends on:** None — can be done independently.

## Dashboard

### Parse-error state in generate.py
**What:** When a SARIF file exists but fails to parse, `generate.py` prints a warning to stderr but the HTML output never reflects the failure.
**Why:** A silently skipped SARIF file could cause false "ALL CLEAR" output — a serious trust issue for a security dashboard.
**Pros:** Users can distinguish "scan didn't run" from "scan file was malformed".
**Cons:** Requires adding a new row type (PARSE ERROR) to `render_table`.
**Context:** `parse_sarif()` returns `None` on failure; currently these `None` values are filtered out silently. Adding an error row would require passing the filename separately.
**Depends on:** None.

## CI / Quality

### yamllint 验证所有模板文件
**What:** 在 GitHub Actions CI 中对 `templates/**/*.yml` 运行 `yamllint`。
**Why:** 模板有语法错误时用户只能在 push 后才能发现；CI 内验证让模板作者立即得到反馈。
**Pros:** 防止破损模板被发布；成本极低（yamllint 单步，~30秒）。
**Cons:** 需要决定 yamllint 配置（relaxed 还是 strict，行长限制等）。
**Context:** 在 `.github/workflows/ci.yml` 中新增一个 job，或在现有工作流中添加步骤。yamllint 是 pip 可安装的命令行工具。
**Depends on:** None.

### templates/ 与 src/cast_cli/templates/ 自动同步检查
**What:** 添加 `scripts/check-template-sync.sh` 脚本，对比 `templates/` 和 `src/cast_cli/templates/` 内容，内容不一致则 exit 1；接入 CI。
**Why:** 已发生一次漂移（templates/ 文件被删除，嵌入式副本仍在），纯手动同步不可靠。
**Pros:** 防止 CLI 嵌入模板与 curl 下载模板静默不同步；每次 PR 自动验证。
**Cons:** 需要维护对比脚本（新增语言/平台时需更新）。
**Context:** 可用 `diff -r templates/python/ src/cast_cli/templates/python/` 对比；需跳过 `__init__.py` 和 `__pycache__`。
**Depends on:** None.

## CLI

### `cast validate` 命令（本期实施）
**What:** `cast validate <file.sarif>` — 本地验证 SARIF 2.1.0 格式，并预览 cast-gate 的拦截行为。
**Why:** 插件作者在推 PR 前需要知道自己生成的 SARIF 是否符合规范，以及 gate 会不会拦截。本地验证消除了"推了才知道"的反馈延迟。
**Pros:** 插件开发体验 ×10；无网络依赖；gate 行为透明化。
**Cons:** 需要内嵌 SARIF 2.1.0 JSON Schema（约 50KB），需跟踪 OASIS 更新。
**Context:** 输出示例：`✓ SARIF 有效 / 工具: Semgrep / 发现数: 12 (3 error) / 在 cast-gate 中: ❌ 3 个会被拦截`。exit code: 0=有效且gate放行, 1=格式错误, 2=有效但gate拦截。见 CEO 计划 2026-03-22。**注：** 原"验证 workflow 版本"功能已推迟，当前版本实施 SARIF 格式校验。
**Depends on:** policy/default.rego 已完成。

### `cast init` 检测失败时的交互式类型选择（本期实施）
**What:** 当 `detect_project()` 检测不到项目类型时，在 `cast init` 中提供交互式菜单让用户选择项目类型，而不是直接 `exit(1)`。
**Why:** 现在检测失败就直接 exit 并列出所有类型让用户手动重运行，对新用户体验较差。
**Pros:** 更好的新用户体验，减少摩擦，降低首次使用门槛。
**Cons:** 需要 TTY 检测（`sys.stdin.isatty()`）— 在 CI 非交互环境中继续 exit(1)，在终端中显示菜单。
**Context:** 参考 `git clone` 的 credential prompt 设计模式。在非 TTY 环境（CI）继续 exit(1) 是正确行为。多语言项目同样触发菜单（TTY）或 exit(1)（非 TTY）。
**Depends on:** 无。

### Gate: conftest Rego 语法错误检查步骤
**What:** 在 gate job 的 policy 评估前增加 `conftest parse --policy policy/` 语法校验步骤。
**Why:** conftest 对 Rego 语法错误和 policy 拒绝均返回 exit 1，无法区分。
**Pros:** CI 红灯时可区分"policy 拒绝"与"Rego 文件损坏"，降低调试成本。
**Cons:** 增加一个 gate 步骤（约 2 秒）。
**Context:** `conftest parse --policy policy/ || { echo "::error::Rego syntax error"; exit 3; }`。exit 3 = Rego 语法错误（与 exit 1 区分）。
**Priority:** P2
**Depends on:** policy/*.rego 文件存在。

### Gate: 必须 artifact 列表外部化配置
**What:** 将 `REQUIRED=(cast-sarif-sast cast-sarif-container)` 从 gate job YAML 硬编码改为可配置（环境变量）。
**Why:** 用户替换内置工具后需要修改 gate YAML，违反"不 fork 模板"的设计目标。
**Pros:** 插件接口真正灵活；用户可自定义 required artifact 集合。
**Cons:** 需要设计配置加载机制。
**Context:** 最简方案：`CAST_REQUIRED_ARTIFACTS` 环境变量，空格分隔。留待 Phase 2 配合 cast.yml 一起设计。
**Priority:** P3
**Depends on:** cast.yml 配置文件方案（Phase 3）。

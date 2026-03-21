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

### `cast validate` 命令
**What:** 一个 `cast validate` CLI 命令，验证已安装的工作流文件是否是最新版本的 CAST 模板。
**Why:** 现在用户安装后没有办法知道模板是否已过时。CAST 发布新模板版本后，用户无感知。模板升级管理是企业用户的核心需求。
**Pros:** 提升用户信任感，能吸引企业用户做模板升级管理，形成 `cast init` → `cast validate` 的完整生命周期。
**Cons:** 需要设计"模板版本"的查询机制（模板内嵌版本号 or 对比 hash），有一定设计复杂度。
**Context:** 起点：在模板 YAML 注释中加入版本标签（如 `# cast-version: 1.2.0`），`validate` 命令解析此标签并与当前最新版本比对。版本策略需先确定（跟随 cast-cli 包版本？独立版本？）。
**Depends on:** 模板版本化策略需先确定。

### `cast init` 检测失败时的交互式类型选择
**What:** 当 `detect_project()` 检测不到项目类型时，在 `cast init` 中提供交互式菜单让用户选择项目类型，而不是直接 `exit(1)`。
**Why:** 现在检测失败就直接 exit 并列出所有类型让用户手动重运行，对新用户体验较差。
**Pros:** 更好的新用户体验，减少摩擦，降低首次使用门槛。
**Cons:** 需要 TTY 检测（`sys.stdin.isatty()`）— 在 CI 非交互环境中继续 exit(1)，在终端中显示菜单。
**Context:** 参考 `git clone` 的 credential prompt 设计模式。在非 TTY 环境（CI）继续 exit(1) 是正确行为。
**Depends on:** 无。

# TODOS

## Design

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

## Phase 0 — 需求验证（实施门栅）

### Phase 0 用户采访 Go/No-Go 门栅
**What:** 在开始实施任何 Phase 2 代码之前，采访 2-3 名 DevOps 工程师。Go 标准：≥2 人说出"我现在无法强制执行 pipeline 标准"或等价表述。
**Why:** 治理层方向来自推断，而非直接用户反馈。Phase 2 是 Governance Suite（cast validate/doctor/score/fix/explain）——投入可观，需要真实需求验证支撑。
**Pros:** 低成本（1-2 小时）验证高成本（数天实施）投入的方向；若 No-Go 则改变方向，节省大量时间。
**Cons:** 延迟实施约 1-2 天。
**Context:** 目标采访对象：DevOps 工程师、技术负责人、小公司 CTO。关键问题："你现在如何保证团队的 CI/CD pipeline 符合你的标准？"接受标准：≥2 人提到无法强制执行、靠 code review 人肉检查、或"AI 随便生成"现象。No-Go 时重新评估方向。见设计文档 `sxp-main-design-20260322-093557.md`。
**Priority:** P0 — 所有 Phase 2 实施的前提。
**Depends on:** 无。

## Governance Suite (Phase 2) — 实施后续

### `cast fix` 备份文件加时间戳
**What:** `WorkflowPatcher` 在 `--apply` 时将备份文件名从 `.workflow.bak` 改为 `.workflow.bak.YYYYMMDDTHHMMSS`。
**Why:** 当前方案第二次运行 `--apply` 会静默覆盖原始备份，导致用户无法恢复到最初版本。
**Pros:** 防止数据丢失；实现极简（`datetime.now().strftime('%Y%m%dT%H%M%S')`）。
**Cons:** 多次运行会积累 bak 文件，需要用户手动清理（可接受）。
**Context:** 实施 `cast fix` 时直接采用时间戳方案，无需另立 PR。
**Priority:** P1 — 与 cast fix 同期实施。
**Depends on:** cast fix (Phase 2) 实施。

### `cast score --compare` 跨运行 delta 比较
**What:** 实现 `+15 from yesterday` 效果——将上次运行分数持久化到 `.cast-score.json`，下次运行时读取并展示 delta。
**Why:** CEO plan 明确包含此功能；delta 信息让分数从"快照"变为"趋势"，显著提升激励效果。
**Pros:** 用户能看到改进进度，增强使用动力；存储格式简单（JSON）。
**Cons:** 需要设计存储位置（项目根目录 vs `~/.cast/`）和格式；首次运行无 delta 时的 UX 设计。
**Context:** 存储方案候选：项目根目录 `.cast-score.json`（与项目绑定）vs `~/.cast/{repo-slug}.json`（全局）。需要在 Phase 2 设计时决定，避免后期迁移。
**Priority:** P2 — Phase 2 后续迭代。
**Depends on:** cast score (Phase 2) 基础实施完成。

## Completed

### Create DESIGN.md
**What:** Run `/design-consultation` to document the project's design system (Industrial Editorial aesthetic).
**Completed:** v0.1.1 (2026-03-24) — `DESIGN.md` created with full token set: Fraunces/Instrument Sans typography, `#0D0C0B`/`#CBFF2E` palette, spacing scale, and layout rules.

### Redesign website (EN + ZH) per DESIGN.md
**What:** Apply the Industrial Editorial design system to `website/index.html` and `website/zh/index.html`.
**Completed:** v0.1.1 (2026-03-24) — Both pages fully redesigned. Fixed navigation links, SEO meta tags, cross-browser compat, and mobile responsive nav.

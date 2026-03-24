#!/usr/bin/env python3
"""Build documentation HTML from Markdown source files.

Reads Markdown from docs/ and docs/zh/, wraps each page in the shared
site template, and writes HTML to website/docs/ and website/zh/docs/.

Usage:
    pip install markdown
    python scripts/build_docs.py
"""

import pathlib
import re
import sys

try:
    import markdown
except ImportError:
    print("ERROR: 'markdown' package not installed.  Run: pip install markdown", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
WEBSITE_DIR = REPO_ROOT / "website"

# ---------------------------------------------------------------------------
# Per-page metadata
# ---------------------------------------------------------------------------

# slug -> (html_title, breadcrumb_label)
EN_PAGES: dict[str, tuple[str, str]] = {
    "getting-started":  ("Getting Started — CAST",        "Getting Started"),
    "cli-reference":    ("CLI Reference — CAST",           "CLI Reference"),
    "pipeline-reference": ("Pipeline Reference — CAST",    "Pipeline Reference"),
    "policy-reference": ("Policy Reference — CAST",        "Policy Reference"),
    "dashboard-guide":  ("Security Dashboard Guide — CAST","Security Dashboard Guide"),
    "plugin-guide":     ("Plugin Guide — CAST",            "Plugin Guide"),
    "gitlab-guide":     ("GitLab CI Guide — CAST",         "GitLab CI Guide"),
}

ZH_PAGES: dict[str, tuple[str, str]] = {
    "getting-started":  ("快速入门 — CAST",      "快速入门"),
    "cli-reference":    ("CLI 参考 — CAST",       "CLI 参考"),
    "pipeline-reference": ("流水线参考 — CAST",   "流水线参考"),
    "policy-reference": ("策略参考 — CAST",       "策略参考"),
    "dashboard-guide":  ("安全看板指南 — CAST",   "安全看板指南"),
    "plugin-guide":     ("插件指南 — CAST",       "插件指南"),
    "gitlab-guide":     ("GitLab CI 指南 — CAST", "GitLab CI 指南"),
}

# ---------------------------------------------------------------------------
# Sidebar structure  (section_label, [(slug, link_label), ...])
# ---------------------------------------------------------------------------

EN_SIDEBAR = [
    ("Documentation", [
        ("getting-started", "Getting Started"),
    ]),
    ("Reference", [
        ("cli-reference",     "CLI Reference"),
        ("pipeline-reference","Pipeline Reference"),
        ("policy-reference",  "Policy Reference"),
    ]),
    ("Guides", [
        ("gitlab-guide",    "GitLab CI"),
        ("dashboard-guide", "Security Dashboard"),
        ("plugin-guide",    "Plugin Guide"),
    ]),
]

ZH_SIDEBAR = [
    ("文档", [
        ("getting-started", "快速入门"),
    ]),
    ("参考", [
        ("cli-reference",     "CLI 参考"),
        ("pipeline-reference","流水线参考"),
        ("policy-reference",  "策略参考"),
    ]),
    ("指南", [
        ("gitlab-guide",    "GitLab CI"),
        ("dashboard-guide", "安全看板"),
        ("plugin-guide",    "插件指南"),
    ]),
]

# ---------------------------------------------------------------------------
# Shared CSS (identical to the original hand-crafted pages)
# ---------------------------------------------------------------------------

CSS = """\
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #1c2128;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
      --green: #3fb950;
      --red: #f85149;
      --yellow: #d29922;
      --blue: #58a6ff;
      --purple: #bc8cff;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 15px;
      line-height: 1.6;
    }

    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }

    nav {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(13,17,23,0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }
    .nav-inner {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 24px;
      height: 60px;
      display: flex;
      align-items: center;
      gap: 32px;
    }
    .nav-logo {
      font-weight: 700;
      font-size: 16px;
      color: var(--text);
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .nav-links {
      display: flex;
      gap: 24px;
      flex: 1;
    }
    .nav-links a {
      font-size: 14px;
      color: var(--muted);
      text-decoration: none;
      transition: color 0.15s;
    }
    .nav-links a:hover { color: var(--text); }
    .nav-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
    .lang-switch {
      display: flex;
      align-items: center;
      gap: 2px;
      font-size: 13px;
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }
    .lang-switch a {
      padding: 4px 10px;
      color: var(--muted);
      background: transparent;
      transition: color 0.15s, background 0.15s;
      text-decoration: none;
    }
    .lang-switch a:hover { color: var(--text); background: var(--surface); }
    .lang-switch a.active { color: var(--text); background: var(--surface2); }
    .btn-ghost {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 13px;
      color: var(--text);
      text-decoration: none;
      background: transparent;
      transition: border-color 0.15s, background 0.15s;
    }
    .btn-ghost:hover { background: var(--surface); border-color: var(--muted); text-decoration: none; }

    .doc-layout {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 24px 80px;
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 48px;
      align-items: start;
    }
    @media (max-width: 760px) {
      .doc-layout { grid-template-columns: 1fr; }
      .sidebar { display: none; }
    }

    .sidebar {
      position: sticky;
      top: 80px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px 0;
    }
    .sidebar-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      padding: 12px 16px 4px;
    }
    .sidebar a {
      display: block;
      padding: 6px 16px;
      font-size: 14px;
      color: var(--muted);
      text-decoration: none;
      border-left: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s;
    }
    .sidebar a:hover { color: var(--text); }
    .sidebar a.active { color: var(--blue); border-left-color: var(--blue); background: rgba(88,166,255,0.05); }

    .doc-content { min-width: 0; }
    .doc-content h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
    .doc-content h2 { font-size: 20px; font-weight: 600; margin: 40px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
    .doc-content h3 { font-size: 16px; font-weight: 600; margin: 28px 0 10px; color: var(--text); }
    .doc-content h4 { font-size: 14px; font-weight: 600; margin: 20px 0 8px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .doc-content p { margin-bottom: 16px; line-height: 1.7; }
    .doc-content ul, .doc-content ol { margin: 0 0 16px 20px; }
    .doc-content li { margin-bottom: 6px; line-height: 1.6; }
    .doc-content code {
      font-family: "SF Mono", "Fira Code", "Cascadia Code", monospace;
      font-size: 13px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 2px 6px;
      color: var(--purple);
    }
    .doc-content pre {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px 20px;
      overflow-x: auto;
      margin-bottom: 20px;
    }
    .doc-content pre code {
      background: none;
      border: none;
      padding: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.6;
    }
    .doc-content table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }
    .doc-content th { background: var(--surface2); text-align: left; padding: 10px 14px; font-weight: 600; border-bottom: 2px solid var(--border); }
    .doc-content td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
    .doc-content tr:last-child td { border-bottom: none; }
    .doc-content hr { border: none; border-top: 1px solid var(--border); margin: 40px 0; }
    .doc-content blockquote {
      border-left: 3px solid var(--yellow);
      background: rgba(210,153,34,0.08);
      border-radius: 0 6px 6px 0;
      padding: 12px 16px;
      margin: 0 0 16px;
      color: var(--muted);
      font-size: 14px;
    }
    .doc-content a { color: var(--blue); }
    .doc-content a:hover { text-decoration: underline; }
    .doc-content strong { font-weight: 600; color: var(--text); }

    .breadcrumb {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 24px;
    }
    .breadcrumb a { color: var(--muted); text-decoration: none; }
    .breadcrumb a:hover { color: var(--text); }
    .breadcrumb .sep { color: var(--border); }

    footer {
      border-top: 1px solid var(--border);
      padding: 32px 24px;
      text-align: center;
      font-size: 13px;
      color: var(--muted);
    }
    footer a { color: var(--muted); text-decoration: none; }
    footer a:hover { color: var(--text); }"""

GITHUB_SVG = (
    '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59'
    ".4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49"
    "-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53"
    ".63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87"
    ".51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
    "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27"
    " 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1"
    ".16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65"
    " 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15"
    '.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
)

# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------


def _render_sidebar(sidebar: list, active_slug: str) -> str:
    parts: list[str] = ['  <aside class="sidebar">']
    for section_label, items in sidebar:
        parts.append(f'      <div class="sidebar-label">{section_label}</div>')
        for slug, label in items:
            active = ' class="active"' if slug == active_slug else ""
            parts.append(f'      <a href="{slug}.html"{active}>{label}</a>')
    parts.append("    </aside>")
    return "\n".join(parts)


def _render_nav_en(slug: str) -> str:
    return f"""\
  <nav>
    <div class="nav-inner">
      <a class="nav-logo" href="../">
        <span>🛡️</span> CAST
      </a>
      <div class="nav-links">
        <a href="../#how-it-works">How it works</a>
        <a href="../#templates">Templates</a>
        <a href="getting-started.html">Docs</a>
        <a href="https://github.com/castops/cast/blob/main/CHANGELOG.md">Changelog</a>
      </div>
      <div class="nav-right">
        <div class="lang-switch">
          <a href="./" class="active">EN</a>
          <a href="../zh/">中文</a>
        </div>
        <a class="btn-ghost" href="https://github.com/castops/cast">
          {GITHUB_SVG}
          GitHub
        </a>
      </div>
    </div>
  </nav>"""


def _render_nav_zh(slug: str) -> str:
    return f"""\
  <nav>
    <div class="nav-inner">
      <a class="nav-logo" href="../../zh/">
        <span>🛡️</span> CAST
      </a>
      <div class="nav-links">
        <a href="../../zh/#how-it-works">工作原理</a>
        <a href="../../zh/#templates">模板</a>
        <a href="getting-started.html">文档</a>
        <a href="https://github.com/castops/cast/blob/main/CHANGELOG.md">更新日志</a>
      </div>
      <div class="nav-right">
        <div class="lang-switch">
          <a href="../../docs/{slug}.html">EN</a>
          <a href="./{slug}.html" class="active">中文</a>
        </div>
        <a class="btn-ghost" href="https://github.com/castops/cast">
          {GITHUB_SVG}
          GitHub
        </a>
      </div>
    </div>
  </nav>"""


def _render_breadcrumb_en(label: str) -> str:
    return f"""\
      <div class="breadcrumb">
        <a href="../">CAST</a>
        <span class="sep">/</span>
        <span>Docs</span>
        <span class="sep">/</span>
        <span>{label}</span>
      </div>"""


def _render_breadcrumb_zh(label: str) -> str:
    return f"""\
      <div class="breadcrumb">
        <a href="../../zh/">CAST</a>
        <span class="sep">/</span>
        <span>文档</span>
        <span class="sep">/</span>
        <span>{label}</span>
      </div>"""


def _md_to_html(md_text: str) -> str:
    """Convert Markdown text to an HTML fragment."""
    extensions = ["tables", "fenced_code"]
    body = markdown.markdown(md_text, extensions=extensions)
    # Rewrite bare *.md links to *.html (internal cross-doc links)
    body = re.sub(r'href="([^"#/][^"]*?)\.md"', r'href="\1.html"', body)
    return body


def render_page(
    *,
    lang: str,
    slug: str,
    title: str,
    breadcrumb_label: str,
    sidebar: list,
    body_html: str,
) -> str:
    html_lang = "zh-CN" if lang == "zh" else "en"
    nav = _render_nav_zh(slug) if lang == "zh" else _render_nav_en(slug)
    breadcrumb = (
        _render_breadcrumb_zh(breadcrumb_label)
        if lang == "zh"
        else _render_breadcrumb_en(breadcrumb_label)
    )
    sidebar_html = _render_sidebar(sidebar, slug)

    return f"""\
<!DOCTYPE html>
<html lang="{html_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
{CSS}
  </style>
</head>
<body>

{nav}

  <div class="doc-layout">

{sidebar_html}

    <main class="doc-content">
{breadcrumb}

{body_html}
    </main>

  </div>

  <footer>
    <p>CAST — CI/CD Automation &amp; Security Toolkit &nbsp;·&nbsp; <a href="https://github.com/castops/cast">GitHub</a> &nbsp;·&nbsp; <a href="https://github.com/castops/cast/blob/main/LICENSE">MIT License</a></p>
  </footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_lang(
    *,
    lang: str,
    source_dir: pathlib.Path,
    output_dir: pathlib.Path,
    pages: dict[str, tuple[str, str]],
    sidebar: list,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    built = 0
    for slug, (title, breadcrumb_label) in pages.items():
        md_path = source_dir / f"{slug}.md"
        if not md_path.exists():
            print(f"  WARNING: {md_path} not found — skipping", file=sys.stderr)
            continue

        md_text = md_path.read_text(encoding="utf-8")
        body_html = _md_to_html(md_text)

        html = render_page(
            lang=lang,
            slug=slug,
            title=title,
            breadcrumb_label=breadcrumb_label,
            sidebar=sidebar,
            body_html=body_html,
        )

        out_path = output_dir / f"{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  wrote {out_path.relative_to(REPO_ROOT)}")
        built += 1

    print(f"  {built} page(s) built for lang={lang!r}")


def main() -> None:
    print("Building English docs …")
    build_lang(
        lang="en",
        source_dir=DOCS_DIR,
        output_dir=WEBSITE_DIR / "docs",
        pages=EN_PAGES,
        sidebar=EN_SIDEBAR,
    )

    print("Building Chinese docs …")
    build_lang(
        lang="zh",
        source_dir=DOCS_DIR / "zh",
        output_dir=WEBSITE_DIR / "zh" / "docs",
        pages=ZH_PAGES,
        sidebar=ZH_SIDEBAR,
    )

    print("Done.")


if __name__ == "__main__":
    main()

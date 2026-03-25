# Design System — CastOps

## Product Context
- **What this is:** An open-source platform engineering suite for the AI-native era, comprising Cast CLI (DevSecOps governance) and Cast Slice (GPU FinOps engine for Kubernetes)
- **Who it's for:** Platform engineers, DevOps/MLOps engineers, and AI infrastructure teams — technical, opinionated people who run clusters and care deeply about operational efficiency
- **Space/industry:** DevOps / platform tooling; peers include Pulumi, Railway, Fly.io, Grafana, Warp
- **Project type:** Marketing/documentation website
- **License:** Apache 2.0 (open source)

## Aesthetic Direction
- **Direction:** Industrial Editorial
- **Decoration level:** Intentional — signal lines, grid fragments, annotated diagrams, structural rule marks
- **Mood:** An operations room designed by someone who also reads *Monocle*. Not glassy, not neon. Machined surfaces, operator confidence, the energy of a flight operations center that happens to be beautifully typeset. Every design choice signals: "these people run clusters and have taste."
- **Anti-patterns (never use):** Purple/violet gradients, 3-column icon feature grids, centered-everything hero layouts, generic stock developer illustrations, glassmorphism cards, decorative blobs, gradient buttons as primary CTA, fake dashboards full of meaningless charts

## Typography

- **Display/Hero:** [Fraunces](https://fonts.google.com/specimen/Fraunces) — high-contrast editorial serif; in a zero-serif DevOps category, this creates instant visual differentiation and signals authority before a word is read. Use at 72–100px, -0.03em letter-spacing, weight 900
- **Body:** [Instrument Sans](https://fonts.google.com/specimen/Instrument+Sans) — technical clarity with more character than default SaaS grotesks; 16–18px, 1.65 line-height
- **UI/Labels:** Instrument Sans (same as body), 13–14px, weight 600, uppercase with 0.06em tracking for labels
- **Data/Tables:** [IBM Plex Sans Condensed](https://fonts.google.com/specimen/IBM+Plex+Sans+Condensed) — compact, operational, excellent for dense infrastructure content; must use `font-variant-numeric: tabular-nums` for all numeric values
- **Code/Terminal:** [Berkeley Mono](https://berkeleygraphics.com/typefaces/berkeley-mono/) — the best monospace typeface of the last decade; has weight and personality. Requires a commercial license. Use [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) as a free fallback
- **Loading:** Google Fonts CDN for Fraunces, Instrument Sans, IBM Plex Sans Condensed, JetBrains Mono. Berkeley Mono self-hosted after licensing.
- **Scale:**
  | Level | Size | Usage |
  |-------|------|-------|
  | display-2xl | 88–100px | Hero headline (Fraunces) |
  | display-xl | 64–88px | Section openers (Fraunces) |
  | display-lg | 48–64px | Major subheads (Fraunces) |
  | display-md | 32–48px | Card titles (Fraunces) |
  | body-lg | 18px | Marketing prose (Instrument Sans) |
  | body-md | 16px | Docs body (Instrument Sans) |
  | body-sm | 14px | Secondary descriptions (Instrument Sans) |
  | label | 11–12px | Uppercase labels (IBM Plex Sans Condensed, weight 700, 0.1em tracking) |
  | code | 12.5–14px | Terminal / config blocks (Berkeley Mono / JetBrains Mono) |

## Color

- **Approach:** Restrained — the accent is rare and high-value; most of the site lives in graphite and ash tones
- **Background:** `#0D0C0B` — near-black with warmth stripped of blue; feels like matte metal, not a generic dark-mode SaaS clone
- **Surface:** `#171614` — for cards, panels, sidebars, terminal backgrounds
- **Surface Elevated:** `#1F1D1B` — for dropdowns, tooltips, modal backgrounds
- **Border/Hairline:** `#2A2723` — just enough to see the edge without a bright line
- **Primary Text:** `#EDE9E3` — warm off-white; pure white on this background is aggressive and cheap
- **Secondary Text:** `#B5AFA8` — for descriptions, supporting copy
- **Muted Text:** `#7A736C` — for metadata, timestamps, labels, placeholder text
- **Primary Accent:** `#CBFF2E` — electric chartreuse; the color of a GPU under load on a thermal camera. Nothing in DevOps tooling uses this color. Reserve for: CTAs, active states, key metrics, hover highlights, the single brand moment per section
- **Secondary Accent:** `#E87C3E` — construction/engineering orange; for warnings, cost anomalies, "this matters right now" states
- **Semantic:**
  | Role | Hex | Usage |
  |------|-----|-------|
  | Success | `#7DFA9B` | Passing checks, healthy nodes, cost savings |
  | Warning | `#FFBF47` | Idle nodes, policy warnings, approaching limits |
  | Danger  | `#FF6B57` | Failed checks, blocked deployments, critical alerts |
  | Info    | `#63C7FF` | Informational banners, doc notes |
- **Dark mode:** This IS the dark mode. The base palette is dark.
- **Light mode:** Invert to warm off-white base (`#F5F3EF`), surface white (`#FFFFFF`), adjust accent to `#6B8B00` (darker chartreuse for contrast on light). Keep the same type system.

## Spacing

- **Base unit:** 8px
- **Density:** Comfortable-dense — platform engineers can handle information density; sparse layouts signal "made for non-technical stakeholders"
- **Scale:**
  | Token | Value | Usage |
  |-------|-------|-------|
  | 2xs | 2px | Micro gaps, hairlines |
  | xs | 4px | Icon-to-label, tight pairs |
  | sm | 8px | Component internal padding |
  | md | 16px | Standard padding, card internal |
  | lg | 24px | Section-internal gaps |
  | xl | 32px | Between subsections |
  | 2xl | 48px | Between major sections |
  | 3xl | 64px | Hero padding, section separation |
  | 4xl | 96px | Page-level section padding |

## Layout

- **Approach:** Creative-editorial — left-anchored, asymmetric composition; the hero must not look like a document
- **Grid:** 12-column; max content width 1160px; 40px gutters on desktop, 20px on mobile
- **Hero composition:** Left 55% carries the headline (high-left anchor, not centered) and CTA row; right 45% carries a live product tableau (terminal + pipeline visualization). A diagonal structural line or clipped panel edge cuts through for motion.
- **Section rhythm:** Alternate dense content blocks with more open ones. Mix editorial prose blocks with operator-console data modules.
- **Max content width:** 1160px
- **Border radius:**
  | Token | Value | Usage |
  |-------|-------|-------|
  | sm | 4px | Buttons, tags, code tokens |
  | md | 8px | Cards, terminal windows, inputs |
  | lg | 12px | Modals, dialogs |
  | full | 9999px | Pills, avatars |

## Motion

- **Approach:** Intentional — only transitions that aid comprehension; no decorative scroll animations
- **Easing:** enter: `ease-out` / exit: `ease-in` / move: `ease-in-out`
- **Duration:**
  | Token | Range | Usage |
  |-------|-------|-------|
  | micro | 50–100ms | Hover states, focus rings |
  | short | 150–250ms | Button feedback, menu open |
  | medium | 250–400ms | Panel transitions, accordion |
  | long | 400–700ms | Page transitions, terminal line animation |
- **Permitted motion:** Terminal line input animation, number counter rollup on stats, status indicator pulse for active nodes
- **Forbidden motion:** Scroll-triggered entrance animations on marketing copy, parallax backgrounds, looping decorative animations

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-24 | Initial design system created | Created by /design-consultation. Research covered Railway, Fly.io, Pulumi, Warp, and Grafana. Outside voices: Codex (GPT-5.4) and Claude subagent both independently converged on industrial/editorial direction and chartreuse accent. |
| 2026-03-24 | Fraunces as display font (Risk #1) | Every competitor uses grotesque sans-serifs. In a zero-serif category, editorial serif = instant visual differentiation and psychological authority before a word is read. |
| 2026-03-24 | Accent color #CBFF2E — electric chartreuse (Risk #2) | GPU thermal imaging color. Not blue, not purple, not teal. Nothing in DevOps tooling looks like this. Must be used sparingly (rare = valuable). |
| 2026-03-24 | Information-dense layout (Risk #3) | Target users are platform engineers who handle data density daily. Sparse layouts pre-screen for the wrong audience. |
| 2026-03-24 | Background warm near-black #0D0C0B instead of cool graphite | Cool gray (#0B0F10) reads as generic dark-mode SaaS. Warm near-black feels like matte metal — more physical, more material. |

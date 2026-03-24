# CLAUDE.md — CastOps Project Instructions

## Design System
Always read `DESIGN.md` before making any visual or UI decisions.
All font choices, colors, spacing, border-radius, and aesthetic direction are defined there.
Do not deviate without explicit user approval.

Key rules:
- **Display font:** Fraunces (serif) — never substitute with Inter, Roboto, or other grotesks without approval
- **Accent color:** `#CBFF2E` (electric chartreuse) — use sparingly; this is a high-value signal color, not a background fill
- **Background:** `#0D0C0B` (warm near-black) — not cool gray, not pure black
- **Aesthetic:** Industrial Editorial — asymmetric, left-anchored, operator-console energy
- **Never:** purple gradients, 3-column icon grids, centered hero with floating CTA, glassmorphism, decorative blobs

In QA mode, flag any code that doesn't match `DESIGN.md` — including font substitutions, off-palette colors, or layout patterns that conflict with the defined aesthetic.

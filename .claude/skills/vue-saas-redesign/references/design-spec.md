# SaaS design spec

The target look: calm, dense-but-airy business software (think Linear, Vercel, Stripe dashboard). Few colors, consistent rhythm, clear hierarchy, quiet borders instead of heavy shadows.

## Contents
1. Tokens
2. Shell layout
3. Sidebar
4. Content header
5. Components
6. Responsive behavior
7. Accessibility
8. Review checklist

---

## 1. Tokens

Define on `:root` in the global stylesheet. Names below are suggestions; if the project already has tokens, extend them instead of adding a parallel set.

**Spacing (4 px base)** — every padding, margin and gap should land on this scale:

| Token | Value | Typical use |
|---|---|---|
| `--space-1` | 4px | icon-to-text gap, badge padding-y |
| `--space-2` | 8px | tight stacks, nav item padding-y |
| `--space-3` | 12px | control padding-x, table cell padding-y |
| `--space-4` | 16px | card inner gaps, table cell padding-x |
| `--space-5` | 20px | card padding (compact) |
| `--space-6` | 24px | card padding, grid gaps, content padding (mobile) |
| `--space-8` | 32px | content padding (desktop), section gaps |
| `--space-12` | 48px | large section separation |

**Type scale** — system font stack unless the app already loads a font:

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `--text-xs` | 12 / 16 | 500 | badges, table headers (uppercase, +0.04em tracking) |
| `--text-sm` | 13 / 20 | 400–500 | nav items, table body, secondary text |
| `--text-base` | 14 / 22 | 400 | body, inputs, buttons |
| `--text-lg` | 16 / 24 | 600 | card titles |
| `--text-xl` | 20 / 28 | 600 | section titles |
| `--text-2xl` | 24 / 32 | 600 | page title |
| `--text-3xl` | 30 / 36 | 600 | KPI numbers |

Use `font-variant-numeric: tabular-nums` for numbers in tables and KPIs so columns align.

**Radius**: `--radius-sm` 6px (inputs, buttons, badges), `--radius-md` 8px (cards, menus), `--radius-lg` 12px (modals, large panels). Pills (`999px`) only for status badges or toggles.

**Elevation**: borders do most of the work. `--shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05)` for cards; `--shadow-md: 0 4px 12px rgb(0 0 0 / 0.08)` for dropdowns and popovers; `--shadow-lg` for modals only.

**Color roles** (map the app's existing colors onto these):

| Role | Purpose |
|---|---|
| `--color-bg` | app background behind content (slightly off-white) |
| `--color-surface` | cards, sidebar, header (white) |
| `--color-surface-muted` | table header, hover rows, input backgrounds |
| `--color-border` | 1px dividers and card borders |
| `--color-text` | primary text |
| `--color-text-muted` | secondary text, labels, inactive nav |
| `--color-accent` | primary buttons, active nav, links, focus ring |
| `--color-accent-soft` | active nav background, selected rows (accent at ~8–12% opacity) |
| `--color-success` / `-info` / `-warning` / `-danger` | status text; each with a `-soft` background |

**Neutral fallback** (only when the app has no palette of its own): bg `#f8fafc`, surface `#ffffff`, surface-muted `#f1f5f9`, border `#e2e8f0`, text `#0f172a`, text-muted `#64748b`, accent `#2563eb`, success `#16a34a`, info `#2563eb`, warning `#d97706`, danger `#dc2626`.

**Sizes**: `--sidebar-width: 248px`, `--sidebar-width-collapsed: 64px`, `--header-height: 56px`, `--content-max-width: 1440px`.

## 2. Shell layout

```
+------------+--------------------------------------------+
|  Logo      |  Page title            [filters] [lang] [@]|  <- content header (sticky)
|            +--------------------------------------------+
|  Nav item  |                                            |
|  Nav item  |   content (max-width, centered, padded)    |
|  Nav item  |                                            |
|  ...       |                                            |
|            |                                            |
|  ---       |                                            |
|  Profile   |                                            |
+------------+--------------------------------------------+
```

- Root: CSS Grid `grid-template-columns: var(--sidebar-width) 1fr`, `min-height: 100vh`.
- Sidebar: `position: sticky; top: 0; height: 100vh; overflow-y: auto`, so the nav stays put while content scrolls.
- Main column: content header, then an optional global toolbar (for example a filter bar), then `<router-view>` inside a container with `max-width: var(--content-max-width)`, `padding: var(--space-8)`, `margin: 0 auto`.
- Page background `--color-bg`; cards sit on it as `--color-surface` with a 1px border. This contrast is what makes the layout read as "SaaS".

## 3. Sidebar

**Structure (top to bottom)**: brand block (logo or app name + optional subtitle, aligned with the header height) → primary nav → optional secondary group with a small uppercase label → spacer → footer (user/profile menu or settings).

**Nav item**:
- Full-width row, `height: 36px`, `padding: 0 var(--space-3)`, `gap: var(--space-3)`, `border-radius: var(--radius-sm)`, `margin: 0 var(--space-3)`.
- 16–18px icon (inline SVG, `stroke="currentColor"`, 1.5–2 stroke width) + label at `--text-sm` weight 500.
- Default: `--color-text-muted`. Hover: `--color-surface-muted` background, `--color-text`.
- **Active**: `--color-accent-soft` background, `--color-accent` text and icon. Set `aria-current="page"`. Match nested routes too (a path that starts with the item's path), but make the root `/` match exactly.
- Use `<router-link>`, not `<a href>`, so navigation stays client-side.

**Icons**: draw simple 24×24 stroke icons inline (a small `NavIcon` component with a `name` prop and a `switch` over paths works well). Pick obvious metaphors: grid for overview/dashboard, box for inventory, receipt/list for orders, wallet/credit card for finance, trending-up line for forecasts, bar chart for reports, refresh/cart for restocking. Keep them all the same size and stroke weight; mixed icon styles look worse than no icons.

**Separation**: the sidebar is `--color-surface` with a 1px right border. No heavy shadow.

## 4. Content header

- Height `--header-height`, `padding: 0 var(--space-8)`, 1px bottom border, `--color-surface` background, `position: sticky; top: 0; z-index` above content.
- Left: the current page title at `--text-lg`/600 (derive it from the route — a `meta.title` key or the matching nav label; do not hard-code one title for every page). Optional breadcrumb above or before it in `--text-sm` muted.
- Right: global controls moved out of the old top bar (language switcher, notifications, profile menu if not in the sidebar footer), `gap: var(--space-3)`.
- A global filter bar becomes a toolbar row under the header (or inside it, if it fits in one row at 1440px): controls at 32–36px height, labels muted `--text-xs`/`--text-sm`, a "Clear" ghost button at the end.

Inside each page, keep a page header block: title (`--text-2xl`) + one-line description (muted) + optional actions aligned right, with `margin-bottom: var(--space-6)`. If the content header already shows the page title, the in-page title may become the description only. Pick one pattern and apply it to every view in scope.

## 5. Components

**Card**: surface, 1px border, `--radius-md`, `--shadow-sm` (optional), `padding: var(--space-6)`. The card header row has title `--text-lg`/600, optional muted subtitle, and actions on the right, with `margin-bottom: var(--space-4)`. No colored top borders or gradients.

**KPI / stat card**: label (`--text-sm`, muted) → value (`--text-3xl`, tabular-nums) → optional delta or sub-label (`--text-xs`, status color). Use a grid with `repeat(auto-fit, minmax(220px, 1fr))` and `gap: var(--space-6)`. If the old design colored the whole card by status, change it to a small status dot or badge — the full-color card is the most "dated" signal.

**Table**:
- Wrapper card with `overflow-x: auto`; the table is `width: 100%`, `border-collapse: separate; border-spacing: 0`.
- Header: `--color-surface-muted` background, `--text-xs` uppercase muted labels, `padding: var(--space-3) var(--space-4)`.
- Body rows: `--text-sm`, `padding: var(--space-3) var(--space-4)`, 1px bottom border, hover `--color-surface-muted`. No zebra stripes.
- Right-align numeric and currency columns; use tabular-nums.

**Badge**: inline-flex, `--text-xs`/500, `padding: 2px var(--space-2)`, pill or `--radius-sm`, status `-soft` background with status text color. Optional 6px leading dot.

**Buttons**: height 36px (32px small), `padding: 0 var(--space-4)`, `--radius-sm`, `--text-base`/500.
- Primary: accent background, white text.
- Secondary: surface background, 1px border, text color.
- Ghost: transparent background, muted text, surface-muted on hover.
- Every button gets a visible `:focus-visible` ring: `outline: 2px solid var(--color-accent); outline-offset: 2px`.

**Form controls**: height 36px, 1px border, `--radius-sm`, surface background, accent border + ring on focus. Selects match inputs.

**Modals and menus**: `--radius-lg` / `--radius-md`, `--shadow-md`/`-lg`, 1px border, header/body/footer padding `var(--space-6)`.

## 6. Responsive behavior

- **≥ 1280px**: full sidebar.
- **1024–1279px**: full sidebar; reduce content padding to `var(--space-6)`.
- **768–1023px**: collapsed icon rail (`--sidebar-width-collapsed`), labels hidden, `title`/`aria-label` on each link so the name is still available.
- **< 768px**: the sidebar becomes an off-canvas drawer opened by a menu button in the content header. Close it on route change, on backdrop click, and on Escape. The grid becomes a single column; KPI grids stack; tables scroll horizontally inside their card; the page must not scroll horizontally.

Keep the open/collapsed state in a small composable (or local state in the shell) — it is UI state, so it does not belong in the data layer.

## 7. Accessibility

- The sidebar is a `<nav aria-label="Main">` landmark; content is in `<main>`.
- Text contrast meets WCAG AA (4.5:1 for body, 3:1 for large text and icons). Muted gray on white is the usual failure — check it.
- Visible focus on every interactive element; logical tab order (sidebar → header → content).
- The drawer toggle has `aria-expanded` and `aria-controls`.
- Respect `prefers-reduced-motion`: keep transitions under 200 ms and disable them under that query.

## 8. Review checklist

Check these against the after screenshots before reporting:

- [ ] Sidebar on the left; the top nav bar is gone; every old header element has a home.
- [ ] Active nav item is clear and follows the route, including on `/`.
- [ ] One accent color; status colors used only for status.
- [ ] Spacing visibly consistent: the same gaps between cards, the same card padding, the same page header spacing on every screen in scope.
- [ ] No full-bleed colored stat cards, gradients, or heavy shadows left over.
- [ ] Tables: aligned numbers, quiet header, hover state, no overflow outside the card.
- [ ] At 390px wide: drawer works, nothing overflows horizontally, text is readable.
- [ ] Build passes; every route loads; filters, language switch and profile menu still work.
- [ ] No new dependencies; no changed logic, route paths or translation keys.

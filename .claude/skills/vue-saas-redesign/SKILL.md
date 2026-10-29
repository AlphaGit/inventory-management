---
name: vue-saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface — a fixed vertical navigation sidebar on the left instead of a top nav bar, a content header, a consistent spacing and type scale, and polished cards, tables, badges and buttons — while keeping the app's own colors and all of its behavior. Use this skill whenever the user wants to modernize, polish, restyle or "make professional" a Vue (Vite) app, move navigation into a sidebar, make it "look like a SaaS dashboard" (Linear, Vercel, Stripe style), fix inconsistent spacing across views, or redesign the app shell or layout — even if they only name one page or just say the UI "looks dated". Not for building new features, React/Angular apps, or creating a new brand.
---

# Vue SaaS Redesign

Turn a Vue 3 app's layout into a modern SaaS shell: left sidebar navigation, a slim content header, and one consistent visual system. This is a **layout and polish** change, not a rebrand and not a rewrite. The user should recognize their app and their colors; it should just feel calmer, more spacious and more deliberate.

## What stays fixed

The redesign earns trust by changing only presentation. Keep these exactly as they are, because users and tests depend on them:

- Route paths, route names, navigation order, and what each link points to.
- Data loading, API calls, props, emits, computed logic, watchers, and filter behavior.
- i18n: reuse existing translation keys. If you need a new label, add the key to **every** locale file, not only English.
- `v-for` keys, component names, and the script style each file already uses (Composition API vs Options API).
- The app's palette (see "Color" below). Do not import a new brand.
- Dependencies. Do not add an icon library, CSS framework, or UI kit. Inline SVG and plain CSS cover everything here. If something truly needs a package, stop and ask.
- Project rules in `CLAUDE.md` files (for example "no emojis in UI", or a rule to delegate `.vue` edits to a specific subagent). Read them first and follow them; they override this skill.

## Workflow

Work in four steps. The plan step exists because a redesign touches many files and taste is personal; a two-minute review up front is much cheaper than undoing a finished redesign.

### 1. Audit (read only)

Build an accurate picture before proposing anything:

1. **Shell**: find where the layout lives — usually `src/App.vue`, sometimes `src/layouts/*.vue`. Note every element in the current header (logo, nav links, language switcher, profile menu, global filter bar, search) — each one needs a new home.
2. **Routes**: read the router (`src/main.js`, `src/router/*`). List every route the nav shows, plus any routed view that the nav omits (mention it; do not add it unless asked).
3. **Global styles**: find where shared classes live (`App.vue` unscoped `<style>`, `src/assets/*.css`, `src/style.css`). List the shared classes views rely on (`.card`, `.badge`, `.stat-card`, tables, buttons, page headers). Restyling these once restyles every view, which is the cheapest route to consistency.
4. **Palette and spacing in use**: run the bundled scanner to see which colors and spacing values the app actually uses:
   ```bash
   python3 <skill-dir>/scripts/scan_styles.py <app-src-dir>
   ```
   It prints colors by frequency and the px values used for padding, margin, gap, radius and font-size. Use it to pick the palette roles and to spot the off-scale values you will normalize.
5. **Before screenshots**: if the app can run, capture the screens in scope at desktop width (see "Verify"). Save them; they make the plan and the final report concrete.

### 2. Plan, then wait for approval

Write a short plan (aim for one screen of text) and ask the user to approve or adjust it. Include:

- **Scope**: which screens. If the user named one page, the shell plus that page are in scope; other views only change through shared classes. Say so.
- **Layout sketch**: a small ASCII diagram of the shell (sidebar, content header, content area) and where each current header element moves.
- **Tokens**: the palette roles mapped to the app's existing colors, plus the spacing, radius and type scales (from `references/design-spec.md`).
- **Files to change**, grouped: tokens, shell, shared classes, per-view touch-ups.
- **Out of scope**: anything you noticed but will not change (bugs, unrouted views, logic issues).

Do not edit files until the user approves. If the user already said to go ahead without review, or the request explicitly pre-approves the plan, still write the plan out, then continue.

### 3. Apply

Work outside-in, so each layer builds on the one before it:

1. **Tokens**: define CSS custom properties on `:root` in the global stylesheet — colors by role, spacing, radius, shadow, type scale, sidebar width. Everything after this uses the tokens, not raw values.
2. **Shell**: rebuild the layout as a sidebar + main grid. Follow the sidebar and header specs in `references/design-spec.md` (structure, active state, responsive behavior, accessibility). Move header widgets to their planned homes without changing their props or events.
3. **Shared classes**: restyle cards, tables, badges, buttons, stat cards, page headers and form controls with the tokens. Prefer editing the shared class over adding view-specific overrides.
4. **Views in scope**: replace hard-coded spacing and colors with tokens, align the page header pattern, and fix layout grids. Leave view logic alone.

Keep the diff reviewable: change style blocks and template structure, not script blocks (except adding a small composable for sidebar open/collapsed state if the responsive pattern needs it).

### 4. Verify

1. Build: `npm run build` (or `npx vite build`) must pass. Delete the build output afterwards if it was not there before.
2. Run the dev server and capture **after** screenshots of each screen in scope at 1440×900 and 390×844. Use the Playwright MCP tools if they are available; otherwise use headless Chrome:
   ```bash
   bash <skill-dir>/scripts/screenshot.sh <url> <out.png> [width] [height]
   ```
3. Look at the screenshots, not only the code. Check against the review checklist at the end of `references/design-spec.md` and fix what fails.
4. Click through every nav link once: each route still loads, the active state follows the route, and the global controls (filters, language switch, profile menu) still work.

## Color

Keep the app's colors and assign them roles; this is what makes the result feel like the same product. From the scan, pick:

- **Neutrals** (text, muted text, borders, surfaces, app background) from the app's grays. If the app mixes several gray families, choose the most used one and map the others onto it.
- **Accent**: the color used for primary actions or active nav today. One accent only.
- **Status**: success, info, warning, danger — reuse the app's existing status colors.

If the app has almost no palette (browser defaults, one or two colors), fall back to the neutral palette in `references/design-spec.md` and say so in the plan. Only add dark mode if the app already supports it.

## Report

When done, tell the user: what changed (shell, tokens, shared classes, views), where each old header element went, the before/after screenshot paths, anything you could not verify, and the out-of-scope issues you noticed.

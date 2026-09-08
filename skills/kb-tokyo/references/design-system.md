# TrailGoat design system

*A reference for agents. It describes how every surface of trailgoat.run is
built — the palette vocabulary, the type, the chrome, the components, the maps
and charts — precisely enough that a new page, a new report, or a new app can
be built in the same language without opening the site. Where a value is
quoted, it is the value in the stylesheet on the day this was written
(2026-09-06); the file:line beside it is where to confirm it.*

**Sources of truth, in load order.** `static/tokens.css` (the vocabulary and
the Tokyo Night palette), the page's own stylesheet, `static/tg-store.js`
(theme switch), `static/nav.css` + `static/nav-template.js` + `static/nav.js`
(the shared chrome), `static/icons.js` (every pictogram),
`static/trail-map.js` (maps and charts). A rule in this document that
disagrees with one of those files is wrong; fix the document.

**Companion.** The `/kb-tokyo` skill (`.claude/skills/kb-tokyo/`) carries a
standalone stylesheet distilled from this document so the same look can be
built outside the repo. This document is the *why* and the *exactly*; the
skill's `assets/tokyo.css` is the *paste this*.

---

## Contents

1. [Principles](#1-principles)
2. [Themes, and Tokyo Night in full](#2-themes)
3. [Token reference](#3-token-reference)
4. [Type](#4-type)
5. [Page shell and layout](#5-page-shell-and-layout)
6. [Navigation](#6-navigation)
7. [Components](#7-components)
8. [Maps and mini maps](#8-maps)
9. [Charts](#9-charts)
10. [Iconography](#10-iconography)
11. [Motion, touch and accessibility](#11-motion-touch-accessibility)
12. [Page recipes](#12-page-recipes)
13. [Checklist for a new surface](#13-checklist)

---

## 1. Principles

These are the rules the stylesheets argue for in their own comments. Each one
has a Linear issue behind it; the number is quoted so the history is findable.

1. **One accent on duty (TG-282).** `--accent` is the only hue that marks an
   action or "current": the primary button, the active nav link, the lit tab,
   the focus ring, the "you are here" chip. Everything else interactive is
   drawn from the **neutral ladder** — steps of the ink over transparent
   (`--fill-idle` 4% → `--fill-hover` 8% → `--fill-selected` 18%; edges at
   `--edge` 40% and `--edge-soft` 25%). Never a coloured glow, never a
   feature tint on chrome.
2. **The feature palette is for data, not chrome (TG-282, KRI-119).** Nine
   hues — fuel, pace, crew, course, gear, weather, climb, aid, plus `--gold`
   for the AI coach — belong to charts, map layers, section icons and the
   4px identity stripe on a card. Not to buttons, hovers, or selected states.
3. **Depth from ground steps and hairlines, not blur (TG-283).** Four ground
   steps (`--bg-well` → `--bg-0` page → `--bg-1` panel → `--bg-2` raised); a
   resting surface is a 1px `--line` edge on the next step up. Exactly one
   shadow token, `--shadow-pop`, and only for layers that leave the page plane
   (menus, palette, toasts, tooltips, popovers).
4. **Two radii (TG-283).** `--r-ctl: 6px` for anything you press; `--r-card:
   10px` for the surface it sits on. Avatars, swatch dots, meters, progress
   bars and slider tracks stay round — they are pictures or data, not
   controls.
5. **Three cuts of one family (TG-288).** Red Hat Display for headlines and
   the wordmark, Red Hat Text for copy and chrome, Red Hat Mono for labels
   and every figure. TrailGoat is "secretly a numbers product", so figures are
   set like instrument readings: tabular, with the unit tracked out in caps.
6. **Mono caps is the label voice, and it has a floor (TG-284, TG-301).**
   Eyebrows, section labels, table headers and nav doors are
   `var(--mono)`, weight 500, `letter-spacing: 0.1em`, uppercase. Never below
   `--mono-cap` (11px desktop, 12px phone).
7. **Motion announces, then stops (TG-285).** One easing (`--ease-snap`,
   easeOutQuint), two durations (`--dur-ctl` 150ms, `--dur-layer` 250ms), one
   entrance (`tg-pop-in`: fade up from 96%). Nothing in the chrome loops
   forever under a planning tool the runner is trying to read. Every
   animation has a `prefers-reduced-motion` suppression.
8. **One "you are here" mark per view (TG-287).** The teal→accent gradient
   ring (`.tg-here`) marks exactly one element on the page — the section chip
   in view, the active view tab. Never on cards, buttons, menus or the topbar
   (which uses a flat 2px underline). The installed tab bar opts out and uses
   a rail instead.
9. **SVG icons only; no emoji (KRI-200).** Every pictogram is 24×24 line art
   stroked in `currentColor` from `icons.js`. The drawn goat mascot is the one
   image exception, and it is a PNG, never 🐐.
10. **Tokens, not literals.** A stylesheet reads `var(--…)`. A theme is a
    scoped block that redefines the same names under `html.theme-*`. Anything
    painted with a literal colour must be re-lit in every theme file, so
    literals are the exception you justify in a comment.
11. **Touch is first-class.** 44px minimum tap targets on phones,
    `touch-action: manipulation` on every control, tap highlight replaced by
    the control's own `:active` fill.

---

## 2. Themes

### 2.1 Mechanism

* The roster lives once, in `static/tg-store.js` (`THEMES`). Order is picker
  order; `swatch = [ground, hue, hue]`:

  | key | label | class on `<html>` | stylesheet | swatch |
  |---|---|---|---|---|
  | `default` | Forest | *(none — plain `:root`)* | none | `#07120f` `#ff7a1a` `#9ae600` |
  | `emerald` | Emerald | `theme-emerald` | `/emerald.css` | `#04182a` `#35bcc6` `#69be28` |
  | `alpenglow` | Alpenglow | `theme-alpenglow` | `/alpenglow.css` | `#190d12` `#f95d8f` `#ff6a3d` |
  | `aurora` | Aurora | `theme-aurora` | `/aurora.css` | `#0a0c1e` `#7fb5ff` `#56e39f` |
  | `firstlight` | First Light | `theme-firstlight` | `/firstlight.css` | `#f5f7f6` `#1f7a3a` `#d9580d` |
  | `tokyonight` | **Tokyo Night** (default) | `theme-tokyonight` | *none — inside tokens.css* | `#1a1b26` `#7aa2f7` `#bb9af7` |

* `DEFAULT_THEME = 'tokyonight'`. Its palette rides inside `tokens.css`
  (already on the critical path) so a first visit never flashes Forest; every
  other theme lazy-loads its file. A theme with no `file` is one whose block
  is in tokens.css.
* Public API, `window.TrailGoatTheme`: `get()`, `set(key)` (stores + applies,
  clears any preview), `list()`, `adopt(key)` (only if nothing stored),
  `preview(key)` (view-only, never written — used by shared links and the
  embed builder), `stored()`, `isPreview()`, `DEFAULT`. `?theme=<key>` on a URL
  is a view-only preview. A signed-in user's pick is mirrored to
  `users.theme` via `PUT /api/me/theme`.
* `<meta name="theme-color" data-tg-theme>` is repainted to the active
  `--bg-0` so the phone status bar matches.
* A theme file overrides **only token names** under its class, then re-lights
  the handful of spots that paint literals (`.backdrop`, `.aurora`, `.goat`
  glow, `.cta-band`, the hero route gradient stops). First Light, the only
  light palette, additionally re-derives the depth tokens (`--raise-*`,
  `--well`, `--shadow-pop`, `--line`, `--glass`) because the dark versions
  assume a dark ground.

### 2.2 Tokyo Night, resolved

The palette is Omarchy's Tokyo Night, mapped onto the TrailGoat roles. The
left column is the declared value (`tokens.css` `html.theme-tokyonight`); the
derived tokens are `color-mix()` results resolved to hex so a tool that
cannot evaluate `color-mix` (a PDF renderer, an email, a canvas) can still
match.

| Role | Token | Value | Note |
|---|---|---|---|
| Page ground | `--bg-0` | `#1a1b26` | "tokyo midnight" |
| Panel | `--bg-1` | `#24283b` | "storm" |
| Raised surface | `--bg-2` | ≈ `#333749` | `color-mix(--bg-1 93%, #fff)` |
| Well / inset track | `--bg-well` | ≈ `#15161e` | `color-mix(--bg-0 80%, #000)` |
| Text | `--ink` | `#c0caf5` | periwinkle white |
| Secondary text | `--muted` | `#9aa5ce` | streetlight slate |
| Headline emphasis | `--ink-bright` | ≈ `#d9dff9` | `color-mix(--ink 60%, #fff)` |
| Hints / placeholders | `--faint` | ≈ `#747c9c` | `color-mix(--muted 70%, --bg-0)` |
| **Accent** | `--accent` | `#7aa2f7` | signal blue — the one hue on duty |
| Text on accent | `--accent-ink` | `--bg-well` (≈ `#15161e`) | dark ink on the blue fill |
| Selection | `--selection` | `rgba(122,162,247,.28)` | |
| Hairline | `--line` | `rgba(255,255,255,.09)` | inherited from `:root` |
| Half hairline | `--line-faint` | ≈ `rgba(255,255,255,.05)` | |
| Glass | `--glass` / `--glass-2` | `rgba(255,255,255,.045)` / `.07` | |
| Fill idle / hover / selected | `--fill-*` | ink @ 4% / 8% / 18% | ≈ `rgba(192,202,245,.04/.08/.18)` |
| Edge / soft edge / ring | `--edge` / `--edge-soft` / `--ring` | ink @ 40% / 25% / 25% | |
| Fueling | `--c-fuel` (`--orange`) | `#ff9e64` | lantern orange |
| Pacing | `--c-pace` (`--moss`) | `#7aa2f7` | signal blue |
| Crew | `--c-crew` (`--fern`) | `#9ece6a` | vending-machine green |
| Course | `--c-course` (`--teal`) | `#0db9d7` | neon cyan |
| Gear | `--c-gear` (`--violet`) | `#bb9af7` | arcade violet |
| Weather | `--c-weather` (`--plum`) | `#d98ae0` | dusk neon (pink-shifted so it is not a second violet) |
| Climbs | `--c-climb` (`--coral`) | `#f7768e` | vermilion sign |
| Aid + descents | `--c-aid` (`--aqua`) | `#7dcfff` | pale sky glass |
| AI coach / brand gold | `--gold` | `#e0af68` | brass |
| Wordmark gradient | `.grad` | `linear-gradient(100deg, #0db9d7, #7aa2f7)` | `--teal` → `--accent` |
| "You are here" ring | `--here-ring` | `linear-gradient(45deg, #0db9d7, #7aa2f7)` | |
| Pop shadow | `--shadow-pop` | `0 8px 24px rgba(0,0,0,.45)` | |

Tokyo Night's literal spot overrides (`tokens.css`, bottom):

```css
html.theme-tokyonight .backdrop {
    background:
        radial-gradient(1200px 600px at 70% -10%, rgba(13, 185, 215, 0.10), transparent 60%),
        radial-gradient(900px 500px at 10% 10%, rgba(187, 154, 247, 0.08), transparent 55%),
        linear-gradient(180deg, var(--bg-0), var(--bg-1));
}
html.theme-tokyonight .aurora {
    background: conic-gradient(from 180deg at 50% 50%, transparent, rgba(122, 162, 247, 0.07), transparent 40%);
}
html.theme-tokyonight .goat {
    filter: drop-shadow(0 24px 36px rgba(0, 0, 0, 0.55)) drop-shadow(0 0 10px rgba(122, 162, 247, 0.45));
}
html.theme-tokyonight .cta-band {
    background-image: radial-gradient(600px 200px at 50% -20%, rgba(187, 154, 247, 0.12), transparent 70%);
}
html.theme-tokyonight #hr-grad stop:nth-of-type(1) { stop-color: #0db9d7; }
html.theme-tokyonight #hr-grad stop:nth-of-type(2) { stop-color: #7aa2f7; }
html.theme-tokyonight #hr-grad stop:nth-of-type(3) { stop-color: #bb9af7; }
```

The depth tokens Tokyo Night inherits from `fuel.css :root` (dark ground):

```css
--raise-1: inset 0 1px 0 rgba(255,255,255,0.07), 0 2px 6px rgba(0,0,0,0.35);
--raise-2: inset 0 1px 0 rgba(255,255,255,0.09), 0 2px 5px rgba(0,0,0,0.45), 0 10px 22px -8px rgba(0,0,0,0.55);
--well:    inset 0 2px 6px rgba(0,0,0,0.5), inset 0 -1px 0 rgba(255,255,255,0.05);
```

### 2.3 The other palettes, in one line each

* **Forest** (`:root`): pine `#07120f` / navy `#0a1a1c`, ink `#eaf4ee`, muted
  `#8ea7a0`, accent moss `#9ae600`, fuel orange `#ff7a1a`, gold `#ffd23f`.
* **Emerald**: College Navy `#04182a` / `#0a2740`, accent Action Green
  `#69be28`, glacier teal `#35bcc6`.
* **Alpenglow** and **Aurora**: see their files; same override shape.
* **First Light** (light): page `#f5f7f6`, panels `#ffffff`, ink `#15201b`,
  muted `#5b6864`, accent `#1f7a3a` with white `--accent-ink`; ladder
  re-stepped (fills 4/8/14%, edges 22/14%); no aurora, no grain, whisper
  shadows; feature hues at a "600" weight (`#d9580d #4f8f0a #1c8f4e #0f8b7d
  #6d4fd6 #a63ab9 #d63d5c #1180bd`, gold `#a5780a`).

**Adding a theme** is one roster entry in `tg-store.js` plus one stylesheet
that redefines the token names under `html.theme-<key>` and re-lights the
literal spots listed above. `evals/test_theme_roster.py` sweeps the roster.

---

## 3. Token reference

Everything in `static/tokens.css :root`, grouped as the file groups it. A
consumer reads these names and nothing else.

| Group | Tokens |
|---|---|
| Ground | `--bg-well` `--bg-0` `--bg-1` `--bg-2` |
| Ink | `--ink-bright` `--ink` `--muted` `--faint` |
| Accent | `--accent` `--accent-ink` `--selection` |
| Neutral ladder | `--fill-idle` `--fill-hover` `--fill-selected` `--edge` `--edge-soft` `--ring` |
| Lines & glass | `--line` `--line-faint` `--glass` `--glass-2` |
| Feature palette | `--c-fuel` `--c-pace` `--c-crew` `--c-course` `--c-gear` `--c-weather` `--c-climb` `--c-aid` `--gold` |
| Legacy aliases (read-only) | `--orange`→fuel `--moss`→pace `--fern`→crew `--teal`→course `--violet`→gear `--plum`→weather `--coral`→climb `--aqua`→aid |
| Corners | `--r-ctl: 6px` `--r-card: 10px` (`--radius` in page sheets is an alias of `--r-card`) |
| Type | `--display` `--body` `--mono` `--mono-cap` |
| Motion | `--ease-snap: cubic-bezier(0.23,1,0.32,1)` `--dur-ctl: 150ms` `--dur-layer: 250ms` |
| You-are-here | `--here-ring` `--here-fill` `--here-bg` |
| Shadow | `--shadow-pop` |
| Depth (fuel.css `:root`, dark ground) | `--raise-1` `--raise-2` `--well` (`--raise-primary`, `--ledge-orange` are retired) |
| Layout (nav.css) | `--tg-tabbar-h: 56px` `--tg-tabbar-space` (only inside the installed-phone gate) `--foot-cols` |

Global element rules tokens.css also ships: `body { font-family: var(--body) }`;
`code, kbd, pre` as a mono chip (`0.85em`, `--bg-well` fill, `--line-faint`
border, 4px radius, `1px 5px` padding); `a:not([class])` in `--accent` with a
3px-offset underline; anchor-buttons never underlined; the `.data`,
`.data-u`, `.data-label` utilities; `.tg-here`; `@keyframes tg-pop-in`; the
touch block.

---

## 4. Type

**Loading.** Every served page requests exactly these, with `display=swap`,
and nothing else (`evals/test_fonts.py` asserts it):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@700;800&family=Red+Hat+Text:wght@400;500;600;700&family=Red+Hat+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

Fallbacks are deliberate: `-apple-system, BlinkMacSystemFont, sans-serif` and
`ui-monospace, 'SF Mono', Menlo, Consolas, monospace`. Block Google Fonts and
the page still reads and the columns still line up.

**Roles and the scale in use.**

| Voice | Token / weight | Where | Sizes seen |
|---|---|---|---|
| Display headline | `--display` 800, `letter-spacing: -0.015em`…`-0.02em`, `line-height: 1.02`…`1.05` | `h1`, section `h2`, CTA band | h1 `clamp(2.4rem, 6vw, 4.1rem)` (home), `clamp(2rem, 5vw, 3.2rem)` (tools); h2 `clamp(1.7rem, 4vw, 2.5rem)` |
| Display title | `--display` 700 | `.panel-title` 1.15rem, `.tool h3` 1.25rem, `.col-head` 600 0.98rem, `.btn` 0.98rem, `.tool .go` 0.92rem |
| Wordmark | `--display` 800, `letter-spacing: 0.02em` | `.wordmark` 1.4rem (1.15rem in the 44px topbar); "Goat" in `.grad` |
| Body | `--body` 400, `line-height: 1.5`–`1.55` | copy; `.hero-sub` 1.05–1.12rem `--muted` |
| Chrome | `--body` 600–700 | nav rows 0.92–1rem, buttons 0.85–0.92rem, `.set-label` 0.88rem, small meta 0.76–0.85rem `--muted` |
| Label (mono caps) | `--mono` 500, `letter-spacing: 0.1em`, uppercase | `.eyebrow` 0.76–0.8rem, `.kicker` 0.74rem, nav doors 0.72rem, footer `h4` 0.72rem, tab labels 0.6rem (floor applies), badges 0.62–0.68rem with `0.08–0.12em` |
| Figure | `--mono`, `font-variant-numeric: tabular-nums`, `font-feature-settings: "tnum" 1` | `.data`, `.metric-num`, plan table cells; unit `.data-u` at `0.8em` 500 caps `0.08em` |
| Code | `--mono` 0.85em chip | `code`, `kbd`, `pre` |

Rules of thumb: hierarchy inside a figure is by **weight**, not by a second
colour; a label never drops below `--mono-cap`; body copy that is secondary
is `--muted`, never a smaller size alone; `-webkit-font-smoothing:
antialiased` on `body`.

---

## 5. Page shell and layout

### 5.1 The `<head>` contract

Order matters; the comments in each file assume it.

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#1a1b26" data-tg-theme>   <!-- repainted by tg-store.js -->
<!-- fonts (section 4) -->
<link rel="stylesheet" href="/tokens.css?v=N">     <!-- 1. vocabulary + Tokyo Night, before anything paints -->
<link rel="stylesheet" href="/<page>.css?v=N">     <!-- 2. the page's own sheet -->
<script src="/tg-store.js?v=N"></script>           <!-- 3. NOT deferred: applies html.theme-* before first paint -->
<link rel="stylesheet" href="/nav.css?v=N">        <!-- 4. after the page sheet, so the shared chrome wins -->
<script src="/nav.js?v=N" defer></script>
<script src="/auth.js?v=N" defer></script>
…
<script src="/icons.js?v=N"></script>              <!-- before nav-template.js, which draws with TG_ICON -->
<script src="/nav-template.js?v=N"></script>
```

`?v=` numbers are rewritten on the way out from the one map in
`app/assets.py` (`VERSIONS`). Bump the asset's line there when its contents
change; never edit the literal in 25 HTML files.

### 5.2 Body

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--body); background: var(--bg-0); color: var(--ink);
       min-height: 100vh; line-height: 1.5; -webkit-font-smoothing: antialiased;
       overflow-x: clip; }            /* clip, not hidden — hidden makes body a scroll container */
@media (prefers-reduced-motion: no-preference) { html:focus-within { scroll-behavior: smooth; } }
```

Body class variants: `body.app-shell` (Course Creator, Dashboard — flex column
that hides the footer to reclaim space), `body.split-page` (Race Day / the
planner: left pane + scrolling right pane; the section chips move into the
right pane), `body.nav-open`, `body.pal-open`, `html.tg-standalone`
(installed PWA), `html.reveal-armed` (reveal-on-scroll enabled).

### 5.3 The backdrop

Every dark page sits on a fixed atmosphere behind the content, tokens for the
ground and literal alphas for the tints (which is why each theme re-lights it):

```css
.backdrop { position: fixed; inset: 0; z-index: -1; overflow: hidden; background:
    radial-gradient(1200px 600px at 70% -10%, <course-hue @ .10>, transparent 60%),
    radial-gradient(900px 500px at 10% 10%,  <second-hue @ .08>, transparent 55%),
    linear-gradient(180deg, var(--bg-0), var(--bg-1)); }
.aurora   { position: absolute; inset: -40%; opacity: 0.7;
    background: conic-gradient(from 180deg at 50% 50%, transparent, <accent @ .06–.07>, transparent 40%); }
.ridge    { position: absolute; bottom: 0; left: 0; width: 100%; height: 42vh; }  /* three SVG mountain silhouettes */
.ridge path { fill: rgba(255,255,255,0.025); } .ridge-mid { fill: …0.035 } .ridge-front { fill: …0.05 }
.backdrop::after { /* film grain: inline feTurbulence SVG, opacity 0.025 */ }
```

Tokyo Night's tints are cyan `rgba(13,185,215,.10)` + violet
`rgba(187,154,247,.08)`, aurora signal blue `rgba(122,162,247,.07)`. First
Light removes aurora and grain and paints `.backdrop` flat `--bg-0`.

Cross-fade between pages: `@view-transition { navigation: auto; }` with
`::view-transition-old(root), ::view-transition-new(root) { animation-duration: 0.18s }`,
switched off under reduced motion.

### 5.4 Containers and breakpoints

| Container | Width | Padding |
|---|---|---|
| `.wrap` (home) | `max-width: 1140px; margin: 0 auto` | `0 24px 90px` |
| `.wrap` (tool pages) | `max-width: 1180px` | `10px clamp(16px, 4vw, 40px) 80px` |
| `.topbar` | full-bleed, `max-width: none` | `0 clamp(16px, 2vw, 30px)` (desktop 44px row) |
| `footer.foot` | `max-width: 1180px` | grid `30px 8px 22px` |
| `.hm-pocket` | `max-width: 1180px` | `0 20px` |

Breakpoints, in order of how often they appear: **860px** (the phone/desktop
seam — the topbar, tab bar, `--mono-cap` step-up, hero stacking all key on it;
desktop rules are `min-width: 861px`), **600px** (plan tables become cards,
two-column card grids collapse), **560px** (home tool cards become tap rows),
**720px** (footer to one column), **1079px** (search field collapses to an
icon), plus `pointer: coarse` for tap-target growth.

Grid idioms: `repeat(auto-fit, minmax(232px, 1fr))` for tool cards,
`minmax(260px, 1fr)` for effort columns and course lists, `repeat(2,
minmax(0, 1fr))` for paired result cards (`minmax(0,…)`, never bare `1fr`, so
a long label cannot widen its column). Gaps 18px between cards, 10–12px
between list rows.

Z-index ladder: page `auto` → section chips `1890` → menu scrim `1900` →
topbar `2000` → tab bar `2050` → sheets/dropdowns `2100` → account/settings
menus `3000` → toasts `4000` → command palette `4500` → tips/popovers `9999` →
tour ring `10000` / tour card `10001`.

---

## 6. Navigation

All chrome is injected by `nav-template.js` into `<header class="topbar"
id="site-topbar">` and `<footer class="foot">`; pages ship only the shell plus
a crawlable `<nav class="foot-nav">`. Styles in `nav.css`.

### 6.1 Desktop: the terminal topbar (≥861px, TG-286)

One 44px row on `--bg-0` with a hairline under it; it never wraps.

```css
.topbar { display: flex; align-items: center; justify-content: space-between; flex-wrap: nowrap;
    height: 44px; gap: 14px; padding: 0 clamp(16px, 2vw, 30px);
    background: var(--bg-0); border-bottom: 1px solid var(--line); }
.topbar .wordmark { font-family: var(--display); font-weight: 800; font-size: 1.15rem; letter-spacing: 0.02em; }
.topbar .grad { background: linear-gradient(100deg, var(--teal), var(--accent));
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
/* the three "doors": Plan ▾ · Courses ▾ · Why TrailGoat ▾ */
.topbar .nav > .nav-group > .nav-group-btn, .topbar .nav > a {
    display: inline-flex; align-items: center; height: 44px; padding: 0 11px; border-radius: 0;
    font-family: var(--mono); font-weight: 500; font-size: 0.72rem; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--muted);
    transition: color var(--dur-ctl) var(--ease-snap), background var(--dur-ctl) var(--ease-snap); }
.topbar .nav > a:hover, .nav-group-btn:hover, .nav-group-btn[aria-expanded="true"] { color: var(--ink); background: var(--fill-hover); }
.topbar .nav > a[aria-current="page"], .nav-group-btn.nav-group-here {
    color: var(--accent); background: none; box-shadow: inset 0 -2px 0 var(--accent); }   /* the flat underline */
```

Left to right: wordmark (`Trail<span class="grad">Goat</span>`) · doors ·
search field (`.nav-search`, `flex: 0 1 440px; height: 30px`, mono 0.68rem,
labelled "Search courses ⌘K", collapses to a 32px icon button below 1080px or
when `nav.js` measures overflow and stamps `.topbar-tight` / `.topbar-tighter`)
· gear (`.nav-gear`, 32px square, `--glass` fill, `--line` border, `--r-ctl`)
· account (`.tg-auth-btn` "Sign in" or `.tg-auth-chip` avatar 26px round +
first name, ellipsis past `12ch`).

Dropdown menus (`.nav-group-menu`, `.tg-auth-menu`, `.nav-settings-menu`) are
the one floating-layer recipe:

```css
position: absolute; top: calc(100% + 6–8px); z-index: 2100–3000; min-width: 220–260px; padding: 6–12px;
background: color-mix(in srgb, var(--bg-1) 96%, #fff 4%);   /* or var(--bg-1) */
border: 1px solid var(--line); border-radius: var(--r-card); box-shadow: var(--shadow-pop);
transform-origin: top left|right; animation: tg-pop-in var(--dur-layer) var(--ease-snap);
/* rows */ display: flex; padding: 9px 12px; border-radius: var(--r-ctl); font: 600 0.92rem var(--body); color: var(--muted);
/* row hover */ color: var(--ink); background: var(--fill-hover);
/* row current */ color: var(--accent); background: var(--fill-selected);
```

### 6.2 Phone: sticky bar + burger panel (≤860px)

```css
.topbar { position: sticky; top: 0; z-index: 2000; padding: 10px clamp(16px,2vw,30px);
    background: color-mix(in srgb, var(--bg-0) 86%, transparent);
    -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); border-bottom: 1px solid var(--line); }
@supports not (backdrop-filter: blur(1px)) { .topbar { background: var(--bg-0); } }
.nav-burger { width: 44px; height: 44px; margin: -4px 0; order: 10; }   /* three 20×2px bars → X morph, 0.2s */
.topbar-mascot { display: inline-flex; margin-right: auto; }             /* the 32px goat trotting beside the wordmark, phone only */
.topbar-tools { position: absolute; top: calc(100% + 8px); left: 12px; right: 12px; padding: 8px;
    background: color-mix(in srgb, var(--bg-1) 96%, #fff 4%); border: 1px solid var(--line);
    border-radius: var(--r-card); box-shadow: var(--shadow-pop); max-height: calc(100dvh - 90px); overflow-y: auto; }
.topbar .topbar-tools .nav a { display: flex; align-items: center; min-height: 46px; padding: 10px 14px;
    border-radius: var(--r-ctl); font-size: 1rem; font-weight: 600; }
body.nav-open::after { content: ""; position: fixed; inset: 0; z-index: 1900; background: rgba(4,10,8,0.45); }
```

Inside the panel: the account control first (`order: -1`, full-width, 46px),
then the nav groups flattened into labelled sections (children indented
`padding-left: 36px`, 42px rows), the search row, then the settings rows
inline (unit toggles as full-width segmented controls, the theme grid).

### 6.3 Section chips (long tool pages)

Built by `nav.js`; a horizontally scrolling row of jump pills that also acts
as a scroll-spy.

```css
.section-chip { min-height: 36px (40px on phone); padding: 6px 14px; background: var(--fill-idle); color: var(--muted);
    border: 1px solid var(--line); border-radius: var(--r-ctl); font: 600 0.82rem var(--body); white-space: nowrap; }
.section-chip:hover { color: var(--ink); background: var(--fill-hover); border-color: var(--edge-soft); }
.section-chip[aria-current], .section-chip.tg-here { color: var(--accent); border-color: transparent; background: var(--here-bg); }
/* phone: sticky under the topbar */
.section-chips { position: sticky; top: 63px; z-index: 1890; display: flex; gap: 8px; padding: 8px 16px 10px; overflow-x: auto;
    scrollbar-width: none; background: color-mix(in srgb, var(--bg-0) 86%, transparent); backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--line); }
.section-chips.chips-more-right { mask-image: linear-gradient(90deg, #000 calc(100% - 44px), transparent); }  /* "more this way" fade */
/* desktop split page: a wrapped, centred toolbar pinned to the top of the right pane */
body.split-page .split-right > .section-chips { position: sticky; top: 0; z-index: 7; display: flex; flex-wrap: wrap;
    justify-content: center; gap: 7px; padding: 10px 12px; background: var(--bg-0);
    border: 1px solid var(--line); border-radius: var(--r-card); }
```

### 6.4 Installed app: tab bar, More sheet, back arrow (TG-294)

Gated on `html.tg-standalone` **and** `max-width: 860px`. A browser tab, a
tablet or a desktop install keep the nav above.

```css
:root { --tg-tabbar-h: 56px; }
html.tg-standalone { --tg-tabbar-space: calc(var(--tg-tabbar-h) + env(safe-area-inset-bottom, 0px)); }
html.tg-standalone body { padding-bottom: var(--tg-tabbar-space); }
.tg-tabbar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 2050; display: flex; align-items: stretch;
    height: calc(var(--tg-tabbar-h) + env(safe-area-inset-bottom, 0px)); padding-bottom: env(safe-area-inset-bottom, 0px);
    background: color-mix(in srgb, var(--bg-0) 92%, transparent); backdrop-filter: blur(14px); border-top: 1px solid var(--line); }
.tg-tab { flex: 1 1 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 44px; gap: 3px; padding: 6px 2px; margin: 4px 4px; position: relative;
    border: 1px solid transparent; border-radius: var(--r-ctl); color: var(--muted);
    font-family: var(--mono); font-weight: 500; font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; }
.tg-tab .ico { width: 20px; height: 20px; }
.tg-tab:active { background: var(--fill-hover); }
.tg-tab-on { color: var(--accent); }
.tg-tab-on::before { content: ""; position: absolute; top: -6px; left: 22%; right: 22%; height: 2px;
    background: var(--accent); border-radius: 0 0 2px 2px; }         /* the rail — not the ring, on purpose */
```

Tabs (markup built in `nav-template.js`): `<a class="tg-tab"><span
class="tg-tab-ico">{svg}</span><span class="tg-tab-label">Plan</span></a>`, and
a `<button class="tg-tab tg-tab-more">` that opens the sheet:

```css
.tg-sheet-scrim { position: fixed; inset: 0; z-index: 2100; display: flex; align-items: flex-end; background: rgba(0,0,0,0.45); }
.tg-sheet { width: 100%; max-height: 78dvh; overflow-y: auto; display: flex; flex-direction: column; gap: 2px;
    padding: 10px 10px calc(10px + env(safe-area-inset-bottom, 0px));
    background: color-mix(in srgb, var(--bg-1) 96%, #fff 4%); border-top: 1px solid var(--line);
    border-radius: var(--r-card) var(--r-card) 0 0; transform-origin: bottom center; animation: tg-pop-in var(--dur-layer) var(--ease-snap); }
.tg-sheet .nav-link { display: flex; align-items: center; gap: 10px; min-height: 48px; padding: 0 14px;
    border-radius: var(--r-ctl); color: var(--ink); font: 600 0.95rem var(--body); }
.tg-back { width: 40px; height: 40px; order: -1; margin: -4px 2px -4px -8px; border-radius: var(--r-ctl); }  /* .ico 20px */
```

Settings deep-link: `window.TrailGoatOpenSettings(focusId)` opens the gear
menu on desktop or the burger panel on a phone and focuses a field.

### 6.5 Footer (one template)

```css
.foot-grid { display: grid; grid-template-columns: repeat(var(--foot-cols, 3), 1fr); gap: 28px;
    padding: 30px 8px 22px; border-top: 1px solid var(--line); }          /* 1 column ≤720px */
.foot-col h4 { font-family: var(--mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink); }
.foot-link { color: var(--accent); font-weight: 600; font-size: 0.92rem; text-decoration: none; }  /* underline on hover; 40px rows on phone */
.foot-note { font-size: 0.8rem; line-height: 1.5; color: var(--muted); }
.foot-donate { /* bordered neutral button, see 7.1 */ padding: 9px 18px; font-weight: 700; }
.foot-soc { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%; color: var(--muted);
    background: var(--glass); border: 1px solid var(--line); }             /* hover: ink, --edge-soft, translateY(-2px) */
.foot-legal, .foot-nav { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.foot-legal a { color: var(--muted); font-size: 12.5px; }                    /* hover: --accent */
.foot-credits { text-align: center; color: var(--muted); font-size: 0.8rem; padding: 14px 8px 6px; border-top: 1px solid var(--line); }
```

---

## 7. Components

Every recipe below is the tokenised form. A hex or an `rgba()` appears only
where the stylesheet itself paints a literal.

### 7.1 Buttons

There is **one solid accent button per view** — the page's primary verb. All
other verbs are the ladder's bordered neutral, or a quiet text link.

| Class | Look | Geometry | File |
|---|---|---|---|
| `.btn.btn-primary` | `color: var(--accent-ink); background: var(--accent); border: 1px solid var(--accent)`; hover `translateY(-2px)` + `brightness(1.08)`; active `translateY(0)` | `display: inline-flex; gap: 9px; padding: 13px 22px; border-radius: var(--r-ctl); font: 700 0.98rem var(--display)` | home.css |
| `.btn.btn-ghost` | `color: var(--ink); border: 1px solid rgba(255,255,255,.12); background: linear-gradient(180deg, rgba(255,255,255,.09), rgba(255,255,255,.04)); box-shadow: inset 0 1px 0 rgba(255,255,255,.1), 0 2px 5px rgba(0,0,0,.4), 0 10px 22px -10px rgba(0,0,0,.6)`; hover `border-color: var(--edge)`; active `translateY(1px)` + inset well | same as `.btn` | home.css |
| `.export-btn` (the tool-page workhorse) | `background: var(--fill-idle); color: var(--ink); border: 1px solid var(--edge)`; hover `background: var(--fill-hover); translateY(-1px)`; active `var(--fill-selected); translateY(1px)`; disabled `opacity: .6` | `inline-flex; gap: 7px; padding: 9px 18px; border-radius: var(--r-ctl); font: 700 0.85rem inherit` | fuel.css |
| `.export-btn.tonal` | tinted glass: `border: 1px solid rgba(255,255,255,.12); background: linear-gradient(180deg, rgba(255,255,255,.085), rgba(255,255,255,.04)); box-shadow: var(--raise-1)`; the icon inside is `--accent` | same | fuel.css |
| `.export-btn` gold variant (pricing "Request it") | `background: var(--gold); color: #1a1205; border-color: var(--gold)` | same | pricing.html |
| `.tg-plan-save`, `.foot-donate`, `.tg-install-go`, `.tg-storage-clear`, `.tg-tour-btn.primary` | the same bordered neutral: `var(--fill-idle)` / `1px solid var(--edge)` / hover `var(--fill-hover)` | `padding: 7–9px 15–18px; font: 600 0.82–0.92rem var(--body)` | nav.css |
| `.tg-auth-btn`, `.nav-gear`, `.nav-search` | quiet glass: `background: var(--glass); border: 1px solid var(--line)`; hover `border-color: var(--edge-soft); background: var(--fill-hover)` | `padding: 7px 16px; font: 600 0.88rem` / 32–36px squares | nav.css |
| Text action (`.tg-plan-crew-copy`, `.tg-tour-skip`) | `color: var(--accent)` (or `--muted`), `text-decoration: underline; text-underline-offset: 3px`, no border, no fill | `font: 600 0.76–0.8rem` | nav.css |
| Icon-only close (`.tg-install-x`, `#tg-pop .tg-pop-x`) | `background: none; border: 0; color: var(--muted)`; hover `--ink` | `font-size: 1.15rem; padding: 2px 4px` | nav.css |

Buttons carry `.ico` line icons at 15px (13px in nav rows); icons inherit the
text colour. Anchor-buttons (`a.btn`, `a.export-btn`) never show an underline
(tokens.css resets it in every state).

### 7.2 Segmented controls: `.unit-toggle`

An inset track with a raised neutral key. Used for mi/km, °F/°C, view
switches, and any two-to-four-way exclusive choice.

```css
.unit-toggle { display: inline-flex; gap: 4px; padding: 4px; background: rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.09); border-radius: var(--r-ctl); box-shadow: var(--well); }
.unit-toggle button { background: transparent; color: var(--muted); border: none; padding: 7px 16px;
    border-radius: calc(var(--r-ctl) - 2px); font: 700 0.78rem var(--body); letter-spacing: 0.04em; transition: all 0.15s; }
.unit-toggle button.active { color: var(--ink);
    background: linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.08));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 3px 8px rgba(0,0,0,0.45); }
```

The theme picker `.theme-grid` is the same track as a 2-column grid
(`repeat(2, minmax(0,1fr)); gap: 5px; padding: 5px; border-radius: var(--r-card)`),
each cell a `.theme-swatch` (22×16px, 5px radius, ground fill with two 6px
accent dots) beside a 0.78rem 700 label; an odd last cell spans the row.

### 7.3 Chips, pills, badges, eyebrows

| Pattern | Recipe |
|---|---|
| **Eyebrow** (`.eyebrow`, hero) | `inline-flex; gap: 8px; color: var(--accent); font: 500 0.76rem var(--mono); letter-spacing: 0.1em; uppercase; border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent); background: color-mix(in srgb, var(--accent) 7%, transparent); border-radius: var(--r-ctl); padding: 6px 13px;` with a 7px `--accent` dot |
| **Kicker** (`.kicker`, section heads) | the eyebrow without the box: `color: var(--accent); font: 500 0.74rem var(--mono); letter-spacing: 0.1em; uppercase; margin-bottom: 12px` |
| **Section chip** | see 6.3 |
| **Gold pill** (`.tool .pill`, beta/pro tags) | `font: 700 0.6rem; letter-spacing: 0.06em; uppercase; color: var(--gold); border: 1px solid rgba(255,210,63,.45); background: rgba(255,210,63,.08); border-radius: var(--r-ctl); padding: 2px 7px` |
| **State badge** (`.tg-offline`) | `padding: 3px 8px; border-radius: var(--r-ctl); background: var(--fill-idle); border: 1px solid var(--edge); color: var(--muted); font: 500 0.62rem var(--mono); letter-spacing: 0.12em; uppercase` — a state is neutral, never an alarm colour |
| **Kind tag** (`.tg-pal-kind`) | `font: 700 0.68rem; letter-spacing: 0.08em; uppercase; color: var(--muted); border: 1px solid var(--line); border-radius: var(--r-ctl); padding: 1px 6px` |
| **Toggle chip** (`.tg-plan-offline`) | bordered neutral, mono caps 0.64rem; when on: `color: var(--accent); border-color: color-mix(in srgb, var(--accent) 45%, transparent)` |
| **Ordinal tile** (`.tool-num`) | `24px; border-radius: 7px; font: 700 0.8rem var(--mono); color: var(--card-acc); background: color-mix(in srgb, var(--card-acc) 16%, transparent); border: 1px solid color-mix(in srgb, var(--card-acc) 34%, transparent)` |
| **Info dot** (`.tg-info`) | 16px round (24px on coarse pointers), `border: 1px solid rgba(255,255,255,.28); background: rgba(255,255,255,.06); font: 700 0.62rem/1 var(--mono); cursor: help`; hover inverts to `--accent` fill / `--accent-ink` |

### 7.4 Cards and panels

The resting surface: raised ground, hairline edge, a slightly brighter top
edge as the light source, and — on the dark themes — `--raise-1`.

```css
.panel, .fuel-card, .tool {
    background: var(--bg-2);
    border: 1px solid var(--line); border-top-color: rgba(255,255,255,0.16);
    border-radius: var(--r-card); padding: 22–26px; box-shadow: var(--raise-1); }
.panel-title { font: 700 1.15rem var(--display); }
.panel-head-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
```

Variants:

* **Identity-striped tool card** (`.tool`, home): `::before` 4px top stripe in
  `var(--card-acc)` (set inline per card — a feature hue, never `--accent`);
  a 56px icon tile (`.tool-emoji`: `border-radius: var(--r-card); border: 1px
  solid rgba(255,255,255,.1); background: linear-gradient(180deg,
  color-mix(in srgb, var(--card-acc) 20%, transparent), color-mix(… 7%,
  transparent))`) with a 26px icon in the hue; `h3` 1.25rem display; `p`
  `--muted` 0.96rem; `.go` 0.92rem display 700 in the hue with an arrow that
  slides 4px on hover. Hover: `translateY(-5px); border-color: var(--edge);
  background: color-mix(in srgb, var(--bg-2) 92%, var(--ink))`. Below 560px
  the card becomes a `44px 1fr auto` tap row and hides its paragraph.
* **Edge-accented list card** (`.hm-course-list a`): `background: var(--glass);
  border: 1px solid var(--line); border-left: 3px solid color-mix(in srgb,
  var(--acc) 65%, transparent); border-radius: var(--r-card); padding: 12px
  14px 12px 13px`; hover `border-color: var(--acc); translateY(-2px)`. Name
  `600 15px --ink`, meta `12.5px --muted`. The hue is an edge, never a fill.
* **Notice bar** (`.tg-install`): `display: flex; gap: 10px; background:
  var(--glass); border: 1px solid var(--line); border-radius: var(--r-card);
  padding: 11px 13px` — an 18px accent-stroked icon, 0.85rem text, a bordered
  neutral button, an × .
* **CTA band** (`.cta-band`): glass card, `padding: 52px 28px; text-align:
  center`, radial glow in the theme's secondary hue at the top edge.
* **Drawn phone** (`.hm-phone`): `190×380px; padding: 9px; background:
  var(--bg-2); border: 1px solid var(--line); border-radius: 26px`, screen
  `--bg-0` at 18px radius — the pattern for any device mock.

### 7.5 Floating layers

Toast, tooltip, popover, command palette, tour card — all share
`--shadow-pop`, `--r-card`, a `--line`/`--edge-soft` border and the
`tg-pop-in` entrance.

```css
/* Toast — window.TrailGoatToast(msg, {acc}) in nav.js */
.tg-toast-stack { position: fixed; bottom: 18px; right: 18px; z-index: 4000; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.tg-toast { max-width: min(90vw, 400px); background: var(--bg-1); border: 1px solid var(--line);
    border-left: 3px solid var(--tg-toast-acc, var(--accent)); color: var(--ink); border-radius: var(--r-card);
    padding: 11px 16px; font-size: 0.92rem; line-height: 1.45; box-shadow: var(--shadow-pop);
    opacity: 0; transform: translateY(8px) scale(0.96); transition: opacity var(--dur-layer) var(--ease-snap), transform … ; }
.tg-toast.show { opacity: 1; transform: none; }

/* Tooltip (#tg-tip) and popover (#tg-pop) — tg-tips.js */
#tg-tip { position: fixed; z-index: 9999; max-width: 260px; background: #10231e; border: 1px solid var(--edge-soft);
    color: var(--ink); font-size: 0.78rem; line-height: 1.5; padding: 9px 12px; border-radius: var(--r-card);
    box-shadow: var(--shadow-pop); }   /* 6px CSS-triangle arrow in --edge-soft at --arrow-x */
#tg-pop { width: min(280px, calc(100vw - 24px)); background: #0e211c; padding: 14px 32px 14px 16px; font-size: 0.8rem; color: var(--muted); }
#tg-pop b { color: var(--ink); display: block; margin-bottom: 4px; }

/* Command palette (⌘K) */
.tg-pal-backdrop { position: fixed; inset: 0; z-index: 4500; background: rgba(3,9,7,0.55); backdrop-filter: blur(6px); padding: 12vh 16px 0; }
.tg-pal { max-width: 520px; margin: 0 auto; background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--r-card); overflow: hidden; box-shadow: var(--shadow-pop); }
.tg-pal-input { width: 100%; padding: 16px 18px; background: transparent; border: none; border-bottom: 1px solid var(--line); color: var(--ink); font: 1.05rem var(--body); }
.tg-pal-list { max-height: 320px; overflow-y: auto; padding: 6px; }
.tg-pal-item { display: flex; align-items: baseline; gap: 10px; width: 100%; padding: 10px 12px; border-radius: var(--r-ctl); text-align: left; }
.tg-pal-item.sel { background: var(--fill-selected); }
.tg-pal-hint { padding: 8px 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 0.75rem; }
```

(The two tooltip grounds `#10231e` / `#0e211c` are Forest-era literals; a
standalone build should use `var(--bg-1)`.)

**Tour** (`tg-tour.css`): a spotlight ring `#tg-tour-ring { border: 2px solid
var(--accent); border-radius: var(--r-card); box-shadow: 0 0 0 200vmax
rgba(3,9,7,0.5) }` and a card `#tg-tour { width: min(340px, calc(100vw -
24px)); padding: 16px 18px 14px; font-size: 0.84rem; color: var(--muted) }`
with a 34px goat in the corner, 6px progress dots (`.on` = `--accent`), a
bordered-neutral "Next", an underlined "Skip". Docked variant pins to the
bottom 12px and clears the tab bar via `--tg-tabbar-space`.

### 7.6 Progress and meters

Flat channel, flat fill, no gloss:

```css
.tg-tile-bar { height: 4px; background: var(--fill-idle); border-radius: 999px; overflow: hidden; }
.tg-tile-bar i { display: block; height: 100%; background: var(--accent); transition: width 0.2s linear; }
.tg-tile-size { color: var(--muted); font: 0.64rem var(--mono); font-variant-numeric: tabular-nums; letter-spacing: 0.06em; }
```

### 7.7 Form fields in the chrome

```css
.set-field { display: flex; flex-direction: column; gap: 6px; }
.set-field .field-label { font-size: 0.8rem; font-weight: 600; color: var(--muted); }
.set-field select, .set-field input[type="number"] { width: 100%; background: rgba(0,0,0,0.3); color: var(--ink);
    border: 1px solid var(--line); border-radius: var(--r-ctl); padding: 8px 10px; font: 0.9rem var(--body);
    box-shadow: var(--well); color-scheme: dark; }
.set-field select:focus, .set-field input:focus { outline: none; border-color: var(--accent); }
.set-sec { margin-top: 6px; padding-top: 10px; border-top: 1px solid var(--line); font: 700 0.88rem; }
.set-sec small { display: block; font-weight: 400; font-size: 0.72rem; color: var(--muted); }
input[type="checkbox"] { accent-color: var(--accent); }
```

Focus everywhere: `:focus-visible { outline: 2px solid var(--accent);
outline-offset: 2px }` (offset `-2px` or `1px` inside tight rows). Never
`outline: none` without a replacement border colour.

### 7.8 Collapsible section card: `.rd-section` (the most reused card)

Every planner section, the training cards, the docs — a `<details class="rd-section panel">` whose `<summary>` is a mono-caps band tinted with the section's `--acc`.

```css
.rd-section { padding-top: 14px; padding-bottom: 14px; }
.rd-section:not([open]) > :not(summary) { display: none !important; }
.rd-section.panel { border: 1px solid color-mix(in srgb, var(--acc, var(--line)) 55%, var(--line)); box-shadow: none; }
.rd-section > summary { list-style: none; cursor: pointer; user-select: none; display: flex; align-items: center; gap: 9px;
    font-family: var(--mono); font-weight: 700; font-size: 1.02rem; color: var(--ink); text-transform: uppercase; letter-spacing: 0.02em;
    margin: -14px -24px; padding: 13px 24px;                       /* mirrors the panel's 24px padding — 18px on phones */
    background: linear-gradient(100deg, color-mix(in srgb, var(--acc, var(--muted)) 26%, transparent), transparent 92%);
    border-radius: calc(var(--radius) - 1px); }
.rd-sec-ico { width: 26px; height: 26px; border-radius: 8px; display: grid; place-items: center; background: var(--acc, var(--muted));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.28), 0 2px 5px rgba(0,0,0,0.35); }
.rd-sec-ico .ico { width: 15px; height: 15px; color: #081410; }  /* dark glyph on the hue tile */
.rd-sec-sub { font-family: var(--body); font-weight: 400; font-size: 0.78rem; color: var(--muted); text-transform: none; letter-spacing: 0; }
.rd-section > summary::after { content: '⌄'; margin-left: auto; color: var(--acc, var(--muted)); font-size: 1.1rem; transition: transform 0.18s ease; }
.rd-section[open] > summary::after { transform: rotate(180deg); }
.rd-section[open] > summary { margin-bottom: 14px; border-bottom: 1px solid var(--line); border-radius: calc(var(--radius) - 1px) calc(var(--radius) - 1px) 0 0; }
```

Each section sets its hue inline: `style="--acc: var(--c-fuel)"`. The AI coach panel is `--acc: var(--gold)`.

### 7.9 Stat tiles and figures

```css
/* fuel.css .metric — the hue rides on a 3px top stripe and a blurred corner disc, never the whole card */
.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.metric { position: relative; background: var(--glass-2); border: 1px solid var(--line); border-radius: var(--r-card); padding: 15px 16px; overflow: hidden; }
.metric::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: var(--stat-acc); opacity: 0.9; }
.metric::after  { content: ''; position: absolute; top: -40px; right: -40px; width: 110px; height: 110px; border-radius: 50%; background: var(--stat-acc); opacity: 0.12; filter: blur(8px); }
.metric-label { color: var(--muted); font-family: var(--mono); font-size: max(0.74rem, var(--mono-cap)); font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
.metric-num   { font-family: var(--mono); font-weight: 700; font-size: 1.5rem; line-height: 1.05; color: var(--stat-acc); font-variant-numeric: tabular-nums; }
.metric-unit  { font-size: 0.8rem; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-left: 3px; }

/* fuel.css .course-stat — the quieter tile; figures share one baseline via margin-top:auto */
.course-stat { background: var(--glass-2); border: 1px solid var(--line); border-radius: var(--r-card); padding: 10px 14px; flex: 1 1 110px; display: flex; flex-direction: column; }
.cs-label { font-family: var(--mono); font-weight: 500; font-size: max(0.72rem, var(--mono-cap)); letter-spacing: 0.1em; text-transform: uppercase; white-space: nowrap; }
.cs-sub   { font-size: 0.7rem; color: var(--muted); opacity: 0.85; }
.cs-val   { font-family: var(--mono); font-weight: 700; font-size: 1.2rem; margin-top: auto; padding-top: 3px; }
.cs-val .unit { font-size: 0.72rem; font-weight: 500; letter-spacing: 0.08em; }
```

Which hue a figure wears is semantic and fixed: gain → `--orange` (fuel), loss → `--aqua`, distance → `--moss`, high point → `--gold`, low point → `--teal`, oxygen → `--plum`; water → `--teal`, sodium → `--violet`, carbs → `--gold`, calories → `--orange`. Dashboard counts (`.dash-count`, `.dash-metric`) are the same tile with a hairline only and hover `--fill-hover`. Sizes in use: 1.5rem (metric), 1.45rem (dash metric), 1.2rem (course stat), 1.12rem (course page / dash count), 0.98rem (discover deck). A figure's count-up animation is 620ms cubic ease-out with a 60ms stagger, skipped under reduced motion.

### 7.10 Tables

The canonical data table, `fuel.css .plan-table`:

```css
.plan-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.plan-table th { text-align: left; color: var(--muted); font-family: var(--mono); font-weight: 500; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.1em; padding: 6px 10px; border-bottom: 1px solid var(--line); }
.plan-table th:not(:first-child), .plan-table td:not(:first-child) { text-align: right; white-space: nowrap; }
.plan-table td:not(:first-child) { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.plan-table td { padding: 9px 10px; border-bottom: 1px solid var(--line); }
.plan-table tbody tr:nth-child(even) { background: rgba(255,255,255,0.03); }
.plan-table tbody tr:hover { background: var(--fill-hover); }
.plan-table tbody tr:hover td { border-bottom-color: var(--edge-soft); }
```

First column is the label in the body face, every other column is a right-aligned mono figure. Semantic cell classes: `.t-up` orange 600, `.t-down` aqua 600, `.t-pace` gold 700, `.t-water` teal, `.t-carb` gold, `.t-sep`/`.t-flat` muted; grades `.grade-soft` gold → `.grade-mid` orange → `.grade-hard` coral 700. A wide table sits in a `.plan-scroll { overflow-x: auto }` wrapper — the body never scrolls sideways. A row the map points at flashes `rgba(255,210,63,0.18)` for 1.6s.

**Phone collapse (≤600px).** Rows become cards; the order of the pieces is deterministic:

```css
@media (max-width: 600px) {
    .plan-table thead { display: none; }
    .plan-table, .plan-table tbody { display: block; }
    .plan-table tr { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 14px; row-gap: 3px;
        padding: 11px 4px; border-bottom: 1px solid var(--line); }
    .plan-table td { display: block; padding: 0; border: 0; text-align: left; }
    .plan-table tr::before { content: ""; flex: 1 1 100%; order: 3; }      /* an invisible line break */
    .plan-table td:nth-child(1) { flex: 1 1 100%; order: 1; font-weight: 600; }
    .plan-table td.detail { order: 4; font-size: 0.82rem; color: var(--muted); }
    .plan-table td.detail::before { content: "elapsed "; }                   /* the header, re-injected as a label */
    .plan-table td.plan-none { display: none; }
    .plan-table td.multi { display: contents; }                              /* let a cell's children take their own lines */
}
```

Other table recipes share the header (`.cmp-table` 0.88rem, `.cp-aid-table` 0.88rem / `7px 10px`, `.dv-aid-table` 0.76rem with a 0.64rem header, `.dash-ref-tbl` `min-width: 460px`).

### 7.11 Forms in content

```css
input[type="number"], input[type="text"], input[type="search"], input[type="datetime-local"], input[type="date"], select, textarea {
    background: var(--glass-2); color: var(--ink); border: 1px solid var(--line); border-radius: var(--r-ctl);
    padding: 11px 14px; font-family: inherit; font-size: 1rem; width: 100%; transition: border-color 0.15s;
    color-scheme: dark; -webkit-appearance: none; appearance: none; }
:is(input, select, textarea):focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--ring); }
select option { background: var(--bg-1); color: var(--ink); }
@media (max-width: 860px) { input, select, textarea { font-size: max(1rem, 16px); } }   /* iOS zoom guard */

.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { color: var(--muted); font-size: 0.85rem; font-weight: 500; }
.field-label em { font-style: normal; color: var(--teal); font-weight: 600; }
.field-label small { color: var(--muted); opacity: 0.7; font-weight: 400; }
.field-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; }

/* Slider: a hue gradient track, ink thumb ringed in the accent */
.slider { -webkit-appearance: none; appearance: none; width: 100%; height: 6px; border-radius: 999px;
    background: linear-gradient(90deg, var(--teal), var(--gold), var(--orange)); outline: none; }
.slider::-webkit-slider-thumb { -webkit-appearance: none; width: 22px; height: 22px; border-radius: 50%;
    background: var(--ink); border: 3px solid var(--accent); cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
.slider-hint { color: var(--gold); font-weight: 600; margin-left: 4px; }

/* Segmented (content) — cousin of .unit-toggle with the accent as the selected ink */
.segmented { display: inline-flex; gap: 4px; background: var(--glass-2); border: 1px solid var(--line); border-radius: var(--r-ctl); padding: 4px; }
.segmented button { flex: 1; background: transparent; color: var(--muted); border: none; font: 600 0.9rem inherit;
    padding: 9px 12px; border-radius: calc(var(--r-ctl) - 2px); white-space: nowrap; }
.segmented button.active { background: var(--fill-selected); color: var(--accent); }
@media (max-width: 600px) { .segmented { display: flex; overflow-x: auto; scrollbar-width: none; } .segmented button { flex: 0 0 auto; } }

/* Dropzone */
.dropzone { padding: 32px 20px; border: 1.5px dashed var(--line); border-radius: var(--r-card); background: var(--glass-2); text-align: center; }
.dropzone:hover, .dropzone.dragover { border-color: var(--accent); background: var(--fill-hover); }

/* Checkbox / radio */
input[type="checkbox"], input[type="radio"] { accent-color: var(--accent); }
/* Disclosure */
.advanced summary::before { content: '＋ '; color: var(--accent); }  .advanced[open] summary::before { content: '－ '; }
```

Status text: `.estimate-out { color: var(--muted); font-size: 0.85rem }` with `strong` in gold mono; `.ok` → `--moss`, `.warn` → `--coral`. The **danger pattern is muted, not red**: a destructive button is `background: none; color: var(--muted); border: 1px solid transparent` that steps the ladder on hover; an *armed* one turns `--coral`. The single true red button (account deletion) is `rgba(255,93,115,.08)` fill, `rgba(255,93,115,.55)` border, `#ff8d9d` text.

### 7.12 Empty, loading, skeleton

* **Empty state**: centred column, `gap: 12px; padding: 20–28px; color: var(--muted)`, a 30px feature-hue icon, `p { max-width: 26–30rem }`. Framed variants use `border: 1px dashed var(--line); border-radius: var(--r-card); background: var(--glass)`.
* **Skeleton** (`library.css`): `.lib-skel { border: 1px solid var(--line); border-radius: var(--r-card); padding: 14px; background: var(--glass) }`, lines `height: 12px; border-radius: 6px; background: linear-gradient(90deg, rgba(255,255,255,.05) 25%, rgba(255,255,255,.12) 50%, rgba(255,255,255,.05) 75%); background-size: 200% 100%; animation: lib-shimmer 1.3s ease-in-out infinite` at 100/60/40% widths. Off under reduced motion.
* **Working**: the mascot trots — `.tp-goat { width: 84px; animation: tp-trot 1.2s ease-in-out infinite }` (`50% { translateY(-7px) rotate(-4deg) }`) inside `text-align: center; padding: 64px 24px`.
* **Progress**: 4px channel, flat fill (7.6); gradient fills only for the two brand meters (`--teal → --moss` training progress, `--orange → --gold` site performance). The food-pack coverage bar is the one deliberately glossy meter (`fuel.css .fp-cov-*`).

### 7.13 Modals and dialogs

Backdrop `rgba(3,9,7,0.8)` (or `.55` + `blur(6px)` for the palette), centred or `align-items: flex-start; padding: 4vh 16px` for tall content. Box: `width: min(440–620px, 100%); max-height: 92vh; overflow-y: auto; background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--r-card); box-shadow: var(--shadow-pop); padding: 22–26px`. Choice rows `.tg-modal-choice { background: var(--glass-2); border: 1px solid var(--line); border-radius: var(--r-card); padding: 14px 16px }`. Step dots `height: 4px; flex: 1; border-radius: 999px; background: var(--line)` → `.on { background: var(--accent) }`. `body.*-open { overflow: hidden }` while open. Native `confirm()` stays for destructive confirms on purpose.

### 7.14 Chat bubbles (AI coach)

`.coach-msg { max-width: 85%; padding: 10px 14px; border-radius: var(--r-card); font-size: 0.92rem }`; user `background: var(--fill-selected); border-bottom-right-radius: 4px`; assistant `background: rgba(25,195,177,.08); border: 1px solid rgba(25,195,177,.28); border-left: 3px solid var(--teal); border-bottom-left-radius: 4px`. The brand lockup `.coach-brand` is display 800 with GOAT + AI in `.grad`.

### 7.15 Reading list of "3px left edge" notices

A 3px left border in a hue is the site's notice signature: the toast, `.dash-week` (teal), `.crew-card` (`--pc`), `.coach-assistant` (teal), `.dash-ref-thesis` (gold), the edge-accented course cards. Use it for "this row belongs to X" and for a callout; never a filled coloured box.

---

## 8. Maps

Everything is `static/trail-map.js` → `TrailGoatMap.createMap(elId, course, opts)`; nothing calls `L.map()` directly. Leaflet 1.9.4 from a CDN. Colours are read at call time with `tok(name, fallback)` so a theme switch is picked up on the next redraw (`tg:theme` event).

**Container.**

```css
.map-wrap { position: relative; isolation: isolate; border-radius: var(--r-card); overflow: hidden; border: 1px solid var(--line); }
.leaflet-container { background: var(--bg-1); font-family: inherit; }
#course-map { height: 425px; }             /* planner; 380px on course pages; 450px creator/preview */
#mini-map   { height: clamp(240px, 34vh, 440px); }   /* planner left rail, ≥861px only */
#base-map   { height: clamp(450px, 72vh, 775px); }   /* empty-state base map */
#embed-map  { flex: 1 1 0; min-height: 150px; }      /* iframe: fills the frame; 220px on phones */
.map-wrap.map-expanded { position: fixed; inset: 0; z-index: 9999; border: none; border-radius: 0; }
body.map-modal-open { overflow: hidden; }
```

`isolation: isolate` is load-bearing: it keeps Leaflet's z-400 panes and z-1000 controls inside the card. A Leaflet map with no explicit height renders 0px tall.

**Construction.**

```js
const map = L.map(elId, { zoomControl: !opts.zoomPosition, scrollWheelZoom: !!opts.scrollWheelZoom,
  dragging: !coarsePointer,            // phone: one finger scrolls the page, two fingers pan; drag returns when expanded
  preferCanvas: true, renderer: L.canvas({ padding: 0.5 }), zoomSnap: 0.5, zoomDelta: 0.5 });
map.attributionControl.setPrefix(false);
map.fitBounds(line.getBounds(), { padding: [22, 22] });    // re-run at 220ms and on resize
```

Tile layers (`{ crossOrigin: true, updateWhenIdle: false, keepBuffer: 4, maxZoom: 19 }`), default USGS in the US, Terrain elsewhere:

| Name | URL | maxNativeZoom |
|---|---|---|
| USGS topo | `https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}` | 16 |
| Terrain | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}` | 19 |
| OpenTopo | `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png` | 17 |
| Satellite | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | 19 |
| Dark | `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png` | 19 |

**Route and markers.**

```js
L.polyline(latlngs, { color: "#000", weight: 7, opacity: 0.35 });                                  // casing
L.polyline(latlngs, { color: tok("--c-fuel"), weight: 4, opacity: 1 });                              // the route, fuel orange; 520ms fade-in
L.circleMarker(start,  { radius: 6, color: "#04201d", weight: 2, fillColor: tok("--c-pace"), fillOpacity: 1 });   // start — pace green
L.circleMarker(finish, { radius: 6, color: "#04201d", weight: 2, fillColor: tok("--c-climb"), fillOpacity: 1 });  // finish — climb red
L.circleMarker(p, { radius: 7, color: "#fff", weight: 2, fillColor: tok("--c-fuel"), fillOpacity: 1 });        // hover/scrub dot
// aid stations: a 7-step hue cycle, DOM markers so they can be styled
const AID_TOKENS = [["--c-course"],["--gold"],["--c-gear"],["--c-fuel"],["--c-pace"],["--c-climb"]]; // then --aqua
L.marker(pt, { icon: L.divIcon({ className: "aid-marker-wrap", iconSize: [26,26], iconAnchor: [13,13],
  html: `<span class="aid-marker" style="background:${aidColor(i)}">A</span>` }) })
 .bindTooltip(`${name} · ${dist} ${unit}`, { direction: "top" });
// night: dark casing then dashed violet, non-interactive, brought to front
L.polyline(seg, { color: "#0d1030", weight: 9, opacity: 0.85, interactive: false });
L.polyline(seg, { color: tok("--c-gear"), weight: 3, opacity: 0.95, dashArray: "7 5", interactive: false });
// highlight a span
L.polyline(seg, { color: tok("--gold"), weight: 7, opacity: 0.95 });
// surface overlay: weight 5; paved --muted, gravel --gold, trail --moss, unknown --muted @ .55 dashArray "4 8"
```

```css
.aid-marker { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; color: #06140f;
    font-family: var(--display); font-weight: 800; font-size: 0.92rem; border: 2px solid rgba(255,255,255,0.92); box-shadow: 0 1px 5px rgba(0,0,0,0.5); }
.aid-marker-wrap.aid-mini .aid-marker { width: 11px; height: 11px; font-size: 0; }   /* >12 aids at zoom ≤11, and the mini map */
.aid-marker-wrap.aid-hover .aid-marker { transform: scale(1.45); box-shadow: 0 0 0 4px rgba(255,255,255,0.25), 0 0 18px 2px rgba(255,255,255,0.35); }
.aid-badge { width: 18px; height: 18px; font-size: 0.72rem; }                          /* the table's twin */
.tg-mile { width: 22px; height: 22px; border-radius: 50%; background: rgba(7,18,15,0.88); color: var(--gold); border: 1.5px solid var(--gold);
    font: 700 0.62rem var(--mono); display: grid; place-items: center; }               /* distance pucks every 1/5/10 units */
.leaflet-div-icon.aid-marker-wrap, .tg-mile-wrap { background: transparent; border: 0; }
```

**Controls** — one glass recipe, bottom-right (expand ⤢, locate, 3D; zoom above them when requested), play/speed bottom-left, layers top-right (collapsed on phones), scale bottom-left `{ imperial: true, metric: true, maxWidth: 110 }`:

```css
.map-expand-btn, .map-locate-btn, .map-3d-btn, .map-play-btn, .map-speed-btn {
    width: 32px; height: 32px; background: rgba(7,18,15,0.92); color: var(--ink); border: 1px solid var(--line);
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.45); display: grid; place-items: center; cursor: pointer; }
:is(.map-expand-btn, .map-locate-btn, .map-3d-btn):hover { border-color: var(--edge-soft); color: var(--accent); }
@media (max-width: 860px) { .map-expand-btn, .map-locate-btn, .map-3d-btn, .map-play-btn { width: 42px; height: 42px; } }
.leaflet-control-layers { background: rgba(7,18,15,0.92) !important; border: 1px solid var(--line); border-radius: var(--r-card); box-shadow: var(--shadow-pop); padding: 8px 12px; }
.leaflet-control-layers input { accent-color: var(--accent); }
.tg-inspect .leaflet-popup-content-wrapper { background: rgba(7,18,15,0.94); border: 1px solid var(--line); border-radius: var(--r-card); box-shadow: var(--shadow-pop); }
.tg-inspect .leaflet-popup-content { font: 600 0.88rem/1.45 var(--body); color: var(--ink); }  .tg-inspect b { color: var(--gold); }
.tg-map-toast { position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%); z-index: 900; background: rgba(4,12,10,0.82);
    border-radius: var(--r-ctl); padding: 10px 18px; font: 600 0.88rem var(--body); opacity: 0; transition: opacity 0.25s ease; }
```

(`rgba(7,18,15,…)` is Forest's `--bg-0` at alpha — in a standalone build use `color-mix(in srgb, var(--bg-0) 92%, transparent)`.)

**Mini map.** Same factory with `{ playback: false, threeD: false, distanceMarkers: false, scaleBar: false, aidDots: true, scrollWheelZoom: true }`, fed by the main handle's `setHoverByIndex / setAidHover / highlightSpan / setAids / setNightSpans / refreshUnits` so both maps agree. The "you are here" locate marker is the mascot: `L.divIcon({ className: "tg-you-goat", html: '<img src="/img/goat-pin.png" width="33" height="44">', iconAnchor: [16, 43] })`.

**3D.** MapLibre GL 4 lazy-loaded, Esri imagery over the AWS terrarium DEM, `fitBounds(b, { padding: 60, pitch: 68, bearing: 20 })`; flythrough duration `clamp(40s, mi × 700ms, 90s)`. Badge `.tg-3d-badge`: mono 700 0.66rem gold on `rgba(7,18,15,.85)` with a `rgba(255,210,63,.45)` border.

**Discover pins** are their own system: `.dv-dot` gold divIcon with a dark ring and `0 0 6px rgba(255,210,63,.4)` glow; community pins `--moss`; `.dim` desaturated; `.dv-you` a pulsing teal dot (`dv-you-pulse 2.4s` to a 14px transparent ring).

---

## 9. Charts

Chart.js 4.4.1. Only two `new Chart()` sites exist — the elevation profile (`trail-map.js createProfile`) and the hourly weather chart — everything else (sparklines, week bars) is hand-rolled CSS or inline SVG `<polyline>`. One global default:

```js
Chart.defaults.font.family = tok("--body", "'Red Hat Text', -apple-system, BlinkMacSystemFont, sans-serif");
```

Colours are read per build so a theme switch redraws correctly (`tg:theme` listener → rebuild):

```js
const lightTheme  = luminance(tok("--bg-1")) > 140;
const mutedTick   = tok("--muted");
const gridLine    = lightTheme ? "rgba(33,48,42,0.08)" : "rgba(255,255,255,0.05)";
const crossLine   = lightTheme ? "rgba(33,48,42,0.45)" : "rgba(255,255,255,0.45)";
const traceColor  = tok("--c-course");                    // the elevation line — course teal/cyan
const hoverColor  = tok("--c-fuel");
const climbShade  = rgbaOf(tok("--c-fuel"), 0.16);       // washes under the trace
const descentShade= rgbaOf(tok("--c-aid"), 0.14);
const tipBg = rgbaOf(tok("--bg-1"), 0.94), tipInk = tok("--ink"), tipEdge = lightTheme ? "rgba(33,48,42,0.14)" : "rgba(255,255,255,0.12)";

const grad = ctx.createLinearGradient(0, 0, 0, 220);      // fill under the trace: the trace hue at .45 → .02
grad.addColorStop(0, rgbaOf(traceColor, 0.45)); grad.addColorStop(1, rgbaOf(traceColor, 0.02));

new Chart(ctx, {
  type: "line",
  data: { datasets: [{ data, borderColor: traceColor, backgroundColor: grad, fill: "origin",
          borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: hoverColor, tension: 0.2 }] },
  options: {
    responsive: true, maintainAspectRatio: false, parsing: false, normalized: true,
    animation: reducedMotion ? false : { duration: 700, easing: "easeOutQuart", onComplete: a => { a.chart.options.animation = false; } },
    interaction: { mode: "index", intersect: false, axis: "x" },
    onHover: (e, els) => map.setHoverByIndex(els.length ? els[0].index : null),   // chart → map sync
    scales: {
      x: { type: "linear", min: 0, max: totalDist, title: { display: true, text: `Distance (${unit})`, color: mutedTick },
           ticks: { color: mutedTick, maxTicksLimit: 7 }, grid: { color: gridLine } },
      y: { title: { display: true, text: `Elevation (${eleUnit})`, color: mutedTick }, ticks: { color: mutedTick, maxTicksLimit: 6 }, grid: { color: gridLine } } },
    plugins: { legend: { display: false },
      tooltip: { backgroundColor: tipBg, borderColor: tipEdge, borderWidth: 1, titleColor: tipInk, bodyColor: tipInk, padding: 10, displayColors: false } } },
  plugins: [altZones, nightShade, spanHover, segShade, crosshair, aidLines, surfRibbon],
});
```

Plugin conventions: washes (`segShade`, `nightShade` at `rgba(124,104,255,.17)` with dashed `rgba(158,140,255,.6)` edges, `altZones` bands at 1000/2500/3500 m, `spanHover` `rgba(255,210,63,.2)`) draw in `beforeDatasetsDraw`; line art (`crosshair` 1px dashed `[4,4]`, `aidLines` per-aid dashed `[3,3]` in `aidColor(i)` with an 8px "A" badge in `700 10px 'Red Hat Display'`, `surfRibbon` a 12px band at the plot's foot labelled PAVED/GRAVEL/TRAIL in `700 9px`, `avgLine` dashed `[6,5]` `rgba(255,93,115,.7)`) draws in `afterDatasetsDraw`, so the built-in tooltip stays on top. Canvas text names the family directly (canvas cannot read a token) with the same fallback stack.

Overlay toggle pills above the chart (`.tg-elev-toggles`): `.tg-tog { padding: 6px 12px; border-radius: var(--r-ctl); background: var(--glass-2); border: 1px solid var(--line); font: 600 0.8rem }` with a 9px dot in the layer's hue at `opacity: .3`, `.on { color: var(--ink); border-color: var(--tg); background: color-mix(in srgb, var(--tg) 13%, transparent) }`. Layer hues: aids `--c-course`, climbs `--c-fuel`, descents `--c-aid`, night `--c-gear`, altitude `--gold`, distance markers gold.

Chart containers: `.elev-canvas-wrap { position: relative; height: 260px }` (140px mini, 210px weather, 96px deck profile, 58px sparkline). Fullscreen `.elev-expanded { position: fixed; inset: 0; z-index: 9999; background: var(--bg-1); padding: 58px 16px 22px }` with a 44px round close.

Weather chart: `tension: 0.4; borderWidth: 2.5; y position: 'right'`, a horizontal temperature-coloured stroke gradient (cool→warm across the day), a vertical fill `rgba(255,170,80,.30) → .10 → rgba(120,180,200,.02)`, weather glyphs drawn onto the canvas with `TrailGoatIcons.draw()`, and a 1.5px `rgba(255,122,26,.85)` race-start line.

Hand-rolled sparklines: inline `<svg>` `<polyline fill="none" stroke="var(--hue)" stroke-width="2">` over a `<path>` fill at `color-mix(in srgb, var(--hue) 18%, transparent)` (the drawn phone on the home page is the reference); week bars `height: 5px; border-radius: 999px; background: rgba(255,255,255,.08)` with a hue fill.

---

## 10. Iconography

**Rule (KRI-200):** no emoji anywhere. Every pictogram is 24×24 line art, `fill: none; stroke: currentColor; stroke-width: 1.7–1.75; stroke-linecap: round; stroke-linejoin: round`, so one CSS colour drives the whole set and it inherits size from its slot. The drawn goat (`/img/goat.png` hero, `/img/goat-pin.png` small) is the single image exception; the generic goat emoji is never used.

`static/icons.js` → `window.TG_ICON(name, cls?)` returns `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">…</svg>`; `TrailGoatIcons.draw(ctx, name, x, y, size, color)` renders the same art on a canvas; `TrailGoatIcons.weather(wmoCode, isDay)` maps Open-Meteo codes; `TrailGoatIcons.waypoint(type)` maps pin types.

Names: **navigation** `gauge flag pen pulse calendar search sliders` · **weather** `sun moon partly cloud fog drizzle rain snow storm sunrise sunset thermometer droplet wind clock` · **activity** `runner mountain home check map mail pin` · **waypoints** `parking signpost crew restroom hazard chart download`. Aliases `partlycloudy→partly showers→rain thunder→storm`. The nav template carries its own parse-time set (`flag compass pen grid search cal crew sliders list embed book help info price route more back reload`) because it runs before icons.js.

Sizes: `.ico` 15px in buttons and rows, 13px in nav rows, 16px on the search/gear squares, 20px in the tab bar and back arrow, 26px in a tool-card tile, 30px in an empty state. Icons inside a hue tile are dark (`#081410`); everywhere else they inherit.

Residual glyph characters where a drawn icon would be overkill: `⤢ ✕` expand/close, `▶ ❚❚` playback, `⌄` disclosure chevrons, `⌘K`, `·` separators, `→` arrows in `.go` links.

---

## 11. Motion, touch, accessibility

**Motion.** `--ease-snap` + `--dur-ctl` (150ms) for controls, `--dur-layer` (250ms) for arriving layers, `tg-pop-in` as the one entrance with a per-consumer `transform-origin`. Hover lifts are `translateY(-1px)` (buttons) to `-5px` (tool cards) over 130–180ms. Reveal-on-scroll is progressive enhancement: content is visible until `html.reveal-armed` confirms an IntersectionObserver exists. Longer effects and their budgets: route fade 520ms, chart draw-on 700ms easeOutQuart then off, count-up 620ms, toast 3600ms visible, tour ring 180ms, playback `clamp(30s, mi×600ms, 75s)`. The only infinite loops are the mascot's idle bob (3.2s) and the trotting loader — and both stop under reduced motion.

**Reduced motion.** Every animation and hover transform has a `@media (prefers-reduced-motion: reduce)` suppression that keeps the *end state* (28 such blocks across the stylesheets). In JS, `matchMedia("(prefers-reduced-motion: reduce)").matches` is an early return. The suppression for a late-defined layer goes at the **end** of the file — equal specificity, later wins.

**Touch.** 44px is the floor for anything a thumb presses (48px sheet rows, 46px panel rows, 40px section chips and footer links, 42px map buttons on phones). `touch-action: manipulation` and no tap highlight, globally. `pointer: coarse` grows the 16px info dot to 24px and turns off map dragging (two-finger pan) until the map is expanded. Inputs are `max(1rem, 16px)` on phones so iOS does not zoom.

**Focus.** `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }` (negative or 1px offsets inside tight rows). Inputs swap the outline for `border-color: var(--accent); box-shadow: 0 0 0 3px var(--ring)`.

**Semantics.** Dropdowns are real `<a>` triggers (crawlable, middle-clickable) that JS upgrades; `aria-current="page"` drives active styling; `aria-expanded` drives carets and open states; toasts live in an `aria-live="polite"` stack; dialogs carry `role="dialog" aria-modal="true"`; decorative SVG is `aria-hidden`. Text set via `textContent`, never innerHTML, for user-supplied strings.

**Contrast.** Dark themes: `--ink` on `--bg-0` ≈ 12:1+; `--muted` ≥ 5:1. Feature hues are marks, not copy — when a hue must be text on First Light it is darkened to `color-mix(in srgb, var(--hue) 86%, #000)`.

**The `[hidden]` trap.** Any component that sets `display` must restate `.thing[hidden] { display: none }` — an author `display` beats the UA rule. It bites every few PRs.

---

## 12. Page recipes

**The split app shell** (`body.split-page`, planner / Race Day / creator) — desktop ≥861px only:

```css
body.split-page { display: flex; flex-direction: column; height: 100dvh; overflow: hidden; }   /* the page never scrolls */
body.split-page .wrap { max-width: none; width: 100%; margin: 0; padding: 0 clamp(16px, 2vw, 30px); flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
body.split-page .foot { display: none; }
body.split-page .hero h1 { font-size: clamp(1.35rem, 2.2vw, 1.85rem); }  body.split-page .hero-sub { display: none; }
.app-split { flex: 1 1 auto; min-height: 0; display: grid; grid-template-columns: minmax(320px, 400px) 1fr; gap: 18px; padding-bottom: 14px; }
.split-left, .split-right { min-height: 0; overflow-y: auto; overscroll-behavior: contain; display: flex; flex-direction: column; gap: 16px; padding-right: 4px; }
.split-left { border-right: 1px solid var(--line); padding-right: 18px; }
.split-left::-webkit-scrollbar, .split-right::-webkit-scrollbar { width: 9px; }  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 8px; }
```

The left rail holds the course card (mini map + stats), the right pane the sections; the section chips sit sticky at the top of the right pane; a `.rd-fade` gradient marks the pane's scroll edges; `html.rd-rail-closed` collapses the rail to 0 with a pull-tab. Below 860px everything stacks and the page scrolls.

**Dashboard** (`.dash-wrap` 1180px, `padding: 26px 20px 60px`): `.dash-grid { grid-template-columns: 300px 1fr; gap: 18px }` (1fr ≤900px), a sticky side column, count tiles, week cards with a teal edge, metric tiles in `repeat(3, 1fr)`.

**Discover**: the map fills the stage (`position: fixed; inset: 0; top: var(--topbar-h)`), a deck of course cards over it, chip rows with the same edge-fade masks as the section chips, `.dv-stat` tiles at deck size (`padding: 8px 10px 7px`, 2px stripe).

**Course / SEO page** (`.cp-wrap` 1040px): h1 `clamp(1.6rem, 4vw, 2.4rem)`, `.cp-stats` tiles `minmax(140px, 1fr)`, a 380px map, `.cp-aid-table`, a rating badge (13px stars pinned `fill: var(--gold)`, empty `var(--line)`), review cards, edge-accented related-course tiles.

**Info / docs** (`.info-wrap` 880px, wide 1060px): prose at `0.98rem/1.65`, `max-width: 68ch`; group headers are a mono-caps word with a hairline running out to the right (`::after { flex: 1; height: 1px; background: var(--line) }`); check lists use a drawn 13×8 tick in `--moss` (`border-left/bottom: 2.2px solid; rotate(-45deg)`).

**Pricing**: `.pr-grid { repeat(auto-fit, minmax(240px, 1fr)); gap: 14px }`; `.pr-card { border: 1px solid var(--line); border-radius: var(--r-card); padding: 22px; background: color-mix(in srgb, var(--bg-1) 88%, transparent); display: flex; flex-direction: column; gap: 10px }`, the featured tier `border-color: var(--accent)`; `.pr-tier` mono caps 0.82rem muted; `.pr-price` display 800 2rem with `small` 0.95rem; feature rows with a 9×5 teal tick; the CTA pinned to the foot with `margin-top: auto`, full width; the "Request it" button in gold.

**Print** (`print.css`): white paper, ink `#16211c`, body 10.5pt; h1 display 800 20pt, brand line `2.5pt solid #e8620c`; h2 display 700 12.5pt `#b34a06`; tables 9.5pt with 7.5pt mono-caps headers over a `1.5pt solid` rule, `0.75pt solid #dfe5e0` row rules, zebra `#f4f6f4`; all dark-ground colour classes neutralised (`color: inherit !important`); `@page { margin: 14mm 12mm 18mm }`; `thead { display: table-header-group }`, `tr, .tile { break-inside: avoid }`; the print palette is First Light's hues (`--p-orange #d95f10 --p-gold #b3821a --p-moss #55870a --p-teal #0d8a7a --p-violet #6a4fd0 --p-coral #d13b5c --p-aqua #0f7fbe --p-fern #1f8a52`); section heads get a `3pt` left rule in `--acc` over a 9% wash with `print-color-adjust: exact`.

**Embed** (`/course/{slug}/embed`): chromeless flex column — `.em-head` (h1 + stats + GPX button) · `.map-wrap > #embed-map` (flex-fills) · `.em-elev` canvas capped 125px · `.em-foot` — on `tokens.css + fuel.css` only, theme from `?theme=` via `TrailGoatTheme.preview()`, `?bg=transparent` drops the backdrop. The builder page previews it in a drawn browser frame and writes `?embed=` so the preview never becomes the visitor's theme.

---

## 13. Checklist for a new surface

Before calling a page done:

- [ ] Loads `tokens.css` first, then its own sheet, `tg-store.js` un-deferred, `nav.css` after; fonts link is the exact Red Hat trio with `display=swap`.
- [ ] Sits on `.backdrop` + `.aurora`; body `--bg-0`, ink `--ink`, `overflow-x: clip`.
- [ ] Exactly one solid `--accent` button, or none. Every other verb is `.export-btn` (bordered neutral) or an underlined text action.
- [ ] Feature hues appear only on data, icons, stripes and edges — never on chrome.
- [ ] Two radii. Hairline edges. `--shadow-pop` only on layers that float.
- [ ] Headlines in `--display`, copy in `--body`, labels in mono caps ≥ `--mono-cap`, every figure `.data`/tabular with the unit tracked out.
- [ ] Section heads are `.kicker` + display `h2`, or a `.rd-section` summary band in the section's hue.
- [ ] Tables: mono-caps header, right-aligned mono figures, zebra `rgba(255,255,255,.03)`, hover `--fill-hover`, card collapse ≤600px, wrapper scrolls not the body.
- [ ] Icons from `icons.js`; no emoji; the goat is a PNG.
- [ ] Phone pass at 390px: sticky blurred topbar, 44px targets, `--mono-cap` 12px, grids collapsed, nothing overlapping; installed-app tab bar clears `env(safe-area-inset-bottom)`.
- [ ] `prefers-reduced-motion` suppresses every animation and hover transform; `:focus-visible` rings on every control; `[hidden]` restated wherever `display` is set.
- [ ] Maps via `TrailGoatMap.createMap`, charts via the profile recipe, colours through `tok()`; a `tg:theme` listener redraws canvases.
- [ ] Asset version bumped in `app/assets.py`; changelog entry under `changelog/`; the relevant `evals/test_*.py` still green (`test_fonts.py`, `test_theme_roster.py`, `test_map_theme.py`).

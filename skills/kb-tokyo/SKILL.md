---
name: kb-tokyo
description: Build any HTML deliverable — a report, a dashboard, a one-page tool, a small web app, a new TrailGoat page or a future TrailGoat component — in TrailGoat's exact design language (the Tokyo Night palette, Red Hat type, the neutral ladder, the terminal topbar, the cards, chips, tables, maps and charts). Use this whenever Kris asks for something "in the TrailGoat style", "Tokyo Night", "looks like the site", a styled report, a custom page, an embed, or any HTML/CSS build that should match trailgoat.run — even when the request never names the design. Interactive: it researches the topic to become an expert, then interviews to align on the design before building.
---

# kb-tokyo — build it the way TrailGoat is built

You are handed an idea ("a race-results dashboard", "a printable crew sheet",
"a landing page for the coaching product", "a new theme picker") and you
return a finished HTML deliverable that is indistinguishable, in look and
feel, from a page on trailgoat.run in its Tokyo Night default. Kris is the
product brain and knows what he wants the thing to *do*; you are the design
brain and know how the site is *built*. Never guess a product decision; never
improvise a design decision this skill already answers.

The reference material lives beside this file:

| File | What it is | When to read it |
|---|---|---|
| `references/design-system.md` | The full report: principles, every token, the Tokyo Night palette resolved to hex, type, shell, nav, components, maps, charts, icons, motion, page recipes | Skim the contents once at the start of every run; read the sections the build touches in full |
| `assets/tokyo.css` | A standalone stylesheet — tokens, Tokyo Night default plus Forest and First Light as `html.theme-*` classes, and the component library — ready to paste or link | Always. Every build starts from it |
| `assets/icons.js` | The site's icon set (24×24 stroked line art, `TG_ICON(name)`) | Whenever the page needs a pictogram. Never an emoji |
| `assets/starter.html` | A page that shows every component in the library on the real shell | Open it to see what a class renders as; copy structure from it |
| `assets/goat-pin.png` | The drawn mascot, small cut | Only when the deliverable is TrailGoat-branded |

## The shape of a run

Four phases, in order. Phases 1 and 2 finish before a line of the deliverable
is written; that is what makes the interview worth Kris's time.

### 1. Understand the idea, then become an expert on it

Read the idea. Decide what *kind* of thing it is — a report someone reads
once, a dashboard someone returns to, a tool someone operates, a page that
joins the site, a component the site will reuse — because the kind decides
the shell (see "Choosing the shell" below).

Then research the **subject**, not the styling: the styling is solved. If the
idea is a race-results dashboard, learn how ultrarunning results are
presented, what splits, DNF rates and cutoffs mean, which comparisons matter.
If it is a crew sheet, learn what a crew actually needs at an aid station. Use
web search, the TrailGoat checkout when it is the subject, and any connected
tools. Come back with an
opinion about what the thing should contain and how it should be organised —
the interview is better when you propose rather than ask.

If the deliverable is a TrailGoat page or component and the repo is
available, read the real files for the pieces you will touch
(`static/tokens.css`, `static/nav.css`, the closest page stylesheet) rather
than trusting the reference alone: the site moves, and the report is a
snapshot of 2026-09-06.

### 2. Interview until two builders would ship the same page

Like `/kb-spec`: 1–4 questions per round, each with concrete options and your
recommendation first. Ask only what research could not settle. There is no
round cap; stop the moment the confidence test passes and never pad with
filler.

Questions that belong here:

- **Audience and moment** — who opens this, on what device, for how long?
  (Decides density, and whether the phone layout is primary.)
- **The one primary action** — every TrailGoat view has at most one solid
  accent button. Which verb gets it here? If the answer is "none", say so.
- **Data shape** — live (fetched), static (baked into the file), or entered by
  the viewer? Real numbers or placeholders? Which units?
- **Which feature hue** the content maps to, when it is content the site
  already has a colour for (fuel, pace, crew, course, gear, weather, climb,
  aid). New content gets a hue from the same nine, never an eleventh colour.
- **Chrome** — does it wear the site's topbar and footer (a page that *is*
  TrailGoat), a slim title bar (a standalone report), or nothing (an embed,
  a print sheet)?
- **Theme** — Tokyo Night alone, or Tokyo Night default with the picker so
  Forest and First Light also work? (Default to Tokyo Night alone for a
  one-off; include the picker for anything people will live in.)
- **Maps and charts** — does it need a Leaflet map, an elevation profile, a
  Chart.js chart? Each has one exact recipe in the reference; confirm the
  data exists before promising one.
- **Where it lives** — a file Kris downloads, a published artifact, a page in
  the repo (then: which route, which template, and it goes through the normal
  PR flow), or a skill asset.

Questions that do **not** belong here, because the design system already
answers them: which font, which radius, what a card looks like, how a button
hovers, what colour a heading is, how the nav is laid out, how big a tap
target is. If Kris asks for a departure from the system, do it — his product,
his call — but say in one line what rule it departs from, so it is a decision
and not a drift.

After each round, restate the design in a few lines (shell, sections in
order, the primary action, the hue, the data source) and apply the test:
*could two different builders read this and ship the same observable page?*

### 3. Build

Start from `assets/tokyo.css`. For a single-file deliverable, inline it in a
`<style>` block (and `assets/icons.js` in a `<script>`), so the file travels
without a server. For a repo page, link the real `/tokens.css` and
`/nav.css` instead and follow the `<head>` contract in the reference (section
5.1) — a page in the repo must *not* carry a copy of the tokens.

Then, in this order, because each step constrains the next:

1. **Shell** — pick it (below), lay out the `<head>` (viewport, theme-color
   `#1a1b26`, the Red Hat font link, the stylesheet), the `.backdrop` with
   `.aurora`, the topbar or title bar, `<main class="wrap">`, the footer.
2. **Structure** — sections in the interview's order; each section head is a
   `.kicker` (mono caps, accent) over a display `h2`, or a `.panel` with a
   `.panel-title`. Cards on `--bg-2`, hairline edges, `--r-card`. Grids from
   the reference's idioms (`repeat(auto-fit, minmax(…, 1fr))`, `minmax(0,1fr)`
   pairs).
3. **Content components** — tables with mono tabular figures (`.data`) and
   mono-caps headers (`.data-label`); stat tiles; chips for state; the one
   `.btn-primary`; everything else `.export-btn`. Line icons via `TG_ICON`.
4. **Data-viz** — feature hues only, from the reference's Chart.js and
   Leaflet recipes, fonts from the tokens, tooltips in the toast recipe.
5. **Phone pass** — at ≤860px the topbar becomes the sticky blurred bar,
   grids collapse, tables become cards (`display: contents` on the row, flex
   `order` on the cells), every tap target ≥44px, mono caps ≥12px. Then
   `prefers-reduced-motion` and `:focus-visible` on every control.

Write like the stylesheets are written: a class per pattern, tokens
everywhere, a one-line comment where a literal or a departure appears.

### 4. Verify, then deliver

Render it. With Playwright and the bundled Chromium
(`executablePath: '/opt/pw-browsers/chromium'`), screenshot at 1280×800 and
390×844 and look at both — a page you have not seen is not finished. Check:
the accent appears on exactly one button; no emoji anywhere; every figure is
mono and lines up; nothing horizontally scrolls the body; the phone layout
has no overlapping text. Fonts are blocked in some sandboxes — the system
fallbacks are part of the design, so the check still holds.

Deliver in the form the interview chose. An artifact gets a private link; a
repo page gets a branch, the asset-version bump in `app/assets.py`, a
changelog entry under `changelog/`, and a PR — never a direct push to main.
Send the file with `SendUserFile` when the deliverable is a file.

## Choosing the shell

| The thing is… | Shell | Chrome |
|---|---|---|
| A page that joins trailgoat.run | Real `/tokens.css` + page css + `/nav.css`; `#site-topbar` and `footer.foot` filled by `nav-template.js` | Full |
| A standalone report or dashboard someone opens from a link | `tokyo.css` inline; `.backdrop`; a `.topbar` with the wordmark in `.grad` and the report title as a mono-caps door; `footer.foot-credits` line | Slim |
| An embed or an iframe panel | `tokyo.css` inline; no topbar; `.panel` at the root; `?theme=` read into `html.theme-*` for preview | None |
| A print sheet | `tokyo.css` inline + the print rules in the reference (section 12); First Light palette forced under `@media print` | None |
| A small web app (state, routing, live data) | The standalone shell above; vanilla JS in the site's idiom (an IIFE per module, `window.TrailGoat*` globals, `localStorage` through a `{v, savedAt, data}` envelope) | Slim or Full |

## Things the system will not let you do

These are the rules the site's own stylesheets defend; a build that breaks
one does not look like TrailGoat no matter how many tokens it uses.

- A second solid accent button, or a feature hue on a button, hover or
  selected state. Chrome is the accent plus the neutral ladder — nothing
  else.
- A glow, a coloured shadow, or a blur under a resting card. Depth is a
  hairline and a ground step; `--shadow-pop` is for layers that float.
- A third radius. `--r-ctl` (6px) for what you press, `--r-card` (10px) for
  what it sits on; round only for avatars, swatches, meters and tracks.
- An emoji, an icon font, or an image where a stroked line icon should be.
- Mono caps under 11px (12px on a phone), a tap target under 44px, or an
  infinite animation in the chrome.
- A literal colour where a token exists, or a token invented for one page.
  If a value is genuinely new, it is either one of the nine feature hues or
  it is a departure Kris chose and you noted.
- Two "you are here" marks in one view.

## Kris's standing preferences (from the sessions this skill came out of)

- Tokyo Night is the look he loves; it is the default and the one to show
  first. Forest and First Light exist for people who want them.
- He notices phones. Every deliverable gets the 390px pass, and the tab-bar /
  safe-area logic when it is an installed-app page.
- He wants to be shown, not asked, when the system already knows the answer.
  Propose, with the recommended option first; interview only on product
  forks.
- He merges through PRs and reads changelogs; a repo change without both is
  not done.

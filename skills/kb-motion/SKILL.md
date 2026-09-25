---
name: kb-motion
description: Research, interview, plan and build motion graphics for a product (heroes, loaders, particle fields, scroll stories, data-driven signatures, view transitions, GPU sims), delivered as live HTML examples. Use when the user types /kb-motion with a short description of the motion they want and the product it's for, or asks for motion graphic ideas or examples for a site or app. Interactive — the user must be present for the interview.
argument-hint: "<what kind of motion> for <which product>"
---

# Motion graphics studio

The user types `/kb-motion` and a line like "a loader for our recipe app" or
"hero motion for the landing page of <product>". One run goes:

**understand → research → interview → plan → build live HTML examples → check → publish → save**

You are the motion designer and the engineer. The user is the product brain:
never guess brand, audience or taste decisions they haven't made. The catalog
in `references/catalog.md` is everything already built and proven; start from
it, but research beyond it every run. Best practice moves.

## 0. Read the request

Pull out, from the arguments and the conversation:
- **Product** — name, URL, repo (the working directory if it's a product repo).
- **Motion type** — hero, loader, empty state, scroll story, data viz, logo
  sting, social/launch reel, page transition, background, mascot, "not sure".
- **Placement** — which page or moment, if said.

If the product or motion type is missing entirely, ask one short question
before researching. Otherwise research first and save questions for the interview.

## 1. Research (before the interview)

Do this in parallel where you can (Agent tool for independent sweeps).

**The product** — ground every idea in the product's own world:
- In a repo: find the design system first (tokens/theme files, CLAUDE.md,
  component CSS). Note fonts, palette tokens, light/dark themes, motion tokens
  (durations, easings), existing animation, reduced-motion handling, the asset
  pipeline (versioning, CSP, service worker). Find the product's **own data**
  worth animating (TrailGoat's best motion came from real course profiles,
  routes, terrain and plan numbers, never invented shapes).
- Live site: open it in the browser pane (mute any autoplaying video at once —
  see `references/lessons.md`), screenshot desktop and phone, note what sits
  still that could move and what already moves.
- Mascot, logo, wordmark files in the repo or marketing folders.

**The field** — what good looks like now for this motion type:
- WebSearch/WebFetch for current techniques and examples (Codrops, Three.js
  Journey, GSAP showcase, Awwwards, MDN for new CSS/APIs, Rive/Lottie
  community, Motion.dev). Check browser support dates for anything new
  (WebGPU, scroll-driven animations, view transitions, @property).
- Read `references/catalog.md` and pick the entries that fit; read
  `references/research.md` for sources already vetted.
- Never sign up for anything, and never run code downloaded from a video's
  links; read it.

Write a short research brief for yourself: product facts, data available,
constraints, 6–12 candidate ideas (each: what it is, why it fits this product,
technique, rough effort, support).

## 2. Interview (AskUserQuestion, in rounds)

Interview until you could hand the brief to another designer and get the same
page. Use AskUserQuestion, up to 4 questions a round, options with a
recommended first. Typical rounds:

1. **Goal and feel** — what the motion must do (explain the product, delight,
   show speed, brand recall, reduce perceived wait); the feel (calm/precise,
   playful, cinematic, technical); references they like or hate.
2. **Where and when** — exact placements; before or after a launch date; which
   devices matter most (phone share); is there existing motion to keep
   (a "keeper") or replace.
3. **Material** — which real data, mascot, logo or footage to use; brand
   rules (colors, what's off limits); light and dark themes.
4. **Constraints** — performance budget, libraries allowed (vanilla vs GSAP vs
   Three.js), accessibility (reduced motion is not optional), how many options
   they want to see, fidelity (quick sketches vs production-grade).

Show your candidate ideas in the interview (short names + one line each) and
let them pick, cut or add. Stop when answers stop changing the plan.

## 3. Plan (confirm before building)

Present a compact plan in chat:
- The page: title, sections, order.
- Each example: name (a real name, e.g. "One field, many shapes"), what the
  viewer sees, the product data it uses, technique, where it would live,
  effort estimate, browser support, reduced-motion behaviour.
- What's reused from `assets/` vs new.
Get a clear yes (or edits) before building.

## 4. Build the HTML examples

One self-contained page of live demos (an Artifact when the Artifact tool is
available; otherwise a local `.html` file). Load the `artifact-design` skill
before writing an artifact.

- **Use the product's real tokens** (copy its palette and fonts), in both its
  light and dark themes, and its real data (embed it; artifacts can't fetch
  the product's API). Name things the way the product does.
- **Start from proven code** in `assets/`:
  - `assets/engine/tg-field.js` — the WebGL dot-field engine (DotField:
    two positions/colours/sizes per dot, staggered eased morph, pointer lens,
    click burst; shape samplers for text, images, elevation profiles, GPS
    routes, dust; `cycle()`; `loader()`; the GPU `swarm()`; the motion
    governor `govern()` that pauses off-screen and rests under reduced motion).
    It reads CSS tokens by name through a small map at the top — remap those
    names to the new product's tokens.
  - `assets/engine/home-motion.js` — synced video readout (frame-accurate via
    requestVideoFrameCallback), the Leadville story engine driven two ways
    (chips + autoplay, and page scroll), signal-drop phone, sand signatures,
    ridgeline.
  - `assets/engine/course-topo.js` — contours that rise from open terrain
    tiles (marching squares). `courses-field.js` — header field + cross-document
    view transition.
  - `assets/demos/` — the full proposal lab and toolbox code (GPU sim,
    WebGPU compute, contours, scrollytelling, scroll-driven CSS, same-document
    view transitions, GSAP SplitText/DrawSVG/MorphSVG, state-machine mascot,
    five course signature styles, variable-font type, flow-field topo, summit
    sting in three sizes, arrival board, signal drop). They depend on the
    page helpers at the top of `lab-modules.js`; `assemble.py`/`build.py` show
    how the proposal page was assembled from parts with data inlined.
- **Each example gets**: a heading with its real name, one-line pitch, the
  live demo, and four facts — why it works, how it's built, where it could
  live, effort · support. Add a toolbox/index section when there are many.
- **Every demo must**: pause when off-screen or the tab is hidden, rest on a
  finished frame under `prefers-reduced-motion` (and a page-level "Pause all
  motion" toggle), work at phone width with no horizontal scroll, fall back
  gracefully without WebGL/WebGPU/new CSS, and keep text readable over motion.

## 5. Check (once, properly)

- Load it in the browser pane at desktop and phone widths, dark and light.
  The pane is often hidden: rAF and IntersectionObserver don't run there, so
  verify with calm mode (rest frames), direct render calls, readPixels or
  canvas snapshots (`references/lessons.md` has the tricks).
- Measure overlap between motion elements and copy at 1130/1440/1920/2560 px
  and 375 px; check the console for errors; check the page doesn't overflow.
- Fix what you find, then publish.

## 6. Deliver and save

- Publish (or save) the page; give the link. If it's for a real site and the
  user later picks items, build them into the product following that repo's
  workflow (tests, PR, deploy), not in the artifact.
- If the user keeps a second brain (e.g. an Obsidian vault with an `inbox/`),
  offer to save the research notes and an offline copy there.
- Add anything new that worked (or failed) to `references/catalog.md` and
  `references/lessons.md` in the SkillZ repo so the next run starts further ahead.

## Hard rules

- Real product data over invented shapes; real names over placeholders.
- Never change the product's gold-standard screens unless asked (e.g.
  TrailGoat's Run Planner).
- Reduced motion always honoured; nothing essential only visible mid-animation.
- One draw call per particle field; no layout thrash per frame; budget dots by
  device width.
- Say what you could not verify (e.g. an animation you only saw as still frames).

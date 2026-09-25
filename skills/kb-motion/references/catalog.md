# Motion catalog

Everything built and proven so far, first for TrailGoat (trailgoat.run), Sep 2026.
Each entry: what the viewer sees · technique · where it fits · effort · support ·
status. "Live" means shipped on trailgoat.run; "Demo" means it exists as a working
example in the proposal page only.

Reference pages (private to KB's claude.ai account):
- Motion proposal + toolbox, all demos: https://claude.ai/artifact/VkZGkTs7LrnpEzZwxeJ5g1
- /courses header mockup: https://claude.ai/artifact/SeB2yzVhbpZLB8Lb7xYiMr
- Offline copy + source zip: `~/Documents/SecondBrain/inbox/TrailGoat in Motion (offline site)/`
- Research notes: `~/Documents/SecondBrain/inbox/TrailGoat Motion Research (Sep 2026).md`

## Heroes and page-level

**A living hero** — a race readout (mile, elevation, grade, carbs, next aid,
race clock) on a pre-rendered Blender flythrough, following the headlamp runner
frame by frame. Technique: the render keys the runner at
`route.at(TOTAL × min(1, (frame−1)/OUT_FR))`, so mile = distance × min(1, t × fps / OUT_FR);
read `meta.mediaTime` from `requestVideoFrameCallback`; everything else is a lookup
in the course data (grade-adjusted pace model for clock and carbs). When autoplay
is refused (iOS Low Power Mode) show the poster and its frame's values, hide the
native play glyph, retry on first tap. Fits: any product with a video hero and
data behind it. Effort ~½ day. Status: **Live** (home). Code: `engine/home-motion.js` §1.

**Summit sting** (+ every size) — a 3-second logo reveal: a real course ridge
draws, the wordmark rises off it, the mascot lands on the summit, optional
three-note WebAudio chime; same animation in 16:9, 1:1, 9:16. SVG + CSS
container queries. Fits: launch reels, social, intros. ~1 day. **Demo**.
Code: `demos/round-one-sting-and-signal.js`.

**Contours that rise** (backdrop) — faint topo lines behind a header, traced by
marching squares from AWS Terrain Tiles (Terrarium: m = R×256 + G + B/256 − 32768;
CORS-readable on GET) around a route, rising low→high, route dashed on top,
masked to fade under the title. Pick zoom *after* stretching the area to the
container's aspect (else tile count explodes). ~1 day. **Live** (course pages
without a flythrough). Code: `engine/course-topo.js`.

## Particle fields (WebGL points, one draw call)

**One field, many shapes** — thousands of dots morph between the wordmark, the
mascot (sampled from its pixels, outline ×3 copies), elevation profiles
(46% on the line, rest filling below, grade-coloured), a route from above,
a number. Pointer lens parts them; click bursts. Each dot has from/to
position, colour, size; vertex shader does a staggered cubic ease with a
sideways swirl. Budget 9k/6k/3k by width. Fits: loader, 404, headers, reels.
**Live**: 404 page (goat → 404 → wordmark), /courses header (catalog count →
six featured races, caption links to the race). Code: `engine/tg-field.js`
(`DotField`, `cycle`), `engine/courses-field.js`.

**The plan builds itself** — one story told in dots: every dot is a slice of
trail and travels map → profile → grade colours → time axis (grade-adjusted
pace) → fuel columns (one dot = N grams per leg) → night (real solar altitude
at the race's lat/lon; below −6° = headlamp). Labels per beat, collision-aware
at narrow widths (merge close labels, thin ticks, greedy placement biggest
first, flip labels that would leave the canvas). Driven by chips + autoplay.
Choose an up-and-down course (Leadville), not a net-downhill one. **Live** (home,
"How it works"). Code: `engine/home-motion.js` §2 (`leadStory`).

**The Leadville story, scrolled** — same engine, the page scroll is the
timeline: sticky canvas + six step cards; progress = where the viewport middle
sits between step centres, eased through the middle 40%, smoothed toward the
target each frame. Phone: canvas pins under the topbar, cards scroll over it.
**Live** (home, right after the chip version).

**Dots with momentum** (GPU simulation) — positions and velocities in float
textures, ping-ponged by a fragment shader: spring to target, curl-noise swirl
that decays, damping, pointer repulsion; draw pass colours by speed.
WebGL2 + EXT_color_buffer_float (fallback half float); declare
`precision highp sampler2D`. 65k dots desktop. **Live** as the course-page map
loader (`swarm()` in `engine/tg-field.js`, profile of that course forms out of
the swarm; falls back to the eased loader). Full demo in `demos/toolbox-demos.js` T1.

**A quarter of a million** (WebGPU compute) — 262k particles step along
terrain contours in a WGSL compute shader; trails accumulate in an
`rgba16float` texture faded each frame (8-bit never fades clean); additive
alpha ~0.045 at that count. ~2 days with fallback. **Demo** (T2).

**Living topo** (Canvas 2D flow field) — particles follow the contour tangent
(−gy, gx) of a real height grid, with fading trails and a headlamp; flat ground
respawns. **Demo** (lab P3).

## Data signatures

**Course signatures, five ways** — per-course mini graphics from a 64–120
point profile: line (draws on scroll, hover traces), dot matrix (stadium
board), **sand** (grains fall with a bounce and settle into the profile, in
the card's accent), seal (profile wrapped radially with a textPath ring),
**ridgeline**. **Live**: sand on the home featured course cards. Code:
`engine/home-motion.js` §4, all five in `demos/lab-modules.js` P4.

**Ridgeline** — dozens of profiles stacked Unknown Pleasures-style, flattest
at the back, each filled with the ground colour to hide the ones behind; hover
names a line; lines draw in back to front. Give it its own dark panel (fills
look like a box on a gradient page). **Live** (home course library, 40 courses
spread evenly by ft/mi). Code: `engine/home-motion.js` §5.

**Type that climbs** — a word set along a profile, each letter's variable-font
weight (300–900) from the grade under it. **Demo** (lab P5).

## Interface motion

**A card that becomes the page** — cross-document view transition:
`@view-transition { navigation: auto; }` on both pages; on click name the card
and its title (`view-transition-name`), the destination names its header and
h1 the same; on Back, `pagereveal` names the card again. Names must be unique
per page (don't reuse a class that exists on both). **Live** (/courses → course
page). Same-document version with `document.startViewTransition` in toolbox T6.

**Scroll-driven CSS** — `animation-timeline: view()` + `animation-range`; a
registered `@property --n <integer>` counter printed with `counter()`;
staggered bars. No JS. An ancestor with `overflow: hidden` becomes a scroll
container and freezes `view()`: use `overflow: clip`. **Demo** (T5).

**Signal drop** — a CSS/SVG phone mockup: signal bars drain to "No service"
while the app keeps working (runner dot moving, ETA on screen) and a toast says
nothing was lost. Rests on the no-signal frame. **Live** (home offline section).

**Arrival board** — split-flap style crew ETA board updating as check-ins land.
**Demo** (parked).

**A goat with moods** (state machine) — mascot switches idle/run/climb/descend/
aid/celebrate from inputs (grade, atAid, finished), confetti at the finish —
the Rive idea as a JS stand-in. Real version: rig in Rive. **Demo** (T8).

**GSAP timeline** — SplitText headline, DrawSVG trace, MorphSVG between race
profiles and the mascot outline (rotational mode). GSAP is free incl. plugins
since 3.13 (jsDelivr). Create SplitText after `document.fonts.ready`. **Demo** (T7).

**Contours that rise** (interactive) — hover highlights the nearest contour and
reads elevation; hillshade under the lines. **Demo** (T3).

## Research techniques index (sources in research.md)

Particle morphing · GPU (GPGPU/FBO) particles · WebGPU compute · flow fields ·
open terrain data · marching-squares contours · scrollytelling · scroll-driven
CSS · view transitions · GSAP · ridgeline plots · variable fonts · Rive /
dotLottie state machines. Ideas from Jack Roberts' "Claude Design + Opus 5.5"
video: animated loops over stills, brand extraction (Firecrawl "branding"
scrape) before designing, one animation in every size, logo reveals with a
jingle, style references → motion, scaling one style across many brands,
the RISE brief (References, Idea, Style, Examine).

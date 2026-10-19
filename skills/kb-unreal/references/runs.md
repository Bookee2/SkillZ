# Run log (newest first)

One entry per piece or session: date, piece, versions, Kris's notes → fixes,
outcome, and what the skill learned. Add the entry at close-out (step 9).

## 2026-10-08 · Niagara Examples Pack · analysis (report, note, reel)
- Kris added the pack (listed for 5.7) to a 5.8 First Person project,
  `NiagraExamples`. Analysed it: offline fingerprints of every system
  (renderers, data interfaces, GPU/lightweight), Epic's embedded previews cut
  out of the .uassets as the catalogue, the Gallery's help stands read in the
  editor, and a 14-effect showcase rendered on a dark stage (36 s in ~2 min).
- Learned: fire Niagara from Sequencer life-cycle sections; some systems need
  gameplay params to draw anything; a grey grid floor washes effects out
  (near-black glossy floor, EV100 2); headless Chrome can't go below 500 px
  wide, so phone-width screenshots need the browser pane or a 500 px check.
- Before it: cleaned the internal drive from 51 to 218 GB free (Epic vault
  cache, Genshin, Game Animation Sample moved to KB SS).

## 2026-10-08 · Capra space intro v5 → v5.1 · straight dive + box · Draft
- Kris: "I love this new video." Then: make the zoom "slower and goes straight
  into the platform … currently it zooms in quickly then rotates a bit and then
  zooms into the platform. It's also a little jerky"; and a small box in the
  rings where the platform is, zoom into the box, then the rest.
- Built: one straight line of sight from 50,000 km (22° up, aimed at the statue
  from frame 0), log distance from one integrated speed profile (peak ~2.5
  dec/s, was 3.4), blast moved 4.5 → 6.0 s; the frame modelled offline first so
  Saturn and the rings fit with the platform centred; lime lock-on box drawn
  after the render from a per-frame JSON (`capra_space_box.py`) with a
  synthesised ping.
- Found the jerk with a frame-difference scan: world-space camera keys rounded
  to 16 cm at Z −2.45e8 → the camera now rides an anchor at the set (v5.1).
  Lesson in lessons.md "Large worlds".
- Also: the Niagara Examples Pack is listed for 5.7 only; route recorded in
  samples.md.

## 2026-10-07/08 · Capra space intro v4 · spotlight · Draft
- Kris: "have the statue light up also as the camera comes in so people can see
  the colors … like a spotlight from above"; "just a light in a circle top down
  over the unicorn … the rest would remain dark".
- Found: no local light worked in the Cassini set (VSM overflow from the ring
  rocks fully shadows them) → shadows off; then lights clipped the pale floor
  → lighting channels (statue lights on channel 1) + a faint shadowless spot for
  the floor circle. Delivered v4 at 720p.
- Also this session: analysed Project Titan (report + note), built the samples
  compendium, and created this skill.

## 2026-10-07 · Capra space intro (Saturn) · v4 at 720p · Draft
- Kris: replace the monolith with his Meshy unicorn statue (first a rider
  version, then "a unicorn without a rider"); the explosion "goes out in a
  circular direction, but not a spherical direction"; "the camera zooms to the
  side of the platform which looks weird … better if we watched the explosion
  centered".
- Built: `capra_statue_prep.py` (fit 260 cm, side profile, volume start points
  as a 4th EXR row set → `capra_space_blocks.exr`); statue as a Nanite mesh with
  Meshy textures; spherical dome burst; dive straight down the final line of
  sight; centred camera all the way (no post-blast swing); statue key light.
- Check stills caught two problems before the full render: the statue rendered
  as a black backlit silhouette (→ key light), and the burst engulfed the camera
  (→ capped radius, flattened camera-side half).

## 2026-10-07 · Capra space intro (Saturn) · v1 → v3 at 720p · Draft
- v1 (14 s): monolith shatters into blocks → lockup → dissolve → hold.
  Notes: camera "bumps up" after the push-in; the monolith "doesn't look like
  it's actually exploding"; the explosion sound is weak; can't tell the blocks
  turn solid; logo glow "too bright to tell what it is"; "you can't really tell
  that you're looking at Saturn"; make it 12–15 s.
  Fixes: PCHIP camera, held height; Burst/Flash explosion with recoil and
  shake; sub boom + suck-in + ducking; left-to-right wipe with a white seam;
  glow 2.3 → 0.75; powers-of-ten dive from 30,000 km; 15 s.
- v2: "awesome". Notes: the platform "appears out of nowhere" at the end of
  the zoom; the explosion is white then turns into colours.
  Fixes: platform and set always loaded (`is_spatially_loaded=False`); the
  last decade of the dive gets ~1.5 s with a swoop to eye level; blocks burst
  in their own colours; the flash light is a few candela (Cassini's sun is
  ~5 lux) and CONSTANT-keyed before the blast frame.
- Learned: local-space ISM instances in large worlds; `modify()` before
  scripted visibility; BeamMeUp switcher re-applies on load; Cassini rings only
  render in a game world; light intensities must be judged against the
  scene's sun; MRQ sub-frame samples ramp keys inside the frame before a
  LINEAR key.

## 2026-10-07 · Capra end screen · 720p → 4K · Delivered
- Kris replaced the reversed-intro outro: "instead of the sphere spinning which
  loses the branding … the solid models get lit up and then we add the
  standard YouTube outro text … stays lit for 20 seconds … slow the lighting".
  Then: "keep more glow on and frame it bigger, then 4k".

## 2026-10-06 → 07 · Capra channel intro (block ident) · Signed off at 4K
- Lights off (chalk wall) v1–v3 rejected ("this sucks", "first day in film
  school") → rebuilt as a block swarm on the Intro_motion stage ("100x
  better"). Notes along the way: letters ended tilted → end dead centre at eye
  level; flat/loose blocks → solid lattice fill; Kris supplied three Meshy
  models; "Capra Studios bigger, with Kris smaller like a spray-painted
  afterthought, not stacked"; 10 s with a fade from 8 s; dissolve back to the
  solid models; "can we not find a real sound library" → Mixkit; picked R3.
- Learned: stage not wall; close Sequencer before saving; out-of-process
  renders with a spare frame; kill CrashReportClient; editor closed during
  renders; no remote Python during renders; resume queues.

## 2026-09-29 → 10-03 · TrailGoat Canyon Run (Electric Dreams) · Delivered 4K
- 16 versions in a day of notes: hoof skate, finish arch too short, rocks in
  the trail, goat clipping rocks → speed-matched stride, raised arch, dynamic
  programming path clearing; green first frames → pre-roll; black sphere →
  stray preview mesh; music cut to bars.

## 2026-09 · TrailGoat ParticleLab openers, WSER Cesium films, goat blocks
- Openers v1–v9 (particles form the goat and the wordmark; smoke only as a
  transition; captions; navbar-exact colours). WSER films delivered but Kris
  prefers the Blender flyovers. Goat blocks delivered at 4K with the
  Breakbeat.

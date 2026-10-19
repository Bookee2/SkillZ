# Techniques: how the proven pieces work

Each technique: the idea, the numbers that worked, and where the working code
is. Copy and adapt the code; don't rewrite from memory.

## Block swarm (the signature technique)

Thousands of rounded cubes fly from a start shape into a target shape.
Motion Design cloners can't do this (they sample the reference pose once and
can't follow animation), so it's one instanced mesh moved entirely by a
material.

**Data (Blender, headless, `Blender -b -P prep.py -- args`)**
- Sample the target into block positions. For solid-looking 3D, fill the
  **volume**: a lattice at the block spacing, inside-test by ray parity (count
  hits along +Y). Surface-only sampling with jitter looked flat and loose.
  Spacing 2.6–3.2 cm for letters, ~1.6–2.2 cm for thin shapes; size blocks to
  touch (scale = spacing × 1.04 / 100 for a 100-unit cube).
- Colour per block from the model's texture luminance mapped between a dark
  and a light brand colour per element (`lum_lo`/`lum_hi` from percentiles).
- Reading order per block (0..1, e.g. left→right, top→bottom) drives the
  stagger. Glow gain per element (thin elements need more).
- Axis swap Blender → Unreal: Blender (x width, y depth, z height) → Unreal
  (X depth, Y width, Z height). glTF imports in quaternion mode: set
  `rotation_mode='XYZ'` before rotating; `parent_clear(KEEP_TRANSFORM)` and
  `transform_apply` first.
- Write a float EXR (`float_buffer=True`, OPEN_EXR 32-bit). Layout: width N
  (wrap at 8192, row sets of R rows): rows 0..R-1 target xyz + order; R..2R-1
  colour rgb + block scale; 2R..3R-1 glow gain. Animated sources add one row
  set per frame. Also export the solid meshes (FBX, rotate −90° about Z, scale
  0.01) and textures for the dissolve.
- Code: `Caprastudios/unreal/capra_blocks_prep.py` (Meshy GLBs → 13,752
  blocks); `Intro_motion/Scripts/blender_prep_blocks.py` (animated goat bake →
  6000×103); `TrailGoatElectricDream/Scripts/blender_bake_cheer.py` (pose in
  Unreal world space by 16-bone similarity fit).

**Unreal**
- Import the EXR with the asset deleted first; then `power_of_two_mode` NONE,
  `TC_HDR_F32`, sRGB off, nearest filter, no mips, never stream; assert the
  size (re-imports keep power-of-two padding).
- One actor, one `InstancedStaticMeshComponent`, N instances at the actor's
  own origin **in local space** (`add_instances(..., False, False)`),
  `num_custom_data_floats=1`, custom data 0 = index set in one call
  (`set_editor_property('per_instance_sm_custom_data', flat_list)` — a Python
  loop hung 10+ min), `bounds_scale` 30. Mesh: `/Avalanche/Toolkit/Geometry/
  SM_MD_Rounded_Cube` (needs the Motion Design plugin) or the engine cube.
- Material (`used_with_instanced_static_meshes`, `max_world_position_offset_
  displacement` 100000): a TextureObjectParameter (sampler type
  LINEAR_COLOR), PerInstanceCustomData[0], PreSkinnedPosition, MPC params;
  three Custom nodes:
  - WPO: hash per index (two float3 hashes) → start point (a cloud, a sphere
    or packed inside a monolith) → `m = saturate(Morph*1.7 - order*0.7)`,
    `em = smoothstep(m)` → `Q = lerp(start, target, em)` plus an arc
    `sin(pi*em)` toward the camera and up, a swirl about the lockup centre,
    per-block spin about a hashed axis, size `scale*(0.85+0.3*hash)` gated in
    → return `Q + rotated(LP*size) - LP`. In far-from-origin worlds run the
    maths in actor-local cm and pass the result through a Transform node
    (Local → World vector) before WPO.
  - Colour (through a VertexInterpolator): target colour (v3: blocks burst in
    their own colour; don't start black or white).
  - Emissive: `colour * Glow * k * gain * saturate(em*2-0.5) * (0.35 +
    0.65*facing)` with k ≈ 0.75 (2.3 washed colours to white; v1 note).
- MPC: Morph, Glow, Solid (+ Burst, Flash). Create missing params only —
  never recreate existing ones (new ids orphan materials). Key MPC values in
  the sequence; asset defaults don't reach `-game` renders.
- Code: `capra_blocks_build.py` (stage), `capra_space_build.py` (space,
  local-space, burst, wipe), `Intro_motion/Scripts/build_swarm.py` (animated
  goat with run/flip rows; hand-wrap `fmod`, GPU `fmod(20,20)` ≈ 1).

## Dissolve blocks → solid models
- **Cell hash** (stage ident): `cell = floor(pos/3)`, `dn = frac(sin(dot(cell,
  (12.9898,78.233,37.719)))*43758.5453)`; the swarm shrinks blocks where
  `Solid*1.25 > dn` and the masked solid material reveals the same cells.
- **Wipe with a hot seam** (space v2+, reads much better on camera):
  `w = saturate((pos.y + 215)/430)*0.85 + dn*0.15`, `edge = Solid*1.2 - w`;
  blocks swell near the seam then vanish (`1 - saturate(edge*30)`), the solid
  appears behind it (`saturate(edge*30)`), and a white seam glows on the
  leading edge. Solid material reads local position via TransformPosition
  (World → Local).

## Particle engine (150k, deterministic)
One ISM of 150k camera-facing quads; a Custom HLSL WPO computes each
particle's position at `T` (and `T − 1/60` for streaks) from per-instance data
(20–26 floats: start, targets, stagger, seeds); a pixel node does colour and
falloff. MPC `T` and `CamV` keyed **every frame** (two keys gave an S-curve
that broke music sync). Staged lerps with stagger and arcs; murmuration is
analytic (Lissajous). Additive, unlit; per-shape gains with <5% clipped pixels
(measure with numpy); fade near the camera; lens flares off; bloom 0.75,
grain 0.22, vignette 0.55. Code: TrailGoat `studio/particle-engine/`
(`Scripts/build_smoke.py`, `prep_*.py`, `blender_bake_points.py`,
`notes/LESSONS.md`).

## Motion Design stage and brand plastic
- The `3D_MotionDesign` template map: `Cyc_02` cyclorama, chrome ring and
  pedestal (AvaShape ellipses), RectLights Left_Key 12 cd, Right_Fill 8 cd,
  Top_Light 80 cd, SkyLight with `EpicQuadPanorama_CC+EV1`, 35/55/75 mm cine
  cameras, a Grid Cloner of rounded cubes with Sphere effectors.
- Brand plastic: MIC of `/Avalanche/Toolkit/Materials/M_Opaque`,
  `BaseColor_Map` = `/Engine/EngineResources/WhiteSquareTexture`, roughness and
  normal maps copied from `M_Plastic_A010`, `Base_ColorTint` = linear brand
  colour, `Roughness Max` 0.55.
- Cloners from Python: CEClonerActor with Mesh layout (VERTICES/TRIANGLES,
  counts ~1800/7000), CEEffectorComponent Unbound/Procedural linked through
  CEClonerEffectorExtension; key effector Magnitude. Refresh in a separate
  call: `set_tree_behavior_name('Flat')` → `('Group')`, `set_enabled(False/
  True)`, verify `get_mesh_count()`. Spawned actors are STATIC until set
  MOVABLE (attach fails silently). Code: `Intro_motion/Scripts/s_*.py`.

## Hero spotlight (space v4)
Kris's ask: "a light in a circle top down over the unicorn; the rest would
remain dark". A shadowless SpotLight straight down (inner 14°, outer 20°, 6.8 m
up → a ~4.8 m soft disc) at ~7 cd lights the floor circle; a shadowless rect
light (45 cd) and a front key (8 cd) on **lighting channel 1** light only the
statue (statue mesh on channels 0+1). Struck at 3.3 s as the platform comes into
view (on → dip → full, with a switch clunk and click in the mix), cut CONSTANT
on the blast frame.

## Lights-off / black-light beat
CONSTANT keys drop key, fill, top and SkyLight to 0 on the click frame; a
violet RectLight tube (460×14 cm, #7a2df5) strikes 70 → 8 → 45 cd over 0.75 s;
Glow flickers 0.55 → 0.12 → 1.0 to match; a pull-chain drops 14 cm and springs
back. Lumen's cached bounce takes ~2 s to fade — on the stage the glow and the
reflective floor hide it; on a wall, split the render at the black frame
(Lumen before; `r.DynamicGlobalIlluminationMethod=0`, `r.ReflectionMethod=0`
after). Code: `capra_blocks_seq.py`, `lights_off_render.py`.

## Explosion (space v2–v4)
- v4 shape: a dome, not a disc. Per block: `rnd` = uniform direction on the
  sphere from two hashes (`z = 2h-1`, `phi = 2πh`), `dir = normalize(rnd*0.8 +
  outward*0.4)`, `dir.z = max(dir.z, -0.12)`, the camera-facing half (local −X)
  scaled ×0.45, distance `120 + 330*h^1.5` cm (keep it under the camera
  distance). Blocks start inside the object's own volume (a fourth EXR row set
  sampled in Blender, paired left-to-right with their targets) so the hero
  object itself blows apart.
- `Burst` MPC 0 → 0.12 on the blast frame → 0.6 at +0.15 s → 1 at +0.7 s (fast
  out, easing). Each block's start = its packed position + direction from the
  core × `(120 + 480*hash²)*Burst + 40*Morph` (most within 2 m, a few to 6 m;
  the cloud keeps drifting), clamped above the floor; extra spin while
  `Burst*(1-em)`.
- The original object hides on the blast frame (visibility track: True =
  visible).
- `Flash` MPC spikes 1 → 0.45 → 0 over 1 s; blocks glow in **their own
  colour** (`colour*Flash*1.3`), not white (4.0 clipped to white).
- A point light in the core keyed 500 → 220 → 40 → 0 cd over 0.7 s (2500
  blew the floor out), ribbon-blue tint.
- Camera recoil (radius 560 → 700 cm over 0.9 s) plus a decaying shake:
  `3 cm·e^(−5.5t)·sin(2π·7t)` sideways, `2.2 cm·…·sin(2π·9t)` up,
  `0.35°·…·sin(2π·8t)` pitch, keyed every frame for 0.8 s.
- Sound: see "Sound design".

## Camera
- Kris prefers watching the hero moment **centred and head-on**: land the dive
  square on the subject along the final line of sight (start direction = the
  final horizontal heading raised ~21°), recoil straight back from a blast, and
  build the lockup in the same view instead of swinging round after it.
- Keypoint tables `(t, theta, radius, height, look-at z [, centre x])` in the
  subject's local frame → world, `find_look_at_rotation`, keyed every 2 frames
  (every frame in dives and shakes). Interpolate each channel with a
  **monotone cubic (Fritsch–Carlson PCHIP)**, not per-segment smoothstep (the
  camera stops and restarts at every key: Kris saw it as a "bump"), and not
  Catmull-Rom (overshoot flung the camera). Code: `capra_space_seq.py`
  (`pchip`, `cam_at`, `shake`); `assets/camera_paths.py` in this skill.
- End frames: dead centre, eye level (camera height = look-at height), slow
  creep-in through the hold.
- **Powers-of-ten dive = one straight line** (`straight_dive` in
  `assets/camera_paths.py`): aim at the subject from the first frame and fall
  straight down that line of sight (from 22° above the ring plane), so the
  camera never turns. v4's swoop to eye level plus an aim hand-off from the
  planet's centre read to Kris as "zooms in quickly then rotates a bit then
  zooms into the platform" and jerked near the set. Drive log10 distance with
  one integrated speed profile (no knots), peak ≤ ~2.5 decades/s, ≥ 1.5 s on
  the last decade, arriving at rest; end the dive above the subject and let
  the blast recoil bring the camera down to eye level. With the subject
  centred, the planet sits off-centre in the wide shot: model the frame
  offline (project the rings and disc) and start far enough out (10^9.7 cm
  for Cassini's Saturn) that the whole system fits. Keep the set **always
  loaded** (`is_spatially_loaded=False`) or World Partition pops it in.
- **Target marker**: a small lime lock-on box over the subject in the wide
  shot (Kris's idea), drawn after the render from a per-frame JSON of the
  subject's projected bounds that the sequence script writes from the same
  camera (`capra_space_dive.json`, `capra_space_box.py`); it stays small,
  then grows with the subject and fades as the subject fills the frame. A
  post overlay can be restyled without re-rendering.
- Focus: manual focus distance keyed to the camera–subject distance (clamped
  for dives); filmback 36×20.25; 30 mm for lockups; motion blur 0.25 when
  close rocks streak.

## Characters (Meshy)
- Kris makes models in Meshy.ai (rigged biped GLBs with clips). Import every
  clip with `AssetImportTask`; mark each move's skeleton
  `compatible_skeletons` with the main one so all clips play on one goat.
- Play rate via `MovieSceneTimeWarpVariant` (`set_fixed_play_rate`); set the
  section range after the parameters. Run_03 measures 2.53 m/s at 1×.
  Re-importing a skeletal mesh keeps the old AnimSequence: delete it first.
- Motion matching: retarget to UEFN/Manny (`IK_*`, `RTG_*`) and build a
  PoseSearch database (Amandine: 109 entries). Blender FBX for rigs: Add Leaf
  Bones off, Only Deform Bones on, Apply Unit on.
- Point bakes: sample on the rest mesh so every clip shares the same points
  (crossfades); `blender_bake_points.py`, `blender_goat_perf.py`.

## Paths through worlds
`make_trail.py`: hand waypoints → ground line traces → spline resampled every
50 cm → median-then-mean height smoothing. `clear_path.py`: for each sample try
lateral offsets ±250 cm, score sphere overlaps at knee/hip/chest (38/70/120 cm)
ignoring foliage by name regex, pick the smoothest clear line by dynamic
programming, re-trace the ground (rock hits 17 → 0). Cut shots to music with
two constants (`DROP, BAR = 3.35, 2.41`).

## Real terrain
- **Blender flyovers** (`TrailGoat/scripts/flythrough/`): Terrarium DEM +
  NAIP imagery, shot JSON specs, camera lints (flow ≤ 8°/s, yaw ≤ 7°/s, tilt
  ≤ 4°/s, clearance ≥ 150 m, horizon 8–45% from top), light-state table.
  `--export-cam` writes per-frame cameras in metres for Unreal.
- **Cesium Google 3D Tiles** (WSER): CesiumGeoreference (set the origin and
  read it back — default is Denver) + Cesium3DTileset; async streaming,
  900 warm-up frames, `t.MaxFPS 8`, 240 handle frames per cut, SSE 12,
  120 simultaneous loads; portrait renders need a portrait window (culls
  against the window's aspect); assemble with `assemble_google.py --shots`;
  never two renders on one cache (sqlite "database is locked").

## Runtime GPU PCG worlds (Cassini)
The rings and asteroids are "generate at runtime" GPU graphs: they appear only
in Simulate or a game world, so render with `-game` and ~90 engine warm-up
frames; they compile for Metal. From 30,000 km the ring LOD still reads.
Facing a sunlit planet head-on gives a flat cream wall; frame the limb.

## Niagara effects in renders (Niagara Examples Pack)
- Put the system on a NiagaraActor with Auto Activate off, bind its component
  in the sequence (`seq.add_possessable(actor.niagara_component)`), add a
  `MovieSceneNiagaraSystemTrack` section over the shot: bursts fire on the
  section start (evaluate behaviour NONE), loops re-activate while it plays
  (ACTIVATE_IF_INACTIVE; start the section 1–3 s before the cut as pre-roll).
  Repeatable in MRQ. Builder: `assets/niagara_showcase.py` (dark stage, one
  cut per effect, life-cycle sections, MRQ queues).
- Ribbon trails need motion: key the NiagaraActor's transform along a path.
- Mesh → particles in its own colours: skeletal-mesh triangle sampling plus a
  texture lookup (NS_Dino_Tris_Color_Burst); pass the mesh as a user param.
- Exposure: fixed EV100 2 under an 8-lux sun matched Epic's gallery on a
  near-black glossy floor (M_NX_DarkFloor); effects own the frame.
- Catalogue without rendering: Epic stores a preview JPEG/PNG inside each
  .uasset — `assets/extract_uasset_thumbs.py` cuts them out (65 of 67).

## Reveal materials (World Wakes)
`mask = clamp((Time*270 − (WP.x + 365))/95)` lerps dark → bright and drives
emissive; foliage bands grow by keying Scale.Z 0 → 1 staggered. Good for "a
world waking up". Code: `Caprastudios/unreal/world_wakes_*.py`.

## Overlays and end screens
Pillow RGBA overlays composited by ffmpeg (`overlay`, `format=yuv420p`):
URL cards anchored to a 3D point projected through a Python copy of the camera
keypoints (`post_url.py`), captions (`captions_*.py`), end-screen bays and
stepped letters with a layout-guide PNG (`capra_outro_post.py`). HTML clips as
ProRes 4444 overlays (`-itsoffset`, `overlay=eof_action=pass`).

## Sound design
- `Caprastudios/unreal/capra_sfx_library.py`: `Mix(dur)`, `.cue(id, at,
  gain_db, align='hit'|'start'|'end', trim, fade_in, fade_out, pan, lp, rev)`
  places Mixkit recordings by their measured loudest 10 ms (the hit lands on
  the picture beat), `.add()` for synthesised arrays, `.master(fade_from,
  drive)` with optional tanh soft clip. Library: `Caprastudios/output/unreal/
  sfx/library/` (Mixkit, licence file beside it).
- Blast recipe: reverse swell ending on the hit (784), a beat of ducking
  (bed −13 dB from −0.15 s, recovering over 1.8 s), layered hits (774 +
  2902 or 3057 + 1143) and a synthesised sub boom (80 → 28 Hz with a noise
  crack), debris whooshes (3003, 169).
- Never reverse a click; reverse only power-ups. Cut risers just before the
  hit. Kris's own music goes on with `mux_music.sh` (loudnorm −14 LUFS).

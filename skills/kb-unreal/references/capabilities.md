# Capabilities: everything built and proven so far

Each entry: **what the viewer sees** · technique · project / map · scripts ·
render cost · **status**. Status words: **Signed off** (Kris approved the
final), **Delivered** (final made and used), **Draft** (720p, awaiting notes),
**Proven in test** (works, not used in a piece), **Rejected** (keep the
lesson, don't pitch again), **Untested on Mac**.

Paths: KB SS = `/Volumes/KB SS`; projects live in `KB SS/Unreal Projects/`
(symlinked from `~/Documents/Unreal Projects/`). Engine UE 5.8.3 at
`KB SS/Unreal Engine/UE_5.8`. Blender 5.2 at `/Applications/Blender.app`.

## A. Productions

### Capra Studios channel intro — the block ident · **Signed off (4K)**
A chrome-ringed Motion Design stage; the camera pushes in on a spinning sphere
of coloured cubes; it bursts; 13,752 blocks fly on arcs into Kris's three
Meshy models (unicorn bust, one-line "capra studios", sprayed "with Kris");
a pull-chain clicks, the studio lights cut, a UV tube strikes, the blocks
fluoresce; the camera arcs to dead centre and the blocks dissolve back into
the solid models; fade 8–10 s. 10 s at 30 fps.
- Technique: block swarm (ISM + float EXR + Custom HLSL WPO + MPC Morph/Glow/
  Solid), solid lattice fill in Blender, 3 cm cell-hash dissolve shared by the
  swarm and the masked solid material, CONSTANT light keys for the cut, orbit
  keypoint camera.
- Project: Intro_motion, `/Game/Capra/Maps/Capra_Stage` (a duplicate of the
  TrailGoat stage, from the Motion Design template).
- Scripts: `Caprastudios/unreal/capra_blocks_prep.py` (Blender) →
  `capra_blocks_build.py` → `capra_blocks_seq.py` → `capra_render.sh <Q>` →
  `capra_sfx_library.py` (mix R3).
- Cost: 720p ~42 min (301 frames); 4K 8 samples ~2 h 20 min.
- Output: `Caprastudios/output/unreal/capra-blocks-intro-4k-R3-neon-power.mp4`.

### Capra end screen · **Delivered (4K)**
Reverse of the intro's ending without the swarm: the solid models start dark,
the chain clicks, the studio lights ease up over 3 s while the models glow;
the camera pulls back and holds 20 s; Pillow overlay adds WATCH THIS NEXT and
LIKE & SUBSCRIBE labels and card bays (layout guide PNG for YouTube Studio).
- Scripts: `capra_outro_seq.py`, `capra_outro_post.py`, mix `endscreen()`.
- Cost: 720p ~48 min (600 frames); 4K ~4 h 35 min.

### Capra space intro (Saturn) · **Draft v4 (720p)**
Opens on all of Saturn and its rings from 30,000 km; a powers-of-ten dive
through the ring rocks onto a floating platform; a black monolith silhouetted
against the planet blasts apart (flash, recoil, shake); the cloud hangs and
streams into the lockup in reading order; a left-to-right wipe with a white
seam turns blocks into the solid models; hold among tumbling lit rocks; fade
13–15 s. 15 s at 30 fps.
- Technique: the block swarm in lockup-local space (large-world precision),
  Burst/Flash MPC params, log-space dive with PCHIP and an aim hand-off,
  decaying shake, Cassini's runtime GPU PCG rings (game-world render only).
- Project: CapraSpace (APFS clone of Cassini), `/Game/Levels/Demo`; lockup at
  (−435, −18610, −245440259) yaw −40.
- Scripts: `capra_space_build.py`, `capra_space_seq.py`,
  `capra_space_render.sh Q_CapraSpace_check|Q_CapraSpace_720`, mixes `s1`
  (all space sounds) / `s2` (stage-intro impact in a space bed).
- Cost: check stills (every 15th frame) ~5 min; 720p ~35 min (450 frames,
  ~4.7 s/frame).
- History: v1 (camera bump, no real explosion, weak boom, invisible dissolve,
  glow too bright, didn't read as Saturn) → v2 (dive, blast, wipe; "awesome")
  → v3 (platform no longer pops in; blast in colour) → v4 (Kris's Meshy unicorn
  statue replaces the monolith and explodes in a spherical dome; camera centred
  throughout). Prep: `capra_statue_prep.py`.

### TrailGoat blocks — goat to wordmark · **Delivered (4K)**
6,000 cubes form the Meshy goat, which runs, backflips, then morphs into
TRAILGOAT on the TG stage. 20 s and a 7.6 s intro cut, with Kris's Breakbeat.
- Project: Intro_motion `/Game/TrailGoat/Maps/TG_Stage`; `Scripts/`
  (`blender_prep_blocks.py`, `build_swarm.py`, `build_seq3.py`,
  `build_intro.py`, `make_queue.py`, `render_final_guarded.sh`, `post_url.py`,
  `mux_music.sh`). MPC_TG_Blocks (T, Build, Morph, GoatYaw, FlipT, FlipMix,
  Skip); `blocks.exr` 6000×103 (20 run frames + 81 flip frames + wordmark +
  colour rows).
- Cost: 720p ~3 s/frame; 1080p ~9 s/frame; 4K 17–27 s/frame.
- Output: `KB SS/TrailGoat-Studio/Renders/blocks/`.

### TrailGoat Canyon Run ("the goat running through the woods") · **Delivered (4K)**
The Meshy goat runs a cleared singletrack through Electric Dreams' canyon and
creek: establishing push, low side tracking, 0.6× slow-motion jump, chase,
creek wide under a Blender-built finish arch, front cheer, idle; the goat
becomes 6,000 blocks that form TRAILGOAT; a URL card; HTML feature popups
overlaid. 29.8 s cut to the music's bars.
- Project: TrailGoatElectricDream (open `ElectricDreamsSample.uproject`, the
  one with Python/Remote Control/MCP), map `/Game/Levels/ElectricDreams_Env`.
- Scripts (`Scripts/`): `import_goat.py`, `import_moves.py` (compatible
  skeletons), `make_trail.py` (50 cm ground-traced line), `clear_path.py`
  (dynamic-programming obstacle avoidance), `build_canyon.py`,
  `blender_bake_cheer.py` (16-bone similarity fit), `build_swarm_ed.py`,
  `blender_finish_line.py`, `make_queue.py`, `render.sh` (the .app binary,
  not -Cmd), `final_canyon.sh`, `final_4k_canyon.sh`, `post_url_canyon.py`.
- Cost: 720p ~1 s/frame; 1080p 3–15 s/frame; 4K run ~4 h.
- Output: `TrailGoat-Studio/Renders/trail/TrailGoat-CanyonRun-4k-popups-A.mp4`.
- Next asked for: a 30 s forest commercial (run → blocks form the course
  profile → fuel/hydration → wordmark). Not started.

### TrailGoat particle openers (ParticleLab) · **Delivered (1080p)**
Deterministic 150k-particle films: a space prototype (19.2 s, 125 BPM), the
smoke/particle opener v1–v9 (25.4 s; particles form the goat, flip, morph to
the 3D wordmark in exact navbar colours, captions), Sky Trail islands and Sky
to Summit 25K (one Meshy island with the route painted on).
- Technique: one ISM of 150k quads, Custom HLSL WPO evaluates each particle at
  T and T−1/60 (streaks), per-instance custom data 20–26 floats, MPC T and CamV
  keyed every frame; Blender point bakes of Meshy animation; six-way smoke
  sprites; PIL caption overlays projected through the camera spline;
  synthesised house cues.
- Project: `KB SS/TrailGoat-Studio/ParticleLab` (Metal SM6, HW ray tracing).
  Source of truth: TrailGoat repo `studio/particle-engine/` (`sync.sh`),
  `notes/LESSONS.md`, `notes/RUNBOOK-space.md`, `notes/UVFX_TECHNIQUES.md`.
- Cost: 576-frame 960×540 preview ~3 min; 1080p 8-sample final ~5–8 min.

### TrailGoat Films ident ("Headlamp") · **Signed off (v2, 720p); 1080p final**
A headlamp clicks on in the dark over a glossy trail floor; dust hangs in its
beam; the dust pours back into the lamp and the particle goat condenses around
it (it was his headlamp); he runs at the camera and leaps; at the apex he
bursts in brand colour and the burst streams into TRAILGOAT (navbar colours) /
gradient rule / FILMS (tracked caps), which turn solid and reflect in the
floor; the lamp settles behind the rule; the letters drain and it clicks off.
5.0 s at 24 fps; opens every TrailGoat YouTube flyover (`/tg-films` intro slot).
- Technique: the 150k engine with run + leap bakes and a forehead track, a
  mirrored second ISM for floor reflections, a shader cone plus a real
  SpotLight in volumetric fog for the beam, per-frame lamp/glow tables.
- Project: ParticleLab `/Game/Films/Main`; repo `studio/particle-engine/`
  (`prep_films.py`, `build_films.py`, `blender_head_track.py`,
  `blender_exr_npy.py`, `export_sounds.py`, `post/sound_films.py`,
  `post/encode_films.py`, `render_films.sh`; `blender_text3d.py --text`).
- Sound: "Night trail" from Epic sample recordings (crickets, footfalls, wind,
  boulder hit) + a real switch click; the drone cut is the signed-off one.
- Cost: check 9 min, 720p 11.6 min.
- Output: `KB SS/TrailGoat-Studio/Renders/films-ident/`; installed as
  `Films/assets/intro-trailgoat-films-1080p24.mp4`.

### TrailGoat Western States flyover, commercial, sting, outro · **Delivered (1080p); not used on the site**
Blender camera → Unreal on Cesium Google Photorealistic 3D Tiles (and a DEM
fallback): 44 s commercial (16:9 and 9:16), 6 s channel sting with an alpha
tail, 20 s end-screen outro (the hillside TRAILGOAT sign at night), 100 s
landing-page hero; keyed sun/moon day-to-night, altitude-adaptive clouds and
haze, a glowing route ribbon revealed by MPC Progress, aid pins and labels.
- Project: `KB SS/TrailGoat-Studio/WSER/WSER.uproject` (Cesium plugin);
  `Scripts/build_scene.py` (1,090 lines, stages), `chase_cam.py`, `map_cam.py`,
  `blender_export.py`; top-level `render_night.sh` (watchdog, black-frame
  check), `assemble_google.py --shots` (handle-frame flicker fix),
  `encode_channel.sh` (ProRes 4444 alpha), `hero_4k_once.sh`.
- Status note: Kris prefers the Blender flyovers; "renders stay Blender until
  Unreal matches it". The 4K hero never completed.

### TrailGoat Leadville dawn test · **Proven in test**
30k ISM cubes rest on the trail, lift off and form the course elevation
profile above Hope Pass at dawn (Cesium tiles). 7 s 1080p30.
- `WSER/Scripts/build_leadville.py`, `TrailGoat-Studio/leadville-test/prep_leadville.py`.

### Blender course flyovers (tg-render) · **Delivered, live on trailgoat.run**
Real terrain (AWS Terrarium DEM + USGS NAIP imagery), headlamp runner with a
lit wake, aid pins, labels, race billboard, PREDAWN→NIGHT lighting arc.
Leadville 160 s, Cocodona 219 s, Cloudland, Wild Florida, Perpetua.
- `TrailGoat/scripts/flythrough/` (`render.py`, `geo.py`, `author_film.py`,
  `encode.py`, `deliver.py`); the `/tg-render` skill runs batches.
- Cost: 0.6–0.9 s/frame at 720p on the M5 Pro.
- This is the bar Unreal flyovers must beat.

### HTML/Chromium video graphics (kb-ytvideo, HyperFrames) · **Delivered**
Chapter cards, lower thirds, feature popups (ProRes 4444 overlays on Unreal
renders), a 12 s HTML particle opener, product-demo captures. Every frame is a
pure function of time; Playwright renders with sub-frame blending.
- `TrailGoat/.claude/skills/kb-ytvideo/` (`engine/render.js`); HyperFrames
  trial in `Caprastudios/output/hyperframes-trial/` (4K60 600 frames in 17 s).
- Use for 2D type and UI motion; Unreal for 3D worlds.

### Capra studies (Capra_intro, Sept 29) · **Studies / Rejected**
- **Lights off (chalk wall)** — Rejected. `lights_off_*.py`. Lesson: wall
  concepts fail; Lumen bounce lags ~2 s after a light cut (split render).
- **World Wakes** — a world-position + time reveal material and staggered
  growth bands (90 frames). Proven in test; good for "a world waking up".
- **Ribbon light study**, **Electric Dreams creek** (the creek dressing was
  "incoherent"; its project CapraElectricDreamStudy is gone).

### Blender web motion for caprastudios.co · **Live**
Ribbon-unicorn film (Geometry Nodes ribbons, 480 frames 60 fps), turntable
WebP sprite, 150-shard rigid-body break played in reverse.
`Caprastudios/blender/` (`unicorn.py`, `render.py`, `encode.py`,
`bake_turntable.py`, `bake_shards.py`).

### Games (not motion pieces, but proven pipelines)
- **HostileTakeover** (tower defense, `KB SS/HostileTakeover`): fully scripted
  Blender bpy asset pipeline (palette material per faction, budgets,
  standard animation takes, 2×2 previews, FBX round-trip check), an isolated
  Unreal import validator, a C++ UE 5.8 game with headless self-play.
- **Amandine OW** (City Sample, `KB SS/Unreal Engine/Amandine_OW`): vampire
  sandbox prototype; Meshy character retargeted to Game Animation Sample
  motion matching; Blueprint graphs authored as DSL by agent; Mac
  performance tuning (minimised editor, 75% screen percentage, hair cards).

### Capra land flyover — Petit Ridge (spec for realtors) · **v2 final delivered in 4K (2026-10-29)**
Low over Lake Petit, up the valley to a real 4.9-acre lot in Big Canoe GA; the lot line draws itself in ribbon
blue; "Read the Land" turns the forest into glowing contours and paints the visible part of the lake; a concept
stone cabin resolves behind a glowing seam (World Wakes) on its cut-and-fill pad; the turn to the lake view,
leaves fall; blue-hour hold on the lit cabin; Capra lockup. 80 s at 24 fps.
- Technique: USGS lidar → Nanite glTF terrain tiles, OSM roads, data-placed Megascans forest with fall tints,
  canopy-aware viewshed, PCHIP camera traced offline, MPC + per-component material tracks (tick-resolution
  keys), two-render reveal composite, Pillow cards (unbranded/agent cuts need no re-render). v2: forest from
  the real lidar trees (+ infill, + a far ring planted from the NAIP photo), NAIP 60 cm ground colour at distance,
  76k Megascans ground-cover pieces where the camera gets close (techniques.md "Real ground and real trees").
- Project: `KB SS/Capra Studios/Unreal/PetitRidge` (Megascans + MSPresets APFS-cloned from Electric Dreams);
  map `/Game/PetitRidge/Maps/PetitRidge`; scripts `Caprastudios/unreal/petit_ridge/` (terrain_tiles,
  site_meshes, forest_points, viewshed, film_path, pr_build/scene/forest/seq/film, pr_render.sh,
  post_film, mix_film; VERSIONS.md).
- Cost: 720p 0.86 s/frame (1,921 frames 27.5 min); check stills (every 48th) ~7 min. v2 with 508k trees and
  76k ground pieces: 0.82 s/frame (26.4 min), reveal pass 17 min, check stills 2 min 45 s. 4K final (8 samples):
  5.1 s/frame (2 h 44 min), the reveal pass only over the seam (141 frames, 9.4 min), post 5 min; 715 MB master.
- Still open: the 9:16 cut, 6 stills and the 15 s sizzle (4K frames kept on KB SS for them); subdued canopy fall
  colour, a fast orbit at 34–35 s, pines tinted as hardwoods.
- For clients: any parcel with public lidar (USGS 3DEP) + county GIS + OSM; the honest-view study and the
  approximate-boundary and concept-home labels are part of the product.

### Capra land films, batch 1 (spec for five listing agents) · **720p drafts delivered 2026-10-29**
Five lots in WNC and north Georgia (Timber Cliff, Wilson Cove, Bear Creek, Little Potts, Big Knoll), each with a
different listing agent, made in one night on the shared `Caprastudios/unreal/landfilm/` pipeline (a `lot.json` per
lot, APFS clones of the PetitRidge project, `orchestrate.sh`). Petit Ridge's beats and look; the stone cabin on all
five. Cost per lot: ~45 min of downloads and offline steps (parallel), 16–30 min editor build, 26–31 min 720p.
Details: capra-realtorfilm `references/batch-2026-10-29.md`.

## B. Building blocks (mix and match)

| Block | Proven in | Notes |
|---|---|---|
| Block swarm → any mesh, text or point set | Capra ident, space, TG blocks, canyon | 6k–14k blocks; data in a float EXR |
| Dissolve blocks → solid models (cell hash or wipe + seam) | Capra ident, space v2+ | shared hash in both materials |
| 150k-particle closed-form engine | ParticleLab openers | deterministic per frame |
| Meshy character → animation in Unreal | canyon run, ParticleLab, Amandine | compatible skeletons; retarget to UEFN/Manny for motion matching |
| Animated pose → point bake → blocks/particles | TG blocks, canyon finale, ParticleLab | sample the rest mesh so clips crossfade |
| Motion Design stage + cloners/effectors | TG stage, Capra stage | cloners can't follow animation |
| Lights-off / black-light beat | Capra ident | CONSTANT keys + tube strike flicker |
| Explosion: burst + flash light + shake | space v2+ | colour the burst, keep the light soft |
| Powers-of-ten dive | space v2+ | log-distance PCHIP + aim hand-off |
| Orbit / keypoint camera, PCHIP | everything | key every 2 frames; every frame in shakes and dives |
| Ground-traced character path + obstacle DP | canyon run | any Nanite/landscape world |
| Real terrain: Cesium Google tiles | WSER, Leadville | async streaming, handles, never two renders on one cache |
| Real terrain: Blender DEM + imagery | flyovers | the quality bar |
| Runtime GPU PCG world (Cassini rings) | space | renders only in a game world |
| Day→night keyed light states | flyovers, WSER | per-frame light table |
| Character-carried light (beam + dust + real spot in fog) | Films ident | head track from Blender, one lamp table for shader and light |
| Particle reflections on a glossy floor (mirror ISM) | Films ident | `disable_depth_test`, dimmed by depth below the floor |
| Captions/URL/end-screen overlays (Pillow) | TG openers, canyon, end screen | wording changes need no re-render |
| HTML overlays (ProRes 4444) | canyon popups | kb-ytvideo render.js |
| Sound: Mixkit library mixes placed by hit point | Capra ident, end screen, space | `capra_sfx_library.py` |
| Sound: synthesised cues / sub boom | ParticleLab, space blast | numpy synth |
| Music mux at −14 LUFS | TG pieces | `mux_music.sh` |
| Out-of-process MRQ with check/resume queues | everything Unreal | see pipeline.md |
| Real land from lidar: Nanite tiles, OSM roads, data forest, viewshed | Petit Ridge | techniques.md "Real land from lidar" |

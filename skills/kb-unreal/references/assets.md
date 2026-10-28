# Assets and data on hand

## Unreal projects (Kris's work)
| Project | Path | What's in it |
|---|---|---|
| Intro_motion | `KB SS/Unreal Projects/Intro_motion` | TG_Stage, Capra_Stage; `/Game/TrailGoat` (MI_TG_* palette, M_TG_BlockSwarm, MPC_TG_Blocks, LS_GoatBlocks, Q_*), `/Game/Capra` (M_Capra_BlockSwarm, M_Capra_Solid, MPC_Capra_Blocks, solids, LS_CapraIntro, LS_CapraOutro, Q_*); `Scripts/` (37 files); `Data/` (blocks.exr, capra_blocks.exr + json) |
| CapraSpace | `KB SS/Unreal Projects/CapraSpace` (Cassini clone) | `/Game/Capra` space swarm, solids, LS_CapraSpace, Q_CapraSpace_check/720 |
| TrailGoatElectricDream | `KB SS/Unreal Projects/TrailGoatElectricDream` | `/Game/TrailGoat` goat + 7 moves, finish arch, swarm, LS_CanyonRun; `Scripts/` (20), `Data/` (trail.json, swarm.exr…) |
| ParticleLab | `KB SS/TrailGoat-Studio/ParticleLab` | Space, Smoke, Islands, VFXCollections (mushe/UnrealVFXCollection, MIT) |
| WSER | `KB SS/TrailGoat-Studio/WSER` | Cesium Google tiles + DEM levels, route wake, labels, sequences and queues for commercial/sting/outro/hero, Leadville |
| Capra_intro | `~/Documents/Unreal Projects/Capra_intro` | CapraStudy: ribbon study, World Wakes, Lights Off |
| HostileTakeover | `KB SS/HostileTakeover/unreal` | C++ tower-defense game; Blender asset pipeline |
| Amandine_OW | `KB SS/Unreal Engine/Amandine_OW` | City Sample game prototype |

## 3D models
- **Capra lockup (Meshy)**: `KB SS/Capra Studios/Unreal/IntroMotion/models/
  {unicorn,capra_studios,with_kris}.glb`; solids (FBX + PNG) in `…/solids/`;
  block data `Intro_motion/Data/capra_blocks.exr/.json` (13,752 blocks: unicorn
  2512, capra_studios 10159, with_kris 1081).
- **TrailGoat goat (Meshy rigged biped, 19 clips)**: `TrailGoat/assets/3D
  Models/Meshy_AI_Running_Goat_biped/*_withSkin.glb` (Run_03, Running,
  Jump_Run, Jump_Over_Obstacle_2, Handstand_Flip, Victory_Cheer, Idle_15,
  All_Night_Dance, Big_Wave_Hello, slide_light, climbing_up_wall…; avoid
  Stand_and_Drink). Copies in `ParticleLab/data/goat_src/`. Faces −X.
  Bakes in `ParticleLab/data/`: run03 (20 frames), flip (81), dance (90),
  leap = Jump_Over_Obstacle_2 (21 frames, real airborne leap with 2.15 m of
  travel; Jump_Run is an in-place crouch), each with `head_track.json`
  (forehead lamp + beam) where tracked. FILMS letters: `data/text3d_films/`.
- **Meshy props/islands**: bottle, orange (Citrus Glow), shoe; islands
  (Floating Alpine Citadel, Sky to Summit 25K, Summit Market Isle, Whispering
  Pine Falls, Winding Alpine Ascent) in `TrailGoat/assets/3D Models/`.
- **Blender-built**: finish arch/line/mat (`TrailGoat-Studio/Assets/
  FinishLine/*.fbx`), rounded cube, extruded TRAILGOAT (86 m wide, 38 cm
  bevel), Capra ribbon unicorn (`Caprastudios/blender/capra-ribbon-
  unicorn.blend`), Sky to Summit 25K course model (DEM + GPX).
- **Amandine** (Meshy fitness character, Saint Mercy church from Blender).

## Brand files
- Capra: `Caprastudios/assets/brand/` (mark.svg, wordmark.svg, favicon,
  ribbon-hero.png), `marketing/brand/fonts/` (Red Hat Display 900, Red Hat
  Text, Sedgwick Ave, Rubik Spray Paint), `docs/BRAND.md`,
  `docs/ANIMATION.md`, 4K Meshy lettering/logo exports in
  `KB SS/Capra Studios/Brand/`.
- TrailGoat: `TrailGoat/marketing/launch-kit-2026/` (brand mascots,
  wordmarks, lockups, video kit: chapter cards, lower thirds, intro/end cards,
  topo backgrounds; YouTube thumbnails and banner), `static/tokens.css`,
  `.claude/skills/kb-ytvideo/brands/trailgoat/brand.json`, `studio/
  particle-engine/data/nav_calib.json`.

## Sound
- Mixkit library (free licence, commercial and monetised YouTube use, no
  attribution; don't redistribute files on their own):
  `Caprastudios/output/unreal/sfx/library/mixkit-<id>-*.mp3|wav` +
  `LICENSE.md`. Studio set: 1891 light pull switch, 2579 light switch, 2301
  quick bass switch, 2594/2595/2597 electric glitches, 2132 low electricity
  hum, 3201 electric charge hum, 2602 electronics power-up, 1486 tunnel
  whoosh, 1493 swirling whoosh, 2350 sparkle whoosh, 2583 magical light
  transition, 2900/2902 movie logo/intro impacts, 1143 whoosh deep impact,
  784 reverse cinematic impact. Space set: 653 space soundscape, 1144 space
  stutter riser, 774 space impact, 3003 space deploy whizz, 169 futuristic
  sweep pass-by, 2745 low drone engine hum, 3108 crystal chime, 2523 futuristic
  space intro, 3001 space shot whoosh, 3114 fast sci-fi sweep, 3057
  apocalyptic stomp impact.
- Mixes: `Caprastudios/unreal/capra_sfx_library.py` (r1–r4, outro,
  endscreen, s1, s2); synthesised options `capra_sfx_design.py`.
- Kris's music: `KB SS/TrailGoat-Studio/Renders/blocks/Trail Goat
  {Breakbeat,Tech House} {20s,Opener}.wav`; `Intro_motion/Scripts/
  songs_all.txt` lists in-points. Synth cues: `particle-engine/post/synth.py`.

- Epic sample recordings exported to WAV: `KB SS/TrailGoat-Studio/Music/
  sfx-epic/` — `electric-dreams/` (crickets, forest leaves, foliage rustle,
  boulder impacts ×10, twig snaps, the intro drone) and
  `game-animation-sample/` (sneaker run ×29, jump ×17, land ×20 on concrete;
  starter wind ×2). Epic content: inside Unreal-made video only, never handed
  out. Project Titan's orchestral stems didn't export (no python headless).

- **Capra field-recording library** `KB SS/Capra Studios/Sound/library/` (README with sources and licences): Sonniss
  S1 lake waves (96k), S2 wind in a treeline (96k), S3 night crickets + gusts on a lookout; Pixabay list P1–P9 (crows,
  woodpecker, blue jay in October wind, dry oak leaves, lake lapping, a November cricket) to save by hand.

## Data
- Course data: trailgoat.run API `/api/fuel/courses/{id}` (GPX, aid stations,
  elevation profile); `particle-engine/data/{wser,leadville}.json`.
- Terrain: Terrarium DEM tiles cached in `TrailGoat/scripts/flythrough/.tiles`;
  Cesium Google tiles via a key file (secret — never copy it anywhere).

## Deliverables already made (for reuse and reference)
- Capra: `Caprastudios/output/unreal/` (intro 4K R3, end screen 4K, space
  drafts, studies, sfx).
- TrailGoat: `KB SS/TrailGoat-Studio/Renders/` (blocks, trail, smoke, sky,
  space, flyovers, opener, demo, h01), `TrailGoat-Studio/output/deliverables/`
  (01 YouTube intro 6 s with alpha, 02 outro 20 s, 03/04 commercials 44 s,
  05 landing flyovers, 06 Leadville test).

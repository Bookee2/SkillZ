# Epic samples and templates on this machine

What each one is, where it lives, what runs on the Mac, what to borrow, and
what it lets Capra sell. Full HTML analyses live in `Caprastudios/docs/`;
vault notes in `~/Documents/SecondBrain/inbox/`. Don't modify a sample in
place: clone it (`cp -c -R`). Fab samples carry the Standard licence (use in
Unreal-based work, rendered video is fine; don't hand raw assets to clients
outside Unreal). Don't flag the "NoAI" tag.

| Sample / template | Path | Size | Mac | Best for |
|---|---|---|---|---|
| Motion Design template | Intro_motion (`KB SS/Unreal Projects/Intro_motion`) | 0.7 GB | Yes | Logo stages, idents, block swarms |
| Cinematic template | `~/Documents/Unreal Projects/Capra_intro` | 0.7 GB | Yes | Studies; path tracing on (careful) |
| Electric Dreams | `KB SS/Unreal Projects/TrailGoatElectricDream` | 65 GB | Yes (open `ElectricDreamsSample.uproject`) | Canyon/forest/creek runs, PCG assemblies |
| Cassini | `KB SS/Unreal Projects/CassiniSample` (+ clone CapraSpace) | 2.4 GB | Yes, rings in game only | Space: Saturn, rings, platform + monolith |
| Content Examples | `KB SS/Unreal Projects/ContentExamples` | 15 GB | Yes (Fluids room Windows-marked) | Lookup library: 64 rooms, 1,016 stands |
| ICVFX Production Test | `KB SS/Unreal Projects/ICVFXProductionTest` | 17 GB | Partly (`-DisablePlugins=ICVFX`) | LED-stage practice; canyon + caves |
| Project Titan | `KB SS/Unreal Projects/ProjectTitan` | 63 GB | Yes (Mac binaries + Metal shader cache) | 8×8 km open world, 9 biomes, PCG at scale |
| City Sample | `KB SS/Unreal Engine/Amandine_OW` (Amandine game) | 121 GB | Yes, heavy (~4–30 fps) | City streets, crowds, traffic, PCG city |
| Game Animation Sample | `KB SS/Unreal Projects/GameAnimationSample` (moved 2026-10-08; symlinked from ~/Documents) | 7 GB | Yes | Motion matching, retargeting |
| Niagara Examples Pack | `KB SS/Unreal Projects/NiagraExamples` (sic; First Person template + pack) | 1.3 GB | Yes, all rendered | 59 finished VFX: explosions, sparks, fire, smoke, arcs, mesh bursts, markers, fog |

## Motion Design template → Intro_motion
- Stage map `3D_MotionDesign`: cyc, chrome ring and pedestal, three-light rig,
  cloner sphere. Kris's stages: `/Game/TrailGoat/Maps/TG_Stage`,
  `/Game/Capra/Maps/Capra_Stage`. Config: Lumen HWRT, Substrate, bloom/auto
  exposure/motion blur off, alpha propagation; MCP auto-start.
- Borrow: the stage itself, brand plastic MIs, cloners/effectors, Text3D,
  rounded cube mesh.

## Electric Dreams → TrailGoatElectricDream
- 3.8 km landscape with a detailed ~320 × 380 m area; PCG forest, ditch
  (spline that carves a trail), ground, background graphs; 53 procedural
  assemblies (cliffs, vines, embankments) as packed level actors; Megascans
  25 GB; Substrate on; Lumen HWRT. Shoot map `/Game/Levels/ElectricDreams_Env`.
- Gotchas: its C++ module loads only under the `.app` binary (not `-Cmd`);
  green first frames (pre-roll); camera proxy meshes render black.
- Borrow: the Ditch/Spline PCG for new trails, assemblies, fog cards.

## Cassini → CapraSpace
- True-scale Saturn (PlanetSphere2 + SaturnLUT material), SkyAtmosphere,
  a 15 × 10 m floor plate 2,450 km below the origin inside the ring plane, a
  monolith; the Mars set (removed in the clone). Runtime GPU PCG asteroid belt
  and close-up rocks (compile for Metal; only in game/Simulate). Shape grammar,
  geometry processing and kit-builder graphs.
- Gotchas: LWC precision (local-space maths), BeamMeUp switcher, MRQ not
  enabled (pass `-EnablePlugins=MovieRenderPipeline`), facing the sunlit disc
  reads as a cream wall, sun ~5 lux.
- Clients: space brand films; rule-built spaces (booths, retail); data at
  scale (every customer a rock); orbit-to-doorstep openers.

## Content Examples
- Rooms worth opening for motion: Sequencer (51 stands: Fade tracks, camera
  blends and shakes, Time Warp, Niagara cache reverse), Niagara particles and
  advanced (ribbons, mesh sampling, boids, plexus), Niagara Data Channels,
  Chaos destruction (cached sims played in reverse), materials (vertex
  animation, Pivot Painter, Substrate), lighting and post, Blueprint tools
  (spline meshes, render targets, Editor Utilities), MSDF fonts, MetaSounds.
- Read stands by script (`BP_DemoDisplay` `Title Text`/`Description Text`);
  `new_blank_map(False)` between rooms; migrate assets with Asset Actions →
  Migrate.
- Clients: idents and logo reveals, product heroes, launch reveals, data
  stories, places and spaces, sonic branding, explainers, AI-directed
  production as a service.

## ICVFX Production Test
- Epic/Bullitt 2021 LED-wall test (4.27 assets): Space Junkyard canyon, Cave
  Entrance, Cave Path (baked lighting, manual exposure −5.5 to −8, bloom off,
  colour-correct regions, department sublevels); nDisplay rigs (4-PC and
  1-PC), OpenColorIO LED configs, a Remote Control preset (per-wall grading,
  light cards), 10 Level Snapshots.
- Mac: nDisplay won't load; the shader cache is DirectX-only; Cave Entrance's
  baked lighting shows "Preview". Stage-floor views: junkyard (−397, 7726,
  588), Cave Path (−3040, 7415, 1216), Cave Entrance (−4308, 2664, 1211);
  editor shots need ~1.5 stops less exposure.
- Borrow: locked exposure, colour-correct regions, Level Snapshots for
  variants, a Remote Control browser panel, build only what the lens sees.
- Clients: stage-ready environments (virtual art department) for Atlanta LED
  shoots, commercial backgrounds, event screens run from a web panel,
  installations, live design options, previs, OCIO setup.

## Project Titan
- Epic's 2024 art-jam open world (Standard licence, commercial use): 8×8 km
  TitanMain (World Partition: 12,654 external actors, 855 HLOD actors, a
  16×16 Nanite landscape, 99 lakes and 63 rivers, 143 PCG partition actors),
  biomes Starter Island, Grassland, Desert, Arctic, Tropic, Clifftop (Upper
  City), Marshland, Volcanic, Sulfur; 8,893 static meshes (8,188 Nanite,
  ~437M triangles), 301 PCG graphs, 201 Niagara systems, 762 level instances,
  a day-night manager (`/DayNightCycle/BP_TODManager`, `EUW_TOD`), Mover
  character with glider and raft, Landmass + Water + LandscapeDesigner tools,
  Geometry Scripting and Scriptable Tools (e.g. `EU_DrawRiver`).
- Mac: ships Mac binaries and a 19 GB Metal-only shader cache, but the first
  open rebuilds Nanite meshes for 5.8.3 (13.8 GB RSS, all cores, editor
  unresponsive for a long time) — pause it during renders.
- No cinematic sequences (3 perf-test ones), no Megascans.
- In the editor: `/Game/Maps/TitanMain`; 64 one-kilometre regions are
  `LocationVolume`s named `LandscapeRegion_<x>_<y>` (x, y = 0..7; world X right,
  Y down on the map capture) — `lv.load()` loads one, merged HLOD fills the
  distance. Region picks: grassland 4_4, desert with the labyrinth 1_6, Arctic
  4_1, volcano 6_4 (frame it from outside its ash-cloud volume, which renders
  as noise). The world map capture is `/Game/Blueprint/MapMode/T_MapCapture_D`
  (8K; export with an AssetExportTask). Look: stylised and painterly.
- Borrow: biome sets for flyovers and brand films, PCG graphs (forests,
  roads, cliffs, ivy, bridges), the time-of-day manager, water bodies.
- Clients: stylised world flyovers for games/tourism/events, procedural
  environment builds, open-world pitch films.

## City Sample → Amandine_OW
- Matrix Awakens city: Big City (101,981 external actors) and Small City
  levels, MassAI crowds (VAT) and MassTraffic on ZoneGraph, Chaos vehicles
  with glass damage, MetaHuman crowd, HoverDrone camera, CitySamplePCG (the
  whole city rebuilt in PCG, no Houdini needed), flythrough test sequences.
- Mac: prebuilt dylibs load (BuildId 55116800); Lumen HWRT + SM6 runs ~4 fps
  with a foreground 6K editor, ~30 fps minimised with 75% screen percentage
  and hair cards. Houdini 18.5 files never used.
- Clients: city flythroughs with living crowds and traffic, smart-city/
  mobility data stories, real-estate street context.

## Game Animation Sample
- Motion matching (PoseSearch), Mover, Choosers, Smart Objects, MetaHuman
  Kellan. Used to give the Meshy Amandine character a 109-entry motion
  matching database via UEFN/Manny retargeting. Use for natural character
  locomotion in films (walks, runs, turns) instead of single Meshy clips.

## Niagara Examples Pack → NiagraExamples
- Epic's VFX library for 5.7 (Jan 2026; opens in 5.8): 59 effects in 14
  families (+8 baked-atlas holders): explosions (fire/dirt × S/M/L), sparks,
  fire, fireworks, smoke, weapon impacts per surface, muzzle flash, tracers,
  rocket/ribbon trails, character buffs/debuffs/electricity/teleports, mesh
  bursts (NS_Dino_Tris_Color_Burst: skeletal-mesh triangles coloured from the
  texture; NS_HitDissolve for static meshes), markers, boundaries, pickups,
  footsteps, Tesla coil (NE_Arc), SVT fog banks (BP_FogBankVolume). 46 GPU,
  23 lightweight (stateless), 25 decal, 21 light renderers; 2 Niagara Data
  Channels; 5 effect types. Gallery: `/Game/NiagaraExamples/GalleryLevel`
  (playable FPS range, 10 help stands with explanations, LWC copy 1,000,000
  units out). Epic course: "Niagara Examples Pack" (9 modules).
- Mac: everything renders in MRQ (`/Game/CapraLab/NX_Showcase` +
  `LS_NX_Showcase`; 1,074 frames at 720p in ~2 min). Standalone, NS_Marker_*
  and NS_Pickup_Spawn draw nothing (gameplay params), the Tesla coil needs a
  target, character effects need a skeletal mesh user param. Grey floor →
  dirt-explosion decal draws as a dark square.
- Borrow: mesh → own-colour particles for statue/logo bursts, markers and arcs
  in-engine, explosions/sparks/fireworks for reveals, footstep dust for
  TrailGoat, fog banks. Migrate single systems (Asset Actions → Migrate).
- Clients: product/logo particle reveals, game-studio VFX, LED/event loops,
  map and data films with markers.
- Report: `Caprastudios/docs/niagara-examples-analysis-2026-10-08.html`; reel
  `Caprastudios/output/niagara/niagara-showcase-720.mp4`.

## Not on this machine / not usable here
- Niagara Fluids beyond Gas 3D, nDisplay, the Path Tracer at high spp (kernel
  panic) — Windows or tiled only.
- Fab samples listed for an older engine: tick "Show all projects" in Add to
  Project and pick the older content version (how the Niagara pack went in).

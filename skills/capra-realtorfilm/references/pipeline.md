# Parcel to film: the pipeline

**One pipeline for every lot** (2026-10-29): `~/Desktop/Projects/Caprastudios/unreal/landfilm/`. Every number that
belongs to a lot lives in that lot's `Data/lot.json`; the scripts are shared (`lot.py` loads it, offline and in the
editor). Petit Ridge's own folder (`unreal/petit_ridge/`) stays as the reference it was built from.

```
Lots/<Slug>/Data/lot_in.json   address, county, parcel file, listing facts, agent  (you write it)
make_kit.py <Data>             DEM hero 1 m + wide 2 m + horizon 20 m, water, georef  -> lot.json
osm_fetch.py <Data>            OpenStreetMap roads (slow server: runs on its own)
lot_offline.sh <Slug>          home terrain lidar naip trees site photos view camera forest ground
new_lot.sh <Slug>              APFS clone of the PetitRidge project as Lots/<Slug>/<Slug>.uproject
lot_editor.sh <Slug>           build scene forest film: every editor stage, unattended, then quit
render_lot.sh <Slug> check|720|4k   out of process, Blender batch frozen
post_lot.sh <Slug> <NN> [vN] [720|1080]   post_film.py (lint first for "type": "phone") + the mix + review copy
```
The clone keeps the Megascans forest, ground cover and presets, Electric Dreams' renderer block in
`Config/DefaultEngine.ini` (required: a blendable GBuffer crashed Megascans foliage), the materials and the map, at
no disk cost; `pr_build.py reset` deletes the template's terrain, site meshes, home and lot textures so the stages
rebuild them. Content stays under `/Game/PetitRidge` in every clone (renaming it buys nothing).

## Coordinates (the one convention everything shares)
Hero grid: a 4,033 m square, 1 m per sample, x east and y south from its NW corner, z = elevation − Z0
(`lot.json`; Z0 = middle of the hero's range). UTM E = E0 + x, N = N0 − y in the lot's own NAD83 / UTM zone
(WNC is 17N, most of north Georgia 16N). The far ring is the 8,066 m area at 2 m centred on the hero (offset
−2,016 m), decimated to 8 m and 3 m lower; the horizon DEM (80 km at 20 m) is only for the view study. The hero is
centred on the lot; `lot_in.json hero_offset_m` shifts it when water or the approach needs the room.

## What site_plan.py decides (check it, don't trust it)
- **Home site and facing** (`site_plan.py <Data> home`): candidates every 8 m at least 22 m inside the lines with
  the pad and its banks inside; skyline distance every 5° (bare earth + an assumed 20 m forest, first 120 m
  cleared, earth curvature), water in sight counted double; cut-and-fill and relief against it; `prefer_bearing`
  breaks ties. `--at x,y --bearing b` overrides.
- **Camera** (`site_plan.py <Data> camera`): `film_path.template()` (Petit Ridge's beats, relative to the lot, the
  home and the view) with the opening low over the valley or the water along the view line, then any key lifted
  until the path before the drop clears the real canopy by 30 m (18 m in the opening).
- **Cards**: place and region, elevation, lot and acreage with the boundary caveat, elevation range and aspect, the
  view (water share from the lidar canopy, or the farthest ridge in sight), concept home, winter, end card.

## Stages, in order
1. **Kit** (`references/data.md`): parcel outline, DEM hero + wide heightmaps (16-bit PNG; height = lo + v/65535 ×
   range), lot outline CSV in hero cm, water outline, OSM roads (`osm_hero.json`), `georef.json` (pixel → lon/lat).
   Petit Ridge's kit came ready-made (`PetitRidgeKit/README.md` documents it); for the next parcel write the kit
   steps into a `kit.py` first and keep it here.
2. **Terrain** (`terrain_tiles.py` → `pr_build.py level cabin terrain`): pad and lakebed carved in numpy, 8×8
   Nanite glTF tiles + far ring, imported with Interchange (`combine_static_meshes_behavior`), `hero_heights_m.npy`
   saved for everything that drapes.
3. **Site** (`site_meshes.py` → `pr_scene.py site textures materials place`): roads, lot line + curtain, water,
   ground photos, the terrain material (litter near, the NAIP canopy photo far, Read the Land contours), the home.
4. **Real trees** (`ept_fetch.py`, `lidar_trees.py`, `naip_textures.py`, `forest_points.py <Data> <Kit>`,
   `groundcover_points.py` → `pr_forest.py leaves meshinfo forest ground`): CHM, tree tops, evergreens, infill,
   far-ring trees from the photo's forest mask, understory, shore shrubs, ground cover. Run `meshinfo` before
   trusting any mesh list (sizes vary 30×).
5. **Honest numbers** (`viewshed.py`): bare earth, assumed and real canopy; the real one goes on screen.
6. **Camera** (`film_path.py`): trace offline (speed, turn rate, clearance) and against the placed trees
   (`clear_check.py` pattern in petit-ridge.md); interpolate the view direction, not the look-at point.
7. **Sequence** (`pr_seq.py post look`, `pr_film.py haze lights film reveal`): cameras keyed every frame, MPC keys
   at tick resolution (×1000) but channel `add_key` in display frames, leaf tracks per component, the home hidden
   until just before its reveal, the no-cabin sequence trimmed to the reveal seam.
8. **Render** (`render_lot.sh <Slug> check|720|4k` over `pr_render.sh`: out of process, freezes the Blender batch):
   check stills every 48th frame (2 samples, ~2.5 min), then the 720p film and the no-home reveal pass. Close the
   editor first; never send remote Python during a render. Grep the render log for `Failed to compile Material`
   before reading the stills.
9. **Post** (`post_lot.sh <Slug> <NN>`, or `post_film.py <frames> <out> --lot <Data> --reveal <no-home frames>
   [--unbranded] [--workers 8]`): frame 0 →
   frame 1 (brown water until reflections warm up), the World Wakes seam, cards and credits scaled from 720p, the end
   card; frames composite in parallel. Then `mix_film_v2.py` (real field-recording beds; `dc_mix.py` for a data-center
   film) and mux at −20 LUFS; a review copy under ~14 MB for SendUserFile (post_lot.sh sizes the bitrate from
   lot.json `end_s`, which also names the file). A final also gets a 1080p preview and a 720p-vs-4K detail crop.
   **Size the type for a phone** (Kris reviews on his phone; Project Sail v2: "the fonts are too small to read on
   the phone"): lot.json `"type": "phone"` (every new lot) gives pin titles 32 px at 720p (~10 pt on a phone held
   upright), chips 44/25 with wrapped source lines, dark plates under pins, a shaded chip corner, and pins that place
   themselves clear of each other, the chips and the property outline. `post_film.py - - --lot <Data> --lint`
   (post_lot.sh runs it) checks every label against the frame, the others, the pin dots and the chips every 1/8 s.
   Judge stills shrunk to 390 px wide. `"classic"` (the default) re-posts older films byte for byte.
10. **QA the final against the approved draft** (`scan_frames.py` on both frame folders, compare by frame number): only
   differences from the draft are faults.

## Timber mode (a tract, no home: lot.json "mode": "timber"; Buckeye Road, 2026-11-16)
For a fund or a land broker selling acreage: no house, no contours on flat land, the stands instead. lot_in.json adds
`"mode": "timber"`; lot.json gets `timber.planted` (the listing's planting year) and `split` (the concept division).
1. `make_kit.py` → `osm_fetch.py` (background) → `ept_fetch.py --find` + the LAZ download → `naip_fetch.py` (windowed
   by default) → `terrain_tiles.py` (no pad) → `lidar_trees.py` → `site_meshes.py` → `naip_textures.py` (no fall
   grade in timber mode). Skip `site_plan.py`, `viewshed.py`, `forest_points.py`, `groundcover_points.py`.
2. `timber_stands.py`: stands (plantation / mature / water / open / cut since the lidar) from the lidar's stand height
   and the newest photo, rows from the photo's spectrum → timber/stands.json, stand_map.png, stand_preview.jpg.
   Look at stand_preview.jpg against the photo before going on.
3. `timber_points.py`: plantation rows (young Baltic Pine C/D sized for the planting year), the mature stands from the
   lidar tops (pine A/B or summer Hornbeam), the hero outside the parcel (cut-since trees dropped, young stands added),
   the far ring from the photo's forest (per-tile Otsu). ~510k trees.
4. `timber_split.py` (lot.json split: frontage vertex ranges, the new road's polyline, tracts per side): road lots
   square to the county road, tracts cut at equal acres square to the new road, slivers merged. Check split_preview.jpg.
5. `timber_meshes.py`: canopy-top surface, then LotLine/LotCurtain on the canopy, StandSheet, StandEdges, SplitLines,
   ConceptRoad (Data/site). 6. `timber_plan.py`: camera, MPC curves (StandMix, StandDraw, RoadDraw, SplitDraw),
   sun, exposure, cards, pins, credits into lot.json; prints speed / turn / clearance over the 2026 canopy.
   Keep under ~120 m/s low, 20°/s of turn, 25 m over the canopy; check the pins stay inside the frame.
7. `lot_editor.sh <Slug>` as usual (the home, place, lights and reveal stages skip themselves), `render_lot.sh`
   (no reveal pass), `post_lot.sh` (pins are projected through film_path's camera in post);
   post_lot.sh passes `--day` to the mix (no blue-hour end, so no crickets or night bed). A 1080p version:
   `render_lot.sh <Slug> 1080` then `post_lot.sh <Slug> NN vN 1080` (crf 16, `_1080p` in the name).
Pines: Megaplants Baltic Pine converted to static Nanite in FabStaging (`pine_convert.py`), copied into the lot's
Content (`/Game/Megaplant_Library`, `/Game/CapraPines`). Clone the lot from PetitRidge as usual, then copy those in.

## Data-center mode (a proposed campus: lot.json "mode": "datacenter"; Project Sail, 2026-11-18)
Today → cleared → graded → built, measured to scale, the view from the public road, the region round it.
`references/projectsail.md` is the reference production. Each script's docstring says how to run it.
1. **Kit** as usual (make_kit.py centres the hero on the outline's box, not its vertex mean), plus `source/vectors`
   (FEMA flood zones, streams, wetlands, lakes, building footprints, transmission lines: `data.md`) and the program
   from the DRI filing in lot.json `dc`. `dc_sitecheck.py`: a first read of whether a roof of the program's height
   shows from the roads, on bare earth and with the lidar canopy kept (it decides the road beat).
2. **Layout** (Kris approves it before any 3D): `dc_layout.py` (equal floor plates on level pads inside the setbacks,
   buffers, flood zones, wetlands, stream buffers and line clearances; greedy pads with a 2 m gap: the pads carry their
   aisles), `dc_siteworks.py` (entrances, least-cost drives, ponds, admin), `dc_grade.py` (pads, 8 % roads, ponds; earth
   moved, disturbed acres, forest cleared → the cards), `dc_towers.py` (the real line structures from the lidar).
3. **Kit in Blender** (one model for the film and the web): `dc_prep_blender.py` (in the venv: textures, ground colours,
   trees) → `dc_blender.py kit / scene / stills / export` → `blender/kit/*.glb`. Look at `Renders/check3d` with Kris.
4. **Unreal**: clone the BuckeyeRoad project (summer pines, Substrate renderer block). `dc_forest.py` (lidar trees +
   infill where the photo shows forest the leaf-off lidar missed, split into kept and cleared), `dc_terrain_graded.py`
   (G_ tiles only where the earthwork touches), `dc_works_textures.py`, `dc_outline.py` (the property line on the kept
   canopy, never on the ground under it), `region_fetch.py` + `region_tiles.py` (the ±40 km zoom-out ground),
   `dc_plan.py` (camera A and B, MPC BuildPhase / GradeMix, cards, pins, edge pins, atmosphere keys; lints the framing
   and every pin). Then `lot_editor.sh` and `pr_dc.py graded kit place clear region trees`.
5. **Render** `render_lot.sh <Slug> 720` (the film, then the trees pass LS_Film_Trees as the "reveal": the forest
   crossfades out in post because Nanite ignores ISM cull distance), **post** `post_lot.sh <Slug> <NN> vN` (dc_mix.py,
   the 130 s name from `end_s`).
Atmosphere for a climb to ~30 km: volumetric clouds off before the camera reaches them, aerial perspective ×0.2 and fog
×0.08 keyed over the climb (lot.json `atmos`), or the map washes pale blue. Text and numbers: `projectsail.md` honesty
rules (illustrative layout label, measured road views, straight-line distances to a named point).

## Timings (M5 Pro, Petit Ridge v2: 508k Nanite trees, 12k understory, 76k ground pieces, Lumen HWRT)
| Step | Time |
|---|---|
| NAIP textures (4 tiles → two 8K maps) | 2 min |
| Lidar trees (79 M points) | 2 min |
| Editor open + forest/ground/film stages | ~5 min |
| Check stills, 41 frames, 2 samples | 2 min 45 s |
| 720p film, 1,921 frames, 4 samples | 26.4 min (0.82 s/frame) |
| 720p no-cabin pass | 17 min from frame 0 (before trimming), ~3 min trimmed |
| 4K test frames (every 192nd, 8 samples) | ~30 s each: jumps rebuild every cache, so continuous runs are faster |
| 4K film, 1,921 frames, 8 samples | 2 h 44 min (5.1 s/frame); 19 GB of PNGs |
| 4K no-cabin pass, 141 frames (1100–1240) | 9.4 min |
| Glitch scan of the 4K (`scan_frames.py`, 8 processes) | ~3 min |
| Post at 720p (composite + cards) | 3 min |
| Post at 4K (composite + crf 14 encode, 8 workers) / mux + 1080p preview + review copy | 4.4 min / 44 s |
| 1080p timber film (Buckeye Road: 510k assembly pines), 1,921 frames, 8 samples | 68 min (2.13 s/frame); 6.4 GB of PNGs |
| Post at 1080p (composite, pins, crf 16, day mix, mux, review copy) | 1.7 min; master 256 MB, review copy 11 MB |
| 720p data-center film (Project Sail v2: 398k trees, 9 halls, the region mesh), 3,121 frames, 4 samples | 30.4 min (0.58 s/frame) + 64-frame trees pass 95 s |
| Post at 720p, 130 s (composite, phone type, dc_mix, mux, review copy) | ~3 min; master 171 MB, review copy 13.8 MB |
Total for a 4K final once the 720p is signed off: about 3 h, nearly all of it the film render.
Instance count barely matters on Nanite: 508k trees rendered no slower than 292k.

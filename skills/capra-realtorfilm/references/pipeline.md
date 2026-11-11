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
post_film.py <frames> <out> --lot <Data> --reveal <no-home frames>;  mix_film_v2.py <out> <name> [--water]
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
   card; frames composite in parallel. Then `mix_film_v2.py` (real field-recording beds) and mux at −20 LUFS; review
   copy ~1 Mbps for SendUserFile. A final also gets a 1080p preview and a 720p-vs-4K detail crop for the client.
10. **QA the final against the approved draft** (`scan_frames.py` on both frame folders, compare by frame number): only
   differences from the draft are faults.

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
Total for a 4K final once the 720p is signed off: about 3 h, nearly all of it the film render.
Instance count barely matters on Nanite: 508k trees rendered no slower than 292k.

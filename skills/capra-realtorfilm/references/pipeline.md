# Parcel to film: the pipeline

Template code: `~/Desktop/Projects/Caprastudios/unreal/petit_ridge/` (Petit Ridge, 2026-10-28). For a new parcel,
copy the folder to `Caprastudios/unreal/<parcel_slug>/` and the project with an APFS clone
(`cp -c -R "KB SS/Capra Studios/Unreal/PetitRidge" "KB SS/Capra Studios/Unreal/<Parcel>"`, then rename the
.uproject and delete its `Data/`, `Renders/`, `Saved/`, `DerivedDataCache/`). The clone keeps the Megascans
forest, ground cover and presets, Electric Dreams' renderer block in `Config/DefaultEngine.ini` (required: a
blendable GBuffer crashed Megascans foliage) and the map; the terrain, site, forest and sequence stages rebuild
everything parcel-specific.

## Coordinates (the one convention everything shares)
Hero grid: a 4,033 m square, 1 m per pixel, x east and y south from its NW corner, z = elevation − Z0. Unreal cm
= metres × 100. UTM of hero (0, 0) comes from the parcel corners in both frames (Petit Ridge: E 745,802,
N 3,820,567, NAD83 / UTM 16N). The far ring is the 8,066 m wide area at 2 m, decimated to 8 m, offset
(−2,300, −2,200) m and 3 m lower so the hero wins. Pick the hero square so the lot, any water and the camera's
whole path fit inside it.

## Site constants to change per parcel
| Where | What |
|---|---|
| `pr_common.py` | `KIT`, `CABIN_GLTF`, `DATA`, `Z0_M`, `CABIN_LOC`, `LAKE_Z` |
| `terrain_tiles.py` | `Z0`, `PAD` (centre, bearing, size, level), `carve_lake` seed and box, the heightmap scale, the far ring offset |
| `site_meshes.py` | lake level, road classes kept |
| `forest_points.py`, `viewshed.py`, `groundcover_points.py` | cabin centre, deck bearing, clearing radius, view corridor (depth, half-angle), eye height |
| `naip_textures.py`, `lidar_trees.py` | `E0`, `N0` (UTM of hero 0, 0), far ring offset, UTM zone (EPSG) |
| `ept_fetch.py` | the hero box in lon/lat (+150 m) and the EPT project name |
| `film_path.py` | `CAB`, `LOT`, camera keys A and B, `LAKE_VIEW`, `PARAMS` (lot draw, glows, data mix, leaf, reveal), `SUN`, `INTERIOR`, `EXPOSURE_A`, `END_S`, `CUT_S` |
| `pr_film.py` | `CABIN_SHOW_F`, `REVEAL_RANGE` (follow `post_film.REVEAL_T`) |
| `post_film.py` | `CARDS` (times, facts), `CREDITS`, `REVEAL_T` |
| `mix_film_v2.py` | bed timings (they follow the beats) |

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
8. **Render** (`pr_render.sh <Queue> <dir> <last frame> [keep]`: out of process, freezes the Blender batch):
   check stills every 48th frame (2 samples, ~3 min), then `draft720.sh`, later `final4k.sh`. Close the editor first
   (`run.sh quit.py`); never send remote Python during a render.
9. **Post** (`post_film.py <frames> <out> --reveal <no-cabin frames> [--unbranded] [--workers 8]`): frame 0 →
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

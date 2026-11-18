# Real structures: a measured building for a website and a film (KSU West Parking Deck, 2026-11-18)

Kris: "can we make a land film of this real parking deck in its real dimensions" (3510 Campus Loop Rd, Kennesaw).
The real job was a model for his friend's WebGPU site that shows open spaces per section and for the whole deck;
the film shows the friend the model. Code: `Caprastudios/structures/` (each script's docstring says how to run it);
data and renders: `KB SS/Capra Studios/Structures/<Slug>/`. Blender, not Unreal: one model serves the film and the web.

## Pipeline
1. `deck_fetch.py` — site.json (address, OSM way, box) → USGS LAZ tiles (TNM API names the tiles for a bbox),
   3DEP 1 m DEM window, the newest NAIP window at full resolution. rockyweb.usgs.gov answers **429 to parallel
   downloads** and resets long transfers: one file at a time with `curl -C -` resume (~50–120 KB/s). The tiles are
   not on the prd-tnm S3 mirror.
2. `deck_measure.py` — registers the OSM outline on the lidar's building returns (±12 m search; a tile that clips the
   building drags the fit, so read every tile that touches it), the deck frame (long axis), top-deck rasters (10th
   percentile per 0.5 m = the slab under any cars), grade around each side from class-2 returns, facade elevations.
3. `deck_photo.py` — the photo in the deck frame; stall stripes by a shear search (stripe angle) + FFT along the row.
4. `deck_layout.py` — levels, bays/zones, ramp, columns, spandrels, poles and every stall (id, quad, z), from the
   measured plan kept in site.json "deck" (edit there).
5. `campus_prep.py` — terrain at 2 m, a model-look ground from NAIP (paper, sage grass, OSM roads, OSM water), OSM
   footprints extruded to the lidar's 90th-percentile roof, lidar tree tops (drop trees within 1.8 m of a building).
6. `deck_blender.py build|still|film|glb|glbplain`, then `deck_post.py` (land-film cards; pins ride per-frame anchors
   exported from Blender's camera, so labels follow levels as they lift).

## What lidar and photos can and can't tell about a building
- **Floors through the open sides**: a parking deck's openings let oblique pulses hit the lower slabs near the edge.
  Histogram the heights of returns 0.5–8 m inside the outline, below the top deck: peaks are slab tops (313.1, 316.4).
  Facade elevations (returns within ±3 m of each face, plotted along the face) show the parapet, the spandrel bands
  and the grade line. The ramp's low end on the top deck gives floor-to-floor directly (319.15 → 316.0 = 3.1 m).
- **The level count stays ambiguous** on a hillside (ground fell 12.8 m to one corner: room for 5 levels; OSM said 3).
  Ask; build with the count as one setting. A sloped centre bay over the lowest level has no headroom at its low end:
  that geometry itself hints at a level below.
- **NAIP leans raised roofs**: the top deck sat 4.4 m W / 1.5 m N of the lidar (relief displacement), the ground ~2 m.
  Don't shift the whole photo by a roof offset; paint every roof out (lidar class 6 widened 3–6 m, flat concrete).
- **Stalls**: 30 cm NAIP resolves stripes only with a shear search + FFT on clear rows (peak/mean ≥ 3): 2.61 m along
  the aisle at ~76° (8 ft 6 in). Real counts per level and zone come from the owner, never from the model: say so.
- Night lidar flights (GPS time → 23:23 local) leave a deck empty: clean slab heights.

## Web model
- One mesh and one material per zone (`L<n>_<West|Centre|East>`, `Zone_L<n>_…`), levels as groups (`Level_1..3`), the
  structure merged per level; leave out film-only parts (foundation fill, outline curve). Draco 38 KB, plain 277 KB.
- **Artifacts don't serve .glb** and block fetches to CDNs (so no Draco decoder): ship the plain GLB as a base64 JS
  module and `GLTFLoader.parseAsync`. three@0.170.0 `three/webgpu` via an import map from jsDelivr: WebGPURenderer with
  automatic WebGL 2 fallback; `NeutralToneMapping`.

## Film (Blender EEVEE, 720p, ~1-2 s a frame; Kris wants demo films 10-15 s: `DECK_CUT=short`, 14 s)
- AgX turns bright emissive overlays pastel: saturated base colour, emission ~0.5, alpha ~0.94.
- Late afternoon: sun 7 W/m² (1.0, 0.74, 0.5) from az 242° el 19°, sky background 0.11, exposure −0.2. Sky 0.3 read cold blue.
- Keep the camera ~120 m+ over a deck in 20 m trees and pitch the opener down so the terrain box's edge stays out.
- Model trees: ico crowns r = clip(min(ray, 0.28h + 1.2), 1.5, 6.5), half-height max(0.3h, 0.9r); tall ovals read as broccoli.

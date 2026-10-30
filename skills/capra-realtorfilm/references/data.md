# Parcel data: sources, endpoints, licences, gotchas

All free and public. Ask Kris before downloading (list files, sources, sizes). Keep each download in its own
folder under `KB SS/Capra Studios/Unreal/<Parcel>/Data/source/`; read them with `python -I`. Python's urllib
fails SSL on this Mac: use curl. A scratch venv with numpy, Pillow, scipy, rasterio, laspy[lazrs], pyproj does all
of it (no GDAL or PDAL needed).

| Data | Source | Size (Petit Ridge) | Licence / credit |
|---|---|---|---|
| Parcel outline | NC: the statewide NC OneMap layer (`services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/1`, public, query by `parno` or a point). GA: county by county — Dawson below; Union `services.arcgis.com/ISpzx3B5ZsVA6e1Z/ArcGIS/rest/services/Union_Web_Map_2026_Update/FeatureServer/18`. Otherwise the county's public ArcGIS parcel layer (find it from the county GIS hub; Dawson: `services7.arcgis.com/Ptz860OPLeIY55cX/arcgis/rest/services/Energov_Layers_Update2021/FeatureServer/3`, query `PARCELID='016A 009'`, `outSR=4326`, `f=geojson`) | KB | public record; on screen: "Boundaries approximate (county GIS, not a survey)" |
| Bare-earth DEM, 1 m | USGS 3DEP elevation image service, cut straight onto the hero grid in UTM (`elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage`, `bboxSR=imageSR=269xx`, F32 tiff, bilinear) — `landfilm/make_kit.py`. A 4033 px request answers 502; 2017 px blocks that share an edge sample work (~17 MB, ~18 s each). Hero 1 m, wide 8 km at 2 m, a 40 km horizon at 20 m for the view study | ~195 MB a lot | public domain; "Terrain: USGS 3DEP lidar" |
| Lidar point cloud (the trees) | USGS 3DEP **EPT on AWS**: `s3-us-west-2.amazonaws.com/usgs-lidar-public/<project>/ept.json` (Web Mercator; walk `ept-hierarchy/`, fetch `ept-data/<D-X-Y-Z>.laz` 8 at a time) — `ept_fetch.py`. Find the project name from the TNM LPC listing for the bbox | 2,145 nodes, 694 MB, ~6 min | public domain |
| Aerial photos, 60 cm, 4-band | USDA **NAIP** via Microsoft Planetary Computer: STAC `POST /api/stac/v1/search` (`collections: ["naip"]`, bbox), anonymous token `GET /api/sas/v1/token/naip` appended to the blob URL | 4 tiles × ~510 MB | public domain; USDA asks for a credit: "Imagery: USDA NAIP" |
| Roads | OpenStreetMap via Overpass (`highway` ways in the hero box, with geometry) — `landfilm/osm_fetch.py`. Answers 406 without a User-Agent and 502 "at capacity" when busy: retry with backoff across mirrors, and never block the rest of the kit on it | KB | ODbL: "Roads © OpenStreetMap contributors" |
| Water outlines | from the DEM's hydro-flattened areas (Petit Ridge kit) or NHD | KB | public domain |
| Satellite colour (fallback, 10 m) | Copernicus Sentinel-2 L2A COGs on AWS | ~100 MB | "contains modified Copernicus Sentinel-2 data" |

## Gotchas (each cost time once)
- **USGS rockyweb throttles** LAZ downloads (HTTP 429, ~100 KB/s): use the EPT copy on AWS instead.
- **Leaf-off lidar** (most 3DEP flights): bare hardwood crowns return few pulses, so a 1 m canopy model is full of
  holes; roofs, wires and towers make 60 m "trees". Use vegetation classes 3–5 only, the highest return in a 3×3
  search, close pits, blur 0.9 m; fill trees where the surrounding canopy is tall but no top was found.
  Evergreens show as crowns whose returns are mostly high vegetation (share > 0.6).
- **NAIP needs NIR** for anything that tests vegetation: inpaint all four bands, or the filled patches skip the
  grade. Water in the photo is NDVI < 0 and NIR < 80/255 (not < 0.16: the lake read NIR ≈ 48).
- **Register** the photo against the lidar lake edge (shift search ±6 m) before trusting it; Petit Ridge was
  within 1 m. The EPT points (WGS84 Web Mercator) sat 1 m off the NAD83 DEM: register the point cloud's ground
  against the terrain too (median error 0.18 m after the shift).
- **Neighbours' houses**: remove them from the photo (compact low-NDVI blobs away from roads and water, plus the
  lidar's class-6 building cells) and plant trees on their lots, or the slopes show bald patches.
- County aerials can be sharper (Dawson 2024 ~15 cm) but are leaf-off, have tile export switched off and state no
  licence: ask the county before using them. Google Photorealistic 3D tiles need Google's logo and credits on
  screen and melt forest into lumps.
- No public data gives finer ground **shape** than the 1 m DEM under forest, and no aerial source gets near the
  2 cm/px of a cabin close-up: close ground comes from 3D ground cover.

## Finding lots and their lines (the 2026-10-29 batch)
- **Check the parcel against the listing, not just the ID.** Big Knoll's MLS parcel ID (038 077 A20) was a different
  lot 500 m away; the right one (038 077 A01) matched on lot number, acreage and lake frontage.
- **New subdivision lots often aren't in county GIS yet** (Kalmia Knoll: only the 78.9-acre parent tract; the
  10.83-acre lot exists on a marketing photo). No lines, no lot-line beat: swap the lot or ask Kris.
- **Tracts of several parcels** (Little Potts: three) merge into one outline (`make_kit.py` rasterises, closes the
  slivers, traces it back). County lines and listings disagree by 0–10 %: quote the listing.
- **County-by-county lidar**: a lot near a county line needs every flight that overlaps it (`ept_fetch.py --find`
  keeps all of the newest year; node files are prefixed by project so they don't collide). Picking one by name
  fetched Rutherford County's flight for a Buncombe lot.
- **Reservoirs drawn down in the lidar**: TVA lakes are flown in winter at low pool (Nottely: 1,766 ft against a
  1,777 ft summer pool), so the shore is mudflat. `lot.json water_fill` floods the connected ground below the level.
- **Hurricane Helene (Sept 2024)**: every WNC dataset predates it (NC lidar 2017, newest NAIP Sept 2022). Check the
  listing photos for blowdown, slides and washouts before trusting the trees, and avoid the worst-hit gorges.
- **The listing's selling view decides ties**: views that reach the 40 km horizon score alike in every direction, so
  `prefer_bearing` (sunset = ~250) turns the home to what the listing sells.

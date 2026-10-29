# Parcel data: sources, endpoints, licences, gotchas

All free and public. Ask Kris before downloading (list files, sources, sizes). Keep each download in its own
folder under `KB SS/Capra Studios/Unreal/<Parcel>/Data/source/`; read them with `python -I`. Python's urllib
fails SSL on this Mac: use curl. A scratch venv with numpy, Pillow, scipy, rasterio, laspy[lazrs], pyproj does all
of it (no GDAL or PDAL needed).

| Data | Source | Size (Petit Ridge) | Licence / credit |
|---|---|---|---|
| Parcel outline | the county's public ArcGIS parcel layer (find it from the county GIS hub; Dawson: `services7.arcgis.com/Ptz860OPLeIY55cX/arcgis/rest/services/Energov_Layers_Update2021/FeatureServer/3`, query `PARCELID='016A 009'`, `outSR=4326`, `f=geojson`) | KB | public record; on screen: "Boundaries approximate (county GIS, not a survey)" |
| Bare-earth DEM, 1 m | USGS 3DEP via the TNM API (`tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital Elevation Model (DEM) 1 meter&bbox=…`), tiles on `prd-tnm.s3.amazonaws.com` | 4 tiles, ~120 MB for 8 km | public domain; "Terrain: USGS 3DEP lidar" |
| Lidar point cloud (the trees) | USGS 3DEP **EPT on AWS**: `s3-us-west-2.amazonaws.com/usgs-lidar-public/<project>/ept.json` (Web Mercator; walk `ept-hierarchy/`, fetch `ept-data/<D-X-Y-Z>.laz` 8 at a time) — `ept_fetch.py`. Find the project name from the TNM LPC listing for the bbox | 2,145 nodes, 694 MB, ~6 min | public domain |
| Aerial photos, 60 cm, 4-band | USDA **NAIP** via Microsoft Planetary Computer: STAC `POST /api/stac/v1/search` (`collections: ["naip"]`, bbox), anonymous token `GET /api/sas/v1/token/naip` appended to the blob URL | 4 tiles × ~510 MB | public domain; USDA asks for a credit: "Imagery: USDA NAIP" |
| Roads | OpenStreetMap via Overpass (`highway` ways in the hero box, with geometry) | KB | ODbL: "Roads © OpenStreetMap contributors" |
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

---
name: capra-realtorfilm
description: Make a Capra Studios land film for a realtor or land broker from an address or parcel ID — a 3D flyover of the real lot built from public lidar, aerial photos, county parcel lines and OpenStreetMap in Unreal Engine (real terrain, the real trees, the lot line drawn on, an honest view study, an optional labelled concept home), delivered as a 16:9 film, a 9:16 cut, stills and an unbranded MLS cut. Use when Kris types /capra-realtorfilm with a lot, or asks for a land/lot/listing flyover, a "Petit Ridge style" film, or a realtor or broker video. Interactive: the interview needs Kris.
argument-hint: <address or county + parcel ID> [for <agent or brokerage>] [spec|paid]
---

# Capra realtor film

`/capra-realtorfilm 37 Petit Ridge Dr, Big Canoe GA (Dawson 016A 009) for Big Canoe Brokerage`

One run goes **read the request → load what's proven → assemble the parcel kit → interview → treatment →
720p build and review loop → 4K final → deliverables → close out by improving this skill**.

This is the product version of the Petit Ridge spec film (2026-10-28): every step below has run once, end to end,
and the code is in `~/Desktop/Projects/Caprastudios/unreal/petit_ridge/` (each script's docstring says how to run
it). A new parcel reuses that pipeline with new data and new site constants; it does not start from scratch.
Kris is the creative director and the client brain. Never guess the client's branding, the facts on screen or
whether to show a concept home: ask.

## 0. Read the request

Pull out: the **parcel** (address, county, parcel ID; lat/lon if given), the **client** (listing agent or
brokerage, or none for a spec piece), **spec or paid**, where it will play (listing site, MLS, YouTube, social,
a pitch meeting), and any deadline. If there's no parcel, ask for one before anything else.

## 1. Load what's proven (every run)

Read in full:
1. `references/product.md` — the market, prices, compliance rules (concept-home label, approximate boundaries,
   unbranded MLS cut, honest view numbers), deliverables and naming.
2. `references/pipeline.md` — the parcel-to-film pipeline step by step: which script does what, which site
   constants change per parcel, timings, the render plan.
3. `references/data.md` — where every dataset comes from (endpoints, sizes, licences, credit lines) and the
   gotchas (throttled servers, leaf-off lidar, house removal).
4. `references/petit-ridge.md` — the reference production: beats with times, numbers, versions, Kris's notes.

Then the Unreal machine knowledge this depends on, from the kb-unreal skill (`~/.claude/skills/kb-unreal/references/`):
`lessons.md` (everything), `pipeline.md` (editor control, render and encode recipes), and in `techniques.md` the
sections "Real land from lidar" and "Real ground and real trees". Run kb-unreal's `scripts/preflight.sh`: KB SS
mounted, disk free, no editor or render already running.

## 2. Assemble the parcel kit (ask before downloading)

From `references/data.md`: the parcel outline (county GIS), the 3DEP 1 m DEM (4 km hero, 8 km wide), the lidar
point cloud (USGS EPT on AWS), NAIP aerial photos, OSM roads, water outlines. **List every file, its source and
size, and get Kris's yes before downloading.** Put sources in `KB SS/Capra Studios/Unreal/<Parcel>/Data/source/`
(each download in its own folder) and run anything that reads them with `python -I`.

Then check the site before anything is built: lot size against the listing (county lines are approximate),
elevation range across the lot, distance and drop to any water, where a house could sit (slope, setbacks, inside
the lines) and which way it would face. If there's a view to sell, run the viewshed on the **real canopy** now —
the number decides whether "the view" is a concept at all.

## 3. Interview (AskUserQuestion, rounds of up to 4)

- **Purpose and audience**: spec demo to win the listing, or paid; the agent's brand or Capra-forward; where it plays.
- **Story**: which of the proven beats (open low over the water or the approach road; the lot line draws; Read the
  Land contours and elevation; the view painted; a concept home revealed; leaf-off/winter view; blue-hour hold)
  and anything new. Show 3–5 concepts with what each costs.
- **The home**: none (land only), a labelled concept home (which model; Kris makes his own in Meshy, or a
  licensed one; scale and footprint checked), or the client's plan.
- **Season and light**, **facts on screen** (only ones you can source: lot size with "boundaries approximate",
  elevation, distances, the view percentage with its method), **sound** (real field recordings; music later),
  **formats** (16:9 film, 9:16 cut, stills, unbranded MLS cut, Capra sizzle).
Stop when answers stop changing the plan.

## 4. Treatment (confirm before building)

Beats with times and camera moves, facts and their sources, deliverables and names, the render budget (720p
drafts ~30 min; 4K finals ~5–8 h with the Blender batch frozen), and what's new versus Petit Ridge. Get a yes.

## 5. Build at 720p, review, final

Follow `references/pipeline.md`. Clone the scripts and the project (APFS `cp -c -R`), change the site constants,
build in stages, look at check stills yourself (crop and zoom; compare against the previous version), trace the
camera against the **placed** trees offline, render 720p, mix, send. Iterate on Kris's notes at 720p only; keep
`VERSIONS.md` with his words. **4K only after he says so.**

## 6. Deliver

Full-quality files to iCloud `Capra Studios/Videos/` (SendUserFile only takes ~15 MB: send the review cut).
Name files `<NN>_<Parcel>_<cut>_<length>_<aspect>_<version>.mp4`. Credit lines go on the end card (USGS 3DEP,
USDA NAIP, OpenStreetMap contributors, Copernicus Sentinel-2 if used, any CC BY model).

## 7. Close out: improve this skill (every run)

Write lessons the moment they happen. At the end: Kris's notes word for word, failures with causes and fixes,
timings, prices quoted → `references/` here (product, pipeline, data, a new `<parcel>.md` like petit-ridge.md)
and the Unreal-side lessons → kb-unreal's references. Then install (`./install.sh capra-realtorfilm kb-unreal`
from the SkillZ repo), commit on a branch, open a SkillZ PR, and tell Kris in two lines what the skill learned.

## Hard rules

- Never put a number on screen you can't source. View percentages come from the real lidar canopy, not bare
  earth and not an assumed tree height (Petit Ridge: 82 % bare earth, 32 % assumed, 20 % real).
- A concept home is labelled "Concept home · artist's rendering / Not an existing structure"; lot lines say
  "Boundaries approximate (county GIS, not a survey)".
- No neighbouring houses invented or shown; their lots get trees, not bald patches.
- Spec pieces: no price, no call to action, no agent branding; get the listing firm's written OK before posting
  anything that names the address publicly.
- Ask before every download and every 4K or multi-hour render; never two renders at once; freeze the TrailGoat
  Blender batch while Unreal renders (pr_render.sh does it).
- Report what you couldn't verify (motion seen only as stills, a mix judged by levels and spectrum).

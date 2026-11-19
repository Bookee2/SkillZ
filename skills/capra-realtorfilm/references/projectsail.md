# Reference production: Project Sail data center campus, Sargent, Coweta County GA (data-center mode)

Capra-forward pitch piece, 2026-11-18 → 19. Lot folder `KB SS/Capra Studios/Unreal/Lots/ProjectSail/`
(`TREATMENT.md`, `VERSIONS.md` with Kris's words verbatim, `Data/lot.json` mode "datacenter"). Code: the shared
landfilm pipeline plus its `dc_*.py` scripts (`pipeline.md`, "Data-center mode"). Outputs:
`Caprastudios/output/unreal/lots/ProjectSail/08_ProjectSail_film_130s_16x9_v<N>`, masters in iCloud
`Capra Studios/Videos/Data center films/`.

## Why this film exists
Kris wanted "the ultimate /capra-realtorfilm": a real proposed data center shown as it is today, then cleared, graded
and built out, measured to scale, for data center developers and county commissions (hearing exhibits). Four GA
candidates came from Georgia DCA DRI filings (`data.md`); Kris picked **Project Sail**: about 830 acres, 9 buildings,
4.34M sq ft, 7 two-story at 60 ft and 2 at 40 ft, 910 MW. Prologis is the developer (Atlas Development LLC filed it).
DRI #4361, REZONE 24-019, rezoned 3-2 in April 2026, then sued on 2026-05-05. The Plant Yates 230/115 kV corridor
crosses the site; Wahoo Creek runs through it.

## Interview answers (what changes the plan for this kind of film)
Capra-forward pitch piece (not listed anywhere); all four concepts (The Plan Measured, From the Road, Ten Years in
Ninety Seconds, Night and Light); about 2 min plus a 45 s cut; summer for the build, leaf-off for the road views,
then night (v1; v2 dropped both); stage names plus "2036 (DRI #4361)", no invented years; facts: land and buildings,
power, water (the newest sourced figure), Capra's own measurements; realistic buildings labelled illustrative;
films first, a web model later; real field recordings.

## Honesty rules for a proposed project (on top of `product.md`)
- The layout is Capra's illustration, not the applicant's plan: every card that shows it says "Illustrative layout ·
  not the applicant's plan". Swap in the real plan if the county releases one.
- Sizes follow the published program; equipment counts are a plausible fit (~100 MW a hall), never "the design".
- Road views are measured, not claimed: the worst case is the bare-earth or evergreen-only number, and no screening
  trees go in unless they are a condition of approval. No noise numbers.
- Distances to landmarks are straight lines from the site centre, measured to a named point (the courthouse, the
  plant's fence); v1's "Newnan 6 mi" was a guess and wrong (6.7 mi).

## The layout and what it measured (layout v1, "Approved")
- 9 halls of 1,000 × 271 ft (16 equal floor plates = 4.34M sq ft; H1–H7 60 ft, H8–H9 40 ft), campus axis 175°;
  substation on the Yates corridor (one 230 kV + three 115 kV lines, bearing 153°); drives from the north access strip
  on Wagers Mill Rd, Welcome To Sargent Rd and west Wagers Mill Rd; 9 ponds; admin + 230 spaces.
- Constraints: 300 ft building setback (local paper), 100 ft site buffer (DRI), 300 ft from homes, FEMA A/AE,
  wetlands, 30 m stream buffers, 40 m from each line.
- Earth moved ≈ 1.98M yd³ (cut 1.14M, fill 0.84M); disturbed 204 ac (24.5 % of 831); forest cleared 145 of 521 ac;
  max cut 10.3 m, max fill 9.8 m; roofs 56 ac.
- Road study (1,256 road points within a mile, 1,134 roof points): bare earth 75 % see a roof; the 2020 canopy kept as
  solid outside the cleared footprint 0.5 % (only looking down the two drive entrances); winter worst case (only the
  lidar's 19,637 evergreen crowns block) 19.7 %. Prologis's site says the buildings "sit well below the crest of the
  hill" from Wagers Mill Road: the trees screen it, not the hill.

## The film (v2/v3, 130 s)
| s | Beat |
|---|---|
| 0–9 | low over the Wahoo Creek woods toward the site (title) |
| 9–27 | crane up and back; the property line draws on the canopy (13–20.5 s); acreage, Read the Land |
| 27–52 | down into the orbit: Clearing (32 s), Grading (42 s) |
| 52–76 | the build: substation and admin first, then the halls rise in phase order |
| 76–88.5 | To scale: along the north hall's generator yard with dimension pins |
| 88.5–98.5 | camera B, From the Road: eye level (1.7 m, 50 mm) at the east drive on Welcome To Sargent Rd; today → built |
| 98.5–106 | B rises straight up out of the trees; the line returns; road study and water cards |
| 106–126 | the zoom-out to ~30 km, north up, over NAIP + Sentinel-2; landmark pins: Chattahoochee 1.9 mi, Plant Yates 1.5 mi, Newnan 6.7 mi, I-85 8.4 mi, Wansley / Chattahoochee Energy 8.6–8.9 mi, Power plants · 8 mi (Hawk Road · Tenaska); edge arrows to Hartsfield-Jackson 30 mi and Atlanta 36 mi |
| 126–130 | end card |

## Versions and Kris's notes (verbatim; details in VERSIONS.md)
- Layout v1 → "Approved". Blender kit v1 → "Ultimately this film needs to be in unreal engine", and on the kit's look
  "I think it looks good" (kept as is in Unreal).
- **v1** (122 s, 2026-11-18 17:20) → "We don't need the drop the leaves part, it's fine with full foliage." / "It would
  be nice to outline the full shape of the property like we did on the pine forrest tract." / "We don't need it to
  go to night time, we can keep it daytime, and at the end of the film zoom out so we can see the nearest city or
  surrounding landmarks to show how close it is to things. Can we pull in real map tiles for that last part?"
  Picks: "Public imagery (Recommended)"; landmarks "Plant Yates + river, Newnan + I-85, Power plants to the west,
  Atlanta + airport".
- **v2** (130 s, 22:31): no leaf-off, no night, the outline on the canopy, the regional zoom-out with pins.
  → "The video looks good, but the fonts are too small to read on the phone, especially when we zoom out and show
  the surrounding area."
- **v3** (2026-11-19, post only, ~3 min): post_film.py "type": "phone" (bigger type, dark plates, pins that place
  themselves, `--lint`) → "Reads well".
- Open after v3: 4K final (on his OK), the 45 s cut, construction sound (the library has none; a download on his OK),
  the web model.

## Failures, causes, fixes
- make_kit centred the hero on the outline's vertex mean: a merged 5-parcel outline sat 141 m off → the box centre.
- Overpass at capacity for power lines → HIFLD transmission lines (`data.md`). Coweta building footprints page at 1,000.
- Greedy pads with an 18 m gap fitted only 8 halls; the pads already carry their aisles → gap 2 m fits 9.
- The editor's stale `lot` module (loaded before dc_plan.py wrote "camera") broke pr_film → pr_common reloads it.
- v1's ground-level lot line never showed under a 25 m canopy → dc_outline.py rides it 1.5 m over the kept canopy.
- A whole-frame smear at f_1248: the camera's yaw flipped +180/−180 looking due west → pr_film unwraps yaw.
- The zoom-out flew into the cloud layer and the atmosphere washed the map pale blue → clouds off from 106.5 s,
  aerial perspective ×0.2 and fog ×0.08 keyed over 106–117 s.
- The 8 km block of lidar trees read as a bright speckled square against the region photo (Nanite ignores ISM cull
  distance) → forest hidden from 113 s; a 64-frame trees pass crossfaded out in post over 113–115.5 s.
- A maroon strip past the hero's east edge: the far ring sampled the hero-UV works mask over its own 8 km UV →
  the far ring gets an empty mask.
- The road view darker than v1: manual EV100 is lower = brighter (−0.4 → −1.3).
- v2's type was sized for a monitor: ~6 pt pin titles on a phone held upright, grey subs lost over bright towns
  → v3's phone type; the first auto-placement (greedy, no side places) put Plant Yates under its dot with its lead
  across the site outline, so it read as the site's own name → side placements, four passes, leads count as overlap.

## Timings (M5 Pro)
| Step | Time |
|---|---|
| Blender kit, scene, check stills (EEVEE 720p) | ~1 s a still |
| Editor build (scene, forest 398k + 12.7k cleared, 17 graded tiles, kit, campus, film) | 8 min |
| 720p v1, 2,929 frames | 34.5 min (0.7 s/frame) |
| 720p v2, 3,121 frames + 64-frame trees pass | 30.4 min (0.58 s/frame) + 95 s |
| Post + dc_mix + review encode (130 s) | ~3 min |
| Region imagery (42 NAIP overviews + 4 Sentinel-2 tiles, windowed reads) | 272 MB in all |

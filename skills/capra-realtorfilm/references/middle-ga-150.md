# Middle GA 150: the first paid film (a fund's anonymous timber tract, 2026-11-19)

Capra's first paying client came from the Buckeye Road film. John at Southview Timberland Investments asked for a
film of a tract held by the Southview Timberland Fund, to post on LinkedIn. Read this before any **client film**
(their disclosures, their brand, their wording) or any **anonymous** tract (no place may be identifiable).

## The client's brief and what it changes
- **Name everywhere:** the property is "Middle GA 150" in the video and every file name. The client gave the title
  card's wording, and "Middle Georgia" is the only place reference.
- **Anonymous:** no road names, highway numbers or shields, towns, counties or county lines, and no base-map labels.
  - No landmarks: the church whose lot is notched into the frontage, buildings, distinctive neighbouring parcels.
  - No coordinates and no north arrow.
  - Location data stripped from the files.
  - The camera stays tight, and the surroundings are generalized so they can't be matched to satellite imagery.
  - The parcel ID is for reference only.
- **Securities wording:**
  - Before the film: a 6 s disclosure card (John asked for ~4 s, but 34 words can't be read in 4 s; Kris chose 6)
    and an intro card.
  - After the end card: a long closing disclosure, held 20 s.
  - The client's text goes on screen word for word.
  - No price, valuation or return figures.
  - Capra doesn't review securities compliance. Suggest the fund's counsel approves the cut: inviting accredited
    investors in a public post may count as general solicitation, depending on how the offering is set up.
- **Highlights:** mature merchantable timber (the heart), road access (unnamed), recreation and hunting, room to
  divide.
- **Brand files:** the client's brand guide, fonts and logotype were attached but never arrived. iCloud Mail rejects
  messages over 20 MB, so ask for a share link. Build with Capra ink and Red Hat until they come: lot.json
  client.brand takes bg, accent, text, font_display, font_text and logo, and post re-renders nothing.
- **Kris's picks:** the generalized ring, 16:9 plus a 4:5 LinkedIn cut, a small "Film: Capra Studios" credit,
  ~95 s.
  - On the division, Kris first said not to divide the land "unless John tells us to". John's email asked for it;
    shown that line, Kris chose "Draw a concept division". He then sent the survey plat (two tracts of 75.00 ac),
    which replaced the 3-tract concept before the first render.

## Finding the tract
- **Parcel lines:** qPublic (Schneider) answers automated reads with 403. Pulaski County GA's lines came from the
  Middle Georgia Regional Commission's ArcGIS Online layer:
  - services1.arcgis.com/Ug5xGQbHsD8zuZzM, Hawkinsville_Pulaski_Zoning_Classifications, field PAR_ID with no spaces.
  - The same org has parcels for Crawford, Houston, Monroe, Peach, Twiggs and others.
  - A public Experience app's item data names its web maps, and the web map names its layers.
- **Same-name trap:** pulaski.integritygis.com is Pulaski County, **Missouri**. Same-name counties again (Laurens GA
  and SC): check the state.
- **Photo history:** NAIP previews of every year (Planetary Computer `item/crop/{bbox}.png`, ~1 MB each) give the
  tract's history before downloading anything.
  - Here: closed forest 2010-2025, apart from a north-west block cut between Jul 2015 and Sep 2017.
  - Bright-patch test: in each year's photo, the biggest patch inside the mature stands brighter than 1.6x their
    median. It found no clearing over 0.2 ac, so "no clearcut in USDA aerial photos since 2010" is sourced.

## Data lessons
- **The lidar's year is not its name.** GA_SW_Georgia_B4_2017 was flown 2021-01-19..30 (GPS time in the points). Put
  the flight date on screen, never the project year.
- **Pick the survey by points, not by year.** `ept_fetch.py --find` used to keep the newest year. A 2018 statewide
  block whose bounding box overlapped (19k points) beat the 2017 block that covers the tract (29 M). It now keeps the
  newest project with at least 1 point/m² over the box. `ept_lonlat_box` limits the fetch to the tract + 400 m:
  624 nodes, 160 MB.
- **NAIP "year" is the season, not the flight date.** The Jan 2022 leaf-off flight is `naip:year` 2021.
  `naip_fetch.py --year 2021 --lot-pad 200` fetches it into `source/naip_2021/`.
  - `--ring-res 4.8` makes the far ring 9 MB when it'll be generalized anyway.
- **Pine vs hardwood from a winter photo.** Bare hardwood crowns are grey, pine crowns green. Visible greenness
  (2g-r-b)/(r+g+b) over 0.08, checked by eye on a zoom, marks evergreen crowns.
  - Winter NDVI doesn't work: Otsu split the unimodal histogram at the mode and called 62 % evergreen. The real
    figure is 12.6 %.
  - Stands at 41 m: pine & hardwood 20-50 % evergreen, pine over 50 %.
  - lot.json timber.leafoff and timber.class_names drive it; `timber_stands.py` writes evergreen_1m.npy for
    `timber_points.py`.
- **Edge rings and grass-as-water.** A 25 m *mean* stand height rings every opening with "young" (timber.young_by_median
  fixes it). A grass lane, green in January, read as 2.2 ac of water by NDWI. With a leaf-off photo, water that doesn't
  touch the kit's water and is green in winter is open ground.
- **Overpass was down again** (two days running). `osm_fetch.py --api` (and the automatic fallback) reads the OSM API's
  map call and rebuilds Overpass-style ways.
- **Acres on screen must agree.** Stands by GIS lines summed to 154 ac against the client's 150, so the stands show as
  shares (75 % hardwood, 17 % pine & hardwood, 5 % young pine, 3 % openings and lanes). Tracts use the survey's 75.00.
  - Frontage: the GIS lines gave ~3,200 ft. The plat's legible road courses add to over 2,400 ft (the south curve is
    hidden on the copy), so the card says "Over 2,400 ft · per the survey".

## Anonymous mode (lot.json "anonymous": true; `anon_ring.py`)
- **What stays real and what's made up:** the tract stays real (its lidar ground, trees and 30 cm photo). Everything
  outside it is made up.
- **Terrain:** blended 30-110 m outside the line into the real ground smoothed at 50 m, plus a gentle swell; the wide
  ground at 120 m and the horizon at 300 m.
- **Water and roads:** no water anywhere. Only the frontage road class is kept, with its names stripped.
- **Cover:** a made-up forest with noise clearings, none within 250 m of the line, and a 12 m grass verge along the road.
- **Trees:** placed in that cover, at the tract's own density (6 m apart near the line, 8.5 m beyond) and its height
  and pine mix.
- **Ground photos:** `anon_ring.py textures` writes every file `naip_textures.py` would. Inside the line it uses the
  real photo with a 4 m feather; outside, canopy mottle and grass in the tract's own photo colours.
- **The real files are kept** as `*_real`, osm_hero_real.json and lot.json water_real.
- **What a determined searcher could still match:** the tract's own outline, its notch and its interior lanes are real.
  Say so to the client: the surroundings can be made unmatchable, the property itself can't without misrepresenting it.
- **Past the 8 km ring there is no ground.** The sky atmosphere's planet surface reads as a flat blue sea under haze.
  - lot.json look.ground_albedo (34, 44, 30) and fog_density 0.0034 soften it but don't remove it.
  - Keep high shots looking ~22-25° down, so the frame's top stays below the ring's far edge
    (atan(altitude / distance to the edge)).
- **Metadata:** an anonymous lot's files carry none. post_film encodes with -map_metadata -1 and bitexact, and
  post_lot.sh re-muxes every output the same way.

## Client films (lot.json "client": {pre, post, brand}; post only, nothing re-renders)
- **Timeline:** `film_s` (69) is what Unreal renders, `end_s` (95) is the whole timeline, and `cut_s` stays the film's
  camera cut. `film_path.END_S` uses film_s, which first rendered the sequence 95 s long, 25 s too many.
- **Cards and panels:**
  - pre and post are full-frame panels in the brand's background. The pre fades in from ink, and the film opens from
    ink. The post crossfades from the end card and carries the data credits.
  - Card kinds: 'intro' is a paragraph over the shaded picture; 'client_end' is the client's name or logo, their
    line and their contacts, with no Capra lockup.
- **Sound:** `mix_film_v2.py --film 69 --pre 6 --post 20`. The treeline rises under the disclosure and settles and
  fades under the closing one.
- **4:5 cut:** `post_lot.sh <Slug> NN vN 720 4x5`.
  - It crops about the centre, projects pins through the full 16:9 frame, and sets type at 0.64 of the 16:9 size.
  - It reuses the 16:9 mix.
  - At 720p the crop is 576x720; a 4K master crops to a full 1080x1350.
- **Per-lot beats live in `landfilm/plans/<Slug>.py`**, which timber_plan.py runs with its helpers; Buckeye's beats
  are the default. The lint caught pins behind the camera and a label covering a tract pin. Aiming a high orbit
  *further away* pushes the near tract off the bottom of the frame; aim nearer to lift it.
- **Divisions:** split.layout "equal" gives n equal tracts square to a bearing, each on the road. "lines" gives
  surveyed cuts from a parcel vertex, a road course and a bearing; the plat's 2,039.22 ft line came out at 1,997 ft
  on the GIS lines.

## Build gotchas
- **Primary roads:** site_meshes.py drew only residential, tertiary, secondary and unclassified roads. Primary and
  trunk now get 7.4 m ribbons.
- **Open ground was autumn tan.** The ground material turns open ground olive-tan, Petit Ridge's fall, which made a
  green food plot read as mud. lot.json look.open_keep sets how much of the photo's green stays (0.3 was the
  default; 0.85 here).
- **Real lanes on screen:** woods lanes in the tract read as grey ribbons through the canopy from the air. They're
  real (no trees in the lidar there).
- **Editor check (`editor.sh`):** it matched `pgrep -f "$S.uproject"` against a watch loop's own command line, so it
  said "editor already running" and never launched one. It and lot_editor.sh's pkill now match
  `MacOS/UnrealEditor .*$S[.]uproject`.

## Numbers
- **Data:** 525 MB (DEM 201, lidar 160, NAIP 164).
- **Forest:** 596k trees: 19.5k real on the tract, about 250k made up in the hero and 344k in the ring.
- **Editor build:** about 18 min (terrain placement 15).
- **Renders:** check stills, 35 frames, ~110 s. The 720p film, 1,657 frames, 4 samples: ~36 min (1.3 s/frame;
  596k trees and the made-up ring).
- **Post:** 16:9 with the mix, ~5 min; 4:5 reusing the mix, under a minute. Masters 71 MB (16:9) and 35 MB (4:5);
  review copies ~11 MB each; −18.3 LUFS integrated.
- **The mix hung once:** the new disclosure bed read the treeline recording from 200 s, past its end, and `bed()` looped
  forever on an empty slice. It now starts at a stretch the file has, and `bed()` asserts there's material to loop.

## Versions
- **v1 (2026-11-19):** 95 s, 16:9 and 4:5 at 720p, delivered to iCloud Capra Studios/Videos/Middle GA 150. It has
  the surveyed two-tract split (Kris sent the plat mid-build: "Here's the survey for the actual lot division for next
  run"; it went into v1 because the render hadn't started) and placeholder brand cards until John's files arrive.
- **v2:** John's brand.
  - lot.json client.brand: bg, accent, text, font_display, font_text, font_small, font_map (Capra faces swapped for the
    client's in every card and pin), logo, logo_w and logo_w_45.
  - Fonts: PT Serif is on macOS (PTSerif.ttc#3 is Bold). Source Sans 3 came from Adobe's GitHub (OFL), downloaded on
    Kris's yes.
  - The opening disclosure went back to John's 4 s. Kris: "Its a warning not neccessary reading, so it's just there for
    legal protection".
- **v3:** the plat's entrances and rear access as pins.
  - The end card holds 2 s (client.post.hold_s). It must run past the film's end, or the held frame has it faded out.
  - lot.json "crop45" slides the 4:5 crop so pins near the edge stay in frame.
  - lot.json "deliver" makes post_lot.sh copy every master to the client's folders (Proton Drive Client work/<client>
    and iCloud).
- **v4:** the full logo lockup. The zip's logo files were the wordmark only; the lockup lives as 500 px images inside
  the brand PDF (`pdfimages`, each image joined to its transparency mask). Ask the client for a vector lockup before 4K.
- **v5:** John's notes, sent as a Loom.
  - **Reading the Loom:** its Transcript tab needs a sign-in. The captions came from Loom's GraphQL FetchVideoTranscript
    (captions_source_url), fetched inside the page; seeking the page's video element gave the frames he points at.
  - **Camera:** "really zooms in very closely"; "a little bit higher... more like looking down on it". The low runs
    went from 36-60 m to 190-230 m over the canopy, with the property line kept in frame (at 140 m the timber shots
    showed nothing but trees). The road at 150 m, the stand map faded in only after the climb.
  - **Cards:** fewer words. Title-only cards and pins are supported (an empty sub-line).
  - **What the client cut:** "Boundaries approximate", the photo-history line, and the "Suggested" access caveats.
    The client owns the property and the closing disclosure covers graphics.

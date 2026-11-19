# The product: who buys it, what it costs, what it must say

## Market (researched 2026-10-28)
- Drone lot videos sell for **$175–500** (+ ~$10 for drawn lot lines); 3D aerial renders **$600–2,500 a view**;
  only CGI studios (e.g. ArchiCGI) do land flyovers, and none from real lidar with real trees.
- What Capra sells that a drone can't: the lot line drawn on the real ground, Read the Land (contours, elevation,
  slope, aspect), an honest view study from where a house would sit, a labelled concept home, winter (leaf-off)
  views in any season, and a cut for every channel. Raw land and new-construction lots are the fit.
- First client in mind for Petit Ridge: Big Canoe Brokerage (lists 37 Petit Ridge Dr on FMLS, $120k). Ask Kris
  before contacting anyone.

## Compliance (non-negotiable on screen)
- **Concept home** label for any house that isn't there: "Concept home · artist's rendering" / "Not an existing
  structure".
- **Boundaries**: "Boundaries approximate (county GIS, not a survey)" wherever the lot line or acreage shows.
  County lines and listings disagree (Petit Ridge: 5.4 acres from the county lines, 4.9 in the listing): quote the
  listing and say so.
- **Facts** come with a source: elevation from the lidar, distances measured on the DEM, view percentages from the
  real-canopy viewshed with its method on the card ("lidar line-of-sight study"), and the clearing it assumes.
- **MLS cut**: unbranded (`post_film.py --unbranded`), no agent or brokerage branding, no contact details.
- **Spec pieces**: no price, no call to action; the listing firm's written OK before anything naming the address
  goes public.
- Credits on the end card: USGS 3DEP lidar, USDA NAIP, © OpenStreetMap contributors, Copernicus Sentinel-2 (if
  used), and any CC BY model by name.

## Data-center films (a second line, 2026-11-18)
- Who: data center developers (site selection, community meetings) and the county commissions and planning
  boards that hear them; the film is an exhibit, so every number has a source and a date. No prices quoted yet.
- What it shows that a rendering can't: the campus on the real land and trees, the earth moved and forest cleared
  from a measured grading, the view from the public road as a percentage of road points, and how far it sits
  from the towns and plants round it, over real imagery.
- On screen: "Illustrative layout · not the applicant's plan" until there is a plan; the filing (DRI number and
  date) for the program; worst-case road views; no screening that isn't a condition of approval; no noise figures.
- First film: Project Sail (`projectsail.md`), a Capra-forward pitch piece, 130 s; a 45 s cut planned.

## Deliverables (the Petit Ridge set)
- Film: ~80 s, 16:9, 24 fps (`01_<Parcel>_film_80s_16x9_<version>.mp4`), also `_silent` and an unbranded MLS cut.
- Vertical: 20–30 s 9:16 (a 4K master crops to a full 1080×1920; a 720p one doesn't).
- 6 stills (4K frames are 8 MP).
- 15 s Capra sizzle (Capra-forward, for the studio's own channels).
- Drafts at 720p until Kris signs off; finals 4K, 8 temporal samples; a 1080p preview of the 4K.
- Big files to iCloud `Capra Studios/Videos/` (never `TrailGoat Videos`).

## Sound
Real field recordings of the right habitat and season (Sonniss GDC bundles; library in `KB SS/Capra Studios/
Sound/library/` with a README of sources and licences), a few long beds that follow the camera, high-passed at
~100 Hz, −20 LUFS for review; stems for Kris's music. No sample-project ambience, drones or designed hits
(Kris on v1: "the sounds are terrible").

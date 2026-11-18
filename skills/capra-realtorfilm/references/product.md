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
MLS and disclosure rules, researched 2026-11-17 (`Caprastudios/research_notes/Capra rebrand 2026-11/
real_estate_film_market.md`, section 4) and checked against the rule texts the same day. **[read]** = the rule
text itself was read; **[notes]** = taken from the research notes, not re-checked; **[judgment]** = Capra's
reading, not a rule. Not legal advice. These rules bind the listing broker, not Capra: the job is to hand over
media the broker can submit without a fine, and to say where a rule is unsettled.

### On every film
- **Concept home** label for any house that isn't there: "Concept home · artist's rendering" / "Not an existing
  structure".
- **Boundaries**: "Boundaries approximate (county GIS, not a survey)" wherever the lot line or acreage shows.
  County lines and listings disagree (Petit Ridge: 5.4 acres from the county lines, 4.9 in the listing): quote the
  listing and say so.
- **Facts** come with a source: elevation from the lidar, distances measured on the DEM, view percentages from the
  real-canopy viewshed with its method on the card ("lidar line-of-sight study"), and the clearing it assumes.
- **Spec pieces**: no price, no call to action, no agent or firm branding; the listing firm's written OK before
  anything naming the address goes public.
- Credits on the end card: USGS 3DEP lidar, USDA NAIP, © OpenStreetMap contributors, Copernicus Sentinel-2 (if
  used), and any CC BY model by name.

### MLS: export per MLS (there is no single "MLS cut")
FMLS, Georgia MLS and Canopy MLS ask for opposite things, so one cut cannot satisfy all three. Ask which MLS the
listing is on and export for that one.

| | FMLS (Atlanta) | Georgia MLS | Canopy MLS (Charlotte, western NC) |
|---|---|---|---|
| Rule text | Rules and Regulations effective 2025-03-17 [read] | Photo policy of 2020-09-09 [read]; the rules of 2024-08-01 add little on media [notes] | Section 1.18.1 article, updated 2026-02-27 [read]; branding notice of 2024-08-21 [read] |
| Text on a still | None: "No text may be superimposed on photos" (10.6(a)(1)) | No frames, watermarks, time stamps, logos or overlaid images | The disclosure label must be on the image; other overlaid text can be rejected |
| Where the disclosure goes | Public remarks (20.1(e)(i)) | Public remarks, plus a current-state image immediately before or after | On the image or within the tour; remarks or captions alone are "NOT acceptable"; an unaltered image immediately before or after, or "easily accessible alongside the virtual tour" |
| Film as a tour | Three URL fields: two unbranded, the third may be branded. 10.6(a)(4) allows "descriptive text of the property's attributes" and bans text "superimposed on any virtual tour": open which one covers our labels | Nothing found beyond the photo policy | May be branded since 2024-08-21 (one field, "Virtual Tour URL Branded"); the disclosure must be in the tour |
| Names, logos, contact details | None in photos, remarks or the unbranded tour fields; links and URLs count (10.6) | None in images | None in photos, captions or remarks (1.7); the tour may carry the firm's brand |
| Land listings | Land/Lot is exempt from the 72-hour photo rule (20.1(d)); a graphical representation of the specific property may stand in for a photo (10.6(c)) | Renderings and plat maps are accepted for listings under construction | A plat or map of the specific property is accepted as the photo |

FMLS fines run from $50 a business day up to $500 a day, and any violation can cost up to $15,000 (20.1(b), (g)).

**What goes in each export**
- **FMLS**: stills with no text at all, land only (a concept home cannot carry its label there, so it stays out
  of FMLS stills [judgment]); the unaltered reference as a photo; the public-remarks wording below. Keep the film
  out of the tour fields until FMLS answers the label question. Do not strip its labels to make it fit.
- **Georgia MLS**: the same text-free stills, with no logo, frame or watermark, each one next to the unaltered
  reference; the public-remarks wording. Submitted media becomes Georgia MLS's property, so the client licence
  has to allow that.
- **Canopy MLS**: stills with one label burned in ("3D rendering", plus the concept-home label where a home
  shows) and no other text; the unaltered reference next to them. The film can go in as a branded tour if it
  names the firm (Branded cuts, below) and says on screen that it is a rendering. It has no such card today; the
  wording is Kris's to approve.
- **What the pipeline makes today**: `post_film.py --unbranded` drops only the Capra lockup and service line.
  The cards stay, and so does the credits line, which names Capra Studios by default. That is not an FMLS or
  Georgia MLS export. Text-free stills are the render's own frames (cards are composited in post). None of the
  three exports is built yet: assemble them by hand and say so in the delivery note.

**Unaltered reference (every job)**: the film is built from data, so there is no camera original. The reference
is the NAIP aerial of the parcel as downloaded (capture year stated, nothing drawn on, nothing removed), plus a
no-home frame from the reveal pass when a concept home is shown. Host it on a link, with a QR code for print,
and give the link wherever the film plays and in the delivery note. On an MLS it also goes in as a photo next to
the rendered stills: Georgia MLS and Canopy require the pairing, and FMLS 10.6 counts links and URLs in photos,
remarks and tours as self-promotion, so there the safe route is a photo. Whether an aerial counts as the
"original" of a rendering is untested with all three [judgment]. Where the link is hosted is not decided.

**Public-remarks wording** (draft, not reviewed by any MLS; the agent fills in the photo numbers):
- Land only: "Photos [n] to [n] and the video are computer-generated 3D renderings (virtually staged), built
  from public lidar and aerial imagery. They are not photographs. Lot lines shown are approximate (county GIS,
  not a survey). Photo [n] is the unaltered aerial."
- With a concept home, add: "The home shown is a concept only. It is not built and is not part of the sale."
- "Virtually staged" is there on purpose: FMLS and Georgia MLS both say staged images "must be designated as
  such in the public remarks". No Capra name, link or URL in remarks.

### Neighbouring structures: open conflict for MLS media (Kris decides)
- **What the film does now**: neighbouring houses are neither invented nor shown. The pipeline takes them out of
  the NAIP ground photo and plants trees on their lots (`data.md`, "Neighbours' houses").
- **What the rules say**: FMLS 20.1(e)(iii): staged images "cannot remove elements outside the property owner's
  control, such as buildings on adjacent properties, power lines, utility poles, water towers, retaining walls,
  and highways" [read]. The Georgia MLS photo policy says the same of virtually staged images [read]. Canopy
  1.18.1 bars changing photos, renderings or virtual tours "to remove or conceal visual elements not within a
  property owner's control" [read].
- **What is unsettled**: the FMLS and Georgia MLS rules are written for staged photos, and neither says whether
  a film rendered from data, which never was a photo, is one. FMLS 3.3 separately bars photos altered "in any
  way that might misrepresent the property". Canopy's wording names renderings and tours outright. The same
  lists cover power lines, poles and highways: the film draws roads from OpenStreetMap, and nothing in the
  pipeline handles power lines or poles either way.
- **Options** (not chosen):
  1. Show neighbouring structures as plain massing from the lidar: real footprint and height, no invented
     detail. Pipeline work, not built, and it changes the look approved on Petit Ridge.
  2. Keep the film off the MLS (agent's site, YouTube, social) and give the MLS unaltered stills only. The MLS
     rule then does not reach the film; the agent's duty not to mislead still does (NAR Code of Ethics,
     Articles 2 and 12 [notes]).
- **Until Kris decides**: when media is going to an MLS and a neighbouring structure, power line or highway
  would fall in frame, raise it in the treatment. Do not settle it silently either way.

### Questions for FMLS compliance (before any film or still goes on an FMLS listing)
1. Our media is a film and stills rendered in 3D from public lidar and aerial imagery, with no camera footage.
   Buildings on adjacent lots are not modelled; their lots show as tree cover. Does Rule 20.1(e)(iii), or Rule
   3.3, treat that as removing elements outside the owner's control? Would plain massing blocks at the real
   footprint and height satisfy it?
2. The film carries labels: acreage, elevation, "boundaries approximate", "concept home, not an existing
   structure". Under Rule 10.6(a)(4), are they "descriptive text of the property's attributes", or text
   "superimposed on any virtual tour"? Is the answer different for the third (branded) tour field?
3. Are the Rules and Regulations effective 2025-03-17 still the current text? (FMLS's rules page would not load
   on 2026-11-17, so a later revision is not ruled out.)

### Branded cuts name the listing firm
A branded cut is the broker's advertising, and both states require the firm's name in it.
- **Georgia Rule 520-1-.09** [read on Cornell LII, whose history for the rule ends in 2014: check the
  Commission's current text]: "videos" are among the media covered ((1)(b)); the advertisement must include the
  firm's name as registered with the Commission and a telephone number for the firm ((7)(a)); the firm's name
  must be at least as large, prominent and frequent as the agent's or team's ((7)(b)).
- **North Carolina 21 NCAC 58A .0105(a)(1)** [read; last amended 2021-07-01]: no advertising "without including
  in the advertisement the name of the firm or sole proprietorship with which the broker is affiliated", and
  none without the broker-in-charge's consent.
- So: at the interview, get the firm's name exactly as registered (in Georgia, the firm's phone number too) and
  put it on the branded cut's end card at least as large as the agent's. An agent-only card is not enough.
- Spec pieces stay unbranded: no agent, no firm, no price, no call to action.
- FMLS and Georgia MLS exports stay unbranded whatever the cut. A branded Canopy tour must name the firm.

### Digital-alteration laws (none found in Georgia or North Carolina)
- **California AB 723** (Bus. & Prof. Code 10140.8, in force 2026-01-01) [notes: read through Inman; the statute
  page returned a 403 again on 2026-11-17]: disclose digitally altered listing images and give access to the
  unaltered original by link, URL or QR code.
- **Wisconsin 2025 Act 69**, s. 452.136(1m), in force 2027-01-01 [read]: licensees disclose advertising altered
  with technology, AI included, where the change "creates a false or misleading impression of the property".
- The unaltered reference on a link is the remedy both ask for, which is one reason it ships with every job.

### Still open
- **Neighbouring structures**: which option (above). Kris's call, after FMLS answers.
- **FMLS**: whether labels on a rendered tour are allowed, and whether the 2025-03-17 text is current.
- **Georgia MLS**: whether the photo policy of 2020-09-09 is still the current text (a vendor post of 2026-05-14
  repeats it [notes]; nothing newer from Georgia MLS turned up), and whether it treats a rendered film as a
  staged image. Ask Georgia MLS.
- **Firm name in a video**: neither state says whether it must be on screen or may sit in the caption. On
  screen is the working default [judgment].
- **Unaltered reference**: where the link is hosted.
- **Labels the research proposes, not adopted** (on-screen wording is Kris's to approve): a slate at the start
  and end saying the film is a 3D rendering from named public data with capture years; "simulated" on the
  leaf-off view; "Drone-style movement is simulated. No drone footage was captured." (HousingWire [notes]).

### Sources (checked 2026-11-17)
- FMLS rules: https://firstmls.com/wp-content/uploads/2025/03/RR2.0_3_18_25-2.pdf · tour fields:
  https://firstmls.com/?p=6488
- Georgia MLS photo policy: https://georgiamls.wordpress.com/2020/09/09/georgia-mls-updated-photo-policy/
- Canopy 1.18.1: https://support.canopymls.com/kb/article/104-digital-images-virtual-staging-and-unauthorized-use-of-listing-content
  · branding notice: https://support.canopymls.com/kb/article/809-08-21-2024-canopy-mls-has-removed-the-prohibition-against-branding-in-virtual-tours/
- Georgia 520-1-.09: https://www.law.cornell.edu/regulations/georgia/Ga-Comp-R-Regs-R-520-1-.09
- North Carolina 58A .0105: https://www.law.cornell.edu/regulations/north-carolina/21-N-C-Admin-Code-58A-0105
- Wisconsin Act 69: https://docs.legis.wisconsin.gov/2025/related/acts/69

## Deliverables (the Petit Ridge set)
- Film: ~80 s, 16:9, 24 fps (`01_<Parcel>_film_80s_16x9_<version>.mp4`), also `_silent` and the export for the
  listing's MLS (Compliance, above).
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

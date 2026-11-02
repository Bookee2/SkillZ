---
name: tg-films
description: Dress a rendered TrailGoat course flyover for YouTube and publish it — the race readout and corner mark, the 5 s TrailGoat Films ident (Unreal, with its sting), a licensed track mixed to -14 LUFS, a 15 s end card naming the next film, a thumbnail, aid-station chapters and the description — then upload through the TrailGoat uploader (or hand Kris the file to drag in) and place YouTube's end-screen elements in Studio. Use when a 1080p flyover master exists and the ask is to get it onto @trailgoatrun; /tg-render makes the masters, this skill ships them.
argument-hint: [film.json path, or a course name and the master's path]
---

# TG-films

Turn one rendered flyover into one published YouTube video. The render side (`/tg-render`) ends with a clean 1080p master and a `hud-frames.json`; this skill ends with a video live on the channel. One film per invocation, one command per step, nothing destructive: every output lands in the film's own folder on KB SS.

## Set up the machine

1. **TrailGoat checkout at main.** `hud.py` and the uploader live in the repo. Use `$TRAILGOAT_REPO` if set, else a worktree of `origin/main` (the main checkout at `~/Desktop/Projects/TrailGoat` is often behind and carries Kris's uncommitted work: never use it for this). The checkout needs `.venv` (symlink the main one) with `imageio-ffmpeg` and `Pillow`.
2. **The uploader.** `~/.config/trailgoat-youtube/` holds its venv, `client_secret.json` and `token.json`; `yt_upload.py whoami` must print `@trailgoatrun`. If the token is gone, Kris signs in again with `yt_upload.py auth`.
3. **kb-ytvideo.** The end card renders with its engine: `~/.claude/skills/kb-ytvideo`, the work folder `~/Movies/TrailGoat Launch/motion` (Playwright in `node_modules`) and its venv. `scripts/render_end_card.py` has the paths at the top with env overrides.
4. **Assets on KB SS.** `/Volumes/KB SS/TrailGoat-Studio/Films/assets/`: the intro `intro-trailgoat-films-1080p24.mp4`; `/Volumes/KB SS/TrailGoat-Studio/Music/audio-library/`: the licensed tracks and `LICENSES.md`. The intro is a slot, not a build step: any 1920×1080 24 fps clip with its own sound goes in `film.json`'s `intro`. The house intro is the TrailGoat Films ident "Headlamp" (signed off 2026-10-26): 5.0 s, a headlamp clicks on, the particle goat forms around it, leaps and bursts into TRAILGOAT FILMS, with its "Night trail" sting (crickets, footfalls, one rock-impact hit, a low drone) mastered in, ending on black. It's rendered in Unreal ParticleLab (`studio/particle-engine/`, `/kb-unreal`); `intro-standin-canvas-1080p24.mp4` beside it is the old 4 s canvas cut. The sting plays as mastered and the race music fades in at 5.0 s. A 1 s cut for Shorts and trailers is in `Renders/films-ident/TrailGoatFilms-sting-1s-1080p24.mp4`.
5. **Blender may be rendering.** Only `short_film.py` runs Blender (a Short's portrait frames), and it waits for the studio's render lock like the batch queues do. ffmpeg and Playwright share the CPU with a running batch, so expect everything to take about twice as long while one runs.

## Prepare the film

Make `/Volumes/KB SS/TrailGoat-Studio/Films/<slug>/film.json`:

```json
{
  "out_dir": "/Volumes/KB SS/TrailGoat-Studio/Renders/flyovers/youtube-1080/<slug>",
  "master":  "/Volumes/KB SS/TrailGoat-Studio/Renders/flyovers/youtube-1080/<slug>/<slug>-1080p-master.mp4",
  "slug": "<slug>",
  "shots": "/Volumes/KB SS/TrailGoat-Studio/Films/<slug>/<id>.json",
  "music": {"file": "…/audio-library/<track>.mp3", "start": 0, "title": "…", "artist": "…", "reason": "…", "credit": ""},
  "next": {"title": "<the next film's title>"},
  "intro": "/Volumes/KB SS/TrailGoat-Studio/Films/assets/intro-trailgoat-films-1080p24.mp4",
  "dest": "/Volumes/KB SS/TrailGoat-Studio/Films/<slug>",
  "playlist": "Race Flyovers", "privacy": "public"
}
```

- `out_dir` must hold `course-{id}.json`, `hud-frames.json` and `poster.webp` from the render. A master rendered before the readout existed only needs a `--dry` run of `render.py` to write `hud-frames.json`.
- `shots` is the authored shot spec; its verified `aids` become the chapters. Copy it into the film's own folder and point there, never at a worktree: a removed worktree silently drops a re-dress to the catalogue's chapters (Cocodona, 2026-10-26). Without a shots file the chapters come from the catalogue's aid list, which is unverified: say so in the report.
- `music`: **always classical**: a famous public-domain piece, in a free-to-use recording, with a one-line reason tied to the race (Toccata and Fugue for Javelina's Halloween weekend, Vivaldi's Autumn for a harvest festival). Kris, 2026-10-27: "I want to keep the classic music theme for the flyovers. The feedback I've gotten is overwhelmingly positive." Never pitch a non-classical track. Pick from the library by the race's character. Prefer a track no other film has used, but reuse is fine, sparingly, when the Audio Library lacks the pick or downloads are refused. Kris, 2026-10-27: "we can reuse some of the music we have sparingly. I'm sure people are going to come watch the races they are in and maybe some big races, but not all of them." Reuse on smaller races, not between two big ones; start the reused piece at a different point where it fits; note the reuse in `LICENSES.md`. Also and copy the exact credit line from `LICENSES.md` when the licence needs one (CC-BY tracks do). `start` skips into a long piece (to its famous theme, or so a finale lands on the film's last frames); `delay` holds the track back that many seconds after the intro (a piece shorter than the film can then end on the finish pull-back); a track that runs out before the video ends finishes on its own ending, not a forced fade. `reason` is the one-line joke that goes in the description.
  - **A track shorter than the film** (batch 2, 2026-10-28): measure its audible end with `silencedetect=n=-50dB:d=0.3`, because Audio Library MP3s carry about 0.7 s of lead-in and 5 s of trailing silence. `post_film.py` prints when the runner finishes and when the film ends. Aim the last note at one of them: `delay` ≈ film end − audible end puts it on the closing frame (Forgotten Florida, Gymnopédie, delay 5), and `delay` 0 can land it on the runner's finish (Grayson Highlands 50K, Für Elise ends 1 s after the finish). Keep the opening gap ≤ about 6 s, and say how long the quiet tail runs, because 20 s or more of silent zoom-out is Kris's call. When the Audio Library has a longer recording of the same piece, get it: The Thunderer's Army Band 2:48 recording filled Keweenaw's 2:54 film, where the Marine Band 2:20 one would have left 33 s. If there isn't one, lengthen the piece by repeating one of its phrases, as if taking a repeat once more: `scripts/extend_track.py find` lists where the theme comes back, and `splice --at A --again B` joins the music on the same note and checks the join. Grayson Highlands 50K's Für Elise went from 2:31 to 2:46 this way, so it plays through the closing zoom-out. Kris asked for a filled tail rather than 22 s of silence, 2026-10-28. Put the edit in the film's `music/` folder, add a row to `LICENSES.md`'s Edits table, and send Kris a clip of the join and one of the ending before it goes up. He passed that first join ("The Grayson 50K join sounds clean", 2026-10-28), so offer a phrase-repeat first for a quiet tail, ahead of a later start that only moves the silence to the opening.
  - **Recordings cleared everywhere, since 2026-11-02.** The films and Shorts also go to Instagram, Facebook and TikTok, and the YouTube Audio Library licence covers YouTube only. Kris: "Lets switch all of it, except leave the films on youtube as they are, so youtube switches moving forward."
    - **Every new film and Short uses one of:**
      - a recording from `Music/public-domain/`: Musopen (via its Wikimedia Commons or Internet Archive mirrors), the US federal bands' own sites (US government works, so public domain), or Commons PD/CC0. That folder's `LICENSES.md` holds each source URL and licence wording as proof for any Content ID claim;
      - a CC BY track (Kevin MacLeod), with its credit.
    - **The 64 films already on YouTube keep their Audio Library tracks.** Anything new built from them, a Short or an off-YouTube copy, takes the same piece's cleared recording from `Music/public-domain/MAP.json`, starting at the same passage.
    - **Enforced in the scripts:** `scripts/music_rights.py` decides, `post_film.py` refuses a YouTube-only track (a re-dress of a live film passes `--youtube-music-ok`), and `short_film.py` and `week_short.py` take the mapped copy or stop.
    - **The Audio Library steps below now apply only to re-dressing those older films.**
  - **Getting a track yourself (Audio Library, older films only):** Studio → Audio library (`studio.youtube.com/channel/UCQoBvGjrnX902dMStuGnHIg/music`) in Kris's Chrome. Search the title; Download appears when you hover the row's Added column, and the MP3 lands in `~/Downloads`. Move it into the audio library and add its `LICENSES.md` row. Leave the terms banner alone. Kris OK'd grabbing classical tracks for the flyovers on 2026-10-27.
  - **Licence wording comes from `LICENSES.md`, not the performer.** The U.S. Army and Marine Band recordings there are listed under the YouTube Audio Library License, so don't call them "public domain".
- `next`: the title of the film that follows in the playlist; it's typed into the end card and linked in Studio.
- `gain_m` (optional): the climb in metres for the description and thumbnail, when the catalogue's figure is wrong. The catalogue's `official_gain_m` wins over its own `gain_m` (a terrain estimate), and this beats both. Check the climb against the race's published figure before every dress: Georgia Death Race's catalogue said 10,581 ft where published listings say about 14,000 ft and the z13 terrain at a 10 m noise filter says 14,556 ft (2026-10-27, `gain_m` 4267.2). Use the race's own figure when it publishes one, else the most-cited listing figure that agrees with the terrain, and tell Kris which.
- `distance_m` (optional): the race's own distance in metres, where its course line runs short of it. Tahoe 200's line is the organiser's map at 187.4 mi for 200.4 (2026-10-30). The readout's distances, the thumbnail and the description then read the race's figure (trailgoat hud.py `--distance-m`); the terrain is still read along the line. Chapters and the NEXT AID countdown sit where each pin stands on the line (its shots-file mile), and name it with the label's official figure, so a short line no longer puts them late.

## Dress it

```bash
TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/post_film.py <dest>/film.json
```

It runs, in order: `hud.py` (readout + corner mark onto the master; its fourth cell is ELEVATION GAIN, the climb so far, ending on film.json's `gain_m` at the finish, in place of the site hero's carbs eaten (Kris, 2026-10-29: "a better stat for the YouTube vids"; trailgoat hud.py `--gain-m`; films dressed before that show CARBS EATEN); a thin glass the trail shows through: 22 % fill, no blur, a soft shadow behind the type, Kris's pick from four levels on 2026-10-27, trailgoat #752. Don't thicken it back to the site's 66 % blurred glass); if something in the film passes under the card, such as the Western States hero's TRAILGOAT sign at frames 645-735, set `"hud": {"hide": "645-735"}` in film.json and the card fades aside for those frames → `render_end_card.py` (15 s, the next film named) → ffmpeg concat of intro + film + card at 24 fps with the track trimmed to the length, faded 1.5 s in and 3 s out, normalised to -14 LUFS (an intro with its own sound, the sonic logo, plays as mastered and the track starts as it ends; a silent intro gets the track under it) → the thumbnail from `poster.webp` (race name in Sora, distance and climb, the wordmark) → chapters (0:00 TrailGoat Films, the start, every pin ≥ 10 s apart, the finish at the shot named THE FINISH (moved 10 s past a last pin just before it; until 2026-10-29 it sat on the whole-course back-out, 20-30 s after the runner arrives, in every film up to Moab), the card) → `description.txt` and `meta.json`. Flags: `--skip-hud` when the master already carries the readout, `--skip-intro` / `--skip-end` while those assets are missing, `--meta-only` to redo the thumbnail, description and `meta.json` without re-encoding, `--upload` to push at the end. A rerun reuses `work/<slug>-hud.mp4` when it exists, so after a `hud.py` change move that file to the Trash first, or the old readout goes out again (Ultra Pirineu's 'Niu de L'àliga' survived one re-dress, 2026-10-31).

**Data credits are automatic.** The description's credit block comes from what the render actually used, read from `render.py`'s log in `out_dir`: the terrain source and the USGS credit, any country's required DEM notice (EU-DEM, Canada, UK, Australia, New Zealand, Norway, Austria, Mexico, ArcticDEM above 60° N), the USGS/NAIP imagery line when imagery was draped (and a NAIP year's own line when the shots file picked one, `"imagery": "naip-2018-ut,usgs,s2-2016"`, for a summer flight where USGS's newest is winter), and `© OpenStreetMap contributors, openstreetmap.org/copyright` whenever the coastline went in. A render that used Esri World Imagery is refused: its terms don't allow publishing. Don't edit the credit lines by hand; they're the licences' wording. The tags and closing hashtags follow the race's length (ultramarathon past 45 km, mountain marathon from 40, else trail race), and an organizer whose name is the race's own is left out of the description and tags.

**Look before publishing.** Pull frames from `<slug>-youtube.mp4` at 4.5 s (the ident's lockup), the first aid pin's chapter time (readout + pin together), 60 % through, and 3 s from the end (card), and read them. Check: the readout's next aid matches the pin in frame; the corner mark isn't over a label; the end card's zones are clear; the music fades, not cuts, and comes in after the ident's click-off, not under it. Read `description.txt` once as a viewer would. The course link is looked up live and checked before the description is written: a course snapshot from before the course had its page slug has no `page_url`, and the old fallback `/course/<film slug>` 404'd in four batch-3 descriptions (2026-10-29); post_film now stops rather than write a dead link.

**Look at the thumbnail too.** `poster.webp` is the render's own pick and is sometimes poor. On Keweenaw (2026-10-28) the TRAILGOAT wordmark landed on the start pin's label, and on Grayson Highlands 50K the frame was mostly ridge shadow. Pull a 3×3 grid of candidate frames from the master. Prefer sunlit terrain with the trail winding through it, or the closing whole-course shot, with the top-left clear for the wordmark and no label under the title. Set `"thumb_at": <seconds into the master>` in film.json and rerun with `--meta-only`. That rebuilds the thumbnail with the sourced climb without re-encoding the video.

## Publish

**Race-week publishing (from batch 6, 2026-11-02).** Kris: "Approved: start batch 6 as proposed, with the catalogue imports and race-week scheduled publishing." Films are made in race-date order and each goes public at 06:00 New York time on the Monday of its race's week, its Short on that Thursday. Put `"publish_at"` (UTC, e.g. `"2026-11-16T11:00:00Z"`; 10:00Z once daylight time starts) and `"short_publish_at"` in film.json; post_film.py and short_film.py copy them into meta.json and yt_upload.py uploads private with that `publishAt`. The end card's `next` is the film published just before this one, so its end-screen tile points at a film that is already public and can be placed at upload time. The batch's schedule (`queue/batch6_schedule.json`) holds each film's week, times, `next_slug` and video ids; the scheduled task `trailgoat-race-week-monday` checks each Monday that the week's films went public (`queue/race_week.py`), resyncs /films and sets each Short's Related video.

- **Through the API** (after Google's audit passes): `post_film.py film.json --upload`, or `yt_upload.py upload <mp4> <meta.json>`. It sets the title, description, tags, thumbnail and playlist and prints the link with the privacy YouTube actually applied. Until the audit passes an API upload lands **private**, so:
- **By hand until then:** open Studio's upload box in Chrome, bring Finder forward with the MP4 (and its thumbnail) already selected, and ask Kris to drag it in. For several files, select them all at once with `osascript` (Finder `activate`, `reveal`, `select` on a list of POSIX-file aliases); for one, `mcp__ccd_host__reveal_path` also works. Kris, 2026-10-27: "could you highlight them in finder for me?" Fill the details from `meta.json` (title, description, playlist, not made for kids, no paid promotion, AI use No, English, Sports, the tags), upload the thumbnail, select Public, and stop before Publish for his OK. Studio pre-ticks the last-used playlist: check the box's state before clicking it.
- **End screen, in Studio either way:** Content → the video → Editor → End screen → "Video: choose specific video" (the `next` film) and "Subscribe"; drag the video element onto the card's 16:9 zone and the subscribe button onto its circle; timing is the last 15 s. Then add the video to the `next` film's predecessor if its card named this one.
- Confirm with the API afterwards (`videos.list`: public, processed; the playlist contains it) and record the link.
- **Then put it on trailgoat.run/films** (2026-10-29, trailgoat #764). The page lists the Race Flyovers playlist from `app/films.json`, which `scripts/films_sync.py` writes (read-only, the uploader's token). After a batch has processed, in a TrailGoat worktree at `origin/main`: `~/.config/trailgoat-youtube/venv/bin/python scripts/films_sync.py`, then ship the changed `app/films.json` in a PR and merge it when CI is green. A film YouTube is still processing is skipped; sync again later. A swapped film (a new upload replacing a public one set to private) drops off and its replacement comes in on the same sync. The page takes each film's course from the first `trailgoat.run/course/` link in its description and its climb from the opening line ("…to the finish: 126 km and 6,764 m of climbing…"), so keep both as post_film writes them. On the page YouTube only suggests our films (rel=0, and our own Up next card replaces the end grid).

## Make its Short

Every published film gets a YouTube Short: its biggest-climbing 40 seconds, filmed again in 9:16 from the film's own camera, with the race readout and a hook naming the climb (Kris, 2026-11-02: "build the Shorts pipeline"; the growth report's idea 2, since Shorts are how new viewers find the channel and the long films are where they subscribe).

```bash
TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/short_film.py <dest>/film.json
```

- **pick** (trailgoat `short.py pick`) slides a 40 s window over the film's LEG shots and keeps the one whose readout climbs most. The film runs about a mile of course a second, so the window holds 25-30 miles and the race's big climbs. The hook names the biggest sustained climb inside it (a rise no drop of more than 40 m interrupts) by the verified aid pin within 1.5 km of its top, else "The high point", else "The biggest climb", with its height and length off the profile: Leadville picks Hope Pass, +3,330 ft in 4.3 mi. The pick is saved to `<dest>/short/pick.json` and kept on a rerun: when an aid name isn't what runners call the climb, edit `climb.place` and rerun.
- **render**: Blender `render.py --res 1080x1920 --portrait 0.5 --frames a-b`, a window half the 16:9 frame's width and taller, so the picture stays sharp instead of a crop blown up 1.8x. The camera solve and all label and sign maths keep the 16:9 aspect, so every pose is the film's. About 6 min of scene setup and 0.8 s a frame (13 min for 960 frames); the PNGs are about 10 MB each, in `Renders/flyovers/shorts/<slug>/` on KB SS. Resumable.
- **dress** (trailgoat `short.py dress`): the hook at the top (the race mark, the climb's place in Red Hat Display, its figures in --c-climb), the readout as one strip of four cells (mile, elevation, grade, elevation gain), and in the last 2.5 s "The whole 100 miles / FULL 3D FILM · LINK BELOW". Everything sits in the top third and the middle, clear of the Shorts player's title, buttons and progress bar along the bottom and right. Then the film's own track at the same moment, -14 LUFS, and `short/description.txt` + `short/meta.json` (playlist "Race Shorts", the long film's link first).
- **Disk**: the portrait frames are about 3.5 GB a Short. Once dressed, short_film.py keeps them as one clean CRF 14 video, `Renders/flyovers/shorts/<slug>/<slug>-portrait.mp4`, and drops the PNGs after the frame count checks out. week_short.py plays that video behind the race's card. KB SS was at 87 % on 2026-11-02.
- **Look before publishing**: frames at 0.5 s (the hook must read on the first frame), the climb's top (`climb.frame_top`), and 1 s from the end (the link line). Play the audio at the start: a Short starting mid-phrase is fine, a click isn't.
- **Publish**: `yt_upload.py upload <dest>/short/<slug>-short.mp4 <dest>/short/meta.json` (a vertical video under 3 min is a Short), then in Studio set the Short's **Related video** to the long film (the API can't), so the player's link under the Short opens it.

## This week in Trail Racing (the Monday Short)

Kris, 2026-11-02, in order:
- "lets also make a short every monday announcing the races for the week, the details (distance, elevation, location, etc..) with very short previews of each race in the background"
- the name "This week in Trail Racing"
- every race of 50K and up: a card for each filmed race, then the rest as a list ("I like your idea better")
- "in the details of the short we need to list every race so that they all show up in search results"

```bash
TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/week_short.py --week <monday>
```

- **Filmed races:** every film whose race runs that Monday to Sunday, found from the catalogue: the film's course → its event → that event's edition this week. Each gets a 6.5 s card with:
  - its name, in the gradient;
  - where it runs, its distance and its climb, all from the description's first line, so the Short says what the film says;
  - the day, plus the start time only where our prep verified it in `queue/<slug>/start`. The catalogue's 07:00 is often a default, not the gun;
  - its aid stations.
- **Card backgrounds:** the film's Short frames, else a preview rendered for the card (`render.py --portrait` on the film's biggest-climbing stretch of that length, under the studio lock, 2–3 min a race plus the scene setup).
  - Never a crop of the 16:9 master. It blows the map labels up 1.8x, and films rendered before 2026-10-28 carry no label boxes to dodge them (Grand Ridge's "1,194 FT" filled its card).
- **Every other race of 50K and up that week:** read-only from the catalogue, one row per event (day, name, place, distances), seven to a page at 3 s a page, behind the frosted glass.
  - Backyard, timed, relay, stage and virtual events are left out.
  - The last card's clip plays back and forth underneath.
  - A week ran 12 to 51 such events from November to March (2026-11-02 count); 2–8 Nov has 4 filmed + 59 listed, a 58 s Short.
- **Each Monday the featured races' own Shorts go up too**, from 09:00 New York, an hour apart. Kris, 2026-11-02: "It would be nice to also release the shorts for the races we feature each monday." The scheduled task `trailgoat-this-week-in-trail-racing` (Thursdays) makes and schedules them before the weekly Short, which then uses their frames.
- **Running order:** opener 2.5 s (TrailGoat.run, "This week in / Trail Racing", the dates, each filmed race's day, "+ N more races of 50K and up"), then the cards, the pages and a 2.5 s closer.
- **Music:** Grieg's Morning Mood every week, the series theme.
- **Search:** the description lists every race, filmed ones first with their film and course links, then "Also racing this week" one per line (trimmed from the end only past YouTube's 5,000 characters). Tags carry as many race names as fit in 480 characters, never one with a comma.
- **Output:** `Films/_race-week/<monday>/this-week-<monday>.mp4` + `meta.json` (playlist "This week in Trail Racing", `publish_at` the Monday 07:00 New York, `related_video` the first filmed race).
  - Build it once the week's films are dressed, and hand it to the upload session with them.
  - For the current week, drop `publish_at` and publish at once.

## Report

For each film: the YouTube link and privacy, length, the track and its licence line, the chapters, where the aid pins came from (shots file or catalogue), and anything skipped (no intro, no end screen yet).

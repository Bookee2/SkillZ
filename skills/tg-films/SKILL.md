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
5. **Blender may be rendering.** This skill never runs Blender. ffmpeg and Playwright share the CPU with a running batch, so expect everything to take about twice as long while one runs.

## Prepare the film

Make `/Volumes/KB SS/TrailGoat-Studio/Films/<slug>/film.json`:

```json
{
  "out_dir": "/Volumes/KB SS/TrailGoat-Studio/Renders/flyovers/youtube-1080/<slug>",
  "master":  "/Volumes/KB SS/TrailGoat-Studio/Renders/flyovers/youtube-1080/<slug>/<slug>-1080p-master.mp4",
  "slug": "<slug>",
  "shots": "<repo>/scripts/flythrough/shots/<id>.json",
  "music": {"file": "…/audio-library/<track>.mp3", "start": 0, "title": "…", "artist": "…", "reason": "…", "credit": ""},
  "next": {"title": "<the next film's title>"},
  "intro": "/Volumes/KB SS/TrailGoat-Studio/Films/assets/intro-trailgoat-films-1080p24.mp4",
  "dest": "/Volumes/KB SS/TrailGoat-Studio/Films/<slug>",
  "playlist": "Race Flyovers", "privacy": "public"
}
```

- `out_dir` must hold `course-{id}.json`, `hud-frames.json` and `poster.webp` from the render. A master rendered before the readout existed only needs a `--dry` run of `render.py` to write `hud-frames.json`.
- `shots` is the authored shot spec; its verified `aids` become the chapters. Without it the chapters come from the catalogue's aid list, which is unverified: say so in the report.
- `music`: pick from the library by the race's character, never reuse a track across films, and copy the exact credit line from `LICENSES.md` when the licence needs one (CC-BY tracks do). `start` skips into a long piece; `reason` is the one-line joke that goes in the description.
- `next`: the title of the film that follows in the playlist; it's typed into the end card and linked in Studio.

## Dress it

```bash
TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/post_film.py <dest>/film.json
```

It runs, in order: `hud.py` (readout + corner mark onto the master) → `render_end_card.py` (15 s, the next film named) → ffmpeg concat of intro + film + card at 24 fps with the track trimmed to the length, faded 1.5 s in and 3 s out, normalised to -14 LUFS (an intro with its own sound, the sonic logo, plays as mastered and the track starts as it ends; a silent intro gets the track under it) → the thumbnail from `poster.webp` (race name in Sora, distance and climb, the wordmark) → chapters (0:00 TrailGoat Films, the start, every pin ≥ 10 s apart, the finish, the card) → `description.txt` and `meta.json`. Flags: `--skip-hud` when the master already carries the readout, `--skip-intro` / `--skip-end` while those assets are missing, `--meta-only` to redo the thumbnail, description and `meta.json` without re-encoding, `--upload` to push at the end.

**Data credits are automatic.** The description's credit block comes from what the render actually used, read from `render.py`'s log in `out_dir`: the terrain source and the USGS credit, any country's required DEM notice (EU-DEM, Canada, UK, Australia, New Zealand, Norway, Austria, Mexico, ArcticDEM above 60° N), the USGS/NAIP imagery line when imagery was draped, and `© OpenStreetMap contributors, openstreetmap.org/copyright` whenever the coastline went in. A render that used Esri World Imagery is refused: its terms don't allow publishing. Don't edit the credit lines by hand; they're the licences' wording.

**Look before publishing.** Pull frames from `<slug>-youtube.mp4` at 4.5 s (the ident's lockup), the first aid pin's chapter time (readout + pin together), 60 % through, and 3 s from the end (card), and read them. Check: the readout's next aid matches the pin in frame; the corner mark isn't over a label; the end card's zones are clear; the music fades, not cuts, and comes in after the ident's click-off, not under it. Read `description.txt` once as a viewer would.

## Publish

- **Through the API** (after Google's audit passes): `post_film.py film.json --upload`, or `yt_upload.py upload <mp4> <meta.json>`. It sets the title, description, tags, thumbnail and playlist and prints the link with the privacy YouTube actually applied. Until the audit passes an API upload lands **private**, so:
- **By hand until then:** open Studio's upload box in Chrome, `open -R` the MP4 in Finder, and ask Kris to drag it in. Fill the details from `meta.json` (title, description, playlist, not made for kids, no paid promotion, AI use No, English, Sports, the tags), upload the thumbnail, select Public, and stop before Publish for his OK. Studio pre-ticks the last-used playlist: check the box's state before clicking it.
- **End screen, in Studio either way:** Content → the video → Editor → End screen → "Video: choose specific video" (the `next` film) and "Subscribe"; drag the video element onto the card's 16:9 zone and the subscribe button onto its circle; timing is the last 15 s. Then add the video to the `next` film's predecessor if its card named this one.
- Confirm with the API afterwards (`videos.list`: public, processed; the playlist contains it) and record the link.

## Report

For each film: the YouTube link and privacy, length, the track and its licence line, the chapters, where the aid pins came from (shots file or catalogue), and anything skipped (no intro, no end screen yet).

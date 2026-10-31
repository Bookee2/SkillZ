---
name: tg-render
description: Render one or more TrailGoat catalogue race flyovers by course name, including a race-name billboard, overhead runner-follow shots, verified aid-station pins, visual QA, and a resumable overnight batch. Use for TrailGoat 3D course video requests, not ordinary map screenshots.
argument-hint: <race name>[, <race name>...]
---

# TG-render

Turn catalogue race names into locally inspectable, encoded 3D flyovers using TrailGoat's existing Blender engine. One invocation may name one race or a batch. A render is not a deployment: do not run `deliver.py`, commit media, or publish without a separate request.

## Set up the machine (any computer)

1. **Checkout.** Use the current repository when it is TrailGoat. Otherwise try `$TRAILGOAT_REPO`, then `~/Desktop/Projects/TrailGoat`, then `~/TrailGoat`. If none exists, ask before cloning `gh repo clone Bookee2/trailgoat`. The main checkout usually carries Kris's uncommitted work, so render from a worktree of `origin/main` made for the job: `git worktree add --detach .claude/worktrees/<job> origin/main`. Then symlink the main checkout's `.venv` and `scripts/flythrough/.tiles` into it. The tile cache holds tens of thousands of terrain and imagery tiles; a worktree with an empty cache fetches every tile again, and a long render then dies on an S3 "Connection reset". A job that runs overnight keeps its worktree until the job ends. Don't remove it, and don't merge its branch with `--delete-branch` while the job runs. Losing the checkout mid-batch (2026-10-26) failed seven previews at the authoring step.
2. **Current engine.** Run `git fetch origin` and confirm that `scripts/flythrough/` matches `origin/main` (`git diff --stat origin/main -- scripts/flythrough`). If it doesn't, stop and tell the user. The encoder changes over time (since 2026-09-22 the phone cut is encoded from the frames at crf 26, not re-encoded from `hero.mp4`), and a stale checkout gives oversized files. Never pull over someone's uncommitted work.
3. **Encoder venv.** Check that `.venv/bin/python -c "import imageio_ffmpeg"` succeeds. If it fails, and with the user's go-ahead, run `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt imageio-ffmpeg numpy`.
4. **Blender 5.2+.** Look in this order: `$BLENDER_BIN`, `/Applications/Blender.app/Contents/MacOS/Blender`, then `blender` on `PATH`. Export the one you find as `BLENDER_BIN` for the batch. If Blender is missing, say so and stop. You can't render without it, and installing it is the user's call.
5. **Storage.** At 1280×720, frames take about 1.6 MB each, so a 132 s film at 24 fps (3168 frames) needs about 5 GB under `out/`. Check free space before starting.
6. **Tile cache.** `render.py` caches terrain and imagery tiles in `scripts/flythrough/.tiles` *inside the checkout*, so a fresh worktree starts empty and re-downloads everything (2026-10-31: batch-5 stills from a new worktree failed on S3 connection resets). Clone a warm cache in first, on the same volume: `cp -c -n -R <old>/scripts/flythrough/.tiles/. <new>/scripts/flythrough/.tiles/`.

Then read `CLAUDE.md` / `AGENTS.md` if present, plus `scripts/flythrough/README.md`. Before editing, inspect `render.py`, `geo.py`, `run.sh`, `encode.py`, the nearest authored `shots/*.json` and `git status`. Don't overwrite existing shots or outputs.

## Resolve and prepare

1. Resolve every supplied name through `https://trailgoat.run/api/fuel/courses/search?q=...` (or the local app). Confirm the exact race, distance and course ID by fetching `/api/fuel/courses/{id}`. Never pick an ambiguous result; ask. Save a course JSON snapshot in the output directory. The renderer accepts its path or the ID.
2. For each course, use an authored `shots/{id}.json` when it suits. Otherwise author one in the house structure. Kris, 2026-10-26: "begin zoomed out, then come into the start, follow the runner to the finish and then zoom back out. Just like we did Appalachian 200". So:
   - **open on the whole course**, then zoom into the start: the full race-name billboard and the start pin;
   - **follow the runner overhead** to the finish, with no dominant horizon;
   - **settle on the finish, then pull back out** to the whole course, ending on the opening pose so the film loops.

   Two scripts in `scripts/flythrough/` do it. Run them in order, both on the same shots file:
   ```bash
   .venv/bin/python scripts/flythrough/author_film.py <course.json> <shots.json> --legs "0,10.6,20.5,…" --merge-aids
   .venv/bin/python scripts/flythrough/whole_course.py <course.json> <shots.json>
   ```
   `author_film.py` writes the follow (THE START, one leg per mile range in `--legs`, THE FINISH). `whole_course.py` adds the open and close:
   - the zoom's length scales with its log ratio (about 0.16 log-units a second, 10–22 s);
   - the pan moves in step with the distance covered;
   - each end turns at most 40°;
   - the box takes in both wide footprints.

   **Close enough to read.** Kris, 2026-10-27, on a batch flown 2–7 km out: "I can't read the billboard or aid station names on any of them … come closer in and follow closer to the runner." render.py sizes pins, labels and the sign with the course (label scale SZ: 0.35 up to 50 km, then distance/161 km up to 1.0), so readability is label size over camera distance. Since trailgoat PR #753 (merged 2026-10-27), `author_film.py` follows at 3,550 m × SZ of slant, about 15% closer than Wild Florida's approved 1.46 km:
   - a 50K follows about 760 m out, a 50-miler 1.1 km, a 100 2.2 km;
   - the look-ahead is 0.15× the slant;
   - each leg lasts as long as its miles take at 18 °/s of ground flow, so films run about 2:50–3:20;
   - THE START drifts in from 1.05× to 0.78× the slant.

   Kris signed this off on 2026-10-27, after all 11 redone review copies: "These all look good, I think we've got our process down to a nice science." It is the standard for every new course: close follow, fixers, a 720p review copy, his OK, then the 1080p master.

   For a film authored by hand, check it against Wild Florida: about 900 m out, a 170–200 m look-ahead and 0.31 mi/s. The 2026-10-26 batch flew 2.3–6.5 km out with a 900 m look-ahead at 0.6–0.7 mi/s, and every course was redone.

   Then fix three things on the shots file with this skill's scripts (`~/.claude/skills/tg-render/scripts/`), in order:
   ```bash
   python3 fix_stems.py <course.json> <shots.json>    # aid pins on the start, finish or HIGH POINT stack instead of overprinting
   python3 fix_sign.py  <course.json> <shots.json>    # the race sign faces THE START, sized and turned for the finish
   ```
   - `fix_stems.py`: a loop's HQ aid stands on the start at a mid-race mile, so render.py doesn't lift either pin. It stacks the aid under the start or finish pin (stem 0.2, never up into the sign) and lifts a pin on the high point to 2.6.
   - `fix_sign.py`: the sign stands 0.3× the follow slant behind the start, facing THE START's camera (not the whole-course opener's). Its letters scale with SZ, capped so the name fits the frame. On a loop it turns toward the finish cameras only as far as its row's near end stays 150 m behind the start pin. A long name on a loop still shows side-on where the camera comes back past it. That's fine: the sign stays up all film. Kris, 2026-10-27: "It kind of nice as just a fixture in the film." Don't make it leave after the opener.

   Appalachian 200's `shots/69.json` is the reference; Wild Florida's `shots/96.json` is the close-follow example. Keep the full route covered, and use `--dry` to check the camera lints and map. The limits are:
   - ground flow ≤ 8 °/s (18 on follow legs);
   - yaw ≤ 7 °/s;
   - zoom ≤ 1.6×/s.

   `flow_const` moves count only sideways motion. A course whose aids can't be verified renders from a copy of its record with `aid_stations` cleared, so it gets no pins.
   Copy the finished shots file into the film's output folder too. Later steps, like tg-films chapters and re-dresses, then never depend on a worktree that may be gone.
   **Courses the catalogue doesn't hold yet** (races abroad and others off UltraSignup; batch three, 2026-10-27). Most already have a `race_editions` row with no course. Put the official file in the race's queue folder (`src/`) and attach it with this skill's `import_local.py` (run from the TrailGoat checkout: `.venv/bin/python …/import_local.py <edition_id> <file.gpx> [--name "…"] [--want-km N] [--commit]`). It mirrors `gpx_import.py`: `build_course()`, the ±25 % distance check, `save_fuel_course()` and the edition link. Dry-run first, then run `backfill_route_preview.py`.
   - **Check the climb against the official figure before importing**, because it goes on a public course page. A user-uploaded track's GPS elevation can read 60 % high (the Diagonale des Fous: 16.8 km against 10.2 km); smooth it over about ±120 m. A track with no elevation gets the importer's coarse lookup, which reads low on long courses (the Spine: 6.4 km against about 10 km). Fill it first from render.py's own Terrarium tiles with `add_ele.py`.
   - **Waypoints become catalogue aid stations.** Strip ones that aren't aid, such as Badwater's time stations (the race is crew-supported).
   - **Race-folder files `reauthor.py` honours:** `race_name` (the sign and readout; put the distance in it for races abroad, e.g. "UTMB Mont-Blanc 174K"), `units` (`metric` reads the readout in km) and `start` (the next edition's gun, for the race clock). Labels on races abroad read `· KM x`.
   - **Direction and edition.** Some races alternate direction: Hardrock went clockwise in 2026, so 2027 runs counter-clockwise; the official CCW GPX and the last CCW aid sheet are on hardrock100.com. Use the newest official line. The catalogue's own 2027 course can still hold an old track (Hardrock 473, Bigfoot 100's dropped Windy Ridge spur), so compare before rendering.
   - **Imagery abroad.** USGS covers only the US. Since trailgoat #756/#757, render.py's default `--imagery auto` takes each tile from the first source that covers it: USGS (US), IGN BD ORTHO (France, Corsica, Réunion), swisstopo (Switzerland), PNOA (Spain, the Canaries), else Sentinel-2 cloudless 2016 by EOX, brightened with a 0.65 gamma. All of them are free to publish with credits, which tg-films writes, plus an on-screen line. Kris chose Sentinel-2 over `--style relief` for Italy and the UK (2026-10-27). Esri is never used: its terms forbid publishing. A 400/404 tile is a miss and isn't retried; the old nine retries per tile stalled a film abroad for 90 minutes. To settle a look, take a stills check first: the dry run doesn't fetch imagery.
   - **Blocked sites.** A site behind a bot check (Cloudflare on torxtrail.com) or a login (Outdooractive, Trace de Trail) is Kris's to download in his browser. Never work around it. Ask him for the file, use an older official copy (e.g. from the Wayback Machine), or use a clearly labelled public reconstruction (e.g. the OpenStreetMap route relation).
3. Keep catalogue aid stations when present. If they're absent, research the organizer's current course and aid information. Record the source and edition, reconcile station miles with the actual GPX, and add verified `[mile, label]` entries to the shot spec. One physical station visited twice may be one labeled pin. Never invent pins. If aid data can't be verified, say so and render without guessed stations.
4. For a new course Kris hasn't seen, a review copy comes first: `render.py … --shots <shots.json> --res 1280x720 --samples 8 --every 2`. That's about 0.3 s a frame, about 13 min a course. Encode it at `-framerate 12 -r 24` so the timing is the film's, and copy it to iCloud `TrailGoat Videos/review/<date>/` for his phone. The full render waits for his OK.
   - **Never 360p.** At 640×360 the sign and aid labels are a few pixels tall, so he can't judge what matters (2026-10-27).
   - **Never every 4th frame.** Shown at 6 fps, mountain parallax jumps and reads as a shaky camera. Quest's render jolts 4 times in 85 s at 24 fps and 37 times at every 4th frame.
   - **Motion needs every frame.** For a mountain course, also make one copy at the full 24 fps (no `--every`, about 25 min) and point him to it.
   - **Measuring motion:** `shake.py <cam.json>` (from `render.py --dry --export-cam cam.json`) measures the camera path. `picture_jitter.py <video> <t0> <t1> <step>` measures the rendered picture. Check the picture: a steady camera path can still look shaky, and the reverse.
5. Render full-resolution stills (`--stills`) at the opening, the billboard exit, representative follow legs, each aid pin, and the finish. Read the images yourself, checking label readability and frame edges, and fix bad framing before the expensive pass. Check the imagery's **season** too: a national mosaic takes its newest flight, which can be winter. The Wasatch 100's USGS imagery was a 21 Nov 2021 flight with every ridge under snow for a September race; `"imagery": "naip-2018-ut,usgs,s2-2016"` in the shots file took Utah's summer 2018 NAIP from Microsoft's Planetary Computer instead (its STAC search lists a place's NAIP years and flight dates). A long race name can run its sign out of the frame during THE START (Grand Raid des Pyrénées Ultra, 33 characters at 226 m letters): set `title.letters_m` smaller and `_auto: false` so the queue's fix_sign.py keeps it. A clean lint is necessary, but it doesn't replace looking.

## Render and batch

Build a JSON manifest with a unique output directory per course:

```json
{
  "courses": [
    {"id": 96, "name": "Wild Florida 50k", "out": "out/wild-florida-50k"},
    {"id": 148, "name": "Perpetua Coast", "out": "out/perpetua-coast"}
  ]
}
```

Validate the queue first with `--dry-run`, then run the batch from the TrailGoat checkout. `batch_render.py` is in this skill's `scripts/` directory (installed at `~/.claude/skills/tg-render/scripts/`):

```bash
python3 ~/.claude/skills/tg-render/scripts/batch_render.py --repo <checkout> --manifest <manifest.json>
```

- **One at a time.** It renders and encodes one course at a time through `scripts/flythrough/run.sh` (Blender, then `encode.py`). Never run simultaneous full renders on one machine. When several drivers share the night (previews, a batch, an Unreal render), take the GPU with a lock directory: `until ! pgrep -f 'Blender.*-b' >/dev/null && mkdir <queue>/.render.lock 2>/dev/null; do sleep 30; done`. Only the driver that made the lock removes it, so never `rmdir` a lock in a retry loop.
- **Network retries.** A run that fails on a dropped tile fetch (`URLError`, `Connection reset`, `timed out`) is retried up to three times, a minute apart and then longer. The retry resumes from the frames already rendered. Any other failure isn't retried. At the start, the batch says so if the checkout's `.tiles` is empty.
- **Resumable.** It writes per-course logs and an atomic `batch-status.json`, skips outputs that are already complete, and resumes existing Blender frames after an interruption.
- **Re-encode only.** Pass `--reencode` to re-run `encode.py` on frames that are already rendered, for example after an encoder change. It never re-renders.
- **Budget check.** After encoding, it checks each file's bitrate against the reference budget (Perpetua Coast: phone ≈ 670 kb/s, webm ≈ 1080 kb/s, mp4 ≈ 1630 kb/s, with 15 % headroom). A file over budget is marked `over_budget` in the status, and you report it. Don't hide it.
- **Failures.** A failed race is recorded and the next independent race continues. Report every failure explicitly.

A full film takes hours. In Claude Code, start the batch with the Bash tool's `run_in_background`, or detach it with `nohup … &` and keep the PID and log path. Watch progress with the Monitor tool or by reading `batch-status.json` and the frame count under `<out>/frames`. If the user wants check-ins while they're away, suggest `/loop`. (In Codex, use a heartbeat automation instead. The script sits at `~/.codex/skills/tg-render/scripts/` there.) Don't assume one foreground turn stays alive overnight.

## Report

Inspect `contact-sheet.png` and a phone-cut frame after encoding. Then report, for each race:

- the output path and film duration;
- the size and bitrate of each file, and whether any file is over budget;
- where the aid-pin data came from;
- how far it got: rendered, encoded, locally verified, or published.

To put a finished render on its course page, the user asks separately. Then run `.venv/bin/python scripts/flythrough/deliver.py <id> <out>`. It copies the four files and bumps `app/assets.py`. Commit on a branch and open a PR.

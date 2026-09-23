---
name: tg-render
description: Render one or more TrailGoat catalogue race flyovers by course name, including a race-name billboard, overhead runner-follow shots, verified aid-station pins, visual QA, and a resumable overnight batch. Use for TrailGoat 3D course video requests, not ordinary map screenshots.
argument-hint: <race name>[, <race name>...]
---

# TG-render

Turn catalogue race names into locally inspectable, encoded 3D flyovers using TrailGoat's existing Blender engine. One invocation may name one race or a batch. A render is not a deployment: do not run `deliver.py`, commit media, or publish without a separate request.

## Set up the machine (any computer)

1. **Checkout.** Use the current repository when it is TrailGoat. Otherwise try `$TRAILGOAT_REPO`, then `~/Desktop/Projects/TrailGoat`, then `~/TrailGoat`. If none exists, ask before cloning `gh repo clone Bookee2/trailgoat`.
2. **Current engine.** Run `git fetch origin` and confirm that `scripts/flythrough/` matches `origin/main` (`git diff --stat origin/main -- scripts/flythrough`). If it doesn't, stop and tell the user. The encoder changes over time (since 2026-09-22 the phone cut is encoded from the frames at crf 26, not re-encoded from `hero.mp4`), and a stale checkout gives oversized files. Never pull over someone's uncommitted work.
3. **Encoder venv.** Check that `.venv/bin/python -c "import imageio_ffmpeg"` succeeds. If it fails, and with the user's go-ahead, run `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt imageio-ffmpeg numpy`.
4. **Blender 5.2+.** Look in this order: `$BLENDER_BIN`, `/Applications/Blender.app/Contents/MacOS/Blender`, then `blender` on `PATH`. Export the one you find as `BLENDER_BIN` for the batch. If Blender is missing, say so and stop. You can't render without it, and installing it is the user's call.
5. **Storage.** At 1280×720, frames take about 1.6 MB each, so a 132 s film at 24 fps (3168 frames) needs about 5 GB under `out/`. Check free space before starting.

Then read `CLAUDE.md` / `AGENTS.md` if present, plus `scripts/flythrough/README.md`. Before editing, inspect `render.py`, `geo.py`, `run.sh`, `encode.py`, the nearest authored `shots/*.json` and `git status`. Don't overwrite existing shots or outputs.

## Resolve and prepare

1. Resolve every supplied name through `https://trailgoat.run/api/fuel/courses/search?q=...` (or the local app). Confirm the exact race, distance and course ID by fetching `/api/fuel/courses/{id}`. Never pick an ambiguous result; ask. Save a course JSON snapshot in the output directory. The renderer accepts its path or the ID.
2. For each course, use an authored `shots/{id}.json` when it suits. Otherwise start from the engine's planner and author a close, overhead film:
   - the opening shows the full race-name billboard and the start pin;
   - the runner is tracked with no dominant horizon;
   - the film ends on a local finish pull-back, not a distant whole-course view.

   Keep the full route covered, and use `--dry` to check the camera lints and map. Wild Florida's `shots/96.json` is one close-follow example, not a camera template for every course.
3. Keep catalogue aid stations when present. If they're absent, research the organizer's current course and aid information. Record the source and edition, reconcile station miles with the actual GPX, and add verified `[mile, label]` entries to the shot spec. One physical station visited twice may be one labeled pin. Never invent pins. If aid data can't be verified, say so and render without guessed stations.
4. Render full-resolution stills (`--stills`) at the opening, the billboard exit, representative follow legs, each aid pin, and the finish. Read the images yourself, checking label readability and frame edges, and fix bad framing before the expensive pass. A clean lint is necessary, but it doesn't replace looking.

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

- **One at a time.** It renders and encodes one course at a time through `scripts/flythrough/run.sh` (Blender, then `encode.py`). Never run simultaneous full renders on one machine.
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

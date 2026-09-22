---
name: tg-render
description: Render one or more TrailGoat catalogue race flyovers by course name, including a race-name billboard, overhead runner-follow shots, verified aid-station pins, visual QA, and a resumable overnight batch. Use for TrailGoat 3D course video requests, not ordinary map screenshots.
---

# TG-render

Turn catalogue race names into locally inspectable, encoded 3D flyovers using TrailGoat's existing Blender engine. One invocation may name one race or a batch. A render is not a deployment: do not run `deliver.py`, commit media, or publish without a separate request.

## Resolve and prepare

1. Locate the TrailGoat checkout. Use the current repository when it is TrailGoat; otherwise check `TRAILGOAT_REPO`, then the user's saved/local TrailGoat project. Read its `AGENTS.md` and `scripts/flythrough/README.md`. Inspect `scripts/flythrough/render.py`, `geo.py`, `run.sh`, `encode.py`, the nearest authored `shots/*.json`, and the current `git status` before editing. Do not overwrite existing shots or outputs.
2. Resolve every supplied name through the catalogue search endpoint `/api/fuel/courses/search?q=...` or the equivalent local catalogue. Verify exact race/distance identity and course ID by fetching `/api/fuel/courses/{id}`. Do not select an ambiguous result. Save a stable course JSON snapshot in the output directory; the renderer accepts its path or the ID.
3. For each course, use an authored `shots/{id}.json` when suitable. Otherwise use the engine's planner as a starting point and author a close, overhead film: full race-name billboard and start pin in the opening, runner tracking with no dominant horizon, local finish pull-back rather than a distant whole-course view. Keep the full route covered. Use `--dry` to inspect camera lints and map. The Wild Florida `shots/96.json` is a close-follow example, not a universal camera geometry template.
4. Preserve catalogue aid stations when present. If absent, research the race organizer's current course/aid information; record source and edition, reconcile station miles with the actual GPX, and add verified `[mile, label]` entries to the shot spec. One physical station visited twice may be one labeled pin. Never invent pins. If aid data cannot be verified, say so and render without guessed stations.
5. Render full-resolution stills at opening, billboard exit, representative follow legs, each aid pin, and finish. Inspect the images, including readability and frame edges; correct bad framing before starting the expensive pass. A clean lint is necessary but does not replace visual QA.

## Render and batch

Find Blender 5.2+ and the repo's `.venv/bin/python` with `imageio-ffmpeg`. Check storage for the estimated frame count and tell the user the expected duration based on a short local sample when possible. Build a JSON manifest (see below) with unique output directories, then run this skill's `scripts/batch_render.py` from the TrailGoat checkout. It renders and encodes one course at a time, writes per-course logs and an atomic status file, skips verified completed outputs, and resumes existing Blender frames after an interruption. A failed race is recorded and the next independent race continues; report all failures explicitly. Never run simultaneous full renders on one Mac mini by default.

For a long queue, launch it detached with `nohup` and retain the PID/log path; do not assume a foreground Codex turn will remain alive overnight. Check progress when feasible. If the user asks you to monitor or notify later, create a Codex heartbeat automation separately; this skill alone does not schedule follow-ups.

Manifest example (course IDs must be resolved and QA'd first):

```json
{
  "courses": [
    {"id": 96, "name": "Wild Florida 50k", "out": "out/wild-florida-50k"},
    {"id": 148, "name": "Perpetua Coast", "out": "out/perpetua-coast"}
  ]
}
```

Command: `python3 <skill>/scripts/batch_render.py --repo <trailgoat-checkout> --manifest <manifest.json>`. Use `--dry-run` to validate the queue without rendering. The script invokes `scripts/flythrough/run.sh`, which runs Blender then `encode.py`. Set `BLENDER_BIN` for a nonstandard installation. Output files are `hero.mp4`, `hero.webm`, `hero-phone.mp4`, `poster.webp`, and `contact-sheet.png`; inspect the contact sheet and phone crop after encoding. Report each race's output path, duration, aid-pin provenance, and whether it was rendered, encoded, locally verified, or published.

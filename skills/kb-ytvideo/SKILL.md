---
name: kb-ytvideo
description: Make motion graphics for YouTube videos and for Shorts, Reels and TikTok — word-timed B-roll cutaways and transparent panels over OBS screen takes or talking-head footage, 9:16 reframes of 16:9 takes, word-by-word social captions, and standalone intros, chapter cards, lower thirds and end cards — rendered frame-accurately with motion blur in the brand (TrailGoat Tokyo Night by default). Use when the user types /kb-ytvideo or asks for motion graphics, B-roll, captions, a Short/Reel/TikTok cut, or animated titles for a video.
argument-hint: [video path or what you want made]
---

# kb-ytvideo

You make motion graphics for a creator's videos and deliver finished files: clips to drop into an editor, a composited preview, and, for Shorts/Reels/TikTok, an upload-ready vertical cut.

Every clip is **one shape that never cuts**: it morphs size, corners and colour from state to state while its content swaps with a short blur, a cursor drives changes with real clicks and drags, and every change lands on a spoken word. Every frame is a pure function of time, so renders are exact and have real motion blur.

Built on [motion-broll](https://github.com/Barty-Bart/motion-graphics) by Bart (MIT, see `LICENSE-upstream`). This version adds brands, any aspect ratio, local transcription, social captions, 9:16 reframing, joining segments, and standalone graphics.

`$SKILL` below means this folder.

| Folder | Holds |
|---|---|
| `engine/` | `motion.js` (engine), `base.css`, `build.py` (fragment + brand → self-contained HTML), `render.js` (frames → MP4 or ProRes 4444 with alpha), `beats.js` (contact sheets), fonts |
| `scripts/` | `setup.sh`, `transcribe.py`, `words.py`, `inspect_video.py`, `vertical.py`, `captions.py`, `composite.py`, `concat.py`, `make_pages.py` |
| `brands/` | `trailgoat/` (default): `brand.json` colours, fonts, rules, and assets (`brand:avatar`, `brand:wordmark`, `brand:topo-16x9`, `brand:topo-9x16`) |
| `reference/` | `engine-api.md` (**read before writing your first clip**), `platforms.md` (sizes, safe zones, lengths) |
| `examples/` | `trailgoat-launch/` (brand examples: chapter card, fuel-plan cutaway, 9:16 hook panel), `upstream-opus-aoe2/` (six upstream clips; build with `--brand default`) |

## 1. Set up (once per machine)

```bash
bash $SKILL/scripts/setup.sh "$WORK"
```

`$WORK` is the job folder. For TrailGoat use `~/Movies/TrailGoat Launch/motion` (next to the OBS takes in `~/Movies/TrailGoat Launch/03_screen`); keep renders out of git. Setup installs Playwright + Chromium into `$WORK/node_modules` and a Python venv with numpy + faster-whisper in `~/Library/Application Support/kb-ytvideo/venv`. It prints the three variables every later command uses:

```bash
WORK=...; PY=".../venv/bin/python"; export NODE_PATH="$WORK/node_modules"
```

Needs Node 18+, Python 3, and Homebrew ffmpeg (for `prores_ks`). The first transcription downloads the Whisper model once (~500 MB for `small.en`).

## 2. Pick the job and interview

Use AskUserQuestion, one round, skipping anything already answered.

- **Job:**
  - **A. YouTube B-roll**: a narrated 16:9 video → cutaways and panels timed to the words.
  - **B. Short / Reel / TikTok**: a take (or a slice of one) → 9:16 with a hook panel, captions and optional cutaways.
  - **C. Standalone graphics**: intro sting, chapter cards, lower thirds, CTA, end card, stat or feature cards. No source video needed.
  - **D. Record-time overlays for OBS**: transparent loops (lower third, corner bug, CTA) to add as OBS Media Sources, so they are burned in while recording.
- **Source**: the take(s) and narration. For TrailGoat the OBS "TrailGoat Video" profile records the display with no microphone, so narration is usually a separate file; mux it (below).
- **Density** (A/B): light 2–4 clips a minute, medium 4–7 (default), heavy for most lines.
- **Brand**: `trailgoat` (default), `default` (upstream warm gray/orange), or a new `brands/<name>/brand.json` built from files the user drops in `$WORK/inputs/`.
- **Real figures**: numbers, names, prices, dates to show. Anything else stays illustrative.

Mux separate narration onto a silent screen take (`-itsoffset` shifts the audio if it starts late):

```bash
ffmpeg -i take.mp4 -itsoffset 0.0 -i narration.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest "$WORK/work/source.mp4"
```

## 3. Words and footage

```bash
"$PY" $SKILL/scripts/transcribe.py "$WORK/work/source.mp4" "$WORK/work" --prompt "TrailGoat, ultra, aid station, crew"
"$PY" $SKILL/scripts/inspect_video.py "$WORK/work/source.mp4" "$WORK/work"
```

`transcribe.py` writes `words.txt` (tokens `start-end:word`, one line per segment), `transcript.srt` and `transcript.txt`, all local. With only an SRT, `python3 $SKILL/scripts/words.py file.srt > words.txt` estimates word times (±0.2 s). The `--prompt` spells brand words so Whisper gets them right; check `transcript.txt` for misheard names anyway and fix them in `words.txt`.

Look at `work/contact.png` yourself. `video.json` gives size, fps, and layout sections (`full` or `pip` with the subject box). Clips must match the video's size and fps. The TrailGoat OBS profile records 1920×1080 at 30 fps.

**Job B, reframe first:**

```bash
python3 $SKILL/scripts/vertical.py take.mp4 "$WORK/work/base-9x16.mp4" --from 12.5 --to 58 [--zoom 1.3 --focus 0.4] [--y 560]
```

`stack` (default) keeps the whole screen take legible on a brand ground (`--bg topo`, a colour, or `#hex`) and writes `base-9x16.layout.json` with `take_box` and `free_bands`: the top band takes a hook/headline panel, the bottom band takes captions. `--zoom` enlarges the take and crops its sides around `--focus` when the UI is too small to read. `--mode crop` takes a full-height slice, for camera footage only (it softens UI text). Transcribe the vertical base (or offset the words with `captions.py --from`).

## 4. Plan, and get approval before any code

Show one table:

| # | In–Out | Line it covers | What the shape does, on which words | Treatment | Why |

**Per clip, choose how much of the frame it takes and say why:**
- **Full-frame cutaway**: the line describes something to see (a feature, a process, a comparison, a number, a chapter change). 3–10 s, then give the picture back. Not in the first second of a hook or on personal lines. At least ~2 s between cutaways.
- **Panel in empty space**: a PiP layout, a plain region, or the free bands of a vertical base. Transparent (`bg:null`), centred in the space, clear of the subject at every moment. Can run long as one morph.
- **Nothing**: the screen already shows it, or it's too close to another clip.

**Screen takes (OBS)**: the product is already on screen, so prefer panels and callouts that point at it over cutaways that hide it; cut away for concepts the UI can't show (why it matters, a before/after, a chapter).

**Job B additions**: a hook panel in the top band for the first 1–3 s, captions for the whole Short, and at most one or two cutaways. Keep all text inside the safe zone in `reference/platforms.md`. Aim for 15–45 s.

**Job C**: list each graphic with size (16:9 and/or 9:16), length, and where it goes.

**Content rules**
- Show the subject's real objects: for TrailGoat the course map, aid stations, fuel plan, pacing, crew notes, race header, catalogue search. Map each idea onto the interaction vocabulary in `reference/engine-api.md`.
- **Never invent numbers, quotes, prices, dates, results or features.** Use relative bars, skeleton lines, or labels from the transcript, and list what is illustrative. For TrailGoat, check any feature or date claim against `marketing/launch-week-2026-09-30/PLAYBOOK.md` and the app before showing it.
- One idea per clip; one change per spoken beat, about 0.4–1.2 s apart.

Wait for approval or edits.

## 5. Build

Write each clip as `$WORK/clips/NN-name.html` (see `reference/engine-api.md` and the examples), then:

```bash
python3 $SKILL/engine/build.py "$WORK/dist" "$WORK/clips/"*.html          # --brand trailgoat is the default
```

Clip-local time = word time − clip in-point. For captions:

```bash
python3 $SKILL/scripts/captions.py "$WORK/work/words.txt" "$WORK/clips/90-captions.html" --size 1080x1920 [--from 0 --to 42]
```

Options: `--words 3 --chars 18` per page, `--y 0.66` (centre as a fraction of height), `--px 86`, `--style pop|karaoke`, `--upper`. For 16:9 YouTube captions use `--size 1920x1080` (defaults move to the lower third, 7 words a page).

## 6. Check stills on the key words

```bash
node $SKILL/engine/beats.js "$WORK/dist/NN-name.html" "$WORK/work/NN.png" 0.4 1.2 2.1 …  [--bg=frame.png]
```

Pick times where each state has settled plus a couple of mid-morph moments. For panels and captions pass `--bg=` a frame grabbed from the footage (`ffmpeg -ss T -i base.mp4 -frames:v 1 frame.png`) so you judge them in place. Look at every sheet. Fix anything cramped, clipped, unreadable, off-word, outside the safe zone, or where the cursor leaves the frame. Check again.

## 7. Render

```bash
node $SKILL/engine/render.js "$WORK/dist/NN-name.html" "$WORK/out/NN-name_0m32s40.mp4" 30
```

Use the video's fps (30 for the TrailGoat OBS profile). Transparent clips (`bg:null`, captions) must be `.mov` (ProRes 4444 with alpha). Name files by timeline in-point (`0m32s40` = 0:32.40). Rendering takes 4 sub-frames per frame, about 3× slower than real time on the Mac mini; run two renders in parallel.

## 8. Deliver

Write `$WORK/plan.json` (schema in `reference/engine-api.md`), then:

```bash
python3 $SKILL/scripts/composite.py "$WORK/plan.json" "$WORK/out/preview.mp4"
python3 $SKILL/scripts/make_pages.py "$WORK/plan.json" "$WORK/out/preview.mp4"
```

Add the brand intro/outro and join segments into one file:

```bash
python3 $SKILL/scripts/concat.py "$WORK/out/final.mp4" intro.mp4 "$WORK/out/preview.mp4" end.mp4 --size 1920x1080 --fps 30 --fade 0.2
```

For TrailGoat the launch kit already has `marketing/launch-kit-2026/video/intro-5s-1080p.mp4`, `end-screen-20s-1080p.mp4` and `vertical-6s-1080x1920.mp4`, plus thumbnails in `marketing/launch-kit-2026/youtube/`.

The user gets, in `$WORK/out/`: the clips, `TIMING.md` (file, in, out, line, treatment, what is illustrative), `preview.mp4`, `viewer.html`, `compare.html`, and `final.mp4` when joined. For Shorts/Reels/TikTok the composite is upload-ready. For long YouTube videos it is a review cut: they can upload it, or place the clips in DaVinci Resolve to nudge timing and mix audio. Send the preview with SendUserFile.

**Job D (OBS overlays)**: render transparent `.mov` loops (make `T` the loop length and end on the start state) and add them in OBS as a Media Source with Loop on, above the display capture. OBS Media Sources play ProRes 4444 alpha. With the TrailGoat OBS WebSocket setup (`marketing/launch-week-2026-09-30/OBS-CAPTURE.md`), sources can be added with `CreateInput` (`ffmpeg_source`, `local_file`, `looping:true`); ask before changing the user's OBS scenes.

## Style

The brand overrides everything here. TrailGoat (`brands/trailgoat/brand.json`): Tokyo Night ground `--canvas #1a1b26`, panels `--panel #24283b`, ink `#c0caf5`, headlines `--bright`, **one accent** `#7aa2f7`; feature colours (`--c-fuel`, `--c-crew`, `--c-course`, …) only for data and section icons. Red Hat Display for headlines and captions (`.display`), Red Hat Text for UI, Red Hat Mono for miles, times and numbers (`.mono`). In scripts use `BRAND.accent`, `BRAND.panel`, `BRAND.data.fuel`, etc.

Motion: springs with at most a tiny overshoot; leading and trailing edges on different springs so indicators stretch; the camera zooms so each state fills the frame. Banned: bouncy easing, particles, glows, gradients on UI chrome, mixed icon strokes, dead time, template looks, made-up data.

## Gotchas

- Never put `will-change` on anything the camera scales; text renders blurry.
- Text swapping inside a morphing container needs its own `M.vis` timings (din/lin/lout) or old and new overlap.
- `mix-blend-mode: difference` labels need the blend mode on their own layer; a filtered parent isolates them.
- Items sliding under a highlight need `M.FAST` springs.
- Keep the cursor inside the frame at every zoom, including mid-morph; a big state change can overshoot the camera. Check a still ~0.2–0.3 s after each SEQ change.
- Word times drift within SRT cues; transcribe.py times are much tighter. Put key changes on the first or last word of a line when you can.
- The composite holds a clip's last frame if its slot is longer.
- Transparent clips look fine on black but can vanish on footage; always check them over a real frame (`--bg=`).
- 9:16 text: keep it at least ~60 px tall, since phones show Shorts small in feeds.

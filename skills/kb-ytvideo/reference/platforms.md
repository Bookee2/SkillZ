# Platforms: sizes, lengths and safe zones

Check each platform's current creator docs before a campaign; limits change. These are working defaults.

| Output | Size | fps | Notes |
|---|---|---|---|
| YouTube long form | 1920×1080 (16:9) | match the take (TrailGoat OBS: 30) | Chapters come from timestamps in the description; chapter cards should match them. End screen elements need the last 5–20 s. |
| YouTube Shorts | 1080×1920 (9:16) | 30 | Keep it short; a hook in the first 1–2 s. |
| Instagram Reels | 1080×1920 (9:16) | 30 | The grid crops the cover to a centred 4:5 or 1:1; keep the title in the middle. |
| TikTok | 1080×1920 (9:16) | 30 | |
| Instagram / Facebook feed | 1080×1350 (4:5) | 30 | Use `vertical.py --size 1080x1350`. |

## 9:16 safe zone

The apps draw their own UI over the video: account name and caption text at the bottom, like/comment/share buttons down the right, tabs or search at the top. Exact sizes differ by app and device, so use conservative margins that clear all three:

| Edge | Keep text and key visuals clear of |
|---|---|
| Top | 220 px |
| Bottom | 420 px |
| Right | 140 px |
| Left | 60 px |

That leaves roughly x 60–940, y 220–1500 at 1080×1920. `captions.py` defaults (centre at 0.66 H ≈ 1267 px, 8% side padding) and the `vertical.py` stack layout (take at y 556–1162 for a 16:9 source) sit inside it; a hook panel belongs in the top band below y 220.

## 16:9 safe zone

Keep text 5% in from each edge (96 px × 54 px at 1080p). Leave the bottom-right clear in the last 20 s for end-screen elements, and the top-right when a channel watermark is shown.

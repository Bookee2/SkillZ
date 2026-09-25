# Lessons (hard-won, keep adding)

## Testing in the Claude browser pane
- The pane is often hidden: `document.hidden` is true, requestAnimationFrame and
  IntersectionObserver don't fire, screenshots can be a frame stale (take two).
- Verify without animation: switch the page to calm/reduced-motion so demos paint
  their rest frame; call render functions directly; read WebGL back with
  `gl.readPixels`; snapshot a WebGPU canvas with `drawImage` into a 2D canvas in
  the same task; expose small debug hooks (`window.__tgFields`, `__tgGPU`).
- Isolate a section for screenshots by hiding the ones before it.
- YouTube and any video page autoplay audio in the pane: pause and mute right
  after navigating, then leave the page.
- The pane can't open local files under ~/Documents; serve over http instead.
- A local server without a charset shows "Â·" for "·"; the artifact wrapper adds
  one. Put `<meta charset="utf-8">` + viewport meta in local/offline copies.
- Local servers need byte-range support for `<video>` seeking.

## Layout
- A 16:9 box with `min-height` transfers that height into a min *width* through
  `aspect-ratio` (380px → 675px) and widens the page on phones. Give it
  `width: 100%`; give grid columns `minmax(0, 1fr)`.
- Absolute panels inside an already-centred column must not add a viewport
  offset (`calc((100vw - 1140px)/2)`) — it double-shifts over the copy on wide
  screens. Measure overlap at 1130/1440/1920/2560 and 375 px.
- A component's own `display` beats the `hidden` attribute unless the site has
  `[hidden]{display:none!important}` — add `.x[hidden]{display:none}`.
- Negative margins that pull a strip up can land it on a caption; check stacking
  on phones.
- Mask/fade canvases under text; keep text readable first.

## Particles and GPU
- One draw call per field; budget dots by width (e.g. 9k/6k/3k).
- Theme colours: read CSS tokens (normalise any colour string through a canvas
  2D fillStyle), rebuild shapes on theme change.
- Ink outlines vanish on dark grounds: remap near-black pixels to a mid tone.
- Additive blending washes out in dark themes at high counts; lower alpha.
- WebGPU trails: accumulate in rgba16float; 8-bit leaves ghosts.
- WebGL2 GPGPU: `precision highp sampler2D`, half-float fallback.
- A canvas measured before its CSS applies starts at 300×150: rebuild on resize.
- Only create SplitText (GSAP) after `document.fonts.ready`.

## Scroll and transitions
- `overflow: hidden` on an ancestor freezes `view()` timelines; use `overflow: clip`.
- Scroll-driven progress: map the viewport middle between step centres, ease
  through the middle 40%, lerp toward the target each frame.
- View-transition names must be unique on each page at capture; set them only on
  the clicked element; a name shared by a class on both pages aborts the
  transition.

## Video heroes
- iOS Low Power Mode refuses autoplay: fall back to the poster, hide
  `::-webkit-media-controls-start-playback-button`, retry play on first tap.
- A paused first frame fires requestVideoFrameCallback at time 0: only update
  data readouts while the video is actually playing.

## Data and copy
- Use an up-and-down course for pacing stories (net-downhill hides the point).
- Tidy catalog names for captions (drop year, "Endurance Run", repeated distance).
- Label collisions on phones: merge near labels, fewer ticks, greedy placement.
- Caption numbers from one source (two DEM readings gave 12,530 vs 12,533 ft).

## Process
- The user reacts best to live demos, one page, real data; round two went deep
  on what they loved (particles) and parked what they were lukewarm on.
- Keep an index of every technique linking to its demo so options can be compared.
- For heavy offline/remote work keep a PROGRESS.md and, if asked, an hourly
  wake-up (CronCreate) that resumes from it.

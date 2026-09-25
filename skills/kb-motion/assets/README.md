# Assets

Proven code to start from. Copy and adapt; don't link to it.

- `engine/` — code as shipped on trailgoat.run (Sep 2026).
  - `tg-field.js` — WebGL dot-field engine: DotField, shape samplers (text, image,
    profile, route, dust), `cycle()`, `loader()`, GPU `swarm()`, `govern()`.
    Remap the TOKENS table at the top to the new product's CSS variables.
  - `home-motion.js` — video-synced readout, the two-way Leadville story engine,
    signal-drop phone, sand signatures, ridgeline. Data is embedded at the top.
  - `course-topo.js` — contours that rise from terrain tiles around a route.
  - `courses-field.js` — header field cycling featured items + cross-document
    view transition from a card to its page.
- `demos/` — the proposal page's modules (lab + toolbox). `lab-modules.js`
  starts with shared helpers (`$`, `clamp`, `rafLoop`, `register` governor,
  token readers) that the rest assume; `assemble.py`/`build.py` show how the
  page was assembled from parts with data and images inlined.

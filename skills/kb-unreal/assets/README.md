# Assets: code to start from

Copy and adapt into the owning repo; don't import from the skill folder at
runtime (the installed copy changes when the skill updates).

- `run_remote.py` — run a Python file in a live Unreal editor over Python
  remote execution (macOS loopback multicast patch; selects the editor by
  `UNREAL_PROJECT_ROOT` / `UNREAL_PROJECT_NAME`; copies the script into
  `<Project>/Saved/CapraStudy`). Canonical copy:
  `~/Desktop/Projects/Caprastudios/unreal/run_remote.py`.
- `camera_paths.py` — PCHIP keypoint orbits, a decaying shake and the
  powers-of-ten dive, in a local subject frame (works far from the origin).
- `render_mrq.sh` — the out-of-process Movie Render Queue wrapper (guard,
  poll, kill the hang, kill CrashReportClient, trim).
- `niagara_showcase.py` — a dark stage with one camera cut per Niagara effect,
  each fired by a life-cycle section, plus MRQ check/720 queues (the Niagara
  Examples test reel).
- `extract_uasset_thumbs.py` — cut the preview images out of .uasset files
  for a catalogue without rendering.

The full working pipelines are the best templates; open them before writing
new code:

| Need | Start from |
|---|---|
| Block swarm into models, dissolve, lights-off | `Caprastudios/unreal/capra_blocks_{prep,build,seq}.py` |
| Swarm in a far-away world, explosion, wipe, dive | `Caprastudios/unreal/capra_space_{build,seq}.py`, `capra_space_render.sh` |
| End screen with overlay labels and card bays | `Caprastudios/unreal/capra_outro_{seq,post}.py` |
| Box/marker drawn over frames from per-frame projected bounds | `Caprastudios/unreal/capra_space_box.py` (+ `capra_space_dive.json` written by `capra_space_seq.py`) |
| Niagara effects fired from Sequencer, test reel | `assets/niagara_showcase.py` |
| Sound mixes from the Mixkit library (+ synth boom) | `Caprastudios/unreal/capra_sfx_library.py` |
| Animated character into blocks | `Intro_motion/Scripts/{blender_prep_blocks,build_swarm,build_seq3}.py`, `TrailGoatElectricDream/Scripts/blender_bake_cheer.py` |
| Character run through a world, cut to music | `TrailGoatElectricDream/Scripts/{import_goat,import_moves,make_trail,clear_path,build_canyon}.py` |
| 150k-particle film | TrailGoat `studio/particle-engine/` |
| Cesium real-terrain film | `KB SS/TrailGoat-Studio/WSER/Scripts/build_scene.py`, `render_night.sh`, `assemble_google.py` |
| Blender flyover (the quality bar) | TrailGoat `scripts/flythrough/` (+ `/tg-render`) |
| URL / caption overlays projected through the camera | `Intro_motion/Scripts/post_url.py`, particle-engine `post/captions_*.py` |
| Music mux at −14 LUFS | `Intro_motion/Scripts/mux_music.sh` |
| Reading a sample by script | `Caprastudios/unreal/run_remote.py` + the probe scripts in each sample's `Saved/CapraStudy/` |

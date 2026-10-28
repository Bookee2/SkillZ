# Pipeline: machine, control, render, encode, deliver

## Machine and tools
- Mac mini M5 Pro, 64 GB, Metal. Heavy work lives on the external SSD
  **KB SS** (`/Volumes/KB SS`); new projects go under
  `KB SS/Capra Studios/Unreal` (Capra) or `KB SS/TrailGoat-Studio` (TrailGoat).
  DDC/Zen caches are symlinked to the SSD. The Epic launcher's VaultCache
  refills by ~100 GB per big sample download.
- Unreal 5.8.3 (CL 58210709, compatible 5.8.0 / 55116800):
  - editor: `/Volumes/KB SS/Unreal Engine/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor`
  - headless/render: `…/Engine/Binaries/Mac/UnrealEditor-Cmd`
  - remote execution module: `…/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py`
  - plugins available: Avalanche (Motion Design, cloners/effectors, Text3D),
    MovieRenderPipeline (+ mask pass), NiagaraFluids/MRQ/Nanite, PCG (+ GPU,
    Biome, Primitives), Water, Volumetrics, Mover, Toolsets (Editor, Niagara,
    PCG, Sequencer, AnimationAssistant…), ModelContextProtocol (MCP),
    RemoteControl, OpenColorIO, nDisplay (Windows/Linux only).
- Blender 5.2 `/Applications/Blender.app/Contents/MacOS/Blender` (ships numpy;
  headless `-b -P script.py -- args`, `--python-exit-code 1`).
- ffmpeg on PATH (Homebrew); venvs: TrailGoat `.venv` (numpy, Pillow,
  imageio-ffmpeg) for Capra post and sound; kb-ytvideo venv
  `~/Library/Application Support/kb-ytvideo/venv` for ParticleLab post.
- Export `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` in
  render scripts that need the Metal toolchain.

## Driving the editor (pick one per project)
1. **Python remote execution** (Capra): `Caprastudios/unreal/run_remote.py
   <script.py>` with `UNREAL_PROJECT_ROOT`, `UNREAL_PROJECT_NAME` (the
   .uproject's base name) and optionally `UNREAL_REMOTE_GROUP` /
   `UNREAL_COMMAND_PORT`. It's Epic's `remote_execution.py` patched for macOS
   loopback multicast (239.0.0.1:6766, TCP 6776; a second editor can use
   239.0.0.2:6767 / 6777), copies the script into `<Project>/Saved/CapraStudy`
   (avoids the Desktop permission prompt), and selects the editor by project.
   Wait until a probe script answers before sending real work.
2. **Remote Control HTTP** (TrailGoat projects): `Scripts/ue <script.py>` →
   `PUT http://127.0.0.1:30010/remote/object/call` on
   `/Script/PythonScriptPlugin.Default__PythonScriptLibrary`
   `ExecutePythonCommand`; WebSocket fallback on 30020 (`rcws.mjs`); results
   written to an OUT file. Remote Control security settings are per project.
3. **MCP** (`http://127.0.0.1:8000/mcp`, `bAutoStartServer=True`): toolsets
   for Editor (`CaptureViewport`), Niagara (`unreal.ToolsetRegistry.
   execute_tool('NiagaraToolsets.NiagaraToolset_System', tool, json)`), PCG,
   Sequencer, Blueprint graphs. The MCP sandbox can't `import unreal`; call
   one tool at a time.
4. **Headless build**: `UnrealEditor-Cmd <proj> -ExecutePythonScript="<script>
   <stages>" -unattended -nosplash -log` (or `-run=pythonscript
   -script="…"`); end scripts with `_os._exit(0)`.

**Launch an editor for scripting without touching the project's config:**
```
"$UE" "<project>.uproject" \
  -EnablePlugins=PythonScriptPlugin,SequencerScripting,EditorScriptingUtilities,MovieRenderPipeline \
  "-ini:Engine:[/Script/PythonScriptPlugin.PythonScriptPluginSettings]:bRemoteExecution=True" \
  "-ini:EditorPerProjectUserSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False" \
  -nosplash > /dev/null 2>&1 &
```
Add `-DisablePlugins=ICVFX` for ICVFX. Logs: `~/Library/Logs/Unreal Engine/
<Project>Editor/<Project>.log`. If the log stalls at "pre map load", a modal
dialog is up (screenshot the app with computer-use and dismiss it). Quit with
`unreal.SystemLibrary.quit_editor()`; to discard changes first,
`EditorLoadingAndSavingUtils.new_blank_map(False)`.

**Projects from samples:** APFS clone on the same volume,
`cp -c -R "<Sample>" "<NewName>"` (instant, no extra space), keep the
.uproject's original file name so shipped binaries still match, then remove
anything the sample re-applies on load (switchers) in the clone.

## Movie Render Queue (always out of process)
- Build saved `MoviePipelineQueue` assets from the sequence script: Deferred
  pass, PNG `f_{frame_number}` zero-padded to 4, output directory on KB SS,
  `override_existing_output`, TSR with 1 spatial and N temporal samples (2 for
  checks, 4 for 720p drafts, 8 for finals), `engine_warm_up_count` 32 (90 for
  runtime PCG, 900 for Cesium), `render_warm_up_count` 16; check queues use
  `output_frame_step` 15 or 30; resume queues use a custom playback range;
  `MoviePipelineGameOverrideSetting` for cinematic quality where the level's
  GameMode interferes. Reuse queue assets (`delete_all_jobs()`), never
  delete-and-recreate.
- Pad the sequence with one spare frame (playback end = N + 1).
- Render script pattern (`Caprastudios/unreal/capra_space_render.sh`,
  `capra_render.sh`; `assets/render_mrq.sh` in this skill is the generic one):
  refuse to start if another render runs → `rm -rf` the frames folder →
  `caffeinate -is "$UE_CMD" "<proj>" <map> -game -MoviePipelineConfig=<queue>
  -windowed -resx=1280 -resy=720 -unattended -nosplash -NoLoadingScreen -log
  -stdout -FullStdOutLogOutput -notexturestreaming -EnablePlugins=…
  "-ini:Engine:[…PythonScriptPluginSettings]:bRemoteExecution=False" > log &`
  → poll for the last real frame (detect early death) → sleep 20–45 s →
  `kill -9` the render → `pkill -9 -x CrashReportClient` → trim extras.
- Sharing the Mac with a Blender batch: `render_films.sh` freezes it with
  `kill -STOP` for the length of the Unreal render and resumes it with
  `kill -CONT` from a trap (it carries on exactly where it was).
- Close the project's editor first; pause other heavy editors
  (`kill -STOP <pid>`, resume with `kill -CONT`).
- Nightly/unattended: `TrailGoat-Studio/render_night.sh` (queue list,
  watchdog minutes, black/white frame check), launchd one-shots
  (`hero_4k_once.sh`); a launchd agent probably can't read `~/Documents`.

## Timings measured on this Mac
| Piece | Setting | Speed |
|---|---|---|
| Capra block intro | 720p, 4 samples | ~42 min / 301 frames (~8 s/frame incl. load) |
| Capra block intro | 4K, 8 samples | ~2 h 20 min / 300 frames |
| Capra end screen | 720p / 4K | ~48 min / ~4 h 35 min (600 frames) |
| Capra space intro | 720p, 4 samples | ~35 min / 450 frames (~4.7 s/frame) |
| Capra space checks | every 15th frame, 2 samples | ~5 min |
| TG blocks | 720p / 1080p / 4K | ~3 / ~9 / 17–27 s per frame |
| Canyon run | 720p / 1080p | ~1 / 3–15 s per frame; 4K ~4 h |
| ParticleLab | 960×540 1 sample / 1080p 8 | ~3 min / 5–8 min per film |
| Blender flyovers | 720p Eevee | 0.6–0.9 s/frame |
| Films ident (ParticleLab, 150k ×2 + fog) | checks every 6th frame, 2 samples / 720p 4 samples | ~9 min / 11.6 min (121 frames; ~5 min is startup and shaders) |
| Editor open | big sample first open | minutes to an hour (Nanite + shaders) |
| Petit Ridge land flyover (4 km Nanite terrain, 292k Nanite trees, Lumen HWRT) | 720p, 4 samples / checks every 48th | 0.86 s/frame (1,921 in 27.5 min) / ~7 min |

## Encode and post (ffmpeg)
- Master from frames: `ffmpeg -framerate 30 -i f_%04d.png -frames:v N
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart`
  (crf 18 for 720p drafts, 16 for 1080p, 14 for 4K).
- Mux sound: `-map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k|256k -shortest`.
  Music: `loudnorm=I=-14:TP=-1:LRA=11`.
- 1080p preview of a 4K: `-vf scale=1920:-2:flags=lanczos -crf 19`.
- Alpha: ProRes 4444 `-c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le`.
- Contact sheets: `hstack`/`vstack` of chosen frames, or `select=…,tile=4x3`.
- Web/phone: encode the phone cut from the frames, not from the master;
  serve with byte ranges (206) for iPhone.
- Overlays: Pillow RGBA frames + `overlay=shortest=1,format=yuv420p`.

## Delivery and storage
- Repo `output/` (git-ignored) for MP4s and contact sheets; frames on KB SS
  (`KB SS/Capra Studios/Unreal/<Project>/…_frames`,
  `KB SS/TrailGoat-Studio/Renders/…`); delete frame folders once the MP4 is
  checked. Deliverable names: `NN_What_length_shape_vN`.
- SendUserFile for drafts (~15 MB limit; 15 s 720p ≈ 19 MB went through);
  iCloud `~/Library/Mobile Documents/com~apple~CloudDocs/TrailGoat Videos` for
  big files and phone review; `Caprastudios/scripts/unreal-preview.mjs` serves
  `output/unreal/` with byte ranges on the LAN.
- Final for YouTube: upload 4K (better encoding ladder even when watched at
  1080p).

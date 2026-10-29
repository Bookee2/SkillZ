# Lessons (hard-won, keep adding)

Each line: what went wrong → the fix. Grouped by where it bites.

## Unreal Python API
- `unreal.Rotator(a, b, c)` is (roll, pitch, yaw) → always use keywords.
- A Rotator rolls before it yaws (a tilted plate leaned into the wall) →
  `MathLibrary.compose_rotators(rot(yaw=…), rot(roll=…))`.
- Editor Python keeps globals between exec calls → a commented-out assignment
  silently keeps its old value; write scripts that set everything.
- Run `ast.parse` on a script before sending it; delete stale logs first.
- Blueprint variables aren't in `dir()` → `get_editor_property('Title Text')`.
- Struct properties sometimes aren't attributes → use
  `get_editor_property('parameter_name')` (e.g. MPC CollectionScalarParameter).
- `create_asset` returns None after deleting a loaded LevelSequence or
  MoviePipelineQueue → reuse the asset (strip bindings/tracks,
  `delete_all_jobs()`). UE 5.8 lacks `MoviePipelineQueueFactoryNew` →
  `create_asset(name, path, unreal.MoviePipelineQueue, None)`.
- `InstancedStaticMeshComponent` has no `get_static_mesh()` → `.static_mesh`.
- Custom-data per instance in one call (a loop hung 10+ min).
- Long Unreal Python runs launched headless need `_os._exit(0)` at the end (a
  graceful quit hangs on a dialog).

## Sequencer
- **Close Sequencer before saving or reading actor values**
  (`LevelSequenceEditorBlueprintLibrary.close_level_sequence()`): a level was
  saved with the lights keyed off and the first render was black for 5 s.
  Assert lights > 0 before a render.
- Transform channels carry suffixes (`Location.X_12`) → match the prefix.
- Float and double channels take `MovieSceneKeyInterpolation`.
- An empty transform section evaluates to scale 0 → NaN view, transparent PNGs
  → key scale 1.
- **Visibility channel: True = visible** (the property is `bHiddenInGame`).
- Camera-cut binding: `seq.get_binding_id(binding)`.
- MPC values must be keyed in the sequence (asset defaults didn't reach the
  `-game` render). Key time-like params (T) every frame — two keys make an
  S-curve.
- Per-segment smoothstep camera stops at every key (Kris: "bump") → one PCHIP
  curve per channel. Catmull-Rom overshoots.
- Run the `level` and `sequence` build stages together (level destroys the
  camera); `queue` only with `sequence`.

- **MPC and material-parameter section keys take TICK frames, not display frames** (Petit Ridge, 2026-10-28):
  `MovieSceneMaterialParameterCollectionTrack` / `MovieSceneComponentMaterialTrack` sections'
  `add_scalar_parameter_key(name_or_MaterialParameterInfo, FrameNumber, value[, layer, asset])` have no time-unit
  argument, so `FrameNumber(f)` at 24 fps lands at f/24000 s — every key in the first 0.08 s and the render holds
  the end values (no lot-line glow, no data layer, no leaf-off). → `FrameNumber(f * tick_per_frame)` (×1000 at
  24 fps / 24000 tick; WSER's build_scene.py already did ×1000). Transform/float channels take
  `MovieSceneTimeUnit.DISPLAY_RATE` and are fine. Read keys back and check their times, not just their values.
  **The reverse bites too**: channel `add_key` (bool visibility, float, transform) defaults to display frames, so
  carrying the ×1000 over put the cabin's "show" key at frame 1,105,000 and it never appeared (caught on 4K test
  frames, Petit Ridge final). Sections' `add_*_parameter_key` → ticks; channels' `add_key` → display frames.
- Component material tracks in 5.8: `track.set_material_info(ComponentMaterialInfo(material_slot_index=…))`, and the
  section's key wants `unreal.MaterialParameterInfo(name, MaterialParameterAssociation.GLOBAL_PARAMETER, -1)`.
- Megascans foliage master: `Albedo Tint Leaves`/`Albedo Controls Leaves` only apply with the static switch
  `Split Albedo Controls` on (it's off in the Hornbeam MIs) → set the plain `Albedo Tint` / `Albedo Controls`.

## Rendering (Movie Render Queue)
- In-editor MRQ (PIE executor) crashed at Finalize → always render out of
  process: `UnrealEditor-Cmd <proj> <map> -game -MoviePipelineConfig=<queue
  asset>` (projects with their own C++ module, e.g. Electric Dreams: use the
  `UnrealEditor.app/Contents/MacOS/UnrealEditor` binary with `-game` — `-Cmd`
  can't load the module).
- The `-game` render hangs or crashes after the last frame → pad the sequence
  by one spare frame, wait for the last real PNG, `kill -9`, trim extras.
- Every crashed render leaves a CrashReportClient at 99% CPU (4K slowed from 17
  to 27 s/frame) → `pkill -9 -x CrashReportClient` after each render.
- **Don't time a final from stepped check frames**: every 192nd frame at 4K took ~30 s each (the camera jumps
  seconds, so virtual shadow maps, Lumen and TSR history rebuild every frame); the same scene rendered
  continuously ran 4.4 s/frame (Petit Ridge, 508k Nanite trees, 8 samples). Time a short continuous run.
- A queue's custom playback range was ignored (v1 rendered the no-cabin pass from frame 0) → trim the duplicated
  sequence's own `set_playback_start/end`; frames keep their absolute numbers.
- **A two-render reveal doesn't need two full renders**: hide the object in the main pass until just before the
  reveal (a visibility key ~1 s ahead, while post still shows the other pass, so Lumen settles on it) and render the
  object-free pass only over the seam. Petit Ridge 4K: 141 frames instead of ~1,240.
- The render process answers Python remote execution (a quit killed a render)
  → launch renders with `-ini:Engine:[/Script/PythonScriptPlugin.
  PythonScriptPluginSettings]:bRemoteExecution=False`; never send remote
  Python during a render.
- `pkill caffeinate` doesn't kill the wrapped job; an orphan's `rm -rf` wiped a
  live 4K at 543/600 → kill the whole tree, `pgrep` before starting, render
  scripts refuse to start if one runs.
- Lumen gives green first frames even with warm-up → render a 1 s pre-roll and
  drop it; add `MoviePipelineGameOverrideSetting` (the level's GameMode gave
  green, low-quality frames); auto-exposure speed 20 so cuts don't go black.
- Physical-camera manual exposure gave NaN frames → histogram metering with
  min = max EV100, or a camera post-process exposure bias.
- Resume a dead render with a queue using a custom playback range from the
  next frame, render to its own folder, copy in, check the join (hstack the
  frames around it).
- `-game` ignores `-LOG=` → `-stdout -FullStdOutLogOutput > file`.
- Camera actors' lens meshes and stray `SM_MatPreviewMesh` render as black
  spheres → hide them; never set CameraProxyMesh to None (crash).
- MRQ alpha drops additive particles once opaque geometry exists → composite
  RGB only.
- **WPO particle ISMs vanish whenever the world origin is off screen** (TrailGoat
  Films ident, 2026-10-26: no particles for the first 2.2 s, then all of them as
  the camera swung round to face the origin). UE5 culls every ISM instance on the
  GPU by its own bounds, and instances parked at the origin at scale 0.0001 have
  bounds there no matter where the WPO moves them; `max_world_position_offset_
  displacement` and far-off dummy instances don't help. Fix: a copy of the quad
  mesh with `positive/negative_bounds_extension` of ±60,000 cm, instances at
  scale 1, and the WPO returning `o - WorldPosition` (the target minus the
  vertex's own position). Earlier openers got away with it because their camera
  always faced the origin.
- The Path Tracer at 960×540 64 spp untiled **kernel-panicked the Mac** →
  never run it untiled; low spp, unattended only.
- Claude Code background tasks die after ~30 min → for long jobs use
  `nohup … & disown` and poll, or the harness's background mode with a
  completion check.
- Check renders: render every 15th/30th frame first (`output_frame_step`) and
  read them; motion problems need the camera numbers traced offline.

- `MoviePipelineOutputSetting.use_custom_playback_range` + `custom_start_frame`/`custom_end_frame` set from
  Python on a saved queue did NOT restrict the render (Petit Ridge reveal pass rendered from frame 0) → give the
  pass its own sequence whose playback range is the beat (`set_playback_start/end`), or let the render script stop
  at the last frame you need. Frame 0 of an out-of-process render can come out with unwarmed reflections (brown
  water) even with 96 warm-up frames → replace it with frame 1 or start the cut a few frames in.
- Speed reference: 4 km Nanite terrain + 292k Nanite Hornbeam instances + Lumen HWRT at 720p, 4 temporal samples:
  **0.86 s/frame** on the M5 Pro (1,921 frames in 27.5 min), much faster than the forest's size suggested.

## Editor, levels, World Partition
- `AutomationLibrary.take_high_res_screenshot` from a background editor never wrote its file (Petit Ridge,
  2026-10-28) → for look stills build a tiny LS_Look (one 1-frame camera-cut shot per viewpoint) and render it
  with MRQ out of process: four 720p stills in 65 s including startup.
- Never `load_level` a map duplicated/created in the same session (fatal "Old
  world not cleaned up") → duplicate, save, quit, relaunch with the map.
- Passing a map on the editor command line sometimes fails with "filename ''
  is not within…" (a modal dialog blocks startup) → omit it and use
  EditorStartupMap, or `load_level` after start; dismiss dialogs via
  computer-use if the log stalls at "pre map load".
- `-EnablePlugins=` with a wrong plugin name (e.g. MovieRenderPipelineSettings)
  also blocks startup on a dialog.
- World Partition: scripted edits need `actor.modify()`, `comp.modify()` then
  `save_dirty_packages(True, True)` — visibility set without modify() reloaded
  hidden. Actors that must be on screen during fast camera moves need
  `is_spatially_loaded=False`.
- Samples with switchers (Cassini's BeamMeUp) re-apply their state on load →
  remove the switcher in your clone.
- Rooms/maps that rebuild on load mark themselves dirty → `new_blank_map(False)`
  before loading the next one.
- To watch the editor viewport live while scripting (fastest lighting loop):
  `UnrealEditorSubsystem.set_level_viewport_camera_info(...)`, click empty space
  in the viewport with computer-use to make it redraw, then `app_screenshot`.
  With two Unreal editors open, window tools target the first process (both
  share a bundle id) — close or pause the other.
- `take_high_res_screenshot` handles one request per frame; batching several
  hangs it; it fails or fires late while shaders compile or when the editor is
  in the background → one per call, wait for the file, `bThrottleCPUWhenNot
  Foreground=False`; or render stills with MRQ instead.
- A modal "check out and save" prompt blocks remote Python → restart the
  editor, Don't Save.
- First open of a big sample builds Nanite meshes and shaders for a long time
  (Titan: 13.8 GB RSS, all cores, editor unresponsive) → don't render
  meanwhile; pause it with `kill -STOP <pid>` and resume with `kill -CONT`.

## Large worlds (LWC)
- ISM `add_instances(..., world_space=True)` with instances at (0,0,0) put
  13,752 blocks at the world origin, 2,450 km from the platform → always local
  space (`False`) with instances at the actor's origin.
- Do WPO maths in actor-local cm and transform the vector Local → World;
  position-based masks via TransformPosition World → Local.
- **Never key a camera in world space far from the origin.** The Python
  `add_key` on a transform's MovieSceneScriptingDoubleChannel rounds values
  through a float: at Z = −245,440,000 cm every height snapped to 16 cm steps,
  so near the set the picture hopped ~15 px every few frames ("a little jerky
  when zooming into the platform", Saturn ident v4 and v5). Fix: attach the
  camera to an always-loaded anchor actor at the set and key the relative
  transform (`capra_space_seq.py`, `Capra_CamAnchor`). Check by reading keys
  back (`get_keys()` values should change smoothly) and by a frame-difference
  scan of the render (single-frame spikes while the camera is slow = steps).

## Materials and textures
- **`r.Substrate.ProjectGBufferFormat=0` (blendable GBuffer) breaks Megascans foliage on Metal** (Petit Ridge,
  2026-10-28: three crashes, editor and MRQ, `Assertion failed: ShaderMapId.ContainsShaderType ... M_Foliage ...
  missing expected shader type FAnisotropyPS`, first blamed on a Python edit of the master). → for a new project
  that will use Megascans/Epic sample content, copy the source project's whole `[/Script/Engine.RendererSettings]`
  block (Electric Dreams: Substrate on, BytesPerPixel 170, adaptive GBuffer). With `r.RayTracing=True` the editor
  also refuses to start unless `r.SkinCache.CompileShaders=True`.
- Never recreate MPC parameters (orphans every material) → append missing.
- Texture re-imports keep power-of-two padding → delete first, NONE, assert.
- TextureObjectParameter sampler type must match the texture (LINEAR_COLOR for
  data). Custom-node helper functions must be struct methods.
- GPU `fmod(20,20)` ≈ 1 → wrap loops by hand.
- An If node with a missing input silently fell back to grey → use
  subtract/multiply/saturate graphs.
- Emissive gains that clip lose the colour (glow 2.3, flash ×4 → white) →
  keep peaks near 1× colour; measure clipped pixels (<5%).
- Bursts that push blocks away from the object's centre come out as a flat disc
  when the object is wide, tall and thin (monolith, statue side-on to the camera)
  — Kris: "goes out in a circular direction, but not a spherical direction" →
  random directions on the sphere blended with the outward one, kept above the
  floor (a dome), the half flying at the lens flattened, and the radius capped
  below the camera distance (a 6 m burst at 5.6 m engulfed the camera).
- **Local lights did nothing in the Cassini ring set** — a spot, rect keys and
  even a 50,000 cd test light — because the ring field's thousands of non-Nanite
  rocks overflow Virtual Shadow Maps (viewport warning: "Non-Nanite Marking Job
  Queue overflow"), and an overflowed shadow-casting local light comes out fully
  shadowed. Effects I'd credited to a flash light were the emissive blocks'
  bounce. Fix: `set_cast_shadows(False)` on local lights in such sets (or raise
  the VSM page pool). Check for that warning in the viewport before lighting.
- Once local lights work in a scene exposed for a 5-lux sun, a few candela is a
  lot: 45 cd + 8 cd lit the statue nicely but blew the pale platform to white →
  **lighting channels**: hero lights on channel 1 only (statue on channels 0+1),
  and a separate faint light (7 cd spot) for the floor pool.
- A Meshy statue placed between the camera and Cassini's sun renders as a black
  rim-lit silhouette (not a material problem — UVs, normals and textures were
  fine) → give hero objects their own key light, sized against the scene's sun,
  and cut it when the object goes.
- Meshy GLB textures: Image_0 base colour (sRGB), Image_1 metal/roughness
  (G roughness, B metallic), Image_2 normal (OpenGL: flip green in Unreal).
  Keep metallic at 0 in space unless you want it to mirror black sky.
- Judge light intensities against the scene's sun: Cassini's directional light
  is ~5 lux, so a 500–2500 cd point light a metre off the floor blew the
  platform out white for half a second → a few candela (12 cd peak).
- MRQ's temporal sub-samples evaluate keys inside the frame, so a LINEAR key
  from 0 on frame N−1 to a peak on frame N already lights frame N−1 → key the
  hold CONSTANT up to the event frame.

## Import and Blender

- **Sketchfab glTF from SketchUp/Collada is often in inches** (Stone Cabin, 2026-10-28: 873 × 302 × 547 "metres";
  a 57 × 32 TV = 65-inch TV, a 23.5 oven = 60 cm). Interchange reads glTF as metres, so it would come in 39× too big
  → check the bounds against a known object before import; scale the root node by 0.0254 (and re-centre it) in the
  .gltf JSON rather than fiddling with import scale.
- Interchange glTF → Unreal axes: glTF (x, y-up, z) → Unreal (x, z, y). Verified with a terrain tile whose glTF
  +z ran south: Unreal bounds came out Y 0..+50,400. A glTF model's +Z side faces Unreal +Y at yaw 0.
- `InterchangeGenericMeshPipeline.combine_static_meshes` is deprecated in 5.8 (raises) →
  `combine_static_meshes_behavior = unreal.InterchangeCombineStaticMeshesBehavior.ALL`. Import from Python with
  `InterchangeManager.get_interchange_manager_scripted().import_asset(dest, create_source_data(path), params)` and
  a pipeline object in `params.override_pipelines`.
- **There is no Python call that creates a Landscape from a heightmap** (only `landscape_import_heightmap_from_
  render_target` into an existing one). When the editor UI can't be driven (Kris declined computer-use control of
  Unreal), build the terrain as Nanite static-mesh tiles written straight from the heightmap as glTF
  (`petit_ridge/terrain_tiles.py`: 8×8 tiles of 505² vertices at 1 m, ~32 M triangles, 65 imports ≈ 11 min).
- glTF imports in quaternion mode → `rotation_mode='XYZ'` before rotating.
- Blender → FBX/glTF → Unreal maps (x, −y, z)·100; don't add a normal flip
  after mirroring (inside-out text). Blender north = Unreal −Y. FBX-embedded
  textures don't import.
- Spray/graffiti fonts are overlapping blobs → extrusion leaves holes;
  rasterise with Pillow onto a decal/quad, or sample into blocks.
- `FbxImportUI` overrides silently dropped animation takes → plain
  `AssetImportTask` / default Interchange.
- Blender 5.2: no movie output (render PNG, encode outside); generated images
  render black until saved and reloaded; COPY_ROTATION for billboards; sparse
  keys ease as Bezier; set `dither_intensity = 0` for data bakes.

## Mac / Metal
- Target SM6 (`+TargetedRHIs=SF_METAL_SM6`) with `r.GenerateMeshDistanceFields`
  for Niagara Fluids Gas 3D colour; Fluids beyond Gas 3D are Windows-marked.
- nDisplay (ICVFX) is Windows/Linux only → `-DisablePlugins=ICVFX` to open.
- Samples that ship only DirectX shader caches compile everything on first
  open; Titan ships a Metal cache.
- Export `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` for
  scripts that need the Metal toolchain.
- macOS has no `timeout`/`setsid` → loops with sleep, `nohup`.
- `bash scripts/preflight.sh` fails on every line (`print: command not found`): it's a zsh script → run it as `zsh scripts/preflight.sh` or directly by path.

## Cesium
- Default georeference is Denver → set and read back. Synchronous capture
  never finishes under MRQ → async + handles. Two renders sharing the sqlite
  cache → "database is locked" ×300k. Fog 0.004 whited out the valley →
  0.00035, falloff 0.2. Use `open_map()`; reloading with the credits widget
  hangs. The tileset URL carries the Google key → treat the map and logs as
  sensitive.

## Process
- **Real places need real recordings** (Petit Ridge v1, Kris: "the sounds are terrible"): sample-project ambience
  (Electric Dreams' tropical canopy and crickets, a riverbed for a still lake, a sci-fi drone, a designed knock) reads
  fake on a real place → field recordings of the right habitat and season, a few long beds that follow the camera.
- Sonniss GDC bundles: the official mirror has per-library folders of single files
  (`https://ftpmirror.your.org/pub/misc/sonniss20XX/individual/<Vendor - Library>/`; track lists are public Google
  Sheets, `…/export?format=csv`), so one 30–90 MB recording instead of 3 GB zip parts. Licence: media production, no
  attribution, no AI/ML training, no redistribution. Python's urllib failed SSL on this Mac → curl.
- Pixabay audio sits behind a Cloudflare bot check: scripted downloads are blocked (and the safety classifier refuses
  fetching past it) → Kris saves the files by hand, or use Sonniss/Freesound with his own account.
- Level-matching beds: measure the same band you'll play. Measuring only above 100 Hz, then boosting the full-band
  file, made the night bed's gust rumble boom 15 dB over the rest → high-pass beds first (~100 Hz), then match.
- **A bare-earth viewshed oversells a view** (Petit Ridge: 82% of the lake visible on lidar ground, 25–32% with a
  20 m canopy and a cleared view corridor, **20 % with the real lidar canopy**: the trees there are 24 m, not 20).
  Lidar DEMs are bare earth: use the point cloud's canopy height model before putting a view number on screen, and
  say which one it is.
- Leaf-off lidar leaves holes in a 1 m canopy model (bare hardwood crowns return only ground hits), and roofs, wires
  and towers make 60 m "trees" → vegetation classes only, a 3×3 max search, close pits; fill trees where the
  surrounding canopy says forest.
- `rr.sh` already calls `run.sh`: `run.sh x.py | rr.sh` runs a second, empty command (AssertionError on a directory).
- Look at the frames yourself (crop, zoom, contact sheets); a clean log isn't
  proof. Trace camera numbers offline (replicate the curve in plain Python).
- Delete frame folders once the MP4 is encoded and checked (245 GB freed once).
- The Epic Launcher keeps a full installer copy of every sample it creates a
  project from in `/Users/Shared/UnrealEngine/Launcher/VaultCache` (104 GB on
  the internal drive by 2026-10-08: Titan 63, ICVFX "TheOrigin" 17, Content
  Examples 15, Game Animation 7, Cassini 2). Once the project exists the copy
  is redundant → Trash it, and set Launcher → Settings → Edit Vault Cache
  Location to `/Volumes/KB SS/Unreal Engine/VaultCache`.
- SendUserFile times out above ~15 MB → iCloud `TrailGoat Videos` for big
  files; 720p drafts of 15 s are ~19 MB and went through.
- The `rm -rf "$VAR"` guard blocks variable paths → use literal paths.
- zsh doesn't word-split `$var` → `${=var}` (a download loop silently failed).
- Mixkit full files: the download page links `…/sfx/<id>/<id>.mp3` or `.wav`;
  the asset host wants `Referer: https://mixkit.co/`.
- **A per-particle random that ranks one thing must not drive another** (TrailGoat Films
  ident v1, 2026-10-26: "the wordmark tilts down to the right"). R.y was sorted to match
  each particle with its letter in reading order (corr 0.999), then reused for the drain's
  fall speed, so the right half fell twice as far and the word tipped. Give each job its
  own hash (`frac(R.x*7.31 + R.z*3.17)`), and check correlations offline before a render.
- `-run=pythonscript` does nothing in a project without PythonScriptPlugin enabled, even
  with `-EnablePlugins=` on the command line (Project Titan). Export what you need from a
  project that has it, or enable the plugin in a clone.

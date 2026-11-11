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
  continuously ran 4.4 s/frame (Petit Ridge, 508k Nanite trees, 8 samples), 5.1 s/frame over the whole film
  (1,921 frames in 2 h 44 min). Time a short continuous run and add ~15 %.
- **QA a final against the approved draft, frame for frame**: run the same scan (frame-to-frame difference, magenta,
  pure black, blown white) on both and compare by frame number. Petit Ridge 4K flagged a fast orbit, a hard cut and
  2–4 % pure-black shadow at 52 s; all three matched the 720p Kris approved, so none was a render fault. Only a
  difference from the draft is a new problem (`scan_frames.py`, 1,921 4K frames in ~3 min on 8 processes).
- Pillow card post at 4K, one frame at a time with default PNG compression, would have taken ~1½ h for 80 s → a
  `multiprocessing.Pool` over frames (8 workers) and staging PNGs at `compress_level=1`: composite + crf 14 encode
  in 4.4 min (Petit Ridge `post_film.py --workers`). Module-level `sys.argv` parsing still works in spawned workers.
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
- **A material that fails to compile renders as the Default Material in `-game`, with no other sign** (landfilm
  batch: a Linear Grayscale sampler on an ordinary BC texture). The ground went flat grey-brown and every MPC effect
  on it (Read the Land) vanished, and the stills almost passed as an improvement. After any material change, grep
  the render log for `Failed to compile Material` before reading the stills; samplers: Linear Color for non-sRGB
  masks unless the texture's compression is Grayscale.
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
- The fog switch is `enable_volumetric_fog` in Python (`volumetric_fog` fails silently through a guarded setter).
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
- **Template code carries the template's numbers in strings too**: Petit Ridge's terrain material had its Z0 (698.89)
  and elevation range (456–942 m) inside the HLSL of the Read the Land block, so every new lot's contours sat at the
  wrong heights. When a script becomes a template, grep the shader strings and docstrings as well as the constants.
- **Open ground isn't forest floor** (landfilm batch, Big Knoll): with the litter material everywhere near the camera,
  lawns, pasture and cleared lots read as a sand beach. Mask open ground from the lidar canopy (< 2.5 m) and give it
  the photo's own colour blurred to ~10 m (house-free); the sharp photo up close would show neighbours' roofs.
  Cap the tint's luminance (forest floor ≤ 0.21, open ground ≤ 0.19) and desaturate it: a sunlit ridge-top
  clearing (Timber Cliff, golden hour, exposure opened for the home's shaded faces) read lemon-yellow and a
  September photo's lawn read lime; Petit Ridge's clearing was in shade, so its numbers never hit the limit.
- **zsh in batch scripts**: `${@:-a b c}` stays one word (loop ran once with "a b c" and matched nothing), and an
  unmatched glob in `rm -f dir/[0-9]*.laz` is an error that fails the step. Set arrays explicitly; use `find -delete`.
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

## Notes Below Sauvage (2026-11-09)
- **`unreal.MaterialProperty` has no `MP_CUSTOM_DATA0/1` in 5.8 Python** (dir() shows no MP_C* at all), so a clear coat
  can't be wired with `connect_material_property` → look the pin up with `hasattr` and fall back to default lit with low
  roughness (0.10–0.16 read as lacquered glass under strip lights); a material function or a hand-made parent is the
  untested alternative.
- **Scripted material graphs log "Failed to compile Material … missing input" once per wire** (the editor recompiles a
  half-built graph after every connect). Those are not failures: judge by the render log (`grep -c "Failed to compile"`
  = 0) or by errors logged after the final `recompile_material`.
- **Bright blocks under lights sized for a dark hero clip to pastel**: a 110 cd top light chosen for a near-black bottle
  put ~2 nits on albedo-0.9 blocks, so red read pink and the vote colours went mint. → a per-shape albedo scale
  (0.2–0.35 for word and colour shapes, 1.0 for textured object shapes) and emissive ≤ ~0.6× colour; flight glow
  0.7·bump, blast +1.6. Tokyo Night's "red" #f7768e is salmon: for HATE/danger use a truer red (linear 0.90, 0.045, 0.10).
- **Meshy 7.1 "Ultra 2K" models are 1–10 M triangles** (GLBs of 40–330 MB). trimesh voxelisation and closest-point
  queries crawl at that size → 2.5 M area-weighted surface samples (with the texture colour under each), cells from
  `floor(p/pitch)`, `ndimage.binary_fill_holes`, colours from a cKDTree over the samples: 8 models + words in 59 s.
  Import them as Nanite; seven models took ~4.5 min headless, and instance/triangle count barely moved render time.
- **Portrait with captions: the subject only owns y 640–1300 of 1920** (34 % of the height). Pushing the hero closer
  for "presence" ran the bottle into the sub-line and the source line. Compute the camera distance from that band, and
  judge framing on captioned key frames, not clean stills.
- A violet rim light behind the subject mirrors in a glossy dark floor as a large blob at the bottom of frame → keep the
  rim small, off-axis and a few candela; give the floor albedo ~0.03 and roughness ~0.3 so the top light pools on it.
- **ffmpeg `alimiter` auto-levels by default** (`level=true` normalises the output to 0 dBFS): a mix set to -14 LUFS came
  out at -12.5 with a 0 dBTP peak → `alimiter=limit=0.84:level=false`. Measure the muxed file, not the intermediate.
- **A hand nearest the camera balloons** (spray film v1: the Meshy forearm lay along depth, hand toward a 34 mm camera
  2 m away; it filled half the frame, hid the notes and clipped to white) → shoot bodies from high (52–56°) and far with
  a 50 mm lens, scale them to leave the props a quarter of the frame width each, and give skin a 0.55 albedo tint under
  lights sized for a dark bottle.
- **Opaque blocks are not smoke**: 34,870 blocks at 1.5 cm in a 1.7 m dome previewed as a solid wall. For a haze, size
  the blocks so n·σ·L ≈ 0.4 (0.8 cm here) and thin the count as the cloud shrinks; put a gradient scrim under captions
  that sit over it.
- **A masked-out model still shows in a glossy floor** (spray film v2: after the forearm and bottle dissolved, their
  dark silhouettes sat in the floor's reflection under the end words; ray-traced reflections ignore the opacity mask)
  → give every such actor a Sequencer visibility track and hide it outside its appearance window (bool keys from the
  same windows the material uses). Check an eye-level still after every dissolve-out, not only the top-down ones.
- **Voice cut in a very quiet room**: a noise floor of -80 dB put the "floor + 14 dB" speech threshold at -66 dB, so
  breaths and tails counted as words and no pause was tightened (the edit ran 3 s long) → take the threshold from the
  speech level instead (95th percentile - 34 dB). Whisper also starts a sentence's first word up to 0.9 s early when a
  breath precedes it: if no onset is found near its time, take the first sound after it; and list the above-threshold
  runs inside each clip to catch a lip click before the first word.
- **Re-timing to a voice squeezes camera moves**: a push-in keyed between two beats that the narration pulls together
  dropped from 1.0 s to 0.5 s. After the warp, print the camera key times and re-key any move under ~1.5 s to start
  on an earlier word. Model fade-ins and block transitions keep their own length; only their start time is warped.
- **Social films: the first second has to hold the product, motion and the claim** (audit of both Notes Below films,
  9 Nov 2026: the hero showed the bottle at 5.5 s behind a near-static red ball; the spray film sprayed at 6.5 s after
  building its own set). Never open by assembling the set. Start the first transition before frame 0 (t0 = -1.1 s) so
  frame 0 is already mid-motion with the object half-built, put the headline up at t = 0 with no fade, and give it a
  dark gradient scrim while blocks pour in behind it.
- **Block words that repeat the caption are dead screen time** (26 of 68 s were white block letters on black, the
  Meshy models on screen for 10 s). Give each story beat a real object (two bottles for "the name", a gavel for the
  trial, a clapperboard for the ad, four trophies) and keep block words for the one number the film is about.
- **Tell a beat in the order the picture needs**: "ad pulled within a day, accused of..." swept the stage empty for
  3.5 s while the accusation was read. Cause first, effect last, so the sweep is the end of the beat.
- **Let the camera carry the idea**: three "distances" shot from one distance read as one shot. Wide for the room,
  closer for arm's length, a close-up for skin; move the props in to fit the close-up.
- **A haze that hides the props**: clear a pocket along the camera's line of sight to each prop (push blocks
  perpendicular to the view ray out to a radius of ~0.6 x the prop's size), not a sphere around it.
- **Labels on models**: project a point on each model through `cam_at` per frame and pin a mono label there. Label only
  the group being named (two or three at a time), front row on the floor in front, back rows above, each on a dark pill.
- **Meshy with 2K textures gives 40-180 k faces** (not 1-10 M): imports in seconds and looks the same at 720p. Its gold
  comes out ivory and its black comes out too dark for a dark stage: multiply the base texture by a gold tone
  (1.0, 0.76, 0.36), lift dark props with a material tint of ~1.9, and apply the same factor to the block lattice.
- **Selective dissolve**: to keep some blocks alive while others dissolve into a solid, gate the dissolve by position
  (`if outside the model's box: sol = 0`), not by block id; blocks flown into the box later vanish as they enter it.
- **Never synthesise sound effects, a third time** (Notes Below, 2026-11-09: synth whooshes, thumps and blips on every
  block move; Kris: "absolutely terrible ... these fake synth sounds don't represent what's happening at all. I'd rather
  have no sounds than these"). Read `taste.md` "Real sound" before any sound pass. Fix: real recordings only, one per
  thing on screen (crowd, glass, gavel, clapperboard, broom, applause, spritz, blocks stacking, clock), silence for moves
  with no real-world sound, placed from the timeline table so a re-time keeps them in sync (`Fragrance/unreal/sfx.py`).
  One-shots peak -16 to -8 dBFS, beds about -30 dBFS RMS under a -14 LUFS voice.
- Mixkit has no gavel or clapperboard: a wood-hammer hit and a hard plastic snap over a wood hit stand in; say so.
  Its tag pages answer HTTP 429 with a Cloudflare check after ~50 scripted requests: don't crawl, open the tag page in
  the browser pane and read ids from `data-audio-player-item-id-value`; full files come from
  `assets.mixkit.co/active_storage/sfx/<id>/<id>.wav` (Referer mixkit.co), which is not rate-limited.
- Choosing recordings without ears: profile each file (length, onsets, loudest 10 ms, band energy) and read a
  log-frequency spectrogram (`showspectrumpic`); a pump spray is broadband, an aerosol can has a ring near 1.5 kHz.
- **Audit the story before the polish** (Notes Below second audit): the first audit fixed pacing and pictures and left
  a trial beat that said nothing about the trial and an opinion line ("should have ended it") the verdict contradicts.
  For each beat ask what a stranger learns, and whether every promise the hook makes is paid off in words.
- News photos of a trial are agency-owned (AP, Getty, pool); Wikimedia Commons had none for Depp v. Heard. Free and
  real: the courthouse (CC0), court documents. Check licence per file with the Commons API (`iiprop=extmetadata`);
  prefer CC0/CC BY over BY-SA for video. Meshy's image tool (Nano Banana Pro) costs 9 credits an image, 16:9 only,
  1376x768; ask for silhouettes from behind when a real person is involved and label the result on screen.
- **Four props through Chrome in a forked agent** took 10 min and 212 Meshy credits while the main thread kept
  building; write the prep with a fallback (the old block word) for each prop so the build never waits on them.

## Notes Below Sauvage v7 (2026-11-10)
- Plan the effect per beat before the first build. Six versions used one effect (the swarm) for every beat until Kris
  said "we rely too much on the swarms". Keep the swarm for counts of people; give objects light, haze, dust, mist.
- Niagara Examples Pack for product work: NS_Smoke_Plume reads as a fog machine and greys the frame, NS_Impact_Wood
  is a small spark plus a decal square, NS_SmokePuffLight is a sprite-baking utility, not an effect. For a spray or
  impact dust, fly sprites in the material instead (techniques.md). The pack can be cloned into a project by copying
  `Content/NiagaraExamples` at the same path; delete it again if nothing uses it.
- Check stills of one beat: set the check queue's custom playback range and a step of 3–9 frames (`NOTES_RANGE=a:b`,
  `NOTES_STEP`, `NOTES_LAST`, `NOTES_STALL=30`): 15–25 frames in about 38 s, instead of a whole-film pass.
- A Meshy prop is one mesh: the gavel cannot swing and the clapper cannot close. Ask for separate parts when the
  beat needs the motion, or carry the hit with light, dust, a camera jolt and sound, and say so.
- `scripts/preflight.sh` is zsh; `bash preflight.sh` prints "print: command not found".
- ffmpeg's image2 glob drops frames when a folder mixes RGB and RGBA PNGs (opaque and transparent overlay stills):
  tile such sheets with PIL.
- Patch scripts that insert triple-quoted code: write the fragment to a file and read it, not a heredoc inside a
  heredoc.
- A transparent overlay rendered with kb-ytvideo's render.js must never have a fully opaque frame: Playwright writes
  that screenshot as RGB, the PNG pipe changes format, ffmpeg resets its filter graph and the .mov comes out short
  (550 of 1,845 frames) while render.js still prints the full count. Leave one clear pixel row on full-frame cards,
  and probe `nb_frames` before compositing.
- Props swapped in the dark still flash if their material has a dissolve glow: give swapped props a hard window
  (2 ms) and switch the edge glow off per instance (`Edge` = 0).
- A real product needs a real reference. The first 1966 Eau Sauvage model came from a prompt written from memory
  ("tall rectangular flask, vertical ribbing") and was wrong; Kris sent a photo: "Can we make the 1966 bottle look like
  the 1966 bottle please" (10 Nov 2026). Look at a photo of the actual object before writing the Meshy prompt and
  describe what is in it (squat flask, diagonal twisted ribs, silver cylinder cap, clipped-corner label). Meshy bakes
  clear glass as an opaque texture: darken the tint (0.58) and add a little emissive lift (0.05) so it reads as
  liquid, and keep the key light near neutral or a silver cap turns cream.
- Re-importing one model: `NOTES_ONLY=<name> ./build.sh import,materials,level,sequence,queue` (36 s) instead of the
  whole set (the note models are millions of faces).
- People in the story: Kris asked for the two people side by side, not the courthouse ("There have to be free rights
  pictures of both of them"). Wikimedia Commons has them (Depp: Harald Krichel, Berlinale 2020; Heard: Gage Skidmore,
  Comic-Con 2018), nearly all CC BY-SA: crop only, name and photo year on each half, photographers and licence on the
  card, full credit with licence versions in the post caption, and tell him share-alike is the open question.
- Commons API: fetch with curl (python.org's Python has no CA certs: CERTIFICATE_VERIFY_FAILED). `iiurlwidth` thumbs
  come back in bucketed sizes, not the width asked for or reported; ffprobe the file before computing a crop.

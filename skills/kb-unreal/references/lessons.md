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
- The Path Tracer at 960×540 64 spp untiled **kernel-panicked the Mac** →
  never run it untiled; low spp, unattended only.
- Claude Code background tasks die after ~30 min → for long jobs use
  `nohup … & disown` and poll, or the harness's background mode with a
  completion check.
- Check renders: render every 15th/30th frame first (`output_frame_step`) and
  read them; motion problems need the camera numbers traced offline.

## Editor, levels, World Partition
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

## Cesium
- Default georeference is Denver → set and read back. Synchronous capture
  never finishes under MRQ → async + handles. Two renders sharing the sqlite
  cache → "database is locked" ×300k. Fog 0.004 whited out the valley →
  0.00035, falloff 0.2. Use `open_map()`; reloading with the credits widget
  hangs. The tileset URL carries the Google key → treat the map and logs as
  sensitive.

## Process
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

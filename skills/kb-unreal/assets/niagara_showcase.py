"""NX_Showcase: the Niagara Examples pack's hero effects on a dark stage, one camera cut
per effect, each fired by a Niagara life-cycle section so bursts land on the cut.
Builds /Game/CapraLab/NX_Showcase + LS_NX_Showcase + MRQ queues Q_NX_check / Q_NX_720."""
import json
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MAP = '/Game/CapraLab/NX_Showcase'
FPS = 30
OUT = '/Volumes/KB SS/Capra Studios/Unreal/NiagaraExamples'
X0, DX = 10000.0, 6000.0
NX = '/Game/NiagaraExamples/'

# (name, asset, kind, seconds, start offset s (negative = pre-roll), system z, cam dist, cam height, look z)
SHOTS = [
    ('Boundary_Sphere', 'FX_Misc/NS_Boundary_Sphere', 'loop', 2.0, -1.0, 150, 700, 220, 150),
    ('Pickup_Idle', 'FX_PickUp/NS_Pickup_Idle', 'loop', 2.0, -1.0, 100, 300, 140, 100),
    ('Bubble_Burst', 'FX_Misc/NS_Bubble_Burst', 'burst', 2.0, 0.15, 100, 340, 140, 110),
    ('Spark_Continuous', 'FX_Sparks/NS_Spark_Continuous', 'loop', 2.0, -1.0, 150, 380, 150, 110),
    ('Spark_Burst', 'FX_Sparks/NS_Spark_Burst', 'burst', 2.0, 0.15, 100, 280, 120, 90),
    ('Impact_Metal', 'FX_Weapons/Impacts/NS_Impact_Metal', 'burst', 1.8, 0.15, 0, 180, 70, 30),
    ('Fire', 'FX_Misc/NS_Fire', 'loop', 2.5, -1.5, 0, 420, 150, 110),
    ('TeslaCoil', 'FX_Ribbons/NS_TeslaCoil', 'loop', 2.5, -1.0, 400, 1000, 380, 330),
    ('SimpleRibbonTrail', 'FX_Weapons/Trails/NS_SimpleRibbonTrail', 'ribbon', 2.5, 0.0, 150, 650, 220, 150),
    ('Smoke_Plume', 'FX_Smoke/NS_Smoke_Plume', 'loop', 3.0, -3.0, 0, 1800, 400, 600),
    ('FogBank', 'FX_Fog/BP_FogBankVolume', 'bp', 3.0, 0.0, 0, 4000, 400, 300),
    ('FireworkBurst', 'FX_Misc/NS_FireworkBurst', 'burst', 3.5, 0.15, 800, 2000, 300, 950),
    ('Dirt_Explosion', 'FX_Explosions/NS_Dirt_Explosion', 'burst', 3.0, 0.15, 0, 1500, 260, 220),
    ('Explosion', 'FX_Explosions/NS_Explosion', 'burst', 4.0, 0.15, 0, 1700, 300, 320),
]
PITCH = {'Impact_Metal': 90.0}   # impacts spray along the system's X axis (the hit normal): point it up

if EAL.does_asset_exist(MAP):
    LES.load_level(MAP)
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith('NX_'):
            EAS.destroy_actor(a)
else:
    assert LES.new_level(MAP), 'new_level failed'


def spawn(cls, loc, rot=None, label=None):
    a = EAS.spawn_actor_from_class(cls, loc, rot or unreal.Rotator(0.0, 0.0, 0.0))
    if label:
        a.set_actor_label(label)
    return a


# Stage: a dark grid floor, a dim sun like the Gallery's (8 lux), fixed exposure.
floor = spawn(unreal.StaticMeshActor, unreal.Vector(X0 + DX * len(SHOTS) / 2, 0, 0), label='NX_Floor')
floor.static_mesh_component.set_static_mesh(EAL.load_asset('/Engine/BasicShapes/Plane'))
MP = '/Game/CapraLab/M_NX_DarkFloor'   # near-black, a little glossy, so the effects own the frame
if not EAL.does_asset_exist(MP):
    MEL = unreal.MaterialEditingLibrary
    mat = TOOLS.create_asset('M_NX_DarkFloor', '/Game/CapraLab', unreal.Material, unreal.MaterialFactoryNew())
    c3 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c3.set_editor_property('constant', unreal.LinearColor(0.012, 0.012, 0.016, 1.0))
    MEL.connect_material_property(c3, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rc = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 200)
    rc.set_editor_property('r', 0.35)
    MEL.connect_material_property(rc, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
floor.static_mesh_component.set_material(0, EAL.load_asset(MP))
floor.set_actor_scale3d(unreal.Vector(DX * (len(SHOTS) + 2) / 100.0, 400.0, 1.0))
sun = spawn(unreal.DirectionalLight, unreal.Vector(X0, 0, 2000), unreal.Rotator(roll=0.0, pitch=-40.0, yaw=60.0), 'NX_Sun')
sun.light_component.set_intensity(8.0)
sky = spawn(unreal.SkyLight, unreal.Vector(X0, 0, 500), label='NX_Sky')
sky.light_component.set_intensity(0.6)
ppv = spawn(unreal.PostProcessVolume, unreal.Vector(X0, 0, 0), label='NX_Post')
ppv.set_editor_property('unbound', True)
s = ppv.settings
s.override_auto_exposure_method = True
s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
s.override_auto_exposure_min_brightness = True
s.auto_exposure_min_brightness = 2.0
s.override_auto_exposure_max_brightness = True
s.auto_exposure_max_brightness = 2.0
ppv.settings = s

P = '/Game/CapraLab/LS_NX_Showcase'
if EAL.does_asset_exist(P):
    EAL.delete_asset(P)
seq = TOOLS.create_asset('LS_NX_Showcase', '/Game/CapraLab', unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1))
total = sum(sh[3] for sh in SHOTS)
END = int(round(total * FPS)) + 1
seq.set_playback_start(0)
seq.set_playback_end(END)
TICK = seq.get_tick_resolution().numerator // seq.get_tick_resolution().denominator
K = TICK // FPS
DR = unreal.MovieSceneTimeUnit.DISPLAY_RATE
AUTO = unreal.MovieSceneKeyInterpolation.AUTO
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
plan = []
t = 0.0
for i, (name, rel, kind, dur, off, z, dist, ch, lz) in enumerate(SHOTS):
    x = X0 + DX * i
    tgt = unreal.Vector(x, 0.0, lz)
    f0, f1 = int(round(t * FPS)), int(round((t + dur) * FPS))
    if kind == 'bp':
        a = spawn(EAL.load_blueprint_class(NX + rel), unreal.Vector(x, 0, z), label='NX_' + name)
        o, e = a.get_actor_bounds(False)
        dist = max(dist, 1.3 * max(e.x, e.y, e.z))
        tgt = unreal.Vector(o.x, o.y, max(o.z, 150.0))
    else:
        sysa = EAL.load_asset(NX + rel)
        a = spawn(unreal.NiagaraActor, unreal.Vector(x, 0, z), unreal.Rotator(roll=0.0, pitch=PITCH.get(name, 0.0), yaw=0.0), 'NX_' + name)
        comp = a.niagara_component
        comp.set_asset(sysa)
        comp.set_editor_property('auto_activate', False)
        nb = seq.add_possessable(comp)
        nt = nb.add_track(unreal.MovieSceneNiagaraSystemTrack)
        ns = nt.add_section()
        s0 = max(0, int(round((t + off) * FPS)))
        ns.set_range(s0, f1 + 2)
        ns.set_editor_property('section_evaluate_behavior',
                               unreal.NiagaraSystemSpawnSectionEvaluateBehavior.ACTIVATE_IF_INACTIVE if kind in ('loop', 'ribbon')
                               else unreal.NiagaraSystemSpawnSectionEvaluateBehavior.NONE)
        if kind == 'ribbon':   # the emitter trails behind a moving component: fly it round a rising loop
            ab = seq.add_possessable(a)
            tr = ab.add_track(unreal.MovieScene3DTransformTrack)
            ts = tr.add_section()
            ts.set_range(0, END)
            chs = ts.get_all_channels()
            for k in range(0, f1 - f0 + 1, 2):
                u = k / float(f1 - f0)
                ang = 2 * math.pi * 1.4 * u
                pos = (x + 260 * math.cos(ang), 260 * math.sin(ang), z - 60 + 160 * u)
                for c, v in zip(chs[:3], pos):
                    c.add_key(unreal.FrameNumber(f0 + k), v, 0.0, DR, AUTO)
    # camera: on -Y looking +Y at the target, a slow push in over the shot
    cam = spawn(unreal.CineCameraActor, unreal.Vector(x, -dist, ch), label='NX_Cam_' + name)
    cc = cam.get_cine_camera_component()
    fb = cc.filmback
    fb.sensor_width, fb.sensor_height = 36.0, 20.25
    cc.filmback = fb
    fs = cc.focus_settings
    fs.focus_method = unreal.CameraFocusMethod.DISABLE
    cc.focus_settings = fs
    cc.current_focal_length = 35.0
    cb = seq.add_possessable(cam)
    tr = cb.add_track(unreal.MovieScene3DTransformTrack)
    ts = tr.add_section()
    ts.set_range(0, END)
    chs = ts.get_all_channels()
    for ff, scale in ((f0, 1.06), (f1, 0.94)):
        p = unreal.Vector(tgt.x, tgt.y - dist * scale, tgt.z + (ch - lz) * scale)
        r = unreal.MathLibrary.find_look_at_rotation(p, tgt)
        for c, v in zip(chs, (p.x, p.y, p.z, r.roll, r.pitch, r.yaw)):
            c.add_key(unreal.FrameNumber(ff), v, 0.0, DR, AUTO)
    cs = cut.add_section()
    cs.set_range(f0, f1)
    cs.set_camera_binding_id(seq.get_binding_id(cb))
    plan.append({'name': name, 'asset': rel, 'kind': kind, 'f0': f0, 'f1': f1, 'dist': round(dist)})
    t += dur
EAL.save_loaded_asset(seq)

for qname, samples, step, sub in (('Q_NX_check', 1, 10, 'check_frames'), ('Q_NX_720', 2, 1, 'showcase_frames')):
    path = '/Game/CapraLab/' + qname
    q = EAL.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(qname, '/Game/CapraLab', unreal.MoviePipelineQueue, None)
    q.delete_all_jobs()
    job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.map = unreal.SoftObjectPath(MAP + '.NX_Showcase')
    job.sequence = unreal.SoftObjectPath(P + '.LS_NX_Showcase')
    cfg = job.get_configuration()
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    o.output_resolution = unreal.IntPoint(1280, 720)
    o.output_directory = unreal.DirectoryPath('%s/%s' % (OUT, sub))
    o.file_name_format = 'f_{frame_number}'
    o.zero_pad_frame_numbers = 4
    o.override_existing_output = True
    o.output_frame_step = step
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.override_anti_aliasing = True
    aa.spatial_sample_count = 1
    aa.temporal_sample_count = samples
    aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_TSR
    aa.engine_warm_up_count = 30
    aa.render_warm_up_count = 8
    g = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    g.game_mode_override = unreal.GameModeBase   # deprecated name, still applied
    EAL.save_loaded_asset(q)
assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
json.dump({'fps': FPS, 'end': END, 'shots': plan}, open(OUT + '/showcase_plan.json', 'w'), indent=1)
print('NX_READY frames %d' % END)
for p_ in plan:
    print('SHOT', p_)

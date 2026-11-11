#!/usr/bin/env python3
"""Every aid station in 30 seconds: a race-week Reel (9:16) for a race we've filmed.

Kris, 2026-11-11, on the ideas report https://claude.ai/artifact/2Y2wvovM6UWPr8KnBq6r9g ("I love this proceed"): the
Tuesday-of-race-week Reel that replaced the race-week carousel. The whole course from above, upright: the film's own
opening pose (THE WHOLE COURSE) rendered at --portrait 1.0, which keeps the film's width and adds room above and below.
Over it the trail fills in from start to finish, each verified aid pin pops in numbered, a list grows at the foot with
each station's official distance and the gap from the one before, and the longest stretch is called out at the end.

    aidreel.py <slug> shots              # <out>/shots.json: the film's whole-course pose, held for the Reel
    aidreel.py <slug> render             # under the studio's render lock: cam.json, then frames/f_NNNN.png (1080x1920)
    aidreel.py <slug> video [youtube|social]
    aidreel.py <slug> mix [youtube|social]
    aidreel.py <slug> words              # captions/{instagram,facebook,tiktok}.txt and meta.json for YouTube
    aidreel.py <slug> all                # every step in order

Out: frames and cam in Renders/flyovers/shorts/<slug>/aids-<year>/, the Reels and words in Films/<slug>/aids-<year>/.
Run with the weekly-shorts venv (Pillow, imageio-ffmpeg). Music: the film's own cleared track (music_rights).
"""
import bisect, glob, json, math, os, re, subprocess, sys, time
TG = '/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts/scripts/flythrough'
sys.path.insert(0, TG); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hud, short as S, geo           # noqa: E402
from PIL import Image, ImageDraw     # noqa: E402

STUDIO = '/Volumes/KB SS/TrailGoat-Studio'
W, H, FPS, MI = 1080, 1920, 24, 1609.344
SECS = 30.0                           # the Reel's length; the trail fills in over T_IN..T_DONE
T_IN, T_DONE, T_LONG = 1.6, 21.0, 22.0
N = round(SECS*FPS)
SLUG = sys.argv[1]; CMD = sys.argv[2] if len(sys.argv) > 2 else 'all'
FILM = json.load(open(f'{STUDIO}/Films/{SLUG}/film.json'))
SPEC = json.load(open(FILM['shots']))
COURSE_P = sorted(glob.glob(FILM['out_dir'] + '/course-*.json'))[0]
COURSE = json.load(open(COURSE_P))
YEAR = int(os.environ.get('AIDS_YEAR') or (COURSE.get('start_datetime') or '2026')[:4])
OUT = f'{STUDIO}/Renders/flyovers/shorts/{SLUG}/aids-{YEAR}/'
DEST = f'{STUDIO}/Films/{SLUG}/aids-{YEAR}/'
os.makedirs(OUT, exist_ok=True); os.makedirs(DEST, exist_ok=True)
KM = any(' · KM ' in lab for _, lab in SPEC.get('aids', []))
UNIT = 'KM' if KM else 'MI'


def race_name():
    p = f'{STUDIO}/Films/queue/{SLUG}/race_name'
    name = open(p).read().strip() if os.path.exists(p) else COURSE['name']
    return re.sub(r'\s{2,}', ' ', re.sub(r'\b(19|20)\d{2}\b', '', re.split(r'\s+[—–-]\s+', name)[0])).strip(' -—–')


# ---------- the stations: official distances from the pin labels, positions on our route ----------
def stations():
    out = []
    for m, lab in SPEC.get('aids', []):
        name, _, dist = lab.partition(' · ')
        mm = re.search(r'(KM|MI)\s+([\d.]+)(?:\s*/\s*([\d.]+))?', dist)
        out.append(dict(d=m*MI, name=hud.aid_name(name.strip()), off=float(mm[2]) if mm else None))
    out.sort(key=lambda s: s['d'])
    # the race's own distance as the film's description states it ("… to the finish: 161 km and …"), else our track's
    desc = f'{STUDIO}/Films/{SLUG}/description.txt'
    m = re.search(r'to the finish: ([\d,.]+) (miles|km)', open(desc).read()) if os.path.exists(desc) else None
    total = float(m[1].replace(',', '')) if m else (COURSE.get('distance_m') or 0)/(1000 if KM else MI)
    prev = 0.0
    for s in out:
        s['gap'] = None if s['off'] is None else round(s['off'] - prev, 1); prev = s['off'] if s['off'] is not None else prev
    finish_gap = round(total - prev, 1) if total else None
    return out, round(total, 1), finish_gap


def longest(st, finish_gap):
    """(gap, from, to, route d from, route d to): the longest stretch between aid, the run to the finish included
    (d to is None for the finish: the end of the route)"""
    legs = [(s['gap'], st[i-1]['name'] if i else 'the start', s['name'], st[i-1]['d'] if i else 0.0, s['d'])
            for i, s in enumerate(st) if s['gap'] is not None]
    if finish_gap is not None and st: legs.append((finish_gap, st[-1]['name'], 'the finish', st[-1]['d'], None))
    return max(legs) if legs else None


# ---------- shots and render ----------
def shots():
    """The film's opening pose (its first shot, THE WHOLE COURSE) held for the Reel's length as one slow drift."""
    first = dict(SPEC['shots'][0]); assert 'WHOLE COURSE' in first.get('name', '').upper(), first.get('name')
    first['t'] = [0, SECS]; first['light'] = [first['light'][0]]*2 if isinstance(first.get('light'), list) else first.get('light')
    spec = dict(SPEC, shots=[first]); json.dump(spec, open(OUT + 'shots.json', 'w'), indent=1)
    print('shots', OUT + 'shots.json', first['name'], first['t'])


def render():
    """render.py at 1080x1920 --portrait 1.0 under the render lock (masters let us in between films, as won_render.sh)."""
    q = f'{STUDIO}/Films/queue'; lock = f'{q}/.render.lock'; waitf = f'{q}/won.wait.aids-{SLUG}'
    if not os.path.exists(OUT + 'shots.json'): shots()
    open(waitf, 'w').close()
    try:
        while True:
            busy = subprocess.run(['pgrep', '-f', 'Blender.*-b'], capture_output=True).returncode == 0
            if not busy:
                try: os.mkdir(lock); break
                except FileExistsError: pass
            time.sleep(20)
    finally:
        if os.path.exists(waitf): os.remove(waitf)
    print('LOCK', SLUG, time.strftime('%H:%M'), flush=True)
    try:
        B = '/Applications/Blender.app/Contents/MacOS/Blender'
        base = [B, '-b', '-P', 'scripts/flythrough/render.py', '--', COURSE_P, OUT, '--shots', OUT + 'shots.json',
                '--res', '1080x1920', '--portrait', '1.0', '--samples', '32']
        root = os.path.dirname(os.path.dirname(TG))
        with open(OUT + 'render.log', 'a') as log:
            for attempt in range(4):                       # a dropped tile fetch kills the dry pass with exit 0: check for cam.json
                subprocess.run(base + ['--dry', '--export-cam', OUT + 'cam.json'], cwd=root, stdout=log, stderr=subprocess.STDOUT)
                if os.path.exists(OUT + 'cam.json'): break
                time.sleep(30*(attempt + 1))
            else:
                sys.exit('no cam.json after four dry passes (see render.log)')
            for attempt in range(4):                       # a dropped tile fetch ends a pass; the next one resumes
                subprocess.run(base, cwd=root, stdout=log, stderr=subprocess.STDOUT)
                n = len(glob.glob(OUT + 'frames/f_*.png'))
                print(f'pass {attempt + 1}: {n} of {N} frames', time.strftime('%H:%M'), flush=True)
                if n >= N: break
                time.sleep(60*(attempt + 1))
    finally:
        os.rmdir(lock)


# ---------- composing ----------
def projector():
    cam = json.load(open(OUT + 'cam.json'))
    U, VX, ZMIN, RT, TOTAL = cam['unit_m'], cam['vx'], cam['zmin'], cam['route'], cam['total_m']
    cum = [min(i*0.25*U, TOTAL) for i in range(len(RT)-1)] + [TOTAL]
    def scene(p): return (p[0], p[1], (p[2]-ZMIN)*VX)
    def at(d):
        d = max(0.0, min(TOTAL, d)); i = max(0, min(len(cum)-2, bisect.bisect_right(cum, d)-1)); t = (d-cum[i])/max(1e-9, cum[i+1]-cum[i])
        return [RT[i][k] + (RT[i+1][k]-RT[i][k])*t for k in range(3)]
    def proj(f, p):
        c = cam['cam'][min(f, len(cam['cam']))-1]
        b = geo.screen_box(scene(c['cam']), scene(c['tgt']), c['lens'], H/W, scene(p), (0, 0, 0, 0), sensor_mm=36.0)
        return None if b is None else (b[0]*W, b[1]*H)
    step = max(1, len(RT)//1500)                       # ~1,500 points draw the line smoothly at this scale
    return proj, at, TOTAL, [(cum[i], RT[i]) for i in range(0, len(RT), step)] + [(TOTAL, RT[-1])]


_CALLOUT = {}


def callout_y(f, proj, pts):
    """Top of the longest-stretch callout: under the lowest point of the drawn course, above the list (its top row is y 1500),
    worked out once at the callout's first frame so it doesn't creep with the camera's drift."""
    if 'y' not in _CALLOUT:
        low = max((xy[1] for _, p in pts if (xy := proj(f, p))), default=1000)
        y = round(max(560, low + 36))                  # the block is ~280 px tall
        # a map reaching below 1210 leaves no room above the list: the list steps aside and the callout takes its place
        # (Bariloche, 2026-11-11: at the clamp it sat on pin 8 and the gold stretch)
        _CALLOUT['y'], _CALLOUT['over_list'] = (y, False) if y <= 1500 - 290 else (1520, True)
    return _CALLOUT['y']


def ease(u): u = max(0.0, min(1.0, u)); return u*u*(3 - 2*u)


def layers(f, proj, at, total, pts, st, tot_off, finish_gap, top, cta, cta_box, F):
    t = f/FPS
    prog = total*ease((t - T_IN)/(T_DONE - T_IN))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    line = [xy for dd, p in pts if dd <= prog and (xy := proj(f, p))]
    if prog > 0: line.append(proj(f, at(prog)))
    line = [p for p in line if p]
    if len(line) > 1:
        d.line(line, fill=(0, 0, 0, 120), width=14, joint='curve')
        d.line(line, fill=hud.C_MILE + (255,), width=7, joint='curve')
    lg = longest(st, finish_gap) if T_LONG <= t < SECS - 4.5 else None
    if lg:                                             # the longest stretch lit gold, under the pins
        a = round(255*min(1.0, (t - T_LONG)/0.5))
        d0, d1 = lg[3], lg[4] if lg[4] is not None else total
        seg = [xy for dd, p in pts if d0 <= dd <= d1 and (xy := proj(f, p))]
        if len(seg) > 1:
            g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            gd.line(seg, fill=(0, 0, 0, 150), width=18, joint='curve'); gd.line(seg, fill=hud.DOT + (255,), width=10, joint='curve')
            g.putalpha(g.getchannel('A').point(lambda v: v*a//255)); lay.alpha_composite(g); d = ImageDraw.Draw(lay)
    shown = [s for s in st if s['d'] <= prog]
    for i, s in enumerate(st, 1):                     # numbered pins, popping in over 6 frames as the trail reaches them
        if s['d'] > prog: continue
        xy = proj(f, at(s['d']))
        if not xy: continue
        k = min(1.0, (prog - s['d'])/max(1.0, total/len(st))*6) if s['d'] > 0 else 1.0
        r = 17*(0.6 + 0.4*k)
        d.ellipse((xy[0]-r-3, xy[1]-r-3, xy[0]+r+3, xy[1]+r+3), fill=(0, 0, 0, 150))
        d.ellipse((xy[0]-r, xy[1]-r, xy[0]+r, xy[1]+r), fill=hud.C_AID + (255,))
        num = str(i); tw = d.textlength(num, font=F['pin'])
        d.text((xy[0]-tw/2, xy[1]-F['pin'].size*0.62), num, font=F['pin'], fill=(26, 27, 38, 255))
    if prog > 0 and prog < total:                      # the runner's head of the line
        xy = proj(f, at(prog))
        if xy: d.ellipse((xy[0]-11, xy[1]-11, xy[0]+11, xy[1]+11), fill=hud.DOT + (255,), outline=(0, 0, 0, 160), width=3)
    lay = Image.alpha_composite(top, lay)
    # the list at the foot: the latest six stations, newest at the bottom
    rows = shown[-6:]; base_y = 1500
    if rows:
        def draw_rows(ld):
            for j, s in enumerate(rows):
                i = st.index(s) + 1; y = base_y + (j - len(rows) + 6)*58
                hud.Card.text(None, ld, (64, y), f'{i:>2}', F['row'], hud.C_AID, 0.06)
                hud.Card.text(None, ld, (130, y), s['name'].upper()[:22], F['row'], hud.INK, 0.06)
                right = (f'{UNIT} {s["off"]:.1f}' if s['off'] is not None else '') + (f'  +{s["gap"]:.1f}' if s['gap'] else '')
                rw = ld.textlength(right, font=F['row']) + 0.06*F['row'].size*len(right)
                hud.Card.text(None, ld, (W - 64 - rw, y), right, F['row'], hud.MUTED, 0.06)
        rl = S.shadowed((W, H), draw_rows, 6, 0.8)
        if t >= T_LONG and t < SECS - 4.5 and _CALLOUT.get('over_list'):
            k = max(0.0, 1 - (t - T_LONG)/0.4); rl.putalpha(rl.getchannel('A').point(lambda v: round(v*k)))
        lay.alpha_composite(rl)
    if t >= T_LONG:                                    # the longest stretch, then the closing line
        lg = longest(st, finish_gap)
        if lg and t < SECS - 4.5:
            a = round(255*min(1.0, (t - T_LONG)/0.5))
            y0 = callout_y(f, proj, pts)
            def draw_long(bd):
                hud.Card.text(None, bd, (64, y0), 'LONGEST STRETCH WITHOUT AID', F['label'], hud.MUTED + (a,), 0.12)
                bd.text((64, y0 + 40), f'{lg[0]:.1f} {UNIT.lower()}', font=F['big'], fill=hud.INK + (a,))
                bd.text((64, y0 + 210), f'{lg[1]} to {lg[2]}'[:34], font=F['sub'], fill=hud.DOT + (a,))
            lay.alpha_composite(S.shadowed((W, H), draw_long, 8, 0.85))
        if t >= SECS - 4.5: lay.alpha_composite(cta)
    return lay


def top_layer(name, st, tot_off, F):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    S.brand(lay, (64, 150))
    f, lines = S.fit(name, 96, 64, W - 128, S.fonts(2.0))
    y = 214
    for ln in lines:
        lay.alpha_composite(S.grad_text(ln, f, (64, y))); y += round(f.size*1.08)
    kick = f'EVERY AID STATION · {len(st)} OF THEM · {tot_off:g} {UNIT}'
    lay.alpha_composite(S.shadowed((W, H), lambda d: hud.Card.text(None, d, (64, y + 12), kick, F['label'], hud.C_AID, 0.12), 6))
    return lay


def video(cut='youtube'):
    st, tot_off, finish_gap = stations()
    proj, at, total, pts = projector()
    F0 = S.fonts(2.0); disp = F0['disp']
    F = dict(label=F0['cta'], row=F0['value'], pin=F0['small'], big=disp(150), sub=disp(54))
    top = top_layer(race_name(), st, tot_off, F)
    words = 'Plan it free at trailgoat.run'
    cta, cta_box = S.cta_layer({}, words, cta=cut)
    ff = hud.ffmpeg() if hasattr(hud, 'ffmpeg') else 'ffmpeg'
    dst = OUT + f'aids-silent-{cut}.mp4'
    p = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst],
                         stdin=subprocess.PIPE)
    for f in range(1, N + 1):
        src = OUT + f'frames/f_{min(f, N):04d}.png'
        im = Image.open(src).convert('RGBA') if os.path.exists(src) else Image.new('RGBA', (W, H), (26, 27, 38, 255))
        band = 520
        S.frost(im, (0, 0, W, band), S.band_mask(band))                # the glass under the title, as the race Shorts
        S.frost(im, (0, 1400, W, H), S.band_mask(H - 1400).transpose(Image.FLIP_TOP_BOTTOM), glass=0.5)
        if f/FPS >= SECS - 4.5:                                        # glass under the closing card, as finishreel
            bx = cta_box; S.frost(im, bx, S.band_mask(bx[3] - bx[1], 24).resize((bx[2] - bx[0], bx[3] - bx[1])), glass=0.55)
        im.alpha_composite(layers(f, proj, at, total, pts, st, tot_off, finish_gap, top, cta, cta_box, F))
        p.stdin.write(im.convert('RGB').tobytes())
        if f % 120 == 0: print(f'frame {f}/{N}', flush=True)
    p.stdin.close(); p.wait()
    print('SILENT', cut, N, 'frames', f'{N/FPS:.1f} s', dst)


# ---------- sound ----------
def track():
    import music_rights
    m = music_rights.cleared_music(FILM.get('music') or {}, SLUG)
    if not m: sys.exit('no cleared music for this film')
    return m


def mix(cut='youtube'):
    """The film's track under the silent Reel at -14 LUFS, from the loudest stretch of the piece; a gain-plus-limiter
    fallback when loudnorm leaves a quiet piece short (won.py's mix, 2026-11-04)."""
    m = track(); ff = hud.ffmpeg() if hasattr(hud, 'ffmpeg') else 'ffmpeg'
    silent = OUT + f'aids-silent-{cut}.mp4'; dur = N/FPS
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', m['file'], '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    L = [float(x) for x in re.findall(r'M:\s*(-?[\d.]+)', r)]; n = int(dur*10)
    def score(i):
        w = L[i:i + n]; return (sum(w)/len(w)) - (15 if min(w[:10]) < -45 else 0)
    start = max(range(0, max(1, len(L) - n), 5), key=score)/10 if len(L) > n else 0.0
    pre = f"atrim=start={start:.3f}:end={start + dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={dur - 1.5:.2f}:d=1.5"
    dst = DEST + f'{SLUG}-{YEAR}-aid-stations{"" if cut == "youtube" else "-social"}.mp4'
    def mux(af):
        subprocess.run([ff, '-y', '-loglevel', 'error', '-i', silent, '-i', m['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', dst], check=True)
        e = subprocess.run([ff, '-hide_banner', '-nostats', '-i', dst, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])
    got = mux(f'[1:a]{pre},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]')
    if got < -16.5:
        e = subprocess.run([ff, '-hide_banner', '-nostats', '-i', m['file'], '-af', pre + ',ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        gain = -14 - float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])
        got = mux(f'[1:a]{pre},volume={gain:.2f}dB,alimiter=limit=0.841:attack=5:release=50:level=0,aresample=48000[a]')
    print('MUXED', dst, f'{dur:.1f} s', 'music from', f'{start:.1f} s', f'{got:.1f} LUFS')


# ---------- words ----------
def words():
    st, tot_off, finish_gap = stations(); name = race_name(); lg = longest(st, finish_gap)
    desc = open(f'{STUDIO}/Films/{SLUG}/description.txt').read() if os.path.exists(f'{STUDIO}/Films/{SLUG}/description.txt') else ''
    page = (re.search(r'https://trailgoat\.run/course/[^\s)]+', desc) or [None])[0]
    up = f'{STUDIO}/Films/{SLUG}/uploaded.json'; film_id = json.load(open(up))['id'] if os.path.exists(up) else None
    handles = json.load(open(f'{STUDIO}/Films/_social/race-handles.json'))['handles']; ig = handles.get(SLUG)
    m = track()
    def fmt(v): return f'{v:.1f}'
    lst = '\n'.join(f'{i}. {s["name"]}' + (f', {UNIT.lower()} {fmt(s["off"])}' if s['off'] is not None else '') +
                    (f' (+{fmt(s["gap"])})' if s['gap'] else '') for i, s in enumerate(st, 1))
    long_line = f'Longest stretch without aid: {fmt(lg[0])} {UNIT.lower()}, {lg[1]} to {lg[2]}.' if lg else ''
    music = f'Music: "{m["title"]}" ({m["artist"]})' + (f'. {m["credit"]}' if m.get('credit') else '')
    open_line = f'Racing {name} {YEAR}? Every aid station in 30 seconds.'
    tags = '#trailrunning #ultramarathon #ultrarunning #trailgoat'
    utm = 'utm_source={}&utm_medium=social&utm_campaign=aids'
    cap = dict(
        instagram='\n\n'.join(x for x in [open_line + (f' @{ig}' if ig else ''), f'{len(st)} aid stations over {fmt(tot_off)} {UNIT.lower()}. {long_line}',
                                          lst, f'Plan your race free: {page.replace("https://", "") if page else "trailgoat.run"} (link in bio)',
                                          'The whole course in 3D: full film on our YouTube channel, TrailGoat', music, tags] if x),
        facebook='\n\n'.join(x for x in [open_line, f'{len(st)} aid stations over {fmt(tot_off)} {UNIT.lower()}. {long_line}', lst,
                                         f'Plan your race free: {page}?{utm.format("facebook")}' if page else '',
                                         f'The whole course in 3D: https://trailgoat.run/films?{utm.format("facebook")}', music, tags] if x),
        tiktok='\n\n'.join(x for x in [open_line, long_line, f'Plan your race free: {page.replace("https://", "") if page else "trailgoat.run"}',
                                       'The whole course in 3D: full film on our YouTube channel, TrailGoat', music, tags + ' #runtok'] if x))
    os.makedirs(DEST + 'captions', exist_ok=True)
    for k, v in cap.items(): open(DEST + f'captions/{k}.txt', 'w').write(v + '\n')
    title = f'{name} {YEAR}: every aid station in 30 seconds #Shorts'
    if len(title) > 100: title = f'{name}: every aid station #Shorts'
    yt_desc = '\n\n'.join(x for x in [f'{name} {YEAR}: every aid station on the real course in 3D, with the official distances and the gaps between them.',
                                      lst, long_line, f'The whole course, every aid station, in the full film:\n▶ https://youtu.be/{film_id}' if film_id else '',
                                      f'Plan this race free on TrailGoat:\n▶ {page}' if page else '', music] if x)
    meta = dict(title=title, description=yt_desc[:4900], tags=['trail running', 'ultramarathon', name, f'{name} {YEAR}', 'aid stations',
                'race week', '3D course map', 'TrailGoat', 'Shorts'], privacy='public', playlist='Race Shorts')
    if film_id: meta['related_video'] = film_id
    json.dump(meta, open(DEST + 'meta.json', 'w'), indent=1, ensure_ascii=False)
    print(title); print(cap['instagram'][:400])


if __name__ == '__main__':
    steps = {'shots': shots, 'render': render, 'video': lambda: video(sys.argv[3] if len(sys.argv) > 3 else 'youtube'),
             'mix': lambda: mix(sys.argv[3] if len(sys.argv) > 3 else 'youtube'), 'words': words}
    if CMD == 'all':
        shots(); render()
        for cut in ('youtube', 'social'): video(cut); mix(cut)
        words()
    else:
        steps[CMD]()

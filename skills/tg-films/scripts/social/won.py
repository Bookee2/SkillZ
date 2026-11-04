"""How it was won: a 9:16 Short that replays the decisive miles of a race from its official splits, on the race's own
3D flyover camera. Built from the Javelina Jundred 2026 Short (Films/javelina-jundred-100/won-2026/src), made generic
for the Monday after every filmed race (Kris, 2026-11-02: "Week before a race we post the short then Monday after we
post how it was won. I think the real value is in the how it was one. We may need bigger fonts on that too").

    python3 won.py <slug> plan                 # segments, frames to render, captions (no pictures)
    python3 won.py <slug> stills 0,40,300      # output frames as PNGs in the render folder, to look at
    python3 won.py <slug> video youtube|social # the silent Short

Inputs, per race and year (Films/<slug>/won-<year>/):
  src/race.json  official splits: gun, checkpoints [{id, name, mile, lat, lon}], runners [{key, name, sex, place,
                 finish_s, splits {checkpoint id: seconds since the gun}}]
  cfg.json       the cut: races {men|women: {hero, rivals, from_mi, to_mi, slow_mi?}}, order, open (which race's
                 decisive moment opens the Short), outro title/sub, instagram (the race's handle), handles {runner key:
                 Instagram handle} for the winners, confirmed by hand (the captions congratulate and tag them)
and the film's solved camera (Renders/flyovers/shorts/<slug>/won-<year>/cam.json, won_render.sh <slug> dry) and its
frames rendered at 2160x1920 (won_render.sh <slug> <ranges from plan>).

The film's camera follows a runner at the film's pace: here that runner IS each race's winner. Film frame -> the
winner's route distance -> the race time they got there (official splits, even pace between checkpoints) -> where
everyone else was at that time -> screen. Between checkpoints the positions are estimates; every gap called out at an
aid station is the official one.
"""
import bisect, json, math, os, re, subprocess, sys
TG = '/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts/scripts/flythrough'
sys.path.insert(0, TG)
import hud, short as S, geo           # noqa: E402
from PIL import Image, ImageDraw, ImageFilter

STUDIO = '/Volumes/KB SS/TrailGoat-Studio'
W, H, SW, FPS, MI = 1080, 1920, 2160, 24, 1609.344
GOLD, CYAN, LILAC, GREEN = hud.DOT, hud.DOWN, hud.C_ELE, hud.C_MILE
RIVAL_COLS = [CYAN, LILAC, GREEN]
OPEN_FRAMES = 48                     # the cold open: 2 s of the decisive moment at half speed
DIP = 8                              # frames of dark between segments

SLUG = sys.argv[1]
YEAR = int(os.environ.get('WON_YEAR', '2026'))
SRC = f'{STUDIO}/Films/{SLUG}/won-{YEAR}/'
OUTD = f'{STUDIO}/Renders/flyovers/shorts/{SLUG}/won-{YEAR}/'
CFG = json.load(open(SRC + 'cfg.json'))
KM = CFG.get('units') == 'km'        # a metric race (Mt.FUJI100): km on screen and in the words; miles stay inside
UNIT, UNIT_L = ('KM', 'km') if KM else ('MILE', 'mile')
def du(mile): return mile*1.609344 if KM else mile
DATA = json.load(open(SRC + 'src/race.json'))
FILM = json.load(open(f'{STUDIO}/Films/{SLUG}/film.json'))
SPEC = json.load(open(FILM['shots']))
FR = OUTD + 'frames/f_{:04d}.png'

# ---------- the route and the camera ----------
cam = json.load(open(OUTD + 'cam.json'))
U, VX, ZMIN = cam['unit_m'], cam['vx'], cam['zmin']
RT = cam['route']                                   # [x m, y m, z m ASL] every 0.25 units = every 25 m of the render's route
TOTAL = cam['total_m']
cum = [min(i*0.25*U, TOTAL) for i in range(len(RT)-1)] + [TOTAL]
def at(d):
    d = max(0.0, min(TOTAL, d)); i = max(0, min(len(cum)-2, bisect.bisect_right(cum, d)-1)); t = (d-cum[i])/max(1e-9, cum[i+1]-cum[i])
    return [RT[i][k] + (RT[i+1][k]-RT[i][k])*t for k in range(3)]
o = cam['origin']
def xy(lat, lon): return ((lon-o['lon'])*o['kx'], (lat-o['lat'])*o['ky'])
def scene(p): return (p[0], p[1], (p[2]-ZMIN)*VX)
def film_d(f): return cam['cam'][f-1]['dist_m']
SHOTS = SPEC['shots']
def is_leg(i):
    mi = SHOTS[i].get('mi') or [0, 0]; return mi[0] != mi[1]
LEGS = [f for f in range(1, cam['frames']+1) if is_leg(cam['cam'][f-1]['shot'])]
FINISH_SHOT = next(i for i, s in enumerate(SHOTS) if 'FINISH' in s.get('name', '').upper() and not is_leg(i)
                   and i > cam['cam'][LEGS[-1]-1]['shot'])

# ---------- the checkpoints on our route ----------
CPS = DATA['checkpoints']
OFF_TOTAL = float(DATA.get('official_total_mi') or next(c['mile'] for c in CPS if c['id'] == 'finish'))
def guess(mile): return mile/OFF_TOTAL*TOTAL
def norm(s): return re.sub(r'[^a-z]', '', s.lower())
PINS = []                    # every visit of every aid pin: the label lists the official miles of return visits
for m, lab in SPEC.get('aids', []):
    nm = hud.aid_name(lab.split(' · ')[0]); PINS.append((m*MI, nm))
    k = 1/1.609344 if ' KM ' in f' {lab} ' else 1           # a metric film's labels list km
    for x in re.findall(r'/ *(\d+(?:\.\d+)?)', lab): PINS.append((guess(float(x)*k), nm))
def place_cp(c):
    if c['id'] == 'finish': return TOTAL, 'finish'
    g = guess(c['mile'])
    if c.get('lat') is not None and c.get('lon') is not None:
        px, py = xy(c['lat'], c['lon'])
        best = min((i for i in range(len(RT)) if abs(cum[i]-g) < 5000), key=lambda i: math.hypot(RT[i][0]-px, RT[i][1]-py), default=None)
        if best is not None and math.hypot(RT[best][0]-px, RT[best][1]-py) < 800: return cum[best], 'coords'
    key = norm(c['name'].split('(')[0].replace('Inbound', '').replace('Outbound', '').replace(' In', '').replace(' Out', ''))
    words = [w for w in re.findall(r'[a-z]+', c['name'].lower()) if len(w) > 3 and w not in ('inbound', 'outbound', 'station', 'aid')]
    cand = [p for p in PINS if abs(p[0]-g) < 3*MI and (key and (key in norm(p[1]) or norm(p[1]) in key) or any(w in p[1].lower() for w in words))]
    if cand: return min(cand, key=lambda p: abs(p[0]-g))[0], 'pin ' + min(cand, key=lambda p: abs(p[0]-g))[1]
    return g, 'scaled'
for c in CPS: c['d'], c['how'] = place_cp(c)
CP_BY = {c['id']: c for c in CPS}

def off_mi(d):
    """official mile at route distance d (the checkpoints map one to the other)"""
    pts = sorted([(0.0, 0.0)] + [(c['d'], c['mile']) for c in CPS])
    for (d0, m0), (d1, m1) in zip(pts, pts[1:]):
        if d <= d1: return m0 + (m1-m0)*(d-d0)/max(1e-9, d1-d0)
    return OFF_TOTAL
def d_of_mi(m):
    pts = sorted([(0.0, 0.0)] + [(c['mile'], c['d']) for c in CPS])
    for (m0, d0), (m1, d1) in zip(pts, pts[1:]):
        if m <= m1: return d0 + (d1-d0)*(m-m0)/max(1e-9, m1-m0)
    return TOTAL

RUN = {r['key']: r for r in DATA['runners']}
for _k, _v in CFG.get('labels', {}).items(): RUN[_k]['short'] = _v     # e.g. two Macdonalds at Leadville
def runner(key):
    """[(route d, seconds since the gun)] where this runner was timed, in course order"""
    t = RUN[key]['splits']; pts = [(0.0, 0.0)] + [(CP_BY[k]['d'], v) for k, v in t.items() if k in CP_BY]
    if RUN[key].get('finish_s') and 'finish' not in t: pts.append((TOTAL, RUN[key]['finish_s']))
    return sorted(pts)
def d_at(pts, T):
    if T <= pts[0][1]: return pts[0][0]
    for (d0, t0), (d1, t1) in zip(pts, pts[1:]):
        if T <= t1: return d0 + (d1-d0)*(T-t0)/max(1e-9, t1-t0)
    return pts[-1][0]
def t_at(pts, d):
    for (d0, t0), (d1, t1) in zip(pts, pts[1:]):
        if d <= d1: return t0 + (t1-t0)*(d-d0)/max(1e-9, d1-d0)
    return pts[-1][1]

def hms(s):
    s = int(s); return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}"        # truncated, as official results are
def ms(s):
    s = int(round(abs(s))); return f"{s//60}:{s%60:02d}" if s < 3600 else hms(s)
def surname(key): return RUN[key].get('short') or RUN[key]['name'].split()[-1].upper()

# ---------- the cut ----------
RACES = {}
for r, c in CFG['races'].items():
    RACES[r] = dict(hero=(c['hero'], surname(c['hero']), GOLD),
                    rivals=[(k, surname(k), RIVAL_COLS[i]) for i, k in enumerate(c['rivals'])],
                    title={'men': "Men's race", 'women': "Women's race"}.get(r, r), cfg=c)

def frames_between(d0, d1):
    return [f for f in LEGS if d0 <= film_d(f) <= d1]

def build_segs():
    segs = []
    for r in CFG['order']:
        c = CFG['races'][r]
        fr = frames_between(d_of_mi(c['from_mi']), d_of_mi(c.get('to_mi', OFF_TOTAL)) - 1)
        seg = dict(race=r, f0=fr[0], f1=fr[-1], hold=c.get('hold', 36))
        if c.get('slow_mi'):
            seg['slow'] = next(f for f in fr if film_d(f) >= d_of_mi(c['slow_mi']))
        segs.append(seg)
    fin = [f for f in range(1, cam['frames']+1) if cam['cam'][f-1]['shot'] == FINISH_SHOT]
    segs.append(dict(race='outro', f0=fin[0], f1=min(fin[-1], fin[0] + CFG.get('outro_frames', 120))))
    return segs
SEGS = build_segs()
SEGF = {}

# ---------- where everyone is ----------
def landscape(f, p):
    c = cam['cam'][f-1]
    b = geo.screen_box(scene(c['cam']), scene(c['tgt']), c['lens'], 1920/SW, scene(p), (0, 0, 0, 0), sensor_mm=36.0)
    return None if b is None else (b[0]*SW, b[1]*H)

def state(f, race):
    cfg = RACES[race]; key, name, col = cfg['hero']; Hp = runner(key)
    d = film_d(f); T = t_at(Hp, d)
    people = [dict(key=key, name=name, col=col, d=d, hero=True, xy=landscape(f, at(d)), pts=Hp)]
    for k, n, c in cfg['rivals']:
        P = runner(k); dr = d_at(P, T)
        people.append(dict(key=k, name=n, col=c, d=dr, hero=False, xy=landscape(f, at(dr)), pts=P))
    return T, people

def state_at(a, b, w, race):
    Ta, pa = state(a, race)
    if w == 0 or a == b: return Ta, pa
    Tb, pb = state(b, race)
    for p, q in zip(pa, pb):
        p['d'] = p['d'] + (q['d'] - p['d'])*w
        if p['xy'] and q['xy']: p['xy'] = (p['xy'][0] + (q['xy'][0] - p['xy'][0])*w, p['xy'][1] + (q['xy'][1] - p['xy'][1])*w)
    return Ta + (Tb - Ta)*w, pa

def lead_frame(race):
    """the first frame of the race's segment where the hero is in front of every rival (None: led throughout)"""
    s = next(x for x in SEGS if x['race'] == race); was_behind = False
    for f in range(s['f0'], s['f1'] + 1):
        T, ppl = state(f, race); ahead = [p for p in ppl[1:] if p['d'] > ppl[0]['d']]
        if ahead: was_behind = True
        elif was_behind: return f
    return None

def stakes(race):
    """the cold open's lines: the biggest gap the winner closed on the runner they passed, where, and the margin; or,
    for a winner who led throughout, the margin"""
    st = story(race); key = st['key']; margin = st['margin']
    won = f"{surname(key).title()} won by {ms(margin) if margin >= 60 else f'{round(margin)} seconds'}" if margin else f"{surname(key).title()} won"
    if st['worst'] >= 60: return f"{ms(st['worst'])}", "DOWN", f"AT {UNIT} {du(st['w_cp']['mile']):.0f}", won
    return f"{ms(margin)}" if margin else 'WIRE', "AHEAD", "AT THE FINISH", won

def crop_path(seg):
    s = SEGS[seg]; frames = range(s['f0'], s['f1'] + 1); race = s['race'] if s['race'] in RACES else CFG['order'][-1]
    want, hx = [], []
    for f in frames:
        T, ppl = state(f, race); h = ppl[0]['xy'][0] if ppl[0]['xy'] else SW/2; c = h
        near = [p for p in ppl[1:] if p['xy'] and abs(p['d'] - ppl[0]['d']) < 0.45*MI and abs(p['xy'][0] - h) < 620]
        if near:
            r = min(near, key=lambda p: abs(p['d'] - ppl[0]['d'])); c = (h + r['xy'][0])/2
        want.append(c); hx.append(h)
    sig = 14; k = [math.exp(-0.5*(i/sig)**2) for i in range(-3*sig, 3*sig + 1)]
    def smooth(v):
        out = []
        for i in range(len(v)):
            acc = wt = 0.0
            for j, kk in enumerate(k):
                t = i + j - 3*sig
                if 0 <= t < len(v): acc += v[t]*kk; wt += kk
            out.append(acc/wt)
        return out
    c = smooth(want)
    c = [min(max(ci, h - 0.20*W), h + 0.30*W) for ci, h in zip(c, hx)]
    c = smooth(c)
    c = [min(max(ci, h - 0.24*W), h + 0.33*W) for ci, h in zip(c, hx)]
    return [min(max(ci, W/2), SW - W/2) for ci in c]

# ---------- drawing (bigger than Javelina's: Kris, 2026-11-02 "We may need bigger fonts") ----------
F = S.fonts(2.0)
TAG = S.fonts(2.4)['cta']
RACE_PX, TITLE_PX, CAP_S = 92, 64, 2.6

LAST_SPOT = {}                       # each runner's last tag position, kept while it stays clear (no flicker)

def tag_size(name):
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    return probe.textlength(name, font=TAG) + 0.12*TAG.size*len(name) + 28, TAG.size + 16

def place_tag(xy, name, hero, side, taken):
    """the tag's box: right or left of the dot, then the four diagonals, the first that stays clear of everything
    already on screen (the leaderboard band, the open's panel, other tags and dots); the last frame's spot first"""
    x, y = xy; r = 19 if hero else 15; w, h = tag_size(name)
    spots = {'right': (x + r + 14, y - h/2), 'left': (x - r - 14 - w, y - h/2), 'below-right': (x + r - 6, y + r + 10),
             'below-left': (x - r + 6 - w, y + r + 10), 'above-right': (x + r - 6, y - r - 10 - h), 'above-left': (x - r + 6 - w, y - r - 10 - h)}
    order = (['right', 'left'] if side > 0 else ['left', 'right']) + ['below-right', 'below-left', 'above-right', 'above-left']
    if LAST_SPOT.get(name) in order: order.remove(LAST_SPOT[name]); order.insert(0, LAST_SPOT[name])
    def box(k):
        tx, ty = spots[k]; tx = min(max(tx, 24), W - 24 - w); return (tx, ty, tx + w, ty + h)
    def clear(bx):
        return bx[1] > 0 and bx[3] < H and not any(bx[0] < o[2] + 6 and o[0] < bx[2] + 6 and bx[1] < o[3] + 6 and o[1] < bx[3] + 6 for o in taken)
    pick = next((k for k in order if clear(box(k))), order[0])
    LAST_SPOT[name] = pick; bx = box(pick); taken.append(bx); return bx

def dot(lay, xy, col, name, hero, bx):
    d = ImageDraw.Draw(lay); x, y = xy; r = 19 if hero else 15
    glow = Image.new('RGBA', lay.size, (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse((x - r*2.2, y - r*2.2, x + r*2.2, y + r*2.2), fill=col + (110,))
    lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
    d.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=(16, 17, 26, 235))
    d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
    if bx:
        d.rounded_rectangle(bx, 12, fill=(26, 27, 38, 215), outline=col + (200,), width=2)
        hud.Card.text(None, d, (bx[0] + 14, bx[1] + 7), name, TAG, col, 0.12)

def draw_people(lay, vis, taken):
    """vis: [(person, (x, y))]. The dots claim their spots first, then the winner's tag, then the others'; drawn rivals
    first so the winner's dot sits on top"""
    for p, (x, y) in vis:
        r = 19 if p['hero'] else 15; taken.append((x - r - 4, y - r - 4, x + r + 4, y + r + 4))
    hx = next((xy[0] for p, xy in vis if p['hero']), W/2)
    boxes = {}
    for p, xy in sorted(vis, key=lambda v: not v[0]['hero']):
        mine = [t for t in taken if not (t[0] <= xy[0] <= t[2] and t[1] <= xy[1] <= t[3])]     # not its own dot
        side = (1 if xy[0] < W*0.62 else -1) if p['hero'] else (1 if xy[0] >= hx else -1)
        bx = place_tag(xy, p['name'], p['hero'], side, mine); taken.append(bx); boxes[p['name']] = bx
    for p, xy in sorted(vis, key=lambda v: v[0]['hero']):
        dot(lay, xy, p['col'], p['name'], p['hero'], boxes[p['name']])

def edge_chip(lay, xy, col, name, slot, top):
    d = ImageDraw.Draw(lay); x, y = xy
    tw = d.textlength(name, font=TAG) + 0.12*TAG.size*len(name); pad, th = 14, TAG.size + 16
    bx = min(max(x - tw/2 - pad, 40), W - 200 - tw - 2*pad)
    up = y < H/2
    by = (top + 40 + slot*(th + 34)) if up else (1420 - slot*(th + 34))
    d.rounded_rectangle((bx, by, bx + tw + 2*pad, by + th), 12, fill=(26, 27, 38, 215), outline=col + (200,), width=2)
    hud.Card.text(None, d, (bx + pad, by + 7), name, TAG, col, 0.12)
    cx, cy, r = bx + (tw + 2*pad)/2, (by - 16 if up else by + th + 16), 12
    d.polygon([(cx - r, cy + (r*0.6 if up else -r*0.6)), (cx + r, cy + (r*0.6 if up else -r*0.6)), (cx, cy - (r*0.8 if up else -r*0.8))], fill=col + (255,))

def top_block(title, sub=None, scrim_h=700, scrim_a=160):
    """the race name always on top (Kris on Javelina v2: "we need to have the race name at the top throughout")"""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); x = 64
    scrim = Image.new('L', (1, scrim_h))
    for y in range(scrim_h): scrim.putpixel((0, y), round(scrim_a*max(0.0, 1 - y/scrim_h)**1.6))
    sc = Image.new('RGBA', (W, scrim_h), hud.PANEL[:3] + (0,)); sc.putalpha(scrim.resize((W, scrim_h))); lay.alpha_composite(sc)
    S.brand(lay, (x, 176)); y = 234
    rf, rl = S.fit(CFG['race_name'], RACE_PX, 68, W - 2*x, F)
    for ln in rl: lay.alpha_composite(S.grad_text(ln, rf, (x, y))); y += round(rf.size*1.12)
    if title:
        tf, tl = S.fit(title, TITLE_PX, 52, W - 2*x, F)
        for ln in tl:
            lay.alpha_composite(S.shadowed((W, H), lambda d, ln=ln, y=y: d.text((x, y), ln, font=tf, fill=hud.INK), 6)); y += round(tf.size*1.14)
    if sub:
        sf = S.fonts(2.4)['stat']
        lay.alpha_composite(S.shadowed((W, H), lambda d: hud.Card.text(None, d, (x, y + 4), sub, sf, hud.MUTED, 0.04), 5))
        y += round(sf.size*1.5)
    return lay, y + 12

class Board:
    """the runners in the clip as a leaderboard: the winner's mile and the race clock, then one row per runner in race
    order (place, colour, name, gap to the leader where that runner is now); the winner's row gold-tinted, rows slide
    when places change"""
    HEAD, ROW, PAD = 64, 72, 26
    def __init__(self, width=780):
        self.w, self.y = width, {}
        f = S.fonts(2.45); self.val, self.small = f['value'], f['small']
    def height(self, n): return self.HEAD + n*self.ROW + 14
    def draw(self, T, ppl, mile, snap):
        order = sorted(ppl, key=lambda p: -p['d']); lead = order[0]; n = len(order)
        im = Image.new('RGBA', (self.w, self.height(n)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, self.w - 1, self.height(n) - 1), 26, fill=hud.PANEL[:3] + (176,), outline=hud.EDGE, width=2)
        card = hud.Card.text
        card(None, d, (self.PAD, 17), f'{UNIT} {du(mile):.1f}', self.small, hud.C_MILE, 0.1)
        clock = hms(T); cw = d.textlength(clock, font=self.small) + 0.1*self.small.size*len(clock)
        card(None, d, (self.w - self.PAD - cw, 17), clock, self.small, hud.C_CLOCK, 0.1)
        d.line((self.PAD, self.HEAD, self.w - self.PAD, self.HEAD), fill=hud.EDGE, width=2)
        for i, p in enumerate(order):
            target = self.HEAD + 7 + i*self.ROW
            y = target if snap or p['name'] not in self.y else self.y[p['name']] + (target - self.y[p['name']])*0.3
            self.y[p['name']] = y
            if p['hero']: d.rounded_rectangle((8, y, self.w - 9, y + self.ROW - 6), 16, fill=GOLD + (40,))
            ty = y + (self.ROW - 6 - self.val.size)/2 - 2
            card(None, d, (self.PAD, ty), str(i + 1), self.val, hud.MUTED)
            cx, cy, r = self.PAD + 58, y + (self.ROW - 6)/2 + 2, 12
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=p['col'] + (255,))
            card(None, d, (cx + 30, ty), p['name'], self.val, GOLD if p['hero'] else hud.INK, 0.04)
            if p is lead: gtxt, gcol = 'LEAD', hud.FIN
            else: gtxt, gcol = f"+{ms(T - t_at(lead['pts'], p['d']))}", (hud.UP if p['hero'] else hud.MUTED)
            gw = d.textlength(gtxt, font=self.val) + 0.04*self.val.size*len(gtxt)
            card(None, d, (self.w - self.PAD - gw, ty), gtxt, self.val, gcol, 0.04)
        return im
    def compact(self, T, ppl, mile):
        """the board folded to one line while the winner runs high in the frame: mile, the winner, their gap"""
        order = sorted(ppl, key=lambda p: -p['d']); lead = order[0]; h = next(p for p in ppl if p['hero'])
        hh = self.HEAD + 10
        im = Image.new('RGBA', (self.w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, self.w - 1, hh - 1), 26, fill=hud.PANEL[:3] + (176,), outline=hud.EDGE, width=2)
        card = hud.Card.text; ty = (hh - self.val.size)/2 - 2
        card(None, d, (self.PAD, (hh - self.small.size)/2 - 1), f'{UNIT} {du(mile):.1f}', self.small, hud.C_MILE, 0.1)
        place = order.index(h) + 1
        if h is lead: gtxt, gcol = 'LEAD', hud.FIN
        else: gtxt, gcol = f"+{ms(T - t_at(lead['pts'], h['d']))}", hud.UP
        gw = d.textlength(gtxt, font=self.val) + 0.04*self.val.size*len(gtxt)
        card(None, d, (self.w - self.PAD - gw, ty), gtxt, self.val, gcol, 0.04)
        nw = d.textlength(h['name'], font=self.val) + 0.04*self.val.size*len(h['name'])
        nx = self.w - self.PAD - gw - 30 - nw
        card(None, d, (nx, ty), h['name'], self.val, GOLD, 0.04)
        cx, cy, r = nx - 24, hh/2 + 1, 12
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=h['col'] + (255,))
        card(None, d, (cx - r - 16 - d.textlength(str(place), font=self.val), ty), str(place), self.val, hud.MUTED)
        return im

BOARD = Board()
FOLD = {}                            # per segment, per output frame: 0 the full board .. 1 folded to one line

def fold_plan(P):
    """fold the board while the winner's dot would sit under it (above y 830), opening again when they drop below 960;
    smoothed so it slides rather than snaps"""
    for i, s in enumerate(SEGS):
        if s['race'] not in RACES: continue
        rows = [(a, b, w) for sg, a, b, w, fi in P if sg == i]
        want = []
        for a, b, w in rows:
            T, ppl = state_at(a, b, w, s['race']); y = ppl[0]['xy'][1] if ppl[0]['xy'] else H
            want.append(1.0 if y < 830 else 0.0 if y > 960 else (960 - y)/130)
        sig = 8; k = [math.exp(-0.5*(j/sig)**2) for j in range(-3*sig, 3*sig + 1)]
        out = []
        for j in range(len(want)):
            acc = wt = 0.0
            for q, kk in enumerate(k):
                t = j + q - 3*sig
                if 0 <= t < len(want): acc += max(want[max(0, t - 6):t + 7])*kk; wt += kk    # max: fold a little early
            out.append(min(1.0, acc/wt))
        FOLD[i] = out

def caption(lay, y, text, col, a=1.0, s=CAP_S):
    if a <= 0: return
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); probe = ImageDraw.Draw(c); fnt = S.fonts(s)['stat']
    while probe.textlength(text, font=fnt)*1.04 > W - 128 and s > 1.7:
        s -= 0.1; fnt = S.fonts(s)['stat']
    c.alpha_composite(S.shadowed((W, H), lambda d: hud.Card.text(None, d, (64, y), text, fnt, col, 0.04), 6, 0.9))
    if a < 1: c.putalpha(c.getchannel('A').point(lambda v: round(v*a)))
    lay.alpha_composite(c)

def ordinal(n): return {1: '1ST', 2: '2ND', 3: '3RD'}.get(n, f'{n}TH')

def finish_lines(race):
    key, name, _ = RACES[race]['hero']; me = RUN[key]
    others = sorted((r for r in DATA['runners'] if r['sex'] == me['sex'] and r['key'] != key and r.get('finish_s')), key=lambda r: r['finish_s'])[:2]
    return f"{name} WINS · {hms(me['finish_s'])}", ' · '.join(f"{surname(r['key'])} +{ms(r['finish_s'] - me['finish_s'])}" for r in others)

def events(race):
    """(film frame from, until, text, colour): where the winner stood, the official gap at each aid station crossed in
    the clip, each pass as it happens, the result"""
    cfg = RACES[race]; s = next(x for x in SEGS if x['race'] == race); out = []
    hk, hn = cfg['hero'][0], cfg['hero'][1]; keys = [hk] + [k for k, _, _ in cfg['rivals']]
    T, ppl = state(s['f0'], race); h = ppl[0]; ahead = [p for p in ppl[1:] if p['d'] > h['d']]
    m0 = off_mi(h['d'])
    if ahead:
        lead = max(ahead, key=lambda p: p['d'])
        out.append((s['f0'], s['f0'] + 4*FPS, f"{UNIT} {du(m0):.0f}: {hn} {ordinal(1 + len(ahead))}, {ms(T - t_at(lead['pts'], h['d']))} BACK", hud.MUTED))
    else:
        nxt = max(ppl[1:], key=lambda p: p['d'])
        out.append((s['f0'], s['f0'] + 4*FPS, f"{UNIT} {du(m0):.0f}: {hn} LEADS BY {ms(T - t_at(nxt['pts'], h['d']))}", hud.MUTED))
    for c in CPS:
        if c['id'] == 'finish': continue
        f = next((f for f in range(s['f0'] + 1, s['f1'] + 1) if film_d(f - 1) < c['d'] <= film_d(f)), None)
        times = {k: RUN[k]['splits'].get(c['id']) for k in keys}
        if f is None or times[hk] is None: continue
        others = [t for k, t in times.items() if k != hk and t is not None]
        if not others: continue
        place = re.sub(r'\s*\(.*?\)', '', c['name']).upper()
        if all(times[hk] < t for t in others): text = f"{place}: {hn} LEADS BY {ms(min(others) - times[hk])}"
        else: text = f"{place}: {hn} {ms(times[hk] - min(others))} BACK"
        out.append((f, f + int(3*FPS), text, hud.C_AID))
    prev = None
    for f in range(s['f0'], s['f1'] + 1):
        T, ppl = state(f, race); h = ppl[0]
        ahead = {p['name'] for p in ppl[1:] if p['d'] > h['d']}
        if prev is not None:
            for n in prev - ahead:
                out.append((f, f + int(2.6*FPS), f"{hn} {'TAKES THE LEAD' if not ahead else 'PASSES ' + n}", GOLD))
        prev = ahead
    out.append((s['f1'], 10**9, finish_lines(race)[0], hud.FIN))
    out.sort()
    for i in range(1, len(out) - 1):
        a0, a1, t, c = out[i]; p0 = out[i-1][0]
        if a0 < p0 + int(2.4*FPS): out[i] = (p0 + int(2.4*FPS), max(a1, p0 + int(2.4*FPS) + 2*FPS), t, c)
    return out

def plan():
    """[(segment, film frame a, frame b, weight of b, frame within segment)]: the cold open (the decisive moment at
    half speed), then each race at film speed, half speed from its `slow` frame, the last frame held with the result"""
    out = []
    lf = lead_frame(CFG['open'])
    s0 = next(x for x in SEGS if x['race'] == CFG['open'])
    c = lf if lf else s0['f1'] - FPS
    oa, ob = max(s0['f0'], c - 18), min(s0['f1'], c + 6)
    seq = []; t = float(oa)
    while t <= ob and len(seq) < OPEN_FRAMES:
        a = int(t); seq.append((a, min(a + 1, ob), t - a)); t += 0.5
    out += [(-1, a, b, w, k) for k, (a, b, w) in enumerate(seq)]
    for i, s in enumerate(SEGS):
        seq = []
        slow = s.get('slow') or s['f1'] + 1
        seq += [(f, f, 0.0) for f in range(s['f0'], min(slow, s['f1'] + 1))]
        t = float(slow)
        while t <= s['f1']:
            a = int(t); w = t - a; seq.append((a, min(a + 1, s['f1']), w)); t += 0.5
        seq += [(s['f1'], s['f1'], 0.0)]*s.get('hold', 0)
        out += [(i, a, b, w, k) for k, (a, b, w) in enumerate(seq)]
    return out, (oa, ob)

def _round_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m

OPEN_Y = [1010]
def open_panel(t):
    """the cold open's stakes, counting up over the first 0.8 s; low in the frame unless the pass is (OPEN_Y)"""
    big_t, word, where, won = STAKES
    m = re.match(r'(\d+):(\d\d)$', big_t)
    if m and t < 0.8:
        u = t/0.8; total = int(m[1])*60 + int(m[2]); v = round(total*(1 - (1 - u)**3)); big_t = f'{v//60}:{v%60:02d}'
    big, mid, small = F['disp'](220), F['disp'](84), F['disp'](60)
    probe = ImageDraw.Draw(Image.new('L', (1, 1))); x = 64; y0 = OPEN_Y[0]
    y1 = y0 + 22 + big.size + round(mid.size*1.25) + round(small.size*1.3) + 30
    box = (36, y0, W - 36, y1)
    def draw(d):
        y = y0 + 4
        d.text((x, y), big_t, font=big, fill=hud.UP)
        d.text((x + probe.textlength(big_t, font=big) + 26, y + big.size - round(mid.size*1.2)), word, font=mid, fill=hud.UP)
        y += big.size + 18
        d.text((x, y), where, font=mid, fill=hud.INK); y += round(mid.size*1.25)
        d.text((x, y), won, font=small, fill=GOLD)
    return S.shadowed((W, H), draw, 8, 0.85), box

def compose(seg, a, b, w, fi, n, base, cx, ev, tops):
    x0 = round(cx - W/2); f = a + w
    im = base.crop((x0, 0, x0 + W, H)).convert('RGBA')
    if seg == -1:
        top, y = tops['open']; band = y + 50
        S.frost(im, (0, 0, W, band), S.band_mask(band)); im.alpha_composite(top)
        T, ppl = state_at(a, b, w, CFG['open'])
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        layer, box = open_panel(fi/FPS); aa = min(1.0, (fi + 1)/4)
        vis = [(p, (p['xy'][0] - x0, p['xy'][1])) for p in ppl if p['xy'] and 20 < p['xy'][0] - x0 < W - 20 and band < p['xy'][1] < H - 380
               and not (box[1] - 20 < p['xy'][1] < box[3] + 20)]
        draw_people(lay, vis, [(0, 0, W, band), box])
        im.alpha_composite(lay)
        S.frost(im, box, S.rounded(box, aa), glass=0.62)
        if aa < 1: layer.putalpha(layer.getchannel('A').point(lambda v: round(v*aa)))
        im.alpha_composite(layer)
        return im
    s = SEGS[seg]; race = s['race']
    if race == 'outro':
        top, y = tops['outro']
        band = y + 2*round(S.fonts(2.4)['stat'].size*1.4 + S.fonts(2.2)['stat'].size*1.75) + 90   # under the results too
        S.frost(im, (0, 0, W, band), S.band_mask(band, 120), glass=0.55); im.alpha_composite(top)
        if fi < n - round(2.6*FPS):
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); yy = y
            for r in CFG['order']:
                l1, l2 = finish_lines(r)
                caption(lay, yy, l1, GOLD, s=2.4); yy += round(S.fonts(2.4)['stat'].size*1.4)
                caption(lay, yy, l2, hud.MUTED, s=2.2); yy += round(S.fonts(2.2)['stat'].size*1.75)
            im.alpha_composite(lay)
        else:
            cta, box = tops['cta']; aa = min(1.0, (fi - (n - round(2.6*FPS)))/(0.4*FPS))
            S.frost(im, box, S.rounded(box, aa), glass=0.5)
            layer = cta.copy(); layer.putalpha(layer.getchannel('A').point(lambda v: round(v*aa))); im.alpha_composite(layer)
        return im
    top, y_board = tops[race]
    T, ppl = state_at(a, b, w, race); h = ppl[0]
    c = FOLD.get(seg, [0.0]*(fi + 1))[fi]
    bh = round(BOARD.height(len(ppl))*(1 - c) + (BOARD.HEAD + 10)*c); band = y_board + bh + 110
    S.frost(im, (64, y_board, 64 + BOARD.w, y_board + bh), _round_mask(BOARD.w, bh, 26), glass=0.0, blur=10)
    im.alpha_composite(top)
    full = BOARD.draw(T, ppl, off_mi(h['d']), SNAP[0] or fi == 0)
    if c < 0.5:                       # the full board fades out as it folds, then the one line fades in: never both
        f_ = full.crop((0, 0, BOARD.w, bh)) if bh < full.size[1] else full
        if c > 0: f_.putalpha(f_.getchannel('A').point(lambda v: round(v*(1 - 2*c))))
        im.alpha_composite(f_, (64, y_board))
    else:
        one = BOARD.compact(T, ppl, off_mi(h['d']))
        if c < 1: one.putalpha(one.getchannel('A').point(lambda v: round(v*(2*c - 1))))
        im.alpha_composite(one, (64, y_board))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    yc = y_board + bh + 24
    live = [e for e in ev if e[0] <= f <= e[1]]
    if live:
        a0, a1, text, col = max(live, key=lambda e: e[0])
        sf = SEGF[seg]; i0 = bisect.bisect_left(sf, a0); i1 = bisect.bisect_right(sf, a1) - 1
        ca = min(1.0, (fi - i0 + 1)/6, (i1 - fi + 1)/6)
        cbox = (40, yc - 14, W - 40, yc + round(S.fonts(CAP_S)['stat'].size*1.25) + 14)   # glass, so map labels pass under the line
        S.frost(im, cbox, S.rounded(cbox, max(0.0, ca)), glass=0.45)
        caption(lay, yc, text, col, ca)
    slots = {True: 0, False: 0}; vis = []
    for p in ppl:
        if not p['xy']: continue
        x, y = p['xy'][0] - x0, p['xy'][1]
        if p['hero'] or (20 < x < W - 20 and band < y < H - 380): vis.append((p, (x, y)))
        else:
            up = y < H/2; edge_chip(lay, (min(max(x, 60), W - 60), y), p['col'], p['name'], slots[up], band); slots[up] += 1
    draw_people(lay, vis, [(0, 0, W, band)])
    im.alpha_composite(lay)
    return im

def build_tops(cut):
    tops = {'open': top_block('How it was won')}
    for r in CFG['order']: tops[r] = top_block(RACES[r]['title'], scrim_h=640, scrim_a=150)
    tops['outro'] = top_block(CFG.get('outro_title', 'The result'), CFG.get('outro_sub'))
    tops['cta'] = S.cta_layer({}, f"The whole {du(OFF_TOTAL):.0f} {UNIT_L}s" if not KM else f"The whole {du(OFF_TOTAL):.0f} km", cut)
    return tops

SNAP = [False]
STAKES = None
def run(cut='youtube', stills=None):
    global STAKES
    STAKES = stakes(CFG['open'])
    P, (oa, ob) = plan(); tops = build_tops(cut); SNAP[0] = bool(stills)
    ys = [state(f, CFG['open'])[1][0]['xy'] for f in range(oa, ob + 1)]
    ys = [xy[1] for xy in ys if xy]
    if ys and sum(ys)/len(ys) > 960: OPEN_Y[0] = tops['open'][1] + 70     # the pass is low: the stakes go up under the title
    paths = {i: crop_path(i) for i in range(len(SEGS))}
    s0 = next(i for i, x in enumerate(SEGS) if x['race'] == CFG['open'])
    evs = {r: events(r) for r in CFG['order']}
    for r, ev in evs.items(): print(r, [(a, t) for a, b, t, c in ev])
    want = set(stills) if stills else None
    proc = None
    if not stills:
        proc = subprocess.Popen([hud.ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                                 '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
                                 '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart',
                                 OUTD + f'won-silent-{cut}.mp4'], stdin=subprocess.PIPE)
    count = {i: sum(1 for e in P if e[0] == i) for i in [-1] + list(range(len(SEGS)))}
    for i in range(len(SEGS)): SEGF[i] = [a + w for sg, a, b, w, fi in P if sg == i]
    fold_plan(P)
    cache = {}
    def frame(f):
        if f not in cache:
            if len(cache) > 4: cache.pop(next(iter(cache)))
            cache[f] = Image.open(FR.format(f)).convert('RGB')
        return cache[f]
    for k, (seg, a, b, w, fi) in enumerate(P):
        if want is not None and k not in want: continue
        base = frame(a) if w == 0 or a == b else Image.blend(frame(a), frame(b), w)
        ps = paths[s0 if seg == -1 else seg]; sf0 = SEGS[s0 if seg == -1 else seg]['f0']
        pa, pb = ps[a - sf0], ps[b - sf0]
        n = count[seg]
        im = compose(seg, a, b, w, fi, n, base, pa + (pb - pa)*w, evs.get(SEGS[seg]['race'], []) if seg >= 0 else [], tops)
        dip = min(fi, n - 1 - fi)
        if (seg >= 0 and fi < DIP) or (seg < len(SEGS) - 1 and n - 1 - fi < DIP):
            aa = 1 - min(1.0, dip/DIP); im = Image.blend(im.convert('RGB'), Image.new('RGB', (W, H), (10, 11, 18)), aa*0.85).convert('RGBA')
        if stills: im.convert('RGB').save(OUTD + f'won_{k:04d}.png'); print('still', k, seg, a, w)
        else: proc.stdin.write(im.convert('RGB').tobytes())
        if k % 120 == 0: print(f'frame {k}/{len(P)}', flush=True)
    if proc:
        proc.stdin.close(); proc.wait(); print('SILENT', cut, len(P), 'frames', f'{len(P)/FPS:.1f} s')

def ranges():
    """the film frames to render, as won_render.sh takes them"""
    spans = sorted((s['f0'], s['f1']) for s in SEGS)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else: merged.append((a, b))
    return ','.join(f'{a}-{b}' for a, b in merged), sum(b - a + 1 for a, b in merged)

# ---------- the words and the music ----------
sys.path.insert(0, os.path.expanduser('~/.claude/skills/tg-films/scripts'))
DEST = f'{STUDIO}/Films/{SLUG}/won-{YEAR}/'

def story(race):
    """from the official splits: the runner the winner had to pass (the leader at the last checkpoint, from 20 % of the
    race on, where the winner trailed), the winner's biggest gap to them before the pass and where, the checkpoint where
    the winner led for good, the winning time and margin, and the top three"""
    key = RACES[race]['hero'][0]; me = RUN[key]; sex = me['sex']
    field = [r for r in DATA['runners'] if r['sex'] == sex]
    late = [c for c in CPS if c['id'] in me['splits'] and c['id'] != 'finish' and c['mile'] >= 0.2*OFF_TOTAL]
    def leader(c):
        return min((r for r in field if c['id'] in r['splits']), key=lambda r: r['splits'][c['id']])
    trail = [c for c in late if leader(c)['key'] != key]
    worst, w_cp, w_lead, lead_cp = 0, None, None, None
    if trail:
        last = trail[-1]; rival = leader(last)
        for c in late[:late.index(last) + 1]:
            if c['id'] in rival['splits'] and me['splits'][c['id']] - rival['splits'][c['id']] > worst:
                worst, w_cp, w_lead = me['splits'][c['id']] - rival['splits'][c['id']], c, rival
        lead_cp = next((c for c in late[late.index(last) + 1:]), None)
    else:
        lead_cp = late[0] if late else None
    top = sorted((r for r in field if r.get('finish_s')), key=lambda r: r['finish_s'])[:3]
    margin = top[1]['finish_s'] - me['finish_s'] if len(top) > 1 else None
    return dict(key=key, name=me['name'], worst=worst, w_cp=w_cp, w_lead=w_lead, lead_cp=lead_cp, finish=me['finish_s'], margin=margin, top=top)

def secs_words(s):
    s = int(round(s)); return f'{s} seconds' if s < 60 else ms(s)

def words(film_id, page):
    race_name = CFG['race_name']; year = YEAR
    parts, heads = [], []
    for r in CFG['order']:
        st = story(r); who = st['name']; label = {'men': 'Men', 'women': 'Women'}.get(r, r)
        line = f"{label}: {who}"
        if st['worst'] >= 60:
            line += f" was {ms(st['worst'])} behind {st['w_lead']['name']} at {UNIT_L} {du(st['w_cp']['mile']):.1f} ({re.sub(r'\s*\(.*?\)', '', st['w_cp']['name'])})"
            if st['lead_cp']: line += f", led by {UNIT_L} {du(st['lead_cp']['mile']):.1f}"
            line += f", and won in {hms(st['finish'])}"
        else:
            line += f" led from {UNIT_L} {du(st['lead_cp']['mile']):.1f} and won in {hms(st['finish'])}" if st['lead_cp'] else f" won in {hms(st['finish'])}"
        if st['margin']: line += f", {secs_words(st['margin'])} ahead."
        # a race the automatic line misreads (Mt. Fuji 2026: two men together to the second for 83 km, so "led from" was
        # true but said nothing) carries its own line in cfg.json, written from the same official splits
        if CFG['races'][r].get('line'): line = f"{label}: {CFG['races'][r]['line']}"
        parts.append(line)
        heads.append(f"{who.split()[-1]} by {secs_words(st['margin']) if st['margin'] < 60 else ms(st['margin'])}" if st['margin'] else who.split()[-1])
        parts_top = ' · '.join(f"{i + 1} {t['name']} {hms(t['finish_s'])}" for i, t in enumerate(st['top']))
        st['podium'] = f'{label}: {parts_top}'; RACES[r]['story'] = st
    title = f"{how(race_name)} was won: {', '.join(heads)} #Shorts"
    if len(title) > 100: title = f"{how(race_name)} was won #Shorts"
    m = MUSIC
    music = f'Music: "{m["title"]}" ({m["artist"]}).' + (f"\n{m['credit']}" if m.get('credit') else '')
    long_desc = open(f'{STUDIO}/Films/{SLUG}/description.txt').read().split('\n\n')
    credits = [b for b in long_desc if b.startswith(('Terrain:', 'Imagery:', 'Rendered', '©', 'Contains', 'Elevation'))]
    tag = re.sub(r'[^A-Za-z0-9]', '', CFG.get('tag') or race_name.split(' 20')[0])
    src = CFG.get('splits_source', 'official results')
    desc = '\n\n'.join(x for x in [
        f"{race_name}: how it was won, on the real course in 3D, from the official splits.",
        '\n'.join(parts) + (f"\n{CFG['note']}" if CFG.get('note') else ''),
        '\n'.join(RACES[r]['story']['podium'] for r in CFG['order']),
        f"Splits: {src}. Between aid stations each runner is placed at an even pace, so the exact passing points are estimates.",
        f"The whole course, every aid station, in the full film:\n▶ https://youtu.be/{film_id}",
        f"Plan this race free on TrailGoat:\n▶ {page}",
        music, *credits, f"#Shorts #TrailRunning #Ultramarathon #{tag}"] if x)
    tags = list(dict.fromkeys(['trail running', 'ultramarathon', race_name.split(' 20')[0], race_name, 'race results', 'race replay',
                               *[RACES[r]['story']['name'] for r in CFG['order']], *[t['name'] for r in CFG['order'] for t in RACES[r]['story']['top'][1:2]],
                               '3D course map', 'TrailGoat', 'Shorts']))
    tags = [t.replace(',', '') for t in tags]
    meta = dict(title=title, description=desc, tags=tags, privacy='public', playlist='Race Shorts', related_video=film_id)
    os.makedirs(DEST + 'captions', exist_ok=True)
    open(DEST + 'description.txt', 'w').write(desc + '\n')
    json.dump(meta, open(DEST + 'meta.json', 'w'), indent=1, ensure_ascii=False)
    # off YouTube: one question people can answer in a word; the race's own account tagged on Instagram
    ask = CFG.get('ask', f"Who are you picking for {year + 1}?")
    sound = f'Music: "{m["title"]}" ({m["artist"]})' + (f"\n{m['credit']}" if m.get('credit') else '')
    hashtags = f'#trailrunning #ultramarathon #ultrarunning #{tag} #trailgoat'
    utm = 'utm_source=facebook&utm_medium=social&utm_campaign=won'
    open_line = f"{how(race_name)} was won, from the official splits."
    ig_tag = f" @{CFG['instagram']}" if CFG.get('instagram') else ''
    # congratulate every winner (Kris, 2026-11-03: "make it standard for every How it was won"); Instagram tags them
    # with handles confirmed by hand into cfg.json "handles" (runner key -> handle), never guessed: no handle, just the name
    hh = CFG.get('handles', {})
    def congrats(ig):
        names = [f"@{hh[RACES[r]['story']['key']]}" if ig and hh.get(RACES[r]['story']['key']) else RACES[r]['story']['name'] for r in CFG['order']]
        return f"Congratulations to {' and '.join([', '.join(names[:-1]), names[-1]] if len(names) > 1 else names)}!"
    caps = dict(
        facebook=[open_line, '\n'.join(parts) + (f"\n{CFG['note']}" if CFG.get('note') else ''), congrats(False), ask, f"Plan this race free: {page}?{utm}", f"The whole course in 3D: https://trailgoat.run/films?{utm}", sound, hashtags],
        instagram=[open_line + ig_tag, '\n'.join(parts) + (f"\n{CFG['note']}" if CFG.get('note') else ''), congrats(True), ask, f"Plan this race free: {page.replace('https://', '')} (link in bio)", 'The whole course in 3D: full film on our YouTube channel, TrailGoat', sound, hashtags],
        tiktok=[open_line, '\n'.join(parts) + (f"\n{CFG['note']}" if CFG.get('note') else ''), congrats(False), ask, f"Plan this race free: {page.replace('https://', '')}", 'The whole course in 3D: full film on our YouTube channel, TrailGoat', sound, hashtags + ' #runtok'])
    for k, v in caps.items(): open(DEST + f'captions/{k}.txt', 'w').write('\n\n'.join(x for x in v if x) + '\n')
    print('TITLE', title, len(title)); print(desc)

def track():
    import music_rights
    m = CFG.get('music') or music_rights.cleared_music(FILM.get('music') or {}, SLUG)
    if not m: sys.exit('no cleared music for this film: set cfg.music')
    return m
MUSIC = None

def how(race_name):
    """"How the Mt. Fuji 100 2026", but "How The Bear 100 2026" when the race's own name starts with The"""
    return f"How {race_name}" if race_name.lower().startswith('the ') else f"How the {race_name}"

def loudness(path):
    """momentary loudness every 0.1 s (ffmpeg ebur128)"""
    r = subprocess.run([hud.ffmpeg(), '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r'M:\s*(-?[\d.]+)', r)]

def mix(cut):
    """the music under the silent Short at -14 LUFS (two passes): from cfg.music.start, else the window of the track
    that is loud throughout and loudest in its last third (the race is decided at the end)"""
    m = MUSIC; silent = OUTD + f'won-silent-{cut}.mp4'
    probe = subprocess.run([hud.ffmpeg(), '-i', silent], capture_output=True, text=True).stderr
    h_, m_, s_ = probe.split('Duration: ')[1].split(',')[0].split(':'); dur = int(h_)*3600 + int(m_)*60 + float(s_)
    start = (CFG.get('music') or {}).get('start')
    if start is None:
        L = loudness(m['file']); n = int(dur*10)
        def score(i):
            w = L[i:i + n]; tail = w[int(n*0.66):]
            return (sum(tail)/len(tail)) + 0.5*(sum(w)/len(w)) - (15 if min(w[:10]) < -45 else 0)
        best = max(range(0, max(1, len(L) - n), 5), key=score); start = best/10
    pre = f"atrim=start={start:.3f}:end={start + dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={dur - 1.5:.2f}:d=1.5"
    r = subprocess.run([hud.ffmpeg(), '-hide_banner', '-nostats', '-i', m['file'], '-af', pre + ',loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    af = (f"[1:a]{pre},loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000[a]")
    os.makedirs(DEST, exist_ok=True)
    dst = DEST + f"{SLUG}-{YEAR}-how-it-was-won{'' if cut == 'youtube' else '-social'}.mp4"
    def mux(af):
        subprocess.run([hud.ffmpeg(), '-y', '-loglevel', 'error', '-i', silent, '-i', m['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', dst], check=True)
        r = subprocess.run([hud.ffmpeg(), '-hide_banner', '-nostats', '-i', dst, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        return r[r.rindex('I:'):].split('\n')[0].strip()
    got = mux(af)
    # A quiet, peaky piece (the Bear's Brahms lullaby, 2026-11-04) came out at -26 LUFS from linear loudnorm, and at -20
    # from its dynamic mode. A plain gain to -14 with a -1.5 dBFS limiter on the peaks reaches it.
    if float(re.search(r'-?[\d.]+', got)[0]) < -16.5:
        gain = -14 - float(j['input_i'])
        print('loudnorm left it at', got, f'- {gain:+.1f} dB with a limiter instead')
        got = mux(f"[1:a]{pre},volume={gain:.2f}dB,alimiter=limit=0.841:attack=5:release=50:level=0,aresample=48000[a]")
    print('MUXED', dst, f'{dur:.1f} s', 'music from', f'{start:.1f} s', got)

def auto_cut(max_span=12.0, after=4.0, early=0.2):
    """the cut chosen from the splits alone, for the unattended Monday run. Per sex: the winner; the decisive miles
    around the last checkpoint (from 20 % of the race on) where they trailed, to just past where they led for good, or
    the last ten miles of a wire-to-wire win; the rivals are whoever was ahead of the winner in those miles (most
    recent first), then the runner-up and third, leaving out anyone who dropped before the clip ends (their dot would
    stop on the trail). The race with the bigger comeback opens the Short and goes first."""
    races = {}
    for sex, label in (('M', 'men'), ('F', 'women')):
        field = [r for r in DATA['runners'] if r['sex'] == sex]
        fin = sorted((r for r in field if r.get('finish_s')), key=lambda r: r['finish_s'])
        if len(fin) < 2: continue
        win = fin[0]; me = win['splits']
        def trailing(c):
            if c['id'] not in me or c['id'] == 'finish' or c['mile'] < early*OFF_TOTAL: return []
            return [r for r in field if c['id'] in r['splits'] and r['splits'][c['id']] < me[c['id']]]
        behind = [c for c in CPS if trailing(c)]
        if behind:
            last = behind[-1]
            lead_cp = next((c for c in CPS[CPS.index(last) + 1:] if c['id'] in me), None)
            b = min(OFF_TOTAL - 0.5, (lead_cp['mile'] if lead_cp else last['mile']) + after)
            a = max(0.0, last['mile'] - 3.0)
            if b - a > max_span: a = b - max_span
            if b - a < 8: a = max(0.0, b - 8)
        else:
            a, b = OFF_TOTAL - 10.5, OFF_TOTAL - 0.5
        def last_mile(r):
            return OFF_TOTAL if r.get('finish_s') else max((CP_BY[k]['mile'] for k in r['splits'] if k in CP_BY), default=0)
        ahead = []
        for c in reversed([c for c in CPS if a - 3 <= c['mile'] <= b]):
            for r in sorted(trailing(c), key=lambda r: r['splits'][c['id']]): ahead.append(r['key'])
        pool = list(dict.fromkeys(ahead + [r['key'] for r in fin[1:3]]))
        rivals = [k for k in pool if k != win['key'] and last_mile(RUN[k]) >= b][:2]
        worst = max((me[c['id']] - min(r['splits'][c['id']] for r in field if c['id'] in r['splits'])
                     for c in CPS if c['id'] in me and c['id'] != 'finish'), default=0)
        races[label] = dict(hero=win['key'], rivals=rivals, from_mi=round(a, 1), to_mi=round(b, 1), comeback_s=worst)
    order = sorted(races, key=lambda r: -races[r]['comeback_s'])
    return dict(order=order, open=order[0], races={r: {k: v for k, v in c.items() if k != 'comeback_s'} for r, c in races.items()})

if __name__ == '__main__':
    cmd = sys.argv[2]
    if cmd == 'auto':
        print(json.dumps(auto_cut(), indent=1)); sys.exit(0)
    if cmd in ('mix', 'words'): MUSIC = track()
    if cmd == 'mix': mix(sys.argv[3] if len(sys.argv) > 3 else 'youtube')
    if cmd == 'words':
        for r in CFG['order']: RACES[r]['story'] = story(r)
        words(CFG['film_id'], CFG['page'])
    if cmd == 'plan':
        for c in CPS: print(f"  {c['name']:<34} mi {c['mile']:6.1f}  route mi {c['d']/MI:6.1f}  ({c['how']})")
        print('segments', [(s['race'], s['f0'], s['f1'], round(off_mi(film_d(s['f0'])), 1), round(off_mi(film_d(s['f1'])), 1)) for s in SEGS])
        STAKES = stakes(CFG['open']); print('stakes', STAKES)
        P, op = plan(); print(len(P), 'frames', f'{len(P)/FPS:.1f} s', 'open', op)
        print('render', *ranges())
        for r in CFG['order']: print(r, [(a, t) for a, b, t, c in events(r)])
    elif cmd == 'stills': run(sys.argv[4] if len(sys.argv) > 4 else 'youtube', [int(x) for x in sys.argv[3].split(',')])
    elif cmd == 'video': run(sys.argv[3] if len(sys.argv) > 3 else 'youtube')

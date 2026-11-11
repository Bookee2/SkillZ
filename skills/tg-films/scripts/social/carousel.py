#!/usr/bin/env python3
"""TrailGoat carousel posts for Instagram and Facebook: 1080x1350 slides in the Shorts' look (Tokyo Night, Red Hat,
the race name in the wordmark gradient), made from data we already have, with their captions.

Kris, 2026-11-02, on the formats report (https://claude.ai/artifact/EpcfE1xhpxqAEtUKq8mHyV): "Yes, I love these ideas
let's build an automated calendar to post this". calendar.py decides what goes out each day and calls these.

    python3 carousel.py results <slug> [year]     # the Monday results, from Films/<slug>/won-<year>/
    python3 carousel.py where <slug> [year]       # where a 20/24/30-hour runner was when the winner finished
    python3 carousel.py guess [slug]              # guess the race from its profile (next unused film if no slug)
    python3 carousel.py ranking [topic]           # a ranking of our filmed races (next topic in rotation if none)
    python3 carousel.py raceweek <slug> <monday>  # the race-week card (course facts, aid-station gaps) from that week's spec
    python3 carousel.py forecast <slug> <monday>  # race-day weather at the start, high point and finish, at mid-pack times
    python3 carousel.py requests                  # "comment your race"
    python3 carousel.py entry <slug> <kind>       # a lottery or registration moment (moments.py; confirmed dates only)

Each writes Films/_social/posts/<id>/ with slide_N.jpg, captions/{instagram,facebook}.txt and post.json, and prints the
folder. Run it with the weekly-shorts venv (PIL, hud and short.py from the flyover scripts).
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import math
import os
import re
import sys
import urllib.request

TG = '/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts/scripts/flythrough'
sys.path.insert(0, TG)
import hud            # noqa: E402
import short as S     # noqa: E402
from PIL import Image, ImageDraw, ImageFilter   # noqa: E402

STUDIO = '/Volumes/KB SS/TrailGoat-Studio'
FILMS = f'{STUDIO}/Films'
SOCIAL = f'{FILMS}/_social'
POSTS = f'{SOCIAL}/posts'
STATE = f'{SOCIAL}/calendar-state.json'
W, H = 1080, 1350
X = 72                                   # side margin
MI, FT = 1609.344, 3.28084
UTM = 'utm_source=facebook&utm_medium=social&utm_campaign=carousel'
TAGS = '#trailrunning #ultramarathon #ultrarunning #trailgoat'
INK, MUTED, DIM = hud.INK, hud.MUTED, (115, 122, 162)
CLIMB, AID, OK, GOLD, ELE, GAIN, BLUE = hud.UP, hud.DOWN, hud.FIN, hud.DOT, hud.C_ELE, hud.C_GAIN, (122, 162, 247)
BG = (26, 27, 38)


# ---------- data ----------
def load(p):
    with open(p) as f:
        return json.load(f)


def state():
    try: return load(STATE)
    except OSError: return {}


def save_state(s):
    tmp = STATE + '.tmp'; json.dump(s, open(tmp, 'w'), indent=1); os.replace(tmp, STATE)


def films():
    """every published film: slug, name, miles, feet, ft/mi, thumb, course record, page, YouTube id"""
    out = []
    for d in sorted(glob.glob(f'{FILMS}/*/description.txt')):
        slug = d.split('/')[-2]
        first = open(d).read().split('\n')[0]
        m = re.search(r'^(.*?) from the start line to the finish: ([\d,.]+) (miles|km) and ([\d,]+) (ft|m) of climbing', first)
        if not m: continue
        name, dist, du, gain, gu = m.groups()
        mi = float(dist.replace(',', '')) if du == 'miles' else float(dist.replace(',', ''))/1.609344
        ft = float(gain.replace(',', '')) if gu == 'ft' else float(gain.replace(',', ''))*FT
        try: film = load(f'{FILMS}/{slug}/film.json')
        except OSError: continue
        course = next(iter(glob.glob(f"{film['out_dir']}/course-*.json")), None)
        desc = open(d).read()
        page = (re.search(r'https://trailgoat\.run/course/[^\s)]+', desc) or [None])[0]
        try: vid = load(f'{FILMS}/{slug}/uploaded.json').get('id')
        except OSError: vid = None
        master = film.get('master') if film.get('master') and os.path.exists(film.get('master')) else None
        out.append(dict(slug=slug, name=name, mi=mi, ft=ft, fpm=ft/mi, course=course, page=page, vid=vid,
                        master=master, thumb=frame_of(slug, master) if master else None, metric='km' in du))
    return out


def frame_of(slug, master, at=0.42):
    """a clean frame of the film (no thumbnail lettering, no HUD: the master is undressed), cached as the slides'
    background: 42 % of the way through, mid-race, the route line and its labels in view"""
    out = f'{SOCIAL}/bg/{slug}.jpg'
    if os.path.exists(out): return out
    os.makedirs(f'{SOCIAL}/bg', exist_ok=True)
    import subprocess
    ff = hud.ffmpeg()
    probe = subprocess.run([ff, '-i', master], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', probe)
    secs = int(m[1])*3600 + int(m[2])*60 + float(m[3]) if m else 60
    subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', f'{secs*at:.2f}', '-i', master, '-frames:v', '1', '-q:v', '2', out], check=True)
    return out


def course(path):
    c = load(path)
    for k in ('elevation_profile', 'aid_stations'):
        if isinstance(c.get(k), str): c[k] = json.loads(c[k])
    return c


def won_ns(slug, year):
    """won.py's model of the race (its splits, checkpoints and stories), loaded without running it"""
    argv = sys.argv; sys.argv = ['won.py', slug, 'x']; os.environ['WON_YEAR'] = str(year)
    ns = {'__name__': 'won'}
    src = open(f'{FILMS}/_won/won.py').read().split("if __name__ == '__main__':")[0]
    try: exec(compile(src, 'won.py', 'exec'), ns)
    finally: sys.argv = argv
    return ns


# ---------- drawing ----------
F2 = S.fonts(2.0)
def disp(px): return F2['disp'](px)
def mono(px):
    return S.fonts(px/20.0)['stat']                          # the readout's mono at px


def brand(lay, xy, px=34):
    """TrailGoat.run as the Shorts carry it (short.brand draws on a 1080x1920 layer)"""
    f = disp(px); probe = ImageDraw.Draw(Image.new('L', (1, 1))); x, y = xy
    w1 = probe.textlength('Trail', font=f); w2 = probe.textlength('Goat', font=f)
    lay.alpha_composite(S.shadowed((W, H), lambda d: (d.text((x, y), 'Trail', font=f, fill=INK), d.text((x + w1 + w2, y), '.run', font=f, fill=MUTED)), 4))
    lay.alpha_composite(S.grad_text('Goat', f, (x + w1, y), size=(W, H)))


class Slide:
    def __init__(self, bg: str | None = None, darken: float = 0.62):
        if bg:
            im = Image.open(bg).convert('RGB'); w, h = im.size
            cw = min(w, h*W/H); ch = cw*H/W
            im = im.crop(((w - cw)/2, (h - ch)/2, (w + cw)/2, (h + ch)/2)).resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3.5))   # the film's map labels go soft
            self.im = im.convert('RGBA')
            shade = Image.new('L', (1, H))
            for y in range(H): shade.putpixel((0, y), round(255*min(0.92, darken + 0.3*(1 - y/H)**2)))
            ov = Image.new('RGBA', (W, H), BG + (0,)); ov.putalpha(shade.resize((W, H))); self.im.alpha_composite(ov)
        else:
            self.im = Image.new('RGBA', (W, H), BG + (255,))
            glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
            g.ellipse((W*0.35, -H*0.35, W*1.45, H*0.55), fill=(52, 59, 96, 150))
            self.im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(140)))
        self.d = ImageDraw.Draw(self.im, 'RGBA'); self.y = 92        # RGBA: translucent rules and fills blend
        brand(self.im, (X, self.y)); self.y += 70

    def gap(self, px): self.y += px

    def kicker(self, text, col=BLUE):
        hud.Card.text(None, self.d, (X, self.y), text.upper(), mono(26), col, 0.14); self.y += 52

    def title(self, text, px=84, grad=False, col=INK, floor=56):
        f, lines = S.fit(text, px, floor, W - 2*X, {'disp': disp})
        for ln in lines:
            if grad: self.im.alpha_composite(S.grad_text(ln, f, (X, self.y), size=(W, H)))
            else: self.d.text((X, self.y), ln, font=f, fill=col)
            self.y += round(f.size*1.12)
        self.y += 10

    def para(self, text, px=38, col=INK, font=None, width=None):
        f = font or disp(px)
        for ln in S.wrap(text, f, width or W - 2*X):
            self.d.text((X, self.y), ln, font=f, fill=col); self.y += round(f.size*1.32)
        self.y += 8

    def label(self, text, col=DIM):
        hud.Card.text(None, self.d, (X, self.y), text.upper(), mono(22), col, 0.14); self.y += 42

    def rows(self, rows, px=34, gap=18, rule=True):
        """rows of (left, right, colour, right colour), mono, ruled"""
        f = mono(px)
        for left, right, col, rcol in rows:
            if rule: self.d.line((X, self.y - gap/2, W - X, self.y - gap/2), fill=(255, 255, 255, 24), width=2)
            hud.Card.text(None, self.d, (X, self.y), left, f, col, 0.04)
            if right:
                rw = self.d.textlength(right, font=f) + 0.04*f.size*len(right)
                hud.Card.text(None, self.d, (W - X - rw, self.y), right, f, rcol, 0.04)
            self.y += round(f.size*1.35) + gap

    def bars(self, items, unit='', ref=None):
        """horizontal bars: (label, value, shown value)"""
        top = max(v for _, v, _ in items); lw = 380
        px = 30
        while px > 25 and max(self.d.textlength(l, font=mono(px)) + 0.03*px*len(l) for l, _, _ in items) > lw - 16: px -= 1
        def fit_(l):
            while len(l) > 6 and self.d.textlength(l, font=mono(px)) + 0.03*px*len(l) > lw - 16: l = l[:-2].rstrip() + '…'
            return l
        items = [(fit_(l), v, sh) for l, v, sh in items]
        f = mono(px)
        for lab, v, shown in items:
            col = DIM if ref and lab == ref else CLIMB
            hud.Card.text(None, self.d, (X, self.y + 4), lab, f, INK if col != DIM else MUTED, 0.03)
            bw = (W - 2*X - lw - 150)*v/top
            self.d.rounded_rectangle((X + lw, self.y + 6, X + lw + bw, self.y + 38), 6, fill=col)
            hud.Card.text(None, self.d, (X + lw + bw + 16, self.y + 4), shown, f, INK, 0.03)
            self.y += 64

    def profile(self, cum, ele, h=330, col=BLUE, marks=()):
        x0, x1, y0, y1 = X, W - X, self.y, self.y + h
        lo, hi = min(ele), max(ele); n = len(cum)
        pts = [(x0 + (x1 - x0)*cum[i]/cum[-1], y1 - (ele[i] - lo)/max(1, hi - lo)*(h - 20)) for i in range(0, n, max(1, n//400))] + \
              [(x1, y1 - (ele[-1] - lo)/max(1, hi - lo)*(h - 20))]
        fill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fill)
        fd.polygon([(x0, y1)] + pts + [(x1, y1)], fill=col + (52,)); self.im.alpha_composite(fill)
        self.d.line(pts, fill=col, width=5, joint='curve')
        for mx, mcol in marks:
            xx = x0 + (x1 - x0)*mx
            self.d.ellipse((xx - 11, y1 - 11, xx + 11, y1 + 11), fill=mcol)
        self.y = y1 + 30

    def foot(self, text, i=None, n=None):
        y = H - 104
        hud.Card.text(None, self.d, (X, y), text.upper(), mono(24), MUTED, 0.12)
        if n and n > 1:
            for k in range(n):
                cx = W - X - (n - 1 - k)*34; r = 10 if k == i else 7
                self.d.ellipse((cx - r, y + 13 - r, cx + r, y + 13 + r), fill=GOLD if k == i else (255, 255, 255, 70))

    def save(self, path):
        self.im.convert('RGB').save(path, quality=90, optimize=True, progressive=True)


def write_post(pid, kind, title, slides, ig, fb, extra=None):
    d = f'{POSTS}/{pid}'; os.makedirs(f'{d}/captions', exist_ok=True)
    for f_ in glob.glob(f'{d}/slide_*.jpg'): os.remove(f_)
    paths = []
    for i, s in enumerate(slides, 1):
        p = f'{d}/slide_{i}.jpg'; s.save(p); paths.append(p)
    open(f'{d}/captions/instagram.txt', 'w').write(ig.strip() + '\n')
    open(f'{d}/captions/facebook.txt', 'w').write(fb.strip() + '\n')
    # YouTube channel posts take the same images; links click there too (Kris, 2026-11-02: "And add YouTube posts")
    open(f'{d}/captions/youtube.txt', 'w').write(fb.strip().replace('utm_source=facebook', 'utm_source=youtube') + '\n')
    json.dump(dict(id=pid, kind=kind, title=title, slides=paths, made=dt.datetime.now().astimezone().isoformat(timespec='seconds'), **(extra or {})),
              open(f'{d}/post.json', 'w'), indent=1)
    size = sum(os.path.getsize(p) for p in paths)
    print('POST', d, len(paths), 'slides', f'{size/1e6:.1f} MB')
    if size >= 9.5e6: sys.exit('slides over 9.5 MB together: the browser upload takes 10 MB per call')
    return d


def caps(lines_ig, lines_fb):
    return '\n\n'.join(x for x in lines_ig if x), '\n\n'.join(x for x in lines_fb if x)


def ms(s):
    s = int(round(abs(s))); return f"{s//60}:{s%60:02d}" if s < 3600 else f"{s//3600}:{s%3600//60:02d}:{s%60:02d}"


def hms(s):
    s = int(s); return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}"


def tag(name): return '#' + re.sub(r'[^A-Za-z0-9]', '', name)


# ---------- results ----------
def results(slug, year=2026):
    ns = won_ns(slug, year); CFG, RACES = ns['CFG'], ns['RACES']
    fl = next(f for f in films() if f['slug'] == slug)
    stories = {r: ns['story'](r) for r in CFG['order']}
    race = CFG['race_name']; n = 2 + len(CFG['order'])
    slides = []
    s = Slide(fl['thumb']); s.gap(120); s.kicker('Results · how it was won', GOLD); s.title(race, 92, grad=True); s.gap(24)
    for r in CFG['order']:
        st = stories[r]; lab = {'men': 'MEN', 'women': 'WOMEN'}.get(r, r.upper())
        s.rows([(f"{lab} · {st['name'].split()[-1].upper()}", hms(st['finish']), INK, GOLD)], px=36)
        if st['margin']: s.para(f"won by {ms(st['margin'])}", 34, MUTED)
    if CFG.get('note'): s.gap(10); s.para(CFG['note'], 36, OK)
    s.foot('Swipe for how', 0, n); slides.append(s)
    for k, r in enumerate(CFG['order'], 1):
        st = stories[r]; s = Slide(); s.kicker(race, BLUE); s.title({'men': "Men's race", 'women': "Women's race"}.get(r, r), 76)
        s.label('official result')
        rows = []
        for i, t in enumerate(st['top']):
            right = hms(t['finish_s']) if i == 0 else f"+{ms(t['finish_s'] - st['finish'])}"
            rows.append((f"{i + 1}  {t['name'].upper()}", right, GOLD if i == 0 else INK, GOLD if i == 0 else MUTED))
        s.rows(rows, px=32)
        s.gap(10); s.label('the move')
        if st['worst'] >= 60:
            text = (f"{st['name'].split()[-1]} was {ms(st['worst'])} behind {st['w_lead']['name']} at mile {st['w_cp']['mile']:.0f} "
                    f"({re.sub(r'\s*\(.*?\)', '', st['w_cp']['name'])})" + (f", and led by mile {st['lead_cp']['mile']:.0f}." if st['lead_cp'] else '.'))
        else:
            text = f"{st['name'].split()[-1]} led from mile {st['lead_cp']['mile']:.0f} to the finish." if st['lead_cp'] else f"{st['name'].split()[-1]} won it."
        s.para(text, 40)
        # the gap to the runner they passed, checkpoint by checkpoint from 20 % on: the line crosses zero at the pass
        me = ns['RUN'][st['key']]; riv = st['w_lead'] or (st['top'][1] if len(st['top']) > 1 else None)
        pts = []
        if riv:
            for c in ns['CPS']:
                if c['id'] in me['splits'] and c['id'] in riv['splits'] and c['mile'] >= 0.2*ns['OFF_TOTAL'] and c['id'] != 'finish':
                    pts.append((c['mile'], (me['splits'][c['id']] - riv['splits'][c['id']])/60))
            pts.append((ns['OFF_TOTAL'], (me['finish_s'] - riv['finish_s'])/60) if riv.get('finish_s') else pts[-1])
        if len(pts) > 2:
            rn = ns['surname'](riv['key']); hn = ns['surname'](st['key'])          # cfg labels: 'A. MACDONALD'
            s.gap(6); s.label(f"{hn} against {rn}, checkpoint by checkpoint"); s.gap(44)
            x0, x1, y0, hh = X, W - X, s.y, 250
            vmax, vmin = max(1.0, max(v for _, v in pts)), min(0.0, min(v for _, v in pts)); m0, m1 = pts[0][0], ns['OFF_TOTAL']
            def yv(v): return y0 + (hh - 56)*(v - vmin)/(vmax - vmin)        # room under the deepest point for its label
            xy = [(x0 + (x1 - x0)*(m - m0)/(m1 - m0), yv(v)) for m, v in pts]
            s.d.line((x0, yv(0), x1, yv(0)), fill=(255, 255, 255, 70), width=2)
            s.d.line(xy, fill=CLIMB, width=6, joint='curve')
            for (mx, v), (px_, py_) in zip(pts, xy):
                s.d.ellipse((px_ - 7, py_ - 7, px_ + 7, py_ + 7), fill=GOLD if v <= 0 else CLIMB)
            hud.Card.text(None, s.d, (x0, yv(0) - 38), f"LEVEL WITH {rn}", mono(22), OK, 0.1)
            hud.Card.text(None, s.d, (x0, y0 + hh + 18), f"MILE {m0:.0f}", mono(22), DIM, 0.1)
            fw = s.d.textlength('FINISH', font=mono(22)) + 12
            hud.Card.text(None, s.d, (x1 - fw, y0 + hh + 18), 'FINISH', mono(22), DIM, 0.1)
            (wm, wv), (wx, wy) = max(zip(pts, xy), key=lambda q: q[0][1])
            if wv > 0:
                lab = f"{ms(wv*60)} BEHIND · MI {wm:.0f}"; lw = s.d.textlength(lab, font=mono(24)) + 0.1*24*len(lab)
                hud.Card.text(None, s.d, (min(max(wx - lw/2, X), W - X - lw), wy + 20), lab, mono(24), CLIMB, 0.1)
        s.foot('official splits', k, n); slides.append(s)
    s = Slide(fl['thumb'], 0.7); s.gap(200); s.kicker('The whole race in 3D', BLUE); s.title(race, 80, grad=True)
    s.para('Every mile and every aid station in our full 3D flyover on YouTube, and the decisive miles replayed from the official splits in "How it was won".', 40)
    s.gap(20); s.para(f"Plan your {race.split(' 20')[0]} free: pacing, fuel and every cutoff.", 40, GOLD)
    s.foot('Link in bio', n - 1, n); slides.append(s)
    lines = [f"{s_['name']}: {'won by ' + ms(s_['margin']) if s_['margin'] else 'won'} in {hms(s_['finish'])}" for s_ in stories.values()]
    ask = 'Who are you picking for next year?'
    ig, fb = caps([f"{race} results." + (f" @{CFG['instagram']}" if CFG.get('instagram') else ''), '\n'.join(lines) + (f"\n{CFG['note']}" if CFG.get('note') else ''), ask,
                   f"Plan this race free: {CFG['page'].replace('https://', '')} (link in bio)", f"{TAGS} {tag(CFG.get('tag', race))}"],
                  [f"{race} results.", '\n'.join(lines) + (f"\n{CFG['note']}" if CFG.get('note') else ''), ask,
                   f"Plan this race free: {CFG['page']}?{UTM}", f"The whole course in 3D: https://trailgoat.run/films?{UTM}", f"{TAGS} {tag(CFG.get('tag', race))}"])
    return write_post(f'results-{slug}-{year}', 'results', f'{race} results', slides, ig, fb)


# ---------- the story carousel (learned from @hardcoreharrys' backyard record post, 2026-11-02) ----------
# Kris: "This post got a ton of engagement and it's a carousel. Can we learn anything from it" (24.8K likes, 248
# comments, 816 reposts). What it does: one beat of the story per slide, each a small cliffhanger; two or three
# lines of huge bold capitals low on a full-bleed picture, the number that matters in the accent colour; the brand
# on a thin rule above the words; SWIPE on the first. We can't use race photos, so each slide shows the place the beat
# happened, from the film's own camera.
CYAN = (42, 195, 222)

def film_frame(ns, d, slug):
    """the master's frame where the film's runner reaches route distance d, cropped 4:5 around them"""
    import subprocess
    legs = ns['LEGS']; f = next((f for f in legs if ns['film_d'](f) >= d), legs[-1])
    film = load(f'{FILMS}/{slug}/film.json'); out = f'{SOCIAL}/bg/{slug}-f{f}.jpg'
    if not os.path.exists(out):
        os.makedirs(f'{SOCIAL}/bg', exist_ok=True)
        subprocess.run([hud.ffmpeg(), '-y', '-loglevel', 'error', '-ss', f'{(f - 1)/24:.3f}', '-i', film['master'], '-frames:v', '1', '-q:v', '2', out], check=True)
    im = Image.open(out).convert('RGB'); w, h = im.size
    c = ns['cam']['cam'][f - 1]
    import geo
    b = geo.screen_box(ns['scene'](c['cam']), ns['scene'](c['tgt']), c['lens'], h/w, ns['scene'](ns['at'](d)), (0, 0, 0, 0), sensor_mm=36.0)
    cx = (b[0] if b else 0.5)*w; cw = h*W/H
    x0 = min(max(cx - cw/2, 0), w - cw)
    crop = im.crop((round(x0), 0, round(x0 + cw), h)).resize((W, H), Image.LANCZOS)
    p2 = f'{SOCIAL}/bg/{slug}-f{f}-45.jpg'; crop.save(p2, quality=92); return p2


class Beat:
    """one story slide: the place, and two or three lines of big capitals at the bottom"""
    def __init__(self, bg, lines, sub=None, first=False, i=0, n=1):
        self.im = Image.open(bg).convert('RGBA') if bg else Slide().im
        shade = Image.new('L', (1, H))
        for y in range(H):                          # clear at the top, near-black under the words
            t = min(1.0, max(0.0, (y/H - 0.28)/0.32)); shade.putpixel((0, y), round(255*(0.12 + 0.8*t*t*(3 - 2*t))))
        ov = Image.new('RGBA', (W, H), (8, 9, 16, 0)); ov.putalpha(shade.resize((W, H))); self.im.alpha_composite(ov)
        d = ImageDraw.Draw(self.im, 'RGBA')
        def width(segs, f): return sum(d.textlength(t, font=f) for t, _ in segs)
        def fitted(segs, px):                       # each line as large as it can be, up to px, inside the margins
            while px > 44 and width(segs, disp(px)) > W - 2*X: px -= 2
            return disp(px)
        blocks = [(l, fitted(l, 92)) for l in lines] + ([(None, None)] if sub else []) + [(l, fitted(l, 62)) for l in (sub or [])]
        hgt = sum(round(f.size*1.08) if f else 34 for _, f in blocks)
        y = H - 120 - hgt
        # the brand on a thin rule, centred above the words
        bf = disp(36); bw = d.textlength('TrailGoat.run', font=bf)
        d.line((X, y - 50, (W - bw)/2 - 24, y - 50), fill=(255, 255, 255, 110), width=2)
        d.line(((W + bw)/2 + 24, y - 50, W - X, y - 50), fill=(255, 255, 255, 110), width=2)
        brand(self.im, ((W - bw)/2, y - 72), 36)
        for segs, f in blocks:
            if not segs: y += 34; continue
            if isinstance(segs, str): segs = [(segs, INK)]
            x = (W - width(segs, f))/2
            for t, col in segs:
                d.text((x, y), t, font=f, fill=col if col != 'w' else (245, 247, 255)); x += d.textlength(t, font=f)
            y += round(f.size*1.08)
        if first:
            sf = disp(40); d.text((W - X - d.textlength('SWIPE  ›', font=sf), 78), 'SWIPE  ›', font=sf, fill=CYAN)
        for k in range(n):
            cx = W/2 + (k - (n - 1)/2)*22
            d.ellipse((cx - 5, H - 58, cx + 5, H - 48), fill=(245, 247, 255, 230) if k == i else (255, 255, 255, 80))

    def save(self, path): self.im.convert('RGB').save(path, quality=90, optimize=True, progressive=True)


def story(slug, year=2026, race_key=None):
    ns = won_ns(slug, year); CFG = ns['CFG']; race = CFG['race_name']; short = race.split(' 20')[0]
    rk = race_key or CFG['open']; st = ns['story'](rk)
    me, riv = ns['RUN'][st['key']], st['w_lead']
    hero = ns['surname'](st['key']); rname = riv['name'].upper() if riv else ''
    W_ = lambda t: (t, 'w'); C_ = lambda t: (t, CYAN)
    cps = [c for c in ns['CPS'] if c['id'] in me['splits'] and riv and c['id'] in riv['splits'] and c['id'] != 'finish']
    def gap(c): return me['splits'][c['id']] - riv['splits'][c['id']]
    def place(c): return re.sub(r'\s*\(.*?\)', '', c['name']).upper()
    beats = []
    w = st['w_cp']; L = st['lead_cp']
    beats.append(dict(d=w['d'], lines=[[W_(f'{hero} WAS')], [C_(f'{ms(st["worst"])} DOWN')], [W_(f'AT MILE {w["mile"]:.0f}.')]],
                      sub=[[W_(f'AND STILL WON {short.upper()}.')]]))
    beats.append(dict(d=max(0, w['d'] - 2500), lines=[[W_(f'{rname} LED')], [W_(f'AT {place(w)}.')]],
                      sub=[[W_(f'{ns["OFF_TOTAL"] - w["mile"]:.0f} MILES TO GO.')]]))
    mid = [c for c in cps if w['mile'] < c['mile'] < (L['mile'] if L else 999) and gap(c) > 0]
    pick = sorted(mid, key=lambda c: gap(c))[:2]                 # the two closest before the pass
    for c in sorted(pick, key=lambda c: c['mile']):
        beats.append(dict(d=c['d'], lines=[[W_(f'{place(c)},')], [W_(f'MILE {c["mile"]:.0f}:')], [C_(f'{ms(gap(c))} BACK.')]]))
    if L:
        lg = -gap(L) if L['id'] in riv['splits'] else None
        beats.append(dict(d=L['d'], lines=[[W_(f'BY {place(L)},')], [W_(f'MILE {L["mile"]:.0f},')], [C_(f'{hero} LED.')]],
                          sub=[[W_(f'{ms(lg)} AHEAD.')]] if lg else None))
    cr = 'course record' in (CFG.get('note') or '').lower()
    beats.append(dict(d=ns['TOTAL'] - 200, lines=[[C_(hms(st['finish']) + '.')], [W_('A COURSE RECORD.' if cr else f'WON BY {ms(st["margin"])}.')]],
                      sub=[[W_(f'{ms(st["margin"])} AHEAD OF {rname}.')]] if cr and st['margin'] else None))
    other = [r for r in CFG['order'] if r != rk]
    if other:
        o = ns['story'](other[0]); on = ns['surname'](o['key'])
        beats.append(dict(d=(o['lead_cp'] or o['w_cp'] or {'d': ns['TOTAL']*0.5})['d'], lines=[[W_(f"{on} WON THE")], [W_({'men': "MEN'S", 'women': "WOMEN'S"}.get(other[0], '') + ' RACE')], [C_(hms(o['finish']) + '.')]],
                          sub=[[W_('ALSO A COURSE RECORD.' if cr else f'BY {ms(o["margin"])}.')]]))
    beats.append(dict(d=ns['TOTAL']*0.35, lines=[[W_('EVERY MILE')], [C_('IN 3D.')]], sub=[[W_('FULL FILM ON YOUTUBE.')], [W_('PLAN IT FREE: LINK IN BIO.')]]))
    n = len(beats); slides = []
    for i, b in enumerate(beats):
        bg = film_frame(ns, b['d'], slug) if b['d'] is not None else next(f['thumb'] for f in films() if f['slug'] == slug)
        slides.append(Beat(bg, b['lines'], b.get('sub'), first=(i == 0), i=i, n=n))
    lead = f"{st['name']} was {ms(st['worst'])} behind {riv['name']} at {re.sub(r'\s*\(.*?\)', '', w['name'])}, mile {w['mile']:.0f}, and still won {race}."
    body = (f"{riv['name']} led with {ns['OFF_TOTAL'] - w['mile']:.0f} miles to go. " +
            ' '.join(f"{re.sub(r'\s*\(.*?\)', '', c['name'])}, mile {c['mile']:.0f}: {ms(gap(c))} back." for c in sorted(pick, key=lambda c: c['mile'])) +
            (f" By {re.sub(r'\s*\(.*?\)', '', L['name'])}, mile {L['mile']:.0f}, {st['name'].split()[-1]} led." if L else '') + f" {hms(st['finish'])}" + (', a course record.' if cr else '.'))
    hh = CFG.get('handles', {})                      # confirmed Instagram handles of runners (cfg.json), never guessed
    if hh.get(st['key']): lead = lead.replace(st['name'], f"{st['name']} (@{hh[st['key']]})", 1)
    if other and hh.get(o['key']):
        body += f" {o['name']} (@{hh[o['key']]}) won the women's race in {hms(o['finish'])}" + (', also a course record.' if cr else '.') if other[0] == 'women' else ''
    tags = ' '.join(f"@{h}" for h in [CFG.get('instagram')] if h)
    ask = 'Who are you picking for next year?'      # a keyword prompt ("comment PLAN") needs something to answer it; nothing does yet
    ig, fb = caps([lead + (f' {tags}' if tags else ''), body, ask, 'Every mile in 3D: full film on our YouTube channel, TrailGoat. Plan it free: link in bio.', f"{TAGS} {tag(CFG.get('tag', race))}"],
                  [lead, body, ask, f"Plan it free: {CFG['page']}?{UTM}", f"Every mile in 3D: https://youtu.be/{CFG['film_id']}", f"{TAGS} {tag(CFG.get('tag', race))}"])
    # Instagram only: the winner invited as collaborator (the post lands on their profile and in their followers' feeds
    # if they accept, as the @hardcoreharrys post did with its athletes) and tagged on the slides they're in. Business
    # Suite can tag but not invite, so a post with collaborators goes up through instagram.com (the poster task knows).
    extra = {}
    if hh.get(st['key']):
        fin = len(beats) - (2 if other else 1)        # the finish slide (1-based); one tag per person is plenty
        tagmap = {'1': [hh[st['key']]], str(fin): [hh[st['key']]]}
        if other and hh.get(o['key']): tagmap[str(len(beats) - 1)] = [hh[o['key']]]
        extra = dict(instagram=dict(collaborators=[hh[st['key']]], tags=tagmap))
    fb = re.sub(r' \(@[A-Za-z0-9_.]+\)', '', fb)        # Instagram handles mean nothing on Facebook or YouTube
    return write_post(f'story-{slug}-{year}-{rk}', 'story', f'{race}: how it was won', slides, ig, fb, extra)


# ---------- where would you be ----------
def nice_hours(h):
    return round(h) if h >= 6 else round(h*2)/2


def where(slug, year=2026):
    ns = won_ns(slug, year); CFG = ns['CFG']; race = CFG['race_name']
    fl = next(f for f in films() if f['slug'] == slug)
    st = min((ns['story'](r) for r in CFG['order']), key=lambda s_: s_['finish'])     # the fastest winner on the day
    me = ns['RUN'][st['key']]; F = st['finish']
    pts = sorted([(0.0, 0.0)] + [(ns['CP_BY'][k]['mile'], t) for k, t in me['splits'].items() if k in ns['CP_BY']], key=lambda p: p[1])
    def mile_at(T):
        for (m0, t0), (m1, t1) in zip(pts, pts[1:]):
            if T <= t1: return m0 + (m1 - m0)*(T - t0)/max(1, t1 - t0)
        return pts[-1][0]
    cutoff = (CFG.get('cutoff_h') or (30 if ns['OFF_TOTAL'] > 90 else None))
    goals = sorted({nice_hours(F/3600*k) for k in (1.45, 1.75, 2.15)})
    if cutoff: goals = [g for g in goals if g <= cutoff]
    cps = [c for c in ns['CPS'] if c['id'] != 'finish']
    rows = []
    for g in goals:
        m = mile_at(F*F/(g*3600))
        near = min(cps, key=lambda c: abs(c['mile'] - m)); nm = re.sub(r'\s*\(.*?\)', '', near['name'])
        where_ = f"near {nm}" if abs(near['mile'] - m) <= 1.5 else (f"past {nm}" if m > near['mile'] else f"before {nm}")
        rows.append((g, m, where_))
    who = st['name'].split()[-1]
    slides = []
    s = Slide(fl['thumb']); s.gap(150); s.kicker(race, BLUE)
    s.title(f"When {who} won in {hms(F)}…", 84); s.para('…where would you have been?', 52, GOLD); s.foot('Swipe', 0, 3); slides.append(s)
    s = Slide(); s.kicker(race, BLUE); s.title(f"{who} crosses the line", 70); s.label('a runner on pace for')
    cols = [OK, GOLD, CLIMB]
    s.rows([(f"{g:g} HOURS", f"MILE {m:.0f}", cols[i % 3], INK) for i, (g, m, w) in enumerate(rows)], px=40, gap=8, rule=True)
    for (g, m, w) in rows: pass
    s.gap(6)
    for i, (g, m, w) in enumerate(rows):
        s.para(f"{g:g} h: {w}", 34, MUTED)
    # the course as a line with everyone on it
    s.gap(16); x0, x1, yy = X, W - X, s.y + 30; tot = ns['OFF_TOTAL']
    s.d.line((x0, yy, x1, yy), fill=(255, 255, 255, 70), width=6)
    for c in cps:
        cx = x0 + (x1 - x0)*c['mile']/tot; s.d.line((cx, yy - 10, cx, yy + 10), fill=(255, 255, 255, 60), width=2)
    for i, (g, m, w) in enumerate(rows):
        cx = x0 + (x1 - x0)*m/tot; s.d.ellipse((cx - 14, yy - 14, cx + 14, yy + 14), fill=cols[i % 3])
    s.d.ellipse((x1 - 16, yy - 16, x1 + 16, yy + 16), fill=GOLD)
    hud.Card.text(None, s.d, (x0, yy + 30), 'START', mono(22), DIM, 0.1)
    fw = s.d.textlength(who.upper(), font=mono(22)) + 30
    hud.Card.text(None, s.d, (x1 - fw, yy + 30), who.upper(), mono(22), GOLD, 0.1)
    s.foot("from the winner's official splits", 1, 3); slides.append(s)
    s = Slide(fl['thumb'], 0.72); s.gap(220); s.title('Where would you be?', 80); s.para('Comment your finish time.', 48, GOLD)
    s.gap(20); s.para(f"Plan your own {race.split(' 20')[0]}: arrival times at every aid station, free.", 38)
    s.foot('Link in bio', 2, 3); slides.append(s)
    body = '\n'.join(f"{g:g}-hour runner: mile {m:.0f}, {w}" for g, m, w in rows)
    lead = f"When {st['name']} won {race} in {hms(F)}, where would you have been?"
    note = "From the winner's official splits, scaled to each finish time."
    ig, fb = caps([lead, body, note, 'Comment your finish time.', f"Plan your race free: link in bio", f"{TAGS} {tag(CFG.get('tag', race))}"],
                  [lead, body, note, 'Comment your finish time.', f"Plan your race free: {CFG['page']}?{UTM}", f"{TAGS} {tag(CFG.get('tag', race))}"])
    return write_post(f'where-{slug}-{year}', 'where', f'Where would you be: {race}', slides, ig, fb)


# ---------- guess the race ----------
def shape(c):
    lat, lon = c['start_lat'], c['start_lon']
    try:
        pts = json.loads(c['route_preview']) if isinstance(c.get('route_preview'), str) else c.get('route_preview')
        end = pts[-1]; elat, elon = (end[0], end[1]) if abs(end[0]) <= 90 else (end[1], end[0])
        dist = math.hypot((elat - lat)*111, (elon - lon)*111*math.cos(math.radians(lat)))
        return 'starts and finishes in the same place' if dist < 2 else 'point to point'
    except Exception:
        return None


def guess(slug=None):
    st_ = state(); used = st_.get('guess_used', [])
    fs = [f for f in films() if f['course'] and f['thumb']]
    if not slug:
        # famous first: the longest and biggest-climbing races early, rotating through everything
        order = sorted(fs, key=lambda f: -(f['mi'] + f['ft']/400))
        f = next((x for x in order if x['slug'] not in used), order[0])
    else:
        f = next(x for x in fs if x['slug'] == slug)
    c = course(f['course']); p = c['elevation_profile']
    metric = f['metric']
    dist = f"{f['mi']*1.609344:.0f} KM" if metric else f"{f['mi']:.0f} MILES"
    climb = f"{f['ft']/FT:,.0f} M" if metric else f"{f['ft']:,.0f} FT"
    high = f"{c['high_m']:,.0f} M" if metric else f"{c['high_m']*FT:,.0f} FT"
    month = dt.date.fromisoformat(c['start_datetime'][:10]).strftime('%B') if c.get('start_datetime') else None
    shp = shape(c)
    slides = []
    s = Slide(); s.kicker('Guess the race', GOLD); s.title('Which race is this?', 84)
    s.profile([x for x in p['cumM']], [x for x in p['eleM']])
    s.label('clues')
    rows = [('DISTANCE', dist, MUTED, OK), ('CLIMBING', climb, MUTED, CLIMB), ('HIGH POINT', high, MUTED, ELE)]
    if month: rows.append(('RACED IN', month.upper(), MUTED, AID))
    s.rows(rows, px=34, gap=12)
    s.foot('Guess, then swipe', 0, 3); slides.append(s)
    s = Slide(); s.kicker('Guess the race · hint', GOLD); s.title('Still guessing?', 76)
    s.profile(p['cumM'], p['eleM'], h=260, col=MUTED)
    s.label('where'); s.para(', '.join(x for x in (c.get('region'), c.get('country')) if x) or 'somewhere steep', 56, AID)
    if shp: s.gap(6); s.label('the course'); s.para(shp.capitalize() + '.', 44)
    s.foot('Answer next', 1, 3); slides.append(s)
    s = Slide(f['thumb'], 0.6); s.gap(160); s.kicker('It was', GOLD); s.title(f['name'], 92, grad=True)
    s.para(f"{dist.title().replace('Km', 'km')} and {climb.lower()} of climbing.", 42)
    s.gap(24); s.para('Every mile in 3D: our full flyover is on YouTube.', 38, MUTED)
    s.para('Plan it free: pacing, fuel, every aid station.', 38, GOLD)
    s.foot('Did you get it?', 2, 3); slides.append(s)
    ask = 'Guess the race from its elevation profile. Comment your answer before you swipe to the last slide.'
    ig, fb = caps([ask, f"Clues: {dist.lower()}, {climb.lower()} of climbing, high point {high.lower()}.", 'Answer on slide 3. Plan any race free: link in bio.', f"{TAGS} #guesstherace"],
                  [ask, f"Clues: {dist.lower()}, {climb.lower()} of climbing, high point {high.lower()}.", f"Answer on photo 3. Plan it free: {f['page']}?{UTM}", f"{TAGS} #guesstherace"])
    d = write_post(f"guess-{f['slug']}", 'guess', f"Guess the race: {f['name']}", slides, ig, fb, dict(answer=f['name']))
    st_ = state(); st_.setdefault('guess_used', []); st_['guess_used'] = list(dict.fromkeys(st_['guess_used'] + [f['slug']])); save_state(st_)
    return d


# ---------- rankings ----------
def biggest_climb(f):
    c = course(f['course']); p = c['elevation_profile']; cum, ele = p['cumM'], p['eleM']
    cl = S.climbs(cum, ele, 0, len(cum) - 1)
    if not cl: return 0, 0
    lo, hi = max(cl, key=lambda x: ele[x[1]] - ele[x[0]]); return ele[hi] - ele[lo], (cum[hi] - cum[lo])/MI


TOPICS = ['steep100', 'highpoint', 'bigclimb', 'steepshort', 'mostclimb']


def ranking(topic=None):
    st_ = state()
    if not topic:
        i = st_.get('ranking_next', 0); topic = TOPICS[i % len(TOPICS)]; st_['ranking_next'] = i + 1; save_state(st_)
    fs = [f for f in films() if f['course']]
    if topic == 'steep100':
        sel = sorted([f for f in fs if f['mi'] >= 95], key=lambda f: -f['fpm'])[:7]
        title, unit = "The steepest 100-milers we've flown", 'feet of climbing per mile'
        items = [(short_name(f['name']), f['fpm'], f"{f['fpm']:.0f}") for f in sel]
    elif topic == 'steepshort':
        sel = sorted([f for f in fs if f['mi'] < 40], key=lambda f: -f['fpm'])[:7]
        title, unit = "The steepest short races we've flown", 'feet of climbing per mile, under 40 miles'
        items = [(short_name(f['name']), f['fpm'], f"{f['fpm']:.0f}") for f in sel]
    elif topic == 'highpoint':
        hp = [(f, course(f['course'])['high_m']*FT) for f in fs]
        sel = sorted(hp, key=lambda x: -x[1])[:7]
        title, unit = "The highest races we've flown", 'high point, feet above sea level'
        items = [(short_name(f['name']), v, f"{v:,.0f}") for f, v in sel]
    elif topic == 'bigclimb':
        bc = [(f, *biggest_climb(f)) for f in fs]
        sel = sorted(bc, key=lambda x: -x[1])[:7]
        title, unit = "The biggest single climbs we've flown", 'feet, bottom to top without a real descent'
        items = [(short_name(f['name']), v*FT, f"{v*FT:,.0f}") for f, v, L in sel]
    else:
        sel = sorted(fs, key=lambda f: -f['ft'])[:7]
        title, unit = "The most climbing we've flown", 'total feet of climbing'
        items = [(short_name(f['name']), f['ft'], f"{f['ft']:,.0f}") for f in sel]
    slides = []
    s = Slide(); s.kicker('TrailGoat rankings', GOLD); s.title(title, 76); s.label(unit); s.gap(8); s.bars(items)
    s.foot('Which one did we miss?', 0, 2); slides.append(s)
    bg = next(f for f in fs if short_name(f['name']) == items[0][0])['thumb']
    s = Slide(bg, 0.66); s.gap(220); s.title('Which one did we miss?', 80); s.para('Comment the race. The most-requested one gets its 3D flyover next.', 44, GOLD)
    s.gap(20); s.para('Every race on the list: free plans with pacing, fuel and every aid station.', 36, MUTED)
    s.foot('Link in bio', 1, 2); slides.append(s)
    body = '\n'.join(f"{i + 1}. {lab}: {shown}" for i, (lab, v, shown) in enumerate(items))
    ig, fb = caps([f"{title} ({unit}).", body, 'Which one did we miss? Comment it: the most-requested race gets its 3D flyover next.', 'Plan any of them free: link in bio.', TAGS],
                  [f"{title} ({unit}).", body, 'Which one did we miss? Comment it: the most-requested race gets its 3D flyover next.', f"Plan any of them free: https://trailgoat.run?{UTM}", TAGS])
    return write_post(f"ranking-{topic}-{dt.date.today().isoformat()}", 'ranking', title, slides, ig, fb, dict(topic=topic))


def short_name(n):
    """a race's name short enough for a bar label: no 'by UTMB', no trailing distance where the name stands without it"""
    fixed = {'UTMB Mont-Blanc 174K': 'UTMB', 'Grand Raid des Pyrénées Ultra': 'Grand Raid Pyrénées', 'Madeira Island Ultra-Trail 110K': 'Madeira',
             'Matterhorn Ultraks Sky 49K': 'Matterhorn Ultraks', 'Leadville Trail 100 Run': 'Leadville 100', 'Western States 100': 'Western States',
             'Eiger Ultra-Trail E101': 'Eiger E101', 'Transgrancanaria Classic': 'Transgrancanaria', 'Transvulcania Ultramarathon': 'Transvulcania',
             'Lavaredo Ultra Trail 120K': 'Lavaredo', 'Zugspitz Ultratrail 107K': 'Zugspitz', 'Shinetsu Five Mountains 110K': 'Shinetsu Five Mtns'}
    if n in fixed: return fixed[n]
    n = re.sub(r'\s*\bby UTMB\b', '', n)
    n = re.sub(r'\s+\d+(\.\d+)?\s?(K|KM|k)$', '', n)          # 'Tor des Géants 330K' -> 'Tor des Géants'
    return n.strip()


# ---------- race week ----------
def week_race(slug, monday):
    spec = load(f'{FILMS}/_race-week/{monday}/spec.json')
    return next(r for r in spec['races'] if r['slug'] == slug)


def stop_name(n):
    """an aid station's name as runners say it: 'Duthie Aid Station' -> 'Duthie', '50K, Marathon Lap Aid Station' -> 'Marathon Lap'"""
    n = hud.aid_name(n)
    n = re.sub(r'^(\d+\s?(K|M|MI|Mile|Miler)\b[,/ ]*)+', '', n, flags=re.I)
    n = re.sub(r'\s*(Aid Station|Aid Stn|Aid|AS)$', '', n, flags=re.I).strip(' ,-')
    return n or 'Aid'


def race_date(r, monday):
    """the race's date in its week: the spec's day ('SAT 7') read against the week's Monday"""
    m = dt.date.fromisoformat(monday); n = int(re.search(r'\d+', r.get('day') or '0')[0] or 0)
    return next((m + dt.timedelta(days=k) for k in range(7) if (m + dt.timedelta(days=k)).day == n), m + dt.timedelta(days=5)).isoformat()


def film_aids(slug):
    """the film's own aid pins (its shot spec: [pin mile, 'NAME · MI a / b / c']), one stop per race mile listed, so a lap
    course's repeat visits are all there. These were checked against the organiser when the film was made."""
    try: spec = load(load(f'{FILMS}/{slug}/film.json')['shots'])
    except (OSError, KeyError): return []
    out = []
    for pin, label in spec.get('aids', []):
        nm, _, miles = label.partition('·')
        out += [(stop_name(nm.strip().title()), float(m)) for m in (re.findall(r'\d+(?:\.\d+)?', miles) or [pin])]
    return sorted(out, key=lambda x: x[1])


def raceweek(slug, monday):
    r = week_race(slug, monday); fl = next(f for f in films() if f['slug'] == slug)
    c = course(fl['course']); p = c['elevation_profile']; cum, ele = p['cumM'], p['eleM']
    race = hud.Race(c); metric = fl['metric']
    def up(d0, d1):
        import bisect
        i0, i1 = bisect.bisect_left(cum, d0), bisect.bisect_right(cum, d1)
        return sum(max(0.0, ele[i + 1] - ele[i]) for i in range(i0, min(i1, len(ele) - 1)))
    k_ft = fl['ft']/max(1, up(0, c['distance_m'])*FT)                 # the profile's climbing scaled to the film's total
    aids = sorted([a for a in c.get('aid_stations') or [] if a.get('name') and 200 < float(a.get('distM') or 0) < c['distance_m'] - 200],
                  key=lambda a: float(a['distM']))
    pts = [('Start', 0.0)] + [(stop_name(a['name']), float(a['distM'])) for a in aids] + [('Finish', c['distance_m'])]
    legs = [(a, b, (db - da)/MI, up(da, db)*FT*k_ft) for (a, da), (b, db) in zip(pts, pts[1:])]
    if (c.get('laps') or 1) > 1 or max(l[2] for l in legs) > 12:
        # the course file's aid list is missing or covers one lap only (Wild Florida, Keweenaw, Kessel Run, Nov 2026): use
        # the film's pins, in race miles. A race mile sits at mile/total of the way along the route.
        fa = [(n, m) for n, m in film_aids(slug) if 0 < m < fl['mi']]
        if fa:
            sc = c['distance_m']/(fl['mi']*MI)
            mp = [('Start', 0.0)] + fa + [('Finish', fl['mi'])]
            legs = [(a, b, mb - ma, up(ma*MI*sc, mb*MI*sc)*FT*k_ft) for (a, ma), (b, mb) in zip(mp, mp[1:])]
    name = r['name']; day = r.get('when', '').split()[0] if r.get('when') else 'Saturday'
    longest = max(legs, key=lambda l: l[2])
    if longest[2] > 12:
        # Kessel Run (2026): a lap course whose file pins only the first lap's aid, so it read "36.6 miles to the finish".
        # A card that tells runners to carry for a stretch that doesn't exist is worse than no card.
        raise ValueError(f"aid data looks incomplete for {slug}: laps={c.get('laps')}, longest stretch {longest[2]:.1f} mi to {longest[1]}")
    slides = []
    s = Slide(fl['thumb']); s.gap(130); s.kicker('Race week', GOLD); s.title(f"Racing {name} on {day}?", 84); s.gap(16)      # keep descenders in the title clear of the first row's rule
    s.rows([(lab, f"{v} {u}".strip(), MUTED, {'mile': OK, 'gain': CLIMB, 'aid': AID}.get(t, INK)) for lab, v, u, t in r['stats']], px=36, gap=12)
    if r.get('where'): s.para(r['where'], 36, MUTED)
    n = 2 + math.ceil(len(legs)/7); s.foot('Swipe: aid station to aid station', 0, n); slides.append(s)
    for k in range(0, len(legs), 7):
        s = Slide(); s.kicker(name, BLUE); s.title('Aid station to aid station', 64); s.label('distance and climbing to the next stop')
        rows = []
        for a, b, mi, ft in legs[k:k + 7]:
            rows.append((f"TO {b.upper() if len(b) <= 18 else b.upper()[:19].rsplit(' ', 1)[0]}", f"{mi:.1f} MI · +{ft:,.0f} FT", INK, CLIMB if ft/max(mi, 0.1) > 250 else MUTED))
        s.rows(rows, px=30, gap=14)
        if k == 0: s.gap(6); s.para(f"Longest stretch: {longest[2]:.1f} miles to {longest[1]}. Carry for it.", 36, GOLD)
        s.foot('From our course file', 1 + k//7, n); slides.append(s)
    s = Slide(fl['thumb'], 0.7); s.gap(200); s.title('Your race, planned', 80)
    s.para('Arrival time at every aid station, carbs and fluid per hour, what to carry on each stretch, and a crew sheet.', 40)
    s.gap(16); s.para('Free at trailgoat.run', 44, GOLD); s.foot('Link in bio', n - 1, n); slides.append(s)
    lead = f"Racing {name} this {day}? Here's every stretch between aid stations: how far, how much climbing."
    ask = 'Racing it? Tell us your goal time.'
    ig, fb = caps([lead, ask, f"Your arrival times and fuel plan, free: {r['page'].replace('https://', '')} (link in bio)", f"{TAGS} {tag(name)}"],
                  [lead, ask, f"Your arrival times and fuel plan, free: {r['page']}?{UTM}", f"{TAGS} {tag(name)}"])
    return write_post(f"raceweek-{slug}-{monday}", 'raceweek', f"Race week: {name}", slides, ig, fb)


# ---------- forecast ----------
def forecast(slug, monday):
    r = week_race(slug, monday); fl = next(f for f in films() if f['slug'] == slug)
    c = course(fl['course']); race = hud.Race(c); p = c['elevation_profile']
    start = dt.datetime.fromisoformat((r.get('start') or c.get('start_datetime') or '')[:16]) if (r.get('start') or c.get('start_datetime')) else None
    rd = r.get('date') or race_date(r, monday)
    if not start or start.date().isoformat() != rd[:10]:
        # this year's date with the course's start time
        t = (c.get('start_datetime') or 'T06:00')[11:16] or '06:00'
        start = dt.datetime.fromisoformat(f"{rd[:10]}T{t}")
    hi_i = max(range(len(p['eleM'])), key=lambda i: p['eleM'][i])
    pts = [('Start', 0.0), ('High point', p['cumM'][hi_i]), ('Finish', c['distance_m'])]
    route = json.loads(c['route_preview']) if isinstance(c.get('route_preview'), str) else (c.get('route_preview') or [])
    def ll(dm):
        if not route: return c['start_lat'], c['start_lon']
        k = min(len(route) - 1, round(dm/c['distance_m']*(len(route) - 1))); a, b = route[k][0], route[k][1]
        return (a, b) if abs(a) <= 90 else (b, a)
    rows = []
    for nm, dm in pts:
        lat, lon = ll(dm); eta = start + dt.timedelta(seconds=race.time_at(dm))
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}&hourly=temperature_2m,apparent_temperature,"
               f"precipitation_probability,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto"
               f"&start_date={eta.date()}&end_date={eta.date()}")
        h = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'TrailGoat'}), timeout=30))['hourly']
        i = min(range(len(h['time'])), key=lambda j: abs(dt.datetime.fromisoformat(h['time'][j]) - eta))
        rows.append(dict(name=nm, mile=dm/MI, eta=eta, t=h['temperature_2m'][i], feel=h['apparent_temperature'][i],
                         rain=h['precipitation_probability'][i], wind=h['wind_speed_10m'][i], ele=p['eleM'][min(range(len(p['cumM'])), key=lambda j: abs(p['cumM'][j] - dm))]*FT))
    name = r['name']; fh = race.finish_s/3600
    slides = []
    s = Slide(fl['thumb']); s.gap(130); s.kicker('Race-day forecast', GOLD); s.title(name, 84, grad=True)
    lo, hi = min(x['feel'] for x in rows), max(x['t'] for x in rows)
    s.para(f"From {lo:.0f}°F (feels like) to {hi:.0f}°F on course, for a runner finishing in about {fh:.0f} hours.", 42)
    s.foot('Swipe', 0, 3); slides.append(s)
    s = Slide(); s.kicker(name, BLUE); s.title('Where it matters, when you get there', 62)
    for x in rows:
        s.label(f"{x['name']} · mile {x['mile']:.0f} · {x['ele']:,.0f} ft · {x['eta'].strftime('%a %-I:%M %p')}", AID)
        s.rows([(f"{x['t']:.0f}°F", f"FEELS {x['feel']:.0f}°F", INK, MUTED), (f"RAIN {x['rain']:.0f}%", f"WIND {x['wind']:.0f} MPH", AID if x['rain'] >= 40 else MUTED, MUTED)], px=34, gap=8, rule=False)
        s.gap(10)
    s.foot('Open-Meteo forecast', 1, 3); slides.append(s)
    s = Slide(fl['thumb'], 0.7); s.gap(220); s.title('Pack for the high point', 76)
    s.para('Your own arrival times change the weather you meet. Plan them free, with fuel and a crew sheet.', 40)
    s.foot('Link in bio', 2, 3); slides.append(s)
    body = '\n'.join(f"{x['name']} (mile {x['mile']:.0f}, about {x['eta'].strftime('%-I:%M %p')}): {x['t']:.0f}°F, feels {x['feel']:.0f}°F, rain {x['rain']:.0f}%, wind {x['wind']:.0f} mph" for x in rows)
    lead = f"Race-day forecast for {name}, at the start, the high point and the finish, at the time a ~{fh:.0f}-hour runner gets there."
    ig, fb = caps([lead, body, 'Racing? What are you packing?', f"Plan your own arrival times free: {r['page'].replace('https://', '')} (link in bio)", f"{TAGS} {tag(name)}"],
                  [lead, body, 'Racing? What are you packing?', f"Plan your own arrival times free: {r['page']}?{UTM}", f"{TAGS} {tag(name)}"])
    return write_post(f"forecast-{slug}-{monday}", 'forecast', f"Forecast: {name}", slides, ig, fb)


# ---------- entry moments (lottery, registration) ----------
WHAT = {'lottery_open': 'Lottery opens', 'lottery_close': 'Lottery closes', 'lottery_draw': 'Lottery draw',
        'registration_open': 'Registration opens', 'registration_close': 'Registration closes', 'sold_out': 'Sold out'}


def race_handle(slug):
    """the race's own Instagram account (race-handles.json: each linked from the race's official site), or None"""
    try: return load(f'{SOCIAL}/race-handles.json')['handles'].get(slug)
    except OSError: return None


def entry(slug, kind, day=None):
    """a lottery or registration moment from moments.json (confirmed ones only): the dates, the course, the plan.
    Kris, 2026-11-03: "we need to post with purpose and intent on what's actually happening"."""
    import moments as Mo
    r = Mo.load()['races'][slug]; fl = next(f for f in films() if f['slug'] == slug)
    x = next(m for m in r['moments'] if m['kind'] == kind)
    if x.get('status') != 'confirmed': raise ValueError(f'{slug} {kind} is a pattern date, not confirmed: confirm it first (moments.py set)')
    when, rd = Mo.d(x['date']), Mo.d(r['race_date'])
    ed = r.get('edition') or rd.year; name = fl['name']; title_name = f"{short_name(name)} {ed}"
    wd = when.strftime('%A')
    if r.get('entry') == 'invite':
        # Badwater: an application the organisers choose from, not a random draw; "lottery" would be wrong
        what = dict(WHAT, lottery_open='Applications open', lottery_close='Applications close', lottery_draw='Field announced')
        kick, lead = {'lottery_open': ('Applications open today', f"Applications for {title_name} open today."),
                      'lottery_close': (f'Applications close {wd}', f"Applications for {title_name} close {wd}, {when.strftime('%-d %B')}."),
                      'lottery_draw': ('Field announced today', f"The {title_name} field is announced today."),
                      'registration_open': ('Registration opens today', f"Registration for {title_name} opens today.")}[kind]
        ask = {'lottery_draw': 'Did you get in? Tell us below.'}.get(kind, 'Are you applying?')
    else:
        what = WHAT
        kick, lead = {'lottery_open': ('Lottery opens today', f"The {title_name} lottery opens today."),
                      'lottery_close': (f'Lottery closes {wd}', f"The {title_name} lottery closes {wd}, {when.strftime('%-d %B')}."),
                      'lottery_draw': ('Lottery draw today', f"The {title_name} lottery is drawn today."),
                      'registration_open': ('Registration opens today', f"Registration for {title_name} opens today.")}[kind]
        ask = {'lottery_draw': 'Did your name come up? Tell us below.', 'registration_open': "Signing up? Tell us your goal time."}.get(kind, 'Are you putting your name in?')
    dates = [m for m in Mo.cycle(slug) if m.get('status') == 'confirmed' and m['kind'] in WHAT]
    c = course(fl['course']); p = c['elevation_profile']; metric = fl['metric']
    dist = f"{fl['mi']*1.609344:.0f} KM" if metric else f"{fl['mi']:.0f} MILES"
    climb = f"{fl['ft']/FT:,.0f} M" if metric else f"{fl['ft']:,.0f} FT"
    high = f"{c['high_m']:,.0f} M" if metric else f"{c['high_m']*FT:,.0f} FT"
    slides = []
    s = Slide(fl['thumb']); s.gap(120); s.kicker(kick, GOLD); s.title(title_name, 88, grad=True)
    rows = [(what[m['kind']].upper(), Mo.d(m['date']).strftime('%a %-d %b').upper(), MUTED, GOLD if m['kind'] == kind else INK) for m in dates]
    rows.append(('RACE DAY', rd.strftime('%a %-d %b %Y').upper(), MUTED, OK))
    s.gap(36); s.rows(rows, px=40, gap=22)
    s.foot('Swipe: the course', 0, 3); slides.append(s)
    s = Slide(); s.kicker(name, BLUE); s.title("What you're entering", 72)
    s.profile(p['cumM'], p['eleM'])
    s.rows([('DISTANCE', dist, MUTED, OK), ('CLIMBING', climb, MUTED, CLIMB), ('HIGH POINT', high, MUTED, ELE)], px=34, gap=12)
    s.foot('From our course file', 1, 3); slides.append(s)
    s = Slide(fl['thumb'], 0.7); s.gap(200)
    s.title({'lottery_draw': 'Got in? Now plan it', 'registration_open': 'Signing up?'}.get(kind, 'Putting your name in?'), 80)
    s.gap(12); s.para('Plan it free: your arrival time at every aid station, fuel per hour, and a crew sheet.', 40)
    s.gap(16); s.para('Every mile in 3D: our full flyover is on YouTube.', 38, MUTED)
    s.foot('Link in bio', 2, 3); slides.append(s)
    body = '\n'.join(f"{what[m['kind']]}: {Mo.d(m['date']).strftime('%A %-d %B %Y')}" for m in dates) + f"\nRace day: {rd.strftime('%A %-d %B %Y')}"
    h = race_handle(slug)
    ig, fb = caps([lead + (f" @{h}" if h else ''), body, ask, "Details and entry on the race's own site.", f"Plan it free: {fl['page'].replace('https://', '')} (link in bio)" if fl['page'] else 'Plan it free: link in bio.', f"{TAGS} {tag(short_name(name))}"],
                  [lead, body, ask, f"Details and entry: {x['source']}", f"Plan it free: {fl['page']}?{UTM}" if fl['page'] else '', f"{TAGS} {tag(short_name(name))}"])
    return write_post(f"entry-{slug}-{kind}-{x['date']}", 'entry', f"{what[kind]}: {title_name}", slides, ig, fb, dict(moment=x))


# ---------- requests ----------
def requests():
    fs = [f for f in films() if f['thumb']][:12]
    s = Slide(); mosaic = Image.new('RGB', (W, H), BG)
    tw, th = W//3, H//4
    for i, f in enumerate(fs):
        im = Image.open(f['thumb']).convert('RGB'); w, h = im.size; cw = min(w, h*tw/th); ch = cw*th/tw
        mosaic.paste(im.crop(((w - cw)/2, (h - ch)/2, (w + cw)/2, (h + ch)/2)).resize((tw, th)), ((i % 3)*tw, (i//3)*th))
    tmp = f'{SOCIAL}/.mosaic.jpg'; mosaic.save(tmp, quality=90)
    s = Slide(tmp, 0.8); s.gap(240); s.kicker('Your race next', GOLD); s.title('Running a race in 2027?', 92)
    s.para('Comment it below. The most-requested race gets its 3D flyover next, and everyone who asked gets tagged when it comes out.', 44)
    s.foot('Comment your race'); os.remove(tmp)
    month = dt.date.today().strftime('%B')
    ig, fb = caps(['Running a race in 2027? Comment it below.', 'The most-requested race this month gets its full 3D flyover next, with every aid station, and everyone who asked gets tagged when it comes out.', TAGS],
                  ['Running a race in 2027? Comment it below.', 'The most-requested race this month gets its full 3D flyover next, with every aid station, and everyone who asked gets tagged when it comes out.', f"Our films so far: https://trailgoat.run/films?{UTM}", TAGS])
    return write_post(f"requests-{dt.date.today().strftime('%Y-%m')}", 'requests', f'Comment your race ({month})', [s], ig, fb)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'results': results(a[1], int(a[2]) if len(a) > 2 else 2026)
    elif cmd == 'where': where(a[1], int(a[2]) if len(a) > 2 else 2026)
    elif cmd == 'story': story(a[1], int(a[2]) if len(a) > 2 else 2026, a[3] if len(a) > 3 else None)
    elif cmd == 'guess': guess(a[1] if len(a) > 1 else None)
    elif cmd == 'ranking': ranking(a[1] if len(a) > 1 else None)
    elif cmd == 'raceweek': raceweek(a[1], a[2])
    elif cmd == 'forecast': forecast(a[1], a[2])
    elif cmd == 'requests': requests()
    elif cmd == 'entry': entry(a[1], a[2], a[3] if len(a) > 3 else None)
    else: sys.exit(__doc__)

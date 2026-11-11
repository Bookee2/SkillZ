#!/usr/bin/env python3
"""Lottery odds: a 9:16 Reel of who's in a race's lottery hat and what a first-timer's chances are, for lottery close
and draw days (Western States closes 21 Nov and draws 5 Dec; Hardrock draws 5 Dec).

Kris, 2026-11-11 ("I love this proceed", ideas report https://claude.ai/artifact/2Y2wvovM6UWPr8KnBq6r9g).

    oddsreel.py <slug> <edition> [--when close|draw]

Figures come only from the race's own published numbers: Films/_social/lottery-sources.json ('last' is the previous
draw, copied by hand with its URL; 'counts' is a live page read at build time, e.g. wser.org/lottery2027.html). A race
that doesn't publish them doesn't get one. What the Reel shows:
  rows   Western States: runners in the hat by ticket count (this edition's live counts when there are any), with last
         year's stated odds beside each tier. Hardrock: last draw's four pools and the odds at each pool's fewest tickets.
  big    a first-timer's odds last year, "about 1 in N".
  ends   on the film's 9:16 climb (the race Short's portrait render) when there is one.
Writes Films/<slug>/lottery-<edition>/<close|draw>/: <slug>-<edition>-lottery[-social].mp4, captions/, meta.json, data.json.
"""
import json, math, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or '.') != HERE]   # this folder's queue.py shadows the stdlib queue requests needs
import requests   # noqa: E402
sys.path.insert(0, HERE)
import reelkit as K   # noqa: E402
from reelkit import S, hud, W, H, FPS   # noqa: E402
from PIL import Image, ImageDraw, ImageFilter   # noqa: E402

SLUG, EDITION = sys.argv[1], int(sys.argv[2])
WHEN = sys.argv[sys.argv.index('--when') + 1] if '--when' in sys.argv else 'close'
SRC = json.load(open(f'{K.STUDIO}/Films/_social/lottery-sources.json'))[SLUG]
DEST = f'{K.STUDIO}/Films/{SLUG}/lottery-{EDITION}/{WHEN}/'; os.makedirs(DEST, exist_ok=True)
OUT = f'{K.STUDIO}/Renders/flyovers/shorts/{SLUG}/lottery-{EDITION}/{WHEN}/'; os.makedirs(OUT, exist_ok=True)
FILM = K.film(SLUG)
SECS = 24.0; N = round(SECS*FPS)
T_ROWS, ROW_DT = 1.4, 0.55            # bars grow one after another from T_ROWS
T_BIG, T_CTA = 14.6, SECS - 4.2       # the first-timer's odds, then the closing card
ROW_Y0, LBL_X, BAR_X, BAR_MAX = 540, 64, 390, 340      # BAR_X clears '1,024 TICKETS'
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
UA = {'User-Agent': 'TrailGoat (trailgoat.run)'}


def long_day(iso):
    return time.strftime('%A %-d %B', time.strptime(iso, '%Y-%m-%d'))      # "Saturday 21 November", for captions


def day(iso):
    y, m, d = map(int, iso.split('-')); wd = time.strftime('%a', time.strptime(iso, '%Y-%m-%d')).upper()
    return f'{wd} {d} {MONTHS[m - 1].upper()}'


def wser_counts(url):
    """Runners per ticket tier from the race's live entrants page: [(tickets, runners)], totals, 'updated' stamp."""
    s = requests.get(url, headers=UA, timeout=60).text
    i = s.find('Total Tickets'); tail = s[i:]
    tot_t = int(re.search(r'Total Tickets:\s*<B>([\d,]+)', tail)[1].replace(',', ''))
    tot_a = int(re.search(r'Total Entrants:\s*<B>([\d,]+)', tail)[1].replace(',', ''))
    upd = re.search(r'Last Updated:\s*([\d-]+)', tail)[1]
    rows = re.findall(r'<tr>\s*<TD[^>]*>(\d+)</TD>\s*<TD[^>]*>&nbsp;</TD>\s*<TD[^>]*>([\d,]+)</TD>', tail[:6000], re.I)
    rows = sorted((int(t), int(a.replace(',', ''))) for t, a in rows)
    assert rows and sum(a for _, a in rows) == tot_a, ('tier rows do not add up to the total', rows, tot_a)
    assert sum(t*a for t, a in rows) == tot_t, ('tickets do not add up', rows, tot_t)
    m, d, y = map(int, upd.split('-')); return rows, tot_a, tot_t, f'{d} {MONTHS[m - 1]} {y}'


def spec():
    """What the Reel says, from the official figures only."""
    L = SRC['last']; name = SRC['race']; c = SRC.get('counts')
    fx = (L['first_timers']/L['first_timers_expected']) if L.get('first_timers_expected') else 100/(L.get('first_timer_odds_pct') or L['odds_pct']['1'])
    one_in = int(float(f'{fx:.2g}'))                                     # "about 1 in 320", two figures
    big = dict(kick=f"A FIRST-TIMER'S ODDS IN {L['edition']}", value=f"{L.get('first_timer_odds_pct') or L['odds_pct']['1']:g}%",
               sub=f'about 1 in {one_in:,}')
    when = (f"{EDITION} LOTTERY · ENTRIES CLOSE {day(SRC['close'])}" if WHEN == 'close' else
            f"{EDITION} LOTTERY · THE DRAW IS {day(SRC['draw'])}")
    if c and c['provider'] == 'wser':
        url = c['url'].format(edition=EDITION)
        try: rows, ta, tt, upd = wser_counts(url); live = True
        except Exception as e:                                           # no live page: last year's final counts
            print('live counts unavailable:', e); live = False
        if live:
            r = [dict(label=f'{t:,} TICKET' + ('S' if t > 1 else ''), n=a, right=(f"{L['odds_pct'][str(t)]:.1f}%" if str(t) in L['odds_pct'] else 'NEW'))
                 for t, a in rows]
            facts = [f'{ta:,} RUNNERS · {tt:,} TICKETS' + (' SO FAR' if WHEN == 'close' else '')]   # the date goes in the caption
            top_t, top_n = rows[-1]
            if top_n == 1 and str(top_t) not in L['odds_pct']:
                facts.append(f'ONE RUNNER, {top_t:,} TICKETS: {int(math.log2(top_t)) + 1} YEARS TRYING')   # 2^(n-1) after n years
            src_line = f'Runners and tickets: {url.replace("https://", "")} ({"preliminary, updated " + upd if WHEN == "close" else upd}). Odds: {L["source"].replace("https://", "")}'
            return dict(name=name, when=when, rows_title=f'IN THE {EDITION} HAT, BY TICKETS', right_title=f"ODDS IN {L['edition']}",
                        rows=r, facts=facts, big=big, totals=(ta, tt), upd=upd, live=True, src=src_line,
                        last=dict(applicants=L['applicants'], spots=L['spots'], edition=L['edition']))
    if 'pools' in L:
        r = [dict(label=p['label'], n=p['applicants'], right=f"{p['odds_pct']:.1f}%") for p in L['pools']]
        rt = 'ODDS*'
        facts = [f"{L['applicants']:,} RUNNERS · {L['spots']} PLACES", L['places_split'], '*AT A POOL\'S FEWEST TICKETS']
        big['sub'] = f"{L['applicants']:,} runners for {L['spots']} places"   # no expected count published: no '1 in N' from a rounded %
    else:
        r = [dict(label=f'{t} TICKET' + ('S' if int(t) > 1 else ''), n=None, right=f'{v:g}%') for t, v in L['odds_pct'].items()]
        rt = 'ODDS'; facts = [f"{L['applicants']:,} RUNNERS · {L['spots']} SPOTS"]
    return dict(name=name, when=when, rows_title=f"THE {L['edition']} HAT", right_title=rt, rows=r, facts=facts, big=big,
                totals=(L['applicants'], L.get('tickets')), upd=None, live=False, src=f"Figures: {L['source'].replace('https://', '')}",
                last=dict(applicants=L['applicants'], spots=L['spots'], edition=L['edition']))


def ease(u): u = max(0.0, min(1.0, u)); return u*u*(3 - 2*u)


def backdrop():
    """A film frame, centre-cropped to 9:16, blurred and darkened, a little larger than the screen for a drift."""
    png = OUT + 'backdrop.png'
    if not os.path.exists(png):
        at = float(FILM.get('thumb_at') or 60)
        subprocess.run([K.ffmpeg(), '-y', '-loglevel', 'error', '-ss', f'{at:.2f}', '-i', FILM['master'], '-frames:v', '1', png], check=True)
    im = Image.open(png).convert('RGB'); w, h = im.size; cw = round(h*9/16)
    im = im.crop(((w - cw)//2, 0, (w - cw)//2 + cw, h)).resize((round(W*1.08), round(H*1.08)), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(9)).convert('RGBA')
    im.alpha_composite(Image.new('RGBA', im.size, hud.PANEL[:3] + (150,)))
    return im


def climb_reader():
    """Frames of the race Short's 9:16 climb render, from its middle (the biggest climb), or None."""
    p = f'{K.STUDIO}/Renders/flyovers/shorts/{SLUG}/{SLUG}-portrait.mp4'
    if not os.path.exists(p): return None
    r = subprocess.run([K.ffmpeg(), '-i', p], capture_output=True, text=True).stderr
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r); dur = int(m[1])*3600 + int(m[2])*60 + float(m[3])
    start = max(0.0, dur/2 - (SECS - T_BIG)/2)
    return subprocess.Popen([K.ffmpeg(), '-loglevel', 'error', '-ss', f'{start:.2f}', '-i', p, '-t', f'{SECS - T_BIG + 0.5:.2f}',
                             '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}',
                             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)


def chart(t, sp, F, dim):
    rows = sp['rows']; peak = max((r['n'] or 0) for r in rows) or 1
    stacked = any(F['probe'].textlength(r['label'], font=F['row'])*1.06 > BAR_X - LBL_X - 16 for r in rows)
    pitch = 128 if stacked else min(84, round(880/len(rows)))
    a0 = round(255*ease((t - 0.6)/0.5))

    def draw(d):
        _rows(d, t, sp, F, rows, pitch, peak, a0, stacked)
    lay = S.shadowed((W, H), draw, 6, 0.8)
    if dim < 1: lay.putalpha(lay.getchannel('A').point(lambda v: round(v*dim)))
    return lay


def _rows(d, t, sp, F, rows, pitch, peak, a0, stacked):
    hud.Card.text(None, d, (LBL_X, ROW_Y0 - 62), sp['rows_title'], F['label'], hud.MUTED + (a0,), 0.12)
    rt = sp['right_title']; rw = d.textlength(rt, font=F['label']) + 0.12*F['label'].size*len(rt)
    t_right = T_ROWS + len(rows)*ROW_DT + 0.3
    ar = round(255*ease((t - t_right)/0.4))
    hud.Card.text(None, d, (W - 64 - rw, ROW_Y0 - 62), rt, F['label'], hud.MUTED + (ar,), 0.12)
    for i, r in enumerate(rows):
        t0 = T_ROWS + i*ROW_DT; k = ease((t - t0)/0.6)
        if k <= 0: continue
        y = ROW_Y0 + i*pitch; al = round(255*min(1.0, k*2))
        hud.Card.text(None, d, (LBL_X, y + 6), r['label'], F['row'], hud.INK + (al,), 0.06)
        bx, by, bmax, bh = (LBL_X, y + 50, BAR_X - LBL_X + BAR_MAX, 46) if stacked else (BAR_X, y, BAR_MAX, pitch - 22)
        if r['n'] is not None:
            bl = max(8, bmax*r['n']/peak)*k
            d.rounded_rectangle((bx, by, bx + bl, by + bh), radius=6, fill=hud.C_AID + (235,))
            d.text((bx + bl + 14, by + 4), f"{round(r['n']*k):,}", font=F['num'], fill=hud.INK + (al,))
        ao = round(255*ease((t - t_right - i*0.18)/0.3))
        if ao > 0:
            col = hud.DOT if i == 0 else hud.INK
            tw = d.textlength(r['right'], font=F['num'])
            d.text((W - 64 - tw, (by if stacked else y) + 4), r['right'], font=F['num'], fill=col + (ao,))
    fy = ROW_Y0 + len(rows)*pitch + 30
    t_facts = t_right + len(rows)*0.18 + 0.4
    for j, line in enumerate(sp['facts']):
        af = round(255*ease((t - t_facts - j*0.6)/0.4))
        fnt = F['label'] if d.textlength(line, font=F['label'])*1.12 <= W - 2*LBL_X else F['small']
        col = hud.C_MILE if j == 0 else hud.MUTED if line.startswith('*') else hud.DOT
        if af > 0: hud.Card.text(None, d, (LBL_X, fy + j*48), line, fnt, col + (af,), 0.12)


def video(cut, sp):
    F0 = S.fonts(2.0); disp = F0['disp']
    F = dict(probe=ImageDraw.Draw(Image.new('L', (1, 1))), label=F0['cta'], small=F0['small'], row=F0['value'], num=F0['value'], big=disp(300), sub=disp(64), q=disp(80))
    bg = backdrop(); clip = climb_reader()
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); S.brand(top, (64, 150))
    f, lines = S.fit(sp['name'], 96, 64, W - 128, S.fonts(2.0)); y = 214
    for ln in lines: top.alpha_composite(S.grad_text(ln, f, (64, y))); y += round(f.size*1.08)
    top.alpha_composite(S.shadowed((W, H), lambda d: hud.Card.text(None, d, (64, y + 12), sp['when'], F['label'], hud.C_AID, 0.12), 6))
    cta, cta_box = S.cta_layer({}, 'Plan your race free', cta=cut)
    dst = OUT + f'lottery-silent-{cut}.mp4'; p = K.writer(dst); last_clip = None
    for fr in range(1, N + 1):
        t = fr/FPS; u = fr/N
        ox, oy = round((bg.width - W)*u*0.6), round((bg.height - H)*(0.2 + 0.5*u))
        im = bg.crop((ox, oy, ox + W, oy + H)).copy()
        if clip and t >= T_BIG:                                    # the race's biggest climb comes up under the odds
            raw = clip.stdout.read(W*H*3)
            if len(raw) == W*H*3: last_clip = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
            if last_clip is not None:
                c = last_clip.copy(); k = ease((t - T_BIG)/0.8)
                c.alpha_composite(Image.new('RGBA', (W, H), hud.PANEL[:3] + (round(120 - 40*k),)))
                im = Image.blend(im, c, k)
        S.frost(im, (0, 0, W, 520), S.band_mask(520))
        im.alpha_composite(top)
        dim = 1.0 if t < T_BIG else max(0.0, 1 - (t - T_BIG)/0.5)
        if dim > 0: im.alpha_composite(chart(t, sp, F, dim))
        if T_BIG <= t < T_CTA:
            al = round(255*ease((t - T_BIG - 0.3)/0.5)); b = sp['big']
            def bigt(d):
                hud.Card.text(None, d, (64, 720), b['kick'], F['label'], hud.MUTED + (al,), 0.12)
                d.text((52, 740), b['value'], font=F['big'], fill=hud.INK + (al,))
                d.text((64, 1080), b['sub'], font=F['sub'], fill=hud.DOT + (al,))
                aq = round(255*ease((t - T_BIG - 1.6)/0.5))
                d.text((64, 1440), 'How many tickets', font=F['q'], fill=hud.INK + (aq,))
                d.text((64, 1530), 'are you holding?', font=F['q'], fill=hud.INK + (aq,))
                hud.Card.text(None, d, (64, 1650), 'COMMENT YOUR TICKET COUNT', F['label'], hud.C_MILE + (aq,), 0.12)
            im.alpha_composite(S.shadowed((W, H), bigt, 8, 0.85))
        if t >= T_CTA:
            bx = cta_box; S.frost(im, bx, S.band_mask(bx[3] - bx[1], 24).resize((bx[2] - bx[0], bx[3] - bx[1])), glass=0.55)
            im.alpha_composite(cta)
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    if clip: clip.kill()
    print('SILENT', cut, N, 'frames', dst); return dst


def words(sp, m):
    page, vid, ig = K.links(SLUG); name = sp['name']; L = sp['last']; b = sp['big']
    short = name.replace(' 100', '')
    if WHEN == 'close':
        open_line = f"{short} {EDITION} lottery: entries close {long_day(SRC['close'])}."
    else:
        open_line = f"{short} {EDITION} lottery: the draw is {long_day(SRC['draw'])}."
    ta, tt = sp['totals']
    now = (f'So far {ta:,} runners hold {tt:,} tickets (updated {sp["upd"]}).' if sp['live'] and WHEN == 'close' else
           f'{ta:,} runners hold {tt:,} tickets.' if sp['live'] else '')
    last = (f"In {L['edition']}, {L['applicants']:,} runners went for {L['spots']} lottery spots; a first-timer's odds were {b['value']}, {b['sub']}.")
    ask = 'How many tickets are you holding? Comment below.'
    utm = 'utm_source={}&utm_medium=social&utm_campaign=lottery'
    caps = dict(
        instagram='\n\n'.join(x for x in [open_line + (f' @{ig}' if ig else ''), now, last, ask,
                                          f'Plan your race free: {page.replace("https://", "")} (link in bio)' if page else '',
                                          'The whole course in 3D: full film on our YouTube channel, TrailGoat', sp['src'], K.music_line(m), K.TAGS] if x),
        facebook='\n\n'.join(x for x in [open_line, now, last, ask, f'Plan your race free: {page}?{utm.format("facebook")}' if page else '',
                                         f'The whole course in 3D: https://trailgoat.run/films?{utm.format("facebook")}', sp['src'], K.music_line(m), K.TAGS] if x),
        tiktok='\n\n'.join(x for x in [open_line, now, last, ask, f'Plan your race free: {page.replace("https://", "")}' if page else '',
                                       K.music_line(m), K.TAGS + ' #runtok'] if x))
    title = f"{short} {EDITION} lottery: a first-timer's odds #Shorts"
    desc = '\n\n'.join(x for x in [open_line, now, last, ask, sp['src'], f'The whole course in 3D, every aid station:\n▶ https://youtu.be/{vid}' if vid else '',
                                   f'Plan this race free on TrailGoat:\n▶ {page}' if page else '', K.music_line(m)] if x)
    meta = dict(title=title, description=desc, tags=['trail running', 'ultramarathon', name, f'{short} lottery', f'{name} {EDITION}', 'lottery odds',
                                                     'TrailGoat', 'Shorts'], privacy='public', playlist='Race Shorts')
    if vid: meta['related_video'] = vid
    K.write_words(DEST, caps, meta); print(title); print(caps['instagram'][:600])


def stills(sp, ts):
    """--stills 3,9,13,17,22: those moments as PNGs in the render folder, to look at before encoding."""
    global N
    for t in ts:
        N = round(t*FPS); p = video('social', sp)
        subprocess.run([K.ffmpeg(), '-y', '-loglevel', 'error', '-sseof', '-0.05', '-i', p, '-frames:v', '1', OUT + f'still-{t:g}.png'], check=True)
        print('STILL', OUT + f'still-{t:g}.png')


if __name__ == '__main__':
    sp = spec(); json.dump(sp, open(DEST + 'data.json', 'w'), indent=1, ensure_ascii=False)
    if '--stills' in sys.argv:
        stills(sp, [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]); sys.exit()
    print(json.dumps({k: sp[k] for k in ('when', 'facts', 'big')}, ensure_ascii=False))
    if '--words' in sys.argv:                          # captions and meta only, from the Reel already built
        words(sp, K.track(SLUG)); sys.exit()
    m = None
    for cut in ('youtube', 'social'):
        silent = video(cut, sp)
        m = K.mix(SLUG, silent, DEST + f'{SLUG}-{EDITION}-lottery{"" if cut == "youtube" else "-social"}.mp4', SECS)
    words(sp, m)

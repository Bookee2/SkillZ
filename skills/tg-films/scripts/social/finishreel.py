#!/usr/bin/env python3
"""Where would you finish?: a 9:16 Reel of a race's finish times filling in, for a race we've filmed.

Kris, 2026-11-11 ("I love this proceed", ideas report https://claude.ai/artifact/2Y2wvovM6UWPr8KnBq6r9g). Two moments:
  --before  race week, from last year's field: "Racing JFK 50 Mile on Saturday? Where will you finish?"
  (default) the days after the race, from this year's: "Where would you finish?"
A clock sweeps from the first finisher to the last while the histogram fills in, then the first, the median and the last
are marked, then the question. Finish times only: no names anywhere.

    finishreel.py <slug> <year> [--before]     # Films/<slug>/finish-<year>/times.json -> the Reels and their words
                                               # (in finish-<year>/, or finish-<year>/before/ for the race-week cut)
times.json: {"race", "year", "source", "finish_s": [seconds, …]}, written from an official results feed (RunSignup's
API, UTMB live). UltraSignup refuses scripted requests from this Mac; it isn't a source for this.
"""
import json, math, os, subprocess, sys
import reelkit as K
from reelkit import S, hud, W, H, FPS
from PIL import Image, ImageDraw, ImageFilter

SLUG, YEAR = sys.argv[1], int(sys.argv[2]); BEFORE = '--before' in sys.argv
SRC = f'{K.STUDIO}/Films/{SLUG}/finish-{YEAR}/'
OUT = f'{K.STUDIO}/Renders/flyovers/shorts/{SLUG}/finish-{YEAR}/'; os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(SRC + 'times.json')); T = sorted(DATA['finish_s'])
DEST = SRC + ('before/' if BEFORE else ''); os.makedirs(DEST, exist_ok=True)   # last year's times serve next year's race week too
NAME = K.race_name(SLUG); FILM = K.film(SLUG)
SECS = 22.0; N = round(SECS*FPS)
T0, T1 = 2.4, 11.0                    # the clock's sweep
X0, X1, BASE, BAR_H = 64, W - 64, 1250, 430


def hms(s, secs=False):
    s = round(s); h, m = s//3600, s % 3600//60
    return f'{h}:{m:02d}:{s % 60:02d}' if secs else f'{h}:{m:02d}'


def ease(u): u = max(0.0, min(1.0, u)); return u*u*(3 - 2*u)


def backdrop():
    """A frame of the film, centre-cropped to 9:16, blurred and darkened, a little larger than the screen for a drift."""
    ff = K.ffmpeg(); png = OUT + 'backdrop.png'
    if not os.path.exists(png):
        src = FILM['master']; at = float(FILM.get('thumb_at') or 0) or None
        if at is None:
            r = subprocess.run([ff, '-i', src], capture_output=True, text=True).stderr
            import re; m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r); at = 0.42*(int(m[1])*3600 + int(m[2])*60 + float(m[3]))
        subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', f'{at:.2f}', '-i', src, '-frames:v', '1', png], check=True)
    im = Image.open(png).convert('RGB'); w, h = im.size; cw = round(h*9/16)
    im = im.crop(((w - cw)//2, 0, (w - cw)//2 + cw, h)).resize((round(W*1.08), round(H*1.08)), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(9)).convert('RGBA')
    im.alpha_composite(Image.new('RGBA', im.size, hud.PANEL[:3] + (150,)))
    return im


def bins():
    span = T[-1] - T[0]
    for mins in (5, 10, 15, 20, 30, 60):
        if span/(mins*60) <= 34: break
    w = mins*60; a = math.floor(T[0]/w)*w; n = math.ceil((T[-1] - a + 1)/w)
    counts = [0]*n
    for t in T: counts[min(n - 1, int((t - a)//w))] += 1
    return a, w, counts


def x_of(t, a, w, n): return X0 + (t - a)/(w*n)*(X1 - X0)


def chart(f, a, w, counts, F):
    t = f/FPS; c = T[0] + (T[-1] - T[0])*ease((t - T0)/(T1 - T0)) if t >= T0 else None
    n = len(counts); peak = max(counts); bw = (X1 - X0)/n
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line([(X0, BASE + 2), (X1, BASE + 2)], fill=hud.MUTED + (120,), width=2)
    # at most 8 labels, or "21h22h23h…" runs together on a 45 h hundred (Cape Town, 2026-11-11)
    step = next(s for s in (1800, 3600, 7200, 10800, 14400, 21600, 43200) if w*n/s <= 8)
    k = math.ceil(a/step)*step
    while k <= a + w*n:
        x = x_of(k, a, w, n); lab = f'{k//3600}h' if step % 3600 == 0 else hms(k)
        d.line([(x, BASE + 4), (x, BASE + 16)], fill=hud.MUTED + (160,), width=2)
        tw = d.textlength(lab, font=F['tick']); d.text((x - tw/2, BASE + 22), lab, font=F['tick'], fill=hud.MUTED + (200,))
        k += step
    done = 0
    for i, cnt in enumerate(counts):
        lo = a + i*w
        got = 0 if c is None else sum(1 for v in T if lo <= v < lo + w and v <= c)
        done += got
        if not got: continue
        hgt = BAR_H*got/peak; x = X0 + i*bw
        d.rounded_rectangle((x + 2, BASE - hgt, x + bw - 2, BASE), radius=min(6, bw/3), fill=hud.C_AID + (235,))
    if c is not None and t <= T1 + 0.4:
        x = x_of(c, a, w, n)
        d.line([(x, BASE - BAR_H - 40), (x, BASE)], fill=hud.INK + (220,), width=3)
        lab = hms(c); tw = d.textlength(lab, font=F['clock'])
        d.text((min(X1 - tw, max(X0, x - tw/2)), BASE - BAR_H - 100), lab, font=F['clock'], fill=hud.INK)
    lay2 = S.shadowed((W, H), lambda dd: hud.Card.text(None, dd, (X0, 640), f'FINISHED  {done:,}', F['label'], hud.C_MILE, 0.12), 6)
    lay.alpha_composite(lay2)
    if t > T1 + 0.3:                                       # the first, the half and the last
        marks = [(T[0], 'FIRST', hud.C_MILE), (T[len(T)//2], 'HALF IN BY', hud.INK), (T[-1], 'LAST', hud.MUTED)]
        for j, (v, word, col) in enumerate(marks):
            al = round(255*min(1.0, (t - T1 - 0.3 - j*0.7)/0.4))
            if al <= 0: continue
            x = x_of(v, a, w, n); y = BASE - BAR_H - 40 + j*0
            for yy in range(round(BASE - BAR_H + 20), BASE, 16):
                d.line([(x, yy), (x, yy + 8)], fill=col + (al,), width=3)
            tx = min(X1 - 300, max(X0, x - 150)) if j == 1 else (X0 if j == 0 else X1 - 230)
            ty = BASE + 70 + (0 if j != 1 else 70)
            def lab(dd, tx=tx, ty=ty, word=word, v=v, col=col, al=al):
                hud.Card.text(None, dd, (tx, ty), word, F['label'], col + (al,), 0.12)
                dd.text((tx, ty + 34), hms(v), font=F['value'], fill=col + (al,))
            lay.alpha_composite(S.shadowed((W, H), lab, 6))
    return lay


def video(cut):
    a, w, counts = bins()
    F0 = S.fonts(2.0); disp = F0['disp']
    F = dict(label=F0['cta'], value=F0['value'], tick=F0['small'], clock=F0['stat'], q=disp(92), kick=F0['cta'])
    bg = backdrop()
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); S.brand(top, (64, 150))
    f, lines = S.fit(NAME, 96, 64, W - 128, S.fonts(2.0)); y = 214
    for ln in lines: top.alpha_composite(S.grad_text(ln, f, (64, y))); y += round(f.size*1.08)
    kick = (f"LAST YEAR · {DATA['year']} · {len(T):,} FINISHERS" if BEFORE else f"{DATA['year']} · {len(T):,} FINISHERS")
    top.alpha_composite(S.shadowed((W, H), lambda d: hud.Card.text(None, d, (64, y + 12), kick, F['kick'], hud.C_AID, 0.12), 6))
    q1, q2 = (('Where will', 'you finish?') if BEFORE else ('Where would', 'you finish?'))
    ask = 'COMMENT YOUR GOAL TIME' if BEFORE else 'COMMENT YOUR TIME'
    cta, cta_box = S.cta_layer({}, 'Plan your pace free', cta=cut)
    dst = OUT + f'finish-silent-{cut}.mp4'; p = K.writer(dst)
    for fr in range(1, N + 1):
        t = fr/FPS; u = fr/N
        ox, oy = round((bg.width - W)*u*0.6), round((bg.height - H)*(0.2 + 0.5*u))
        im = bg.crop((ox, oy, ox + W, oy + H)).copy()
        im.alpha_composite(top); ch = chart(fr, a, w, counts, F)
        if t >= SECS - 4.2:                                    # the closing card takes the stage: the chart steps back
            k = max(0.25, 1 - (t - SECS + 4.2)/0.5); ch.putalpha(ch.getchannel('A').point(lambda v: round(v*k)))
        im.alpha_composite(ch)
        if T1 + 2.6 <= t < SECS - 4.2:
            al = round(255*min(1.0, (t - T1 - 2.6)/0.5))
            def qq(d):
                d.text((64, 1520), q1, font=F['q'], fill=hud.INK + (al,)); d.text((64, 1620), q2, font=F['q'], fill=hud.INK + (al,))
                hud.Card.text(None, d, (64, 1750), ask, F['label'], hud.C_MILE + (al,), 0.12)
            im.alpha_composite(S.shadowed((W, H), qq, 8, 0.85))
        if t >= SECS - 4.2:
            bx = cta_box; S.frost(im, bx, S.band_mask(bx[3] - bx[1], 24).resize((bx[2] - bx[0], bx[3] - bx[1])), glass=0.55)
            im.alpha_composite(cta)
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('SILENT', cut, N, 'frames', dst)
    return dst


def words(m):
    page, vid, ig = K.links(SLUG); med = T[len(T)//2]
    when = f'Racing {NAME} this weekend?' if BEFORE else f'{NAME} {DATA["year"]}: where would you have finished?'
    facts = (f'Last year {len(T):,} runners finished, from {hms(T[0])} to {hms(T[-1])}; half were in by {hms(med)}.' if BEFORE else
             f'{len(T):,} runners finished, from {hms(T[0])} to {hms(T[-1])}; half were in by {hms(med)}.')
    ask = 'Where will you finish? Comment your goal time.' if BEFORE else 'Where would you have finished? Comment your time.'
    src = f'Finish times: official results ({DATA["source"].split(" (")[0]}).'
    utm = 'utm_source={}&utm_medium=social&utm_campaign=finish'
    caps = dict(
        instagram='\n\n'.join(x for x in [when + (f' @{ig}' if ig else ''), facts, ask, f'Plan your race free: {page.replace("https://", "")} (link in bio)' if page else '',
                                          'The whole course in 3D: full film on our YouTube channel, TrailGoat', K.music_line(m), K.TAGS] if x),
        facebook='\n\n'.join(x for x in [when, facts, ask, f'Plan your race free: {page}?{utm.format("facebook")}' if page else '',
                                         f'The whole course in 3D: https://trailgoat.run/films?{utm.format("facebook")}', K.music_line(m), K.TAGS] if x),
        tiktok='\n\n'.join(x for x in [when, facts, ask, f'Plan your race free: {page.replace("https://", "")}' if page else '', K.music_line(m), K.TAGS + ' #runtok'] if x))
    title = (f'{NAME}: where will you finish? Last year\'s {len(T):,} finishers #Shorts' if BEFORE else
             f'{NAME} {DATA["year"]}: where would you have finished? #Shorts')
    desc = '\n\n'.join(x for x in [facts, ask, src, f'The whole course in 3D, every aid station:\n▶ https://youtu.be/{vid}' if vid else '',
                                   f'Plan this race free on TrailGoat:\n▶ {page}' if page else '', K.music_line(m)] if x)
    meta = dict(title=title, description=desc, tags=['trail running', 'ultramarathon', NAME, 'finish times', 'race results', 'TrailGoat', 'Shorts'],
                privacy='public', playlist='Race Shorts')
    if vid: meta['related_video'] = vid
    K.write_words(DEST, caps, meta); print(title)


if __name__ == '__main__':
    m = None
    for cut in ('youtube', 'social'):
        silent = video(cut)
        m = K.mix(SLUG, silent, DEST + f'{SLUG}-{DATA["year"]}-finishers{"" if cut == "youtube" else "-social"}{"-before" if BEFORE else ""}.mp4', SECS)
    words(m)

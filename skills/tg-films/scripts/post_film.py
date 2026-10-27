#!/usr/bin/env python3
"""Dress a rendered TrailGoat flyover for YouTube: one command per film.

    post_film.py film.json [--skip-intro] [--skip-end] [--skip-hud] [--meta-only] [--upload]

film.json:
{
  "out_dir": "…/out/yt1080/georgia-sky-to-summit-25k",      render.py's out dir: course-{id}.json, hud-frames.json, poster.webp
  "master":  "…/georgia-sky-to-summit-25k-1080p-master.mp4", the clean 1080p master (no readout)
  "shots":   "…/Films/<slug>/357.json",                       optional: the verified aid pins (chapters come from these)
  "music":   {"file": "…/Bach Cello Suite….mp3", "start": 0, "delay": 0, "title": "Cello Suite No. 1, Prelude",
              "artist": "Bach, played by Cooper Cannell", "reason": "…", "credit": ""},
  "next":    {"title": "Perpetua Coast: 30 miles on the Oregon coast in 3D"},
  "intro":   "…/Films/assets/intro-trailgoat-films-1080p24.mp4",
  "dest":    "…/Films/georgia-sky-to-summit-25k",
  "playlist": "Race Flyovers", "privacy": "public"
}

Writes to dest: {slug}-youtube.mp4, {slug}-thumb.png, description.txt, meta.json (for yt_upload.py), work/.
Steps: hud.py readout → render_end_card.py → ffmpeg concat (intro + film + card) with the music mixed to
-14 LUFS → thumbnail from the poster → chapters from the pins and hud-frames.json → meta.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
# Pillow and imageio-ffmpeg live in the TrailGoat venv: run there, whatever python started this
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])
UPLOADER_PY = os.environ.get('TG_UPLOADER_PY', str(Path.home() / '.config/trailgoat-youtube/venv/bin/python'))
MI, FT, FPS = 1609.344, 3.28084, 24
INTRO_S, CARD_S = 5.0, 15.0        # the Unreal ident and the end card (the real lengths are probed)


def sh(*cmd, **kw):
    print('$', ' '.join(str(c) for c in cmd)[:220], flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def ffmpeg():
    out = subprocess.run([PY, '-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def probe(ff: str, path: str) -> dict:
    """Duration, size and fps of a video, from ffmpeg's own banner (no ffprobe in the venv)."""
    r = subprocess.run([ff, '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r.stderr); d = int(m[1])*3600 + int(m[2])*60 + float(m[3]) if m else 0
    v = re.search(r'Video:.*?(\d{3,5})x(\d{3,5}).*?([\d.]+) fps', r.stderr)
    return dict(seconds=d, w=int(v[1]) if v else 0, h=int(v[2]) if v else 0, fps=float(v[3]) if v else 0,
                audio='Audio:' in r.stderr)


def race_name(rec: dict) -> str:
    base = re.split(r'\s+[—–-]\s+', rec.get('name', ''))[0]
    return re.sub(r'\s{2,}', ' ', re.sub(r'\b(19|20)\d{2}\b', '', base)).strip(' -—–')


def mmss(t: float) -> str:
    t = int(round(t)); return f'{t//60}:{t%60:02d}'


# ---------- chapters ----------
KEEP_CAPS = {'AS', 'AS1', 'AS2', 'AS3', 'AS4', 'AS5', 'AS6', 'AS7', 'AS8', 'AS9', 'TH', 'CP', 'FR', 'NF', 'US', 'SR', 'TR', 'II', 'III', 'IV', 'HQ', 'KOA'}
def chapter_name(label: str) -> str:
    """'ADOBE AS' → 'Adobe AS', 'HWY 189' → 'Hwy 189', 'MT. MITCHELL' → 'Mt. Mitchell': title case that keeps the
    station abbreviations ('AS' is aid station, not 'As')"""
    words = label.split()
    return ' '.join(w if re.sub(r'[^A-Z0-9]', '', w) in KEEP_CAPS or re.fullmatch(r'AS-?\d+', w) else w.capitalize() if not w[:1].isdigit() else w.lower()
                    for w in words)


def chapter_marks(rec: dict, hud: dict, shots: dict | None, intro_s: float, card_s: float = 0.0) -> list[tuple[float, str]]:
    """(seconds in the final film, label): the start, each verified aid pin, the finish, the card."""
    dist = hud['dist_m']; fps = hud.get('fps', FPS); total = float(rec['distance_m'])
    k = total / float(hud.get('route_m') or total)                     # GPX miles → catalogue metres, as hud.py does
    pins: list[tuple[str, float]] = []
    if shots and shots.get('aids'):
        for mi, label in shots['aids']:
            name, _, tail = label.partition(' · ')
            miles = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', tail)] or [float(mi)]
            pins += [(chapter_name(name), x*MI*k) for x in miles]
    else:
        # the catalogue's names carry notes ('Bartram (cutoff only, no aid)'); keep the name, flag a cutoff
        aids = rec.get('aid_stations'); aids = json.loads(aids) if isinstance(aids, str) else (aids or [])
        for a in aids:
            if not a.get('name'):
                continue
            name = re.sub(r'\s*\(.*?\)', '', a['name']).strip()
            if 'cutoff' in a['name'].lower() and 'no aid' in a['name'].lower():
                name += ' (cutoff)'
            pins.append((name, float(a.get('distM') or 0)))
    pins.sort(key=lambda p: p[1])

    def t_at(m: float) -> float:
        for i, d in enumerate(dist):
            if d >= m:
                return intro_s + i/fps
        return intro_s + len(dist)/fps

    marks = [(0.0, f'Start: {race_name(rec)}')]                          # the 4 s intro rides inside the first chapter
    for name, m in pins:
        if 0 < m < total - 400:
            unit = f'km {m/1000:.1f}' if (rec.get('units') == 'metric') else f'mi {m/MI:.1f}'
            marks.append((t_at(m), f'{name} · {unit}'))
    fin_t = intro_s + len(dist)/fps
    shots_idx = hud.get('shot') or []
    if shots_idx:                                                       # the finish settle is the film's last shot
        last = max(shots_idx); first = shots_idx.index(last)
        marks.append((intro_s + first/fps, 'The finish'))
    if card_s > 0:
        marks.append((fin_t, 'Plan this race on TrailGoat'))
    # YouTube wants chapters ≥ 10 s apart and increasing: drop a pin that crowds the previous one
    out = []
    for t, lab in sorted(marks, key=lambda x: x[0]):
        if out and t - out[-1][0] < 10:
            continue
        out.append((t, lab))
    return out


# ---------- data credits ----------
# Terrain comes from Mapzen's Terrain Tiles on AWS; Tilezen asks for each source dataset to be credited "in a place
# reasonable to the medium" (https://github.com/tilezen/joerd/blob/master/docs/attribution.md): the US data is USGS
# 3DEP/SRTM (public domain, credit asked), and several countries' DEMs carry their own required notice. The coastline is
# OpenStreetMap (ODbL: "© OpenStreetMap contributors" plus openstreetmap.org/copyright in the credits or description).
EU_DEM = {'albania', 'andorra', 'austria', 'belgium', 'bosnia and herzegovina', 'bulgaria', 'croatia', 'cyprus', 'czech republic',
          'czechia', 'denmark', 'estonia', 'finland', 'france', 'germany', 'greece', 'hungary', 'iceland', 'ireland', 'italy', 'kosovo',
          'latvia', 'liechtenstein', 'lithuania', 'luxembourg', 'malta', 'monaco', 'montenegro', 'netherlands', 'north macedonia',
          'norway', 'poland', 'portugal', 'romania', 'serbia', 'slovakia', 'slovenia', 'spain', 'sweden', 'switzerland', 'turkey',
          'united kingdom', 'uk', 'england', 'scotland', 'wales'}
DEM_NOTICE = {
    'australia': '© Commonwealth of Australia (Geoscience Australia) 2017.',
    'austria': '© offene Daten Österreichs – Digitales Geländemodell (DGM) Österreich.',
    'canada': 'Contains information licensed under the Open Government Licence – Canada.',
    'mexico': 'Source: INEGI, Continental relief, 2016.',
    'new zealand': 'Copyright 2011 Crown copyright (c) Land Information New Zealand and the New Zealand Government.',
    'norway': '© Kartverket.',
    'united kingdom': '© Environment Agency copyright and/or database right 2015. All rights reserved.',
}
US = {'united states', 'united states of america', 'usa', 'us'}
# Imagery credits, by render.py's source names (its "IMAGERY used" log line). All are free to publish with these.
IMAGERY_CREDIT = {
    'usgs': 'Imagery: USDA NAIP via USGS The National Map: Orthoimagery.',
    'ign': 'Aerial imagery: IGN BD ORTHO®, Licence Ouverte Etalab 2.0.',
    'swisstopo': 'Aerial imagery: © swisstopo, SWISSIMAGE (free geodata of the Swiss Confederation).',
    'pnoa': 'Aerial imagery: PNOA cedido por © Instituto Geográfico Nacional (CC BY 4.0).',
    's2-2016': 'Satellite imagery: Sentinel-2 cloudless 2016 by EOX IT Services GmbH, https://s2maps.eu '
               '(contains modified Copernicus Sentinel data 2016), CC BY 4.0.'}
# the short on-screen form, for sources that ask to be named where their pictures are seen (PNOA's terms require it)
IMAGERY_ONSCREEN = {'ign': 'IGN BD ORTHO', 'swisstopo': '© swisstopo', 'pnoa': 'PNOA cedido por © IGN', 's2-2016': 'Sentinel-2 cloudless 2016 by EOX'}


def render_sources(film: dict) -> dict:
    """what the render actually used, from render.py's own log lines in out_dir: the imagery source and whether the
    OpenStreetMap coastline went in. film.json's "imagery" / "coastal" override when there's no log."""
    found = {'imagery': film.get('imagery'), 'osm': film.get('coastal'), 'used': film.get('imagery_used')}
    for log in sorted(Path(film['out_dir']).glob('*.log')):
        txt = log.read_text(errors='ignore')
        m = re.search(r'TERRAIN chunks .* imagery (\w+)', txt)
        if m and found['imagery'] is None: found['imagery'] = m[1]
        u = re.search(r'IMAGERY used (.+)', txt)                     # render.py since 2026-10-27: which sources filled tiles
        if u and found['used'] is None: found['used'] = [kv.split(':')[0] for kv in u[1].split()]
        if found['osm'] is None and re.search(r'OSM coastline \d+ segments', txt): found['osm'] = True
    return found


def data_credits(rec: dict, film: dict) -> str:
    src = render_sources(film); country = (rec.get('country') or '').strip().lower()
    if src['imagery'] == 'esri':
        sys.exit('this render used Esri World Imagery, whose terms do not allow publishing it: re-render with --imagery usgs or --style relief')
    us = country in US or not country
    terrain = 'Terrain: Mapzen Terrain Tiles (AWS Open Data); ' + ('3DEP and SRTM data courtesy of the U.S. Geological Survey.' if us
               else 'SRTM and GMTED2010 data courtesy of the U.S. Geological Survey.')
    notices = []
    if country in EU_DEM: notices.append('Produced using Copernicus data and information funded by the European Union - EU-DEM layers.')
    key = 'united kingdom' if country in ('uk', 'england', 'scotland', 'wales') else country
    if key in DEM_NOTICE: notices.append(DEM_NOTICE[key])
    lat = rec.get('start_lat') or rec.get('lat')
    if lat is not None and float(lat) > 60:
        notices.append('ArcticDEM: DEMs created from DigitalGlobe, Inc., imagery and funded under National Science Foundation '
                       'awards 1043681, 1559691, and 1542736.')
    parts = [terrain, *notices]
    used = src['used'] or ([src['imagery']] if src['imagery'] not in (None, 'auto', 'none') else ['usgs'] if src['imagery'] is None else [])
    if 'esri' in used: sys.exit('this render used Esri World Imagery, whose terms do not allow publishing it')
    parts += [IMAGERY_CREDIT[k] for k in IMAGERY_CREDIT if k in used]
    if src['osm']: parts.append('Coastline: © OpenStreetMap contributors, openstreetmap.org/copyright')
    parts.append('Rendered in Blender from the course GPX.')
    return '\n'.join(parts)


# ---------- description ----------
def description(rec: dict, film: dict, marks: list[tuple[float, str]], total_s: float) -> str:
    name = race_name(rec); ev = rec.get('event') or {}
    metric = rec.get('units') == 'metric'
    dist = f"{rec['distance_m']/1000:.0f} km" if metric else f"{rec['distance_m']/MI:.0f} miles"
    gain_m = float(rec.get('official_gain_m') or rec.get('gain_m') or 0)
    gain = f"{gain_m:,.0f} m" if metric else f"{gain_m*FT:,.0f} ft"
    where = ', '.join(x for x in (rec.get('region'), rec.get('country')) if x)
    org = f" Organized by {ev['organizer']}." if ev.get('organizer') else ''
    date = ''
    try:                                                                # a race still ahead gets its date; a past one doesn't
        import datetime as dt
        rd = dt.date.fromisoformat(str(ev.get('race_date') or '')[:10])
        if rd >= dt.date.today():
            date = f" Race day: {rd.strftime('%B %-d, %Y')}."
    except ValueError:
        pass
    url = f"https://trailgoat.run{rec.get('page_url') or '/course/' + film['slug']}"
    m = film.get('music') or {}
    music = ''
    if m.get('title'):
        music = f"\nMusic: \"{m['title']}\" ({m['artist']})." if m.get('artist') else f"\nMusic: \"{m['title']}\"."
        if m.get('reason'):
            music += f" Why this one: {m['reason']}"
        if m.get('credit'):
            music += f"\n{m['credit']}"
    credits = data_credits(rec, film)
    chapters = '\n'.join(f'{mmss(t)} {lab}' for t, lab in marks)
    tag = re.sub(r'[^A-Za-z0-9]', '', name)
    return (f"{name} from the start line to the finish: {dist} and {gain} of climbing over the real terrain"
            f"{(' of ' + where) if where else ''}, with every aid station pinned where it stands.{org}{date}\n\n"
            f"Plan this race free on TrailGoat: the elevation profile, every aid station and cutoff, a pacing and "
            f"fuel plan, race-week weather, and a live crew sheet.\n▶ {url}\n\n"
            f"Chapters\n{chapters}\n{music}\n\n{credits}\n\n"
            f"More flyovers: https://www.youtube.com/@trailgoatrun\n\n#TrailRunning #Ultramarathon #{tag}")


# ---------- thumbnail ----------
def thumbnail(rec: dict, poster: Path, out: Path):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(poster).convert('RGB').resize((1280, 720), Image.LANCZOS)
    # a dark gradient up from the bottom so the type reads on snow and sand
    ov = Image.new('L', (1280, 720), 0); d = ImageDraw.Draw(ov)
    for y in range(720):
        d.line([(0, y), (1280, y)], fill=int(200*max(0.0, (y-300)/420)))
    im = Image.composite(Image.new('RGB', (1280, 720), (14, 16, 24)), im, ov)
    font_path = REPO / 'assets/fonts/Sora-wght.ttf'
    def sora(sz, w):
        f = ImageFont.truetype(str(font_path), sz)
        try: f.set_variation_by_axes([w])
        except Exception: pass
        return f
    name = race_name(rec).upper(); metric = rec.get('units') == 'metric'
    gain_m = float(rec.get('official_gain_m') or rec.get('gain_m') or 0)
    sub = (f"{rec['distance_m']/1000:.0f} KM · {gain_m:,.0f} M UP" if metric
           else f"{rec['distance_m']/MI:.0f} MI · {gain_m*FT:,.0f} FT UP") + "  ·  3D COURSE FLYOVER"
    dr = ImageDraw.Draw(im)
    size = 104
    while size > 56 and dr.textlength(name, font=sora(size, 800)) > 1180:
        size -= 6
    f1 = sora(size, 800); words = name.split()
    lines = [name] if dr.textlength(name, font=f1) <= 1180 else [' '.join(words[:len(words)//2]), ' '.join(words[len(words)//2:])]
    y = 720 - 60 - 44 - len(lines)*(size + 8)
    for ln in lines:
        dr.text((50, y), ln, font=f1, fill=(247, 248, 250)); y += size + 8
    dr.text((52, 720 - 60 - 36), sub, font=sora(28, 600), fill=(255, 196, 64))
    # the wordmark top-left: TRAIL in ink, GOAT in the brand gradient
    f2 = sora(40, 800); dr.text((50, 36), 'TRAIL', font=f2, fill=(236, 242, 240))
    tw = dr.textlength('TRAIL', font=f2); gw = int(dr.textlength('GOAT', font=f2)); asc, desc = f2.getmetrics()
    mask = Image.new('L', (gw+6, asc+desc), 0); ImageDraw.Draw(mask).text((0, 0), 'GOAT', font=f2, fill=255)
    grad = Image.new('RGB', mask.size); gd = ImageDraw.Draw(grad)
    for x in range(mask.size[0]):
        t = x/max(1, mask.size[0]-1); c = (int(13+(122-13)*t), int(185+(162-185)*t), int(215+(247-215)*t))
        gd.line([(x, 0), (x, mask.size[1])], fill=c)
    im.paste(grad, (int(50+tw), 36), mask)
    im.save(out, optimize=True)
    if out.stat().st_size > 2_000_000:
        im.save(out.with_suffix('.jpg'), quality=88); print('thumbnail >2 MB as PNG, wrote JPG too')


# ---------- the film ----------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('film'); ap.add_argument('--skip-intro', action='store_true'); ap.add_argument('--skip-end', action='store_true')
    ap.add_argument('--skip-hud', action='store_true', help='the master already carries the readout')
    ap.add_argument('--upload', action='store_true', help='run yt_upload.py at the end')
    ap.add_argument('--meta-only', action='store_true', help='keep the assembled video; redo the thumbnail, description and meta.json')
    a = ap.parse_args()
    film = json.loads(Path(a.film).read_text()); ff = ffmpeg()
    out_dir = Path(film['out_dir']); dest = Path(film['dest']); work = dest / 'work'; work.mkdir(parents=True, exist_ok=True)
    rec = json.loads(next(out_dir.glob('course-*.json')).read_text())
    slug = film.get('slug') or (rec.get('page_url') or '').rsplit('/', 1)[-1] or f"course-{rec['id']}"
    film['slug'] = slug
    hud = json.loads((out_dir / 'hud-frames.json').read_text())
    if film.get('shots') and not Path(film['shots']).exists():          # a removed worktree would quietly swap in the catalogue's chapters
        sys.exit(f"shots file not found: {film['shots']} (copy it into {dest} and point film.json there)")
    shots = json.loads(Path(film['shots']).read_text()) if film.get('shots') else None
    master = Path(film['master'])

    # 1. the readout and corner mark (hud.py, from the TrailGoat checkout)
    hud_mp4 = work / f'{slug}-hud.mp4'
    if a.skip_hud:
        hud_mp4 = master
    elif not hud_mp4.exists():
        # phone sizes: the CSS-sized card (values 17.6 px, labels 10.6 px at 1080p) and the 17 px corner mark can't be read on a
        # phone (Kris, 2026-10-26, 17 Pro Max); 1.7x puts the values at 30 px, 2.2x the mark at 37 px. film.json "hud" overrides.
        hcfg = film.get('hud') or {}; hud_py = REPO / 'scripts/flythrough/hud.py'
        extra = ['--scale', str(hcfg.get('scale', 1.7))]
        if '--mark-scale' in hud_py.read_text(): extra += ['--mark-scale', str(hcfg.get('mark_scale', 2.2))]
        # "hud": {"hide": "645-735"}: frames the card steps aside for (trailgoat #754), e.g. a sign passing under it
        if hcfg.get('hide') and '--hide' in hud_py.read_text(): extra += ['--hide', str(hcfg['hide'])]
        onscreen = [IMAGERY_ONSCREEN[k] for k in IMAGERY_ONSCREEN if k in (render_sources(film)['used'] or [])]
        if onscreen and '--credit' in hud_py.read_text(): extra += ['--credit', 'Imagery: ' + ' · '.join(onscreen)]
        sh(PY, hud_py, out_dir, '--src', master, '--dst', hud_mp4, *extra)
    film_s = probe(ff, str(hud_mp4))['seconds']

    # 2. the end card, with the next film named
    parts = []
    intro = Path(film.get('intro') or '')
    intro_s = 0.0; intro_sound = False
    if not a.skip_intro and intro.exists():
        ip = probe(ff, str(intro)); parts.append(intro); intro_s = ip['seconds']; intro_sound = ip['audio']
    elif not a.skip_intro:
        print('no intro file yet; skipping the intro')
    parts.append(hud_mp4)
    card = work / f'{slug}-end.mp4'
    if not a.skip_end:
        if not card.exists():
            sh(PY, HERE / 'render_end_card.py', '--race', race_name(rec), '--next', (film.get('next') or {}).get('title', 'The next flyover'), '--out', card)
        parts.append(card)
    card_s = probe(ff, str(card))['seconds'] if card.exists() and not a.skip_end else 0.0
    total_s = intro_s + film_s + card_s

    # 3. assemble: concat the video at 24 fps 1920×1080. An intro with its own sound (the sonic logo) plays
    #    as mastered and the music starts as it ends; a silent intro gets the music under it too.
    m = film.get('music') or {}
    inputs = []; fc = []
    for i, p in enumerate(parts):
        inputs += ['-i', str(p)]
        fc.append(f'[{i}:v]fps={FPS},scale=1920:1080:flags=lanczos,format=yuv420p,setsar=1[v{i}]')
    fc.append(''.join(f'[v{i}]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=0[v]')
    final = dest / f'{slug}-youtube.mp4'
    # the track starts as the intro ends (plus music.delay, e.g. to let a short piece finish on the finish pull-back);
    # a track that runs out before the video ends finishes on its own ending instead of a forced fade
    music_at = (intro_s if intro_sound else 0.0) + float(m.get('delay') or 0)
    if m.get('file'):
        inputs += ['-i', m['file']]; ai = len(parts); st = float(m.get('start') or 0)
        music_s = total_s - music_at; avail = max(0.0, probe(ff, m['file'])['seconds'] - st)
        play_s, fade = (avail, f'afade=t=out:st={max(0.0, avail - 0.3):.2f}:d=0.3') if avail < music_s else \
                       (music_s, f'afade=t=out:st={max(0.0, music_s - 3.0):.2f}:d=3')
        if avail < music_s: print(f'the track ends on its own at {music_at + avail:.1f} s of {total_s:.1f} s')
        delayed = intro_sound or music_at > 0
        fc.append(f'[{ai}:a]atrim=start={st}:end={st+play_s},asetpts=PTS-STARTPTS,'
                  f'afade=t=in:st=0:d=1.5,{fade},'
                  f'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000' + (f',adelay={int(music_at*1000)}:all=1[mus]' if delayed else '[a]'))
        if delayed and not intro_sound: fc.append(f'[mus]apad=whole_dur={total_s:.3f}[a]')
    if intro_sound:
        fc.append(f'[0:a]aresample=48000,apad=whole_dur={total_s:.3f}[sting]')
        fc.append('[sting][mus]amix=inputs=2:duration=first:normalize=0[a]' if m.get('file') else '[sting]anull[a]')
    if m.get('file') or intro_sound:
        maps = ['-map', '[v]', '-map', '[a]', '-c:a', 'aac', '-b:a', '192k']
    else:
        maps = ['-map', '[v]', '-an']
    if a.meta_only and final.exists():
        print('keeping', final)
    else:
        sh(ff, '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(fc), *maps,
           '-c:v', 'libx264', '-preset', 'slow', '-crf', 16, '-pix_fmt', 'yuv420p', '-r', FPS,
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', '-t', f'{total_s:.3f}', final)
    got = probe(ff, str(final)); print('final', got)
    if abs(got['seconds'] - total_s) > 0.6 or got['w'] != 1920:
        sys.exit(f'assembly came out wrong: {got} vs {total_s:.1f} s expected')

    # 4. the thumbnail, from the poster frame
    poster = out_dir / 'poster.webp'
    if not poster.exists():
        poster = work / 'poster.png'
        sh(ff, '-y', '-loglevel', 'error', '-ss', f'{intro_s + 0.4*film_s:.2f}', '-i', final, '-frames:v', '1', poster)
    thumb = dest / f'{slug}-thumb.png'; thumbnail(rec, poster, thumb)

    # 5. chapters, description, metadata for the uploader
    marks = chapter_marks(rec, hud, shots, intro_s, card_s); desc = description(rec, film, marks, total_s)
    (dest / 'description.txt').write_text(desc)
    name = race_name(rec); metric = rec.get('units') == 'metric'
    dist = f"{rec['distance_m']/1000:.0f} km" if metric else f"{rec['distance_m']/MI:.0f}-mile"
    # a name that already carries its distance (Javelina Jundred 100 Miler, Bigfoot 200) keeps it: the GPX runs short of
    # the official distance on long courses (98.9 mi, 184 mi), and "the whole 99-mile course" reads wrong under it
    whole = 'the whole course' if re.search(r'\d', name) else f'the whole {dist} course'
    title = film.get('title') or f"{name}: {whole} in 3D, every aid station | TrailGoat"
    if len(title) > 100:
        title = f"{name} in 3D: every aid station | TrailGoat"
    tags = ['trail running', 'ultramarathon', 'race flyover', '3D course map', name, 'aid stations', 'race planning', 'TrailGoat']
    if (rec.get('event') or {}).get('organizer'):
        tags.append(rec['event']['organizer'])
    meta = dict(title=title, description=desc, tags=tags[:15], privacy=film.get('privacy', 'public'),
                thumbnail=str(thumb), playlist=film.get('playlist', 'Race Flyovers'))
    (dest / 'meta.json').write_text(json.dumps(meta, indent=2))
    print(f"\n{final}\n{thumb}\n{dest/'meta.json'}\ntitle: {title}\nchapters:\n" + '\n'.join(f'  {mmss(t)} {l}' for t, l in marks))

    if a.upload:
        sh(UPLOADER_PY, REPO / 'marketing/youtube/yt_upload.py', 'upload', final, dest / 'meta.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())

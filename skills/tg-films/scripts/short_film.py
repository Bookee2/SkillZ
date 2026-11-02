#!/usr/bin/env python3
"""A YouTube Short from a dressed flyover: its biggest-climbing 40 s, filmed again in 9:16 with the readout, the film's
own music at that moment, and a title and description that send people to the full film.

    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/short_film.py <dest>/film.json [--seconds 40]

Reads the film.json post_film.py dressed the long film from, and writes <dest>/short/:
  pick.json            the window and the hook (trailgoat short.py pick). Kept on a rerun, so a hand edit sticks:
                       rename `climb.place` when the nearest aid pin isn't what the climb is known as.
  <slug>-short.mp4     1080x1920, 24 fps, the music at -14 LUFS
  description.txt, meta.json   for yt_upload.py (playlist "Race Shorts", no thumbnail: Shorts don't show one)
The portrait frames render out of process in Blender (render.py --portrait 0.5 --frames …) into
Renders/flyovers/shorts/<slug>/, under the studio's render lock, resumable, and are kept until the Short is checked.

Stages: --stage pick | render | dress | all (default). The long film's video id comes from app/films.json in the
checkout (by its course link) or --video-id. Kris, 2026-11-02: "Yes: after batch 5, order the next batch by race date
and build the Shorts pipeline."

Every race week after, the Short goes out again for that year's edition (Kris, 2026-11-02: "Yes, build the yearly
race-week re-post: year in titles and captions, not in the video; fresh cut each year; links to that year's course
page"):
    short_film.py <dest>/film.json --week 2027-08-16          # the edition from the catalogue (editions.py)
    short_film.py <dest>/film.json --edition 2027 --race-date 2027-08-21 --page <url> --dry-run
    short_film.py <dest>/film.json --uploaded <video id> --publish-at 2027-08-16T13:00:00Z
--week skips a race whose Short already went out for that year (short/history.json), else moves last year's files to
short/<year>/ and picks a window clear of every earlier year's (short.py pick --exclude). The title, description and
captions carry the year and link to that edition's course page; the picture doesn't change. The Short also gets
short/captions/{facebook,instagram,tiktok}.txt. --uploaded records the upload and, now it's checked and out, puts the
social cut and its caption in iCloud's TrailGoat Videos/TikTok for Kris to post and the Meta captions in
Films/_social/captions (Meta posting is by hand until the Meta app exists). --dry-run only picks and writes the words,
into short/dry-<year>/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])
sys.path.insert(0, str(HERE))
import editions  # noqa: E402  (the edition that runs a week, history.json, the year in a title)
import post_film  # noqa: E402  (helpers: ffmpeg, probe, course_page)

STUDIO = Path('/Volumes/KB SS/TrailGoat-Studio')
LOCK = STUDIO / 'Films/queue/.render.lock'
TIKTOK = Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs/TrailGoat Videos/TikTok'
CAPTIONS = STUDIO / 'Films/_social/captions'
UTM = 'utm_source=facebook&utm_medium=social&utm_campaign=shorts'
NY = ZoneInfo('America/New_York')
BLENDER = os.environ.get('BLENDER_BIN', '/Applications/Blender.app/Contents/MacOS/Blender')
MI, FT = 1609.344, 3.28084


def sh(*cmd, **kw):
    print('$', ' '.join(str(c) for c in cmd)[:240], flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def render_shots(film: dict) -> str:
    """The shots file the film was rendered from: a HUD-only copy (Leadville's 228-hud.json names both passes for the
    readout) sits beside it."""
    p = film['shots']
    plain = re.sub(r'-hud\.json$', '.json', p)
    return plain if os.path.exists(plain) else p


def course_json(film: dict) -> str:
    d = Path(film['out_dir'])
    return str(next(d.glob('course-*.json')))


def stage_pick(film: dict, short: Path, secs: float, exclude: list | None = None, pj: Path | None = None) -> dict:
    """The window (short.py pick), clear of `exclude` (earlier years' dist_m), into pj (default short/pick.json)."""
    pj = pj or short / 'pick.json'
    if pj.exists():
        print('pick: keeping', pj); return json.loads(pj.read_text())
    ex = ['--exclude', ','.join(f'{a}-{b}' for a, b in exclude)] if exclude else []
    out = subprocess.run([PY, REPO / 'scripts/flythrough/short.py', 'pick', film['out_dir'], '--shots', film['shots'],
                          '--seconds', str(secs), '--film', short.parent / 'film.json', *ex], capture_output=True, text=True, check=True).stdout
    pj.write_text(out); p = json.loads(out)
    print('pick:', p['frames'], p['climb'], f"(clear of {len(exclude)} earlier, overlap {p.get('overlap_m', 0)} m)" if exclude else '')
    return p


def stage_render(film: dict, p: dict, work: Path) -> None:
    f0, f1 = p['frames']; work.mkdir(parents=True, exist_ok=True)
    have = len(list((work / 'frames').glob('f_*.png'))) if (work / 'frames').exists() else 0
    if have >= f1 - f0 + 1:
        print('render: frames already there'); return
    while True:   # never two renders at once: wait for any batch render and take the studio's lock
        busy = subprocess.run(['pgrep', '-f', 'Blender.*-b'], capture_output=True).returncode == 0
        if not busy:
            try: LOCK.mkdir(); break
            except FileExistsError: pass
        time.sleep(30)
    try:
        for attempt in range(1, 6):
            with open(work / 'render.log', 'a') as log:
                r = subprocess.run([BLENDER, '-b', '-P', REPO / 'scripts/flythrough/render.py', '--', course_json(film), work,
                                    '--shots', render_shots(film), '--res', '1080x1920', '--portrait', '0.5', '--samples', '32',
                                    '--frames', f'{f0}-{f1}'], stdout=log, stderr=subprocess.STDOUT)
            # Blender exits 0 even when the script dies on a dropped tile fetch (Keweenaw, 2026-11-02): count the frames
            if len(list((work / 'frames').glob('f_*.png')) if (work / 'frames').exists() else []) >= f1 - f0 + 1: break
            tail = (work / 'render.log').read_text()[-6000:]
            if not re.search(r'URLError|Connection reset|timed out|RemoteDisconnected', tail):
                sys.exit(f'render failed: see {work}/render.log')
            print(f'render: network retry {attempt}'); time.sleep(60*attempt)
    finally:
        LOCK.rmdir()
    n = len(list((work / 'frames').glob('f_*.png')))
    if n < f1 - f0 + 1: sys.exit(f'render: {n} of {f1 - f0 + 1} frames')


def video_id(film: dict, page: str) -> str | None:
    """The long film's id on YouTube, from the films page's list (scripts/films_sync.py writes it), else from
    title_history.json (race_year.py moves the film's course link to each year's page before the list catches up)."""
    try:
        films = json.loads((REPO / 'app/films.json').read_text())
    except OSError:
        films = []
    films = films if isinstance(films, list) else films.get('films', [])
    slug = page.rstrip('/').split('/')[-1]
    got = next((f['id'] for f in films if f.get('course') == slug), None)
    th = editions.F / film['slug'] / 'title_history.json'
    if not got and th.exists():
        got = next((x.get('video_id') for x in reversed(json.loads(th.read_text())) if x.get('video_id')), None)
    return got


def figures(p: dict) -> tuple[str, str]:
    c = p['climb']; k = p['shown']
    if p['metric']:
        return f"{round(c['rise_m']):,} m", f"{(c['top_m'] - c['low_m'])*k/1000:.1f} km"
    return f"{round(c['rise_m']*FT):,} ft", f"{(c['top_m'] - c['low_m'])*k/MI:.1f} miles"


def the(race: str) -> str:
    return race if race.lower().startswith('the ') else f'the {race}'


def mix(film: dict, p: dict, m: dict, silent: Path, out: Path, ff: str) -> None:
    """The film's music at the same moment: master frame f plays at intro + (f-1)/fps in the long film, and the track
    (from music.start) comes in at music_at, as post_film.py mixes it."""
    n = p['frames'][1] - p['frames'][0] + 1; dur = n/p['fps']
    if not m.get('file'):
        sh(ff, '-y', '-loglevel', 'error', '-i', silent, '-c', 'copy', out); return
    intro = film.get('intro'); intro_s = post_film.probe(ff, intro)['seconds'] if intro and os.path.exists(intro) else 0.0
    intro_sound = bool(intro and os.path.exists(intro) and post_film.probe(ff, intro)['audio'])
    music_at = (intro_s if intro_sound else 0.0) + float(m.get('delay') or 0)
    at = float(m.get('start') or 0) + intro_s + (p['frames'][0] - 1)/p['fps'] - music_at
    avail = post_film.probe(ff, m['file'])['seconds'] - max(at, 0.0)
    lead = max(0.0, -at); play = min(dur - lead, avail)
    fade = f'afade=t=out:st={max(0.0, play - 1.5):.2f}:d=1.5' if play >= dur - lead - 0.05 else f'afade=t=out:st={max(0.0, play - 0.3):.2f}:d=0.3'
    af = (f'[1:a]atrim=start={max(at, 0.0):.3f}:end={max(at, 0.0) + play:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.4,{fade},'
          f'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000' + (f',adelay={int(lead*1000)}:all=1' if lead else '') + ',apad[a]')
    sh(ff, '-y', '-loglevel', 'error', '-i', silent, '-i', m['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', out)


def cleared(film: dict) -> dict:
    import music_rights
    m = music_rights.cleared_music(film.get('music') or {}, film['slug'])
    if m is None:
        sys.exit(f"{film['music']['file']} is a YouTube Audio Library recording and Music/public-domain/MAP.json has no cleared "
                 "copy of the piece: add one (see music_rights.py) before making this Short")
    return m


def stage_dress(film: dict, p: dict, short: Path, work: Path, vid: str | None, social_only: bool = False, ed: dict | None = None) -> None:
    """Two cuts of the same Short with the same music: <slug>-short.mp4 for YouTube ("link below") and
    <slug>-short-social.mp4 for Instagram, Facebook and TikTok (the channel named, since a caption link doesn't click
    there), plus their words (write_words). --social-only makes just the second, from the kept portrait video."""
    slug = film['slug']; ff = post_film.ffmpeg(); dur = (p['frames'][1] - p['frames'][0] + 1)/p['fps']
    m = cleared(film)
    frames_there = (work / 'frames').exists() and any((work / 'frames').glob('f_*.png'))
    src = [] if frames_there else ['--src', work / f'{slug}-portrait.mp4']
    if not frames_there and not (work / f'{slug}-portrait.mp4').exists(): sys.exit(f'{slug}: neither frames nor a portrait video in {work}')
    dress = [PY, REPO / 'scripts/flythrough/short.py', 'dress', work, '--pick', short / 'pick.json', '--film', short.parent / 'film.json', *src]
    out = short / f'{slug}-short.mp4'
    if not social_only:
        silent = work / f'{slug}-short-silent.mp4'
        sh(*dress, '--dst', silent); mix(film, p, m, silent, out, ff)
    silent_s = work / f'{slug}-short-social-silent.mp4'
    sh(*dress, '--cta', 'social', '--dst', silent_s); mix(film, p, m, silent_s, short / f'{slug}-short-social.mp4', ff)
    title, full = write_words(film, p, short, short, vid, m, ed, social_only)
    keep_clean(p, work, ff)
    print('SHORT', short / f'{slug}-short-social.mp4' if social_only else out, f'{dur:.1f} s'); print('title:', title); print('full film:', full)


def write_words(film: dict, p: dict, short: Path, dst: Path, vid: str | None, m: dict, ed: dict | None = None,
                social_only: bool = False) -> tuple[str, str]:
    """The Short's words into dst: description.txt and meta.json for YouTube, social-caption.txt, and
    captions/{facebook,instagram,tiktok}.txt as Business Suite and the TikTok app take them (Facebook's link clicks,
    so it carries the campaign tags; Instagram's doesn't, so "link in bio"; never "@trailgoatrun" off TikTok, which
    on Instagram tags a stranger). With an edition `ed` ({year, race_date, page, post_date}) they carry its year and
    link to its course page; a Short posted in its race week opens "Racing … this Saturday?"."""
    ed = ed or {}; year = ed.get('year')
    long_meta = json.loads((short.parent / 'meta.json').read_text())
    long_desc = (short.parent / 'description.txt').read_text()
    film_page = editions.PAGE_RE.search(long_desc)[0]
    page = ed.get('page') or film_page
    vid = vid or video_id(film, film_page)
    race = p['race']; named = editions.race_year(race, year); c = p.get('climb')
    if c:
        rise, run = figures(p)
        place = c.get('place')
        head = (f'{place} at {the(named)}' if place and place != 'The high point' else
                f'The high point of {the(named)}' if place else f'The biggest climb of {the(named)}')
        title = f'{head}: {rise} up in {run}, in 3D #Shorts'
        lede = f'{head}: {rise} of climbing in {run}, flown in 3D over the real terrain with the race readout.'
        here = (f"Here's {place}" if place and place != 'The high point' else "Here's the high point" if place else
                "Here's the biggest climb") + f': {rise} of climbing in {run}'
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location('flythrough_short', REPO / 'scripts/flythrough/short.py')
        sys.path.insert(0, str(REPO / 'scripts/flythrough')); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        span = mod.miles(p).lower()
        title = f'{named} in 3D: {span} #Shorts'
        lede = f'{named}, {span}, flown in 3D over the real terrain with the race readout.'
        here = f'Here are {span}'
    if len(title) > 100: title = title.replace(', in 3D', '')
    blocks = long_desc.split('\n\n')
    music = (f'Music: "{m["title"]}" ({m["artist"]}).' + (f" Why this one: {m['reason']}" if m.get('reason') else '')
             + (f"\n{m['credit']}" if m.get('credit') else '')) if m.get('title') else ''
    credits = [b for b in blocks if b.startswith(('Terrain:', 'Imagery:', 'Rendered', '©', 'Contains', 'Elevation'))]
    tags_line = next((b for b in reversed(blocks) if b.startswith('#')), '#TrailRunning #Ultramarathon')
    full = f'https://youtu.be/{vid}' if vid else 'https://www.youtube.com/@trailgoatrun'
    desc = '\n\n'.join(x for x in [
        lede,
        f'The whole course, every aid station, in the full film:\n▶ {full}',
        f'Plan this race free on TrailGoat:\n▶ {page}',
        music, *credits, f'#Shorts {tags_line.strip()}'] if x)
    if not social_only: (dst / 'description.txt').write_text(desc + '\n')   # the YouTube cut's, untouched by --social-only
    meta = dict(title=title, description=desc, tags=list(dict.fromkeys(long_meta.get('tags', []) + ([named] if year else []) + ['Shorts'])),
                privacy=film.get('privacy', 'public'), playlist='Race Shorts', related_video=vid)
    if year: meta['edition'] = year
    if film.get('short_publish_at') and not year: meta['publish_at'] = film['short_publish_at']   # batch 6: with its film
    if not social_only: (dst / 'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    # off YouTube: links don't click on Instagram or TikTok, so the page by name; the music and its credit travel with it
    tag = re.sub(r'[^A-Za-z0-9]', '', race)
    sound = (f'Music: "{m["title"]}" ({m["artist"]})' + (f"\n{m['credit']}" if m.get('credit') else '')) if m.get('title') else ''
    tags = f'#trailrunning #ultramarathon #ultrarunning #{tag} #trailgoat'
    cap = '\n\n'.join(x for x in [
        lede.replace('flown in 3D', 'in 3D'),
        'The whole course and every aid station in the full 3D film on YouTube: @trailgoatrun',
        f'Plan this race free on TrailGoat: {page.replace("https://", "")}' if year else 'Plan this race free on TrailGoat: trailgoat.run',
        sound, tags] if x)
    (dst / 'social-caption.txt').write_text(cap + '\n')
    opener = lede.replace('flown in 3D', 'in 3D')
    if ed.get('race_date') and ed.get('post_date'):
        rd, pd = dt.date.fromisoformat(ed['race_date'][:10]), dt.date.fromisoformat(ed['post_date'][:10])
        if 0 <= (rd - pd).days <= 6:
            opener = f"Racing {the(named)} this {rd.strftime('%A')}? {here}, in 3D over the real terrain."
    plan = f"Plan your {editions.race_year(film.get('short_name') or editions.short_name(race), year)} free: pacing, fuel, every aid station and cutoff."
    bare = page.replace('https://', '')
    films_fb = f'https://trailgoat.run/films?{UTM}'
    caps = dict(
        facebook=[opener, f'{plan}\n→ {page}?{UTM}', f'The whole course in 3D, every aid station: full film at {films_fb} (and on YouTube: TrailGoat)', sound, tags],
        instagram=[opener, f'{plan}\n→ {bare} (link in bio)', 'The whole course in 3D: full film on our YouTube channel, TrailGoat (link in bio)', sound, tags],
        tiktok=[opener, f'{plan}\n→ {bare}', 'The whole course in 3D: full film on our YouTube channel, TrailGoat', sound, f'{tags} #runtok'])
    (dst / 'captions').mkdir(exist_ok=True)
    for k, parts in caps.items():
        (dst / 'captions' / f'{k}.txt').write_text('\n\n'.join(x for x in parts if x) + '\n')
    return title, full


def keep_clean(p: dict, work: Path, ff: str) -> None:
    """The portrait frames are ~3.5 GB a Short. Keep them as one clean high-quality video, <slug>-portrait.mp4 (what
    week_short.py plays behind the race's card), and drop the PNGs once its frame count checks out (KB SS was at 87 %,
    2026-11-02)."""
    import shutil
    frames = work / 'frames'; f0, f1 = p['frames']; n = f1 - f0 + 1
    if not frames.exists(): return
    clean = work / f'{work.name}-portrait.mp4'
    sh(ff, '-y', '-loglevel', 'error', '-framerate', str(p['fps']), '-start_number', str(f0), '-i', frames / 'f_%04d.png',
       '-frames:v', str(n), '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', clean)
    got = subprocess.run([ff, '-i', clean, '-map', '0:v', '-c', 'copy', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.findall(r'frame=\s*(\d+)', got)
    if m and int(m[-1]) == n:
        shutil.rmtree(frames); print('kept', clean.name, f'({n} frames); frames removed')
    else:
        print('portrait video frame count', m[-1] if m else '?', 'vs', n, ': frames kept')


def record_upload(film: dict, short: Path, vid: str, publish_at: str | None) -> int:
    """The Short is checked and on YouTube: uploaded.json, its edition in history.json, and the off-YouTube copies,
    dated the day it goes public: the social cut and TikTok caption in iCloud for Kris to post from his phone, the
    Facebook and Instagram captions in Films/_social/captions for Business Suite."""
    slug = film['slug']
    (short / 'uploaded.json').write_text(json.dumps(dict(id=vid, publish_at=publish_at)) + '\n')
    h = editions.load_history(short)
    e = editions.entry(h, h['current']) if h['current'] else None
    if e: e.update(video_id=vid, publish_at=publish_at, status='uploaded'); editions.save_history(short, h)
    when = (dt.datetime.fromisoformat(publish_at.replace('Z', '+00:00')).astimezone(NY).date() if publish_at else dt.date.today()).isoformat()
    social = short / f'{slug}-short-social.mp4'; caps = short / 'captions'
    if social.exists() and caps.exists():
        TIKTOK.mkdir(parents=True, exist_ok=True); CAPTIONS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(social, TIKTOK / f'{when} {slug}.mp4')
        shutil.copy2(caps / 'tiktok.txt', TIKTOK / f'{when} {slug} caption.txt')
        for k in ('facebook', 'instagram', 'tiktok'):
            shutil.copy2(caps / f'{k}.txt', CAPTIONS / f'{when}-{slug}-{k}.txt')
        print(f'TikTok: {TIKTOK / f"{when} {slug}.mp4"}; Meta captions: {CAPTIONS}/{when}-{slug}-*.txt (post by hand until the Meta app exists)')
    print(f'recorded {slug} {vid} {publish_at or "(public now)"}' + (f", edition {h['current']}" if e else ''))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('film', help='the film.json the long film was dressed from')
    ap.add_argument('--seconds', type=float, default=40.0)
    ap.add_argument('--stage', choices=('pick', 'render', 'dress', 'all'), default='all')
    ap.add_argument('--video-id', help="the long film's YouTube id (default: app/films.json by its course link)")
    ap.add_argument('--social-only', action='store_true', help="only the off-YouTube cut (<slug>-short-social.mp4) of a Short already made")
    ap.add_argument('--week', help="the race week's Monday, YYYY-MM-DD: that year's edition from the catalogue. A race whose "
                                   "Short already went out that year is skipped; else a fresh cut, clear of earlier years'")
    ap.add_argument('--edition', type=int, help='the edition year instead of --week (a dry run, or a year the catalogue lacks)')
    ap.add_argument('--race-date', help="with --edition: that edition's race date, YYYY-MM-DD")
    ap.add_argument('--post-date', help="with --edition: the day the Short goes out, YYYY-MM-DD (opens 'Racing … this Saturday?')")
    ap.add_argument('--page', help="with --edition: that edition's course page (default: the film's)")
    ap.add_argument('--dry-run', action='store_true', help='with --week or --edition: pick and write the words into short/dry-<year>/ only')
    ap.add_argument('--uploaded', metavar='VIDEO_ID', help="record the Short's upload (uploaded.json, history.json, the TikTok and Meta copies)")
    ap.add_argument('--publish-at', help='with --uploaded: when it goes public, RFC 3339 UTC')
    o = ap.parse_args()
    film_path = Path(o.film).resolve(); film = json.loads(film_path.read_text())
    short = film_path.parent / 'short'; short.mkdir(exist_ok=True)
    work = STUDIO / 'Renders/flyovers/shorts' / film['slug']
    if o.uploaded: return record_upload(film, short, o.uploaded, o.publish_at)
    ed = None
    if o.week:
        ed = editions.edition(film['slug'], dt.date.fromisoformat(o.week))
        if not ed: sys.exit(f"{film['slug']}: the catalogue has no edition of its race the week of {o.week}")
        ed['post_date'] = o.week
    elif o.edition:
        ed = dict(year=o.edition, race_date=o.race_date, page=o.page, post_date=o.post_date)
    if not ed:      # no edition named: one Short, as before
        p = stage_pick(film, short, o.seconds)
        if o.social_only: stage_dress(film, p, short, work, o.video_id, social_only=True); return 0
        if o.stage in ('render', 'all'): stage_render(film, p, work)
        if o.stage in ('dress', 'all'): stage_dress(film, p, short, work, o.video_id)
        return 0
    if not ed.get('page'):
        ed['page'] = editions.film_page(film['slug'])
        print(f"page: the {ed['year']} edition has no course page yet; linking the film's, {ed['page']}")
    year = ed['year']; h = editions.load_history(short); e = editions.entry(h, year)
    if e and e.get('video_id'):
        print(f"SKIP {film['slug']}: its {year} Short is already out or scheduled ({e['video_id']})"); return 0
    earlier = [x['dist_m'] for x in h['editions'] if x['year'] != year and x.get('dist_m')]
    if o.dry_run:
        dry = short / f'dry-{year}'; dry.mkdir(exist_ok=True)
        p = stage_pick(film, short, o.seconds, earlier, dry / 'pick.json')
        title, full = write_words(film, p, short, dry, o.video_id, cleared(film), ed)
        json.dump(dict(edition=ed, history=h, would_archive=h['current'] if h['current'] not in (None, year) else None),
                  open(dry / 'plan.json', 'w'), indent=1, ensure_ascii=False)
        print('DRY', dry); print('title:', title); print('window:', p['dist_m'], 'frames', p['frames'], 'overlap', p.get('overlap_m', 0), 'm')
        return 0
    if not e:
        if h['current'] not in (None, year) and (short / 'pick.json').exists():
            moved = editions.archive(short, work, h['current'])
            print(f"archived the {h['current']} Short: {len(moved)} files to {short / str(h['current'])} and {work / str(h['current'])}")
        e = dict(year=year); h['editions'].append(e)
    e.update(race_date=ed.get('race_date'), page=ed['page'], status='making'); h['current'] = year
    editions.save_history(short, h)
    p = stage_pick(film, short, o.seconds, earlier)
    e.update(frames=p['frames'], dist_m=p['dist_m'], place=(p.get('climb') or {}).get('place')); editions.save_history(short, h)
    if o.stage in ('render', 'all'): stage_render(film, p, work)
    if o.stage in ('dress', 'all'):
        stage_dress(film, p, short, work, o.video_id, ed=ed)
        e['status'] = 'made'; editions.save_history(short, h)
    return 0


if __name__ == '__main__':
    sys.exit(main())

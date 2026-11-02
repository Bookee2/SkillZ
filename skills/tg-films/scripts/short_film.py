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
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])
sys.path.insert(0, str(HERE))
import post_film  # noqa: E402  (helpers: ffmpeg, probe, course_page)

STUDIO = Path('/Volumes/KB SS/TrailGoat-Studio')
LOCK = STUDIO / 'Films/queue/.render.lock'
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


def stage_pick(film: dict, short: Path, secs: float) -> dict:
    pj = short / 'pick.json'
    if pj.exists():
        print('pick: keeping', pj); return json.loads(pj.read_text())
    out = subprocess.run([PY, REPO / 'scripts/flythrough/short.py', 'pick', film['out_dir'], '--shots', film['shots'],
                          '--seconds', str(secs), '--film', short.parent / 'film.json'], capture_output=True, text=True, check=True).stdout
    pj.write_text(out); p = json.loads(out)
    print('pick:', p['frames'], p['climb']); return p


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
            if r.returncode == 0: break
            tail = (work / 'render.log').read_text()[-4000:]
            if not re.search(r'URLError|Connection reset|timed out|RemoteDisconnected', tail):
                sys.exit(f'render failed: see {work}/render.log')
            print(f'render: network retry {attempt}'); time.sleep(60*attempt)
    finally:
        LOCK.rmdir()
    n = len(list((work / 'frames').glob('f_*.png')))
    if n < f1 - f0 + 1: sys.exit(f'render: {n} of {f1 - f0 + 1} frames')


def video_id(film: dict, page: str) -> str | None:
    """The long film's id on YouTube, from the films page's list (scripts/films_sync.py writes it)."""
    try:
        films = json.loads((REPO / 'app/films.json').read_text())
    except OSError:
        return None
    films = films if isinstance(films, list) else films.get('films', [])
    slug = page.rstrip('/').split('/')[-1]
    return next((f['id'] for f in films if f.get('course') == slug), None)


def figures(p: dict) -> tuple[str, str]:
    c = p['climb']; k = p['shown']
    if p['metric']:
        return f"{round(c['rise_m']):,} m", f"{(c['top_m'] - c['low_m'])*k/1000:.1f} km"
    return f"{round(c['rise_m']*FT):,} ft", f"{(c['top_m'] - c['low_m'])*k/MI:.1f} miles"


def the(race: str) -> str:
    return race if race.lower().startswith('the ') else f'the {race}'


def stage_dress(film: dict, p: dict, short: Path, work: Path, vid: str | None) -> None:
    slug = film['slug']; ff = post_film.ffmpeg()
    silent = work / f'{slug}-short-silent.mp4'
    sh(PY, REPO / 'scripts/flythrough/short.py', 'dress', work, '--pick', short / 'pick.json', '--film', short.parent / 'film.json', '--dst', silent)
    # the film's music at the same moment: master frame f plays at intro + (f-1)/fps in the long film, and the track
    # (from music.start) comes in at music_at, as post_film.py mixes it
    m = film.get('music') or {}
    out = short / f'{slug}-short.mp4'
    n = p['frames'][1] - p['frames'][0] + 1; dur = n/p['fps']
    if m.get('file'):
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
    else:
        sh(ff, '-y', '-loglevel', 'error', '-i', silent, '-c', 'copy', out)
    # title, description, meta
    long_meta = json.loads((short.parent / 'meta.json').read_text())
    long_desc = (short.parent / 'description.txt').read_text()
    page = re.search(r'https://trailgoat\.run/course/[a-z0-9-]+', long_desc)[0]
    vid = vid or video_id(film, page)
    race = p['race']; c = p.get('climb')
    if c:
        rise, run = figures(p)
        place = c.get('place')
        head = (f'{place} at {the(race)}' if place and place != 'The high point' else
                f'The high point of {the(race)}' if place else f'The biggest climb of {the(race)}')
        title = f'{head}: {rise} up in {run}, in 3D #Shorts'
        lede = f'{head}: {rise} of climbing in {run}, flown in 3D over the real terrain with the race readout.'
    else:
        span = subprocess.run([PY, '-c', 'import json, sys; sys.path.insert(0, sys.argv[1]); import short; print(short.miles(json.load(open(sys.argv[2]))))',
                               REPO / 'scripts/flythrough', short / 'pick.json'], capture_output=True, text=True, check=True).stdout.strip().lower()
        title = f'{race} in 3D: {span} #Shorts'
        lede = f'{race}, {span}, flown in 3D over the real terrain with the race readout.'
    if len(title) > 100: title = title.replace(', in 3D', '')
    blocks = long_desc.split('\n\n')
    music = next((b for b in blocks if b.startswith('Music:')), '')
    credits = [b for b in blocks if b.startswith(('Terrain:', 'Imagery:', 'Rendered', '©', 'Contains', 'Elevation'))]
    tags_line = next((b for b in reversed(blocks) if b.startswith('#')), '#TrailRunning #Ultramarathon')
    full = f'https://youtu.be/{vid}' if vid else 'https://www.youtube.com/@trailgoatrun'
    desc = '\n\n'.join(x for x in [
        lede,
        f'The whole course, every aid station, in the full film:\n▶ {full}',
        f'Plan this race free on TrailGoat:\n▶ {page}',
        music, *credits, f'#Shorts {tags_line.strip()}'] if x)
    (short / 'description.txt').write_text(desc + '\n')
    meta = dict(title=title, description=desc, tags=list(dict.fromkeys(long_meta.get('tags', []) + ['Shorts'])),
                privacy=film.get('privacy', 'public'), playlist='Race Shorts', related_video=vid)
    if film.get('short_publish_at'): meta['publish_at'] = film['short_publish_at']   # the Thursday of race week
    (short / 'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print('SHORT', out, f'{dur:.1f} s'); print('title:', title); print('full film:', full)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('film', help='the film.json the long film was dressed from')
    ap.add_argument('--seconds', type=float, default=40.0)
    ap.add_argument('--stage', choices=('pick', 'render', 'dress', 'all'), default='all')
    ap.add_argument('--video-id', help="the long film's YouTube id (default: app/films.json by its course link)")
    o = ap.parse_args()
    film_path = Path(o.film).resolve(); film = json.loads(film_path.read_text())
    short = film_path.parent / 'short'; short.mkdir(exist_ok=True)
    work = STUDIO / 'Renders/flyovers/shorts' / film['slug']
    p = stage_pick(film, short, o.seconds)
    if o.stage in ('render', 'all'): stage_render(film, p, work)
    if o.stage in ('dress', 'all'): stage_dress(film, p, short, work, o.video_id)
    return 0


if __name__ == '__main__':
    sys.exit(main())

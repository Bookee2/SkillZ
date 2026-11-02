#!/usr/bin/env python3
"""The Monday Short: the week's races, each a card with its facts over a few seconds of its flyover.

    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/week_short.py --week 2026-11-16 [--races a,b]

Kris, 2026-11-02: "lets also make a short every monday announcing the races for the week, the details (distance,
elevation, location, etc..) with very short previews of each race in the background."

The week's races are every film on the channel whose race runs that Monday to Sunday: the batch's race-week films
(queue/batch6_schedule.json) and any earlier film whose next edition falls in the week (its queue/<slug>/start), so a
week with no new film still gets its Short when an older one races. --races names them instead (a test). Per race,
from the long film's own files: the name, where it runs and its distance and climb (the description's first line,
so the Short says what the film says), the day and start (queue/<slug>/start, local time), the aid stations (the
verified pins), and the background: its Short's portrait frames from just before the climb's top, else the 1080p
master at its thumbnail moment, cropped to 9:16.

Writes Films/_race-week/<monday>/: spec.json, race-week-<monday>.mp4 (1080x1920, the series theme at -14 LUFS),
description.txt and meta.json (playlist "Race Week", publish_at the Monday at 07:00 New York, an hour after the
week's films, related_video the week's first film).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])
sys.path.insert(0, str(HERE))
import post_film  # noqa: E402

STUDIO = Path('/Volumes/KB SS/TrailGoat-Studio')
F, Q = STUDIO / 'Films', STUDIO / 'Films/queue'
SHORTS = STUDIO / 'Renders/flyovers/shorts'
NY = ZoneInfo('America/New_York')
# the series' theme: the same piece every Monday, so the Short is known by ear (Grieg's dawn for a Monday morning)
THEME = dict(file=str(STUDIO / 'Music/audio-library/Morning Mood (by Grieg) - Grieg.mp3'), title='Morning Mood', artist='Edvard Grieg',
             reason='The race-week theme: Monday morning.')
FIRST = re.compile(r'^(?P<name>.+?) from the start line to the finish: (?P<dist>[\d,.]+ (?:miles|km)) and (?P<gain>[\d,.]+ (?:ft|m)) of climbing '
                   r'over the real terrain of (?P<where>.+?), with every aid station')


def films_by_course() -> dict:
    try:
        films = json.loads((REPO / 'app/films.json').read_text())
    except OSError:
        return {}
    films = films if isinstance(films, list) else films.get('films', [])
    return {f['course']: f for f in films if f.get('course')}


def start_of(slug: str) -> dt.datetime | None:
    p = Q / slug / 'start'
    return dt.datetime.fromisoformat(p.read_text().strip()) if p.exists() else None


def week_races(monday: dt.date) -> list:
    """Slugs of the films whose race runs this week, in race order."""
    found = {}
    sched = Q / 'batch6_schedule.json'
    if sched.exists():
        for slug, v in json.loads(sched.read_text()).items():
            if not slug.startswith('_') and v['week'] == monday.isoformat(): found[slug] = True
    for p in Q.glob('*/start'):
        slug = p.parent.name; t = start_of(slug)
        if t and monday <= t.date() <= monday + dt.timedelta(days=6) and (F / slug / 'description.txt').exists(): found[slug] = True
    return sorted(found, key=lambda s: start_of(s) or dt.datetime.max)


def race(slug: str, films: dict) -> dict:
    film = json.loads((F / slug / 'film.json').read_text())
    desc = (F / slug / 'description.txt').read_text()
    m = FIRST.match(desc.split('\n')[0])
    if not m: sys.exit(f'{slug}: the description has no "from the start line…" first line')
    page = re.search(r'https://trailgoat\.run/course/([a-z0-9-]+)', desc)
    shots = json.loads(Path(film['shots']).read_text()) if film.get('shots') else {}
    t = start_of(slug)
    unit_d = m['dist'].split()[1]
    dist = m['dist'].replace('miles', 'MI').replace('km', 'KM').split()
    gain = m['gain'].split()
    name = m['name']
    return dict(slug=slug, name=name, short=re.sub(r'\s+by UTMB\b|,.*$', '', name).upper(),
                day=t.strftime('%a %-d').upper() if t else '', where=m['where'],
                when=(f"{t.strftime('%A %-d %B')} · start {t.strftime('%H:%M')}" if unit_d == 'km' else
                      f"{t.strftime('%A %-d %B')} · start {t.strftime('%-I:%M %p')}") if t else '',
                stats=[['DISTANCE', dist[0], dist[1], 'mile'], ['CLIMB', gain[0], gain[1].upper(), 'gain'],
                       ['AID STATIONS', str(len(shots.get('aids', []))), '', 'aid']],
                film=films.get(page[1], {}).get('id') if page else None, page=f'https://trailgoat.run/course/{page[1]}' if page else '',
                master=film.get('master'), thumb_at=film.get('thumb_at'))


def background(r: dict, need: int, work: Path) -> list:
    """`need` portrait frames for the race's card: its Short's own frames from 4 s before the climb's top, else the
    master cropped to 9:16 around its thumbnail moment."""
    sf = SHORTS / r['slug'] / 'frames'; pick = F / r['slug'] / 'short' / 'pick.json'
    if sf.exists() and pick.exists():
        p = json.loads(pick.read_text()); frames = sorted(sf.glob('f_*.png'))
        if len(frames) >= need:
            top = (p.get('climb') or {}).get('frame_top') or len(frames)//2
            a = max(0, min(len(frames) - need, top - 4*24))
            return [str(x) for x in frames[a:a + need]]
    ff = post_film.ffmpeg(); out = work / f"bg-{r['slug']}"; out.mkdir(parents=True, exist_ok=True)
    dur = post_film.probe(ff, r['master'])['seconds']; at = r['thumb_at'] if r['thumb_at'] is not None else dur*0.5
    at = max(0.0, min(at - 2, dur - need/24 - 0.5))
    subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', f'{at:.2f}', '-i', r['master'], '-frames:v', str(need),
                    '-vf', 'crop=ih*9/16:ih,scale=1080:1920:flags=lanczos', str(out / 'f_%04d.png')], check=True)
    return [str(x) for x in sorted(out.glob('f_*.png'))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--week', required=True, help='the Monday, YYYY-MM-DD')
    ap.add_argument('--races', help='comma-separated film slugs instead of the week\'s own (a test)')
    o = ap.parse_args()
    monday = dt.date.fromisoformat(o.week)
    slugs = o.races.split(',') if o.races else week_races(monday)
    if not slugs: print(f'week of {monday}: no filmed race; no Short'); return 0
    films = films_by_course(); races = [race(s, films) for s in slugs]
    out = F / '_race-week' / monday.isoformat(); out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO / 'scripts/flythrough')); import short   # noqa: E402
    for r, need in zip(races, short.week_frames(len(races))): r['frames'] = background(r, need, out / 'work')
    sun = monday + dt.timedelta(days=6)
    dates = (f'{monday.day}–{sun.day} {sun.strftime("%B")}' if monday.month == sun.month else
             f'{monday.day} {monday.strftime("%B")} – {sun.day} {sun.strftime("%B")}')
    spec = dict(label=f'RACE WEEK · {monday.day}–{sun.day} {sun.strftime("%b").upper()}' if monday.month == sun.month else
                f'RACE WEEK · {monday.day} {monday.strftime("%b").upper()}–{sun.day} {sun.strftime("%b").upper()}',
                title='Race week', dates=dates.upper(), sub=dates.upper(), outro='Every course in 3D', races=races)
    (out / 'spec.json').write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    silent = out / 'work' / 'silent.mp4'; (out / 'work').mkdir(exist_ok=True)
    subprocess.run([PY, REPO / 'scripts/flythrough/short.py', 'week', out / 'spec.json', '--dst', silent], check=True)
    ff = post_film.ffmpeg(); dur = post_film.probe(ff, str(silent))['seconds']
    mp4 = out / f'race-week-{monday.isoformat()}.mp4'
    af = (f'[1:a]atrim=start=0:end={dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={max(0, dur - 1.8):.2f}:d=1.8,'
          f'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad[a]')
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', silent, '-i', THEME['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', mp4], check=True)
    names = [r['name'] for r in races]
    joined = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    title = f'Race week, {dates}: {joined} in 3D #Shorts'
    if len(title) > 100: title = f"Race week, {dates}: {len(names)} races in 3D #Shorts"
    lines = [f"This week's races on the channel, {dates}. Every course flown in 3D, every aid station pinned.", '']
    for r in races:
        lines += [f"{r['name']} · {r['when']} · {r['where']}",
                  f"{' · '.join(f'{s[1]} {s[2]}'.strip() for s in r['stats'][:2])} · {r['stats'][2][1]} aid stations"]
        if r['film']: lines.append(f"▶ https://youtu.be/{r['film']}")
        if r['page']: lines.append(f"Plan it: {r['page']}")
        lines.append('')
    lines += [f'Music: "{THEME["title"]}" ({THEME["artist"]}). {THEME["reason"]}', '',
              'Terrain and imagery credits are in each race\'s full film.', '', '#Shorts #TrailRunning #Ultramarathon #RaceWeek']
    desc = '\n'.join(lines)
    (out / 'description.txt').write_text(desc + '\n')
    at = dt.datetime.combine(monday, dt.time(7, 0), NY).astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    meta = dict(title=title, description=desc, privacy='public', playlist='Race Week', publish_at=at,
                tags=['trail running', 'ultramarathon', 'race week', '3D course map', 'TrailGoat', 'Shorts'] + names[:6],
                related_video=next((r['film'] for r in races if r['film']), None))
    (out / 'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print('WEEK SHORT', mp4, f'{dur:.1f} s'); print('title:', title); print('public:', at)
    return 0


if __name__ == '__main__':
    sys.exit(main())

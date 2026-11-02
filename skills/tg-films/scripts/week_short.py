#!/usr/bin/env python3
"""This week in Trail Racing: the Monday Short with the week's races of 50K and up.

    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/week_short.py --week 2026-11-16 [--races a,b]

Kris, 2026-11-02: "lets also make a short every monday announcing the races for the week, the details (distance,
elevation, location, etc..) with very short previews of each race in the background", named "This week in Trail
Racing", every race of 50K and up in it ("I like your idea better": a card for each filmed race, then the rest as a
list), and "in the details of the short we need to list every race so that they all show up in search results".

Filmed races: every film on the channel whose race runs that Monday to Sunday, the batch's race-week films
(queue/batch6_schedule.json) and any earlier film whose next edition falls in the week (its queue/<slug>/start). Each
gets a card from the long film's own files: the name, where it runs and its distance and climb (the description's
first line, so the Short says what the film says), the day and start (queue/<slug>/start, local time), the aid
stations (the verified pins), over its Short's portrait frames from just before the climb's top, else a few seconds rendered
for the card the same way (render.py --portrait on the film's biggest-climbing stretch). --races names them instead (a test).

Everything else: every catalogue race of 50K and up that week (read-only from the catalogue), backyard and timed
events left out, one row per event with its day, place and distances, seven to a page.

Writes Films/_race-week/<monday>/: spec.json, this-week-<monday>.mp4 (1080x1920, the series theme at -14 LUFS),
description.txt (every race, so each one's name is in the search index) and meta.json (playlist "This week in Trail
Racing", publish_at the Monday at 07:00 New York, an hour after the week's films, related_video the week's first film).
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
             reason='The theme of This week in Trail Racing, for a Monday morning.')
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


def race(slug: str, films: dict, date: str | None = None) -> dict:
    film = json.loads((F / slug / 'film.json').read_text())
    desc = (F / slug / 'description.txt').read_text()
    m = FIRST.match(desc.split('\n')[0])
    if not m: sys.exit(f'{slug}: the description has no "from the start line…" first line')
    page = re.search(r'https://trailgoat\.run/course/([a-z0-9-]+)', desc)
    shots = json.loads(Path(film['shots']).read_text()) if film.get('shots') else {}
    t = start_of(slug); timed = bool(t)
    if date and (not t or t.date().isoformat() != date):   # this week's edition: the catalogue's date, and no start time,
        t = dt.datetime.fromisoformat(date); timed = False  # since the catalogue's 07:00 is often a default, not the gun
    unit_d = m['dist'].split()[1]
    dist = m['dist'].replace('miles', 'MI').replace('km', 'KM').split()
    gain = m['gain'].split()
    name = m['name']
    return dict(slug=slug, name=name, short=re.sub(r'\s+by UTMB\b|,.*$', '', name).upper(),
                day=t.strftime('%a %-d').upper() if t else '', where=m['where'],
                when=(t.strftime('%A %-d %B') if not timed else f"{t.strftime('%A %-d %B')} · start {t.strftime('%H:%M')}" if unit_d == 'km' else
                      f"{t.strftime('%A %-d %B')} · start {t.strftime('%-I:%M %p')}") if t else '',
                stats=[['DISTANCE', dist[0], dist[1], 'mile'], ['CLIMB', gain[0], gain[1].upper(), 'gain'],
                       ['AID STATIONS', str(len(shots.get('aids', []))), '', 'aid']],
                film=films.get(page[1], {}).get('id') if page else None, page=f'https://trailgoat.run/course/{page[1]}' if page else '',
                master=film.get('master'), thumb_at=film.get('thumb_at'))


def preview(r: dict, need: int) -> list:
    """`need` portrait frames rendered for the card: the film's own camera on its biggest-climbing stretch of that
    length (short.py pick), 9:16 like a Short (render.py --portrait), under the studio's render lock. For a film with
    no Short yet: a crop of the 16:9 master blows its map labels up 1.8x, and the films rendered before 2026-10-28
    carry no label boxes to dodge them with (Grand Ridge's "1,194 FT" filled the card, 2026-11-02)."""
    import time
    film = json.loads((F / r['slug'] / 'film.json').read_text())
    pick = json.loads(subprocess.run([PY, REPO / 'scripts/flythrough/short.py', 'pick', film['out_dir'], '--shots', film['shots'],
                                      '--seconds', f'{need/24 + 0.1:.2f}', '--film', F / r['slug'] / 'film.json'],
                                     capture_output=True, text=True, check=True).stdout)
    f0, f1 = pick['frames']; out = SHORTS / r['slug'] / f'preview-{f0}-{f1}'; out.mkdir(parents=True, exist_ok=True)
    have = sorted((out / 'frames').glob('f_*.png')) if (out / 'frames').exists() else []
    if len(have) < f1 - f0 + 1:
        shots = re.sub(r'-hud\.json$', '.json', film['shots']); shots = shots if os.path.exists(shots) else film['shots']
        course = next(Path(film['out_dir']).glob('course-*.json'))
        lock = Q / '.render.lock'
        while True:
            if subprocess.run(['pgrep', '-f', 'Blender.*-b'], capture_output=True).returncode != 0:
                try: lock.mkdir(); break
                except FileExistsError: pass
            time.sleep(20)
        try:
            for attempt in range(1, 5):
                with open(out / 'render.log', 'a') as log:
                    rc = subprocess.run([os.environ.get('BLENDER_BIN', '/Applications/Blender.app/Contents/MacOS/Blender'), '-b', '-P',
                                         REPO / 'scripts/flythrough/render.py', '--', course, out, '--shots', shots, '--res', '1080x1920',
                                         '--portrait', '0.5', '--samples', '32', '--frames', f'{f0}-{f1}'], stdout=log, stderr=subprocess.STDOUT).returncode
                # Blender exits 0 even when the script dies on a dropped tile fetch (Keweenaw, 2026-11-02): count the frames
                if len(list((out / 'frames').glob('f_*.png')) if (out / 'frames').exists() else []) >= f1 - f0 + 1: break
                if not re.search(r'URLError|Connection reset|timed out|RemoteDisconnected', (out / 'render.log').read_text()[-6000:]):
                    sys.exit(f"{r['slug']}: preview render failed (rc {rc}), see {out}/render.log")
                time.sleep(60*attempt)
        finally:
            lock.rmdir()
        have = sorted((out / 'frames').glob('f_*.png')) if (out / 'frames').exists() else []
        if len(have) < f1 - f0 + 1: sys.exit(f"{r['slug']}: preview has {len(have)} of {f1 - f0 + 1} frames, see {out}/render.log")
    print(f"preview {r['slug']}: frames {f0}-{f1}, {len(have)} rendered")
    return [str(x) for x in have]


def background(r: dict, need: int, work: Path) -> list:
    """`need` portrait frames for the race's card: its Short's own frames from 4 s before the climb's top, else a
    preview rendered for the card."""
    sf = SHORTS / r['slug'] / 'frames'; pick = F / r['slug'] / 'short' / 'pick.json'
    if sf.exists() and pick.exists():
        p = json.loads(pick.read_text()); frames = sorted(sf.glob('f_*.png'))
        if len(frames) >= need:
            top = (p.get('climb') or {}).get('frame_top') or len(frames)//2
            a = max(0, min(len(frames) - need, top - 4*24))
            return [str(x) for x in frames[a:a + need]]
    return preview(r, need)


US_STATES = dict(AL='Alabama', AK='Alaska', AZ='Arizona', AR='Arkansas', CA='California', CO='Colorado', CT='Connecticut', DE='Delaware',
                 FL='Florida', GA='Georgia', HI='Hawaii', ID='Idaho', IL='Illinois', IN='Indiana', IA='Iowa', KS='Kansas', KY='Kentucky',
                 LA='Louisiana', ME='Maine', MD='Maryland', MA='Massachusetts', MI='Michigan', MN='Minnesota', MS='Mississippi', MO='Missouri',
                 MT='Montana', NE='Nebraska', NV='Nevada', NH='New Hampshire', NJ='New Jersey', NM='New Mexico', NY='New York',
                 NC='North Carolina', ND='North Dakota', OH='Ohio', OK='Oklahoma', OR='Oregon', PA='Pennsylvania', RI='Rhode Island',
                 SC='South Carolina', SD='South Dakota', TN='Tennessee', TX='Texas', UT='Utah', VT='Vermont', VA='Virginia', WA='Washington',
                 WV='West Virginia', WI='Wisconsin', WY='Wyoming', DC='Washington DC', PR='Puerto Rico')
COUNTRIES = dict(US='USA', CA='Canada', MX='Mexico', GB='UK', IE='Ireland', FR='France', ES='Spain', PT='Portugal', IT='Italy', DE='Germany',
                 AT='Austria', CH='Switzerland', BE='Belgium', NL='Netherlands', LU='Luxembourg', DK='Denmark', NO='Norway', SE='Sweden',
                 FI='Finland', IS='Iceland', PL='Poland', CZ='Czechia', SK='Slovakia', SI='Slovenia', HR='Croatia', HU='Hungary', RO='Romania',
                 BG='Bulgaria', GR='Greece', TR='Türkiye', ZA='South Africa', MA='Morocco', KE='Kenya', AU='Australia', NZ='New Zealand',
                 JP='Japan', CN='China', HK='Hong Kong', TW='Taiwan', KR='South Korea', TH='Thailand', VN='Vietnam', PH='Philippines',
                 MY='Malaysia', ID='Indonesia', SG='Singapore', IN='India', NP='Nepal', BD='Bangladesh', AR='Argentina', CL='Chile',
                 BR='Brazil', PE='Peru', CO='Colombia', EC='Ecuador', CR='Costa Rica', NI='Nicaragua', OM='Oman', AE='UAE', IL='Israel',
                 VI='US Virgin Islands', AD='Andorra', RE='Réunion')
SKIP = re.compile(r'backyard|last (wo)?man|last person|\b\d+\s*(hr|hrs|hour|hours|h)\b|timed|relay|stage race|virtual', re.I)


def tidy(name: str) -> str:
    name = re.split(r'\s+\|\s+', name)[0].strip()
    name = re.sub(r'\s+[—–-]\s+(19|20)\d{2}$', '', name)
    if name.isupper() and len(name) > 6: name = ' '.join(w if len(w) <= 4 else w.capitalize() for w in name.split())
    return name


def dist_label(km: float, us: bool) -> str:
    for mi in (50, 100, 150, 200, 240, 250, 300):
        if us and abs(km - mi*1.609344) <= 0.04*mi*1.609344: return f'{mi}M'
    return f'{round(km)}K'


def week_rows(monday: dt.date) -> list:
    """Every catalogue edition that runs this week (read-only)."""
    sys.path.insert(0, str(REPO))
    from app.db import get_conn
    sun = monday + dt.timedelta(days=6)
    with get_conn() as c:
        return [dict(r) for r in c.execute(
            """SELECT ed.event_id, ed.race_date, ed.distance_label, ed.course_id, e.name, e.country, e.region, fc.distance_m
               FROM race_editions ed JOIN race_events e ON e.id = ed.event_id LEFT JOIN fuel_courses fc ON fc.id = ed.course_id
               WHERE ed.race_date >= ? AND ed.race_date <= ?""", (monday.isoformat(), sun.isoformat() + 'T23:59')).fetchall()]


def film_courses() -> dict:
    """slug: the catalogue course ids its long film was rendered from, for every film with a description."""
    out = {}
    for fj in F.glob('*/film.json'):
        if not (fj.parent / 'description.txt').exists(): continue
        od = json.loads(fj.read_text()).get('out_dir') or ''
        out[fj.parent.name] = {int(Path(p).stem.split('-')[1]) for p in glob.glob(f'{od}/course-[0-9]*.json')}
    return out


def filmed_this_week(rows: list) -> dict:
    """slug: (race date, event id) for each film whose race (any edition of its event) runs this week."""
    sys.path.insert(0, str(REPO))
    from app.db import get_conn
    fc = film_courses(); ids = sorted({c for v in fc.values() for c in v})
    with get_conn() as c:
        ev_of = {r['course_id']: r['event_id'] for r in c.execute(
            f"SELECT DISTINCT course_id, event_id FROM race_editions WHERE course_id IN ({','.join('?'*len(ids))})", ids).fetchall()} if ids else {}
    out = {}
    for slug, cids in fc.items():
        evs = {ev_of[x] for x in cids if x in ev_of}
        hits = sorted(r['race_date'][:10] for r in rows if r['event_id'] in evs)
        if hits: out[slug] = (hits[0], next(iter(evs & {r['event_id'] for r in rows})))
    # one film per event: two cuts of the same race (Grayson Highlands 50K and 50 mile) both stay, they're different races
    return out


def also_racing(rows: list, skip_events: set) -> list:
    """Every catalogue race of 50K and up that runs this week, one row per event, the filmed races' events left out."""
    sys.path.insert(0, str(REPO))
    from gpx_import import parse_distance_km
    ev = {}
    for r in rows:
        if r['event_id'] in skip_events or SKIP.search(f"{r['name']} {r['distance_label'] or ''}"): continue
        km = (r['distance_m'] or 0)/1000 or (parse_distance_km(r['distance_label'] or '', bare_miles=True) or 0)
        if km < 49.5: continue
        e = ev.setdefault(r['event_id'], dict(name=tidy(r['name']), country=r['country'] or '', region=r['region'] or '',
                                               date=r['race_date'][:10], kms=set()))
        e['date'] = min(e['date'], r['race_date'][:10]); e['kms'].add(round(km))
    out = []
    for e in sorted(ev.values(), key=lambda e: (e['date'], -max(e['kms']), e['name'])):
        us = e['country'] == 'US'; d = dt.date.fromisoformat(e['date'])
        where = (US_STATES.get(e['region'], e['region']) if us else COUNTRIES.get(e['country'], e['country'])) or COUNTRIES.get(e['country'], '')
        out.append(dict(day=d.strftime('%a %-d').upper(), name=e['name'], where=where + (', USA' if us and where else ''),
                        dists=' · '.join(dict.fromkeys(dist_label(k, us) for k in sorted(e['kms'])))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--week', required=True, help='the Monday, YYYY-MM-DD')
    ap.add_argument('--races', help='comma-separated film slugs instead of the week\'s own (a test)')
    o = ap.parse_args()
    monday = dt.date.fromisoformat(o.week)
    rows = week_rows(monday); found = filmed_this_week(rows)
    if o.races: slugs = o.races.split(',')
    else:
        slugs = sorted(set(week_races(monday)) | set(found), key=lambda s: (found.get(s, (None,))[0] or str(start_of(s) or ''), s))
        slugs = [s for s in slugs if (F / s / 'description.txt').exists()]
    if not slugs: print(f'week of {monday}: no filmed race; no Short'); return 0
    films = films_by_course(); races = [race(s, films, found.get(s, (None,))[0]) for s in slugs]
    out = F / '_race-week' / monday.isoformat(); out.mkdir(parents=True, exist_ok=True)
    also = also_racing(rows, {found[s][1] for s in slugs if s in found})
    sys.path.insert(0, str(REPO / 'scripts/flythrough')); import short   # noqa: E402
    for r, need in zip(races, short.week_frames(len(races))): r['frames'] = background(r, need, out / 'work')
    sun = monday + dt.timedelta(days=6)
    dates = (f'{monday.day}–{sun.day} {sun.strftime("%B")}' if monday.month == sun.month else
             f'{monday.day} {monday.strftime("%B")} – {sun.day} {sun.strftime("%B")}')
    spec = dict(dates=dates.upper(), sub=dates.upper(), outro='Every course in 3D', races=races, also=also)
    (out / 'spec.json').write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    silent = out / 'work' / 'silent.mp4'; (out / 'work').mkdir(exist_ok=True)
    subprocess.run([PY, REPO / 'scripts/flythrough/short.py', 'week', out / 'spec.json', '--dst', silent], check=True)
    ff = post_film.ffmpeg(); dur = post_film.probe(ff, str(silent))['seconds']
    mp4 = out / f'this-week-{monday.isoformat()}.mp4'
    af = (f'[1:a]atrim=start=0:end={dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={max(0, dur - 1.8):.2f}:d=1.8,'
          f'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad[a]')
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', silent, '-i', THEME['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', mp4], check=True)
    names = [r['name'] for r in races]
    lead = names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]
    more = f' and {len(also)} more' if also else ''
    title = f'This week in Trail Racing, {dates}: {lead}{more} #Shorts'
    if len(title) > 100: title = f'This week in Trail Racing, {dates}: {names[0]} and {len(names) - 1 + len(also)} more #Shorts'
    if len(title) > 100: title = f'This week in Trail Racing, {dates}: {len(names) + len(also)} races #Shorts'
    total = len(races) + len(also)
    lines = [f'This week in Trail Racing, {dates}: {total} trail races of 50K and up, the ones we\'ve flown in 3D first.', '']
    for r in races:
        lines += [f"{r['name']} · {r['when']} · {r['where']}",
                  f"{' · '.join(f'{s[1]} {s[2]}'.strip() for s in r['stats'][:2])} · {r['stats'][2][1]} aid stations"]
        if r['film']: lines.append(f"▶ Full 3D flyover: https://youtu.be/{r['film']}")
        if r['page']: lines.append(f"Plan it: {r['page']}")
        lines.append('')
    tail = ['Plan any of them free on TrailGoat: https://trailgoat.run', '',
            f'Music: "{THEME["title"]}" ({THEME["artist"]}). {THEME["reason"]}', '',
            'Terrain and imagery credits are in each race\'s full film.', '', '#Shorts #TrailRunning #Ultramarathon #ThisWeekInTrailRacing']
    rows = [f"{a['day'].title()} · {a['name']} · {a['where']} · {a['dists'].replace(' · ', ', ')}" for a in also]
    def compose(k):                           # YouTube's limit is 5,000 characters: the list loses its last rows first
        listed = (['Also racing this week:'] + rows[:k] + ([f'…and {len(rows) - k} more'] if k < len(rows) else []) + ['']) if rows else []
        return '\n'.join(lines + listed + tail)
    k = len(rows); desc = compose(k)
    while len(desc) > 4900 and k: k -= 1; desc = compose(k)
    (out / 'description.txt').write_text(desc + '\n')
    at = dt.datetime.combine(monday, dt.time(7, 0), NY).astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    tags = ['trail running', 'ultramarathon', 'trail race', 'this week in trail racing', '3D course map', 'TrailGoat', 'Shorts']
    for n_ in names + [a['name'] for a in also]:          # YouTube allows 500 characters of tags
        if n_ not in tags and sum(len(t) + 2 for t in tags) + len(n_) <= 480 and ',' not in n_: tags.append(n_)
    meta = dict(title=title, description=desc, privacy='public', playlist='This week in Trail Racing', publish_at=at, tags=tags,
                related_video=next((r['film'] for r in races if r['film']), None))
    (out / 'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print('WEEK SHORT', mp4, f'{dur:.1f} s', f'{len(races)} filmed + {len(also)} listed'); print('title:', title); print('public:', at); print('description', len(desc), 'chars')
    return 0


if __name__ == '__main__':
    sys.exit(main())

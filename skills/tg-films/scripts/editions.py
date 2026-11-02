"""A film's race, year after year: which edition of it runs a given week and that edition's course page, the history of
the film's Shorts (one per edition), and the year in a title.

Kris, 2026-11-02: "Yes, build the yearly race-week re-post: year in titles and captions, not in the video; fresh cut
each year; links to that year's course page." A film is made once; every race week after, its Short goes out again
as a fresh cut (short_film.py --week, clear of earlier years' windows) and the film's title and course link move to
that year (race_year.py). The picture never carries a year, so nothing is rendered again for a new edition.

Films/<slug>/short/history.json:
  {"current": 2027,                       the edition the files in short/ are for
   "editions": [{"year": 2026, "frames": [f0, f1], "dist_m": [d0, d1], "place": "Hope Pass", "page": "https://…",
                 "race_date": "2026-08-22", "video_id": "…", "publish_at": "…", "status": "made|uploaded"}, …]}
An earlier edition's files move to short/<year>/ (and its portrait video to Renders/flyovers/shorts/<slug>/<year>/)
when the next one is made, never deleted.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path

STUDIO = Path('/Volumes/KB SS/TrailGoat-Studio')
F = STUDIO / 'Films'
SHORTS = STUDIO / 'Renders/flyovers/shorts'
PAGE_RE = re.compile(r'https://trailgoat\.run/course/[a-z0-9-]+')
YEAR_DIR = re.compile(r'^(19|20)\d{2}$')
GENERIC = {'ultra', 'ultramarathon', 'marathon', 'endurance', 'miler', 'mile', 'miles', 'k', 'km', 'mi'}


# ---------- the edition that runs this week ----------
def edition(slug: str, monday: dt.date) -> dict | None:
    """This week's edition of the film's race, from the catalogue (read-only): {year, race_date, course_id, page,
    distance_label}, page None when the edition has no course yet. None when its race doesn't run this week."""
    import week_short as w
    import post_film
    rows = w.week_rows(monday)
    hit = w.filmed_this_week(rows).get(slug)
    if not hit: return None
    date, ev = hit
    mine = [r for r in rows if r['event_id'] == ev]
    courses = w.film_courses().get(slug, set())
    film_m = film_distance(slug)
    row = (next((r for r in mine if r['course_id'] in courses), None)
           or min((r for r in mine if r['distance_m'] and film_m and abs(r['distance_m'] - film_m) <= 0.1*film_m),
                  key=lambda r: abs(r['distance_m'] - film_m), default=None)
           or next((r for r in mine if r['course_id']), None))
    cid = row['course_id'] if row else None
    page = None
    if cid:
        try:
            page = post_film.SITE + post_film.course_page({'id': cid})   # checked live; exits when there's no page
        except SystemExit:
            page = None
    return dict(year=int(date[:4]), race_date=date, course_id=cid, page=page, distance_label=row['distance_label'] if row else None)


def film_distance(slug: str) -> float | None:
    try:
        od = json.loads((F / slug / 'film.json').read_text())['out_dir']
        rec = json.loads(next(Path(od).glob('course-*.json')).read_text())
        return float(rec.get('distance_m') or 0) or None
    except (OSError, StopIteration, KeyError, ValueError):
        return None


def film_page(slug: str) -> str | None:
    """The course page the long film's description links to now."""
    try:
        m = PAGE_RE.search((F / slug / 'description.txt').read_text())
    except OSError:
        return None
    return m[0] if m else None


# ---------- words ----------
def with_year(title: str, year: int) -> str:
    """'Leadville Trail 100 Run: the whole course…' -> 'Leadville Trail 100 Run 2027: the whole course…'; a year
    already there is replaced. Over YouTube's 100 characters, ' | TrailGoat' goes first."""
    head, sep, rest = title.partition(': ')
    if not sep: head, rest = title, ''
    head = re.sub(r'\s+(19|20)\d{2}$', '', head.rstrip())
    out = f'{head} {year}{sep}{rest}'
    return out if len(out) <= 100 else out.replace(' | TrailGoat', '')


def race_year(race: str, year: int | None) -> str:
    """'Leadville Trail 100 Run' and 2027 -> 'Leadville Trail 100 Run 2027' (a year already at the end is replaced)."""
    if not year: return race
    return f"{re.sub(r'\s+(19|20)\d{2}$', '', race)} {year}"


def short_name(race: str) -> str:
    """What runners call it in a sentence: 'Leadville Trail 100 Run' -> 'Leadville', 'Kessel Run Ultra 50 Miler' ->
    'Kessel Run', 'Western States 100' -> 'Western States', 'The Bear 100' -> 'Bear 100' (film.json's short_name
    overrides it)."""
    if race.startswith('The '): return race[4:]        # "Plan your Bear 100 free", not "your The Bear"
    words = re.sub(r'\s+by UTMB\b', '', race).split()
    cut_number = False
    while len(words) > 1:
        w = words[-1].lower()
        if re.fullmatch(r'\d+(k|km|m|mi)?', w) or w in GENERIC:
            cut_number |= bool(re.match(r'\d', w)); words.pop()
        elif w in ('run', 'race') and re.match(r'\d', words[-2]):
            words.pop()
        elif w == 'trail' and cut_number:
            words.pop()
        else:
            break
    return ' '.join(words)


def swap_page(text: str, page: str) -> str:
    """The first course link in a description, pointed at `page`."""
    return PAGE_RE.sub(page, text, count=1)


# ---------- the film's Shorts, one per edition ----------
def load_history(short: Path) -> dict:
    """history.json, made from the files already there the first time: the Short in short/ becomes its first edition,
    the year it went (or goes) out: uploaded.json's publish_at, else meta.json's, else when pick.json was made."""
    p = short / 'history.json'
    if p.exists(): return json.loads(p.read_text())
    h = dict(current=None, editions=[])
    pj = short / 'pick.json'
    if not pj.exists(): return h
    pick = json.loads(pj.read_text())
    up = json.loads((short / 'uploaded.json').read_text()) if (short / 'uploaded.json').exists() else {}
    meta = json.loads((short / 'meta.json').read_text()) if (short / 'meta.json').exists() else {}
    when = up.get('publish_at') or meta.get('publish_at')
    year = int(when[:4]) if when else dt.datetime.fromtimestamp(pj.stat().st_mtime).year
    desc = (short / 'description.txt').read_text() if (short / 'description.txt').exists() else ''
    pages = PAGE_RE.findall(desc)
    h['editions'].append(dict(year=year, frames=pick['frames'], dist_m=pick['dist_m'], place=(pick.get('climb') or {}).get('place'),
                              page=pages[-1] if pages else None, video_id=up.get('id'), publish_at=when,
                              status='uploaded' if up.get('id') else 'made', migrated=True))
    h['current'] = year
    return h


def save_history(short: Path, h: dict) -> None:
    h['editions'].sort(key=lambda e: e['year'])
    (short / 'history.json').write_text(json.dumps(h, indent=1, ensure_ascii=False) + '\n')


def entry(h: dict, year: int) -> dict | None:
    return next((e for e in h['editions'] if e['year'] == year), None)


def archive(short: Path, work: Path, year: int) -> list:
    """Move edition `year`'s Short out of the way of the next one: short/* into short/<year>/, the portrait video and
    any frames into the render folder's <year>/. history.json, other years' folders, dry runs and the weekly Short's
    card previews stay put. Returns what moved."""
    moved = []
    for root, keep in ((short, {'history.json'}), (work, set())):
        if not root.exists(): continue
        dst = root / str(year)
        for p in sorted(root.iterdir()):
            if p.name in keep or YEAR_DIR.match(p.name) or p.name.startswith(('dry-', 'preview-')): continue
            dst.mkdir(exist_ok=True)
            shutil.move(str(p), str(dst / p.name)); moved.append(str(dst / p.name))
    return moved

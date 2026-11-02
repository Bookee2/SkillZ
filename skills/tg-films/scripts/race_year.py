#!/usr/bin/env python3
"""The long film in its race week: the edition's year in its title and its course link on that edition's page.

    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/race_year.py --week 2027-08-16           # the plan
    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/race_year.py --week 2027-08-16 --apply   # do it
    … race_year.py --slug leadville-100 --edition 2027 [--page https://trailgoat.run/course/…]                    # one film

Kris, 2026-11-02: "Yes, build the yearly race-week re-post: year in titles and captions, not in the video; fresh cut
each year; links to that year's course page." A film is made once and found again every race week, so on the Monday
of each one (the race-week task) its title carries that year, "Leadville Trail 100 Run 2027: the whole course in 3D,
every aid station | TrailGoat" (100 characters at most), and the description's first trailgoat.run/course link points
at that edition's course page. Nothing else changes: the tags, category and languages go back as they came. An
edition with no course page in the catalogue yet keeps the old link, and says so.

The films are those whose race runs that week: the catalogue's editions (editions.py) and the batch's race-week films.
Without --apply it only reads YouTube. --apply writes with videos.update (yt_video.py, in the YouTube venv), reads it
back, logs the old and new title and page to Films/<slug>/title_history.json, and makes the film's own
description.txt and meta.json match, so films_sync.py and the Shorts find the film by its new link.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])
sys.path.insert(0, str(HERE))
import editions  # noqa: E402

YTPY = os.environ.get('TG_YT_PY', str(Path.home() / '.config/trailgoat-youtube/venv/bin/python'))


class Unreachable(Exception):
    pass


def yt(*args) -> dict:
    out = subprocess.run([YTPY, HERE / 'yt_video.py', *args], capture_output=True, text=True)
    if out.returncode and not out.stdout.strip():
        raise Unreachable(out.stderr.strip().splitlines()[-1][-300:] if out.stderr.strip() else f'exit {out.returncode}')
    return json.loads(out.stdout)


def local(slug: str) -> dict:
    """The film's own meta.json as a snippet, for a plan when YouTube can't be read (an expired sign-in)."""
    meta = json.loads((editions.F / slug / 'meta.json').read_text())
    return dict(snippet=dict(title=meta['title'], description=meta['description'], tags=meta.get('tags', [])),
                status=dict(privacyStatus='unknown: from meta.json'))


def film_id(slug: str) -> str | None:
    """The long film's id: app/films.json by its course link, else the batch schedule's (a film that went public this
    morning isn't on the films page yet), else the last title_history.json entry."""
    page = editions.film_page(slug)
    try:
        films = json.loads((REPO / 'app/films.json').read_text())
    except OSError:
        films = []
    films = films if isinstance(films, list) else films.get('films', [])
    got = next((f['id'] for f in films if page and f.get('course') == page.rsplit('/', 1)[-1]), None)
    sched = editions.F / 'queue/batch6_schedule.json'
    if not got and sched.exists():
        got = (json.loads(sched.read_text()).get(slug) or {}).get('video_id')
    th = editions.F / slug / 'title_history.json'
    if not got and th.exists():
        got = next((x.get('video_id') for x in reversed(json.loads(th.read_text())) if x.get('video_id')), None)
    return got


def this_weeks(monday: dt.date) -> list:
    import week_short as w
    rows = w.week_rows(monday)
    found = set(w.filmed_this_week(rows)) | set(w.week_races(monday))
    return sorted(s for s in found if (editions.F / s / 'description.txt').exists())


def plan(slug: str, ed: dict, offline_ok: bool = False) -> dict:
    vid = film_id(slug)
    if not vid: return dict(slug=slug, skip='no YouTube id (not in app/films.json yet)')
    try:
        live = yt('get', vid)
    except Unreachable as e:
        if not offline_ok: sys.exit(f'{slug}: YouTube unreachable ({e}); nothing changed. An expired sign-in needs '
                                    '`yt_upload.py auth` in the YouTube venv, by Kris')
        print(f'  (YouTube unreachable: {e}. Planning from the local meta.json)'); live = local(slug)
    sn = live['snippet']
    title = editions.with_year(sn['title'], ed['year'])
    page = ed.get('page'); old_page = (editions.PAGE_RE.search(sn['description']) or [None])[0]
    desc = editions.swap_page(sn['description'], page) if page and old_page else sn['description']
    note = None if page else f"the {ed['year']} edition has no course page in the catalogue yet: link kept"
    if len(title) > 100: return dict(slug=slug, vid=vid, skip=f'title would be {len(title)} characters: {title}')
    return dict(slug=slug, vid=vid, year=ed['year'], privacy=live['status'].get('privacyStatus'), old_title=sn['title'],
                title=title, old_page=old_page, page=page if page and old_page else old_page, note=note,
                change=title != sn['title'] or desc != sn['description'], snippet={**sn, 'title': title, 'description': desc})


def apply(p: dict) -> None:
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(p['snippet'], f, ensure_ascii=False); path = f.name
    try:
        back = yt('set', p['vid'], path)
    finally:
        os.unlink(path)
    if not back.get('ok'): sys.exit(f"{p['slug']}: YouTube reads back {back.get('title')!r}, not what was sent")
    d = editions.F / p['slug']
    th = d / 'title_history.json'; hist = json.loads(th.read_text()) if th.exists() else []
    hist.append(dict(date=dt.date.today().isoformat(), year=p['year'], video_id=p['vid'], old_title=p['old_title'], title=p['title'],
                     old_page=p['old_page'], page=p['page']))
    th.write_text(json.dumps(hist, indent=1, ensure_ascii=False) + '\n')
    if p['page'] and p['page'] != p['old_page']:      # the film's own files follow, so its link finds it again
        (d / 'description.txt').write_text(editions.swap_page((d / 'description.txt').read_text(), p['page']))
    mp = d / 'meta.json'
    if mp.exists():
        meta = json.loads(mp.read_text()); meta['title'] = p['title']
        if p['page']: meta['description'] = editions.swap_page(meta.get('description', ''), p['page'])
        mp.write_text(json.dumps(meta, indent=1, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--week', help="the race week's Monday, YYYY-MM-DD")
    ap.add_argument('--slug', help='one film (its Films/ folder name) instead of the whole week')
    ap.add_argument('--edition', type=int, help='with --slug: the edition year, instead of looking it up for --week')
    ap.add_argument('--page', help="with --edition: that edition's course page")
    ap.add_argument('--apply', action='store_true', help='write the changes to YouTube (default: only show them)')
    o = ap.parse_args()
    if not (o.week or (o.slug and o.edition)): ap.error('give --week, or --slug with --edition')
    monday = dt.date.fromisoformat(o.week) if o.week else None
    slugs = [o.slug] if o.slug else this_weeks(monday)
    if not slugs: print('no filmed race this week'); return 0
    done = 0
    for slug in slugs:
        ed = dict(year=o.edition, page=o.page) if o.edition else editions.edition(slug, monday)
        if not ed:
            print(f'{slug}: SKIP, no edition of its race in the catalogue the week of {o.week}'); continue
        p = plan(slug, ed, offline_ok=not o.apply)
        if p.get('skip'): print(f"{slug}: SKIP, {p['skip']}"); continue
        print(f"{slug} ({p['vid']}, {p['privacy']}) {p['year']}:")
        print(f"  title  {p['old_title']}\n      -> {p['title']}" if p['title'] != p['old_title'] else f"  title  already {p['title']}")
        print(f"  link   {p['old_page']}\n      -> {p['page']}" if p['page'] != p['old_page'] else f"  link   already {p['old_page']}")
        if p['note']: print(f"  note   {p['note']}")
        if not p['change']: print('  nothing to change'); continue
        if o.apply:
            apply(p); done += 1; print('  UPDATED on YouTube; title_history.json, description.txt and meta.json follow')
        else:
            print('  (plan only: --apply writes it)')
    if o.apply: print(f'{done} film(s) updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())

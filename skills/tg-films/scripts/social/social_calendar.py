#!/usr/bin/env python3
"""The TrailGoat social calendar: what goes to Instagram and Facebook each day, made and queued for the poster task.

Kris, 2026-11-02: "Yes, I love these ideas let's build an automated calendar to post this" (the formats report,
https://claude.ai/artifact/EpcfE1xhpxqAEtUKq8mHyV). One post a day (two on Mondays); the poster task posts due queue
items at 12:00 and 18:00 New York, one per run, so a busy day spills into the next free slot instead of piling up.

Kris, 2026-11-03: "we need to post with purpose and intent on what's actually happening". So every post rides a moment
from moments.py: a race this week, results from last weekend, or a lottery or registration date that's confirmed.
A day with no moment posts nothing; there's no filler.

    any  a lottery or registration moment (confirmed): lottery opens, draw or registration opens on the day, lottery
         closes two days ahead (12:00, at most two a day; none for a race already queued that day)
    any  story carousel for each race whose "How it was won" goes public that day (18:00; the Reels at 12:00/18:00)
    Tue  race-week card for each race racing this week (12:00, then the next free slots)
    Wed  guess the race: one of this week's or next week's races (12:00)
    Thu  each of this week's races' Short, its social cut (12:00, then the next slots)
    Fri  race-day forecast for this week's first race (12:00)
    Sat  nothing new: the poster drains anything left over
    Sun  first Sunday of the month: comment your race; otherwise "where would you be" for a race whose results came
         out in the last two weeks. (The rankings had no moment, so they no longer go out on their own.)

    python3 social_calendar.py plan [--date YYYY-MM-DD]     # what today holds, nothing made
    python3 social_calendar.py build [--date YYYY-MM-DD]    # make today's posts (carousel.py), print their folders
    python3 social_calendar.py queue [--date YYYY-MM-DD]    # queue today's made posts at their times (after you've looked)

Run with the weekly-shorts venv. State (formats used so far) is in calendar-state.json beside this file.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carousel as C   # noqa: E402
import moments as Mo   # noqa: E402

NY = ZoneInfo('America/New_York')
FILMS = C.FILMS


def at(day: dt.date, hhmm: str) -> str:
    h, m = map(int, hhmm.split(':'))
    return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=NY).isoformat()


def slots(day: dt.date, first: str = '12:00'):
    """12:00 and 18:00 from `first` on, day after day"""
    d, t = day, first
    while True:
        yield at(d, t)
        if t == '12:00': t = '18:00'
        else: d, t = d + dt.timedelta(days=1), '12:00'


def week_spec(monday: dt.date):
    p = f'{FILMS}/_race-week/{monday.isoformat()}/spec.json'
    try: return C.load(p)
    except OSError: return None


def queued_ids():
    try: return {it['id'] for it in json.load(open(f'{HERE}/queue.json'))}
    except OSError: return set()


def recent_won(day: dt.date, days: int = 8):
    """(slug, year) of every "How it was won" (built with won.py: src/race.json + cfg.json) that went public in the
    last `days` days, today included"""
    out = []
    for p in glob.glob(f'{FILMS}/*/won-*/uploaded.json'):
        slug, year = p.split('/')[-3], int(p.split('/')[-2].split('-')[1])
        base = os.path.dirname(p)
        if not (os.path.exists(f'{base}/src/race.json') and os.path.exists(f'{base}/cfg.json')): continue
        u = C.load(p); when = (u.get('publish_at') or u.get('uploaded') or '')[:10]
        try: d = dt.date.fromisoformat(when)
        except ValueError: d = dt.date.fromtimestamp(os.path.getmtime(p))
        if 0 <= (day - d).days <= days: out.append((slug, year))
    return sorted(out)


def raced_within(won, day: dt.date, days: int) -> bool:
    """the race behind a "How it was won" (slug, year) started within `days` days before `day` (its splits' gun time)"""
    try: gun = dt.date.fromisoformat(C.load(f'{FILMS}/{won[0]}/won-{won[1]}/src/race.json')['gun'][:10])
    except (OSError, KeyError, ValueError): return False
    return 0 <= (day - gun).days <= days


def plan(day: dt.date):
    """[(post id, kind, maker args, first slot)] for the day"""
    wd = day.weekday(); monday = day - dt.timedelta(days=wd); spec = week_spec(monday)
    def filmed(sl): return os.path.exists(f"{FILMS}/{sl}/film.json")
    # this week's races: the race-week spec's featured ones first, then any other filmed race moments.json has racing this week
    races = [sl for sl in dict.fromkeys([r['slug'] for r in (spec or {}).get('races', [])] + Mo.race_week(day)) if filmed(sl)]
    st = C.state(); out = []
    # any day: a confirmed lottery or registration moment. A race already queued that day (a "How it was won" held for
    # its lottery draw, say) needs no second post.
    try: busy = {it['id'] for it in json.load(open(f'{HERE}/queue.json')) if it['at'][:10] == day.isoformat()}
    except OSError: busy = set()
    pri = {'lottery_draw': 0, 'lottery_open': 1, 'lottery_close': 2, 'registration_open': 3}
    ms = Mo.on(day, ('lottery_draw', 'lottery_open', 'registration_open'), True) + Mo.on(day + dt.timedelta(days=2), ('lottery_close',), True)
    ms = [x for x in sorted(ms, key=lambda x: pri[x['kind']]) if filmed(x['slug']) and not any(x['slug'] in b for b in busy)]
    for x in ms[:max(0, 2 - len(busy))]:          # two posts a day in all, counting what's already queued for today
        out.append((f"entry-{x['slug']}-{x['kind']}-{x['date']}", 'entry', ('entry', x['slug'], x['kind']), '12:00'))
    # any day: the story carousel for a "How it was won" that goes public today (the Monday after a race), after the Reel.
    # It replaced the results carousel (a dashboard of tables) on 2026-11-02, after the @hardcoreharrys backyard-record
    # post Kris pointed at: one beat per slide, huge type, the place each beat happened.
    for slug, year in recent_won(day, 0):
        if f'{slug}-{year}' not in st.get('results_skip', []):
            out.append((f'story-{slug}-{year}', 'story', ('story', slug, year), '18:00'))
    if wd == 1:
        # the two longest races of the week get a card (four cards in a day buried everything else)
        big = sorted(races, key=lambda sl: -next((f['mi'] for f in C.films() if f['slug'] == sl), 0))   # build stops at two
        for slug in big: out.append((f'raceweek-{slug}-{monday}', 'raceweek', ('raceweek', slug, monday.isoformat()), '12:00'))
    elif wd == 2:
        # a race people are about to run: this week's, else next week's, that hasn't been a guess yet
        soon = races + [sl for sl in Mo.race_week(day + dt.timedelta(days=7)) if filmed(sl)]
        pick = next((sl for sl in soon if sl not in st.get('guess_used', [])), None)
        if pick: out.append((f'guess-{pick}', 'guess', ('guess', pick), '12:00'))
    elif wd == 3:
        for slug in races:
            sh = glob.glob(f'{FILMS}/{slug}/short/*-short-social.mp4')
            if sh and os.path.isdir(f'{FILMS}/{slug}/short/captions') and f'{slug}-{day.year}' not in st.get('meta_shorts', []):
                out.append((f'short-{slug}-{day.year}', 'race-short', ('short', slug), '12:00'))
    elif wd == 4:
        if races: out.append((f'forecast-{races[0]}-{monday}', 'forecast', ('forecast', races[0], monday.isoformat()), '12:00'))
    elif wd == 6:
        if day.day <= 7: out.append((f"requests-{day.strftime('%Y-%m')}", 'requests', ('requests',), '12:00'))
        else:
            # a race actually run in the last three weeks: a June race's video going public late is not a moment
            fresh = [w for w in recent_won(day, 14) if f'{w[0]}-{w[1]}' not in st.get('where_used', []) and raced_within(w, day, 21)]
            if fresh: out.append((f'where-{fresh[0][0]}-{fresh[0][1]}', 'where', ('where', *fresh[0]), '12:00'))
    q = queued_ids()
    try:                                   # made earlier today already: a second build adds nothing
        t = json.load(open(f'{HERE}/calendar-today.json'))
        done = {m['kind'] + ':' + m.get('key', '') for m in t['made']} if t['day'] == day.isoformat() else set()
    except OSError:
        done = set()
    return [p for p in out if p[0] not in q and f"{p[1]}:{p[0]}" not in done]


def build(day: dt.date):
    made = []
    for pid, kind, args, first in plan(day):
        cmd = args[0]
        if kind == 'raceweek' and sum(m['kind'] == 'raceweek' for m in made) >= 2: continue
        try:
            if cmd == 'short':
                slug = args[1]; mp4 = sorted(glob.glob(f'{FILMS}/{slug}/short/*-short-social.mp4'))[0]
                d = mp4                                              # a video: queued as it is
            else:
                d = getattr(C, cmd)(*args[1:])
                if cmd == 'where':
                    st = C.state(); st.setdefault('where_used', []).append(f'{args[1]}-{args[2]}'); C.save_state(st)
            made.append(dict(id=os.path.basename(d.rstrip('/')) if cmd not in ('short',) else pid, kind=kind, key=pid, path=d, first=first))
        except Exception as e:                                       # one format failing never stops the day
            print('FAILED', pid, repr(e)[:300])
    try:
        t = json.load(open(f'{HERE}/calendar-today.json'))
        if t['day'] == day.isoformat(): made = t['made'] + made
    except OSError:
        pass
    json.dump(dict(day=day.isoformat(), made=made), open(f'{HERE}/calendar-today.json', 'w'), indent=1)
    for m in made: print('MADE', m['kind'], m['path'])
    if not made: print('Nothing to make today')
    return made


def queue(day: dt.date):
    try: today = json.load(open(f'{HERE}/calendar-today.json'))
    except OSError: sys.exit('run build first')
    if today['day'] != day.isoformat(): sys.exit(f"calendar-today.json is for {today['day']}: run build for {day}")
    taken = set()
    try: taken = {it['at'] for it in json.load(open(f'{HERE}/queue.json')) if not all(it['posted'].get(w) for w in (('ig', 'fb', 'yt') if it.get('images') else ('ig', 'fb')))}
    except OSError: pass
    q = queued_ids()
    for m in today['made']:
        if m['id'] in q: continue
        caps = os.path.join(os.path.dirname(m['path']), 'captions') if m['kind'] == 'race-short' else os.path.join(m['path'], 'captions')
        when = next(s for s in slots(day, m['first']) if s not in taken); taken.add(when)
        subprocess.run([sys.executable, f'{HERE}/queue.py', 'add', m['id'], when, m['path'], caps, '--kind', m['kind'],
                        '--title', m['id']], check=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    day = dt.date.fromisoformat(a[a.index('--date') + 1]) if '--date' in a else dt.datetime.now(NY).date()
    cmd = a[0] if a else 'plan'
    if cmd == 'plan':
        for p in plan(day): print(p[1], p[0], 'from', p[3])
        if not plan(day): print('Nothing today')
    elif cmd == 'build': build(day)
    elif cmd == 'queue': queue(day)
    else: sys.exit(__doc__)

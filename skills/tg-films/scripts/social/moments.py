#!/usr/bin/env python3
"""Race moments: the dated things runners are talking about. Every social post rides one.

Kris, 2026-11-03: "I guess one of the lessons is that we need to post with purpose and intent on what's actually
happening", then "Yes, build the race-moments list (race weeks, results Mondays, lottery and registration dates) and
make the daily social calendar post from it."

moments.json beside this file holds, per race slug:
  - the next edition's race date and last day, with date_status and date_source;
  - how runners get in (entry);
  - the entry moments: lottery_open, lottery_close, lottery_draw, registration_open, registration_close, sold_out.
    Each has a date, a status (confirmed: an official page says so for this edition; pattern: inferred from the
    last cycle), a source, and a short quote.
A race can also carry `watch` (and `watch_from`): a big moment that's coming but not announced yet, such as the UTMB
Mont-Blanc lottery. `check` lists it from that date until the dates are recorded and `watch` is removed.
Race weeks, race days and results Mondays are worked out from the race date, never stored. Only confirmed moments
go into a post: a pattern moment is a reminder to confirm it, not a fact.

    python3 moments.py on [YYYY-MM-DD]          # that day's moments (today if no date)
    python3 moments.py week [YYYY-MM-DD]        # the Monday-Sunday week holding that date
    python3 moments.py upcoming [days]          # the next N days (30 if not given)
    python3 moments.py check [YYYY-MM-DD]       # what needs a look: pattern moments within 21 days, past race dates, no source
    python3 moments.py set <slug> <kind> <YYYY-MM-DD> <confirmed|pattern> <source> [quote]   # add or replace one entry moment
    python3 moments.py drop <slug> <kind>       # remove an entry moment (it isn't happening, or was wrong)
    python3 moments.py race <slug> <YYYY-MM-DD> [last day] <confirmed|pattern> <source>      # the next edition's dates
    python3 moments.py merge <research.json>... # fold research files in: confirmed beats pattern, a newer edition beats an older one
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = f'{HERE}/moments.json'
ENTRY = ('lottery_open', 'lottery_close', 'lottery_draw', 'registration_open', 'registration_close', 'sold_out')
DERIVED = ('race_week', 'race_day', 'results_monday')


def load():
    try:
        with open(PATH) as f: return json.load(f)
    except OSError:
        return {'races': {}}


def save(m):
    m['updated'] = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    m['races'] = dict(sorted(m['races'].items()))
    tmp = PATH + '.tmp'
    with open(tmp, 'w') as f: json.dump(m, f, indent=1, ensure_ascii=False)
    os.replace(tmp, PATH)


def d(s): return dt.date.fromisoformat(s[:10]) if s else None


def monday(day: dt.date) -> dt.date: return day - dt.timedelta(days=day.weekday())


def all_moments(m=None):
    """every moment of every race, derived ones included, sorted by date"""
    m = m or load(); out = []
    for slug, r in m['races'].items():
        base = dict(slug=slug, name=r.get('name', slug), edition=r.get('edition'))
        rd, last = d(r.get('race_date')), d(r.get('last_day')) or d(r.get('race_date'))
        if rd:
            st, src = r.get('date_status', 'pattern'), r.get('date_source', '')
            out.append(dict(base, kind='race_week', date=monday(rd).isoformat(), status=st, source=src, note=f"race day {rd}"))
            out.append(dict(base, kind='race_day', date=rd.isoformat(), status=st, source=src, note=''))
            # the Monday after the race finishes ("How it was won"); a race ending on a Monday gets the next one
            out.append(dict(base, kind='results_monday', date=(monday(last) + dt.timedelta(days=7)).isoformat(), status=st, source=src, note=''))
        for x in r.get('moments', []):
            if x.get('kind') in ENTRY and x.get('date'):
                out.append(dict(base, kind=x['kind'], date=x['date'][:10], status=x.get('status', 'pattern'), source=x.get('source', ''),
                                note=x.get('note', ''), quote=x.get('quote', '')))
    return sorted(out, key=lambda x: (x['date'], x['slug'], x['kind']))


def on(day: dt.date, kinds=None, confirmed=False):
    return [x for x in all_moments() if x['date'] == day.isoformat() and (not kinds or x['kind'] in kinds)
            and (not confirmed or x['status'] == 'confirmed')]


def between(a: dt.date, b: dt.date, kinds=None, confirmed=False):
    return [x for x in all_moments() if a.isoformat() <= x['date'] <= b.isoformat() and (not kinds or x['kind'] in kinds)
            and (not confirmed or x['status'] == 'confirmed')]


def race_week(day: dt.date):
    """slugs racing in the Monday-Sunday week holding `day`, in race-date order"""
    mo = monday(day)
    return [x['slug'] for x in all_moments() if x['kind'] == 'race_week' and x['date'] == mo.isoformat()]


def cycle(slug):
    """a race's entry moments, in date order (for the slides and captions)"""
    r = load()['races'].get(slug, {})
    return sorted([x for x in r.get('moments', []) if x.get('kind') in ENTRY and x.get('date')], key=lambda x: x['date'])


def check(day: dt.date):
    """lines that need a look"""
    out = []
    for x in all_moments():
        dd = d(x['date'])
        if x['kind'] in ENTRY and x['status'] != 'confirmed' and day <= dd <= day + dt.timedelta(days=21):
            out.append(f"CONFIRM {x['date']} {x['slug']} {x['kind']} (pattern: {x['note'] or x['source']})")
        if x['kind'] == 'race_day' and x['status'] != 'confirmed' and day <= dd <= day + dt.timedelta(days=45):
            out.append(f"CONFIRM {x['date']} {x['slug']} race date (pattern: {x['source']})")
        if not x['source'] and x['kind'] in ENTRY + ('race_day',):
            out.append(f"SOURCE? {x['date']} {x['slug']} {x['kind']}")
    for slug, r in load()['races'].items():
        if r.get('watch') and day >= (d(r.get('watch_from')) or dt.date.min):
            out.append(f"WATCH {slug}: {r['watch']}")          # a big moment that's coming but not announced yet
        rd = d(r.get('race_date'))
        if not rd: out.append(f"NO DATE {slug}: {r.get('notes', '')[:120]}")
        elif rd < day - dt.timedelta(days=9): out.append(f"PAST {slug} raced {rd}: research the next edition (moments.py race)")
    return out


def merge(paths):
    m = load()
    rank = {'confirmed': 2, 'pattern': 1}
    for p in paths:
        with open(p) as f: new = json.load(f)['races']
        for slug, r in new.items():
            old = m['races'].get(slug)
            if not old or (r.get('edition') or 0) > (old.get('edition') or 0) or \
               ((r.get('edition') or 0) == (old.get('edition') or 0) and rank.get(r.get('date_status'), 0) >= rank.get(old.get('date_status'), 0)):
                keep = (old or {}).get('moments', []) if old and (r.get('edition') or 0) == (old.get('edition') or 0) else []
                old_inst = (old or {}).get('instagram')
                m['races'][slug] = r; old = r
                if old_inst and not r.get('instagram'): r['instagram'] = old_inst
                # moments the new file doesn't have survive; for a kind in both, the better status (then the newer file) wins
                have = {x['kind']: x for x in r.get('moments', [])}
                for x in keep:
                    if x['kind'] not in have: r.setdefault('moments', []).append(x)
                    elif rank.get(x.get('status'), 0) > rank.get(have[x['kind']].get('status'), 0):
                        r['moments'] = [x if y['kind'] == x['kind'] else y for y in r['moments']]
            else:
                have = {x['kind'] for x in old.get('moments', [])}
                for x in r.get('moments', []):
                    if x['kind'] not in have: old.setdefault('moments', []).append(x)
        print('merged', p, len(new), 'races')
    save(m)


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else 'on'
    today = dt.date.today()
    if cmd in ('on', 'week', 'check'):
        day = d(a[1]) if len(a) > 1 else today
        rows = on(day) if cmd == 'on' else between(monday(day), monday(day) + dt.timedelta(days=6)) if cmd == 'week' else None
        if cmd == 'check':
            for ln in check(day): print(ln)
            return 0
        for x in rows: print(x['date'], x['kind'].ljust(18), x['status'].ljust(9), x['slug'], x['note'])
        if not rows: print('No moments')
        return 0
    if cmd == 'upcoming':
        n = int(a[1]) if len(a) > 1 else 30
        for x in between(today, today + dt.timedelta(days=n)):
            if x['kind'] == 'race_day': continue
            print(x['date'], x['kind'].ljust(18), x['status'].ljust(9), x['slug'])
        return 0
    m = load()
    if cmd == 'set':
        slug, kind, date, status, source = a[1:6]
        assert kind in ENTRY and status in ('confirmed', 'pattern'); d(date)
        r = m['races'].setdefault(slug, {'name': slug, 'moments': []})
        r['moments'] = [x for x in r.get('moments', []) if x['kind'] != kind] + [dict(kind=kind, date=date, status=status, source=source, quote=a[6] if len(a) > 6 else '', note='')]
        save(m); print('set', slug, kind, date, status); return 0
    if cmd == 'drop':
        slug, kind = a[1:3]
        r = m['races'][slug]; r['moments'] = [x for x in r.get('moments', []) if x['kind'] != kind]
        save(m); print('dropped', slug, kind); return 0
    if cmd == 'race':
        slug, date = a[1], a[2]; rest = a[3:]
        last = rest.pop(0) if rest and rest[0][:4].isdigit() else None
        status, source = rest[0], rest[1]
        r = m['races'].setdefault(slug, {'name': slug, 'moments': []})
        if d(date) > (d(r.get('race_date')) or dt.date.min) + dt.timedelta(days=200):
            r['moments'] = []                               # a new edition: last cycle's entry moments are history
        r.update(race_date=date, last_day=last, date_status=status, date_source=source, edition=d(date).year)
        save(m); print('race', slug, date, last or '', status); return 0
    if cmd == 'merge':
        merge(a[1:]); return 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())

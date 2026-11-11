#!/usr/bin/env python3
"""Race-week Reels for one week's featured races, made on the Thursday before and scheduled on YouTube; the daily
social calendar (Films/_social/social_calendar.py) queues their Instagram/Facebook cuts on the day.

Kris, 2026-11-11: "Maybe we should up the number of reals and shorts we do" / "I love this proceed" (ideas report
https://claude.ai/artifact/2Y2wvovM6UWPr8KnBq6r9g). The race-week cadence it set up:
  Mon  "How it was won" (the Monday task)
  Tue  every aid station in 30 seconds (aidreel.py), YouTube 12:00 New York, then an hour apart
  Wed  where will you finish? from last year's finish times (finishreel.py --before), YouTube 12:00, an hour apart
  Thu  the race Short (the Thursday task's short_film.py)
  Sun  where would you finish? from this year's times, made that day by the calendar when the official feed has them

    reels_week.py --week YYYY-MM-DD <slug> [<slug> …] [--no-upload]

Make with --no-upload, look at the frames, then run again without it to schedule them (made files are reused). A Reel
that fails its check gets an empty HOLD file in its folder: nothing uploads it and the calendar never queues it.

Per race, each step is skipped when its file already exists, and a failure only skips that race's Reel:
  aids    unless Films/_social/aid-reel-skip.json names the race (its film pins only some stations, so "every aid
          station" would be wrong: JFK's pins are its eight cutoff stations)
  before  when Films/_social/finish-sources.json has last year's results feed for the race
Run with the weekly-shorts venv. Renders take the studio's render lock (aidreel.py waits for it).
"""
import datetime as dt
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reelkit as K   # noqa: E402

SOC = f'{K.STUDIO}/Films/_social'


def race_day(slug, monday):
    """the race's day in the week of `monday`, from moments.json"""
    m = json.load(open(f'{SOC}/moments.json'))['races'].get(slug, {})
    rd = (m.get('race_date') or '')[:10]
    if rd and 0 <= (dt.date.fromisoformat(rd) - monday).days < 7: return dt.date.fromisoformat(rd)
    return monday + dt.timedelta(days=5)


def run(args):
    print('$', ' '.join(os.path.basename(a) if a.endswith('.py') else a for a in args), flush=True)
    r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-4:]
    for ln in tail: print('   ', ln[:220])
    if r.returncode != 0: raise RuntimeError(f'{os.path.basename(args[0])} exit {r.returncode}')


def aids(slug, rd, k, upload):
    skip = json.load(open(f'{SOC}/aid-reel-skip.json')) if os.path.exists(f'{SOC}/aid-reel-skip.json') else {}
    if slug in skip: print(f'{slug}: no aid Reel ({skip[slug]})'); return None
    year = rd.year; d = f'{K.STUDIO}/Films/{slug}/aids-{year}/'
    mp4 = d + f'{slug}-{year}-aid-stations.mp4'
    if not (os.path.exists(mp4) and os.path.exists(d + f'{slug}-{year}-aid-stations-social.mp4') and os.path.exists(d + 'meta.json')):
        os.environ['AIDS_YEAR'] = str(year)
        run([f'{HERE}/aidreel.py', slug, 'all'])
    if upload and os.path.exists(d + 'HOLD'): print(f'{slug}: aids held (HOLD)'); return None
    if upload:
        tue = rd - dt.timedelta(days=rd.weekday() - 1)
        vid = K.yt_schedule(d, mp4, K.ny_utc(tue, f'{12 + k}:00')); print(f'{slug}: aids https://youtu.be/{vid}')
    return d


def before(slug, rd, k, upload):
    src = json.load(open(f'{SOC}/finish-sources.json')).get(slug, {})
    last = rd.year - 1
    if str(last) not in src: print(f'{slug}: no {last} results feed in finish-sources.json'); return None
    f = f'{K.STUDIO}/Films/{slug}/finish-{last}/'; d = f + 'before/'
    mp4 = d + f'{slug}-{last}-finishers-before.mp4'
    if not os.path.exists(f + 'times.json'): run([f'{HERE}/finish_times.py', slug, str(last)])
    if not (os.path.exists(mp4) and os.path.exists(d + 'meta.json')): run([f'{HERE}/finishreel.py', slug, str(last), '--before'])
    if upload and os.path.exists(d + 'HOLD'): print(f'{slug}: before held (HOLD)'); return None
    if upload:
        wed = rd - dt.timedelta(days=rd.weekday() - 2)
        vid = K.yt_schedule(d, mp4, K.ny_utc(wed, f'{12 + k}:00')); print(f'{slug}: finish (before) https://youtu.be/{vid}')
    return d


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--week' not in a: sys.exit(__doc__)
    monday = dt.date.fromisoformat(a[a.index('--week') + 1]); upload = '--no-upload' not in a
    slugs = [x for x in a if not x.startswith('--') and x != a[a.index('--week') + 1]]
    slugs = sorted(slugs, key=lambda s: race_day(s, monday))
    ka = kb = 0
    for slug in slugs:
        rd = race_day(slug, monday)
        for name, fn in (('aids', aids), ('before', before)):
            try:
                got = fn(slug, rd, ka if name == 'aids' else kb, upload)
                if got and name == 'aids': ka += 1
                if got and name == 'before': kb += 1
            except Exception as e:                                  # one race's Reel failing never stops the week
                print(f'FAILED {slug} {name}: {e}')

#!/usr/bin/env python3
"""Every finisher's time for one race edition, from the race's official results feed, for finishreel.py.

    finish_times.py <slug> <year>      # -> Films/<slug>/finish-<year>/times.json {"race","year","source","finish_s":[…]}

Times only: names, bibs and the rest of each row are read and dropped. The feed and its ids come from
Films/_social/finish-sources.json (provider + ids per race and year; the providers below are the ones won-sources.json
found open to an identified client with no key). UltraSignup refuses scripted requests from this Mac and isn't used.
  runsignup  {"race": 86044, "event": 965811, "set": 606864}   (set null: the event's 'Overall' set, found at run time)
  utmb       {"tenant": "barilochebyutmb_2025", "race": "130K"}
  sportraxs  {"race": 1328}
"""
import json, os, re, sys, time
# this folder's queue.py would shadow the standard library's queue, which requests (urllib3) imports
sys.path = [p for p in sys.path if os.path.abspath(p or '.') != os.path.dirname(os.path.abspath(__file__))]
import requests   # noqa: E402

STUDIO = '/Volumes/KB SS/TrailGoat-Studio'
UA = {'User-Agent': 'TrailGoat (trailgoat.run)'}
SLUG, YEAR = sys.argv[1], int(sys.argv[2])


def secs(t):
    m = re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,]\d+)?', (t or '').strip())
    return None if not m else int(m[1] or 0)*3600 + int(m[2])*60 + int(m[3])


def runsignup(c):
    out, page = [], 1
    if not c.get('set'):                               # this year's set appears once the race posts results: take 'Overall'
        sets = requests.get(f"https://runsignup.com/Rest/race/{c['race']}/results/get-results", headers=UA, timeout=40,
                            params=dict(format='json', event_id=c['event'], results_per_page=1)).json().get('individual_results_sets') or []
        if not sets: return [], f"https://runsignup.com/Race/Results/{c['race']}"
        c = dict(c, set=next((x for x in sets if (x.get('individual_result_set_name') or '').lower() == 'overall'), sets[0])['individual_result_set_id'])
    while True:
        d = requests.get(f"https://runsignup.com/Rest/race/{c['race']}/results/get-results", headers=UA, timeout=40,
                         params=dict(format='json', event_id=c['event'], individual_result_set_id=c['set'], page=page, results_per_page=250)).json()
        rows = d['individual_results_sets'][0]['results']
        out += [s for s in (secs(r.get('chip_time') or r.get('clock_time')) for r in rows) if s]
        if len(rows) < 250: return out, f"https://runsignup.com/Race/Results/{c['race']}"
        page += 1; time.sleep(2)


def utmb(c):
    h = dict(UA, **{'X-Tenant': c['tenant']}); out, page = [], 0
    while True:
        d = requests.get(f"https://utmblive-api.utmb.world/races/{c['race']}/progressive", headers=h, timeout=40,
                         params=dict(type='FINAL_RANKING', page=page, limit=100)).json()
        rows = d.get('runners') or []
        out += [s for s in (secs(r.get('raceTime')) for r in rows) if s]
        if len(rows) < 100: return out, f"https://live.utmb.world/{c['tenant'].rsplit('_', 1)[0]}/{c['tenant'].rsplit('_', 1)[1]}"
        page += 1; time.sleep(2)


def sportraxs(c):
    # the leaderboard lists everyone at their last checkpoint; a finisher's last checkpoint is the finish
    q = ('query($id:Int!){race(id:$id){m: testLeaderboard(category:"male",limit:5000){checkpointName checkpointTime} '
         'f: testLeaderboard(category:"female",limit:5000){checkpointName checkpointTime}}}')
    d = requests.get('https://tan.sportraxs.com/api/graphql', headers=UA, timeout=60,
                     params=dict(query=q, variables=json.dumps({'id': int(c['race'])}))).json()
    race = (d.get('data') or {}).get('race') or {}
    rows = (race.get('m') or []) + (race.get('f') or [])
    fin = [r for r in rows if re.search(r'finish', r.get('checkpointName') or '', re.I)]
    return [s for s in (secs(r.get('checkpointTime')) for r in fin) if s], f"https://tan.sportraxs.com (race {c['race']})"


if __name__ == '__main__':
    src = json.load(open(f'{STUDIO}/Films/_social/finish-sources.json'))[SLUG][str(YEAR)]
    times, url = {'runsignup': runsignup, 'utmb': utmb, 'sportraxs': sportraxs}[src['provider']](src)
    if len(times) < 10: sys.exit(f'{SLUG} {YEAR}: only {len(times)} finish times from {src["provider"]}; not enough for a chart')
    times.sort(); d = f'{STUDIO}/Films/{SLUG}/finish-{YEAR}/'; os.makedirs(d, exist_ok=True)
    name = src.get('race_name') or SLUG
    json.dump(dict(race=name, year=YEAR, source=f'{url} ({src["provider"]})', finish_s=times), open(d + 'times.json', 'w'))
    h = lambda s: f'{s//3600}:{s % 3600//60:02d}:{s % 60:02d}'
    print(f'{SLUG} {YEAR}: {len(times)} finishers, {h(times[0])} to {h(times[-1])}, median {h(times[len(times)//2])}')

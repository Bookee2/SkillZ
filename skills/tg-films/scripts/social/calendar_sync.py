#!/usr/bin/env python3
"""Send the social queue to the posting calendar on trailgoat.run/admin/social.

Kris, 2026-11-04: "what's the way for me to visualize our instagram posting calendar. Can you add me a posting calendar
function to the admin panel on TrailGoat?" The queue stays here (queue.json, posted from by the poster task); this writes
a snapshot of it into the site's database (table social_calendar, migration 0087), the same way race imports reach it,
so the site never reaches back into this Mac. queue.py starts it in the background after every change, and otherwise at
most every three hours, so the planned days and moments stay current too.

    calendar_sync.py            # build the snapshot and send it (thumbnails only when new or changed)
    calendar_sync.py --dry      # build it and print a summary, send nothing

The snapshot: every queued post (when, kind, race, status per platform, captions, slide count), what social_calendar.py
would make on each of the next six weeks' days (planned, not made), race days and lottery/registration dates around now,
and YouTube uploads scheduled to go public. Thumbnails (the first slide, or a video frame) go as one row each.

Credentials: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN from the TrailGoat checkout's .env; never printed. Run with the
weekly-shorts venv (carousel.py needs Pillow; video frames need imageio-ffmpeg).
"""
from __future__ import annotations

import base64
import datetime as dt
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import carousel as C          # noqa: E402
import moments as Mo          # noqa: E402
import social_calendar as S   # noqa: E402

# this folder's queue.py, by path: `import queue` could hand back the standard library's module
_spec = importlib.util.spec_from_file_location('tg_social_queue', os.path.join(HERE, 'queue.py'))
Q = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(Q)

FILMS = C.FILMS
ENV = os.environ.get('TRAILGOAT_ENV', '/Users/kb/Desktop/Projects/TrailGoat/.env')
STATE = os.path.join(HERE, 'calendar-sync.json')
AHEAD, BEHIND = 42, 60           # planned days ahead; moments from two months back to half a year on
# Kept identical to app/migrations/0087_social_calendar.sql, so a sync before that deploy still has a table to write.
SCHEMA = ("CREATE TABLE IF NOT EXISTS social_calendar (key TEXT PRIMARY KEY, body TEXT NOT NULL,"
          " updated_at TEXT DEFAULT (datetime('now')))")
UPSERT = ("INSERT INTO social_calendar (key, body, updated_at) VALUES (?, ?, datetime('now'))"
          " ON CONFLICT(key) DO UPDATE SET body=excluded.body, updated_at=excluded.updated_at")


def names():
    """slug -> the race's own name: the film's, else moments.json's"""
    out = {s: r.get('name', s) for s, r in Mo.load()['races'].items()}
    out.update({f['slug']: f['name'] for f in C.films()})
    return out


def slug_in(text, slugs):
    """the longest race slug inside a post id ('raceweek-kessel-run-ultra-50-2026-11-02' -> 'kessel-run-ultra-50')"""
    hits = [s for s in slugs if f'-{s}-' in f'-{text}-']
    return max(hits, key=len) if hits else None


def read(p):
    try: return open(p, encoding='utf-8').read().strip()
    except OSError: return ''


def posted(it):
    """{ig|fb|yt: {at, state, url, note}} from queue.py's marks ({id, at})"""
    out = {}
    for w, m in it.get('posted', {}).items():
        pid = str(m.get('id', '')); low = pid.lower()
        skipped = low.startswith(('not posted', 'skipped'))
        url = pid if pid.startswith('https://') else None
        if not url and w == 'ig' and re.fullmatch(r'[A-Za-z0-9_-]{8,14}', pid) and low != 'done':
            url = f'https://www.instagram.com/p/{pid}/'
        out[w] = dict(at=m.get('at'), state='skipped' if skipped else 'posted', url=url,
                      note=pid if skipped else None)
    return out


def title_of(it, slug, race):
    if it.get('images'):
        pj = os.path.join(os.path.dirname(it['images'][0]), 'post.json')
        t = json.load(open(pj)).get('title') if os.path.exists(pj) else None
        if t: return t
    if it['kind'] == 'won' and slug:
        cfg = next(iter(sorted(glob.glob(f'{FILMS}/{slug}/won-*/cfg.json'))), None)
        if cfg: return 'How it was won: ' + json.load(open(cfg)).get('race_name', race or slug)
    label = {'race-short': 'Race Short', 'won': 'How it was won', 'story': 'Story', 'raceweek': 'Race week'}.get(it['kind'])
    return f'{label}: {race}' if label and race else it.get('title') or it['id']


def thumb(it):
    """a small JPEG of the first slide, or of the video 2.5 s in; None if neither can be read"""
    from PIL import Image
    try:
        if it.get('images'):
            im = Image.open(it['images'][0])
        elif it.get('mp4') and os.path.exists(it['mp4']):
            import imageio_ffmpeg
            raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-ss', '2.5', '-i', it['mp4'],
                                  '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                                 capture_output=True, timeout=60).stdout
            im = Image.open(io.BytesIO(raw))
        else:
            return None
        im = im.convert('RGB'); im.thumbnail((300, 540))
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=78, optimize=True)
        return buf.getvalue()
    except Exception as e:                      # a missing frame never stops the calendar
        print('no thumbnail for', it['id'], repr(e)[:160])
        return None


def build():
    now = dt.datetime.now(S.NY); today = now.date()
    nm = names(); slugs = list(nm)
    posts = []
    for it in Q.load():
        slug = slug_in(it['id'], slugs); race = nm.get(slug) if slug else None
        caps = it.get('captions') or ''
        posts.append(dict(id=it['id'], at=it['at'], kind=it['kind'], format='carousel' if it.get('images') else 'video',
                          title=title_of(it, slug, race), race=race, slug=slug, platforms=list(Q.platforms(it)),
                          posted=posted(it), slides=len(it.get('images') or []) or None,
                          captions=dict(instagram=read(f'{caps}/instagram.txt'), facebook=read(f'{caps}/facebook.txt'))))
    planned = []
    for i in range(AHEAD + 1):
        day = today + dt.timedelta(days=i)
        cards = 0
        for pid, kind, args, first in S.plan(day):
            if kind == 'raceweek':                 # build() makes the two longest races' cards and stops
                cards += 1
                if cards > 2: continue
            slug = args[1] if len(args) > 1 and isinstance(args[1], str) and args[1] in nm else slug_in(pid, slugs)
            planned.append(dict(id=pid, day=day.isoformat(), at=S.at(day, first), kind=kind, slug=slug,
                                race=nm.get(slug) if slug else None))
    keep = ('race_day',) + Mo.ENTRY
    lo, hi = (today - dt.timedelta(days=BEHIND)).isoformat(), (today + dt.timedelta(days=180)).isoformat()
    moments = [dict(date=x['date'], kind=x['kind'], slug=x['slug'], race=nm.get(x['slug'], x['name']),
                    status=x.get('status', 'pattern'))
               for x in Mo.all_moments() if x['kind'] in keep and lo <= x['date'] <= hi]
    youtube = []
    for p in glob.glob(f'{FILMS}/**/uploaded*.json', recursive=True):
        try: u = json.load(open(p))
        except (OSError, ValueError): continue
        pa = isinstance(u, dict) and u.get('publish_at')
        if not pa or dt.datetime.fromisoformat(pa.replace('Z', '+00:00')) <= now: continue
        meta = os.path.join(os.path.dirname(p), 'meta.json')
        title = json.load(open(meta)).get('title', '') if os.path.exists(meta) else os.path.basename(os.path.dirname(p))
        youtube.append(dict(at=pa, title=re.sub(r'\s*#Shorts\s*$', '', title), url=u.get('url') or f"https://youtu.be/{u.get('id')}",
                            kind='won' if '/won-' in p else 'video'))
    return dict(synced_at=now.isoformat(timespec='seconds'), posts=posts, planned=planned, moments=moments,
                youtube=sorted(youtube, key=lambda y: y['at']))


def turso():
    env = {}
    for line in read(ENV).splitlines():
        m = re.match(r'\s*(?:export\s+)?(TURSO_DATABASE_URL|TURSO_AUTH_TOKEN)\s*=\s*(.*)$', line)
        if m: env[m[1]] = m[2].strip().strip('"\'')
    url, token = env.get('TURSO_DATABASE_URL'), env.get('TURSO_AUTH_TOKEN')
    if not (url and token): sys.exit(f'no Turso credentials in {ENV}')
    return re.sub(r'^libsql://', 'https://', url).rstrip('/') + '/v2/pipeline', token


def send(rows):
    """[(key, body)] in one pipeline, after the CREATE TABLE IF NOT EXISTS; raises on any statement's error"""
    url, token = turso()
    reqs = [dict(type='execute', stmt=dict(sql=SCHEMA))]
    reqs += [dict(type='execute', stmt=dict(sql=UPSERT, args=[dict(type='text', value=k), dict(type='text', value=b)]))
             for k, b in rows]
    reqs.append(dict(type='close'))
    req = urllib.request.Request(url, data=json.dumps(dict(requests=reqs)).encode(), method='POST',
                                 headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    errs = [x.get('error', {}).get('message') for x in out.get('results', []) if x.get('type') == 'error']
    if errs: raise RuntimeError('Turso refused: ' + '; '.join(map(str, errs))[:300])


def main():
    dry = '--dry' in sys.argv
    snap = build()
    try: state = json.load(open(STATE))
    except (OSError, ValueError): state = {}
    sent = state.get('thumbs', {}); rows = [('snapshot', json.dumps(snap, ensure_ascii=False))]
    for it in Q.load():
        src = (it.get('images') or [it.get('mp4')])[0]
        if not src or not os.path.exists(src): continue
        sig = f'{os.path.getmtime(src):.0f}:{os.path.getsize(src)}'
        if sent.get(it['id']) == sig: continue
        img = thumb(it)
        if img: rows.append((f"thumb:{it['id']}", base64.b64encode(img).decode())); sent[it['id']] = sig
    print(f"{snap['synced_at']}: {len(snap['posts'])} posts, {len(snap['planned'])} planned, "
          f"{len(snap['moments'])} moments, {len(snap['youtube'])} on YouTube, {len(rows) - 1} new thumbnails")
    if dry: return 0
    send(rows)
    json.dump(dict(thumbs=sent, at=snap['synced_at']), open(STATE, 'w'), indent=1)
    print('sent')
    return 0


if __name__ == '__main__':
    sys.exit(main())

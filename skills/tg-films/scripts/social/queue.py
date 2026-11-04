#!/usr/bin/env python3
"""The social queue: every Short waiting to go to Instagram and Facebook, with the time it should go up.

Kris, 2026-11-02: "By automate, I mean the whole creation and posting process of these shorts. Once we perfect it I want
it just to run." Builders (the Thursday race-week Shorts, the Monday "How it was won") add items; the poster task posts
due items one at a time, so no more than one post lands in a run (six Reels in an hour got ~4 s of watch each).

    queue.py add <id> <at ISO> <mp4 | slides dir> <captions dir> [--kind race-short|won|week|results|guess|...] [--title T]
    queue.py due                  # the next due, unposted item as JSON (exit 1 if none)
    queue.py mark <id> <ig|fb|yt> <post id or 'done'>     # yt: carousels only, on the channel's Posts tab
    queue.py move <id> <at ISO>   # a new time for an item nothing has posted yet (e.g. its moment moved)
    queue.py list

captions dir holds instagram.txt and facebook.txt. A video item's mp4 is the off-YouTube cut (the closing line names the
channel); a carousel item's slides dir holds slide_1.jpg, slide_2.jpg… (carousel.py), posted as one multi-image post.
The queue lives beside this file in queue.json; items are never removed, only marked.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

Q = Path(__file__).with_name('queue.json')


def load():
    return json.loads(Q.read_text()) if Q.exists() else []


def save(items):
    tmp = Q.with_suffix('.tmp'); tmp.write_text(json.dumps(items, indent=1, ensure_ascii=False)); tmp.replace(Q)
    sync(changed=True)


def sync(changed=False):
    """refresh the posting calendar on trailgoat.run/admin/social (calendar_sync.py) in the background: after every
    change, and otherwise at most every three hours, so its planned days and moments stay current. Never blocks or
    fails the queue command that started it; calendar-sync.log beside this file says how each went. Off until
    calendar-sync.on exists beside this file: the sync writes to the site's production database, which waits for Kris's yes."""
    if not Q.with_name('calendar-sync.on').exists(): return
    st = Q.with_name('calendar-sync.json')
    if not changed and st.exists() and time.time() - st.stat().st_mtime < 3 * 3600: return
    py = '/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts/.venv/bin/python'
    try:
        with open(Q.with_name('calendar-sync.log'), 'a') as log:
            subprocess.Popen([py if os.path.exists(py) else sys.executable, str(Q.with_name('calendar_sync.py'))],
                             stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def platforms(it):
    """the platforms an item goes to: Instagram and the Facebook Page. Carousels went to the YouTube channel's Posts tab
    too until Kris, 2026-11-03: "I don't think that post will do well on YouTube. We only have 3 subscribers ... Let's see
    how it does on IG first." Now a carousel goes there only when its item says "yt": true (videos are on YouTube already)."""
    return ('ig', 'fb', 'yt') if it.get('images') and it.get('yt') else ('ig', 'fb')


def done(it):
    return all(it['posted'].get(w) for w in platforms(it))


def main():
    a = sys.argv[1:]
    items = load()
    if not a or a[0] in ('list', 'due'): sync()          # the poster's twice-daily `due` keeps the calendar fresh
    if not a or a[0] == 'list':
        for it in items:
            print(it['at'], it['id'], it['kind'], 'carousel' if it.get('images') else 'video', *[(w.upper() if it['posted'].get(w) else '--') for w in platforms(it)])
        return 0
    if a[0] == 'add':
        iid, at, mp4, caps = a[1:5]
        mp4, caps = os.path.abspath(mp4), os.path.abspath(caps)     # the poster runs from elsewhere
        kind = a[a.index('--kind') + 1] if '--kind' in a else 'race-short'
        title = a[a.index('--title') + 1] if '--title' in a else iid
        dt.datetime.fromisoformat(at)                         # must parse, with its offset
        for p in (Path(mp4), Path(caps) / 'instagram.txt', Path(caps) / 'facebook.txt'):
            if not p.exists(): sys.exit(f'missing {p}')
        if any(it['id'] == iid for it in items): print('already queued', iid); return 0
        media = dict(mp4=mp4)
        if Path(mp4).is_dir():                                 # a carousel: its slides in order
            imgs = sorted(Path(mp4).glob('slide_*.jpg'), key=lambda q: int(q.stem.split('_')[1]))
            if not imgs: sys.exit(f'no slide_N.jpg in {mp4}')
            media = dict(mp4=None, images=[str(q) for q in imgs])
        items.append(dict(id=iid, at=at, kind=kind, title=title, captions=caps, posted={}, **media))
        items.sort(key=lambda it: it['at']); save(items); print('queued', iid, at); return 0
    if a[0] == 'due':
        now = dt.datetime.now(dt.timezone.utc)
        for it in items:
            if dt.datetime.fromisoformat(it['at']) <= now and not done(it):
                print(json.dumps(it, ensure_ascii=False)); return 0
        return 1
    if a[0] == 'move':
        iid, at = a[1:3]; dt.datetime.fromisoformat(at)
        for it in items:
            if it['id'] == iid:
                if it['posted']: sys.exit(f'{iid} is already posted on {", ".join(it["posted"])}: not moving it')
                it['at'] = at; items.sort(key=lambda it: it['at']); save(items); print('moved', iid, at); return 0
        sys.exit(f'no item {iid}')
    if a[0] == 'mark':
        iid, where, pid = a[1:4]
        for it in items:
            if it['id'] == iid:
                it['posted'][where] = dict(id=pid, at=dt.datetime.now().astimezone().isoformat(timespec='seconds')); save(items); print('marked', iid, where); return 0
        sys.exit(f'no item {iid}')
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())

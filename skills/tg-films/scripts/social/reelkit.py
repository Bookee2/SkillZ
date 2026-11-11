"""What the race-week Reels share (aidreel.py, finishreel.py, oddsreel.py): the film's facts, the music mix at -14 LUFS,
a 9:16 frame writer and the words around every post (course page, full film, the race's Instagram handle).

Kris, 2026-11-11: "I love this proceed" on the Reel ideas report https://claude.ai/artifact/2Y2wvovM6UWPr8KnBq6r9g.
"""
import glob, json, os, re, subprocess, sys
TG = '/Users/kb/Desktop/Projects/TrailGoat/.claude/worktrees/weekly-shorts/scripts/flythrough'
sys.path.insert(0, TG); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hud, short as S        # noqa: E402,F401

STUDIO = '/Volumes/KB SS/TrailGoat-Studio'
W, H, FPS = 1080, 1920, 24
TAGS = '#trailrunning #ultramarathon #ultrarunning #trailgoat'


def film(slug):
    return json.load(open(f'{STUDIO}/Films/{slug}/film.json'))


def race_name(slug):
    """The race as its sign reads, without the year: queue/<slug>/race_name, else the course's name."""
    p = f'{STUDIO}/Films/queue/{slug}/race_name'
    if os.path.exists(p): name = open(p).read().strip()
    else: name = json.load(open(sorted(glob.glob(film(slug)['out_dir'] + '/course-*.json'))[0]))['name']
    return re.sub(r'\s{2,}', ' ', re.sub(r'\b(19|20)\d{2}\b', '', re.split(r'\s+[—–-]\s+', name)[0])).strip(' -—–')


def links(slug):
    """(course page URL, full film's YouTube id, the race's confirmed Instagram handle) — any may be None."""
    d = f'{STUDIO}/Films/{slug}/description.txt'; desc = open(d).read() if os.path.exists(d) else ''
    page = (re.search(r'https://trailgoat\.run/course/[^\s)]+', desc) or [None])[0]
    up = f'{STUDIO}/Films/{slug}/uploaded.json'; vid = json.load(open(up))['id'] if os.path.exists(up) else None
    if not vid and page:                               # as short_film.video_id: the films page's list, then title_history.json
        repo = os.environ.get('TRAILGOAT_REPO', os.path.expanduser('~/Desktop/Projects/TrailGoat'))
        try: films = json.load(open(f'{repo}/app/films.json'))
        except OSError:                                # Kris's main checkout can lag: read the list from origin/main
            r = subprocess.run(['git', '-C', repo, 'show', 'origin/main:app/films.json'], capture_output=True, text=True)
            films = json.loads(r.stdout) if r.returncode == 0 else []
        films = films if isinstance(films, list) else films.get('films', [])
        vid = next((f['id'] for f in films if f.get('course') == page.rstrip('/').split('/')[-1]), None)
        th = f'{STUDIO}/Films/{slug}/title_history.json'
        if not vid and os.path.exists(th):
            vid = next((x.get('video_id') for x in reversed(json.load(open(th))) if x.get('video_id')), None)
    ig = json.load(open(f'{STUDIO}/Films/_social/race-handles.json'))['handles'].get(slug)
    return page, vid, ig


def ffmpeg():
    return hud.ffmpeg() if hasattr(hud, 'ffmpeg') else 'ffmpeg'


def writer(dst):
    """An ffmpeg process taking raw RGB 1080x1920 frames on stdin."""
    return subprocess.Popen([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                             '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst],
                            stdin=subprocess.PIPE)


def track(slug):
    import music_rights
    m = music_rights.cleared_music(film(slug).get('music') or {}, slug)
    if not m: sys.exit(f'{slug}: no cleared music for this film')
    return m


def lufs(path, af=None):
    e = subprocess.run([ffmpeg(), '-hide_banner', '-nostats', '-i', path, '-af', (af + ',' if af else '') + 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])


def mix(slug, silent, dst, dur):
    """The film's track under a silent Reel at -14 LUFS, from the loudest stretch of the piece, with won.py's
    gain-plus-limiter fallback when loudnorm leaves a quiet piece short (Bear's lullaby, 2026-11-04)."""
    m = track(slug); ff = ffmpeg()
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', m['file'], '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    L = [float(x) for x in re.findall(r'M:\s*(-?[\d.]+)', r)]; n = int(dur*10)
    def score(i):
        w = L[i:i + n]; return (sum(w)/len(w)) - (15 if min(w[:10]) < -45 else 0)
    start = max(range(0, max(1, len(L) - n), 5), key=score)/10 if len(L) > n else 0.0
    pre = f'atrim=start={start:.3f}:end={start + dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={dur - 1.5:.2f}:d=1.5'
    def mux(af):
        subprocess.run([ff, '-y', '-loglevel', 'error', '-i', silent, '-i', m['file'], '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.3f}', '-movflags', '+faststart', dst], check=True)
        return lufs(dst)
    got = mux(f'[1:a]{pre},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]')
    if got < -16.5:
        gain = -14 - lufs(m['file'], pre)
        got = mux(f'[1:a]{pre},volume={gain:.2f}dB,alimiter=limit=0.841:attack=5:release=50:level=0,aresample=48000[a]')
    print('MUXED', dst, f'{dur:.1f} s', 'music from', f'{start:.1f} s', f'{got:.1f} LUFS')
    return m


def music_line(m):
    return f'Music: "{m["title"]}" ({m["artist"]})' + (f'. {m["credit"]}' if m.get('credit') else '')


def write_words(dest, captions, meta):
    os.makedirs(dest + 'captions', exist_ok=True)
    for k, v in captions.items(): open(dest + f'captions/{k}.txt', 'w').write(v.strip() + '\n')
    if len(meta['title']) > 100: sys.exit(f"title over 100 characters: {meta['title']}")
    assert not any(',' in t for t in meta['tags']), 'a comma in a tag wipes the rest'
    json.dump(meta, open(dest + 'meta.json', 'w'), indent=1, ensure_ascii=False)


# ---------- YouTube ----------
YT_PY = os.path.expanduser('~/.config/trailgoat-youtube/venv/bin/python')
YT_UP = '/Users/kb/Desktop/Projects/TrailGoat/marketing/youtube/yt_upload.py'


def ny_utc(day, hhmm):
    """'2026-11-17', '12:00' New York -> '2026-11-17T17:00:00Z'"""
    import datetime as dt
    from zoneinfo import ZoneInfo
    h, m = map(int, hhmm.split(':')); d = dt.date.fromisoformat(str(day))
    t = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ZoneInfo('America/New_York')).astimezone(dt.timezone.utc)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def yt_schedule(folder, mp4, publish_at=None):
    """Upload a Reel's YouTube cut as a Short, public at publish_at (UTC, RFC 3339; a time already past or within 20
    minutes becomes now + 20 min), once: folder/uploaded.json records it and a second call returns that id."""
    import datetime as dt
    up = os.path.join(folder, 'uploaded.json')
    if os.path.exists(up): return json.load(open(up))['id']
    meta_p = os.path.join(folder, 'meta.json'); meta = json.load(open(meta_p))
    soon = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=20)
    when = dt.datetime.strptime(publish_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc) if publish_at else soon
    meta['publish_at'] = max(when, soon).strftime('%Y-%m-%dT%H:%M:%SZ')
    json.dump(meta, open(meta_p, 'w'), indent=1, ensure_ascii=False)
    r = subprocess.run([YT_PY, YT_UP, 'upload', mp4, meta_p], capture_output=True, text=True)
    sys.stdout.write(r.stdout[-800:]); sys.stderr.write(r.stderr[-800:])
    vid = (re.findall(r'https://youtu\.be/([\w-]{11})', r.stdout) or [None])[-1]
    if vid: json.dump(dict(id=vid, publish_at=meta['publish_at']), open(up, 'w'))   # recorded even if the read-back failed: never upload twice
    if r.returncode != 0 or not vid: raise RuntimeError(f'YouTube upload of {mp4}: exit {r.returncode}, id {vid}')
    return vid

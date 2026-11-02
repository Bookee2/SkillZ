#!/usr/bin/env python3
"""Post a finished Short off YouTube: Instagram Reels and the TrailGoat Facebook Page through one Meta app, and TikTok
as a draft in the account's inbox.

    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/social_post.py <ig|fb|tiktok|all> <dest>/short [--dry-run]
    TRAILGOAT_REPO=<checkout> python3 ~/.claude/skills/tg-films/scripts/social_post.py check

Kris, 2026-11-02: "I want to set up our own pipeline" (rather than a paid cross-poster). What it posts is the Short's
off-YouTube copy, `<slug>-short-social.mp4`: the same cut with music cleared everywhere and a closing line naming the
channel instead of "link below" (short_film.py --social makes it). Its caption comes from social-caption.txt beside it.

- Instagram (Instagram API with Instagram Login, instagram_business_content_publish): the video goes to the site's R2
  bucket under social/ first, because Instagram fetches a Reel from a public URL; then a REELS container, a wait for
  FINISHED, and media_publish. 100 API posts a day. A Professional (Creator or Business) account; in the Meta app's
  development mode it posts to accounts whose owner has a role on the app, so it needs no App Review for our own.
- Facebook Page (pages_manage_posts, pages_read_engagement, the Reels publishing flow): start, upload by file_url,
  finish with video_state PUBLISHED and the caption as description.
- TikTok (Content Posting API, video.upload): an upload to the inbox as a draft, which Kris posts from the app with one
  tap. Direct, public posting needs TikTok's audit of the app first (until then everything posts private).

Credentials live in ~/.config/trailgoat-social/ (meta.json, tiktok.json) and are never printed. Each post writes its
id to <dest>/short/posted.json so nothing goes up twice. Not exercised against the live APIs until the accounts exist
(2026-11-02); --dry-run prints every request it would make, without tokens.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(os.environ.get('TRAILGOAT_REPO', Path.home() / 'Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', str(REPO / '.venv/bin/python'))
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])

CONF = Path.home() / '.config' / 'trailgoat-social'
GRAPH = os.environ.get('META_GRAPH_VERSION', 'v23.0')
TIKTOK = 'https://open.tiktokapis.com/v2'
DRY = False


def creds(name: str) -> dict:
    p = CONF / f'{name}.json'
    if not p.exists():
        sys.exit(f'no {p}: set up the {name} account first (tg-films SKILL.md, "Off YouTube")')
    return json.loads(p.read_text())


def call(method: str, url: str, data: dict | None = None, headers: dict | None = None, body: bytes | None = None) -> dict:
    """One HTTP call; tokens are passed in headers or form fields and never printed."""
    shown = url.split('?')[0]
    if DRY:
        safe = {k: ('…' if 'token' in k.lower() else v) for k, v in (data or {}).items()}
        print(f'DRY {method} {shown} {json.dumps(safe)[:300]}')
        return {'id': 'dry-run', 'status_code': 'FINISHED', 'data': {'publish_id': 'dry-run', 'upload_url': 'https://dry-run'}}
    if data is not None and body is None:
        body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {shown}: HTTP {e.code} {e.read()[:400]!r}')


def stage(mp4: Path, key: str) -> str:
    """Put the video in the site's R2 bucket under social/ and return its public URL (Instagram and Facebook fetch it)."""
    sys.path.insert(0, str(REPO))
    from app import config
    url = f'{config.R2_PUBLIC_BASE}/social/{key}'
    if DRY:
        print(f'DRY put {mp4.name} -> {url}'); return url
    import boto3
    s3 = boto3.client('s3', endpoint_url=config.R2_ENDPOINT, aws_access_key_id=config.R2_ACCESS_KEY_ID,
                      aws_secret_access_key=config.R2_SECRET_ACCESS_KEY, region_name='auto')
    s3.upload_file(str(mp4), config.R2_BUCKET, f'social/{key}', ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=604800'})
    return url


def post_instagram(mp4: Path, caption: str, key: str) -> str:
    c = creds('meta'); url = stage(mp4, key)
    base = f"https://graph.instagram.com/{GRAPH}/{c['ig_user_id']}"
    auth = {'Authorization': f"Bearer {c['ig_access_token']}"}
    box = call('POST', f'{base}/media', {'media_type': 'REELS', 'video_url': url, 'caption': caption, 'share_to_feed': 'true'}, auth)
    for _ in range(60):            # Instagram downloads and processes the video before it can publish
        st = call('GET', f"https://graph.instagram.com/{GRAPH}/{box['id']}?fields=status_code", None, auth)
        if st.get('status_code') == 'FINISHED': break
        if st.get('status_code') == 'ERROR': sys.exit(f'Instagram could not process {mp4.name}: {st}')
        time.sleep(10)
    pub = call('POST', f'{base}/media_publish', {'creation_id': box['id']}, auth)
    return pub['id']


def post_facebook(mp4: Path, caption: str, key: str) -> str:
    c = creds('meta'); url = stage(mp4, key)
    base = f"https://graph.facebook.com/{GRAPH}/{c['page_id']}/video_reels"
    tok = {'access_token': c['page_access_token']}
    start = call('POST', base, {'upload_phase': 'start', **tok})
    vid = start.get('video_id', 'dry-run')
    call('POST', f'https://rupload.facebook.com/video-upload/{GRAPH}/{vid}', None,
         {'Authorization': f"OAuth {c['page_access_token']}", 'file_url': url}, b'')
    call('POST', base, {'upload_phase': 'finish', 'video_id': vid, 'video_state': 'PUBLISHED', 'description': caption, **tok})
    return vid


def post_tiktok_draft(mp4: Path) -> str:
    """Upload to the account's TikTok inbox; Kris adds the caption and posts it in the app (until the audit allows
    direct public posts)."""
    c = creds('tiktok'); size = mp4.stat().st_size
    auth = {'Authorization': f"Bearer {c['access_token']}", 'Content-Type': 'application/json; charset=UTF-8'}
    init = call('POST', f'{TIKTOK}/post/publish/inbox/video/init/', None, auth,
                json.dumps({'source_info': {'source': 'FILE_UPLOAD', 'video_size': size, 'chunk_size': size, 'total_chunk_count': 1}}).encode())
    up = init.get('data', {})
    if not DRY:
        call('PUT', up['upload_url'], None, {'Content-Type': 'video/mp4', 'Content-Range': f'bytes 0-{size - 1}/{size}',
                                             'Content-Length': str(size)}, mp4.read_bytes())
    else:
        print(f'DRY PUT <upload_url> {mp4.name} {size} bytes')
    return up.get('publish_id', 'dry-run')


def main() -> int:
    global DRY
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('where', choices=('ig', 'fb', 'tiktok', 'all', 'check'))
    ap.add_argument('short_dir', nargs='?', help='<dest>/short: <slug>-short-social.mp4 and social-caption.txt')
    ap.add_argument('--dry-run', action='store_true')
    o = ap.parse_args(); DRY = o.dry_run
    if o.where == 'check':
        for n in ('meta', 'tiktok'):
            p = CONF / f'{n}.json'
            print(n, 'ok' if p.exists() and json.loads(p.read_text()) else 'MISSING', p)
        return 0
    d = Path(o.short_dir); slug = d.parent.name
    mp4 = d / f'{slug}-short-social.mp4'; cap = (d / 'social-caption.txt').read_text().strip()
    if not mp4.exists(): sys.exit(f'no {mp4}: make it with short_film.py --social first')
    done_p = d / 'posted.json'; done = json.loads(done_p.read_text()) if done_p.exists() else {}
    key = f'{slug}-short-{int(mp4.stat().st_mtime)}.mp4'
    for w in (('ig', 'fb', 'tiktok') if o.where == 'all' else (o.where,)):
        if done.get(w): print(f'{w}: already posted ({done[w]})'); continue
        pid = post_instagram(mp4, cap, key) if w == 'ig' else post_facebook(mp4, cap, key) if w == 'fb' else post_tiktok_draft(mp4)
        print(f'{w}: {pid}')
        if not DRY:
            done[w] = pid; done_p.write_text(json.dumps(done, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())

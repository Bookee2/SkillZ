#!/usr/bin/env python3
"""Read or rewrite one video's snippet on @trailgoatrun, for race_year.py (which runs in the TrailGoat venv, where
the Google client isn't installed).

    ~/.config/trailgoat-youtube/venv/bin/python yt_video.py get VIDEO_ID               # snippet + status, as JSON
    ~/.config/trailgoat-youtube/venv/bin/python yt_video.py set VIDEO_ID snippet.json  # videos.update, then read back

`set` sends the title, description, tags, category and languages it's given, so a snippet read with `get` and
changed goes back whole (videos.update clears whatever part=snippet leaves out, tags included). The credentials are
yt_upload.py's (marketing/youtube in the TrailGoat checkout, or TG_YT_UPLOAD); nothing of them is printed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

YT = Path(os.environ.get('TG_YT_UPLOAD', Path.home() / 'Desktop/Projects/TrailGoat/marketing/youtube/yt_upload.py'))
sys.path.insert(0, str(YT.parent))
import yt_upload  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

SENT = ('title', 'description', 'tags', 'categoryId', 'defaultLanguage', 'defaultAudioLanguage')


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ('get', 'set') or (sys.argv[1] == 'set' and len(sys.argv) != 4):
        sys.exit(__doc__)
    cmd, vid = sys.argv[1], sys.argv[2]
    yt = build('youtube', 'v3', credentials=yt_upload.creds())
    items = yt.videos().list(part='snippet,status', id=vid).execute().get('items', [])
    if not items: sys.exit(f'{vid}: not a video on the channel')
    if cmd == 'get':
        print(json.dumps(dict(snippet=items[0]['snippet'], status=items[0]['status']), ensure_ascii=False)); return 0
    sn = json.loads(Path(sys.argv[3]).read_text())
    yt.videos().update(part='snippet', body={'id': vid, 'snippet': {k: sn[k] for k in SENT if k in sn}}).execute()
    back = yt.videos().list(part='snippet', id=vid).execute()['items'][0]['snippet']
    ok = back['title'] == sn['title'] and back['description'].strip() == sn['description'].strip() and back.get('tags') == sn.get('tags')
    print(json.dumps(dict(title=back['title'], ok=ok), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

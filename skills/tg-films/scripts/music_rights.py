"""Which recordings a film or Short may carry, now that they go to Instagram, Facebook and TikTok as well as YouTube.

Kris, 2026-11-02: "Lets switch all of it, except leave the films on youtube as they are, so youtube switches moving
forward." Every new film and Short uses a recording cleared everywhere:
- anything in Music/public-domain/ (Musopen, US federal bands, Commons PD/CC0; LICENSES.md there has each source); or
- an audio-library track whose row in Music/audio-library/LICENSES.md says CC BY (Kevin MacLeod, with its credit).
YouTube Audio Library tracks are YouTube-only: the 64 films already up keep theirs, and anything new built from those
films (a Short, an off-YouTube copy) takes the same piece's cleared recording from Music/public-domain/MAP.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MUSIC = Path('/Volumes/KB SS/TrailGoat-Studio/Music')
PD, LIB = MUSIC / 'public-domain', MUSIC / 'audio-library'


def cleared(path: str) -> bool:
    p = Path(path or '')
    if PD in p.parents: return True
    if LIB in p.parents:
        lic = (LIB / 'LICENSES.md').read_text() if (LIB / 'LICENSES.md').exists() else ''
        rows = [ln for ln in lic.splitlines() if p.name in ln or p.stem in ln]
        return bool(rows) and all(re.search(r'CC BY\b', ln) for ln in rows)
    return False


def cleared_music(m: dict, slug: str | None = None) -> dict | None:
    """The film's music block if its recording is cleared everywhere, else the same piece's cleared recording from
    MAP.json (its own start for the same passage, title, artist and credit), else None. Films that began the old file
    at different points have their own start under the entry's "starts" ({slug: seconds}), e.g. the Ninth for
    Shinetsu (12.2 s) and Tor des Géants (130 s)."""
    if not m or not m.get('file'): return m
    if cleared(m['file']): return m
    try:
        mp = json.loads((PD / 'MAP.json').read_text()).get(Path(m['file']).name) or {}
    except OSError:
        mp = {}
    if not mp.get('file'): return None
    start = (mp.get('starts') or {}).get(slug, mp.get('start'))
    return {**m, 'file': mp['file'], 'start': float(start or 0), 'title': mp.get('title') or m.get('title'),
            'artist': mp.get('artist') or m.get('artist'), 'credit': mp.get('credit', '')}

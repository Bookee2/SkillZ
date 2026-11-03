#!/usr/bin/env python3
"""Lengthen a classical track that's shorter than its film by playing one of its phrases once more.

    extend_track.py find   <track.mp3> [--theme 0.7] [--len 8]
    extend_track.py loops  <track.mp3> <min add s> <max add s> [--max-b S]
    extend_track.py splice <track.mp3> <out.wav> --at A --again B

find lists where the opening theme comes back (chroma match), with how alike the 1.5 s before each return
sounds and the level either side. Pick two returns whose lead-ins match (similarity ~0.98+): playing the music
up to the later one and then again from the earlier one repeats the phrase between them, like taking a repeat
once more. Then pin both to the same note: run splice with rough times, read the note list it prints, and rerun
with the onset of the same note (the theme's first note) at each return.

loops searches the whole track, not only the opening theme: for every jump length between min and max add it finds
the a..b where the 3 s either side of a sound like the 3 s either side of b (chroma, and level), keeping the last 20 s
(the ending) whole. Splice its a and b as --at and --again. Chroma 0.95+ is a literal repeat (National Emblem's strain
0.996); ~0.87 is the same harmony in a new scoring (a band's next verse). Then read splice's rhythm (the gaps across
the join should look like the gaps either side) and click numbers (both at or under the local percentiles). To add
more than one loop's length, splice the result again at the same a and b: each pass plays a..b once more. Batch 6
(2026-11-03): nine tracks, e.g. Mountain King's quiet opening build (15.28-50.99 s) three times for Chiang Dao.

splice writes out.wav = track[0 : B] + track[A : end], cut 25 ms before the onsets with a 20 ms equal-power
crossfade, and checks the join: the notes either side, the gaps between them, high-frequency (click) energy
at the join against the median, and the largest sample step. Für Elise for Grayson Highlands 50K
(2026-10-28): --at 25.525 --again 40.991 added 15.47 s, with no click and gaps within the pianist's own
rubato; Kris passed the join. Listen to the join before it goes up, or send Kris a clip of it.

Needs numpy and imageio-ffmpeg (the TrailGoat venv).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

REPO = os.environ.get('TRAILGOAT_REPO', os.path.expanduser('~/Desktop/Projects/TrailGoat'))
PY = os.environ.get('TRAILGOAT_PY', os.path.join(REPO, '.venv/bin/python'))
# numpy and imageio-ffmpeg live in the TrailGoat venv: run there, whatever python started this
if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('TG_FILMS_REEXEC'):
    os.environ['TG_FILMS_REEXEC'] = '1'
    os.execv(PY, [PY, __file__, *sys.argv[1:]])

import numpy as np  # noqa: E402

SR = 44100
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def load(path: str) -> np.ndarray:
    raw = subprocess.run([ffmpeg(), '-loglevel', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def chroma_frames(x: np.ndarray, hop: int = 1024, n: int = 4096) -> np.ndarray:
    win = np.hanning(n); frames = 1 + (len(x) - n) // hop
    f = np.fft.rfftfreq(n, 1 / SR); m = (f > 60) & (f < 4000)
    pc = (np.round(12 * np.log2(f[m] / 440)) % 12).astype(int)
    C = np.zeros((frames, 12))
    for i in range(frames):
        S = np.abs(np.fft.rfft(win * x[i*hop:i*hop+n]))[m]
        C[i] = np.bincount(pc, weights=S, minlength=12)
    return C / (np.linalg.norm(C, axis=1, keepdims=True) + 1e-9)


def chroma(x: np.ndarray, t0: float, t1: float, n: int = 4096) -> np.ndarray:
    seg = x[int(t0*SR):int(t1*SR)]; k = len(seg) // n
    S = np.abs(np.fft.rfft(seg[:k*n].reshape(-1, n) * np.hanning(n), axis=1)).sum(0)
    f = np.fft.rfftfreq(n, 1 / SR); m = (f > 60) & (f < 4000)
    c = np.bincount((np.round(12 * np.log2(f[m] / 440)) % 12).astype(int), weights=S[m], minlength=12)
    return c / np.linalg.norm(c)


def rms(x: np.ndarray, a: float, b: float) -> float:
    return float(np.sqrt(np.mean(x[int(a*SR):int(b*SR)] ** 2)))


def onsets(x: np.ndarray, t0: float, t1: float, hop: int = 128, n: int = 1024) -> list[float]:
    a = int(max(0.0, t0) * SR); seg = x[a:int(t1*SR)]; w = np.hanning(n)  # a window that starts before 0 s
    F = np.array([np.abs(np.fft.rfft(w * seg[i:i+n])) for i in range(0, len(seg) - n, hop)])
    fl = np.maximum(np.log1p(100*F[1:]) - np.log1p(100*F[:-1]), 0).sum(1)
    t = a/SR + (np.arange(len(fl)) + 1)*hop/SR + n/2/SR; thr = 0.35 * fl.max(); out: list[float] = []
    for j in range(2, len(fl) - 2):
        if fl[j] == fl[j-2:j+3].max() and fl[j] > thr and (not out or t[j] - out[-1] > 0.07):
            out.append(float(t[j]))
    return out


def note(x: np.ndarray, t: float, N: int = 8192) -> str:
    """The note that starts at t: the strongest new partial between 400 and 1400 Hz (the melody's register)."""
    f = np.fft.rfftfreq(N, 1 / SR)
    S = np.abs(np.fft.rfft(x[int((t+0.01)*SR):int((t+0.01)*SR)+N] * np.hanning(N)))
    p = int(max(0.0, t - 0.12) * SR)
    pre = np.abs(np.fft.rfft(x[p:p+N] * np.hanning(N)))
    k = int(np.argmax(np.maximum(S - 0.8*pre, 0) * ((f > 400) & (f < 1400))))
    mi = int(round(69 + 12 * np.log2(f[k] / 440)))
    return f'{NAMES[mi % 12]}{mi // 12 - 1}'


def show(x: np.ndarray, t0: float, t1: float) -> list[float]:
    on = onsets(x, t0, t1)
    print('  ' + ' '.join(f'{o:.3f}:{note(x, o)}' for o in on))
    return on


def find(a) -> None:
    X = load(a.track); x = X.mean(1); hop = 1024; fps = SR / hop
    C = chroma_frames(x, hop); s0 = int(a.theme * fps); L = int(a.len * fps); T = C[s0:s0+L]
    scores = sorted(((float((C[s:s+L] * T).sum() / L), s / fps) for s in range(s0 + int(4*fps), len(C) - L)), reverse=True)
    picks: list[tuple[float, float]] = []
    for sc, t in scores:
        if sc < 0.75 or len(picks) >= 10: break
        if all(abs(t - u) > 3 for _, u in picks): picks.append((sc, t))
    picks.sort(key=lambda p: p[1])
    pre = [chroma(x, t - 1.5, t - 0.05) for _, t in picks]
    print(f'{len(x)/SR:.2f} s; the theme from {a.theme} s comes back at:')
    print('  time    match  level before/after   lead-in alike (each other return)')
    for i, (sc, t) in enumerate(picks):
        alike = ' '.join(f'{float(pre[i] @ pre[j]):.2f}' for j in range(len(picks)))
        print(f'  {t:6.2f}  {sc:.3f}   {rms(x, t-2, t):.3f} / {rms(x, t, t+4):.3f}      {alike}')
    print('gap between neighbours: ' + ', '.join(f'{picks[i+1][1]-picks[i][1]:.2f}' for i in range(len(picks) - 1)))


def splice(a) -> None:
    X = load(a.track); x = X.mean(1)
    d = 0.025; xf = int(0.020 * SR)
    c2 = int((a.again - d) * SR); c1 = int((a.at - d) * SR)
    head = X[:c2 + xf]; tail = X[c1:]
    g = np.linspace(0, np.pi/2, xf)[:, None]
    Y = np.concatenate([head[:-xf], head[-xf:]*np.cos(g) + tail[:xf]*np.sin(g), tail[xf:]]).astype(np.float32)
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-',
                    '-c:a', 'pcm_s16le', a.out], input=Y.tobytes(), check=True)
    y = Y.mean(1); J = c2 / SR
    print(f'{a.out}: {len(X)/SR:.2f} s -> {len(Y)/SR:.2f} s (+{(len(Y)-len(X))/SR:.2f}); join at {J:.3f} s')
    print(f'notes before --again in the original ({a.again} s):'); show(x, a.again - 0.9, a.again + 0.9)
    print(f'notes from --at in the original ({a.at} s):'); show(x, a.at - 0.9, a.at + 0.9)
    print('notes across the join in the result:'); on = show(y, J - 1.0, J + 1.6)
    print('  gaps (ms): ' + ' '.join(str(int(1000*v)) for v in np.diff(on)))
    seg = y[int((J-1)*SR):int((J+1)*SR)]; S = np.fft.rfft(seg); f = np.fft.rfftfreq(len(seg), 1/SR); S[f < 5000] = 0
    h = np.fft.irfft(S, len(seg)); fr = int(0.002 * SR)
    e = np.array([np.sum(h[i:i+fr] ** 2) for i in range(0, len(h) - fr, fr)]); k = len(e) // 2
    step = np.abs(np.diff(y[int((J-0.05)*SR):int((J+0.05)*SR)])).max()
    print(f'click check: HF energy at the join {e[k-3:k+4].max():.1e} (median {np.median(e):.1e}, 95th pct '
          f'{np.percentile(e, 95):.1e}); largest sample step {step:.4f} (99.9th pct over ±1 s '
          f'{np.percentile(np.abs(np.diff(seg)), 99.9):.4f})')


def loops(a) -> None:
    X = load(a.track); x = X.mean(1); hop = 2048; fps = SR / hop
    C = chroma_frames(x, hop, 8192); n = len(C)
    lr = np.log10(np.array([np.sqrt(np.mean(x[i*hop:i*hop+8192] ** 2)) for i in range(n)]) + 1e-4)
    W = int(3 * fps); k = np.ones(2*W + 1) / (2*W + 1); res = []
    for L in range(max(1, int(a.min_add * fps)), min(int(a.max_add * fps), n - 2*W)):
        m = np.convolve((C[:-L] * C[L:]).sum(1), k, 'same'); ml = np.convolve(np.abs(lr[:-L] - lr[L:]), k, 'same')
        s = m - 0.5 * ml; b = np.arange(len(s)) + L
        s[:W + int(2*fps)] = -9; s[-W:] = -9; s[(b > n - int(20*fps)) | (b > a.max_b * fps)] = -9
        i = int(np.argmax(s)); res.append((float(s[i]), float(m[i]), float(ml[i]), i / fps, (i + L) / fps))
    print(f'{len(x)/SR:.1f} s; loops that add {a.min_add:g}-{a.max_add:g} s:')
    seen: list[float] = []
    for sc, mm, ml, s0, s1 in sorted(res, reverse=True):
        if any(abs((s1 - s0) - u) < 3 for u in seen): continue
        seen.append(s1 - s0)
        print(f'  --at {s0:7.2f} --again {s1:7.2f}  adds {s1-s0:6.2f}  chroma {mm:.3f}  level diff {ml:.3f}')
        if len(seen) >= 6: break


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('find'); f.add_argument('track'); f.add_argument('--theme', type=float, default=0.7)
    f.add_argument('--len', type=float, default=8.0)
    lp = sub.add_parser('loops'); lp.add_argument('track'); lp.add_argument('min_add', type=float); lp.add_argument('max_add', type=float)
    lp.add_argument('--max-b', type=float, default=1e9, help='keep the jump before this time (e.g. inside a slow opening)')
    s = sub.add_parser('splice'); s.add_argument('track'); s.add_argument('out')
    s.add_argument('--at', type=float, required=True, help='the earlier return: the onset the music jumps back to')
    s.add_argument('--again', type=float, required=True, help='the later return: the onset where it jumps back')
    a = ap.parse_args()
    {'find': find, 'loops': loops, 'splice': splice}[a.cmd](a)
    return 0


if __name__ == '__main__':
    sys.exit(main())

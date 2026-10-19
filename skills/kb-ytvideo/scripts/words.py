"""SRT/VTT -> estimated word timestamps (spreads each cue across its characters; ~0.2s accuracy).
Prefer transcribe.py, which gives real word times from the audio.
usage: python3 words.py transcript.srt > words.txt      (tokens 'start-end:word', one line per cue)"""
import sys, re
def ts(x):
    x = x.strip().split(' ')[0]; p = x.replace('.', ',').split(':'); p = ['0'] * (3 - len(p)) + p
    s, ms = p[2].split(','); return int(p[0]) * 3600 + int(p[1]) * 60 + int(s) + int(ms) / 1000
for blk in re.split(r'\n\s*\n', open(sys.argv[1], encoding='utf-8').read().strip()):
    L = [l for l in blk.strip().split('\n') if l.strip()]
    i = next((k for k, l in enumerate(L) if '-->' in l), None)
    if i is None or i + 1 >= len(L): continue
    a, b = [ts(x) for x in L[i].split('-->')]; words = ' '.join(L[i + 1:]).split(); n = sum(len(w) + 1 for w in words); c = 0; out = []
    for w in words:
        s = a + (b - a) * c / n; c += len(w) + 1; out.append(f'{s:.2f}-{a + (b - a) * c / n:.2f}:{w}')
    print(' '.join(out))

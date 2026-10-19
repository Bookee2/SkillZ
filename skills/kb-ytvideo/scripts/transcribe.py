"""Local speech-to-text with word timestamps (faster-whisper; nothing leaves the machine after the one-time model download).
usage: $PY transcribe.py media.(mp4|mov|wav|m4a) out_dir [--model small.en] [--lang en] [--prompt "TrailGoat, ultra, aid station"]
Writes out_dir/words.txt (one line per segment, tokens 'start-end:word'), out_dir/transcript.srt and out_dir/transcript.txt.
Word times are accurate to roughly ±0.05–0.1 s, far better than words.py's SRT estimates."""
import argparse, pathlib
from faster_whisper import WhisperModel
ap = argparse.ArgumentParser(); ap.add_argument('media'); ap.add_argument('out')
ap.add_argument('--model', default='small.en'); ap.add_argument('--lang', default='en'); ap.add_argument('--prompt', default=None)
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
model = WhisperModel(a.model, device='cpu', compute_type='int8')
segs, info = model.transcribe(a.media, language=a.lang, word_timestamps=True, vad_filter=True, initial_prompt=a.prompt)
def srt_t(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f'{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)):03}'
W, S, T = [], [], []
for i, s in enumerate(segs, 1):
    W.append(' '.join(f'{w.start:.2f}-{w.end:.2f}:{w.word.strip()}' for w in (s.words or []) if w.word.strip()))
    S.append(f'{i}\n{srt_t(s.start)} --> {srt_t(s.end)}\n{s.text.strip()}\n'); T.append(s.text.strip())
(out / 'words.txt').write_text('\n'.join(W) + '\n'); (out / 'transcript.srt').write_text('\n'.join(S)); (out / 'transcript.txt').write_text('\n'.join(T) + '\n')
print(f'wrote {out}/words.txt, transcript.srt, transcript.txt ({len(S)} segments, {info.duration:.1f}s audio)')

#!/usr/bin/env python3
"""Render TrailGoat's YouTube end card for one race-flyover film.

usage:
  python3 render_end_card.py --race "Leadville Trail 100" \
      --next "Cocodona 250: 253 miles in 3D" --out /path/out.mp4 [--work "$WORK"] [--keep]

Substitutes {{RACE}} and {{NEXT}} into a temp copy of assets/end-card.html, builds it with the
kb-ytvideo engine (build.py --brand trailgoat), renders it with render.js at 24 fps (to match the
Blender films), then checks the file is 15.0 s ± 0.05, 1920×1080, 24 fps, and only then moves it
to --out. Any failure exits non-zero with a message.

Toolchain paths (env overrides): KB_YTVIDEO_SKILL (the kb-ytvideo skill folder),
KB_YTVIDEO_WORK (the job folder whose node_modules holds Playwright), KB_YTVIDEO_PY (the venv
python used to run build.py; falls back to this interpreter). node, ffmpeg and ffprobe come from PATH.
"""
import argparse, html, json, os, pathlib, re, shutil, subprocess, sys, tempfile

SKILL = pathlib.Path(os.environ.get('KB_YTVIDEO_SKILL', '~/.claude/skills/kb-ytvideo')).expanduser()
WORK = pathlib.Path(os.environ.get('KB_YTVIDEO_WORK', '~/Movies/TrailGoat Launch/motion')).expanduser()
PY = pathlib.Path(os.environ.get('KB_YTVIDEO_PY', '~/Library/Application Support/kb-ytvideo/venv/bin/python')).expanduser()
FRAGMENT = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'end-card.html'
BRAND = 'trailgoat'
FPS = 24
DURATION, TOLERANCE = 15.0, 0.05
SIZE = (1920, 1080)


def die(msg, code=2):
    print(f'render_end_card: {msg}', file=sys.stderr)
    sys.exit(code)


def run(cmd, **kw):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], text=True, capture_output=True, **kw)
    if r.stdout.strip(): print(r.stdout.rstrip())
    if r.stderr.strip(): print(r.stderr.rstrip(), file=sys.stderr)
    if r.returncode: die(f'{cmd[0]} failed with exit code {r.returncode}')
    return r


def probe(path):
    """Return (duration_s, width, height, fps, nb_frames) via ffprobe, or ffmpeg -i as a fallback."""
    if shutil.which('ffprobe'):
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                            'stream=width,height,r_frame_rate,nb_frames:format=duration', '-of', 'json', str(path)],
                           text=True, capture_output=True)
        if r.returncode: die(f'ffprobe failed: {r.stderr.strip()}')
        j = json.loads(r.stdout); s = j['streams'][0]
        num, den = s['r_frame_rate'].split('/')
        return float(j['format']['duration']), int(s['width']), int(s['height']), float(num) / float(den), int(s.get('nb_frames') or 0)
    r = subprocess.run(['ffmpeg', '-i', str(path)], text=True, capture_output=True)
    d = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', r.stderr)
    v = re.search(r'Video:.*?(\d{3,5})x(\d{3,5}).*?(\d+(?:\.\d+)?) fps', r.stderr)
    if not d or not v: die(f'could not probe {path}: {r.stderr.strip()[-300:]}')
    return int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3]), int(v[1]), int(v[2]), float(v[3]), 0


def verify(path):
    dur, w, h, fps, n = probe(path)
    problems = []
    if abs(dur - DURATION) > TOLERANCE: problems.append(f'duration {dur:.3f} s, wanted {DURATION} ± {TOLERANCE}')
    if (w, h) != SIZE: problems.append(f'size {w}×{h}, wanted {SIZE[0]}×{SIZE[1]}')
    if abs(fps - FPS) > 0.01: problems.append(f'fps {fps:g}, wanted {FPS}')
    if n and n != round(DURATION * FPS): problems.append(f'{n} frames, wanted {round(DURATION * FPS)}')
    if problems: die('rendered file failed verification: ' + '; '.join(problems))
    return dur, w, h, fps, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--race', required=True, help='this film\'s race, e.g. "Leadville Trail 100"')
    ap.add_argument('--next', required=True, dest='next_title', help='the next film\'s title (up to ~40 characters reads best)')
    ap.add_argument('--out', required=True, help='output .mp4 path')
    ap.add_argument('--work', help=f'kb-ytvideo job folder with node_modules (default {WORK})')
    ap.add_argument('--keep', action='store_true', help='keep the temp build folder and print its path')
    a = ap.parse_args()

    work = pathlib.Path(a.work).expanduser() if a.work else WORK
    build_py, render_js = SKILL / 'engine' / 'build.py', SKILL / 'engine' / 'render.js'
    node_modules = work / 'node_modules'
    for p, what in [(FRAGMENT, 'fragment'), (build_py, 'build.py'), (render_js, 'render.js'),
                    (node_modules / 'playwright', 'Playwright (run kb-ytvideo/scripts/setup.sh "$WORK")')]:
        if not p.exists(): die(f'{what} not found at {p}')
    for tool in ('node', 'ffmpeg'):
        if not shutil.which(tool): die(f'{tool} not on PATH')
    py = PY if PY.exists() else pathlib.Path(sys.executable)
    out = pathlib.Path(a.out).expanduser()
    if out.suffix.lower() != '.mp4': die('--out must end in .mp4 (the card is opaque; render.js writes H.264)')
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='tg-end-card-'))
    try:
        clips, dist = tmp / 'clips', tmp / 'dist'
        clips.mkdir(); dist.mkdir()
        src = FRAGMENT.read_text(encoding='utf-8')
        for key in ('{{RACE}}', '{{NEXT}}'):
            if key not in src: die(f'placeholder {key} missing from {FRAGMENT}')
        frag = src.replace('{{RACE}}', html.escape(a.race)).replace('{{NEXT}}', html.escape(a.next_title))
        clip = clips / 'end-card.html'
        clip.write_text(frag, encoding='utf-8')

        run([py, build_py, dist, clip, '--brand', BRAND])
        built = dist / 'end-card.html'
        if not built.exists(): die(f'build.py produced no {built}')

        rendered = tmp / 'end-card.mp4'
        env = dict(os.environ, NODE_PATH=str(node_modules))
        r = run(['node', render_js, built, rendered, str(FPS)], env=env)
        if 'ERR' in r.stdout: die(f'render.js reported a page error: {r.stdout.strip()}')
        if not rendered.exists() or rendered.stat().st_size == 0: die('render.js produced no file')

        dur, w, h, fps, n = verify(rendered)
        shutil.move(str(rendered), str(out))
        print(f'ok {out}  {dur:.3f} s  {w}x{h}  {fps:g} fps  {n or "?"} frames  '
              f'race="{a.race}" next="{a.next_title}"')
    finally:
        if a.keep: print(f'kept {tmp}')
        else: shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()

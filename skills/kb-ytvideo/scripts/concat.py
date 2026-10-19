"""Join segments into one upload-ready file: e.g. intro sting + composited take + end screen.
usage: python3 concat.py out.mp4 seg1.mp4 seg2.mp4 ... [--size 1920x1080] [--fps 30] [--fade 0.25]
Every segment is scaled/padded to one size and frame rate. Segments without audio get silence, so the soundtrack stays in sync.
--fade adds a short fade from/to black at each join (0 = hard cuts)."""
import argparse, json, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('segs', nargs='+')
ap.add_argument('--size', default='1920x1080'); ap.add_argument('--fps', default='30'); ap.add_argument('--fade', type=float, default=0.0)
a = ap.parse_args(); W, H = a.size.split('x')
def probe(f):
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', f], capture_output=True, text=True).stdout)
    return float(p['format']['duration']), any(s['codec_type'] == 'audio' for s in p['streams'])
cmd = ['ffmpeg', '-loglevel', 'error', '-y']; fc = []; n = len(a.segs)
for f in a.segs: cmd += ['-i', f]
for i, f in enumerate(a.segs):
    d, has_a = probe(f); fd = a.fade
    fades = (f',fade=t=in:st=0:d={fd}' if fd and i > 0 else '') + (f',fade=t=out:st={max(0, d - fd):.3f}:d={fd}' if fd and i < n - 1 else '')
    fc.append(f'[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,fps={a.fps},format=yuv420p,setsar=1{fades}[v{i}]')
    fc.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]' if has_a else f'anullsrc=r=48000:cl=stereo,atrim=0:{d:.3f}[a{i}]')
fc.append(''.join(f'[v{i}][a{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[v][a]')
cmd += ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', a.out]
subprocess.run(cmd, check=True); print('wrote', a.out)

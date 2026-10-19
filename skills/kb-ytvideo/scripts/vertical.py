"""Turn a 16:9 take (an OBS screen recording) into a 9:16 (or 4:5) base video for Shorts, Reels and TikTok.
usage: python3 vertical.py take.mp4 out.mp4 [--size 1080x1920] [--from 12.5 --to 58] [--mode stack|crop]
        [--y 560] [--zoom 1.0] [--focus 0.5] [--bg brand|topo|#1a1b26] [--brand trailgoat] [--fps 30]
stack (default): the whole take, scaled to the frame width (zoom > 1 enlarges it and crops the sides around --focus),
  sits at --y on a brand ground. The bands above and below are free for a headline panel and captions.
crop: a full-height slice of the take around --focus (0 = left, 1 = right), scaled up. Screen text gets soft; use for
  camera footage, not UI.
Writes out.mp4 (H.264, original audio) and out.layout.json with the take box and the free bands, for planning panels."""
import argparse, json, pathlib, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--size', default='1080x1920'); ap.add_argument('--from', dest='t0', type=float, default=None); ap.add_argument('--to', dest='t1', type=float, default=None)
ap.add_argument('--mode', default='stack', choices=['stack', 'crop']); ap.add_argument('--y', type=int, default=None)
ap.add_argument('--zoom', type=float, default=1.0); ap.add_argument('--focus', type=float, default=0.5)
ap.add_argument('--bg', default='topo'); ap.add_argument('--brand', default='trailgoat'); ap.add_argument('--fps', default=None)
a = ap.parse_args(); W, H = map(int, a.size.split('x'))
SK = pathlib.Path(__file__).resolve().parent.parent; bd = SK / 'brands' / a.brand
brand = json.load(open(bd / 'brand.json')) if (bd / 'brand.json').exists() else {'colors': {'canvas': '#1a1b26'}, 'assets': {}}
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', a.src], capture_output=True, text=True).stdout)
vs = next(s for s in pr['streams'] if s['codec_type'] == 'video'); sw, sh = int(vs['width']), int(vs['height'])
fps = a.fps or vs['r_frame_rate']
cmd = ['ffmpeg', '-loglevel', 'error', '-y']
if a.t0 is not None: cmd += ['-ss', str(a.t0)]
if a.t1 is not None: cmd += ['-to', str(a.t1)]
cmd += ['-i', a.src]
bgcol = a.bg if a.bg.startswith('#') else brand['colors']['canvas']
topo_key = 'topo-9x16' if H / W > 1.5 else None
use_topo = a.bg == 'topo' and topo_key and topo_key in brand.get('assets', {})
if use_topo: cmd += ['-loop', '1', '-i', str(bd / brand['assets'][topo_key])]
layout = {'size': [W, H], 'mode': a.mode, 'source': [sw, sh]}
if a.mode == 'stack':
    tw = int(W * a.zoom) // 2 * 2; th = int(sh * tw / sw) // 2 * 2
    cx = int(max(0, min(tw - W, (tw - W) * a.focus))) if tw > W else 0
    vw = min(tw, W); y = a.y if a.y is not None else int(H * 0.29) // 2 * 2
    fg = f'[0:v]scale={tw}:{th}:flags=lanczos,crop={vw}:{th}:{cx}:0[fg]'
    ground = f'[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},format=yuv420p[bg]' if use_topo else f'color=c={bgcol}:s={W}x{H}:r={fps}[bg]'
    fc = f'{ground};{fg};[bg][fg]overlay=x=(W-w)/2:y={y}:shortest=1,fps={fps},format=yuv420p[v]'
    layout.update({'take_box': [(W - vw) // 2, y, (W + vw) // 2, y + th], 'free_bands': [[0, 0, W, y], [0, y + th, W, H]]})
else:
    cw = int(sh * W / H) // 2 * 2; cx = int((sw - cw) * a.focus)
    fc = f'[0:v]crop={cw}:{sh}:{cx}:0,scale={W}:{H}:flags=lanczos,fps={fps},format=yuv420p[v]'
    layout.update({'take_box': [0, 0, W, H], 'free_bands': [], 'crop_x': cx})
cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', a.out]
subprocess.run(cmd, check=True)
lp = pathlib.Path(a.out).with_suffix('.layout.json'); lp.write_text(json.dumps(layout, indent=1)); print('wrote', a.out, 'and', lp); print(json.dumps(layout))

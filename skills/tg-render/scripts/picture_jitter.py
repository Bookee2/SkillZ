"""Image-space jitter of a rendered film: global shift between consecutive distinct frames (phase correlation), split
into the smooth pan (1.5 s average) and the jitter left over, in pixels at 320 wide.

    <TrailGoat>/.venv/bin/python picture_jitter.py video.mp4 t0 t1 step      (needs numpy; step = frames per distinct render frame)

"big jolts" counts steps more than 3 px off the smooth pan: Quest 2026-10-27, 4 in 85 s at 24 fps, 37 shown every 4th frame."""
import subprocess, sys, numpy as np
v, t0, t1, step = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
W, H = 320, 180
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-to', str(t1), '-i', v, '-vf', f'scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)[::step]
win = np.outer(np.hanning(H), np.hanning(W))
def shift(a, b):
    A, B = np.fft.fft2((a - a.mean()) * win), np.fft.fft2((b - b.mean()) * win); R = A * np.conj(B); R /= np.abs(R) + 1e-9
    r = np.abs(np.fft.ifft2(R)); y, x = np.unravel_index(r.argmax(), r.shape)
    return (x if x < W // 2 else x - W), (y if y < H // 2 else y - H)
s = np.array([shift(fr[i - 1], fr[i]) for i in range(1, len(fr))], float)
k = max(3, int(round(1.5 * 24 / step)))
sm = np.array([s[max(0, i - k // 2):i + k // 2 + 1].mean(0) for i in range(len(s))])
res = s - sm
print(f'{v.split("/")[-1][:40]:40s} steps {len(s)}  pan rms {np.sqrt((s**2).mean(0)).round(2)}  jitter rms x,y {np.sqrt((res**2).mean(0)).round(2)}  big jolts(>3px) {int((np.abs(res) > 3).any(1).sum())}')

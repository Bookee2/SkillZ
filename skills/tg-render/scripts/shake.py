"""Camera shake in numbers, from render.py --export-cam's per-frame poses.

    python3 shake.py cam.json [cam.json …]

For each film: the view's turning rate (yaw and tilt of camera->target, deg/s) frame by frame, split into the slow turn
(a 1.5 s moving average) and the wobble left over. 'wobble' is the RMS of that leftover over the follow legs (deg/s);
'flips' counts turning-rate reversals a second (|rate| > 1.5 deg/s both sides) over the legs: a camera rocking back and
forth on switchbacks. 'drift' is the same for the camera's sideways slide, as a share of the follow distance per second.
Wild Florida and Cloudland, approved, are the reference."""
import json, math, sys

def ma(xs, k):
    h = k // 2; out = []
    for i in range(len(xs)):
        w = xs[max(0, i - h):i + h + 1]; out.append(sum(w) / len(w))
    return out

def film(path):
    c = json.load(open(path)); fps = c['fps']; fr = c['cam']; shots = c['shots']
    legs = [s for s in shots if not any(w in s['name'].upper() for w in ('WHOLE COURSE', 'INTO ', 'START', 'FINISH', 'BACK OUT'))]
    yaw, tilt, slide = [], [], []
    for f in fr:
        (cx, cy, cz), (tx, ty, tz) = f['cam'], f['tgt']
        dx, dy, dz = tx - cx, ty - cy, tz - cz; yaw.append(math.degrees(math.atan2(dy, dx))); tilt.append(math.degrees(math.atan2(dz, math.hypot(dx, dy))))
    def rate(a):
        r = [0.0]
        for i in range(1, len(a)):
            d = a[i] - a[i - 1]; d = (d + 180) % 360 - 180; r.append(d * fps)
        return r
    ry, rt = rate(yaw), rate(tilt)
    res = []
    for s in legs:
        f0, f1 = s['f']; i0, i1 = f0 - 1 + 2, f1 - 2                           # skip the cut frames
        if i1 - i0 < fps: continue
        y = ry[i0:i1]; t = rt[i0:i1]; ys, ts = ma(y, int(fps * 1.5)), ma(t, int(fps * 1.5))
        wob = math.sqrt(sum((a - b) ** 2 + (p - q) ** 2 for a, b, p, q in zip(y, ys, t, ts)) / len(y))
        flips = sum(1 for i in range(1, len(y)) if y[i - 1] > 1.5 and y[i] < -1.5 or y[i - 1] < -1.5 and y[i] > 1.5)
        # sideways slide of the camera relative to its own heading, normalised by the camera-target ground distance
        sl = []
        for i in range(i0 + 1, i1):
            (ax, ay, _), (bx, by, _) = fr[i - 1]['cam'], fr[i]['cam']; (tx, ty, _) = fr[i]['tgt']
            hx, hy = tx - bx, ty - by; L = math.hypot(hx, hy) or 1; sl.append(((bx - ax) * -hy + (by - ay) * hx) / L / L * fps)
        sls = ma(sl, int(fps * 1.5)); drift = math.sqrt(sum((a - b) ** 2 for a, b in zip(sl, sls)) / len(sl)) * 100
        res.append((s['name'], round(wob, 2), round(flips / ((i1 - i0) / fps), 2), round(drift, 2), round(max(abs(v) for v in y), 1)))
    worst = max(res, key=lambda r: r[1]) if res else None
    avg = lambda k: round(sum(r[k] for r in res) / len(res), 2) if res else None
    return dict(film=c.get('name'), wobble=avg(1), flips_per_s=avg(2), drift=avg(3), worst=worst)

for p in sys.argv[1:]:
    print(json.dumps(film(p)))

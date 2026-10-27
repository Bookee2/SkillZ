"""Lift the stems of aid pins that stand on the start or finish pin, (or on the HIGH POINT label), so the labels stack instead of overprinting.

    python3 fix_stems.py <course.json> <shots.json>          (edits the shots file's "aid_stems" in place)

render.py lifts the START / FINISH pin (stem 1.8) only when an aid's MILE is ~0 or the course total. A loop course's
headquarters aid stands on the start at a mid-race mile (Javelina Jeadquarters at 22.2, Keweenaw's trailhead at 4.1),
so its label printed over START / FINISH. Here an aid whose GPX position is within NEAR metres of the start or finish
pin gets the next free stem height (1.0, 1.8, 2.6 …) at that spot; aids at mile ~0 / the total are left to render.py."""
import json, math, re, sys
NEAR = 600.0; MI = 1609.344; LEVELS = (1.0, 1.8, 2.6, 3.4)
C = json.load(open(sys.argv[1])); SP = json.load(open(sys.argv[2]))
g = C['gpx']; trk = g[g.index('<trk'):]
P = [(float(a), float(b)) for a, b in re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"', trk)]
K = math.cos(math.radians(P[0][0]))
xy = [((lon - P[0][1]) * 111320 * K, (lat - P[0][0]) * 111320) for lat, lon in P]
D = [0.0]
for i in range(1, len(xy)): D.append(D[-1] + math.dist(xy[i], xy[i - 1]))
def at(m):
    m = max(0.0, min(m, D[-1]))
    for i in range(1, len(D)):
        if D[i] >= m:
            t = (m - D[i - 1]) / ((D[i] - D[i - 1]) or 1); return (xy[i - 1][0] + t * (xy[i][0] - xy[i - 1][0]), xy[i - 1][1] + t * (xy[i][1] - xy[i - 1][1]))
    return xy[-1]
aids = [(float(m), lab) for m, lab in SP.get('aids') or []]
total_mi = D[-1] / MI; start, finish = xy[0], xy[-1]; loop = math.dist(start, finish) < 400
ends = [('start', start)] if loop else [('start', start), ('finish', finish)]
stems = {k: float(v) for k, v in (SP.get('aid_stems') or {}).items()}
for name, p in ends:
    on_mile = any(abs(m * MI) < 800 or abs(D[-1] - m * MI) < 800 for m, _ in aids)   # render.py's own rule (loop pin only)
    used = [1.8 if (loop and on_mile) else 1.0]
    for i, (m, lab) in enumerate(aids):
        if abs(m * MI) < 800 or abs(D[-1] - m * MI) < 800: used.append(stems.get(str(i), 1.0)); continue
        if math.dist(at(m * MI), p) > NEAR: continue
        # stack under the start/finish pin (a short stem): at the start the race sign stands just behind the pins, and a
        # lifted pin standing nearer the camera put its head over the other's label (Georgia's finish, 2026-10-27)
        s = next(l for l in (0.2,) + LEVELS if l not in used); used.append(s); stems[str(i)] = s
        print(f'{name}: aid {i} {lab[:40]!r} at mi {m} is {math.dist(at(m * MI), p):.0f} m from the pin -> stem {s}')
# the HIGH POINT label (render.py: the route's highest DEM point, label at stem ~1.2) collides with an aid pin standing on it
# (Quest for the Crest's Mt. Mitchell); located from the catalogue's elevation profile (scaled to the GPX), close enough at NEAR
ep = C.get('elevation_profile'); ep = json.loads(ep) if isinstance(ep, str) else ep
if ep and ep.get('eleM'):
    j = max(range(len(ep['eleM'])), key=lambda k: ep['eleM'][k]); hp = at(ep['cumM'][j] * D[-1] / (ep['cumM'][-1] or 1)); used = [1.0]
    for i, (m, lab) in enumerate(aids):
        if math.dist(at(m * MI), hp) > NEAR: continue
        cur = stems.get(str(i), 1.0)
        if cur < 2.6:                                                     # the HIGH POINT label sits higher than a pin's: 1.8 still clips it up close
            cur = 2.6; stems[str(i)] = cur
            print(f'high point: aid {i} {lab[:40]!r} at mi {m} is {math.dist(at(m * MI), hp):.0f} m from it -> stem {cur}')
        used.append(cur)
if stems: SP['aid_stems'] = {k: v for k, v in sorted(stems.items(), key=lambda kv: int(kv[0])) if v != 1.0}
json.dump(SP, open(sys.argv[2], 'w'), indent=1)

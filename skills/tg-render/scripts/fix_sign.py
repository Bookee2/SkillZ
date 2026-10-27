"""Place the race sign for a whole-course film so it faces THE START's camera, not the whole-course opener's.

    python3 fix_sign.py <course.json> <shots.json>          (adds "title": {lat, lon, face} to the shots file in place)

render.py stands the sign 600 m (more on long courses) behind the start, facing the camera of the film's first frame. Since
whole_course.py, that frame is the whole-course wide shot, 10-55 km out on another bearing, so by THE START the sign can be
side-on (Harvest's rail trail: a thin bar the whole film). This places it the way render.py would for THE START's camera:
straight behind the start as seen from that shot's camera (the mean of its anchors), 0.3x the follow slant out, facing it.
Appalachian 200's shots/69.json sets the same keys by hand. Skips a film that isn't whole-course or already places its sign."""
import json, math, re, sys
C = json.load(open(sys.argv[1])); SP = json.load(open(sys.argv[2]))
if (SP.get('title', {}).get('lat') and not SP['title'].get('_auto')) or not SP['shots'] or SP['shots'][0].get('name') != 'THE WHOLE COURSE':
    print('sign: left as it is'); sys.exit()
g = C['gpx']; trk = g[g.index('<trk'):]
P = [(float(a), float(b)) for a, b in re.findall(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"', trk)]
lat0, lon0 = P[0]; K = math.cos(math.radians(lat0))
xy = lambda la, lo: ((lo - lon0) * 111320 * K, (la - lat0) * 111320)
ll = lambda x, y: (lat0 + y / 111320, lon0 + x / (111320 * K))
d_km = sum(math.dist(xy(*P[i]), xy(*P[i - 1])) for i in range(1, len(P))) / 1000
S = min(1.0, max(0.18, d_km / 161.0)); SZ = max(S, 0.35)
# render.py's own distance (600 m, 2 km on a 100) suits the old 2.9 km start camera; the close-follow start sits at about
# 0.8x the follow slant (3550 x SZ m), where 600 m behind the start is above the top of the frame. 0.3x the slant keeps
# the sign's top inside the frame with the start pin below it.
d_back = 0.3 * 3550.0 * SZ
st = next(s for s in SP['shots'] if s.get('name') == 'THE START')
anchors = [xy(a[0], a[1]) for a in st['cam'] if isinstance(a, list)]
cx = sum(a[0] for a in anchors) / len(anchors); cy = sum(a[1] for a in anchors) / len(anchors)
away = math.atan2(-cx, -cy)                                                       # bearing from the start, away from the camera
tx, ty = math.sin(away) * d_back, math.cos(away) * d_back
face = math.degrees(math.atan2(cx - tx, cy - ty)) % 360
lat, lon = ll(tx, ty)
# letters scale with the course like the pins (render.py: 90 m, +0.2 m per km), capped so the row (~0.51 x letters per
# character) stays inside ~80% of the frame at the sign's distance (~1.3x the follow slant)
slant = 3550.0 * SZ; base = re.split(r'\s+[—–-]\s+', C.get('name', ''))[0]; chars = len(re.sub(r'\b(19|20)\d{2}\b', '', base).strip()) + 4
letters = max(90.0, min(90.0 * SZ / 0.35, 2.1 * slant / chars))
# a loop's finish comes back past the sign: the settle and the pull-back cameras can see it side-on, a bar across the
# frame (Javelina, Harvest 2026-10-27). The sign reads from either side, so turn it toward the bearing that keeps both
# THE START's camera and those cameras (within 4 km) furthest from side-on, favouring the start a little.
def dev(a, b): d = abs((a - b + 180) % 360 - 180); return min(d, 180 - d)
b_start = face; fin_b = []
for sh in SP['shots']:
    if sh.get('name') in ('THE FINISH', 'BACK OUT TO THE WHOLE COURSE'):
        for a_ in sh.get('cam', []):
            if isinstance(a_, list):
                x_, y_ = xy(a_[0], a_[1])
                if math.hypot(x_ - tx, y_ - ty) < 4000: fin_b.append(math.degrees(math.atan2(x_ - tx, y_ - ty)) % 360)
if fin_b:
    # the row (~0.51 x letters per character) turns about its middle: its near end must stay 150 m behind the start pin,
    # or the letters cross the start's labels (Harvest 2026-10-27, a 34 deg turn)
    half = 0.51 * letters * chars / 2; rot_max = math.degrees(math.asin(max(0.0, min(1.0, (d_back - 150) / half))))
    face = min((f_ for f_ in range(360) if dev(f_, b_start) <= rot_max), key=lambda f_: max([1.3 * dev(f_, b_start)] + [dev(f_, b) for b in fin_b]))
    print(f'sign: turned {((face - b_start + 180) % 360 - 180):+.0f} deg for the finish cameras (worst side-on {max([dev(face, b_start)] + [dev(face, b) for b in fin_b]):.0f} deg, limit {rot_max:.0f})')
SP['title'] = {**SP.get('title', {}), 'lat': round(lat, 6), 'lon': round(lon, 6), 'face': round(face, 1), 'letters_m': round(letters), '_auto': True}
json.dump(SP, open(sys.argv[2], 'w'), indent=1)
print(f'sign: {d_back:.0f} m behind the start from THE START camera ({math.hypot(cx, cy) / 1000:.1f} km out), facing {face:.0f} deg, letters {letters:.0f} m')

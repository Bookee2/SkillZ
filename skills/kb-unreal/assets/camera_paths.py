"""Camera path helpers for Unreal Sequencer scripts (pure Python, import or paste).

Proven in the Capra space intro (capra_space_seq.py). Everything is computed in
the subject's local frame (camera on -X looking +X, +Y right, Z up, floor 0),
then turned into world space, so it works 2,450 km from the origin too.

    KP = [(t, theta_deg, radius_cm, height_cm, look_z_cm), ...]
    path = OrbitPath(KP, origin=(x, y, z), yaw_deg=-40)
    p, look = path.at(4.2)                    # world-space tuples
    then in Unreal: rot = unreal.MathLibrary.find_look_at_rotation(Vector(*p), Vector(*look))

Key every 2 frames (every frame through dives and shakes). Interpolation is a
monotone cubic per channel (Fritsch–Carlson): smooth through the keys, never
overshoots, never stops and restarts at a key (per-segment smoothstep did, and
Kris saw a "bump"; Catmull-Rom overshot and flung the camera).
"""
import math


def pchip(xs, ys, ease_ends=True):
    """Monotone cubic interpolant through (xs, ys). Returns f(x)."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    if ease_ends:
        m[0] = m[-1] = 0.0

    def f(x):
        x = min(max(x, xs[0]), xs[-1])
        i = n - 2 if x >= xs[-1] else max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
        h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def smoothstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class Frame:
    """Local subject frame → world. yaw_deg turns the local +X (away from camera)."""

    def __init__(self, origin, yaw_deg):
        self.o = origin
        self.c, self.s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))

    def world(self, x, y, z):
        return (self.o[0] + x * self.c - y * self.s, self.o[1] + x * self.s + y * self.c, self.o[2] + z)


class OrbitPath:
    """Keypoint orbit: (t, theta, radius, height, look_z). theta 0 = dead front."""

    def __init__(self, kp, origin, yaw_deg=0.0, shake=None):
        self.kp = kp
        self.frame = Frame(origin, yaw_deg)
        self.curves = [pchip([k[0] for k in kp], [k[j] for k in kp]) for j in range(1, 5)]
        self.shake = shake

    def at(self, t):
        th, r, h, lz = (c(t) for c in self.curves)
        th = math.radians(th)
        jx = jz = jp = 0.0
        if self.shake:
            jx, jz, jp = self.shake(t)
        side = (math.sin(th), math.cos(th))
        p = self.frame.world(-r * math.cos(th) + jx * side[0], r * math.sin(th) + jx * side[1], h + jz)
        return p, self.frame.world(0.0, 0.0, lz), jp      # add jp to the pitch after look-at


def decaying_shake(t0, dur=0.8, side_cm=3.0, up_cm=2.2, pitch_deg=0.35, decay=5.5):
    """A jolt after an impact at t0: returns f(t) -> (sideways cm, up cm, pitch deg)."""
    def f(t):
        u = t - t0
        if u < 0 or u > dur:
            return 0.0, 0.0, 0.0
        e = math.exp(-decay * u)
        return (side_cm * e * math.sin(2 * math.pi * 7 * u + 0.6),
                up_cm * e * math.sin(2 * math.pi * 9 * u),
                pitch_deg * e * math.sin(2 * math.pi * 8 * u + 1.1))
    return f


def powers_of_ten(times, log10_dists, start_dir, end_dir, target, far_aim,
                  swoop=(6.5, 3.0), aim_handover=(8.0, 5.5)):
    """SUPERSEDED by straight_dive (Kris disliked the swoop and aim hand-off in v4).
    A dive whose distance to `target` is one PCHIP curve in log10 space.

    times/log10_dists: e.g. [0, 1.0, 1.8, 2.5, 3.1, 3.7, 4.5] / [9.5, 9.42, 7.6,
    5.2, 4.0, 3.3, log10(arrival_cm)] — give the last decade (~100 m → arrival)
    at least ~1.5 s or the set seems to pop in. Direction slerps from start_dir
    to end_dir as log-distance falls through `swoop`; the aim hands over from
    far_aim (e.g. the planet's centre) to target through `aim_handover`.
    Keep the set always loaded (is_spatially_loaded=False) or World Partition
    streams it in late. Returns f(t) -> (camera_pos, aim_point, distance).
    """
    ld = pchip(times, log10_dists)
    norm = lambda v: (lambda l: tuple(c / l for c in v))(math.sqrt(sum(c * c for c in v)))
    a, b = norm(start_dir), norm(end_dir)

    def f(t):
        x = ld(t)
        w = smoothstep((swoop[0] - x) / (swoop[0] - swoop[1]))
        d = norm(tuple(a[i] * (1 - w) + b[i] * w for i in range(3)))
        dist = 10 ** x
        p = tuple(target[i] + d[i] * dist for i in range(3))
        wa = smoothstep((aim_handover[0] - x) / (aim_handover[0] - aim_handover[1]))
        aim = tuple(far_aim[i] + (target[i] - far_aim[i]) * wa for i in range(3))
        return p, aim, dist
    return f



def straight_dive(target, back_dir, ld0, d_end, t_end, push_start=0.8, hold=0.06,
                  a=1.5, b=2.5, n=6000):
    """The dive Kris approved over powers_of_ten (v5 of the Saturn ident): one
    straight line of sight. The camera sits on target + back_dir * 10**ld, aimed
    at `target` the whole way, so it never turns and the subject stays dead centre
    (a swoop or an aim hand-off reads as "zooms in, rotates a bit, then zooms in",
    and the turning speeds up near the set, which reads as a jerk).

    ld (log10 distance) integrates one smooth speed profile instead of PCHIP knots
    (knots kink the acceleration): a drift that fades out (covers `hold` decades,
    time for a marker to appear) plus a beta-shaped push u**a * (1-u)**b from
    push_start to t_end. a=1.5, b=2.5 over 0.8 -> 6.0 s and 9.7 -> log10(600)
    peaks near 2.5 decades/s and spends 1.9 s on the last decade, arriving at rest.
    back_dir: unit vector from the target back up the line of sight (e.g. the
    final heading raised 22 degrees). Returns f(t) -> (camera_pos, distance) and
    the log-distance table function ld(t).
    """
    dt = t_end / n
    ts = [i * dt for i in range(n + 1)]

    def push(t):
        u = (t - push_start) / (t_end - push_start)
        return u ** a * (1 - u) ** b if 0.0 < u < 1.0 else 0.0

    def cum(arr):
        out = [0.0]
        for i in range(n):
            out.append(out[-1] + (arr[i] + arr[i + 1]) * dt / 2)
        return out
    D = cum([(1 - t / t_end) ** 4 for t in ts])
    M = cum([push(t) for t in ts])
    cd, cm = hold / D[-1], (ld0 - math.log10(d_end) - hold) / M[-1]
    table = [ld0 - cd * D[i] - cm * M[i] for i in range(n + 1)]

    def ld(t):
        x = min(max(t, 0.0), t_end) / dt
        i = min(int(x), n - 1)
        return table[i] + (table[i + 1] - table[i]) * (x - i)

    def f(t):
        dist = 10 ** ld(t)
        return tuple(target[i] + back_dir[i] * dist for i in range(3)), dist
    return f, ld

if __name__ == '__main__':
    # quick offline check: print height and radius through a move (no Unreal needed)
    kp = [(0.0, 50, 1650, 128, 118), (3.5, 44, 560, 128, 118), (4.4, 32, 700, 136, 132), (6.2, 8, 660, 150, 150)]
    path = OrbitPath(kp, (0, 0, 0))
    for f in range(0, 190, 15):
        p, look, _ = path.at(f / 30)
        print(f, ['%.0f' % c for c in p])

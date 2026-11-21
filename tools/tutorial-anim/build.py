"""Build the tutorial's R6 animation chains so every handoff is seamless.

  python -I -X utf8 build.py [path/to/RoMixamo.rbxm]

1. Every clip in chains.json is pulled from the RoMixamo plugin's offline library and converted to the non-bending R6
   rig (mixamo_r6.py, a port of the plugin's own Convert2R6, checked against the plugin's output to 3 decimals).
2. Loops are made seamless (the last 0.35 s eases into the first frame).
3. A chain is cut into PIECES at its loops. Each run of one-shots between loops is baked into ONE clip; each loop is its
   own clip. All blending happens here, offline, so at runtime the Cine only switches clips at frames where the poses
   are identical (fade 0.05): nothing can pop.
4. Every handoff (A -> B) is cut where pose and motion agree best (heading and ground position ignored: B is re-seated
   onto A by baking the alignment into B's torso, so the actor's root never moves during a blend). The blend window
   continues A's motion past the cut and pre-rolls B before it, so velocity carries through. Where the poses are far
   apart the window is longer and staged in the house style: the torso leads, legs then arms follow, the head comes last.
5. Loops get a fixed entry phase (the piece before ends exactly on the loop's frame) and exit phase (the piece after
   starts exactly on it).
6. Writes out/<Piece>.lua (KeyframeSequence builders, the animpro DATA format, run in Studio with rbxc.py),
   out/TutorialAnim.luau (the plan and a small player for the Cine) and REPORT.md.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mixamo_r6 as MX  # noqa: E402
import rbxm_peek as RP  # noqa: E402

PLUGIN = sys.argv[1] if len(sys.argv) > 1 else os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Plugins\RoMixamo.rbxm")
JOINTS = ["Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg"]
WEIGHT = {"Torso": 2.0, "Head": 0.4, "Left Arm": 0.8, "Right Arm": 0.8, "Left Leg": 1.2, "Right Leg": 1.2}
FPS = 30.0
FOLDER = "Tutorial"                         # game.ReplicatedStorage.NHCineClips.<FOLDER>: the clips (and their _End poses)
STAGED_AT = 0.55                            # weighted radians: above this the blend is staged (torso leads, head last)
# staged blend: (start, end) of each joint's own ease inside the window, as fractions of it
STAGE = {"Torso": (0.0, 0.7), "Left Leg": (0.08, 0.8), "Right Leg": (0.12, 0.84), "Left Arm": (0.16, 0.9),
         "Right Arm": (0.2, 0.92), "Head": (0.28, 1.0)}
SOFT = {j: (0.0, 1.0) for j in JOINTS}
SOFT["Torso"] = (0.0, 0.9)                  # even a soft blend lets the root lead a touch


# ------------------------------------------------------------------ quaternions (x, y, z, w)

def mat_to_q(m):
    r = m[:3, :3]
    t = np.trace(r)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, 0.25 * s]
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        q = [0.25 * s, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s, (r[2, 1] - r[1, 2]) / s]
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        q = [(r[0, 1] + r[1, 0]) / s, 0.25 * s, (r[1, 2] + r[2, 1]) / s, (r[0, 2] - r[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        q = [(r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, 0.25 * s, (r[1, 0] - r[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def qinv(a):
    return np.array([-a[0], -a[1], -a[2], a[3]])


def qpow(q, f):
    """the rotation q scaled by f (f may be any real)"""
    q = q if q[3] >= 0 else -q
    ang = 2 * math.acos(max(-1.0, min(1.0, q[3])))
    if ang < 1e-8:
        return np.array([0.0, 0.0, 0.0, 1.0])
    axis = q[:3] / math.sin(ang / 2)
    a = ang * f
    return np.array([*(axis * math.sin(a / 2)), math.cos(a / 2)])


def slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + (b - a) * t
        return r / np.linalg.norm(r)
    th = math.acos(min(1.0, d))
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


def qang(a, b):
    return 2 * math.acos(min(1.0, abs(float(np.dot(a, b)))))


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def zq(a):
    return np.array([0.0, 0.0, math.sin(a / 2), math.cos(a / 2)])


def yaw_of(q):
    """the torso's heading about the pose-space up axis (Z; torso pose space: X sideways, Y forward/back, Z up)"""
    v = qmat(q) @ np.array([1.0, 0.0, 0.0])
    return math.atan2(v[1], v[0])


def tilt(q):
    return qmul(zq(-yaw_of(q)), q)


def smoother(u):
    u = max(0.0, min(1.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


# ------------------------------------------------------------------ frames: q[f, joint, 4], p[f, joint, 3]

class Clip:
    def __init__(self, name, q, p, loop=False):
        self.name, self.q, self.p, self.loop = name, q, p, loop
        for k in range(1, len(self.q)):                       # one quaternion hemisphere per joint, frame to frame
            for j in range(len(JOINTS)):
                if np.dot(self.q[k, j], self.q[k - 1, j]) < 0:
                    self.q[k, j] *= -1

    @classmethod
    def from_frames(cls, name, frames, loop):
        q = np.array([[mat_to_q(f[j]) for j in JOINTS] for _, f in frames])
        p = np.array([[f[j][:3, 3] for j in JOINTS] for _, f in frames])
        return cls(name, q, p, loop)

    @property
    def n(self):
        return len(self.q)

    @property
    def period(self):
        return self.n - 1                                     # a loop's last frame repeats its first

    def frame(self, i):
        """frame i, extrapolated past either end by continuing the motion with a decaying velocity"""
        if self.loop:
            k = i % self.period
            return self.q[k], self.p[k]
        if 0 <= i < self.n:
            return self.q[i], self.p[i]
        if i >= self.n:
            a, b, m = self.n - 1, self.n - 2, i - (self.n - 1)
        else:
            a, b, m = 0, 1, -i
        f = sum(0.82 ** s for s in range(1, m + 1))
        q = np.array([qmul(qpow(qmul(self.q[a, j], qinv(self.q[b, j])), f), self.q[a, j]) for j in range(len(JOINTS))])
        p = self.p[a] + (self.p[a] - self.p[b]) * f
        return q, p

    def aligned(self, phi, tx, ty, name=None):
        """this clip re-seated: its torso turned by phi about up and moved by (tx, ty) on the ground (pose space)"""
        q, p = self.q.copy(), self.p.copy()
        r = zq(phi)
        c, s = math.cos(phi), math.sin(phi)
        for f in range(self.n):
            q[f, 0] = qmul(r, q[f, 0])
            x, y = p[f, 0, 0], p[f, 0, 1]
            p[f, 0, 0], p[f, 0, 1] = c * x - s * y + tx, s * x + c * y + ty
        return Clip(name or self.name, q, p, self.loop)


def pose_dist(qa, pa, qb, pb):
    """the body's pose gap (heading and ground position left out: B gets re-seated onto A): weighted radians + height"""
    d = WEIGHT["Torso"] * qang(tilt(qa[0]), tilt(qb[0]))
    d += sum(WEIGHT[j] * qang(qa[k], qb[k]) for k, j in enumerate(JOINTS) if j != "Torso")
    return d / sum(WEIGHT.values()) + 0.4 * abs(float(pa[0][2] - pb[0][2]))


def motion_dist(A, i, B, j):
    """pose gap at the cut, and 3 frames on, and 3 frames before: agreeing poses AND agreeing motion"""
    c = 0.0
    for o, w in ((0, 1.0), (3, 0.6), (-3, 0.6)):
        qa, pa = A.frame(i + o)
        qb, pb = B.frame(j + o)
        c += w * pose_dist(qa, pa, qb, pb)
    return c / 2.2


def seam_loop(c, secs=0.35):
    """the tail eases into a pre-roll of the head (frame 0's own motion run backwards), so the seam carries pose AND
    velocity: the last frame is frame 0 and arrives moving the way frame 0 leaves"""
    head = Clip(c.name, c.q.copy(), c.p.copy(), loop=False)
    m = min(int(secs * FPS), c.n // 3)
    for k in range(m):
        i = c.n - m + k
        w = smoother((k + 1) / m)
        tq, tp = head.frame(i - (c.n - 1))
        for j in range(len(JOINTS)):
            c.q[i, j] = slerp(c.q[i, j], tq[j], w)
            c.p[i, j] = c.p[i, j] * (1 - w) + tp[j] * w
    c.q[-1], c.p[-1] = c.q[0].copy(), c.p[0].copy()


def load_game(name):
    """a clip sampled from the game's own animation (extract_game.luau): Motor6D.Transform per joint per frame"""
    d = json.load(open(os.path.join(HERE, "game", f"{name}.json"), encoding="utf-8"))
    return [(f["t"], {j: MX.M(f[j]) for j in JOINTS}) for f in d["frames"]]


def seat(qa, pa, qb, pb):
    """(phi, tx, ty): the re-seat that puts B's torso on A's heading and ground position"""
    phi = yaw_of(qa[0]) - yaw_of(qb[0])
    c, s = math.cos(phi), math.sin(phi)
    bx, by = pb[0][0], pb[0][1]
    return phi, pa[0][0] - (c * bx - s * by), pa[0][1] - (s * bx + c * by)


def best_cut(A, i_range, B, j_range):
    best = None
    for i in i_range:
        for j in j_range:
            c = motion_dist(A, i, B, j)
            if best is None or c < best[2]:
                best = (i, j, c)
    return best


GENTLE = 45.0               # st/s^2: a blend into a near-still idle may settle this hard (a slow, readable settle)


def blend(A, i, B, j, gap, secs=None):
    """the window that hands A over to B around cut (i, j): A continues, B pre-rolls, per-joint eased weights.
    Returns (the window's q and p, h, staged)."""
    staged = gap > STAGED_AT
    if secs is None:
        secs = min(0.9, max(0.45, 0.35 + 0.45 * gap)) if staged else min(0.6, max(0.3, 0.25 + 0.5 * gap))
    h = int(round(secs * FPS / 2))
    sched = STAGE if staged else SOFT
    W = 2 * h + 1
    q = np.zeros((W, len(JOINTS), 4))
    p = np.zeros((W, len(JOINTS), 3))
    for k in range(W):
        qa, pa = A.frame(i - h + k)
        qb, pb = B.frame(j - h + k)
        u = k / (W - 1)
        for jj, nm in enumerate(JOINTS):
            s0, s1 = sched[nm]
            w = smoother((u - s0) / (s1 - s0))
            q[k, jj] = slerp(qa[jj], qb[jj], w)
            p[k, jj] = pa[jj] * (1 - w) + pb[jj] * w
    return q, p, h, staged


# ------------------------------------------------------------------ the pieces of a chain

def yaw_matrix(a):
    """the HumanoidRootPart-space rotation about up (Y) by a radians"""
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def end_offset(q, p):
    """the root move that puts the HumanoidRootPart under the torso's last ground position and heading. Torso pose space
    is X sideways, Y forward/back, Z up; under the R6 RootJoint (C0 rotation (-1,0,0; 0,0,1; 0,1,0)) that is HRP
    (-X, Z, Y). A turn about pose Z is a turn about HRP Y with the same sign."""
    return {"X": round(float(-p[0]), 4), "Z": round(float(p[1]), 4), "Yaw": round(math.degrees(yaw_of(q)), 3)}


def end_pose(q, p):
    """the same torso with its ground offset and heading taken out (tilt and height kept): the _End clip's pose"""
    return tilt(q), np.array([0.0, 0.0, float(p[2])])


SETTLE_FRAMES = 10          # a chain's last one-shot piece ends with this many frames of its last motion dying out (0.82 per frame), then a 2-frame hold


def settle(clip):
    """the piece with SETTLE_FRAMES of its last motion dying out (Clip.frame's extrapolation, 0.82 per frame) and a
    2-frame hold appended, under its own root (no re-seat): the piece itself ends at rest, so the re-seat switches a
    still pose to an identical still pose and no frame-level timing slack can show"""
    src = Clip(clip.name, clip.q, clip.p, loop=False)
    qs, ps = list(src.q.copy()), list(src.p.copy())
    for k in range(1, SETTLE_FRAMES + 1):
        q, p = src.frame(src.n - 1 + k)
        qs.append(np.array(q, dtype=float))
        ps.append(np.array(p, dtype=float))
    qs += [qs[-1].copy(), qs[-1].copy()]
    ps += [ps[-1].copy(), ps[-1].copy()]
    return Clip(clip.name, np.array(qs), np.array(ps), loop=False)


def end_clip(clip):
    """the piece's _End clip: its final frame as a still pose (two identical frames, 1/30 s), the torso's ground offset
    and heading taken out (end_pose; tilt and height kept), every limb's local pose as it is. Played with the root
    re-seated by end_offset() of the same frame, the body doesn't move."""
    q, p = clip.q[-1].copy(), clip.p[-1].copy()
    q[0], p[0] = end_pose(q[0], p[0])
    return Clip(clip.name + "_End", np.array([q, q.copy()]), np.array([p, p.copy()]), loop=False)


class Piece:
    def __init__(self, name, loop=False):
        self.name, self.loop = name, loop
        self.q, self.p = [], []
        self.entry = 0.0                                       # loops: the phase the piece before lands on
        self.exit = 0.0                                        # loops: the phase the piece after starts from
        self.hold = False
        self.settled = False                                   # the chain's last one-shot: ends at rest (settle())
        self.parts = []                                        # what it's made of, for the report

    def add(self, q, p):
        self.q.extend(list(q))
        self.p.extend(list(p))

    def clip(self, loop=False):
        c = Clip(self.name, np.array(self.q), np.array(self.p), loop)
        return c


def build_chain(name, steps, clips):
    """steps: [{"clip":..., "hold":...}]. Returns the pieces and the handoff log."""
    pieces, log = [], []
    cur = None          # the aligned clip being laid down
    cur_off = 0         # where cur's frame 0 sits in the open piece
    cur_min = 0         # cur's first frame that is cur's own (after the last window)
    piece = None
    loop_piece = None
    for k, st in enumerate(steps):
        src = clips[st["clip"]]
        if cur is None and loop_piece is None:                 # the chain's first step
            if src.loop:
                loop_piece = Piece(f"{name}{len(pieces) + 1}_{src.name}", loop=True)
                loop_piece.add(src.q, src.p)
                loop_piece.parts.append(src.name)
                pieces.append(loop_piece)
                cur, cur_off, cur_min = src, 0, 0
            else:
                piece = Piece(f"{name}{len(pieces) + 1}")
                piece.parts.append(src.name)
                cur, cur_off, cur_min = src, 0, 0
                n_keep = src.n if "hold" not in st else int(round(st["hold"] * (src.n - 1))) + 1
                piece.add(src.q[:n_keep], src.p[:n_keep])
                if "hold" in st:
                    piece.hold = True
                pieces.append(piece)
            continue
        # where to cut out of the current clip and into this one
        if cur.loop:
            P = cur.period
            i_rng = range(cur_min, cur_min + P)
        else:
            lo = max(cur_min + 6, int(0.55 * (cur.n - 1)))
            i_rng = range(min(lo, cur.n - 1), cur.n)
        j_rng = range(0, src.period) if src.loop else range(0, max(1, int(0.35 * (src.n - 1))) + 1)
        i, j, gap = best_cut(cur, i_rng, src, j_rng)
        qa, pa = cur.frame(i)
        qb, pb = src.frame(j)
        phi, tx, ty = seat(qa, pa, qb, pb)
        B = src.aligned(phi, tx, ty)
        # the shortest window that adds no motion the two clips don't have (or, into an idle, settles gently)
        h_cap = None if cur.loop else max(4, i - cur_min + 2)
        best = None
        for scale in (1.0, 1.3, 1.65, 2.0, 2.5, 3.0, 3.6):
            bq, bp, h, staged = blend(cur, i, B, j, gap, secs=None if scale == 1.0 else
                                      scale * (min(0.9, max(0.45, 0.35 + 0.45 * gap)) if gap > STAGED_AT else min(0.6, max(0.3, 0.25 + 0.5 * gap))))
            if best is not None and (h_cap is not None and h > h_cap or (2 * h + 1) / FPS > 1.85):
                break
            peak, src_peak = audit_blend(cur, i, B, j, bq, bp, h)
            ok = peak <= 1.15 * src_peak or peak <= GENTLE
            if best is None or ok or peak / src_peak < best[4] / best[5]:
                best = (bq, bp, h, staged, peak, src_peak)
            if ok:
                break
        bq, bp, h, staged, peak, src_peak = best
        log.append({"chain": name, "a": cur.name, "b": src.name, "raw": pose_dist(cur.q[-1], cur.p[-1], src.q[0], src.p[0]),
                    "cut": gap, "out": i / FPS, "in": j / FPS, "window": (2 * h + 1) / FPS, "staged": staged,
                    "seat": (math.degrees(phi), math.hypot(tx, ty)), "peak": peak, "src_peak": src_peak})
        if cur.loop:
            # a new piece starts on the loop's own frame (the exit phase) and blends out of it
            s0 = i - h - 4
            if s0 < cur_min:
                s0 += cur.period
                i += cur.period
            loop_piece.exit = (s0 % cur.period) / FPS                # the piece's first frame IS the loop at this phase
            piece = Piece(f"{name}{len(pieces) + 1}")
            piece.parts.append(src.name)
            for f in range(s0, i - h):
                fq, fp = cur.frame(f)
                piece.q.append(fq)
                piece.p.append(fp)
            pieces.append(piece)
            loop_piece = None
        else:
            del piece.q[cur_off + i - h:]
            del piece.p[cur_off + i - h:]
            piece.parts.append(src.name)
        log[-1]["piece"], log[-1]["t"] = piece.name, (len(piece.q) + h) / FPS
        piece.add(bq, bp)
        if B.loop:
            # finish on the loop's own frame a few frames past the window; the loop starts there (the entry phase)
            end = j + h + 4
            for f in range(j + h + 1, end + 1):
                fq, fp = B.frame(f)
                piece.q.append(fq)
                piece.p.append(fp)
            loop_piece = Piece(f"{name}{len(pieces) + 1}_{src.name}", loop=True)
            loop_piece.add(B.q, B.p)
            loop_piece.parts.append(src.name)
            loop_piece.entry = (end % B.period) / FPS                # the piece's last frame IS the loop at this phase
            pieces.append(loop_piece)
            piece = None
            cur, cur_off, cur_min = B, 0, end % B.period
        else:
            start = len(piece.q)
            stop = B.n if "hold" not in st else int(round(st["hold"] * (B.n - 1))) + 1
            for f in range(j + h + 1, stop):
                piece.q.append(B.q[f])
                piece.p.append(B.p[f])
            if "hold" in st:
                piece.hold = True
            cur, cur_off, cur_min = B, start - (j + h + 1), j + h + 1
    # the chain ends at rest: its last piece, if it is a one-shot that isn't a Hold, gets the settle. A Hold already ends
    # frozen (as authored); a loop that comes last keeps cycling until the caller re-seats (it has no end to settle into,
    # and frames appended to it would break its seam), and the piece before it must still end on the loop's entry frame.
    last = pieces[-1] if pieces else None
    if last is not None and not last.loop and not last.hold:
        s = settle(last.clip())
        last.q, last.p = list(s.q), list(s.p)
        last.settled = True
    return pieces, log


# ------------------------------------------------------------------ the blend audit: R6 forward kinematics

ENDS = {"Torso": (0, 1, 0), "Head": (0, 0.5, 0), "Left Arm": (0, -1, 0), "Right Arm": (0, -1, 0), "Left Leg": (0, -1, 0), "Right Leg": (0, -1, 0)}
MOTOR = {"Head": "Neck", "Left Arm": "Left Shoulder", "Right Arm": "Right Shoulder", "Left Leg": "Left Hip", "Right Leg": "Right Hip"}


def fk(qf, pf):
    """the world positions (root at the origin) of every part's centre and far end, as Studio solves the R6 Motor6Ds"""
    def T(q, p):
        m = np.eye(4)
        m[:3, :3] = qmat(q)
        m[:3, 3] = p
        return m
    c0, c1 = MX.R6M["RootJoint"]
    torso = c0 @ T(qf[0], pf[0]) @ MX.inv(c1)
    pts = []
    for k, j in enumerate(JOINTS):
        if j == "Torso":
            w = torso
        else:
            m0, m1 = MX.R6M[MOTOR[j]]
            w = torso @ m0 @ T(qf[k], pf[k]) @ MX.inv(m1)
        pts.append(w[:3, 3])
        pts.append((w @ np.array([*ENDS[j], 1.0]))[:3])
    return np.array(pts)


def accel(frames):
    """per frame, the largest acceleration of any tracked point (studs / s^2)"""
    P = np.array([fk(q, p) for q, p in frames])
    a = np.zeros(len(P))
    if len(P) >= 3:
        d2 = (P[2:] - 2 * P[1:-1] + P[:-2]) * FPS * FPS
        a[1:-1] = np.linalg.norm(d2, axis=2).max(axis=1)
    return a


def audit_blend(A, i, B, j, bq, bp, h):
    """how much acceleration the baked window adds beyond what A and B do over the same frames on their own"""
    W = 2 * h + 1
    res = accel([(bq[k], bp[k]) for k in range(W)])
    ra = accel([A.frame(i - h + k) for k in range(W)])
    rb = accel([B.frame(j - h + k) for k in range(W)])
    src = max(ra[1:-1].max(), rb[1:-1].max(), 1.0)
    return float(res[1:-1].max()), float(src)


# ------------------------------------------------------------------ output

def r4(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def write_lua(c):
    lines, prev = [], None
    for f in range(c.n):
        cur = [",".join(r4(x) for x in [*c.q[f, k], *c.p[f, k]]) for k in range(len(JOINTS))]
        parts = [f"{j}={cur[k]}" for k, j in enumerate(JOINTS) if prev is None or prev[k] != cur[k] or f == c.n - 1]
        if parts:
            lines.append(r4(f / FPS) + ";" + ";".join(parts))
        prev = cur
    src = f'''-- Generated by tools/tutorial-anim/build.py from the RoMixamo library (R6, non-bending). Run with execute_luau / rbxc.py.
-- {c.name}: {c.n} frames at 30 fps, {"loop" if c.loop else "one-shot"}.
local DATA = [==[
{chr(10).join(lines)}
]==]
local PARENT = {{["Torso"]="HumanoidRootPart",["Head"]="Torso",["Left Arm"]="Torso",["Right Arm"]="Torso",["Left Leg"]="Torso",["Right Leg"]="Torso"}}
local seq = Instance.new("KeyframeSequence")
seq.Name = "{c.name}"
seq.Loop = {"true" if c.loop else "false"}
seq.Priority = Enum.AnimationPriority.Action
for line in string.gmatch(DATA, "[^\\n]+") do
	local t, rest = string.match(line, "^([^;]+);?(.*)$")
	local kf = Instance.new("Keyframe")
	kf.Time = tonumber(t)
	local poses = {{}}
	local function ensure(part)
		local p = poses[part]
		if p then return p end
		p = Instance.new("Pose")
		p.Name = part
		p.Weight = 0
		p.EasingStyle = Enum.PoseEasingStyle.Linear
		poses[part] = p
		local par = PARENT[part]
		p.Parent = if par then ensure(par) else kf
		return p
	end
	ensure("HumanoidRootPart")
	for part, vals in string.gmatch(rest, "([^=;]+)=([^;]+)") do
		local n = {{}}
		for v in string.gmatch(vals, "[^,]+") do table.insert(n, tonumber(v)) end
		local p = ensure(part)
		p.Weight = 1
		p.CFrame = CFrame.new(n[5] or 0, n[6] or 0, n[7] or 0, n[1], n[2], n[3], n[4])
	end
	kf.Parent = seq
end
local root = game.ReplicatedStorage:FindFirstChild("NHCineClips")
if not root then
	root = Instance.new("Folder")
	root.Name = "NHCineClips"
	root.Parent = game.ReplicatedStorage
end
local folder = root:FindFirstChild("{FOLDER}") or Instance.new("Folder")
folder.Name = "{FOLDER}"
folder.Parent = root
local old = folder:FindFirstChild(seq.Name)
if old then old:Destroy() end
seq.Parent = folder
local ok, id = pcall(function() return game:GetService("AnimationClipProvider"):RegisterAnimationClip(seq) end)
seq:SetAttribute("PreviewId", ok and tostring(id) or nil)
return string.format("built %s (%d keyframes, %.2f s)", seq:GetFullName(), #seq:GetKeyframes(), {(c.n - 1) / FPS:.3f})
'''
    open(os.path.join(HERE, "out", f"{c.name}.lua"), "w", encoding="utf-8").write(src)


PLAYER = '''
-- Play a chain on an Animator. cues[k] (optional) is a function that yields until the loop at step k may end
-- (no cue: the loop plays once). Every switch lands on an identical frame, so pieces switch instantly (no fade: a fade
-- in from weight 0 would show the rig's default pose for a moment), and the time a switch overshoots its exact point
-- by is carried into the next piece, so even a fast loop never skips. resolve: piece name -> animation id (the director passes `Ctx.Clip`);
-- onSwitch: called as each piece starts (the body check marks the switches). Returns the tracks.
-- A Hold piece, and the chain's last one-shot (which build.py ends at rest: its motion dies out, then 2 identical frames),
-- play to their end and HOLD the final frame (speed 0) until the caller stops them (CineActor.Reseat / Release); Play
-- returns once that hold is in place. A chain that ends on a loop returns with the loop still cycling.
-- isCancelled (optional) is checked in every wait; once it returns true, Play stops all its tracks (Stop(0)) and returns
-- (CineActor.Release: the Skip path).
function TutorialAnim.Play(animator: Animator, chain: string, resolve: (string) -> string?, cues: { [number]: () -> () }?, onSwitch: ((string) -> ())?, isCancelled: (() -> boolean)?)
	local RunService = game:GetService("RunService")
	local function cancelled(): boolean
		return isCancelled ~= nil and isCancelled()
	end
	local steps = TutorialAnim.Chains[chain]
	assert(steps, "no tutorial chain " .. chain)
	local loaded = {}
	for _, st in steps do
		local id = resolve(st.Piece) or ""
		if id ~= "" then
			local a = Instance.new("Animation")
			a.AnimationId = id
			local t = animator:LoadAnimation(a)
			t.Priority = Enum.AnimationPriority.Action
			loaded[st.Piece] = t
		end
	end
	-- freeze t on its final pose: from `from` to its Length every frame is that pose (a settled end's 2 identical frames;
	-- a Hold's last frame). Checked before every animation step: once the drawn time is in that span it just stops there
	-- (no time write, so nothing jumps); if this step's dt would carry it past its Length first (a frame hitch, or a low
	-- frame rate stepping over the span), it stops and is put on `at` (a non-looped track that ends falls to idle).
	-- Resumes the caller on the Heartbeat after the freeze, so the caller's next writes land with the frozen pose.
	local function holdAt(t: AnimationTrack, from: number, at: number)
		local thread = coroutine.running()
		local conn: RBXScriptConnection
		conn = RunService.PreAnimation:Connect(function(dt: number)
			local tp = t.TimePosition
			if cancelled() then
				conn:Disconnect()
			elseif tp >= from or not t.IsPlaying then
				conn:Disconnect()
				t:AdjustSpeed(0)
			elseif tp + 1.25 * dt >= t.Length then
				conn:Disconnect()
				t:AdjustSpeed(0)
				t.TimePosition = at
			else
				return
			end
			RunService.Heartbeat:Once(function() task.spawn(thread) end)
		end)
		coroutine.yield()
	end
	local function stopAll()
		for _, t in loaded do t:Stop(0) end
		return loaded
	end
	local prev: AnimationTrack? = nil
	local over = 0
	for k, st in steps do
		if cancelled() then return stopAll() end
		local t = loaded[st.Piece]
		if not t then continue end
		t.Looped = st.Loop == true
		t:Play(0)
		if onSwitch then onSwitch(st.Piece) end
		t.TimePosition = if st.Loop then ((st.Entry or 0) + over) % st.Length else math.max(0, over)
		if prev then prev:Stop(0) end
		prev = t
		over = 0
		if st.Loop then
			local cued = false                                      -- the cue (or one pass) runs aside, so a cancel isn't stuck behind it
			if cues and cues[k] then
				local cue = cues[k]
				task.spawn(function() cue() cued = true end)
			else
				local t0 = os.clock()
				task.spawn(function() while os.clock() - t0 < st.Length do RunService.Heartbeat:Wait() end cued = true end)
			end
			while not cued do
				if cancelled() then return stopAll() end
				RunService.Heartbeat:Wait()
			end
			if steps[k + 1] then
				local exit = st.Exit or 0
				local before = t.TimePosition
				while true do                                       -- leave on the exit phase, carrying the overshoot
					RunService.Heartbeat:Wait()
					if cancelled() then return stopAll() end
					local after = t.TimePosition
					local passed = (after - exit) % st.Length
					local span = (after - before) % st.Length
					if passed <= span then
						over = passed
						break
					end
					before = after
				end
			end
		elseif st.Hold then
			holdAt(t, st.Length, st.Length)                         -- the authored freeze-frame
		elseif not steps[k + 1] then
			holdAt(t, st.Length - 2 / 30, st.Length - 1 / 60)       -- the settled end: its 2 identical final frames
		else
			-- hand over within the last tick (a one-shot can't play past its last frame: it would stall there); the
			-- piece's tail is the next loop's own frames, so the loop just starts that much earlier in its cycle
			local started = os.clock()
			local dt = 1 / 60
			while os.clock() - started < st.Length - dt do
				dt = RunService.Heartbeat:Wait()
				if cancelled() then return stopAll() end
			end
			over = (os.clock() - started) - st.Length
		end
	end
	if cancelled() then return stopAll() end
	return loaded
end
'''


def main():
    spec = json.load(open(os.path.join(HERE, "chains.json"), encoding="utf-8"))
    classes, ic, names, sp, parent = RP.main(PLUGIN)
    rbxm = {names[r]: p["Source"] for r, p in sp.items() if "Source" in p and names.get(parent.get(r)) == "AnimData"}
    cat = [x for x in json.load(open(os.path.join(HERE, "mixamo_catalog.json"), encoding="utf-8")) if x["Type"] == "Motion"]
    clips = {}
    for name, c in spec["clips"].items():
        if "game" in c:
            frames = load_game(c["game"])
        else:
            _, d = MX.load_anim(rbxm, c["src"], cat)
            frames = MX.convert(d, inplace=c.get("inplace", False))
        clip = Clip.from_frames(name, frames, c.get("loop", False))
        if clip.loop and "game" not in c:
            seam_loop(clip)
        clips[name] = clip
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "out")):
        if f.endswith(".lua"):
            os.remove(os.path.join(HERE, "out", f))
    plan, logs, built = {}, [], []
    for chain, steps in spec["chains"].items():
        steps = [s if isinstance(s, dict) else {"clip": s} for s in steps]
        pieces, log = build_chain(chain, steps, clips)
        logs += log
        plan[chain] = []
        for pc in pieces:
            c = pc.clip(loop=pc.loop)
            write_lua(c)
            built.append((c, pc))
            write_lua(end_clip(c))
            e = {"Piece": pc.name, "Length": round((c.n - 1) / FPS, 3)}
            if pc.loop:
                e.update(Loop=True, Entry=round(pc.entry, 3), Exit=round(pc.exit, 3))
            if pc.hold:
                e["Hold"] = True
            e["EndOffset"] = end_offset(c.q[-1][0], c.p[-1][0])
            plan[chain].append(e)

    def lua_val(v):
        if isinstance(v, dict):
            return "{ " + ", ".join(f"{k} = {x}" for k, x in v.items()) + " }"
        return "true" if v is True else (f'"{v}"' if isinstance(v, str) else str(v))
    mod = ["--!strict", "-- Generated by tools/tutorial-anim/build.py: the tutorial's animation chains (doc 15 §5).",
           "-- A chain is a list of PIECES. A one-shot piece is several clips already blended into one; a Loop piece holds",
           "-- until its cue. Every switch between pieces lands on an identical frame (switch instantly, no fade): a loop is entered at Entry and left at",
           "-- Exit (seconds into the loop), so the blends are all baked and nothing pops. Hold: freeze on the last frame.",
           "-- The KeyframeSequences (and <Piece>_End poses) are in ReplicatedStorage.NHCineClips.Tutorial; published ids live in Config.CineClips.",
           "", "local TutorialAnim = {}", "", "TutorialAnim.Chains = {"]
    for chain, out in plan.items():
        mod.append(f"\t{chain} = {{")
        for e in out:
            mod.append("\t\t{ " + ", ".join(f"{k} = {lua_val(v)}" for k, v in e.items()) + " },")
        mod.append("\t},")
    mod += ["}", PLAYER, "return TutorialAnim", ""]
    open(os.path.join(HERE, "out", "TutorialAnim.luau"), "w", encoding="utf-8").write("\n".join(mod))
    # the check harness, with the plan pasted in
    m = "\n".join(mod)
    i0 = m.index("TutorialAnim.Chains = ") + len("TutorialAnim.Chains = ")
    chains_lua = m[i0:m.index("\n}\n", i0) + 2]
    chk = open(os.path.join(HERE, "chaincheck.luau"), encoding="utf-8").read()
    bl = ["{"]
    for chain in plan:
        items = [f'{{ piece = "{r["piece"]}", t = {r["t"]:.3f}, name = "{r["a"]} -> {r["b"]}" }}' for r in logs if r["chain"] == chain]
        bl.append(f"\t{chain} = {{ " + ", ".join(items) + " },")
    bl.append("}")
    chk = chk.replace("__CHAINS__", chains_lua).replace("__ONLY__", "nil").replace("__BLENDS__", "\n".join(bl))
    open(os.path.join(HERE, "out", "_chaincheck.luau"), "w", encoding="utf-8").write(chk)
    # the report
    rows = ["# Tutorial animation chains: how each handoff is made", "",
            "Generated by `build.py`. **Raw gap**: the body-pose distance (weighted joint angle in radians plus torso height,",
            "heading and ground position left out) if A's last frame went straight into B's first. **Cut gap**: at the cut",
            "build.py chose (pose and motion 3 frames either side). **Window**: the baked blend; *staged* means the torso leads",
            "and the head comes last. **Re-seat**: the turn and ground shift baked into B's torso so the root never moves.", "",
            "| Chain | A -> B | Raw gap | Cut gap | A out (s) | B in (s) | Window | Re-seat |", "|---|---|---|---|---|---|---|---|"]
    for r in logs:
        rows.append(f'| {r["chain"]} | {r["a"]} -> {r["b"]} | {r["raw"]:.2f} | {r["cut"]:.2f} | {r["out"]:.2f} | {r["in"]:.2f} | '
                    f'{r["window"]:.2f} s{" staged" if r["staged"] else ""} | {r["seat"][0]:.0f} deg, {r["seat"][1]:.1f} st |')
    rows += ["", "## Pieces", "", "| Piece | Made of | Length | Loop (entry / exit) |", "|---|---|---|---|"]
    for c, pc in built:
        lp = f"loop ({pc.entry:.2f} / {pc.exit:.2f} s)" if pc.loop else ("holds" if pc.hold else "")
        rows.append(f'| {c.name} | {" + ".join(pc.parts)} | {(c.n - 1) / FPS:.2f} s | {lp} |')
    rows += ["", "## Source clips", "", "| Clip | RoMixamo catalog |", "|---|---|"]
    for n in clips:
        rows.append(f'| {n} | {spec["clips"][n].get("src") or "game: " + spec["clips"][n]["game"]} |')
    res = os.path.join(HERE, "review", "chaincheck_result.txt")
    if os.path.exists(res):                                    # the Studio body check (run out/_chaincheck.luau with rbxc.py)
        rows += ["", "## Measured in Studio", "",
                 "`out/_chaincheck.luau` played every chain on an R6 dummy at 60 fps in NH Combat Test; the full output is in",
                 "`review/chaincheck_result.txt`. A runtime switch passes at or under its chain's own p99 or under 45 st/s2.", "",
                 "```", open(res, encoding="utf-8").read().rstrip(), "```"]
    # the settle audit: the chain's last piece dies out at rest; its deceleration must stay within the piece's own motion
    settles = []
    for c, pc in built:
        if pc.settled:
            a = accel([(c.q[k], c.p[k]) for k in range(c.n)])
            k0 = c.n - SETTLE_FRAMES - 3                       # the settle's frames, plus the junction into it
            own = float(np.percentile(a[1:k0], 99)) if k0 > 2 else 1.0
            settles.append((c.name, float(a[k0:].max()), own))
    rows += ["", "## Settles (each chain's last one-shot ends at rest)", "",
             f"{SETTLE_FRAMES} frames of the last motion dying out (0.82 per frame), then a 2-frame hold. Peak: the largest",
             "acceleration over the settle and the junction into it; own p99: the piece's own motion before it.", "",
             "| Piece | Settle peak (st/s2) | Own p99 | |", "|---|---|---|---|"]
    for n, pk, own in settles:
        rows.append(f"| {n} | {pk:.0f} | {own:.0f} | {'ok' if pk <= own or pk <= GENTLE else 'adds motion'} |")
    open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"{len(clips)} source clips -> {len(built)} pieces over {len(plan)} chains, {len(logs)} handoffs")
    for r in logs:
        ratio = r["peak"] / r["src_peak"]
        print(f'  {r["chain"]:18s} {r["a"]:>18s} -> {r["b"]:<18s} cut {r["cut"]:.2f} window {r["window"]:.2f}{" staged" if r["staged"] else "       "}'
              f'  blend peak {r["peak"]:5.0f} vs sources {r["src_peak"]:5.0f} ({ratio:.2f}x){"" if ratio <= 1.15 or r["peak"] <= GENTLE else "  <-- adds motion"}')
    for n, pk, own in settles:
        print(f'  settle {n:28s} peak {pk:5.0f} vs the piece own p99 {own:5.0f}{"" if pk <= own or pk <= GENTLE else "  <-- adds motion"}')


if __name__ == "__main__":
    main()

"""R6 paired-animation core: forward kinematics, contact (reach) solving, Hermite quaternion splines, baking.

Coordinates are Roblox HumanoidRootPart-local: x right, y up, z BACK (forward is -z). The ground is y = -3.
Joint rotations are body-axis Euler degrees [x, y, z] applied as CFrame.Angles (Rx * Ry * Rz), exactly what
animpro.mjs reads for an R6 "rotation" pose, so a baked frame goes straight into its JSON.
  Root   : { "p": [x, y, z], "r": [x, y, z] }   torso centre offset + rotation about the torso centre
  joints : Neck, RightShoulder, LeftShoulder, RightHip, LeftHip -> [x, y, z] about the joint pivot
Verified against the live rig and the owner's axis notes: Root -x leans forward, shoulder/hip +x swings the
limb forward, RightShoulder +z lifts the arm out to the side (LeftShoulder -z).
"""
import math
import numpy as np

FPS = 30
LIMBS = ["Neck", "RightShoulder", "LeftShoulder", "RightHip", "LeftHip"]
JOINTS = ["Root"] + LIMBS
PIVOT = {
    "Neck": (0, 1, 0), "RightShoulder": (1, 0.5, 0), "LeftShoulder": (-1, 0.5, 0),
    "RightHip": (1, -1, 0), "LeftHip": (-1, -1, 0),
}
# from the pivot, at rest: the part's centre and its far end (hand / sole / crown)
CENTRE = {
    "Neck": (0, 0.5, 0), "RightShoulder": (0.5, -0.5, 0), "LeftShoulder": (-0.5, -0.5, 0),
    "RightHip": (-0.5, -1, 0), "LeftHip": (0.5, -1, 0),
}
END = {
    "Neck": (0, 1.0, 0), "RightShoulder": (0.5, -1.5, 0), "LeftShoulder": (-0.5, -1.5, 0),
    "RightHip": (-0.5, -2, 0), "LeftHip": (0.5, -2, 0),
}
PART_OF = {"Neck": "Head", "RightShoulder": "Right Arm", "LeftShoulder": "Left Arm",
           "RightHip": "Right Leg", "LeftHip": "Left Leg"}
JOINT_OF = {v: k for k, v in PART_OF.items()}
SIZE = {"Torso": (2, 2, 1), "Head": (1, 1, 1), "Right Arm": (1, 2, 1), "Left Arm": (1, 2, 1),
        "Right Leg": (1, 2, 1), "Left Leg": (1, 2, 1)}


# ------------------------------------------------------------------ rotations
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(d):
    x, y, z = (math.radians(v) for v in d)
    return rx(x) @ ry(y) @ rz(z)


def to_euler(R):
    """Inverse of euler(): R = Rx(a) Ry(b) Rz(c)."""
    b = math.asin(max(-1.0, min(1.0, R[0, 2])))
    if abs(R[0, 2]) < 0.99999:
        a = math.atan2(-R[1, 2], R[2, 2])
        c = math.atan2(-R[0, 1], R[0, 0])
    else:
        a = math.atan2(R[2, 1], R[1, 1])
        c = 0.0
    return [math.degrees(a), math.degrees(b), math.degrees(c)]


def mat2q(R):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = math.sqrt(1 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def q2mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def rot_between(a, b):
    """Smallest rotation taking direction a onto direction b."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        axis = np.cross(a, [1, 0, 0])
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(a, [0, 0, 1])
        axis /= np.linalg.norm(axis)
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + 2 * K @ K
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


# ------------------------------------------------------------------ frames (4x4)
def cf(pos=(0, 0, 0), R=None):
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    M[:3, 3] = pos
    return M


def xf(M, p):
    return M[:3, :3] @ np.asarray(p, float) + M[:3, 3]


# ------------------------------------------------------------------ FK
def fk(pose, hrp=None):
    """pose: {Root: {p, r(matrix)}, joint: matrix}. Returns part frames (4x4) in the hrp's parent space."""
    hrp = np.eye(4) if hrp is None else hrp
    torso = hrp @ cf(pose["Root"]["p"], pose["Root"]["R"])
    parts = {"Torso": torso}
    for j in LIMBS:
        R = pose[j]
        piv = cf(PIVOT[j])
        rot = cf(R=R)
        off = pose.get(j + "_off")  # tuck: the limb slid off its socket in torso space (the owner's kneel)
        base = torso if off is None else torso @ cf(off)
        parts[PART_OF[j]] = base @ piv @ rot @ cf(CENTRE[j])
    return parts


def plant_solve(pose, joint, W, hrp=None):
    """A limb whose part frame is fixed in the world (W, 4x4): the joint rotation and the tuck offset (torso space)
    that put it there for the pose's torso."""
    hrp = np.eye(4) if hrp is None else hrp
    torso = hrp @ cf(pose["Root"]["p"], pose["Root"]["R"])
    L = np.linalg.inv(torso) @ np.asarray(W, float)
    R = L[:3, :3]
    off = L[:3, 3] - (np.asarray(PIVOT[joint], float) + R @ np.asarray(CENTRE[joint], float))
    return R, off


def pose_offset(joint, off):
    """Torso-space tuck offset -> Pose.CFrame position for the default R6 hip (C0 = (+-1,-1,0) * rotY(+-90))."""
    R = ry(math.radians(90 if joint == "RightHip" else -90))
    return R.T @ np.asarray(off, float)


def end_point(pose, joint, hrp=None):
    hrp = np.eye(4) if hrp is None else hrp
    torso = hrp @ cf(pose["Root"]["p"], pose["Root"]["R"])
    off = np.asarray(pose.get(joint + "_off", (0, 0, 0)), float)
    return xf(torso, off + np.asarray(PIVOT[joint]) + pose[joint] @ np.asarray(END[joint]))


def _angle(A, B):
    c = (np.trace(A.T @ B) - 1) / 2
    return math.acos(max(-1.0, min(1.0, c)))


def solve_reach(pose, joint, target_world, hrp=None, twist=None, ref=None):
    """Rotation for `joint` that puts its far end on target_world (direction solve; length mismatch reported)."""
    hrp = np.eye(4) if hrp is None else hrp
    torso = hrp @ cf(pose["Root"]["p"], pose["Root"]["R"])
    inv = np.linalg.inv(torso)
    local = xf(inv, target_world) - np.asarray(PIVOT[joint])
    e = np.asarray(END[joint], float)
    R = rot_between(e, local)
    axis = local / np.linalg.norm(local)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])

    def spin(deg):
        a = math.radians(deg)
        return (np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K)

    if ref is not None:  # keep the limb's twist continuous: the spin about the aim line closest to ref
        R = min((spin(d) @ R for d in range(0, 360, 10)), key=lambda C: _angle(C, ref))
    if twist:
        R = spin(twist) @ R
    err = np.linalg.norm(local) - np.linalg.norm(e)  # >0 short of target, <0 passes through it
    return R, err


# ------------------------------------------------------------------ splines
def hermite(keys, t, comp):
    """keys: [(time, value(np array), mode)] sorted. mode 'stop' = zero tangent, 'auto' = Catmull-Rom."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, v0, m0 = keys[i]
        t1, v1, m1 = keys[i + 1]
        if t0 <= t <= t1:
            h = t1 - t0
            s = (t - t0) / h

            def tan(k):
                tk, vk, mk = keys[k]
                if mk == "stop" or k == 0 or k == len(keys) - 1:
                    return np.zeros_like(vk)
                a, b = keys[k - 1], keys[k + 1]
                return (comp(b[1], vk) - comp(a[1], vk) + vk - vk) / (b[0] - a[0])

            d0 = tan(i) * h
            d1 = tan(i + 1) * h
            v1c = comp(v1, v0)
            h00 = 2 * s ** 3 - 3 * s ** 2 + 1
            h10 = s ** 3 - 2 * s ** 2 + s
            h01 = -2 * s ** 3 + 3 * s ** 2
            h11 = s ** 3 - s ** 2
            return h00 * v0 + h10 * d0 + h01 * v1c + h11 * d1
    return keys[-1][1]


def qalign(q, ref):
    return q if np.dot(q, ref) >= 0 else -q


def vec_same(v, ref):
    return v

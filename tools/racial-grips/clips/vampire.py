"""Vampire: The Kiss (3.0 s). The vampire hauls the downed victim up to sitting by the collar, tilts the head aside
and bites the neck from behind. The victim shoves and claws at the arm across their chest, weakening with every
drink, then is let go and slumps back to the floor. No blood: the drink is shown with pale life-thread VFX.

Victim HRP: 2.8 studs in front, same facing, lying on the back with the head toward the vampire.
"""
from _util import plant, part_point, root_for_head, r

OFFSET = {"p": [0, 0, -2.8], "yaw": 0}

# ---------------------------------------------------------------- victim (its own HRP space)
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
SIT = {"p": [0, -1.4, 0.85], "r": [8, 0, 0]}
SIT_HIPS = {"RightHip": [88, 0, 12], "LeftHip": [85, 0, -14]}
BITE_V = {"p": [0, -1.32, 0.8], "r": [14, 0, -6]}
BITE_V_J = {"Neck": [8, -12, -32], "RightHip": [70, 0, 15], "LeftHip": [100, 0, -14]}

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [0, 0, 30], "RightShoulder": [10, 0, 25], "LeftShoulder": [10, 0, -25],
     "RightHip": [0, 0, 6], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.22, "Root": {"p": [0, -2.34, 0.05], "r": [86, 0, 3]}, "Neck": [25, 0, 5],
     "RightShoulder": [125, 0, 15], "LeftShoulder": [100, 0, -22], "RightHip": [25, 0, 10]},
    {"t": 0.42, "Root": {"p": [0, -2.32, 0.15], "r": [80, 0, -4]}, "Neck": [20, 0, -10],
     "RightShoulder": [150, 0, 30], "LeftShoulder": [70, 0, -40], "RightHip": [5, 0, 8], "LeftHip": [32, 0, -10]},
    {"t": 0.62, "Root": {"p": [0, -2.0, 0.55], "r": [45, 0, -3]}, "Neck": [-10, 0, -10],
     "RightShoulder": [60, 0, 10], "LeftShoulder": [60, 0, -50], "RightHip": [52, 0, 15], "LeftHip": [46, 0, -6]},
    # the right hand grabs the vampire's arm across the chest and hangs on until 1.9
    {"t": 0.78, "Root": SIT, "Neck": [0, -10, -22], **SIT_HIPS,
     "RightShoulder": {"reach": ("attacker", "Right Arm", [0, 0, 0]), "slide": [0, 0.95, 0]},
     "LeftShoulder": [110, 0, -45]},
    {"t": 0.95, "Root": BITE_V, **BITE_V_J, "LeftShoulder": [150, 0, -62],
     "RightShoulder": {"reach": ("attacker", "Right Arm", [0, 0, 0]), "slide": [0, 0.95, 0]}, "stop": ["Root"]},
    {"t": 1.12, "Root": {"p": [0, -1.34, 0.8], "r": [10, 0, -3]}, "LeftShoulder": [80, 0, -55], "RightHip": [78, 0, 14],
     "LeftHip": [92, 0, -12]},
    {"t": 1.22, "Root": {"p": [0, -1.32, 0.8], "r": [13, 0, -5]}, "LeftHip": [104, 0, -10]},
    {"t": 1.45, "Root": {"p": [0, -1.35, 0.82], "r": [9, 0, -2]}, "LeftShoulder": [120, 0, -45], "RightHip": [96, 0, 13]},
    {"t": 1.62, "Root": {"p": [0, -1.33, 0.8], "r": [12, 0, -4]}, "LeftHip": [88, 0, -13]},
    {"t": 1.82, "Root": {"p": [0, -1.36, 0.8], "r": [11, 0, -2]}, "LeftShoulder": [60, 0, -35], "RightHip": [86, 0, 12],
     "RightShoulder": {"reach": ("attacker", "Right Arm", [0, 0, 0]), "slide": [0, 0.95, 0]}},
    {"t": 2.02, "Root": {"p": [0, -1.38, 0.8], "r": [14, 0, -4]}, "LeftShoulder": [22, 0, -22], "RightShoulder": [35, 0, 18],
     "LeftHip": [90, 0, -14], "Neck": [-15, -10, -28]},
    {"t": 2.3, "Root": {"p": [0, -1.62, 0.78], "r": [26, 0, -8]}, "Neck": [-38, 0, -20], "RightShoulder": [15, 0, 22],
     "LeftShoulder": [10, 0, -25]},
    {"t": 2.6, "Root": {"p": [0, -2.4, 0.2], "r": [90, 0, -6]}, "Neck": [8, 0, 40], "RightShoulder": [22, 0, 45],
     "LeftShoulder": [14, 0, -50], "RightHip": [6, 0, 10], "LeftHip": [0, 0, -12], "stop": ["Root"]},
    {"t": 2.7, "Root": {"p": [0, -2.34, 0.2], "r": [87, 0, -5]}, "Neck": [4, 0, 46]},
    {"t": 3.0, "Root": {"p": [0, -2.38, 0.2], "r": [90, 0, -6]}, "Neck": [8, 0, 44], "RightShoulder": [20, 0, 48],
     "LeftShoulder": [14, 0, -52], "stop": True},
]

# ---------------------------------------------------------------- attacker
from _util import kneel_legs, kneel_root, kneel_fit, stand_legs, root_for_legs, fit  # noqa: E402
import rig  # noqa: E402

# the owner's kneel (mirrored: left foot ahead) on the victim's left, behind the shoulder; the planted front leg runs
# down the victim's left side, clear of the body. Placed so a hunched lean puts the mouth on the neck.
KX, KYAW, KFRONT = -0.4, 0.0, "RightHip"   # the game's crouch, mirrored (right foot ahead): placement searched for bite, collar and clearance
BITE_NECK = [-14, -20, 18]
bite_target = part_point(OFFSET, BITE_V, BITE_V_J, "Torso", [-0.55, 1.35, 0.35])


def _head(root, neck):
    import numpy as _np
    R = rig.euler(root["r"])
    return _np.asarray(root["p"]) + R @ (_np.asarray(rig.PIVOT["Neck"]) + rig.euler(neck) @ _np.asarray(rig.CENTRE["Neck"]))


def _solve_bite():
    best = None
    for lean in range(-28, 16, 2):
        for turn in range(-30, 32, 2):
            h = _head(kneel_root(KX, 0.0, KYAW, lean, turn, 4, KFRONT), BITE_NECK)
            err = abs(h[0] - bite_target[0]) + abs(h[1] - bite_target[1])
            if best is None or err < best[0]:
                best = (err, lean, turn, float(bite_target[2] - h[2]))
    return best


_b = _solve_bite()
BL, BT, KZ = float(_b[1]), float(_b[2]), round(_b[3], 3)
VK = kneel_legs(KX, KZ, KYAW, front=KFRONT, kid="vampire")
VS = stand_legs(0.0, 0.0, stance=0.6, spread=0.3)
VS_END = stand_legs(-0.6, -0.35, stance=0.7, spread=0.35)
COLLAR = {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]}
HOLD = {"reach": ("victim", "Torso", [-0.75, 0.75, 0.25]), "slide": [0.2, 0.2, 0.25]}
_KF = VK[KFRONT]["plant"][:3, 3]
STEP = {"reach": ("world", None, [float(_KF[0]) * 0.8, -2.55, float(_KF[2]) * 0.8]), "slide": [0.3, 0, 0.3]}


def kroot(z, lean, yaw=0.0, roll=0.0):
    """Kneeling, near upright: lean / turn / roll about the hips."""
    return kneel_root(KX, KZ, KYAW, max(-28, min(15, lean + 12)), yaw, roll, KFRONT)


def croot(t, z, lean, yaw=0.0, roll=0.0):
    """Kneeling, leaning in just enough that the right hand has the collar at time t."""
    from _util import body_point
    tgt = body_point(victim, OFFSET, t, "Torso", [0.45, 0.6, -0.5])
    return kneel_fit(KX, KZ, KYAW, "RightShoulder", tgt, turn=yaw + BT * 0.5, roll=roll, rng=(-25, 15), front=KFRONT)


BITE = kneel_root(KX, KZ, KYAW, BL, BT, 4, KFRONT)


def bite(dy, dz, rr):
    """The drinking bob around the bite: rr is the old absolute pose; only its change from the bite pose is used."""
    return kneel_root(KX, KZ, KYAW, BL + (rr[0] + 50) * 0.6, BT + (rr[1] + 18) * 0.6, 4 + (rr[2] - 8), KFRONT)


attacker = [
    # looms over the body: a slow forward creep, head cocked, hands curling like claws
    {"t": 0.0, "Root": root_for_legs({"p": [0, 0, 0], "r": [-4, 0, 0]}, VS), **VS, "Neck": [-18, 0, 10],
     "RightShoulder": [20, 0, 18], "LeftShoulder": [20, 0, -18], "stop": True},
    {"t": 0.2, "Root": root_for_legs({"p": [0, 0, -0.12], "r": [-16, 4, 3]}, VS), "Neck": [-30, 10, 22],
     "RightShoulder": [55, 0, 30], "LeftShoulder": [48, 0, -30]},
    {"t": 0.3, "Root": root_for_legs({"p": [-0.5, 0, -0.3], "r": [-24, -6, 4]}, {"LeftHip": STEP}),
     "LeftHip": STEP, "RightHip": [-32, 0, 6], "Neck": [-30, 8, 18]},
    # sinks to the knee and takes the collar (0.4)
    {"t": 0.4, "Root": croot(0.4, -0.55, -30), **VK, "Neck": [-28, 6, 14], "RightShoulder": COLLAR,
     "LeftShoulder": [60, 0, -32], "stop": ["Root"]},
    {"t": 0.6, "Root": croot(0.6, -0.6, -22, 0, 3), "Neck": [-14, 0, 8], "RightShoulder": COLLAR, "LeftShoulder": HOLD},
    # drags the body up against its knee; the head draws back, savouring (anticipation, slow)
    {"t": 0.82, "Root": croot(0.82, -0.5, -6, 6, 6), "Neck": [26, 8, 14], "RightShoulder": COLLAR, "LeftShoulder": HOLD,
     "stop": ["Neck"]},
    {"t": 0.89, "Root": croot(0.89, -0.48, -2, 8, 8), "Neck": [32, 10, 16]},
    # the strike: the head snaps down into the neck (0.95), then presses deeper
    {"t": 0.95, "Root": BITE, "Neck": BITE_NECK, "RightShoulder": COLLAR, "LeftShoulder": HOLD, "stop": ["Root"]},
    {"t": 1.05, "Root": bite(-0.07, -0.05, [-54, -19, 9]), "Neck": [-18, -22, 20]},
    # three long drinks: shoulders rise and roll, the body pulled tighter each time
    {"t": 1.2, "Root": bite(0.05, 0.0, [-46, -16, 7])},
    {"t": 1.38, "Root": bite(-0.04, -0.03, [-53, -20, 10])},
    {"t": 1.6, "Root": bite(0.06, 0.0, [-45, -15, 6])},
    {"t": 1.78, "Root": bite(-0.03, -0.03, [-52, -20, 10])},
    {"t": 2.0, "Root": bite(0.05, 0.0, [-46, -16, 7]), "Neck": [-12, -20, 16]},
    {"t": 2.2, "Root": bite(-0.02, 0.0, [-50, -18, 8]), "RightShoulder": COLLAR, "LeftShoulder": HOLD},
    # lets the head fall back, sated, and lets go
    {"t": 2.38, "Root": kroot(-0.45, 2, 4, -2), **VK, "Neck": [42, 0, -10], "RightShoulder": [70, 0, 30],
     "LeftShoulder": [80, 0, -34], "stop": ["Neck"]},
    # rises to stand over the body, head tilted, looking down at it
    {"t": 2.7, "Root": root_for_legs({"p": [0, -0.2, -0.3], "r": [-10, 6, 4]}, VS_END), **VS_END, "Neck": [-24, 12, 18],
     "RightShoulder": [30, 0, 22], "LeftShoulder": [26, 0, -20]},
    {"t": 3.0, "Root": root_for_legs({"p": [0, 0, -0.3], "r": [-12, 8, 5]}, VS_END), "Neck": [-30, 14, 24],
     "RightShoulder": [22, 0, 18], "LeftShoulder": [18, 0, -16], "stop": True},
]


# ---------------------------------------------------------------- heads (2.6.2): eyes on what the body is doing
from _util import look, set_necks  # noqa: E402
_V, _A = "victim", "attacker"
_NECK = [-0.55, 1.35, 0.35]
set_necks(attacker, {
    0.0: look(_V, "Head", tilt=(0, 0, 10)), 0.2: look(_V, "Head", tilt=(0, 10, 22)), 0.3: look(_V, "Head", tilt=(0, 8, 18)),
    0.4: look(_V, "Torso", _NECK, (0, 6, 14)), 0.6: look(_V, "Torso", _NECK, (0, 0, 8)),     # locks onto the neck
    0.82: look(_V, "Torso", _NECK, (18, 8, 14)), 0.89: look(_V, "Torso", _NECK, (24, 10, 16)),  # draws back, savouring
    2.7: look(_V, "Head", tilt=(0, 12, 18)), 3.0: look(_V, "Head", tilt=(0, 14, 24)),         # looks down at the body
})
set_necks(victim, {
    0.0: look(_A, "Head", tilt=(0, 0, 8)), 0.22: look(_A, "Head", tilt=(-6, 0, 0)), 0.42: look(_A, "Head", tilt=(0, 0, -6)),
})

CLIP = {
    "name": "GripVampire", "length": 3.0, "offset": OFFSET,
    "markers": [(0.4, "Grab"), (0.95, "Bite"), (1.2, "Drink"), (1.6, "Drink"), (2.0, "Drink"), (2.3, "Release"),
                (2.6, "Finish"), (2.7, "Wipe")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact", "waive_attacker": "groundContact",  # animpro cannot see the tucked crouch legs
}

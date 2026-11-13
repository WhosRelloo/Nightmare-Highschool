"""Priest: Exorcism (3.2 s). The priest kneels, presses a hand to the forehead and raises the other high (the cross
forms over it in VFX). The possessed body fights: violent arches, drumming heels, a head whipping under the hand,
a hand grabbing the priest's wrist, then a rigid arch that lifts the chest a stud off the floor. On the final word
the priest slams the raised hand onto the chest: the arch snaps flat and the body goes still. The priest bows.

Victim HRP: 2.5 studs in front, turned -90 deg (lying across, head on the priest's LEFT under the left hand).
"""
from _util import plant, fit, body_point

OFFSET = {"p": [0, 0, -2.5], "yaw": -90}
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
FOREHEAD = [0, 0.15, -0.5]   # face of the head (up when lying)
CHEST = [0, 0.15, -0.5]

# heels drum: alternating hip flicks
DRUM = [(0.92, 18, -4), (1.04, -6, 16), (1.16, 20, -2), (1.28, -4, 18), (1.4, 16, 0), (1.52, 0, 20), (1.64, 22, -2),
        (1.76, -2, 18), (1.88, 18, 2), (2.0, 4, 22), (2.12, 20, 4), (2.24, 6, 16)]

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [0, 0, 20], "RightShoulder": [10, 0, 28], "LeftShoulder": [10, 0, -26],
     "RightHip": [0, 0, 6], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.5, "Root": {"p": [0, -2.36, 0], "r": [89, 0, 0]}, "Neck": [-5, 0, 5]},
    {"t": 0.8, "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}, "Neck": [-8, 0, 0], "RightShoulder": [20, 0, 35]},
    # spasm 1 (1.1): the chest jerks up
    {"t": 1.1, "Root": {"p": [0, -2.0, 0.1], "r": [72, 0, 6]}, "Neck": [40, 0, -30], "RightShoulder": [70, 0, 75],
     "LeftShoulder": [120, 0, -40], "stop": ["Root"]},
    {"t": 1.25, "Root": {"p": [0, -2.4, 0], "r": [91, 0, -3]}, "Neck": [20, 0, 32], "LeftShoulder": [40, 0, -70]},
    # the right hand grabs the priest's wrist and fights it
    {"t": 1.4, "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0, 0]), "slide": [0, 0.9, 0]},
     "Neck": [25, 0, -30]},
    # spasm 2 (1.6)
    {"t": 1.6, "Root": {"p": [0, -1.9, 0.12], "r": [68, 0, -6]}, "Neck": [45, 0, 28], "LeftShoulder": [140, 0, -20],
     "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0, 0]), "slide": [0, 0.9, 0]}, "stop": ["Root"]},
    {"t": 1.75, "Root": {"p": [0, -2.25, 0.05], "r": [84, 0, 4]}, "Neck": [30, 0, -34], "LeftShoulder": [60, 0, -80]},
    # spasm 3 (2.0) rising into the rigid arch, lifted a stud off the floor
    {"t": 2.0, "Root": {"p": [0, -1.75, 0.15], "r": [66, 0, 0]}, "Neck": [55, 0, 25], "LeftShoulder": [20, 0, -85],
     "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0, 0]), "slide": [0, 0.9, 0]}, "stop": ["Root"]},
    {"t": 2.15, "RightShoulder": [30, 0, 85], "Neck": [55, 0, -22]},
    {"t": 2.38, "Root": {"p": [0, -1.4, 0.2], "r": [62, 0, 0]}, "Neck": [62, 0, 6], "RightShoulder": [15, 0, 88],
     "LeftShoulder": [15, 0, -88], "RightHip": [-24, 0, 8], "LeftHip": [-24, 0, -8], "stop": ["Root"]},
    # the strike (2.45): snapped flat
    {"t": 2.5, "Root": {"p": [0, -2.48, 0.05], "r": [92, 0, 0]}, "Neck": [0, 0, 0], "RightShoulder": [40, 0, 70],
     "LeftShoulder": [40, 0, -72], "RightHip": [6, 0, 10], "LeftHip": [4, 0, -10], "stop": ["Root"]},
    {"t": 2.6, "Root": {"p": [0, -2.34, 0.05], "r": [89, 0, 0]}, "RightShoulder": [18, 0, 60], "LeftShoulder": [16, 0, -60]},
    {"t": 2.8, "Root": {"p": [0, -2.38, 0.05], "r": [90, 0, 0]}, "Neck": [6, 0, -38], "RightShoulder": [12, 0, 55],
     "LeftShoulder": [12, 0, -58]},
    {"t": 3.2, "Root": {"p": [0, -2.38, 0.05], "r": [90, 0, 0]}, "Neck": [6, 0, -42], "stop": True},
]
for t, a, b in DRUM:
    k = next((k for k in victim if abs(k["t"] - t) < 0.03), None)
    if k is None:
        k = {"t": t}
        victim.append(k)
    k["RightHip"] = [a, 0, 8]
    k["LeftHip"] = [b, 0, -8]
victim.sort(key=lambda k: k["t"])

KNEEL = {"RightHip": [-55, 0, 6], "LeftHip": [85, 0, -6]}  # right knee down, left foot forward


def kneel(x, z, rr, hips=KNEEL):
    return plant({"p": [x, 0, z], "r": rr}, hips)


def strike_hold(t, x, z, rr):
    """Lean so the right palm lands on the chest, then re-check the left hand (it slides on the head)."""
    tgt = body_point(victim, OFFSET, t, "Torso", [0.3, 0.15, -0.5])
    return fit(plant({"p": [x, 0, z], "r": rr}, KNEEL), KNEEL, "RightShoulder", tgt, vary="lean", lo=-70, hi=10,
               plant_parts=("Right Leg", "Left Leg"))


def hold(t, x, z, rr, extra_lean=0):
    """Kneel, leaning (root pitch) so the left hand stays on the forehead at time t."""
    tgt = body_point(victim, OFFSET, t, "Head", FOREHEAD)
    out = fit(plant({"p": [x, 0, z], "r": rr}, KNEEL), KNEEL, "LeftShoulder", tgt, vary="lean", lo=-60, hi=25,
              plant_parts=("Right Leg", "Left Leg"))
    return out


HAND_ON_HEAD = {"reach": ("victim", "Head", FOREHEAD), "slide": [0, 0.3, 0.3]}

attacker = [
    {"t": 0.0, "Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [-10, 0, 0], "RightShoulder": [55, 0, -28],
     "LeftShoulder": [55, 0, 28], "stop": True},
    {"t": 0.2, "Root": plant({"p": [-0.3, 0, -0.2], "r": [-6, 0, 0]}, {"RightHip": [-20, 0, 6], "LeftHip": [40, 0, -6]}),
     "RightHip": [-20, 0, 6], "LeftHip": [40, 0, -6], "Neck": [-20, 0, 0], "LeftShoulder": [40, 0, 10]},
    {"t": 0.48, "Root": hold(0.48, -0.55, -0.45, [-18, 0, 0]), **KNEEL, "Neck": [-28, -10, 0],
     "LeftShoulder": HAND_ON_HEAD, "RightShoulder": [80, 0, 20], "stop": ["Root"]},
    {"t": 0.85, "Root": hold(0.85, -0.55, -0.45, [-10, 0, 3]), "LeftShoulder": HAND_ON_HEAD, "RightShoulder": {"reach": ("world", None, [0.9, 4.5, -0.7])},
     "Neck": [-15, -10, 0]},
    # bracing against each spasm, the raised hand trembling
    {"t": 1.12, "Root": hold(1.12, -0.55, -0.4, [-4, 0, 5]), "RightShoulder": {"reach": ("world", None, [1.05, 4.5, -0.62])}, "Neck": [-10, -14, 0]},
    {"t": 1.3, "Root": hold(1.3, -0.55, -0.45, [-12, 0, 2]), "RightShoulder": {"reach": ("world", None, [0.88, 4.5, -0.74])}},
    {"t": 1.62, "Root": hold(1.62, -0.55, -0.38, [-3, 0, -4]), "RightShoulder": {"reach": ("world", None, [1.06, 4.5, -0.6])}, "Neck": [-6, -8, 0]},
    {"t": 1.8, "Root": hold(1.8, -0.55, -0.45, [-12, 0, 2]), "RightShoulder": {"reach": ("world", None, [0.9, 4.5, -0.7])}},
    {"t": 2.02, "Root": hold(2.02, -0.55, -0.38, [-2, 0, 5]), "RightShoulder": {"reach": ("world", None, [1.08, 4.5, -0.64])}, "Neck": [-4, -12, 0]},
    {"t": 0.95, "Root": hold(0.95, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.05, "Root": hold(1.05, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.2, "Root": hold(1.2, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.4, "Root": hold(1.4, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.5, "Root": hold(1.5, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.7, "Root": hold(1.7, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.9, "Root": hold(1.9, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.1, "Root": hold(2.1, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.2, "Root": hold(2.2, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.28, "Root": hold(2.28, -0.55, -0.42, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    # wind-up: lean back, hand higher and back
    {"t": 2.36, "Root": hold(2.36, -0.55, -0.3, [6, 0, 0]), "RightShoulder": {"reach": ("world", None, [1.25, 4.5, -0.15])}, "Neck": [6, -6, 0],
     "LeftShoulder": HAND_ON_HEAD, "stop": ["Root", "RightShoulder"]},
    # STRIKE at 2.45: palm onto the chest
    {"t": 2.46, "Root": strike_hold(2.46, -0.55, -0.6, [-34, 0, 0]), "Neck": [-30, -6, 0],
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.5, 0.4, 0]}, "LeftShoulder": HAND_ON_HEAD,
     "stop": ["Root"]},
    {"t": 2.62, "Root": strike_hold(2.62, -0.55, -0.62, [-36, 0, 0]),
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.5, 0.4, 0]}, "LeftShoulder": HAND_ON_HEAD},
    # withdraw, bow
    {"t": 2.9, "Root": kneel(-0.55, -0.45, [-14, 0, 0]), "RightShoulder": [55, 0, -25], "LeftShoulder": [55, 0, 25],
     "Neck": [-38, 0, 0]},
    {"t": 3.2, "Root": kneel(-0.55, -0.45, [-12, 0, 0]), "RightShoulder": [58, 0, -28], "LeftShoulder": [58, 0, 28],
     "Neck": [-42, 0, 0], "stop": True},
]

CLIP = {
    "name": "GripPriest", "length": 3.2, "offset": OFFSET,
    "markers": [(0.48, "Seal"), (0.85, "Cross"), (1.1, "Spasm"), (1.6, "Spasm"), (2.0, "Spasm"), (2.45, "Strike"),
                (2.45, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact", "waive_attacker": "rootDrift",
}

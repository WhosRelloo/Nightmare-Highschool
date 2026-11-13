"""Wraith: Soul Siphon (3.0 s). The wraith floats, rises and spreads its arms, dives a palm onto the chest, then
draws the hand slowly up: the victim's chest arches after it as if pulled on a string (heels and head on the floor,
arms clawing the air), until the fist yanks and the body slams down limp. The wraith draws the fist to its chest.
The soul itself is VFX (a translucent copy of the victim stretched between the chest and the palm).

Victim HRP: 2.5 studs in front, turned 90 deg (lying across, head on the wraith's right).
"""
from _util import plant, fit, body_point, heels

OFFSET = {"p": [0, 0, -2.5], "yaw": 90}
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
CHEST = [0, 0.2, -0.5]

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [0, 0, -25], "RightShoulder": [12, 0, 30], "LeftShoulder": [10, 0, -28],
     "RightHip": [0, 0, 8], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.35, "Root": {"p": [0, -2.36, 0], "r": [88, 0, 0]}, "Neck": [-15, 0, -5], "RightShoulder": [50, 0, 25],
     "LeftShoulder": [40, 0, -30]},
    # the palm lands (0.6): a cold jolt
    {"t": 0.6, "Root": {"p": [0, -2.45, 0], "r": [93, 0, 0]}, "Neck": [-25, 0, 0], "RightShoulder": [80, 0, 40],
     "LeftShoulder": [85, 0, -45], "RightHip": [20, 0, 8], "stop": ["Root"]},
    {"t": 0.72, "Root": {"p": [0, -2.34, 0], "r": [88, 0, 0]}, "Neck": [10, 0, 0]},
    # drawn up: chest arches toward the rising hand, head falls back, heels stay down
    {"t": 1.1, "Root": {"p": [0, -2.05, 0.1], "r": [78, 0, 0]}, "Neck": [35, 0, 6], "RightShoulder": [40, 0, 30],
     "LeftShoulder": [110, 0, -25], "RightHip": [-14, 0, 8], "LeftHip": [-10, 0, -6]},
    {"t": 1.35, "LeftShoulder": [70, 0, -45], "RightShoulder": [115, 0, 20], "Neck": [42, 0, -8]},
    {"t": 1.6, "Root": {"p": [0, -1.7, 0.15], "r": [70, 0, 4]}, "LeftShoulder": [125, 0, -15], "RightShoulder": [60, 0, 45],
     "RightHip": [-22, 0, 10], "LeftHip": [-18, 0, -8], "Neck": [50, 0, 10]},
    {"t": 1.85, "LeftShoulder": [65, 0, -55], "RightShoulder": [120, 0, 15], "Neck": [55, 0, -10]},
    {"t": 2.1, "Root": {"p": [0, -1.4, 0.2], "r": [64, 0, -3]}, "LeftShoulder": [30, 0, -40], "RightShoulder": [25, 0, 40],
     "RightHip": [-28, 0, 10], "LeftHip": [-25, 0, -8], "Neck": [62, 0, 4]},
    {"t": 2.22, "Root": {"p": [0, -1.32, 0.2], "r": [60, 0, 0]}, "Neck": [66, 0, 0], "stop": ["Root"]},
    # the yank: the body slams down
    {"t": 2.33, "Root": {"p": [0, -2.45, 0.05], "r": [92, 0, 0]}, "Neck": [5, 0, 30], "RightShoulder": [10, 0, 60],
     "LeftShoulder": [10, 0, -62], "RightHip": [4, 0, 10], "LeftHip": [0, 0, -8], "stop": ["Root"]},
    {"t": 2.42, "Root": {"p": [0, -2.3, 0.05], "r": [88, 0, 0]}, "Neck": [10, 0, 40], "RightShoulder": [22, 0, 55]},
    {"t": 2.6, "Root": {"p": [0, -2.38, 0.05], "r": [90, 0, 0]}, "Neck": [8, 0, 46], "RightShoulder": [14, 0, 62],
     "LeftShoulder": [12, 0, -64]},
    {"t": 3.0, "Root": {"p": [0, -2.38, 0.05], "r": [90, 0, 0]}, "Neck": [8, 0, 48], "stop": True},
]

HEELS = heels(OFFSET, LIE, (1, 0, 0))
for k in victim:
    if 1.05 <= k["t"] <= 2.22:  # drawn up by the chest: heels stay on the floor
        k.update(HEELS)

FLOAT_HIPS = {"RightHip": [-22, 0, 6], "LeftHip": [-30, 0, -6]}


def hover(y, z, rr):
    return {"p": [0, y, z], "r": rr}


_chest06 = body_point(victim, OFFSET, 0.6, "Torso", CHEST)
_chest072 = body_point(victim, OFFSET, 0.72, "Torso", CHEST)
DIVE = fit(hover(0, -0.8, [-42, 0, 0]), {}, "RightShoulder", _chest06, vary="y", lo=-1.2, hi=1.5)
DIVE2 = fit(hover(0, -0.85, [-44, 0, 0]), {}, "RightShoulder", _chest072, vary="y", lo=-1.2, hi=1.5)

attacker = [
    {"t": 0.0, "Root": hover(0.35, 0, [4, 0, 0]), **FLOAT_HIPS, "Neck": [-22, 0, 30], "RightShoulder": [10, 0, 6],
     "LeftShoulder": [10, 0, -6], "stop": True},
    {"t": 0.22, "Root": hover(0.6, 0.05, [8, 0, 0]), "RightShoulder": [-5, 0, 45], "LeftShoulder": [-5, 0, -45],
     "Neck": [5, 0, 0]},
    {"t": 0.45, "Root": hover(0.95, 0.1, [12, 0, 0]), "RightShoulder": [-12, 0, 80], "LeftShoulder": [-10, 0, -82],
     "Neck": [22, 0, -24], "stop": ["Root"]},
    # the dive: palm onto the chest at 0.6
    {"t": 0.6, "Root": DIVE, "Neck": [-10, 0, 0],
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0, 0.3, 0]}, "LeftShoulder": [-30, 0, -70],
     "RightHip": [-62, 0, 10], "LeftHip": [-72, 0, -10], "Neck": [-18, 0, 28]},
    {"t": 0.72, "Root": DIVE2,
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0, 0.3, 0]}},
    # the slow pull: the wraith rises and leans back, the hand climbing above the chest
    {"t": 1.1, "Root": hover(0.55, -0.65, [-36, 0, 0]), "RightShoulder": {"reach": ("victim", "Torso", [0, 0.2, -1.1])}, "LeftShoulder": [-25, 0, -75],
     "Neck": [-24, 0, 26], "RightHip": [-12, 0, 6], "LeftHip": [-22, 0, -6]},
    {"t": 1.6, "Root": hover(0.9, -0.5, [-24, 0, 0]), "RightShoulder": {"reach": ("victim", "Torso", [0, 0.2, -1.6])}, "Neck": [-12, 0, -4]},
    {"t": 2.1, "Root": hover(1.25, -0.35, [-12, 0, 0]), "RightShoulder": {"reach": ("victim", "Torso", [0, 0.2, -2.0])}, "LeftShoulder": [-30, 0, -80],
     "Neck": [-8, 0, 0], "RightHip": [-30, 0, 6], "LeftHip": [-40, 0, -6]},
    {"t": 2.2, "Root": hover(1.22, -0.33, [-14, 0, 0]), "RightShoulder": {"reach": ("victim", "Torso", [0, 0.2, -2.1])}, "stop": ["RightShoulder"]},
    # the yank (2.25): fist rips straight up, body jerks back
    {"t": 2.27, "Root": hover(1.45, -0.2, [6, 0, 0]), "RightShoulder": [172, 0, 4], "Neck": [20, 0, 0],
     "stop": ["Root", "RightShoulder"]},
    # the soul is drawn into the chest
    {"t": 2.5, "Root": hover(1.2, -0.1, [10, 0, 0]), "RightShoulder": [95, 0, -45], "LeftShoulder": [40, 0, -35],
     "Neck": [32, 0, 6]},
    {"t": 2.75, "Root": hover(0.75, 0, [6, 0, 0]), "RightShoulder": [60, 0, -40], "LeftShoulder": [25, 0, -20],
     "Neck": [28, 0, -4], **FLOAT_HIPS},
    {"t": 3.0, "Root": hover(0.45, 0, [4, 0, 0]), "RightShoulder": [25, 0, -10], "LeftShoulder": [15, 0, -12],
     "Neck": [5, 0, 6], "stop": True},
]

CLIP = {
    "name": "GripWraith", "length": 3.0, "offset": OFFSET, "grounded": False,
    "markers": [(0.0, "Frost"), (0.6, "Palm"), (0.72, "Pull"), (2.25, "Yank"), (2.5, "Absorb"), (2.85, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact",
}

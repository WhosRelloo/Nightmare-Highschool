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
KNEEL_HIPS = {"RightHip": [95, 0, 4], "LeftHip": [-15, 0, -6]}


def kneel(p_xz, rr, hips=KNEEL_HIPS):
    return plant({"p": [p_xz[0], 0, p_xz[1]], "r": rr}, hips)


# bite: put the vampire's head just above-behind the victim's left neck, at the victim's bite pose
bite_target = part_point(OFFSET, BITE_V, BITE_V_J, "Torso", [-0.55, 1.35, 0.35])
BITE_R = [-58, -15, 5]
BITE_NECK = [-5, -14, 12]
bite_root = root_for_head(bite_target, BITE_R, BITE_NECK)
BITE = {"p": r(bite_root), "r": BITE_R}

attacker = [
    {"t": 0.0, "Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [-12, 0, 0], "RightShoulder": [0, 0, 8],
     "LeftShoulder": [0, 0, -8], "stop": True},
    {"t": 0.16, "Root": {"p": [0, 0.05, 0.1], "r": [5, 6, 0]}, "Neck": [-18, 0, 0], "RightShoulder": [-15, 0, 20],
     "LeftShoulder": [10, 0, -15], "stop": True},
    {"t": 0.27, "Root": {"p": [0, -0.04, -0.2], "r": [-14, 0, 0]}, "RightHip": [45, 0, 4], "LeftHip": [-4, 0, -6],
     "Neck": [-22, 0, 0]},
    {"t": 0.33, "Root": kneel((0, -0.5), [-26, 0, 0], {"RightHip": [75, 0, 4], "LeftHip": [-10, 0, -6]}),
     "RightHip": [75, 0, 4], "LeftHip": [-10, 0, -6]},
    {"t": 0.4, "Root": kneel((0, -0.75), [-38, 0, 0]), **KNEEL_HIPS, "Neck": [-25, 0, 0],
     "RightShoulder": {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]}, "LeftShoulder": [55, 0, -25]},
    {"t": 0.6, "Root": kneel((0, -0.8), [-24, 0, 0]), "Neck": [-15, 0, 0],
     "RightShoulder": {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", [-0.75, 0.75, 0.25]), "slide": [0.2, 0.2, 0.25]}},
    {"t": 0.82, "Root": kneel((0, -0.55), [-10, 0, 4]), "Neck": [14, 0, 0],
     "RightShoulder": {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", [-0.75, 0.75, 0.25]), "slide": [0.2, 0.2, 0.25]}, "stop": ["Root", "Neck"]},
    {"t": 0.95, "Root": BITE, "Neck": BITE_NECK,
     "RightShoulder": {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", [-0.75, 0.75, 0.25]), "slide": [0.2, 0.2, 0.25]}},
    {"t": 1.04, "Root": {"p": r([bite_root[0], bite_root[1] - 0.06, bite_root[2] - 0.04]), "r": [-61, -16, 6]},
     "stop": ["Root"]},
    {"t": 1.2, "Root": {"p": r([bite_root[0], bite_root[1] + 0.05, bite_root[2]]), "r": [-55, -14, 5]}},
    {"t": 1.36, "Root": {"p": r([bite_root[0], bite_root[1] - 0.03, bite_root[2] - 0.02]), "r": [-60, -16, 6]}},
    {"t": 1.6, "Root": {"p": r([bite_root[0], bite_root[1] + 0.06, bite_root[2]]), "r": [-54, -14, 5]}},
    {"t": 1.76, "Root": {"p": r([bite_root[0], bite_root[1] - 0.02, bite_root[2] - 0.02]), "r": [-59, -15, 6]}},
    {"t": 2.0, "Root": {"p": r([bite_root[0], bite_root[1] + 0.05, bite_root[2]]), "r": [-55, -14, 5]},
     "Neck": [-8, -12, 12]},
    {"t": 2.22, "Root": {"p": r([bite_root[0], bite_root[1] - 0.02, bite_root[2]]), "r": [-58, -15, 5]},
     "RightShoulder": {"reach": ("victim", "Torso", [0.45, 0.2, -0.5]), "slide": [0, 0.75, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", [-0.75, 0.75, 0.25]), "slide": [0.2, 0.2, 0.25]}},
    {"t": 2.38, "Root": kneel((0, -0.5), [-6, 4, 0]), "Neck": [38, 0, 0], "RightShoulder": [45, 0, 25],
     "LeftShoulder": [70, 0, -35], "stop": ["Neck"]},
    {"t": 2.62, "Root": kneel((0, -0.45), [-4, 2, 0]), "Neck": [12, -12, 0],
     "RightShoulder": {"reach": ("self", "Head", [0.15, -0.35, -0.55])}, "LeftShoulder": [20, 0, -15]},
    {"t": 2.82, "Root": kneel((0, -0.45), [-5, 0, 0]), "Neck": [6, -18, 0],
     "RightShoulder": {"reach": ("self", "Head", [-0.2, -0.3, -0.55])}},
    {"t": 3.0, "Root": kneel((0, -0.45), [-6, 0, 0]), "Neck": [0, -10, 0], "RightShoulder": [25, 0, 12],
     "LeftShoulder": [12, 0, -12], "stop": True},
]

CLIP = {
    "name": "GripVampire", "length": 3.0, "offset": OFFSET,
    "markers": [(0.4, "Grab"), (0.95, "Bite"), (1.2, "Drink"), (1.6, "Drink"), (2.0, "Drink"), (2.3, "Release"),
                (2.6, "Finish"), (2.7, "Wipe")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact",
}

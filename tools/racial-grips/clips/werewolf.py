"""Werewolf: Maul (2.8 s). Snarl, pounce onto all fours over the body, pin the chest, three alternating raking
swipes (the victim's guard is knocked open on each), the victim rolls and claws away and is hauled back by the
shoulders, a dog-like shake, then the wolf rears up and howls while the body goes still. No blood or wounds:
silver claw streaks, fur tufts and dust in the VFX.

Victim HRP: 2.6 studs in front, turned 90 deg (lying across in front of the wolf, head on the wolf's right).
Victim-local axes after the turn: local +x points AWAY from the wolf, local -z points to the wolf's left.
"""
from _util import plant, fit, body_point

OFFSET = {"p": [0, 0, -2.6], "yaw": 90}

LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
CHEST = [0, 0.15, -0.5]          # front face of the torso (faces up when lying)
SLIDE_V = [0, 0.6, 0]
SHOULDER_R = [-0.9, 0.8, -0.3]  # near shoulder (victim's left, the side facing the wolf): wolf's right hand
SHOULDER_L = [-0.9, -0.8, -0.3]  # near hip: wolf's left hand


def pin(side_slide=None):
    return {"reach": ("victim", "Torso", CHEST), "slide": side_slide or SLIDE_V}


victim = [
    {"t": 0.0, "Root": LIE, "Neck": [-5, 0, -20], "RightShoulder": [10, 0, 30], "LeftShoulder": [5, 0, -25],
     "RightHip": [0, 0, 8], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.16, "Root": {"p": [0, -2.36, 0], "r": [86, 0, 0]}, "Neck": [-25, 0, -40], "RightShoulder": [60, 0, 25],
     "LeftShoulder": [70, 0, -15]},
    # shield the face as the wolf lands
    {"t": 0.4, "Root": {"p": [0, -2.46, 0], "r": [92, 0, 0]}, "Neck": [-20, 0, -15], "RightShoulder": [135, 0, -20],
     "LeftShoulder": [140, 0, 25], "RightHip": [30, 0, 10], "LeftHip": [5, 0, -6], "stop": ["Root"]},
    {"t": 0.5, "Root": {"p": [0, -2.38, 0], "r": [89, 0, 0]}, "RightShoulder": [128, 0, -25], "LeftShoulder": [135, 0, 22]},
    # swipe 1 (wolf's right hand, 0.65): guard knocked open, head whips
    {"t": 0.6, "RightShoulder": [132, 0, -22], "LeftShoulder": [138, 0, 25], "Neck": [-18, 0, -10]},
    {"t": 0.68, "Root": {"p": [0, -2.44, 0], "r": [93, -14, 0]}, "RightShoulder": [40, 0, 85], "LeftShoulder": [120, 0, 40],
     "Neck": [10, 0, 45], "RightHip": [55, 0, 12], "stop": ["Root", "RightShoulder"]},
    {"t": 0.84, "Root": {"p": [0, -2.38, 0], "r": [89, -4, 0]}, "RightShoulder": [125, 0, -15], "Neck": [-15, 0, 10],
     "RightHip": [10, 0, 10]},
    # swipe 2 (left hand, 0.95)
    {"t": 0.98, "Root": {"p": [0, -2.44, 0], "r": [93, 16, 0]}, "LeftShoulder": [35, 0, -88], "RightShoulder": [110, 0, -30],
     "Neck": [12, 0, -50], "LeftHip": [50, 0, -10], "stop": ["Root", "LeftShoulder"]},
    {"t": 1.13, "Root": {"p": [0, -2.38, 0], "r": [89, 5, 0]}, "LeftShoulder": [120, 0, 20], "Neck": [-10, 0, -5],
     "LeftHip": [8, 0, -6]},
    # swipe 3 (right, 1.25): flung wide, the guard is gone
    {"t": 1.28, "Root": {"p": [0, -2.45, 0], "r": [94, -18, 0]}, "RightShoulder": [15, 0, 95], "LeftShoulder": [60, 0, -70],
     "Neck": [15, 0, 55], "RightHip": [45, 0, 14], "stop": ["Root", "RightShoulder"]},
    # rolls away from the wolf onto the right side and claws at the floor
    {"t": 1.45, "Root": {"p": [0.35, -2.28, 0], "r": [90, 55, 0]}, "RightShoulder": [170, 0, 30], "LeftShoulder": [150, 0, -5],
     "Neck": [-15, 0, 30], "RightHip": [-25, 0, 10], "LeftHip": [35, 0, -8]},
    {"t": 1.56, "Root": {"p": [0.6, -2.18, 0], "r": [90, 75, 0]}, "RightShoulder": [178, 0, 55], "LeftShoulder": [175, 0, -10],
     "RightHip": [20, 0, 8], "LeftHip": [-20, 0, -8]},
    # hauled back by the shoulders and shaken
    {"t": 1.66, "Root": {"p": [-0.15, -2.23, 0], "r": [88, 25, 8]}, "RightShoulder": [150, 0, 70], "LeftShoulder": [120, 0, -40],
     "Neck": [30, 0, 20], "stop": ["Root"]},
    {"t": 1.76, "Root": {"p": [-0.2, -2.18, 0], "r": [86, -10, -10]}, "Neck": [20, -40, 15], "RightShoulder": [70, 0, 60]},
    {"t": 1.86, "Root": {"p": [-0.2, -2.2, 0], "r": [86, 12, 10]}, "Neck": [25, 40, -15], "LeftShoulder": [60, 0, -70]},
    {"t": 1.96, "Root": {"p": [-0.18, -2.18, 0], "r": [86, -8, -8]}, "Neck": [20, -35, 10], "RightShoulder": [30, 0, 75]},
    {"t": 2.08, "Root": {"p": [-0.1, -2.38, 0], "r": [90, 0, 0]}, "Neck": [10, 0, 50], "RightShoulder": [15, 0, 60],
     "LeftShoulder": [10, 0, -65], "RightHip": [5, 0, 12], "LeftHip": [0, 0, -10], "stop": ["Root"]},
    {"t": 2.2, "Root": {"p": [-0.1, -2.34, 0], "r": [88, 0, 0]}, "RightShoulder": [25, 0, 55]},
    {"t": 2.35, "Root": {"p": [-0.1, -2.38, 0], "r": [90, 0, 0]}, "RightShoulder": [12, 0, 62], "Neck": [8, 0, 54]},
    {"t": 2.8, "Root": {"p": [-0.1, -2.38, 0], "r": [90, 0, 0]}, "Neck": [8, 0, 55], "stop": True},
]

# ---------------------------------------------------------------- attacker
FOURS_HIPS = {"RightHip": [50, 0, 10], "LeftHip": [62, 0, -10]}


def fours(p_xz, rr, hips=FOURS_HIPS, parts=("Right Leg", "Left Leg")):
    return plant({"p": [p_xz[0], 0, p_xz[1]], "r": rr}, hips, parts=parts)


def pin_root(t, rr, joint="LeftShoulder"):
    """On all fours, slid along z so `joint`'s hand lands on the chest at time t."""
    tgt = body_point(victim, OFFSET, t, "Torso", [0, 0.15 + 0.3, -0.5])
    return fit({"p": [0, 0, -1.0], "r": rr}, FOURS_HIPS, joint, tgt, vary="z", lo=-2.6, hi=0.5,
               plant_parts=("Right Leg", "Left Leg"))


def haul(t, rr):
    """On all fours, slid along z so the right hand reaches the victim's shoulder at time t."""
    from _util import fit2
    a = body_point(victim, OFFSET, t, "Torso", SHOULDER_R)
    b = body_point(victim, OFFSET, t, "Torso", SHOULDER_L)
    return fit2({"p": [0, -0.4, -1.0], "r": rr}, FOURS_HIPS, "RightShoulder", a, "LeftShoulder", b,
                a_vary="z", b_vary="lean", a_rng=(-2.6, 0.5), b_rng=(-85, -20), plant_parts=("Right Leg", "Left Leg"))


attacker = [
    {"t": 0.0, "Root": plant({"p": [0, 0, 0], "r": [-18, 0, 0]}, {"RightHip": [15, 0, 6], "LeftHip": [-10, 0, -6]}), "Neck": [20, 0, 0], "RightShoulder": [-20, 0, 35],
     "LeftShoulder": [-20, 0, -35], "RightHip": [15, 0, 6], "LeftHip": [-10, 0, -6], "stop": True},
    {"t": 0.1, "Neck": [32, 12, 0], "RightShoulder": [-35, 0, 60], "LeftShoulder": [-30, 0, -62]},
    {"t": 0.16, "Neck": [30, -12, 0]},
    {"t": 0.22, "Neck": [28, 8, 0]},
    # load the pounce
    {"t": 0.3, "Root": plant({"p": [0, 0, 0.35], "r": [-30, 0, 0]}, {"RightHip": [45, 0, 8], "LeftHip": [20, 0, -8]}), "Neck": [10, 0, 0], "RightShoulder": [-70, 0, 40],
     "LeftShoulder": [-65, 0, -40], "RightHip": [45, 0, 8], "LeftHip": [20, 0, -8], "stop": ["Root"]},
    # land on all fours over the body, left hand pinning the chest, right arm cocked
    {"t": 0.42, "Root": pin_root(0.42, [-64, 0, 0], "LeftShoulder"), **FOURS_HIPS, "Neck": [40, 0, 0],
     "LeftShoulder": pin(), "RightShoulder": [150, 0, 40], "stop": ["Root"]},
    {"t": 0.48, "Root": pin_root(0.48, [-66, 0, 2], "LeftShoulder"), "Neck": [44, 0, 0]},
    {"t": 0.56, "Root": pin_root(0.56, [-60, 6, 4], "LeftShoulder"), "RightShoulder": [175, 0, 50], "LeftShoulder": pin()},
    # swipe 1: right hand rakes the chest at 0.65
    {"t": 0.65, "Root": pin_root(0.65, [-68, -10, -6], "RightShoulder"), "RightShoulder": pin([0.6, 0, 0]), "LeftShoulder": pin(),
     "Neck": [30, -15, 0]},
    {"t": 0.74, "Root": fours((0, -1.05), [-64, -14, -6]), "RightShoulder": [30, 0, -30], "LeftShoulder": [150, 0, -40],
     "stop": ["RightShoulder"]},
    {"t": 0.86, "Root": pin_root(0.86, [-60, 8, 5], "RightShoulder"), "RightShoulder": pin(), "LeftShoulder": [175, 0, -50]},
    # swipe 2: left hand at 0.95
    {"t": 0.95, "Root": pin_root(0.95, [-68, 10, 6], "LeftShoulder"), "LeftShoulder": pin([0.6, 0, 0]), "RightShoulder": pin(),
     "Neck": [30, 15, 0]},
    {"t": 1.04, "Root": fours((0, -1.05), [-64, 14, 6]), "LeftShoulder": [30, 0, 30], "RightShoulder": [150, 0, 45],
     "stop": ["LeftShoulder"]},
    {"t": 1.16, "Root": pin_root(1.16, [-60, -8, -5], "LeftShoulder"), "LeftShoulder": pin(), "RightShoulder": [178, 0, 55]},
    # swipe 3: the big one, right hand at 1.25
    {"t": 1.25, "Root": pin_root(1.25, [-72, -14, -8], "RightShoulder"), "RightShoulder": pin([0.7, 0, 0]), "LeftShoulder": pin(),
     "Neck": [26, -20, 0]},
    {"t": 1.36, "Root": fours((0, -1.05), [-62, -16, -8]), "RightShoulder": [20, 0, -40], "stop": ["RightShoulder"]},
    # it crawls off: grab both shoulders and haul it back
    {"t": 1.52, "Root": fours((0, -1.2), [-60, 0, 0]), "RightShoulder": [120, 0, 15], "LeftShoulder": [120, 0, -15],
     "Neck": [38, 0, 0]},
    {"t": 1.6, "Root": haul(1.6, [-66, 0, 0]),
     "RightShoulder": {"reach": ("victim", "Torso", SHOULDER_R), "slide": [0.3, 0.3, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", SHOULDER_L), "slide": [0.3, 0.3, 0]}},
    {"t": 1.68, "Root": haul(1.68, [-50, 0, 0]), "stop": ["Root"],
     "RightShoulder": {"reach": ("victim", "Torso", SHOULDER_R), "slide": [0.3, 0.3, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", SHOULDER_L), "slide": [0.3, 0.3, 0]}},
    {"t": 1.78, "Root": haul(1.78, [-54, 0, -12])},
    {"t": 1.88, "Root": haul(1.88, [-54, 0, 12])},
    {"t": 1.98, "Root": haul(1.98, [-54, 0, -10]), **FOURS_HIPS, "stop": ["RightHip", "LeftHip"],
     "RightShoulder": {"reach": ("victim", "Torso", SHOULDER_R), "slide": [0.3, 0.3, 0]},
     "LeftShoulder": {"reach": ("victim", "Torso", SHOULDER_L), "slide": [0.3, 0.3, 0]}},
    # rear up and howl
    {"t": 2.12, "Root": plant({"p": [0, 0, -0.5], "r": [12, 0, 0]}, {"RightHip": [70, 0, 8], "LeftHip": [-35, 0, -8]}),
     "RightHip": [70, 0, 8], "LeftHip": [-35, 0, -8], "RightShoulder": [-15, 0, 70], "LeftShoulder": [-15, 0, -70],
     "Neck": [45, 0, 0], "stop": ["Root"]},
    {"t": 2.45, "Root": plant({"p": [0, 0, -0.5], "r": [16, 0, 0]}, {"RightHip": [70, 0, 8], "LeftHip": [-35, 0, -8]}),
     "RightShoulder": [-25, 0, 78], "LeftShoulder": [-22, 0, -80], "Neck": [55, 4, 0]},
    {"t": 2.8, "Root": plant({"p": [0, 0, -0.5], "r": [14, 0, 0]}, {"RightHip": [70, 0, 8], "LeftHip": [-35, 0, -8]}),
     "RightShoulder": [-20, 0, 72], "LeftShoulder": [-18, 0, -74], "Neck": [50, -3, 0], "stop": True},
]

CLIP = {
    "name": "GripWerewolf", "length": 2.8, "offset": OFFSET,
    "markers": [(0.1, "Snarl"), (0.42, "Pounce"), (0.65, "Swipe"), (0.95, "Swipe"), (1.25, "Swipe"), (1.6, "Haul"),
                (2.12, "Howl"), (2.12, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact",
}

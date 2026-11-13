"""Human: Hunter's Stake (2.6 s). A knee drops onto the chest, the left hand takes the collar, the stake appears in
the right hand (a prop + silver glint in VFX). The victim grabs the stake arm with both hands and pushes back; the
stake inches down, the arms give way, it's raised high and driven down. No wound, no blood: on a monster the body
crumbles to grey ash in the VFX; on a mortal it is a dust burst and the impact only.

Victim HRP: 2.6 studs in front, turned 90 deg (lying across, head on the hunter's right).
"""
from _util import plant, fit, fit2, body_point

STANCE = {"LeftHip": [-35, 0, -10]}
FOOT = {"reach": ("world", None, [-0.9, -3.0, 0.0]), "slide": [0, 0, 1.6]}  # planted left foot behind

OFFSET = {"p": [0, 0, -2.6], "yaw": -90}
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
CHEST = [0, 0.1, -0.5]
COLLAR = [0, 0.75, -0.5]
PUSH = {"reach": ("attacker", "Torso", [0, -0.2, -0.5]), "slide": [0.9, 1.0, 0]}
STAKE_ARM = {"reach": ("attacker", "Right Arm", [0, 0, 0]), "slide": [0, 1.0, 0]}

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [-5, 0, -15], "RightShoulder": [12, 0, 25], "LeftShoulder": [12, 0, -25],
     "RightHip": [0, 0, 6], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.22, "Root": {"p": [0, -2.36, 0], "r": [88, 0, 0]}, "Neck": [-15, 0, 10], "RightShoulder": [45, 0, 20]},
    # the knee lands (0.3): winded
    {"t": 0.32, "Root": {"p": [0, -2.5, 0], "r": [95, 0, 0]}, "Neck": [-30, 0, 0], "RightShoulder": [95, 0, 30],
     "LeftShoulder": [90, 0, -35], "RightHip": [30, 0, 8], "LeftHip": [25, 0, -8], "stop": ["Root"]},
    {"t": 0.45, "Root": {"p": [0, -2.4, 0], "r": [89, 0, 0]}, "Neck": [10, 0, 0], "RightHip": [5, 0, 6], "LeftHip": [0, 0, -6]},
    {"t": 0.65, "RightShoulder": [110, 0, 10], "LeftShoulder": [105, 0, -12], "Neck": [-10, 0, 0]},
    # both hands on the stake arm, pushing back
    {"t": 0.85, "RightShoulder": STAKE_ARM, "LeftShoulder": PUSH, "RightHip": [35, 0, 8]},
    {"t": 1.0, "Root": {"p": [0, -2.34, 0], "r": [86, 0, 4]}, "LeftHip": [30, 0, -8], "RightHip": [5, 0, 8]},
    {"t": 1.2, "Root": {"p": [0, -2.36, 0], "r": [87, 0, -4]}, "RightHip": [40, 0, 6], "LeftHip": [0, 0, -6]},
    {"t": 1.45, "Root": {"p": [0, -2.34, 0], "r": [86, 0, 3]}, "LeftHip": [35, 0, -6], "RightHip": [8, 0, 6]},
    {"t": 1.65, "RightShoulder": STAKE_ARM, "LeftShoulder": PUSH, "Root": {"p": [0, -2.38, 0], "r": [89, 0, 0]}},
    # the arms give way
    {"t": 1.78, "RightShoulder": [30, 0, 55], "LeftShoulder": [40, 0, -50], "Neck": [15, 0, 0], "RightHip": [4, 0, 6],
     "LeftHip": [2, 0, -6]},
    {"t": 1.95, "RightShoulder": [60, 0, 35], "LeftShoulder": [55, 0, -35], "Neck": [-10, 0, 0]},
    # the strike (2.0): one jolt, then still
    {"t": 2.04, "Root": {"p": [0, -2.18, 0], "r": [78, 0, 0]}, "Neck": [35, 0, 0], "RightShoulder": [95, 0, 60],
     "LeftShoulder": [90, 0, -62], "RightHip": [28, 0, 10], "LeftHip": [24, 0, -10], "stop": ["Root"]},
    {"t": 2.16, "Root": {"p": [0, -2.45, 0], "r": [92, 0, 0]}, "Neck": [10, 0, 35], "RightShoulder": [20, 0, 62],
     "LeftShoulder": [15, 0, -62], "RightHip": [4, 0, 8], "LeftHip": [2, 0, -8], "stop": ["Root"]},
    {"t": 2.3, "Root": {"p": [0, -2.36, 0], "r": [89, 0, 0]}, "Neck": [8, 0, 42]},
    {"t": 2.6, "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}, "Neck": [8, 0, 44], "stop": True},
]

def collar_root(t, z, rr):
    """Knee on the chest (root height) and left hand on the collar (lean) at time t."""
    knee = body_point(victim, OFFSET, t, "Torso", CHEST)
    col = body_point(victim, OFFSET, t, "Torso", COLLAR)
    return fit2({"p": [0.2, -0.9, -1.2], "r": rr}, STANCE, "RightHip", knee, "LeftShoulder", col,
                a_vary="z", b_vary="lean", a_rng=(-2.4, -0.4), b_rng=(-60, 10))


def strike_root(t, rr):
    knee = body_point(victim, OFFSET, t, "Torso", CHEST)
    hit = body_point(victim, OFFSET, t, "Torso", [0.4, 0.1, -0.5])
    return fit2({"p": [0.2, -0.9, -1.2], "r": rr}, STANCE, "RightHip", knee, "RightShoulder", hit,
                a_vary="z", b_vary="lean", a_rng=(-2.6, -0.3), b_rng=(-70, 0))


def knee_root(t, rr, y=-0.9):
    """Keep the knee on the chest at time t with the given lean (slides the root along z)."""
    knee = body_point(victim, OFFSET, t, "Torso", CHEST)
    return fit({"p": [0.2, y, -1.2], "r": rr}, STANCE, "RightHip", knee, vary="z", lo=-2.6, hi=-0.3)


KNEE = {"reach": ("victim", "Torso", CHEST), "slide": [0, 0.6, 0]}

attacker = [
    {"t": 0.0, "Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [-15, 0, 0], "RightShoulder": [-30, 0, 12],
     "LeftShoulder": [10, 0, -10], "stop": True},
    {"t": 0.15, "Root": {"p": [0, 0.08, 0.05], "r": [4, 0, 0]}, "RightHip": [55, 0, 6], "Neck": [-25, 0, 0],
     "RightShoulder": [-40, 0, 15]},
    # knee drop (0.3): right knee onto the chest
    {"t": 0.3, "Root": knee_root(0.3, [-22, 0, 0]), "RightHip": KNEE, "LeftHip": FOOT, "Neck": [-30, 0, 0], "LeftShoulder": [40, 0, -15], "stop": ["Root"]},
    {"t": 0.38, "Root": knee_root(0.38, [-26, 0, 0]), "RightHip": KNEE},
    # collar
    {"t": 0.52, "LeftShoulder": {"reach": ("victim", "Torso", COLLAR), "slide": [0, 0.4, 0]}, "RightHip": KNEE},
    # the stake appears, held up and out
    {"t": 0.65, "RightShoulder": [125, 0, 28], "Neck": [-20, 0, 0]},
    # the struggle: the stake inches down against two hands
    {"t": 0.85, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -2.0])}, "Root": collar_root(0.85, -0.8, [-30, 0, 3])},
    {"t": 1.0, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -1.7])}},
    {"t": 1.15, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -1.9])}, "Root": collar_root(1.15, -0.8, [-27, 0, -3])},
    {"t": 1.35, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -1.5])}},
    {"t": 1.5, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -1.65])}, "Root": collar_root(1.5, -0.8, [-31, 0, 2])},
    {"t": 1.65, "RightShoulder": {"reach": ("victim", "Torso", [0.3, 0.1, -1.3])}, "RightHip": KNEE,
     "LeftShoulder": {"reach": ("victim", "Torso", COLLAR), "slide": [0, 0.4, 0]}},
    # raise high (1.8 - 1.95, creeping)
    {"t": 1.82, "RightShoulder": [172, 0, 18], "Root": knee_root(1.82, [-14, 0, 0]),
     "Neck": [-10, 0, 0], "stop": ["RightShoulder"]},
    {"t": 1.95, "RightShoulder": [178, 0, 22], "Root": knee_root(1.95, [-10, 0, 0]),
     "RightHip": KNEE, "stop": ["Root", "RightShoulder"]},
    # STRIKE (2.0)
    {"t": 2.03, "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.4, 0.3, 0]},
     "Root": strike_root(2.03, [-38, 0, 0]), "Neck": [-35, 0, 0],
     "stop": ["Root"]},
    {"t": 2.2, "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.4, 0.3, 0]},
     "Root": strike_root(2.2, [-36, 0, 0]), "RightHip": KNEE},
    {"t": 2.45, "RightShoulder": [60, 0, 15], "LeftShoulder": [20, 0, -15], "Neck": [-25, 0, 0],
     "Root": knee_root(2.45, [-26, 0, 0])},
    {"t": 2.6, "RightShoulder": [45, 0, 15], "LeftShoulder": [15, 0, -12], "Neck": [-20, 0, 0], "LeftHip": FOOT,
     "Root": knee_root(2.6, [-24, 0, 0]), "stop": True},
]

CLIP = {
    "name": "GripHuman", "length": 2.6, "offset": OFFSET,
    "markers": [(0.3, "Knee"), (0.65, "Stake"), (1.82, "Raise"), (2.0, "Strike"), (2.0, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact", "waive_attacker": "groundContact,rootDrift",
}

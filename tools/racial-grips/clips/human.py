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
PUSH = {"reach": ("attacker", "Left Arm", [0, 0, 0]), "slide": [0, 1.0, 0]}  # claws at the arm pinning its throat
STAKE_ARM = {"reach": ("attacker", "Right Arm", [0, 0, 0]), "slide": [0.5, 1.0, 0.5]}  # anywhere on the arm's surface

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [-5, 0, -15], "RightShoulder": [12, 0, 25], "LeftShoulder": [12, 0, -25],
     "RightHip": [0, 0, 6], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.22, "Root": {"p": [0, -2.36, 0], "r": [88, 0, 0]}, "Neck": [-15, 0, 10], "RightShoulder": [45, 0, 20]},
    # the knee lands (0.3): winded
    {"t": 0.32, "Root": {"p": [0, -2.5, 0], "r": [95, 0, 0]}, "Neck": [-30, 0, 0], "RightShoulder": [95, 0, 30],
     "LeftShoulder": [90, 0, -35], "RightHip": [30, 0, 8], "LeftHip": [25, 0, -8], "stop": ["Root"]},
    {"t": 0.45, "Root": {"p": [0, -2.4, 0], "r": [89, 0, 0]}, "Neck": [10, 0, 0], "RightHip": [5, 0, 6], "LeftHip": [0, 0, -6]},
    {"t": 0.65, "RightShoulder": [110, 0, 10], "LeftShoulder": [105, 0, -12], "Neck": [-10, 0, 0]},
    # both hands on the stake arm, pushing back: the chest strains up off the floor, twisting toward the stake
    {"t": 0.85, "RightShoulder": STAKE_ARM, "LeftShoulder": PUSH, "RightHip": [35, 0, 8]},
    {"t": 1.0, "Root": {"p": [0, -2.04, 0], "r": [61, 0, -16]}, "LeftHip": [30, 0, -8], "RightHip": [5, 0, 8]},
    {"t": 1.2, "Root": {"p": [0, -2.06, 0], "r": [62, 0, -24]}, "RightHip": [40, 0, 6], "LeftHip": [0, 0, -6]},
    {"t": 1.45, "Root": {"p": [0, -2.04, 0], "r": [61, 0, -17]}, "LeftHip": [35, 0, -6], "RightHip": [8, 0, 6]},
    {"t": 1.65, "RightShoulder": STAKE_ARM, "LeftShoulder": PUSH, "Root": {"p": [0, -2.08, 0], "r": [64, 0, -20]}},
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


from _util import kneel_legs, kneel_root, kneel_fit, stand_legs, root_for_legs

# the game's crouch (mirrored: right foot ahead) at the victim's side, the front shin standing just short of the body
KX, KZ, KYAW, KTURN, KFRONT = -0.6, -0.9, -10.0, -10.0, "RightHip"
KNEEL = kneel_legs(KX, KZ, KYAW, front=KFRONT, kid="human")
STAND = stand_legs(0.0, 0.0, stance=0.55, spread=0.25)
THROAT = [0, 0.95, -0.5]   # the pinning hand: the collar / throat


def pin_root(t, lean, roll=0.0, yaw=0.0):
    """Kneeling; leans (within limits, about the hips) just enough that the left hand pins the throat at time t.
    `lean` is the extra lean the beat asks for on top of that."""
    tgt = body_point(victim, OFFSET, t, "Torso", THROAT)
    base = kneel_fit(KX, KZ, KYAW, "LeftShoulder", tgt, turn=KTURN + yaw, roll=roll, rng=(-25, 12), front=KFRONT)
    extra = base["_lean"] + (lean + 30) * 0.35
    return kneel_root(KX, KZ, KYAW, max(-28, min(15, extra)), KTURN + yaw, roll, KFRONT)


def strike_root(t, roll=0.0, sink=0.3):
    """The stake hand lands on the chest: the whole body drives down, hips sinking onto the planted legs."""
    hit = body_point(victim, OFFSET, t, "Torso", [0.4, 0.1, -0.5])
    return kneel_fit(KX, KZ, KYAW, "RightShoulder", hit, turn=KTURN, roll=roll, rng=(-32, 0), front=KFRONT, sink=sink)


PIN = {"reach": ("victim", "Torso", THROAT), "slide": [0, 0.35, 0]}
KF = KNEEL[KFRONT]["plant"][:3, 3]
STEP = {"reach": ("world", None, [float(KF[0]) * 0.8, -2.55, float(KF[2]) * 0.8]), "slide": [0.3, 0, 0.3]}  # foot in the air on its way

attacker = [
    # stands over the prey, head cocked, stake hand hidden behind the back
    {"t": 0.0, "Root": root_for_legs({"p": [0, 0, 0], "r": [-6, 0, 0]}, STAND), **STAND, "Neck": [-28, 8, -10],
     "RightShoulder": [-35, 0, 12], "LeftShoulder": [12, 0, -14], "stop": True},
    {"t": 0.16, "Root": root_for_legs({"p": [0.1, 0, -0.1], "r": [-12, 0, 0]}, STAND), "Neck": [-34, 14, -14],
     "LeftShoulder": [55, 0, -20]},
    {"t": 0.23, "Root": root_for_legs({"p": [0.1, 0, -0.55], "r": [-16, KYAW / 2, 0]}, {"RightHip": STEP}),
     "RightHip": STEP, "LeftHip": [-30, 0, -6], "Neck": [-34, 10, -10]},
    # drops into the kneel and pins the throat (0.3), weight onto the hand
    {"t": 0.3, "Root": pin_root(0.3, -30), **KNEEL, "LeftShoulder": PIN, "Neck": [-30, 10, -8], "stop": ["Root"]},
    {"t": 0.4, "Root": pin_root(0.4, -34, 2), "LeftShoulder": PIN},
    # the stake comes out behind the head: a slow, creeping raise while he stares down
    {"t": 0.65, "Root": pin_root(0.65, -26, -3, 6), "RightShoulder": [150, 0, 38], "Neck": [-22, 16, -12], "LeftShoulder": PIN},
    {"t": 0.85, "Root": pin_root(0.85, -28, 3, 4), "LeftShoulder": PIN,
     "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -2.0])}, "Neck": [-34, 6, -6]},
    # the struggle: the stake inches down against two hands, his weight leaning in
    {"t": 1.0, "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -1.7])}, "Root": pin_root(1.0, -32, -3, 3)},
    {"t": 1.15, "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -1.9])}, "Root": pin_root(1.15, -29, 3, 2)},
    {"t": 1.35, "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -1.5])}, "Root": pin_root(1.35, -34, -2, 3)},
    {"t": 1.5, "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -1.65])}, "Root": pin_root(1.5, -31, 2, 2)},
    {"t": 1.65, "RightShoulder": {"reach": ("victim", "Torso", [-0.3, 0.1, -1.3])}, "LeftShoulder": PIN,
     "Root": pin_root(1.65, -35, 0, 2), "Neck": [-38, 0, 0]},
    # rises up on the knee and lifts the stake high: a held, trembling beat
    {"t": 1.82, "RightShoulder": [176, 0, 16], "Root": pin_root(1.82, -12, 0, 0), "Neck": [-18, 0, 4],
     "stop": ["RightShoulder"]},
    {"t": 1.95, "RightShoulder": [179, 0, 22], "Root": pin_root(1.95, -8, 0, 0), "LeftShoulder": PIN,
     "stop": ["Root", "RightShoulder"]},
    # STRIKE (2.03): the whole body drives down
    {"t": 2.03, "RightShoulder": {"reach": ("victim", "Torso", [0.4, 0.1, -0.5]), "slide": [0.4, 0.3, 0]},
     "Root": strike_root(2.03), "Neck": [-40, 0, 0], "stop": ["Root"]},
    {"t": 2.2, "RightShoulder": {"reach": ("victim", "Torso", [0.4, 0.1, -0.5]), "slide": [0.4, 0.3, 0]},
     "Root": strike_root(2.2, 2, 0.18)},
    # stays over the body, breathing, head tilting as he watches it go still
    {"t": 2.45, "RightShoulder": [70, 0, 20], "LeftShoulder": [30, 0, -18], "Neck": [-34, 12, -14],
     "Root": pin_root(2.45, -22, 0, 0)},
    {"t": 2.6, "RightShoulder": [55, 0, 18], "LeftShoulder": [24, 0, -16], "Neck": [-30, 18, -18],
     "Root": pin_root(2.6, -18, 0, 0), "stop": True},
]

CLIP = {
    "name": "GripHuman", "length": 2.6, "offset": OFFSET,
    "markers": [(0.3, "Knee"), (0.65, "Stake"), (1.82, "Raise"), (2.0, "Strike"), (2.0, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact", "waive_attacker": "groundContact,rootDrift",
}

"""Priest: Exorcism (3.2 s). The priest kneels, presses a hand to the forehead and raises the other high (the cross
forms over it in VFX). The possessed body fights: violent arches, drumming heels, a head whipping under the hand,
a hand grabbing the priest's wrist, then a rigid arch that lifts the chest a stud off the floor. On the final word
the priest slams the raised hand onto the chest: the arch snaps flat and the body goes still. The priest bows.

Victim HRP: 2.5 studs in front, turned -90 deg (lying across, head on the priest's LEFT under the left hand).
"""
from _util import plant, fit, fit2, body_point, kneel_legs, kneel_root, kneel_fit, stand_legs, root_for_legs, heels

OFFSET = {"p": [0, 0, -2.5], "yaw": -90}
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
FOREHEAD = [0, 0.15, -0.5]   # face of the head (up when lying)
CHEST = [0, 0.15, -0.5]

# heels drum: alternating hip flicks
DRUM = [(0.95, 16, -2), (1.18, -2, 16), (1.42, 18, 0), (1.66, 0, 18), (1.9, 16, 2), (2.14, 2, 14)]

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [0, 0, 20], "RightShoulder": [10, 0, 28], "LeftShoulder": [10, 0, -26],
     "RightHip": [0, 0, 6], "LeftHip": [0, 0, -6], "stop": True},
    {"t": 0.5, "Root": {"p": [0, -2.36, 0], "r": [89, 0, 0]}, "Neck": [-5, 0, 5]},
    {"t": 0.8, "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}, "Neck": [-8, 0, 0], "RightShoulder": [20, 0, 35]},
    # spasm 1 (1.1): the chest jerks up
    {"t": 1.1, "Root": {"p": [0, -2.0, 0.1], "r": [72, 0, 6]}, "Neck": [40, 0, -30], "RightShoulder": [70, 0, 75],
     "LeftShoulder": [120, 0, -40], "stop": ["Root"]},
    {"t": 1.25, "Root": {"p": [0, -2.22, 0.05], "r": [82, 0, -3]}, "Neck": [20, 0, 32], "LeftShoulder": [40, 0, -70]},
    # the right hand grabs the priest's wrist and fights it
    {"t": 1.4, "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0.5, 0]), "slide": [0, 0.5, 0]},
     "Neck": [25, 0, -30]},
    # spasm 2 (1.6)
    {"t": 1.6, "Root": {"p": [0, -1.9, 0.12], "r": [68, 0, -6]}, "Neck": [45, 0, 28], "LeftShoulder": [140, 0, -20],
     "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0.5, 0]), "slide": [0, 0.5, 0]}, "stop": ["Root"]},
    {"t": 1.75, "Root": {"p": [0, -2.15, 0.06], "r": [80, 0, 4]}, "Neck": [30, 0, -34], "LeftShoulder": [60, 0, -80]},
    # spasm 3 (2.0) rising into the rigid arch, lifted a stud off the floor
    {"t": 2.0, "Root": {"p": [0, -1.75, 0.15], "r": [66, 0, 0]}, "Neck": [55, 0, 25], "LeftShoulder": [20, 0, -85],
     "RightShoulder": {"reach": ("attacker", "Left Arm", [0, 0.5, 0]), "slide": [0, 0.5, 0]}, "stop": ["Root"]},
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
# the rigid arch (2.0 - 2.45): heels pinned to the floor, legs stretched, while the chest lifts
HEELS = heels(OFFSET, LIE, (1, 0, 0))
for k in victim:
    if 1.95 <= k["t"] <= 2.42:
        k.update(HEELS)


# the game's crouch (left foot ahead, as played in game) beside the head and shoulders
KX, KZ, KYAW, KTURN, KFRONT = -0.7, -0.3, -15.0, 15.0, "LeftHip"
KNEEL = kneel_legs(KX, KZ, KYAW, front=KFRONT, kid="priest")


def kneel(x, z, rr, hips=KNEEL):
    """Kneeling, upright-ish: rr = [lean, turn, roll] on top of the kneel (x, z kept for the old call sites)."""
    return kneel_root(KX, KZ, KYAW, max(-28, min(15, rr[0] + 12)), KTURN + rr[1], rr[2], KFRONT)


def strike_hold(t, x, z, rr):
    """The body drives down about the hips until the right palm lands on the chest."""
    tgt = body_point(victim, OFFSET, t, "Torso", [0.3, 0.15, -0.5])
    sink = 0.15 if t < 2.55 else 0.08  # the weight drops onto the palm, then eases
    return kneel_fit(KX, KZ, KYAW, "RightShoulder", tgt, turn=KTURN + rr[1], roll=rr[2], rng=(-32, 0), front=KFRONT, sink=sink)


def hold(t, x, z, rr, extra_lean=0):
    """Kneeling, leaning just enough that the left hand stays on the forehead at time t; rr[0] above -8 sits up
    a little (the wind-up), below leans in."""
    tgt = body_point(victim, OFFSET, t, "Head", FOREHEAD)
    base = kneel_fit(KX, KZ, KYAW, "LeftShoulder", tgt, turn=KTURN + rr[1], roll=rr[2], rng=(-25, 12), front=KFRONT)
    extra = base["_lean"] + (rr[0] + 8) * 0.35
    return kneel_root(KX, KZ, KYAW, max(-28, min(15, extra)), KTURN + rr[1], rr[2], KFRONT)


P_STAND = stand_legs(0.0, 0.0, stance=0.55, spread=0.2)
HAND_ON_HEAD = {"reach": ("victim", "Head", FOREHEAD), "slide": [0, 0.3, 0.6]}  # rests on the face, never sinks in
_KF = KNEEL[KFRONT]["plant"][:3, 3]
STEP = {"reach": ("world", None, [float(_KF[0]) * 0.8, -2.55, float(_KF[2]) * 0.8]), "slide": [0.3, 0, 0.3]}  # foot in the air on its way

attacker = [
    {"t": 0.0, "Root": root_for_legs({"p": [0, 0, 0], "r": [0, 0, 0]}, P_STAND), **P_STAND, "Neck": [-10, 0, 0], "RightShoulder": [55, 0, -28],
     "LeftShoulder": [55, 0, 28], "stop": True},
    {"t": 0.2, "Root": root_for_legs({"p": [-0.3, 0, -0.3], "r": [-10, 0, 0]}, {"LeftHip": STEP}),
     "LeftHip": STEP, "RightHip": [-28, 0, 6], "Neck": [-20, 0, 0], "LeftShoulder": [40, 0, 10]},
    {"t": 0.48, "Root": hold(0.48, -0.75, -0.9, [-18, 0, 0]), **KNEEL, "Neck": [-28, -10, 0],
     "LeftShoulder": HAND_ON_HEAD, "RightShoulder": [80, 0, 20], "stop": ["Root"]},
    {"t": 0.85, "Root": hold(0.85, -0.75, -0.9, [-10, 0, 3]), "LeftShoulder": HAND_ON_HEAD, "RightShoulder": {"reach": ("world", None, [0.9, 4.5, -0.7])},
     "Neck": [-15, -10, 0]},
    # bracing against each spasm, the raised hand trembling
    {"t": 1.12, "Root": hold(1.12, -0.75, -0.85, [-4, 0, 5]), "RightShoulder": {"reach": ("world", None, [1.05, 4.5, -0.62])}, "Neck": [-10, -14, 0]},
    {"t": 1.3, "Root": hold(1.3, -0.75, -0.9, [-12, 0, 2]), "RightShoulder": {"reach": ("world", None, [0.88, 4.5, -0.74])}},
    {"t": 1.62, "Root": hold(1.62, -0.75, -0.83, [-3, 0, -4]), "RightShoulder": {"reach": ("world", None, [1.06, 4.5, -0.6])}, "Neck": [-6, -8, 0]},
    {"t": 1.8, "Root": hold(1.8, -0.75, -0.9, [-12, 0, 2]), "RightShoulder": {"reach": ("world", None, [0.9, 4.5, -0.7])}},
    {"t": 2.02, "Root": hold(2.02, -0.75, -0.83, [-2, 0, 5]), "RightShoulder": {"reach": ("world", None, [1.08, 4.5, -0.64])}, "Neck": [-4, -12, 0]},
    {"t": 0.95, "Root": hold(0.95, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.05, "Root": hold(1.05, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.2, "Root": hold(1.2, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.4, "Root": hold(1.4, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.5, "Root": hold(1.5, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.7, "Root": hold(1.7, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 1.9, "Root": hold(1.9, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.1, "Root": hold(2.1, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.2, "Root": hold(2.2, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    {"t": 2.28, "Root": hold(2.28, -0.75, -0.87, [-8, 0, 0]), "LeftShoulder": HAND_ON_HEAD},
    # wind-up: lean back, hand higher and back
    {"t": 2.36, "Root": hold(2.36, -0.75, -0.75, [6, 0, 0]), "RightShoulder": {"reach": ("world", None, [1.25, 4.5, -0.15])}, "Neck": [6, -6, 0],
     "LeftShoulder": HAND_ON_HEAD, "stop": ["Root", "RightShoulder"]},
    # STRIKE at 2.45: palm onto the chest
    {"t": 2.46, "Root": strike_hold(2.46, -0.75, -1.05, [-34, 0, 0]), "Neck": [-30, -6, 0],
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.5, 0.4, 0]}, "LeftShoulder": HAND_ON_HEAD,
     "stop": ["Root"]},
    {"t": 2.62, "Root": strike_hold(2.62, -0.75, -1.07, [-36, 0, 0]),
     "RightShoulder": {"reach": ("victim", "Torso", CHEST), "slide": [0.5, 0.4, 0]}, "LeftShoulder": HAND_ON_HEAD},
    # withdraw, bow
    # stays over the emptied body: the palm still pressed to it, head bowed low, a cold, final stillness
    {"t": 2.9, "Root": kneel(-0.75, -0.9, [-20, 0, 4]), "RightShoulder": [70, 0, -10], "LeftShoulder": [60, 0, 20],
     "Neck": [-44, 8, -6]},
    {"t": 3.2, "Root": kneel(-0.75, -0.9, [-22, 0, 5]), **KNEEL, "RightShoulder": [66, 0, -12], "LeftShoulder": [56, 0, 22],
     "Neck": [-48, 10, -8], "stop": True},
]


# ---------------------------------------------------------------- heads (2.6.2): eyes on what the body is doing
from _util import look, set_necks  # noqa: E402
_V, _A = "victim", "attacker"
set_necks(attacker, {
    0.0: look(_V, "Head"), 0.2: look(_V, "Head", tilt=(0, -4, 0)),
    0.48: look(_V, "Head", tilt=(-6, -10, 0)), 0.85: look(_V, "Head", tilt=(-4, -10, 0)),    # on the possessed face
    1.12: look(_V, "Head", tilt=(0, -14, 0)), 1.62: look(_V, "Head", tilt=(2, -8, 0)), 2.02: look(_V, "Head", tilt=(4, -12, 0)),
    2.36: look(_V, "Torso", CHEST, (6, -6, 0)), 2.46: look(_V, "Torso", CHEST, (-8, -6, 0)),   # the strike
    2.9: look(_V, "Head", tilt=(-18, 8, -6)), 3.2: look(_V, "Head", tilt=(-22, 10, -8)),       # bowed over the body
})
set_necks(victim, {
    0.0: look(_A, "Head", tilt=(0, 0, 10)), 0.5: look(_A, "Head", tilt=(-4, 0, 4)),          # glares up at the priest
    0.8: look(_A, "Head"), 1.25: look(_A, "Head", tilt=(10, 0, 18)),
})

CLIP = {
    "name": "GripPriest", "length": 3.2, "offset": OFFSET,
    "markers": [(0.48, "Seal"), (0.85, "Cross"), (1.1, "Spasm"), (1.6, "Spasm"), (2.0, "Spasm"), (2.45, "Strike"),
                (2.45, "Finish")],
    "attacker": attacker, "victim": victim,
    "waive_victim": "groundContact", "waive_attacker": "groundContact,rootDrift",  # animpro cannot see the tucked crouch legs
}

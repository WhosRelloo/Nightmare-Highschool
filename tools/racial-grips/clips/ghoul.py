"""Ghoul: Eat Body victim (3.5 s) for the owner's Eat Body clip (79651374323565, loaded from ghoul_eatbody.txt).
Eaten alive, shown only through body language: pinned on the back under the hunched ghoul, it shoves at the
ghoul's head, kicks, rolls away and claws at the floor with the far hand, is dragged back, weakens with every
feed, jerks at the last rip, and the outstretched hand trembles and drops. No blood (VFX is grave dust and mist).

Victim HRP: 1.95 studs in front, turned 90 deg (across in front of the ghoul, head on its right); the chest sits
under the ghoul's mouth at the feed keys (mouth ~(0, -1.24, -1.91), chest top -1.88).
"""
from _ext import load

OFFSET = {"p": [0, 0, -1.95], "yaw": 90}
LIE = {"p": [0, -2.38, 0], "r": [90, 0, 0]}
SHOVE = {"reach": ("attacker", "Head", [0, 0, 0]), "slide": [0.4, 0.4, 0.4]}

# legs kick through the struggle (alternating), smaller as it weakens
KICKS = [(0.12, 30, 4), (0.3, 6, 38), (0.48, 34, 8), (0.66, 4, 30), (0.86, 28, 6), (1.04, 8, 24), (1.7, 22, 6),
         (1.9, 6, 16), (2.1, 14, 4), (2.32, 4, 8)]

victim = [
    {"t": 0.0, "Root": LIE, "Neck": [0, 0, -20], "RightShoulder": [14, 0, 30], "LeftShoulder": [14, 0, -28],
     "RightHip": [0, 0, 8], "LeftHip": [0, 0, -8], "stop": True},
    # first feed lands (0.25): a hard jolt, hands fly up at the ghoul's head
    {"t": 0.25, "Root": {"p": [0, -2.48, 0], "r": [94, 0, 0]}, "Neck": [-25, 0, 10], "RightShoulder": [95, 0, 30],
     "LeftShoulder": [100, 0, -25], "stop": ["Root"]},
    {"t": 0.36, "Root": {"p": [0, -2.36, 0], "r": [88, 0, -3]}, "LeftShoulder": SHOVE, "RightShoulder": [120, 0, 15]},
    {"t": 0.5, "Root": {"p": [0, -2.34, 0], "r": [87, 0, 3]}, "LeftShoulder": SHOVE, "RightShoulder": [80, 0, 40],
     "Neck": [-10, 0, 35]},
    # second feed (0.67): flinch, the far hand reaches away along the floor
    {"t": 0.67, "Root": {"p": [0, -2.46, 0], "r": [93, 0, -4]}, "LeftShoulder": SHOVE, "RightShoulder": [30, 0, 95],
     "Neck": [5, 0, 45], "stop": ["Root"]},
    {"t": 0.85, "Root": {"p": [0.1, -2.36, 0], "r": [88, 14, 0]}, "LeftShoulder": SHOVE, "RightShoulder": [60, 0, 100]},
    # rolls away onto its side and claws at the floor
    {"t": 1.05, "Root": {"p": [0.35, -2.25, 0], "r": [90, 48, 0]}, "LeftShoulder": [150, 0, 10], "RightShoulder": [175, 0, 40],
     "Neck": [-20, 0, 30], "RightHip": [-20, 0, 8], "LeftHip": [30, 0, -8]},
    {"t": 1.25, "Root": {"p": [0.55, -2.2, 0], "r": [90, 62, 0]}, "LeftShoulder": [178, 0, 5], "RightShoulder": [165, 0, 60],
     "RightHip": [25, 0, 8], "LeftHip": [-15, 0, -8]},
    {"t": 1.38, "RightShoulder": [176, 0, 48], "LeftShoulder": [160, 0, 20]},
    # dragged back under (1.45 - 1.6) and pinned on its back again
    {"t": 1.52, "Root": {"p": [0.05, -2.32, 0], "r": [90, 25, 0]}, "RightShoulder": [150, 0, 70], "LeftShoulder": [120, 0, -10],
     "Neck": [15, 0, 20], "stop": ["Root"]},
    {"t": 1.66, "Root": {"p": [0, -2.46, 0], "r": [93, 0, 0]}, "LeftShoulder": SHOVE, "RightShoulder": [40, 0, 80],
     "Neck": [-5, 0, 35], "RightHip": [8, 0, 8], "LeftHip": [4, 0, -8]},
    {"t": 1.85, "Root": {"p": [0, -2.38, 0], "r": [89, 0, 2]}, "LeftShoulder": SHOVE, "RightShoulder": [25, 0, 85]},
    # the shove weakens and slides off
    {"t": 2.05, "Root": {"p": [0, -2.4, 0], "r": [91, 0, -2]}, "LeftShoulder": [75, 0, -20], "RightShoulder": [18, 0, 88],
     "Neck": [5, 0, 40]},
    {"t": 2.3, "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}, "LeftShoulder": [30, 0, -45], "Neck": [10, 0, 46]},
    # the last rip (2.45): one jerk, then still
    {"t": 2.47, "Root": {"p": [0, -2.22, 0], "r": [80, 0, 3]}, "Neck": [30, 0, 20], "LeftShoulder": [70, 0, -60],
     "RightShoulder": [40, 0, 90], "RightHip": [22, 0, 10], "LeftHip": [18, 0, -10], "stop": ["Root"]},
    {"t": 2.62, "Root": {"p": [0, -2.42, 0], "r": [91, 0, 0]}, "Neck": [8, 0, 48], "LeftShoulder": [14, 0, -55],
     "RightShoulder": [14, 0, 92], "RightHip": [3, 0, 8], "LeftHip": [0, 0, -8]},
    # the outstretched hand trembles, then drops
    {"t": 2.75, "RightShoulder": [22, 0, 94]},
    {"t": 2.88, "RightShoulder": [12, 0, 90]},
    {"t": 3.0, "RightShoulder": [19, 0, 93]},
    {"t": 3.15, "RightShoulder": [6, 0, 86], "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}},
    {"t": 3.5, "Root": {"p": [0, -2.38, 0], "r": [90, 0, 0]}, "RightShoulder": [6, 0, 86], "Neck": [8, 0, 50], "stop": True},
]
for t, a, b in KICKS:
    k = next((k for k in victim if abs(k["t"] - t) < 0.04), None)
    if k is None:
        k = {"t": t}
        victim.append(k)
    k["RightHip"] = [a, 0, 8]
    k["LeftHip"] = [b, 0, -8]
victim.sort(key=lambda k: k["t"])

CLIP = {
    "name": "GripGhoul", "length": 3.5, "offset": OFFSET,
    "attacker": load("ghoul_eatbody.txt"), "victim": victim,
    "external_attacker": True,  # the owner's clip is already published; only the victim is built
    "waive_victim": "groundContact",
}

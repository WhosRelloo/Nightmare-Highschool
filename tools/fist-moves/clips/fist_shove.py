"""Shove (Fist string ender after hit 1): both palms drive into the chest and send them back.

Starts on M1.1's committed pose (0.45 s, just past its hit, where the ender cancels it) and ends on the fist idle's
first frame (slides included), so it joins both without a pop. Real-time markers (speed 1): Hit 0.32 (snaps to 0.333),
EndLag 0.46 (the stand-in's were 0.345 / 0.455). Orthodox stance like the M1s: left foot forward. Limb slides follow
the owner's set: arms pulled in front in the guard, slid forward on the strike (fake extension), legs tucked.
"""
from fist_poses import pose, key, blend, offs, IDLE, WAIVE

START = pose("M1_1", 0.45)

# the gather pose: weight back (anticipation: away from the push)
# (R6 arms can't fold to the chest: the anticipation swings both arms back and out behind instead, the opposite way)
GATHER = {"Root": {"p": [0.04, -0.46, 0.14], "r": [12, -4, 0]}, "Neck": [-10, 3, 0],
          "RightShoulder": [-38, 0, 28], "LeftShoulder": [-36, 0, -28], "RightHip": [-24, 0, 7], "LeftHip": [26, 0, -7],
          "_o": offs(right=(-0.1, -0.5, 0.55), left=(0.1, -0.5, 0.55))}
PUSH_O = offs(right=(-0.1, 0.35, -1.0), left=(0.1, 0.35, -1.0))
EXTENDED = {"Root": {"p": [0.0, -0.34, -0.36], "r": [-22, 2, 0]}, "Neck": [12, 0, 0],
            "RightShoulder": [140, 0, -4], "LeftShoulder": [141, 0, 4], "RightHip": [-34, 0, 7], "LeftHip": [30, 0, -7],
            "_o": PUSH_O}

attacker = [
    key(0.0, START),
    # unwind out of M1.1's lunge: the torso and arms come round first, the legs lag (they still hold M1.1's stance)
    key(0.11, blend(START, GATHER, 0.72, {"RightHip": 0.4, "LeftHip": 0.4}), ground=True),
    # creeping load (a moving hold, still coiling)
    key(0.21, GATHER, ground=True),
    # launch: the hips go first, the arms lag a frame behind (the head dips: it arcs, not a line)
    key(0.27, GATHER, root={"p": [0.0, -0.40, -0.12], "r": [-12, 0, 0]}, ground=True,
        offs=offs(right=(-0.05, -0.25, 0.1), left=(0.05, -0.25, 0.1)),
        Neck=[-6, 0, 0], RightShoulder=[50, 0, 16], LeftShoulder=[52, 0, -16],
        RightHip=[-33, 0, 7], LeftHip=[30, 0, -7]),
    # the strike (Hit): palms out level at chest/shoulder height (the shoulders make up the 26 deg lean), back leg driving, body forward
    key(0.32, GATHER, root={"p": [0.0, -0.36, -0.42], "r": [-26, 2, 0]}, ground=True, offs=PUSH_O,
        Neck=[14, 0, 0], RightShoulder=[138, 0, -6], LeftShoulder=[140, 0, 6],
        RightHip=[-38, 0, 7], LeftHip=[34, 0, -7]),
    # overshoot past the strike
    key(0.38, GATHER, root={"p": [0.0, -0.38, -0.48], "r": [-30, 3, 0]}, ground=True,
        offs=offs(right=(-0.1, 0.38, -1.15), left=(0.1, 0.38, -1.15)),
        Neck=[18, 0, 0], RightShoulder=[146, 0, -3], LeftShoulder=[147, 0, 3],
        RightHip=[-40, 0, 7], LeftHip=[36, 0, -7]),
    # follow-through and settle: the body rises out of the lunge, hands come home, two small corrections
    # (EndLag at 0.46: control is back; the clip keeps settling, and Combat.M1 fades it if you swing again)
    key(0.50, blend(EXTENDED, IDLE, 0.45), ground=True),
    key(0.62, blend(IDLE, {"Root": {"p": [0.1, -0.2, -0.2], "r": [-16, -8, -3]}, "Neck": [4, 8, 3],
                           "RightShoulder": [160, 20, -30], "LeftShoulder": [158, -14, 28], "RightHip": [-12, -4, 9],
                           "LeftHip": [14, 12, -7], "_o": offs()}, 0.35), ground=True),
    key(0.72, blend(IDLE, {"Root": {"p": [0.17, -0.12, -0.15], "r": [-10, -14, -5]}, "Neck": [1, 13, 5],
                           "RightShoulder": [177, 29, -38], "LeftShoulder": [170, -18, 33], "RightHip": [-8, -7, 10],
                           "LeftHip": [11, 19, -7], "_o": offs()}, 0.5), ground=True),
    key(0.84, IDLE),
]

REST = {"Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [0, 0, 0], "RightShoulder": [0, 0, 0],
        "LeftShoulder": [0, 0, 0], "RightHip": [0, 0, 0], "LeftHip": [0, 0, 0]}
CLIP = {
    "name": "FistShove", "length": 0.84, "offset": {"p": [0, 0, -40], "yaw": 180},
    "markers": [(0.32, "Hit"), (0.46, "EndLag")],
    "waive_attacker": WAIVE,
    "floor": False,  # the fist set stands at its own sole height (fist_poses.SOLE); the generator's -3.0 floor pass would fight it
    "attacker": attacker,
    "victim": [dict(REST, t=0.0, stop=True), dict(REST, t=0.84, stop=True)],
}

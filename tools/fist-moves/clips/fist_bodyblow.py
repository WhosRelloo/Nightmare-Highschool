"""Body Blow (Fist string ender after hit 3): a heavy right hook to the ribs.

Starts on M1.3's committed pose (0.40 s, just past its left-hand hit) and ends on the fist idle's first frame (slides
included). The right hand coils way back (the torso turned 40-48 deg away), the hips snap round first, the arm whips
across at rib height a frame behind. Markers (speed 1): Hit 0.37, EndLag 0.50 (the stand-in's were 0.37 / 0.49). The
heavy tell (the critical flash) fires as it starts, from the game code.
"""
from fist_poses import pose, key, blend, offs, IDLE, WAIVE

START = pose("M1_3", 0.40)

COIL = {"Root": {"p": [0.10, -0.50, 0.05], "r": [-14, -40, -4]}, "Neck": [-4, 34, 0],
        "RightShoulder": [30, 10, 60], "LeftShoulder": [150, -10, 22], "RightHip": [-25, -10, 8], "LeftHip": [28, 10, -8],
        "_o": offs(right=(-0.25, -0.55, 0.65))}
COIL_DEEP = {"Root": {"p": [0.10, -0.56, 0.08], "r": [-16, -48, -6]}, "Neck": [-4, 40, 0],
             "RightShoulder": [24, 12, 66], "LeftShoulder": [152, -10, 24], "RightHip": [-27, -10, 8], "LeftHip": [30, 10, -8],
             "_o": offs(right=(-0.35, -0.55, 0.78))}
STRIKE = {"Root": {"p": [0.0, -0.50, -0.25], "r": [-20, 34, 6]}, "Neck": [0, -30, 0],
          "RightShoulder": [78, 0, -18], "LeftShoulder": [150, -10, 25], "RightHip": [-34, -10, 8], "LeftHip": [30, 12, -8],
          "_o": offs(right=(0.1, -0.45, -1.1))}
OVER = {"Root": {"p": [0.0, -0.52, -0.30], "r": [-22, 42, 8]}, "Neck": [2, -36, 0],
        "RightShoulder": [82, 4, -30], "LeftShoulder": [148, -10, 26], "RightHip": [-35, -10, 8], "LeftHip": [31, 12, -8],
        "_o": offs(right=(-0.05, -0.45, -1.2))}

attacker = [
    key(0.0, START),
    # unwind out of M1.3 into the coil: torso and arms first, the legs lag
    key(0.12, blend(START, COIL, 0.7, {"RightHip": 0.4, "LeftHip": 0.4}), ground=True),
    # creeping deeper into the coil (a moving hold)
    key(0.24, COIL_DEEP, ground=True),
    # the hips go first: the torso is already turning back while the arm is still cocked
    key(0.30, COIL_DEEP, root={"p": [0.05, -0.52, -0.05], "r": [-18, -12, -4]}, ground=True,
        Neck=[-6, 12, 0], RightShoulder=[28, 10, 62]),
    key(0.37, STRIKE, ground=True),  # Hit: the fist at the ribs
    key(0.43, OVER, ground=True),
    # follow-through and settle (EndLag 0.50): the arm comes back up into the guard, small corrections
    key(0.55, blend(OVER, IDLE, 0.4), ground=True),
    key(0.68, blend(IDLE, {"Root": {"p": [0.12, -0.2, -0.2], "r": [-14, -4, -2]}, "Neck": [2, 8, 3],
                           "RightShoulder": [168, 22, -34], "LeftShoulder": [162, -14, 30], "RightHip": [-12, -6, 9],
                           "LeftHip": [14, 14, -7], "_o": offs()}, 0.4), ground=True),
    key(0.86, IDLE),
]

REST = {"Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [0, 0, 0], "RightShoulder": [0, 0, 0],
        "LeftShoulder": [0, 0, 0], "RightHip": [0, 0, 0], "LeftHip": [0, 0, 0]}
CLIP = {
    "name": "FistBodyBlow", "length": 0.86, "offset": {"p": [0, 0, -40], "yaw": 180},
    "markers": [(0.37, "Hit"), (0.50, "EndLag")],
    "waive_attacker": WAIVE,
    "floor": False,  # the fist set stands at its own sole height (fist_poses.SOLE); the generator's -3.0 floor pass would fight it
    "attacker": attacker,
    "victim": [dict(REST, t=0.0, stop=True), dict(REST, t=0.86, stop=True)],
}

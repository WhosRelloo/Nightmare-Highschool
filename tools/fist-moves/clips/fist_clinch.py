"""Clinch (M1 while blocking): grab both shoulders, yank down, drive the right knee into the gut. Plus the victim.

Authored as a pair: the victim stands 2.9 studs in front, facing the attacker (Combat.Clinch puts them there when the
grab lands). Attacker time: grab 0.14, knee (Hit) 0.36, EndLag 0.70; the victim clip is this victim track from 0.14
on (it starts when they're caught), so its knee lands at 0.22 of its own clip.
The attacker starts on the Block guard (it comes from a held block) and ends on the fist idle's first frame. The
victim starts and ends on the idle too (a fighter's stance; the clip blends in from whatever they were doing).
"""
from fist_poses import pose, key, blend, offs, IDLE, WAIVE

BLOCK = pose("Block", 0.0)

REACH = {"Root": {"p": [0.0, -0.24, -0.30], "r": [-14, 0, 0]}, "Neck": [8, 0, 0],
         "RightShoulder": [118, 0, -10], "LeftShoulder": [118, 0, 10], "RightHip": [-16, 0, 8], "LeftHip": [16, 0, -6],
         "_o": offs(right=(-0.1, -0.45, -0.9), left=(0.1, -0.45, -0.9))}
GRAB = {"Root": {"p": [0.0, -0.26, -0.38], "r": [-16, 0, 0]}, "Neck": [6, 0, 0],
        "RightShoulder": [102, 0, -14], "LeftShoulder": [102, 0, 14], "RightHip": [-18, 0, 8], "LeftHip": [18, 0, -6],
        "_o": offs(right=(-0.15, -0.45, -0.8), left=(0.15, -0.45, -0.8))}
CHAMBER = {"Root": {"p": [0.0, -0.10, -0.30], "r": [-4, 0, 0]}, "Neck": [-8, 0, 0],
           "RightShoulder": [68, 0, -18], "LeftShoulder": [68, 0, 18], "RightHip": [48, 0, 4], "LeftHip": [-6, 0, -4],
           "_o": offs(right=(-0.05, -0.4, -0.4), left=(0.05, -0.4, -0.4), rleg=(0.0, 0.3, -0.2))}
KNEE = {"Root": {"p": [0.0, 0.0, -0.28], "r": [6, 0, 0]}, "Neck": [-16, 0, 0],
        "RightShoulder": [52, 0, -18], "LeftShoulder": [52, 0, 18], "RightHip": [98, 0, 4], "LeftHip": [-8, 0, -4],
        "_o": offs(right=(-0.05, -0.4, -0.35), left=(0.05, -0.4, -0.35), rleg=(0.0, 0.45, -0.35))}
KNEE_OVER = {"Root": {"p": [0.0, 0.0, -0.26], "r": [8, 0, 0]}, "Neck": [-18, 0, 0],
             "RightShoulder": [48, 0, -18], "LeftShoulder": [48, 0, 18], "RightHip": [106, 0, 4], "LeftHip": [-9, 0, -4],
             "_o": offs(right=(-0.05, -0.4, -0.35), left=(0.05, -0.4, -0.35), rleg=(0.0, 0.48, -0.38))}

attacker = [
    key(0.0, BLOCK),
    key(0.08, blend(BLOCK, REACH, 0.8), ground=True),   # lunge in, hands reaching for the collar
    key(0.14, GRAB, ground=True),                          # the grab
    key(0.24, CHAMBER, ground=True),                       # yank down, knee chambered
    key(0.36, KNEE, ground=True),                          # Hit: the knee in the gut
    key(0.43, KNEE_OVER, ground=True),
    key(0.56, blend(KNEE_OVER, IDLE, 0.45, {"RightHip": 0.7}), ground=True),  # release, the leg comes down first
    key(0.70, blend(IDLE, GRAB, 0.18), ground=True),     # EndLag
    key(0.86, IDLE),
]

VIDLE = IDLE
victim = [
    key(0.0, VIDLE),
    key(0.14, VIDLE),                                                  # caught
    key(0.20, VIDLE, root={"p": [0.0, -0.20, -0.20], "r": [-16, 0, 0]}, ground=True,  # yanked forward
        Neck=[10, 0, 0], RightShoulder=[92, 0, -10], LeftShoulder=[78, 4, 17], RightHip=[-6, 0, 6], LeftHip=[10, 0, -6]),
    key(0.30, VIDLE, root={"p": [0.0, -0.30, -0.22], "r": [-26, 0, 0]}, ground=True,  # pulled down onto the knee
        Neck=[6, 0, 0], RightShoulder=[84, 0, -14], LeftShoulder=[72, 3, 19], RightHip=[-4, 0, 6], LeftHip=[12, 0, -6]),
    key(0.36, VIDLE, root={"p": [0.0, -0.15, -0.05], "r": [-46, 0, 0]}, ground=True,  # impact: folds over the knee
        offs=offs(right=(-0.05, -0.3, -0.4), left=(0.05, -0.3, -0.4)),
        Neck=[-22, 0, 0], RightShoulder=[30, 0, -20], LeftShoulder=[46, 2, 24], RightHip=[14, 0, 4], LeftHip=[18, 0, -4]),
    key(0.44, VIDLE, root={"p": [0.0, -0.38, 0.0], "r": [-58, 0, 0]}, ground=True,
        offs=offs(right=(-0.05, -0.3, -0.4), left=(0.05, -0.3, -0.4)),
        Neck=[-28, 0, 0], RightShoulder=[20, 0, -24], LeftShoulder=[26, 4, 30], RightHip=[18, 0, 4], LeftHip=[22, 0, -4]),
    key(0.70, VIDLE, root={"p": [0.0, -0.45, 0.18], "r": [-52, 0, 3]}, ground=True,   # hurt: staggered back a little
        offs=offs(right=(-0.05, -0.3, -0.4), left=(0.05, -0.3, -0.4)),
        Neck=[-20, 0, 2], RightShoulder=[24, 0, -22], LeftShoulder=[36, -4, 27], RightHip=[-8, 0, 6], LeftHip=[16, 0, -6]),
    key(0.95, VIDLE, root={"p": [0.0, -0.40, 0.14], "r": [-40, 0, 0]}, ground=True,
        offs=offs(right=(-0.03, -0.35, -0.2), left=(0.03, -0.35, -0.2)),
        Neck=[-12, 0, 0], RightShoulder=[38, 0, -16], LeftShoulder=[52, 0, 21], RightHip=[-6, 0, 6], LeftHip=[14, 0, -6]),
    key(1.22, blend(VIDLE, {"Root": {"p": [0.1, -0.3, 0.05], "r": [-24, -6, -2]}, "Neck": [-4, 6, 2],
                            "RightShoulder": [100, 15, -25], "LeftShoulder": [104, -10, 22], "RightHip": [-8, -4, 9],
                            "LeftHip": [12, 12, -7], "_o": offs()}, 0.5), ground=True),
    key(1.40, VIDLE),
]

CLIP = {
    "name": "FistClinch", "length": 1.40, "offset": {"p": [0, 0, -2.9], "yaw": 180},
    "markers": [(0.36, "Hit"), (0.70, "EndLag")],
    "waive_attacker": WAIVE,
    "floor": False,  # the fist set stands at its own sole height (fist_poses.SOLE); the generator's -3.0 floor pass would fight it
    "waive_victim": WAIVE,
    "attacker": attacker,
    "victim": victim,
    "victim_from": 0.14,  # the victim clip starts at the grab (fist-moves pack.py trims it)
}

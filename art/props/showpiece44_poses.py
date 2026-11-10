"""Props batch 44 (the showpiece kit): every figure's own pose, in one place, so no two are alike.
Degrees (rx, ry, rz) per joint, in the parent's rest frame (showpiece44_rig):
  arms   rshoulder (+X arm): ry < 0 raises it out sideways (-90 level, -170 overhead), rx < 0 swings it forward;
         lshoulder mirrored (ry > 0 raises it); elbows: rx < 0 bends the forearm forward, ry bends it in the arm's plane.
  legs   rhip / lhip: rx < 0 swings the leg forward, ry < 0 / > 0 swings it out; knees rx > 0 bend the shin back.
  body   root turns everything about the hips; waist bends the chest (rx > 0 bows, ry tilts sideways, rz twists);
         neck: rx < 0 looks up, rz turns the face (rz > 0 toward +X).
Each entry: (yaw degrees, pose)."""

POSES = {
    # statues
    "VampireLordRising": (8, {"lift": 0.75, "waist": (-10, 0, -10), "neck": (-18, 8, 16), "rshoulder": (-6, -128, 0), "relbow": (0, -22, 0),
                              "lshoulder": (-4, 108, 8), "lelbow": (-8, 28, 0), "rhip": (14, 0, 4), "rknee": (30, 0, 0), "lhip": (-8, 0, -4),
                              "lknee": (42, 0, 0)}),
    "WerewolfTurning": (-10, {"root": (-4, 0, 0), "waist": (-20, 6, 8), "neck": (-24, 0, -14),
                              "rshoulder": (28, -48, 0), "relbow": (-24, 0, 0), "lshoulder": (24, 54, 0), "lelbow": (-30, 0, 0),
                              "rhip": (-18, -14, 0), "rknee": (34, 0, 0), "lhip": (12, 14, 0), "lknee": (38, 0, 0)}),
    "VigilCaptainLantern": (12, {"waist": (14, 0, -10), "neck": (-30, 0, 18), "root": (8, 0, 6), "rshoulder": (-8, -165, 0), "relbow": (0, -12, 0),
                                 "lshoulder": (6, 22, 0), "lelbow": (-38, 0, 0), "rhip": (-50, 0, 4), "rknee": (46, 0, 0), "lhip": (22, 0, -4),
                                 "lknee": (12, 0, 0)}),
    "ChoirConductor": (-12, {"waist": (-8, 4, 10), "neck": (-26, 0, -14), "rshoulder": (-12, -150, 0), "relbow": (0, -28, 0),
                             "lshoulder": (-14, 112, 0), "lelbow": (0, 34, 0), "rhip": (4, 0, 2), "lhip": (-28, 6, 0), "lknee": (26, 0, 0)}),
    "InkScribeTendrils": (-18, {"waist": (24, 0, -18), "neck": (-26, 0, 12), "root": (6, 0, 0),
                                "rshoulder": (-72, -42, 0), "relbow": (-6, 0, 0), "lshoulder": (36, 82, 0), "lelbow": (-28, 0, 0),
                                "rhip": (-72, -8, 0), "rknee": (84, 0, 0), "lhip": (44, 8, 0), "lknee": (16, 0, 0)}),
    "DelinquentGlare": (122, {"waist": (-4, 0, -38), "neck": (-8, 0, -82), "root": (0, 0, 0),
                              "rshoulder": (8, -14, 0), "relbow": (-12, 0, 0), "lshoulder": (-34, 22, 0), "lelbow": (-86, 0, 0),
                              "rhip": (-22, 0, 0), "rknee": (12, 0, 0), "lhip": (24, 0, 0), "lknee": (34, 0, 0)}),
    "AthleteSpinKick": (-18, {"root": (0, -26, 0), "waist": (6, -6, 12), "neck": (-6, 14, 18),
                              "rhip": (0, -104, 0), "rknee": (4, 0, 0), "lhip": (-64, 6, 0), "lknee": (108, 0, 0),
                              "rshoulder": (-66, -14, 0), "relbow": (-96, 0, 0), "lshoulder": (0, 104, 0), "lelbow": (0, 18, 0)}),
    "CourtDuchessThrone": (0, {"waist": (-6, 0, 6), "neck": (6, 0, 14), "rhip": (-88, 0, 4), "rknee": (86, 0, 0), "lhip": (-96, 0, -26),
                               "lknee": (66, 0, 0), "rshoulder": (-34, -22, 0), "relbow": (-58, 0, 0), "lshoulder": (-62, 14, 18),
                               "lelbow": (-112, 0, 0)}),
    "ReaperGuard": (-24, {"waist": (16, 0, -26), "neck": (6, 0, 22), "root": (4, 0, 0), "rhip": (-32, -24, 0), "rknee": (44, 0, 0),
                          "lhip": (22, 26, 0), "lknee": (40, 0, 0), "rshoulder": (-56, -24, 0), "relbow": (-52, 0, 0), "lshoulder": (-38, 34, 0),
                          "lelbow": (-74, 0, 0)}),
    "PackAlphaLanding": (6, {"root": (14, 0, 0), "waist": (34, 0, 8), "neck": (-52, 0, -6), "rhip": (-82, -6, 0), "rknee": (96, 0, 0), "lhip": (18, 8, 0),
                             "lknee": (112, 0, 0), "rshoulder": (-4, -18, 0), "relbow": (0, 0, 0), "lshoulder": (32, 74, 0), "lelbow": (-22, 0, 0)}),
    "FounderRavens": (0, {"waist": (-6, 0, 4), "neck": (-22, 0, 6), "rshoulder": (-10, -138, 0), "relbow": (0, -10, 0), "lshoulder": (-22, 84, 0),
                          "lelbow": (-14, 0, 0), "rhip": (-12, 0, 0), "lhip": (10, 0, 0), "lknee": (10, 0, 0)}),
    "ExorcistSigil": (14, {"waist": (4, 0, 12), "neck": (4, 0, -8), "rhip": (-22, -16, 0), "rknee": (22, 0, 0), "lhip": (16, 16, 0), "lknee": (26, 0, 0),
                           "rshoulder": (-52, -8, 0), "relbow": (-92, 0, 0), "lshoulder": (0, 84, 0), "lelbow": (0, 22, 0)}),
    "GhoulUppercut": (-8, {"waist": (-16, 0, 30), "neck": (-28, 0, 22), "root": (8, 0, 0), "rshoulder": (-150, -22, 0), "relbow": (-24, 0, 0),
                           "lshoulder": (32, 42, 0), "lelbow": (-46, 0, 0), "rhip": (-30, 0, 0), "rknee": (60, 0, 0), "lhip": (10, 0, 0),
                           "lknee": (40, 0, 0)}),
    "CourtIaiDraw": (-20, {"waist": (34, 0, 22), "neck": (-30, 0, -14), "root": (4, 0, 0), "rhip": (-76, -8, 0), "rknee": (82, 0, 0),
                           "lhip": (52, 10, 0), "lknee": (8, 0, 0), "rshoulder": (-40, -56, 0), "relbow": (0, 0, 0), "lshoulder": (14, 24, 0),
                           "lelbow": (-62, 0, 0)}),
    # set-pieces (two figures each)
    "DuelVigil": (90, {"waist": (20, 0, 0), "neck": (-10, 0, 0), "rhip": (-70, 0, 0), "rknee": (72, 0, 0), "lhip": (46, 0, 0), "lknee": (6, 0, 0),
                       "rshoulder": (-118, 0, 0), "relbow": (0, 0, 0), "lshoulder": (22, 72, 0), "lelbow": (-40, 0, 0)}),
    "DuelCourt": (-90, {"waist": (-22, 0, 8), "neck": (-4, 0, 0), "rhip": (-26, 0, 0), "rknee": (30, 0, 0), "lhip": (26, 0, 0), "lknee": (32, 0, 0),
                        "rshoulder": (-112, -8, 0), "relbow": (-62, 0, 0), "lshoulder": (10, 64, 0), "lelbow": (-24, 0, 0)}),
    "StandHunter": (0, {"waist": (4, 0, -10), "neck": (0, 0, 36), "rhip": (-16, -18, 0), "rknee": (24, 0, 0), "lhip": (10, 18, 0), "lknee": (20, 0, 0),
                        "rshoulder": (0, -88, 0), "relbow": (0, 0, 0), "lshoulder": (-66, 26, 0), "lelbow": (-62, 0, 0)}),
    "StandPriest": (180, {"waist": (4, 0, 12), "neck": (-8, 0, -40), "rhip": (-14, -16, 0), "rknee": (20, 0, 0), "lhip": (12, 16, 0), "lknee": (22, 0, 0),
                          "rshoulder": (-30, -70, 0), "relbow": (-30, 0, 0), "lshoulder": (0, 92, 0), "lelbow": (0, 10, 0)}),
}

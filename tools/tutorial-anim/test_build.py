"""python -I -X utf8 -m unittest tools/tutorial-anim/test_build.py  (no RoMixamo needed)"""
import math, os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B
import mixamo_r6 as MX


def torso_world(q, p, hrp=np.eye(4)):
    c0, c1 = MX.R6M["RootJoint"]
    T = np.eye(4); T[:3, :3] = B.qmat(q); T[:3, 3] = p
    return hrp @ c0 @ T @ MX.inv(c1)


class EndOffset(unittest.TestCase):
    def test_reseat_keeps_the_body_still(self):
        # a torso 1.2 studs sideways, 3.4 forward, half a stud up, turned 70 degrees, tilted 10
        q = B.qmul(B.zq(math.radians(70)), np.array([math.sin(math.radians(5)), 0, 0, math.cos(math.radians(5))]))
        p = np.array([1.2, 3.4, 0.5])
        off = B.end_offset(q, p)
        hrp = np.eye(4)
        hrp_new = hrp @ np.array(MX.M([off["X"], 0, off["Z"], *B.yaw_matrix(math.radians(off["Yaw"])).reshape(-1)]))
        eq, ep = B.end_pose(q, p)
        before = torso_world(q, p, hrp)
        after = torso_world(eq, ep, hrp_new)
        self.assertTrue(np.allclose(before, after, atol=1e-6), (before, after))

    def test_end_pose_keeps_height_and_tilt(self):
        q = B.qmul(B.zq(1.0), np.array([0.1, 0, 0, math.sqrt(1 - 0.01)]))
        p = np.array([2.0, -1.0, 0.7])
        eq, ep = B.end_pose(q, p)
        self.assertAlmostEqual(ep[2], 0.7)
        self.assertAlmostEqual(ep[0], 0.0)
        self.assertAlmostEqual(ep[1], 0.0)
        self.assertAlmostEqual(B.yaw_of(eq), 0.0, places=6)


class GameClip(unittest.TestCase):
    def test_game_clip_loads(self):
        frames = B.load_game("Crouch")
        self.assertGreaterEqual(len(frames), 2)
        c = B.Clip.from_frames("GameCrouch", frames, True)
        self.assertEqual(c.n, len(frames))
        self.assertTrue(np.allclose(np.linalg.norm(c.q, axis=2), 1.0, atol=1e-4))


if __name__ == "__main__":
    unittest.main()

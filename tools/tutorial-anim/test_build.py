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


class EndSettle(unittest.TestCase):
    def synthetic(self, n=20):
        """a torso turning and walking, and the left arm swinging at constant speed"""
        q = np.zeros((n, len(B.JOINTS), 4)); p = np.zeros((n, len(B.JOINTS), 3))
        for f in range(n):
            for j in range(len(B.JOINTS)):
                q[f, j] = [0, 0, 0, 1]
            q[f, 0] = B.qmul(B.zq(0.3 + 0.02 * f), np.array([math.sin(0.05), 0, 0, math.cos(0.05)]))
            p[f, 0] = [1.0 + 0.05 * f, -2.0 + 0.03 * f, 0.6]
            a = 0.04 * f
            q[f, 2] = [math.sin(a / 2), 0, 0, math.cos(a / 2)]
        return B.Clip("Synth", q, p, loop=False)

    def test_end_pose_sits_after_the_lead_and_the_limb_stays(self):
        c = self.synthetic()
        s = B.end_settle(c)
        L = B.SETTLE_LEAD
        eq, ep = B.end_pose(c.q[-1][0], c.p[-1][0])
        self.assertTrue(np.allclose(s.q[L][0], eq, atol=1e-6) or np.allclose(s.q[L][0], -eq, atol=1e-6))
        self.assertTrue(np.allclose(s.p[L][0], ep, atol=1e-6))
        self.assertTrue(np.allclose(s.q[L][2], c.q[-1][2], atol=1e-6) or np.allclose(s.q[L][2], -c.q[-1][2], atol=1e-6))

    def test_lead_frames_are_the_pieces_own_frames_under_the_same_transform(self):
        c = self.synthetic()
        s = B.end_settle(c)
        L, last = B.SETTLE_LEAD, c.n - 1
        phi = -B.yaw_of(c.q[last, 0])
        co, si = math.cos(phi), math.sin(phi)
        x, y = c.p[last, 0, 0], c.p[last, 0, 1]
        ref = c.aligned(phi, -(co * x - si * y), -(si * x + co * y))
        for k in range(L):
            src = last - L + k
            self.assertTrue(np.allclose(s.p[k], ref.p[src], atol=1e-6), k)
            for j in range(len(B.JOINTS)):
                self.assertTrue(np.allclose(s.q[k][j], ref.q[src][j], atol=1e-6) or np.allclose(s.q[k][j], -ref.q[src][j], atol=1e-6), (k, j))

    def test_limb_speed_decays_to_zero_after_the_lead_and_the_last_two_frames_match(self):
        c = self.synthetic()
        s = B.end_settle(c)
        L = B.SETTLE_LEAD
        self.assertEqual(s.n, L + B.SETTLE_FRAMES + 3)
        v = [B.qang(s.q[k][2], s.q[k + 1][2]) for k in range(s.n - 1)]
        for k in range(L, L + B.SETTLE_FRAMES - 1):
            self.assertLess(v[k + 1], v[k], v)
        self.assertGreater(v[L], 0.5 * 0.04)
        self.assertAlmostEqual(v[-1], 0.0, places=5)
        self.assertTrue(np.allclose(s.q[-1], s.q[-2]) and np.allclose(s.p[-1], s.p[-2]))


if __name__ == "__main__":
    unittest.main()

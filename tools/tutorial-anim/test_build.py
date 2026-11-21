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


def synthetic(n=20, name="Synth", loop=False):
    """a torso turning and walking, and the left arm swinging at constant speed"""
    q = np.zeros((n, len(B.JOINTS), 4)); p = np.zeros((n, len(B.JOINTS), 3))
    for f in range(n):
        for j in range(len(B.JOINTS)):
            q[f, j] = [0, 0, 0, 1]
        q[f, 0] = B.qmul(B.zq(0.3 + 0.02 * f), np.array([math.sin(0.05), 0, 0, math.cos(0.05)]))
        p[f, 0] = [1.0 + 0.05 * f, -2.0 + 0.03 * f, 0.6]
        a = 0.04 * f
        q[f, 2] = [math.sin(a / 2), 0, 0, math.cos(a / 2)]
    return B.Clip(name, q, p, loop=loop)


def same_q(a, b, atol=1e-6):
    return np.allclose(a, b, atol=atol) or np.allclose(a, -b, atol=atol)


class Settle(unittest.TestCase):
    """the chain's last piece ends at rest: SETTLE_FRAMES of its last motion dying out (0.82/frame), then a 2-frame hold"""

    def test_settle_keeps_the_piece_and_appends_the_decay_and_the_hold(self):
        c = synthetic()
        s = B.settle(c)
        self.assertEqual(s.n, c.n + B.SETTLE_FRAMES + 2)
        self.assertFalse(s.loop)
        self.assertTrue(np.allclose(s.q[:c.n], c.q) and np.allclose(s.p[:c.n], c.p))   # under its own root: no re-seat

    def test_limb_speed_decays_monotonically_to_zero_and_the_last_two_frames_match(self):
        c = synthetic()
        s = B.settle(c)
        v0 = B.qang(c.q[-2][2], c.q[-1][2])                                  # the piece's own last speed
        v = [B.qang(s.q[k][2], s.q[k + 1][2]) for k in range(c.n - 1, s.n - 1)]
        self.assertLess(v[0], v0)
        self.assertGreater(v[0], 0.5 * v0)
        for k in range(len(v) - 1):
            self.assertLessEqual(v[k + 1], v[k] + 1e-9, v)
        for k in range(B.SETTLE_FRAMES - 1):
            self.assertLess(v[k + 1], v[k], v)                               # strictly while it moves
        self.assertAlmostEqual(v[-1], 0.0, places=5)
        self.assertTrue(np.allclose(s.q[-1], s.q[-2]) and np.allclose(s.p[-1], s.p[-2]))


class EndClip(unittest.TestCase):
    def test_end_clip_is_a_still_pose_of_two_identical_frames(self):
        s = B.settle(synthetic())
        e = B.end_clip(s)
        self.assertEqual(e.n, 2)                                             # non-zero length (1/30 s)
        self.assertFalse(e.loop)
        self.assertTrue(np.allclose(e.q[0], e.q[1]) and np.allclose(e.p[0], e.p[1]))
        eq, ep = B.end_pose(s.q[-1][0], s.p[-1][0])
        self.assertTrue(same_q(e.q[0][0], eq) and np.allclose(e.p[0][0], ep))

    def test_world_space_continuity_across_the_reseat(self):
        """Root * CFrame(EndOffset) * T_End == the settled piece's final-frame torso under Root, and every limb's local
        pose is identical across the seam: the switch is a still pose to an identical still pose"""
        s = B.settle(synthetic())
        e = B.end_clip(s)
        off = B.end_offset(s.q[-1][0], s.p[-1][0])
        root = np.array(MX.M([3.0, 1.5, -2.0, *B.yaw_matrix(0.7).reshape(-1)]))   # anywhere, any heading
        moved = root @ np.array(MX.M([off["X"], 0, off["Z"], *B.yaw_matrix(math.radians(off["Yaw"])).reshape(-1)]))
        before = torso_world(s.q[-1][0], s.p[-1][0], root)
        for f in range(e.n):
            after = torso_world(e.q[f][0], e.p[f][0], moved)
            self.assertTrue(np.allclose(before, after, atol=1e-3), (before, after))   # EndOffset is rounded to 1e-4 st, 1e-3 deg
            for j in range(1, len(B.JOINTS)):
                self.assertTrue(same_q(e.q[f][j], s.q[-1][j]) and np.allclose(e.p[f][j], s.p[-1][j]), (f, B.JOINTS[j]))


class ChainEnd(unittest.TestCase):
    def test_a_one_shot_last_piece_gets_the_settle(self):
        a, b = synthetic(40, "A"), synthetic(40, "B")
        pieces, _ = B.build_chain("T", [{"clip": "A"}, {"clip": "B"}], {"A": a, "B": b})
        last = pieces[-1].clip()
        self.assertFalse(pieces[-1].loop)
        self.assertTrue(np.allclose(last.q[-1], last.q[-2]) and np.allclose(last.p[-1], last.p[-2]))
        v = [B.qang(last.q[k][2], last.q[k + 1][2]) for k in range(last.n - B.SETTLE_FRAMES - 3, last.n - 1)]
        for k in range(B.SETTLE_FRAMES - 1):
            self.assertLess(v[k + 1], v[k], v)

    def test_a_hold_last_piece_gets_no_settle(self):
        a, b = synthetic(40, "A"), synthetic(40, "B")
        pieces, _ = B.build_chain("T", [{"clip": "A"}, {"clip": "B", "hold": 0.5}], {"A": a, "B": b})
        last = pieces[-1].clip()
        self.assertTrue(pieces[-1].hold)
        self.assertGreater(B.qang(last.q[-2][2], last.q[-1][2]), 0.01)       # it freezes mid-motion, as authored

    def test_a_loop_last_piece_gets_no_settle_and_its_entry_is_untouched(self):
        """A loop that comes last keeps cycling until the caller re-seats (a loop has no end to settle into; appending
        frames would break its seam). The piece before it still ends exactly on the loop's entry frame."""
        a = synthetic(40, "A")
        lp = synthetic(31, "L", loop=True)
        lp.q[-1], lp.p[-1] = lp.q[0].copy(), lp.p[0].copy()
        pieces, _ = B.build_chain("T", [{"clip": "A"}, {"clip": "L"}], {"A": a, "L": lp})
        self.assertTrue(pieces[-1].loop)
        self.assertEqual(len(pieces[-1].q), lp.n)                           # no frames appended to the loop
        before = pieces[-2].clip()
        entry = int(round(pieces[-1].entry * B.FPS))
        loopq = pieces[-1].clip(loop=True)
        self.assertTrue(all(same_q(before.q[-1][j], loopq.q[entry][j]) for j in range(1, len(B.JOINTS))))
        self.assertGreater(max(B.qang(before.q[-2][j], before.q[-1][j]) for j in range(len(B.JOINTS))), 1e-3)  # no hold appended


if __name__ == "__main__":
    unittest.main()

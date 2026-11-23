"""Offline tests for bake.py (phase6-strafes R3). Synthetic R6 clips only: no Studio.  python -m pytest -q"""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake as B  # noqa: E402


def walk_clip(yaw_deg=0.0, n=31, length=1.0, swing_deg=20.0, drop=0.0, travel=0.0, spin_deg=0.0, cycles=1.0):
    """A synthetic R6 cycle in the internal format: the legs swing about their pose X axis, the torso is yawed by
    yaw_deg about pose Z (the vertical), lowered by drop (pose Z), carried `travel` studs along pose Y, spun spin_deg."""
    t = np.linspace(0.0, length, n)
    P = {j: np.repeat(np.eye(4)[None], n, axis=0) for j in B.JOINTS}
    for i in range(n):
        u = i / (n - 1)
        ph = 2 * math.pi * cycles * u
        sw = math.radians(swing_deg) * math.sin(ph)
        P["Torso"][i] = B.mat(rz=math.radians(yaw_deg + spin_deg * u), pos=(0.0, -travel * u, drop))
        P["Left Leg"][i] = B.mat(rx=sw)
        P["Right Leg"][i] = B.mat(rx=-sw)
        P["Head"][i] = B.mat(rz=math.radians(-yaw_deg * 0.25))
    return B.Clip("synthetic", t, P)


def test_fk_rest_pose_feet_on_the_floor():
    c = walk_clip(swing_deg=0.0)
    w = B.fk(c, 0)
    assert w["lf"][1] == pytest.approx(-3.0, abs=1e-6) and w["rf"][1] == pytest.approx(-3.0, abs=1e-6)


def test_square_chest_removes_yaw_and_keeps_leg_world_rotation():
    src = walk_clip(yaw_deg=58)
    out = B.square_chest(src)
    for i in range(src.n):
        assert abs(B.torso_yaw_deg(out, i)) < 1.0
        ws, wo = B.fk(src, i), B.fk(out, i)
        for leg in ("Left Leg", "Right Leg"):
            assert B.rot_angle_deg(ws[leg], wo[leg]) < 0.5
    assert abs(B.stance_speed(out) - B.stance_speed(src)) <= 0.05 * max(B.stance_speed(src), 1e-6)
    assert abs(B.lowest_foot(out) - B.lowest_foot(src)) < 0.05
    assert B.seam(out) < 1.0


def test_square_chest_head_faces_forward():
    out = B.square_chest(walk_clip(yaw_deg=58))
    for i in range(out.n):
        assert abs(B.head_yaw_deg(out, i)) < 1.0


def test_square_chest_keep_yaw():
    out = B.square_chest(walk_clip(yaw_deg=58), keep_yaw=10.0)
    assert abs(B.torso_yaw_deg(out, 0) - 10.0) < 1.0


def test_foot_lock_plants_the_stance_foot():
    src = walk_clip(yaw_deg=0, n=61, swing_deg=25)
    out = B.foot_lock(src)
    assert B.stance_jitter(out) < 0.05
    assert B.stance_jitter(out) <= B.stance_jitter(src) + 1e-9


def test_loop_cut_is_seamless_and_stays_in_the_band():
    src = walk_clip(drop=-0.95, n=200, length=6.6, cycles=3)
    out, a, b = B.loop_cut(src, drop_max=-0.8, min_len=3.0, blend=0.3)
    assert out.length() >= 3.0 - 1e-6
    assert B.seam(out) <= 1.0
    assert all(out.P["Torso"][i][2, 3] <= -0.8 for i in range(out.n))


def test_split_switches_are_frame_identical():
    src = walk_clip(drop=-0.95, n=200, length=6.6, cycles=3)
    _, a, b = B.loop_cut(src, drop_max=-0.8, min_len=3.0, blend=0.3)
    parts = B.split(src, a, b, blend=0.3)
    assert B.frame_distance(parts["KneelIn"], parts["KneelIn"].n - 1, parts["Loop"], 0) < 1e-6
    assert B.frame_distance(parts["Loop"], parts["Loop"].n - 1, parts["StandUp"], 0) < 1e-6
    assert parts["KneelIn"].length() == pytest.approx(parts["StandUp"].length() * 1.15 + 0.1, abs=0.02)  # 1.15x slower, +0.1 s eased start


def test_upper_body_keeps_arms_and_head_only():
    out = B.upper_body(walk_clip())
    assert set(out.P) == {"Head", "Left Arm", "Right Arm"}


def test_scale_multiplies_translations():
    out = B.scale(walk_clip(drop=-1.5), 0.9)
    assert out.P["Torso"][0][2, 3] == pytest.approx(-1.35)


def test_strip_root_moves_travel_into_carry():
    src = walk_clip(travel=7.24)
    out, carry = B.strip_root(src, yaw=False)
    for i in range(out.n):
        x, y = out.P["Torso"][i][0, 3], out.P["Torso"][i][1, 3]
        assert math.hypot(x, y) < 0.05
    assert math.hypot(carry[-1][1], carry[-1][2]) == pytest.approx(7.24, abs=0.05)


def test_strip_root_yaw_moves_spin_into_carry():
    src = walk_clip(spin_deg=159)
    out, carry = B.strip_root(src, yaw=True)
    assert abs(B.torso_yaw_deg(out, out.n - 1)) < 1.0
    assert abs(carry[-1][3]) == pytest.approx(159, abs=1.0)


def test_decimate_keeps_shape():
    src = walk_clip(n=301, length=10)
    out = B.decimate(src, 15)
    assert out.n <= 152
    assert B.max_joint_error(src, out) < 1.0


def test_stride_is_twice_the_spread_over_the_length():
    c = walk_clip(swing_deg=20, length=1.0)
    assert B.stride(c) == pytest.approx(2 * B.max_spread(c) / 1.0, rel=1e-6)


def test_contact_phase_in_range():
    p = B.contact_phase(walk_clip(n=61))
    assert 0.0 <= p < 1.0


def test_json_round_trip():
    c = walk_clip()
    d = B.to_json(c)
    c2 = B.from_json(d)
    assert c2.n == c.n and B.max_joint_error(c, c2) < 1e-6


def test_emit_lua_has_the_builder_parts():
    txt = B.emit_lua(walk_clip(), "NHG_Test", loop=True, priority="Action")
    assert 'Instance.new("KeyframeSequence")' in txt and '"NHG_Test"' in txt and "seq.Loop = true" in txt
    assert "Enum.AnimationPriority.Action" in txt and "98950102230473" in txt

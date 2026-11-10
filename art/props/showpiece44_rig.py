"""Batch 44 (the showpiece kit) copy of batch 41's rig helper (art41_rig.py), extended with body colliders for the cloth
simulation, settling a posed figure onto a floor, glowing eyes and more carved faces.

The owner's R6 rig for props batch 41 (the art kit): every figure in a statue, relief, painting or tapestry of the batch
is the real R6 body from "E:/Blender Shit/CHARACTER SHIT/PaintRigV3.blend" (read only: its objects are appended, the
file is never saved), posed on its own armature, the pose applied, then dressed and carved.

The rig (inspected 2026-11-09): armature RoBone (bones Base > Lower > Upper > Head, Upper > R A > R E, Upper > L A > L E,
Lower > R L > R K, Lower > L L > L K, plus IK foot targets R/L K.001 and poles K.003), bendy elbows and knees, the
body meshes Idarkgames9 (head, 1.2 rounded), Torso (2 x 1 x 2), Mendula6 / Mendula8 (arms), Mendula5 / Left Leg (legs),
each with an Armature and a Subsurf modifier. 5.1 tall, the feet at z = 0, facing +Y (its knee poles are at +Y).

Here the rig is turned 180 degrees so it faces -Y like every prop, and the sides are named as the viewer sees them, as in
the statue kit (nh_props_batch27.R6): "rshoulder" is the arm at +X. Joints and pivots (R6 units, rest):
  root (Lower, 0 0 2)  waist (Upper, 0 0 3)  neck (Head, 0 0 4)
  rshoulder / lshoulder (+-1.5 0 3.6)  relbow / lelbow (+-1.5 0 3.05)
  rhip / lhip (+-0.5 0 2)  rknee / lknee (+-0.5 0 1.05)
pose: degrees (rx, ry, rz) about the world axes at the joint, applied down the chain (rx < 0 swings a limb forward, -Y;
ry < 0 lifts the +X arm out and up). "lift" raises the body (R6 units). The IK is muted, so a pose is exactly what it says.

Fig.build(part, fn) builds costume pieces in the rest frame and skins them to the posed bones by height (a sleeve bends
at the elbow, a gown at the waist), as the statue kit's R6.build did; Fig.at(part, p) gives a rest point's posed place.
"""
import math

import bpy
from mathutils import Euler, Matrix, Vector

import nh_props as P

RIG = "E:/Blender Shit/CHARACTER SHIT/PaintRigV3.blend"
MESHES = {"Idarkgames9": "head", "Torso": "torso", "Mendula8": "rarm", "Mendula6": "larm", "Left Leg": "rleg", "Mendula5": "lleg"}
# my joint -> (rig bone, parent joint)
JOINTS = {"root": ("Lower", None), "waist": ("Upper", "root"), "neck": ("Head", "waist"),
          "rshoulder": ("L A", "waist"), "relbow": ("L E", "rshoulder"), "lshoulder": ("R A", "waist"), "lelbow": ("R E", "lshoulder"),
          "rhip": ("L L", "root"), "rknee": ("L K", "rhip"), "lhip": ("R L", "root"), "lknee": ("R K", "lhip")}
ORDER = ["root", "waist", "neck", "rshoulder", "relbow", "lshoulder", "lelbow", "rhip", "rknee", "lhip", "lknee"]
# skinning chains for costume: part -> [(joint, below this rest height use the next one)]
CHAINS = {"torso": [("waist", 3.0), ("root", None)], "head": [("neck", None)],
          "rarm": [("rshoulder", 3.05), ("relbow", None)], "larm": [("lshoulder", 3.05), ("lelbow", None)],
          "rleg": [("rhip", 1.05), ("rknee", None)], "lleg": [("lhip", 1.05), ("lknee", None)]}
ALIAS = {"rshoulder": "rarm", "lshoulder": "larm", "rhip": "rleg", "lhip": "lleg", "neck": "head", "head": "head", "torso": "torso",
         "relbow": "rarm", "lelbow": "larm", "rknee": "rleg", "lknee": "lleg", "rarm": "rarm", "larm": "larm", "rleg": "rleg", "lleg": "lleg"}
BLEND = 0.16


def _append():
    names = list(MESHES) + ["RoBone"]
    with bpy.data.libraries.load(RIG, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    got = {}
    for ob in dst.objects:
        if ob is None:
            continue
        bpy.context.scene.collection.objects.link(ob)
        base = ob.name.split(".")[0] if ob.name.split(".")[-1].isdigit() else ob.name
        got[base] = ob
    return got


FIGS = []      # every figure made since the last reset (for the clipping check)


class Fig:
    """A posed R6 from the owner's rig. world = T(base) @ Rz(yaw) @ Scale(scale) @ T(0, 0, lift) @ posed rest."""

    def __init__(self, base=(0, 0, 0), yaw=0.0, scale=1.6, pose=None, mats=None, parts=("head", "torso", "rarm", "larm", "rleg", "lleg"),
                 face=None, dark=None, body=True, decimate=None, glow_eyes=None):
        _start = len(P.PARTS)
        self.pose = dict(pose or {})
        lift = self.pose.pop("lift", 0.0)
        self.G = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(scale, 4) @ Matrix.Translation((0, 0, lift))
        got = _append()
        arm = got["RoBone"]
        off = arm.location.copy()
        arm.location = (-off.x, -off.y, off.z)          # turned about Z, the body stays centred on the origin
        arm.rotation_euler = (0, 0, math.pi)
        bpy.context.view_layer.update()
        A = arm.matrix_world.copy()
        for pb in arm.pose.bones:
            for c in pb.constraints:
                c.mute = True
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        self.pivot = {j: (A @ arm.data.bones[b].head_local).copy() for j, (b, _) in JOINTS.items()}
        self.D = {}
        for j in ORDER:
            b, par = JOINTS[j]
            p = self.pivot[j]
            r = self.pose.get(j, (0, 0, 0))
            L = Matrix.Translation(p) @ Euler([math.radians(a) for a in r], "XYZ").to_matrix().to_4x4() @ Matrix.Translation(-p)
            self.D[j] = (self.D[par] @ L) if par else L
        for j in ORDER:
            b, _ = JOINTS[j]
            bone = arm.data.bones[b]
            arm.pose.bones[b].matrix = A.inverted() @ self.D[j] @ A @ bone.matrix_local
            bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        mats = mats if isinstance(mats, dict) else {k: mats for k in ("head", "torso", "rarm", "larm", "rleg", "lleg")}
        self.body = {}
        for name, part in MESHES.items():
            src = got.get(name)
            if src is None:
                continue
            if body and part in parts:
                ev = src.evaluated_get(dg)
                me = bpy.data.meshes.new_from_object(ev)
                me.transform(src.matrix_world)
                me.transform(self.G)
                me.materials.clear()
                for uv in list(me.uv_layers):
                    me.uv_layers.remove(uv)
                ob = bpy.data.objects.new(f"R6{part}", me)
                bpy.context.collection.objects.link(ob)
                for poly in me.polygons:
                    poly.use_smooth = True
                P._finish(ob, mats[part] if mats.get(part) is not None else mats.get("torso"), 0)
                if decimate:
                    md = ob.modifiers.new("Decimate", "DECIMATE")
                    md.ratio = decimate
                self.body[part] = ob
        for ob in got.values():
            bpy.data.objects.remove(ob, do_unlink=True)
        self.start = _start
        self.hair = None
        FIGS.append(self)
        if face:
            self.face(face, dark or (mats.get("head") if mats else None), mats.get("head"), glow_eyes=glow_eyes)

    # ---------------------------------------------------------------- posed points and costume
    def _mat(self, part, z):
        chain = CHAINS[ALIAS[part]]
        if len(chain) == 1:
            return self.D[chain[0][0]]
        (ja, zc), (jb, _) = chain
        t = min(1.0, max(0.0, (z - (zc - BLEND)) / (2 * BLEND)))       # 0 below the joint (jb), 1 above (ja)
        if t >= 1.0:
            return self.D[ja]
        if t <= 0.0:
            return self.D[jb]
        a, b = self.D[ja], self.D[jb]
        return Matrix([[b[i][k] + (a[i][k] - b[i][k]) * t for k in range(4)] for i in range(4)])

    def at(self, part, p):
        p = Vector(p)
        return self.G @ self._mat(part, p.z) @ p

    def build(self, part, fn):
        s = len(P.PARTS)
        fn()
        for ob in P.PARTS[s:]:
            if ob.type != "MESH":
                continue
            ob.data.transform(ob.matrix_world)
            ob.matrix_world = Matrix.Identity(4)
            for v in ob.data.vertices:
                v.co = self.G @ self._mat(part, v.co.z) @ v.co
            ob.data.update()

    def face(self, kind, dark, m, glow_eyes=None):
        """A carved face on the round head. glow_eyes = a Glow group name ("Glow", "Glow2") puts the eyes in it."""
        from nh_props import box, tube
        from nh_props_batch3 import sphere, cone

        def eyes(y, scale=(1.0, 0.35, 1.3), z=4.6, r=0.09, slant=0.0):
            if glow_eyes:
                g0 = P.GROUP
                P.set_group(glow_eyes)
            for sx in (-1, 1):
                ob = sphere(f"Eye{sx}", r, (sx * 0.22, y + 0.015, z), dark, seg=8, rings=4, scale=scale)
                if slant:
                    ob.rotation_euler[1] = -sx * slant
            if glow_eyes:
                P.set_group(g0)

        def h():
            y = -0.6
            if kind == "closed":
                for sx in (-1, 1):
                    tube(f"Lid{sx}", [(sx * 0.1, y, 4.58), (sx * 0.22, y - 0.01, 4.54), (sx * 0.34, y, 4.58)], 0.022, dark)
            elif kind in ("fierce", "snarl", "shout", "howl"):
                eyes(y, (1.2, 0.35, 0.9), z=4.6, slant=0.35)
            else:
                eyes(y)
            br = {"fierce": 0.38, "snarl": 0.42, "shout": 0.3, "howl": -0.25, "sad": -0.3, "smirk": 0.1}.get(kind, 0.18)
            for sx in (-1, 1):
                lift = 0.04 if (kind == "smirk" and sx > 0) else 0.0
                box(f"Brow{sx}", (0.3, 0.06, 0.07), (sx * 0.22, y - 0.01, 4.77 + lift - (0.03 if br > 0.3 else 0)), m, bevel=0.02, rot=(0, -sx * br, 0))
            if kind in ("sing", "howl", "shout"):
                sc = {"sing": (0.9, 0.3, 1.2), "howl": (1.0, 0.3, 1.6), "shout": (1.5, 0.3, 1.0)}[kind]
                sphere("Mouth", 0.11, (0, y + 0.02, 4.3), dark, seg=10, rings=6, scale=sc)
            elif kind == "snarl":
                box("Mouth", (0.46, 0.04, 0.12), (0, y, 4.29), dark, bevel=0.02)
                for sx in (-1, 1):
                    cone(f"Fang{sx}", 0.035, 0.0, 0.12, (sx * 0.12, y - 0.025, 4.25), m, verts=4, rot=(3.1416, 0, 0))
            elif kind == "smirk":
                tube("Smirk", [(-0.2, y, 4.3), (0.0, y - 0.005, 4.29), (0.16, y - 0.005, 4.31), (0.26, y, 4.37)], 0.024, dark)
            elif kind == "smile":
                tube("Smile", [(-0.26, y, 4.36), (-0.13, y - 0.005, 4.27), (0.0, y - 0.006, 4.24), (0.13, y - 0.005, 4.27), (0.26, y, 4.36)], 0.025, dark)
            elif kind == "fierce":
                box("Mouth", (0.4, 0.04, 0.09), (0, y, 4.28), dark, bevel=0.02)
            elif kind != "none":
                box("Mouth", (0.34, 0.04, 0.05), (0, y, 4.28), dark, bevel=0.015)
            box("Nose", (0.1, 0.07, 0.2), (0, y - 0.025, 4.45), m, bevel=0.035)
        self.build("head", h)

    # ---------------------------------------------------------------- colliders and settling
    BOXES = [("torso", "waist", (0, 0, 3.5), (1.0, 0.5, 0.5)), ("torso", "root", (0, 0, 2.5), (1.0, 0.5, 0.5)),
             ("rarm", "rshoulder", (1.5, 0, 3.5), (0.5, 0.5, 0.55)), ("rarm", "relbow", (1.5, 0, 2.5), (0.5, 0.5, 0.55)),
             ("larm", "lshoulder", (-1.5, 0, 3.5), (0.5, 0.5, 0.55)), ("larm", "lelbow", (-1.5, 0, 2.5), (0.5, 0.5, 0.55)),
             ("rleg", "rhip", (0.5, 0, 1.5), (0.5, 0.5, 0.55)), ("rleg", "rknee", (0.5, 0, 0.5), (0.5, 0.5, 0.55)),
             ("lleg", "lhip", (-0.5, 0, 1.5), (0.5, 0.5, 0.55)), ("lleg", "lknee", (-0.5, 0, 0.5), (0.5, 0.5, 0.55)),
             ("head", "neck", (0, 0, 4.6), (0.62, 0.62, 0.62))]

    def colliders(self, pad=0.0, skip=()):
        """Oriented boxes of the posed body, for showpiece44_geo.drape: (world matrix of the box's unit frame, half extents)."""
        out = []
        for part, j, c, h in self.BOXES:
            if part in skip:
                continue
            M = self.G @ self.D[j] @ Matrix.Translation(c)
            out.append((M, Vector(h) + Vector((pad, pad, pad))))
        return out

    def settle(self, z, parts=None, extra=0.0):
        """Move everything built for this figure since it was made so its lowest foot corner (or lowest point of the
        `parts` objects, when given) rests on z; extra lowers it by that much more (a boot sole's thickness is added by
        the boots themselves)."""
        bpy.context.view_layer.update()
        obs = [o for o in P.PARTS[self.start:] if o.type == "MESH"]
        if parts is not None:
            lo = min((o.matrix_world @ v.co).z for o in parts for v in o.data.vertices)
        else:
            pts = [self.at(leg, (sx * 0.5 + dx, dy, 0.0)) for leg, sx in (("rleg", 1), ("lleg", -1)) for dx in (-0.45, 0.45) for dy in (-0.45, 0.45)]
            lo = min(p.z for p in pts)
        dz = z - lo - extra
        for o in obs:
            o.matrix_world = Matrix.Translation((0, 0, dz)) @ o.matrix_world
        self.G = Matrix.Translation((0, 0, dz)) @ self.G
        return dz

    def world(self, j):
        """The posed world matrix of a joint (rest frame of its part)."""
        return self.G @ self.D[j]

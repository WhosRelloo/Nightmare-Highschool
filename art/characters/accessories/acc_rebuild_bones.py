"""Rebuild a template piece's bones in Studio from the builder's .blend (the exact rest frames the FBX carried).

python acc_rebuild_bones.py <Item>[,<Item>...]   ->  tools/accessories/rebuild_bones_<first item>.luau (+ runs Blender)

Why: when an item's FBX has several pieces, Roblox's importer puts the bones on a separate part of the imported
model, and acc_assemble keeps only the named MeshParts, so a rigged piece arrives with its skin weights but no bones
(1.86: both coats' tails, the scarves, the ledger, the mantle's crows). The meshes still carry the weights by bone
name, so bones rebuilt at the bind pose restore them.
Convention (fitted on three imported rigs, exact to 2e-6 studs): a bone's frame in the piece's space is
  rotation  A @ R_blender @ K,  A = [[-1,0,0],[0,0,1],[0,1,0]] (Blender -> Roblox), K = diag(-1, 1, -1)
  position  A @ (head - piece bounding-box centre)          (the import centres each MeshPart on its box)
and each bone's CFrame is relative to its parent (Root's to the piece).
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "E:/NH-Work/acc"
items = sys.argv[1].split(",")
DUMP = os.path.join(ROOT, "bones_rebuild.json")
BLENDER_SIDE = r'''
import bpy, json, sys
from mathutils import Vector
items = sys.argv[sys.argv.index("--") + 1].split(",")
out = {}
for it in items:
    lay = json.load(open(f"%(root)s/layout/{it}.json"))
    bpy.ops.wm.open_mainfile(filepath=f"%(root)s/blend/{it}.blend")
    for pn, e in lay["pieces"].items():
        arm = bpy.data.objects.get(pn + "Rig")
        if arm is None:
            continue
        ob = bpy.data.objects[pn]
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        pts = [ob.matrix_world @ v.co for v in me.vertices]
        ob.evaluated_get(dg).to_mesh_clear()
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        out[f"{it}.{pn}"] = dict(centre=list((lo + hi) / 2), bones=[
            dict(name=b.name, parent=b.parent.name if b.parent else None, m=[list(r) for r in arm.matrix_world @ b.matrix_local])
            for b in arm.data.bones])
json.dump(out, open("%(dump)s", "w"))
''' % dict(root=ROOT, dump=DUMP.replace("\\", "/"))
side = os.path.join(ROOT, "tmp", "bones_dump.py")
os.makedirs(os.path.dirname(side), exist_ok=True)
open(side, "w").write(BLENDER_SIDE)
subprocess.run(["E:/Blender/blender.exe", "-b", "--factory-startup", "-P", side, "--", ",".join(items)], check=True,
               stdout=subprocess.DEVNULL)
B = json.load(open(DUMP))
A = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
K = np.diag([-1.0, 1.0, -1.0])
L = ['if game.PlaceId ~= 98950102230473 then return "WRONG PLACE" end', "local st = game.ReplicatedStorage.NHAccessories",
     "local rep = {}"]
for key, e in B.items():
    it, pn = key.split(".")
    c = np.array(e["centre"])
    world = {}
    L.append(f'do local p = st:FindFirstChild("{it}") and st["{it}"]:FindFirstChild("{pn}")')
    L.append(f'  if not p then table.insert(rep, "{key} missing") else')
    L.append('  for _, x in p:GetChildren() do if x:IsA("Bone") then x:Destroy() end end')
    L.append("  local B = {}")
    for b in e["bones"]:
        M = np.array(b["m"])
        W = np.eye(4)
        W[:3, :3] = A @ M[:3, :3] @ K
        W[:3, 3] = A @ (M[:3, 3] - c)
        world[b["name"]] = W
        P = world[b["parent"]] if b["parent"] else np.eye(4)
        Lc = np.linalg.inv(P) @ W
        comps = ", ".join("%.7f" % x for x in list(Lc[:3, 3]) + list(Lc[:3, :3].reshape(-1)))
        par = f'B["{b["parent"]}"]' if b["parent"] else "p"
        n = b["name"]
        L.append(f'  B["{n}"] = Instance.new("Bone") B["{n}"].Name = "{n}" B["{n}"].CFrame = CFrame.new({comps}) B["{n}"].Parent = {par}')
    L.append('  local n = 0 for _, x in p:GetDescendants() do if x:IsA("Bone") then n += 1 end end')
    L.append(f'  table.insert(rep, "{key}: " .. n .. " bones, skinned " .. tostring(p.HasSkinnedMesh)) end end')
L.append("return table.concat(rep, string.char(10))")
out = os.path.join(REPO := os.path.abspath(os.path.join(HERE, "..", "..", "..")), "tools", "accessories", f"rebuild_bones_{items[0]}.luau")
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print(out, len(B), "pieces")

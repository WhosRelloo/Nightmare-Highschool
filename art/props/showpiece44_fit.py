"""Props batch 44 (the showpiece kit): keeping layered clothing clean. Hair, headwear, hoods, collars and garments are
tested against each other with BVH-tree overlaps of their evaluated meshes, and headwear is seated (moved up off
the hair) or hoods eased (scaled out about the head) until nothing pokes through.
"""
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def _tree(ob):
    """A BVH tree of the object's evaluated mesh in world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def overlap(a, b):
    """Number of overlapping triangle pairs between two objects (their modifiers applied)."""
    bpy.context.view_layer.update()
    return len(_tree(a).overlap(_tree(b)))


def any_overlap(obs, against):
    bpy.context.view_layer.update()
    ta = [_tree(o) for o in obs if o is not None]
    tb = [_tree(o) for o in against if o is not None]
    return sum(len(x.overlap(y)) for x in ta for y in tb)


def seat(obs, against, up, step=0.02, max_move=1.0):
    """Lift the headwear `obs` along the world direction `up` until it clears `against` (hair, head)."""
    up = Vector(up).normalized()
    moved = 0.0
    while any_overlap(obs, against) and moved < max_move:
        for o in obs:
            o.matrix_world = Matrix.Translation(up * step) @ o.matrix_world
        moved += step
    return moved


def ease(obs, against, centre, step=0.03, max_scale=1.4):
    """Scale a hood or cowl out about `centre` until it clears the head and hair."""
    c = Vector(centre)
    k = 1.0
    while any_overlap(obs, against) and k < max_scale:
        f = (k + step) / k
        for o in obs:
            o.matrix_world = Matrix.Translation(c) @ Matrix.Scale(f, 4) @ Matrix.Translation(-c) @ o.matrix_world
        k += step
    return k


def report(groups):
    """groups: {label: [objects]}; prints the overlapping pairs between every two groups."""
    labels = list(groups)
    out = []
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            n = any_overlap(groups[a], groups[b])
            if n:
                out.append((a, b, n))
    return out


def apply_mods(ob):
    """Apply an object's modifiers in place (so its vertices can be trimmed)."""
    if not ob.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)


def trim_inside(ob, test):
    """Delete the vertices of `ob` (world space) for which test(point) is true, with the faces using them."""
    import bmesh
    apply_mods(ob)
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [v for v in bm.verts if test(mw @ v.co)]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(ob.data)
    bm.free()
    return len(kill)


def inside_obbs(boxes):
    """A test for trim_inside: inside any of the oriented boxes [(matrix, half extents)]."""
    inv = [(M.inverted(), h) for M, h in boxes]

    def t(p):
        for Mi, h in inv:
            q = Mi @ p
            if abs(q.x) < h.x and abs(q.y) < h.y and abs(q.z) < h.z:
                return True
        return False
    return t


def inside_mesh(obs):
    """A test for trim_inside: inside any of these closed meshes (nearest-surface normal test)."""
    trees = [_tree(o) for o in obs]

    def t(p):
        for tr in trees:
            hit = tr.find_nearest(p)
            if hit[0] is not None and (p - hit[0]).dot(hit[1]) < 0:
                return True
        return False
    return t


def ease_xy(obs, against, centre, up, step=0.03, max_scale=1.5):
    """Widen a crown or circlet about the head's up axis (not up the head) until it clears the hair and head."""
    c = Vector(centre)
    u = Vector(up).normalized()
    Rm = u.rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
    k = 1.0
    while any_overlap(obs, against) and k < max_scale:
        f = (k + step) / k
        S = Matrix.Diagonal((f, f, 1.0, 1.0))
        for o in obs:
            o.matrix_world = Matrix.Translation(c) @ Rm.inverted() @ S @ Rm @ Matrix.Translation(-c) @ o.matrix_world
        k += step
    return k

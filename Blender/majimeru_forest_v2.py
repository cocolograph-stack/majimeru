# ============================================================
# __  __    _      _ ___ __  __ _____ ____  _   _
# |  \/  |  / \    | |_ _|  \/  | ____|  _ \| | | |
# | |\/| | / _ \ _ | || || |\/| |  _| | |_) | | | |
# | |  | |/ ___ \| || || || |  | | |___|  _ <| |_| |
# |_|  |_/_/   \_\\___/|___|_|  |_|_____|_| \\_\\___/
#
# Author: majimeru + tobiuo-pyonpyon
# Tool: majimeru_forest  v2
# What    : Blender tool: scatter trees/rocks on a ground (keeping clear
#           of a path curve), colour them in 3 depth layers, and add a
#           gentle geometry-nodes sway to selected objects.
# YouTube: https://www.youtube.com/@3DCGいろいろ
# License: GPL-3.0
# ============================================================
import bpy
import random
from mathutils import Vector
from bpy.props import (
    IntProperty, FloatProperty, PointerProperty, FloatVectorProperty,
)
from bpy.types import Operator, Panel

bl_info = {
    "name": "Majimeru Forest",
    "author": "majimeru + tobiuo-pyonpyon",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar (N) > Majimeru",
    "description": "Scatter a forest with 3 depth colour layers and a gentle sway",
    "category": "Object",
}


MAT_NAMES = ("MajimeruForest_Near", "MajimeruForest_Mid", "MajimeruForest_Far")
SWAY_GROUP = "MajimeruSway"


def get_mat(idx, color):
    name = MAT_NAMES[idx]
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


def get_sway_group():
    tree = bpy.data.node_groups.get(SWAY_GROUP)
    if tree is not None:
        return tree
    tree = bpy.data.node_groups.new(SWAY_GROUP, "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n = tree.nodes
    inp = n.new("NodeGroupInput"); inp.location = (-700, 0)
    out = n.new("NodeGroupOutput"); out.location = (500, 0)
    setpos = n.new("GeometryNodeSetPosition"); setpos.location = (250, 0)
    pos = n.new("GeometryNodeInputPosition"); pos.location = (-700, -250)
    sep = n.new("ShaderNodeSeparateXYZ"); sep.location = (-520, -250)
    mask = n.new("ShaderNodeMath"); mask.location = (-340, -250)
    mask.operation = "MULTIPLY"
    mask.inputs[1].default_value = 0.12
    mask.use_clamp = True
    comb = n.new("ShaderNodeCombineXYZ"); comb.location = (60, -250)
    time = n.new("GeometryNodeInputSceneTime"); time.location = (-700, -520)
    slow = n.new("ShaderNodeMath"); slow.location = (-520, -520)
    slow.operation = "DIVIDE"
    slow.inputs[1].default_value = 90.0
    noise = n.new("ShaderNodeTexNoise"); noise.location = (-340, -520)
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 1.5
    vscale = n.new("ShaderNodeVectorMath"); vscale.location = (-120, -520)
    vscale.operation = "SCALE"
    vscale.inputs[3].default_value = 0.6
    vmul = n.new("ShaderNodeVectorMath"); vmul.location = (60, -420)
    vmul.operation = "MULTIPLY"
    L = tree.links
    L.new(inp.outputs["Geometry"], setpos.inputs["Geometry"])
    L.new(setpos.outputs["Geometry"], out.inputs["Geometry"])
    L.new(pos.outputs["Position"], sep.inputs["Vector"])
    L.new(sep.outputs["Z"], mask.inputs[0])
    L.new(mask.outputs["Value"], comb.inputs["X"])
    L.new(mask.outputs["Value"], comb.inputs["Y"])
    L.new(comb.outputs["Vector"], vmul.inputs[0])
    L.new(time.outputs["Frame"], slow.inputs[0])
    L.new(slow.outputs["Value"], noise.inputs["W"])
    L.new(noise.outputs["Color"], vscale.inputs[0])
    L.new(vscale.outputs["Vector"], vmul.inputs[1])
    L.new(vmul.outputs["Vector"], setpos.inputs["Offset"])
    return tree


def path_samples(obj, dg):
    """Dense world-space points along a curve object, for distance checks."""
    if obj is None:
        return []
    pts = []
    try:
        ev = obj.evaluated_get(dg)
        mesh = ev.to_mesh()
        pts = [obj.matrix_world @ v.co for v in mesh.vertices]
        ev.to_mesh_clear()
    except Exception:
        pts = []
    if len(pts) < 2 and getattr(obj, "type", "") == "CURVE":
        mw = obj.matrix_world
        for sp in obj.data.splines:
            if sp.type == "BEZIER":
                pts.extend(mw @ p.co for p in sp.bezier_points)
            else:
                pts.extend(mw @ Vector((p.co.x, p.co.y, p.co.z)) for p in sp.points)
    dense = []
    for a, b in zip(pts, pts[1:]):
        steps = max(1, int((b - a).length / 1.5))
        for i in range(steps):
            dense.append(a.lerp(b, i / steps))
    if pts:
        dense.append(pts[-1])
    return dense


class MAJIMERU_OT_scatter(Operator):
    bl_idname = "majimeru_forest.scatter"
    bl_label = "森をばらまく"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        src = sc.forest_src_collection
        ground = sc.forest_ground
        if src is None:
            self.report({"ERROR"}, "ばらまく物のコレクションを選んで")
            return {"CANCELLED"}
        if ground is None:
            self.report({"ERROR"}, "地面のオブジェクトを選んで")
            return {"CANCELLED"}
        protos = [o for o in src.all_objects if o.type == "MESH"]
        if not protos:
            self.report({"ERROR"}, "コレクションの中にメッシュが無い")
            return {"CANCELLED"}
        corners = [ground.matrix_world @ Vector(c) for c in ground.bound_box]
        xs = [c.x for c in corners]; ys = [c.y for c in corners]; zs = [c.z for c in corners]
        top = max(zs) + 10.0
        cam = sc.camera
        origin = cam.matrix_world.translation if cam else Vector((0, 0, 0))
        mats = [get_mat(0, sc.forest_col_near), get_mat(1, sc.forest_col_mid), get_mat(2, sc.forest_col_far)]
        target = bpy.data.collections.get("MajimeruForest")
        if target is None:
            target = bpy.data.collections.new("MajimeruForest")
            context.scene.collection.children.link(target)
        rng = random.Random(sc.forest_seed)
        dg = context.evaluated_depsgraph_get()
        samples = path_samples(sc.forest_path, dg)
        margin = sc.forest_path_margin
        down = Vector((0, 0, -1))
        made = 0
        for _ in range(sc.forest_count):
            for _try in range(10):
                x = rng.uniform(min(xs), max(xs))
                y = rng.uniform(min(ys), max(ys))
                hit, loc, _n, _i, obj, _m = sc.ray_cast(dg, (x, y, top), down)
                if not (hit and obj == ground):
                    continue
                if samples:
                    dmin = min((Vector((x, y, 0)) - Vector((p.x, p.y, 0))).length for p in samples)
                    if dmin < margin:
                        continue
                break
            else:
                continue
            proto = rng.choice(protos)
            ob = proto.copy()
            ob.data = proto.data.copy()
            target.objects.link(ob)
            ob.location = loc
            ob.rotation_euler = (0, 0, rng.uniform(0, 6.2832))
            f = rng.uniform(sc.forest_scale_min, sc.forest_scale_max)
            ob.scale = (proto.scale.x * f, proto.scale.y * f, proto.scale.z * f)
            d = (loc - origin).length
            idx = 0 if d < sc.forest_band1 else (1 if d < sc.forest_band2 else 2)
            ob.data.materials.clear()
            ob.data.materials.append(mats[idx])
            made += 1
        self.report({"INFO"}, "森をばらまいた: %d 本" % made)
        return {"FINISHED"}


class MAJIMERU_OT_sway(Operator):
    bl_idname = "majimeru_forest.sway"
    bl_label = "選んだ物にそよぎを付ける"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        group = get_sway_group()
        done = 0
        for ob in context.selected_objects:
            if ob.type != "MESH":
                continue
            if any(m.type == "NODES" and m.node_group == group for m in ob.modifiers):
                continue
            mod = ob.modifiers.new("そよぎ", "NODES")
            mod.node_group = group
            done += 1
        self.report({"INFO"}, "そよぎを付けた: %d 個" % done)
        return {"FINISHED"}


class MAJIMERU_PT_forest(Panel):
    bl_idname = "MAJIMERU_PT_forest"
    bl_label = "森づくり"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        box = layout.box()
        box.label(text="ばらまく準備", icon="OUTLINER_COLLECTION")
        box.prop(sc, "forest_src_collection", text="ばらまく物")
        box.prop(sc, "forest_ground", text="地面")
        box.prop(sc, "forest_count", text="数")
        box.prop(sc, "forest_seed", text="タネ（並びの決め方）")
        row = box.row(align=True)
        row.prop(sc, "forest_scale_min", text="大きさ最小")
        row.prop(sc, "forest_scale_max", text="大きさ最大")
        big = box.row()
        big.scale_y = 1.5
        big.operator("majimeru_forest.scatter", text="森をばらまく", icon="PARTICLES")

        box = layout.box()
        box.label(text="道よけ", icon="CURVE_PATH")
        box.prop(sc, "forest_path", text="道（カーブ）")
        box.prop(sc, "forest_path_margin", text="道から空ける距離 (m)")
        box.label(text="道の近くには、ばらまかへんよ")

        box = layout.box()
        box.label(text="色の3層（カメラからの距離）", icon="COLOR")
        box.prop(sc, "forest_band1", text="手前の終わり (m)")
        box.prop(sc, "forest_band2", text="中間の終わり (m)")
        box.prop(sc, "forest_col_near", text="手前の色")
        box.prop(sc, "forest_col_mid", text="中間の色")
        box.prop(sc, "forest_col_far", text="遠くの色")

        box = layout.box()
        box.label(text="そよぎ", icon="FORCE_WIND")
        box.operator("majimeru_forest.sway", text="選んだ物にそよぎを付ける")
        box.label(text="頭だけ揺れて、根元は動かへんよ")


classes = (
    MAJIMERU_OT_scatter,
    MAJIMERU_OT_sway,
    MAJIMERU_PT_forest,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    sc = bpy.types.Scene
    sc.forest_src_collection = PointerProperty(name="Src", type=bpy.types.Collection)
    sc.forest_ground = PointerProperty(name="Ground", type=bpy.types.Object)
    sc.forest_count = IntProperty(name="Count", default=100, min=1, max=5000)
    sc.forest_seed = IntProperty(name="Seed", default=1, min=0)
    sc.forest_scale_min = FloatProperty(name="Min", default=0.8, min=0.05, max=10.0)
    sc.forest_scale_max = FloatProperty(name="Max", default=1.3, min=0.05, max=10.0)
    sc.forest_band1 = FloatProperty(name="Band1", default=15.0, min=0.0)
    sc.forest_band2 = FloatProperty(name="Band2", default=40.0, min=0.0)
    sc.forest_col_near = FloatVectorProperty(name="Near", subtype="COLOR", size=4,
        default=(0.015, 0.09, 0.09, 1.0), min=0.0, max=1.0)
    sc.forest_col_mid = FloatVectorProperty(name="Mid", subtype="COLOR", size=4,
        default=(0.03, 0.30, 0.05, 1.0), min=0.0, max=1.0)
    sc.forest_path = PointerProperty(name="Path", type=bpy.types.Object)
    sc.forest_path_margin = FloatProperty(name="Margin", default=3.0, min=0.0, max=50.0)
    sc.forest_col_far = FloatVectorProperty(name="Far", subtype="COLOR", size=4,
        default=(0.45, 0.55, 0.78, 1.0), min=0.0, max=1.0)


def unregister():
    sc = bpy.types.Scene
    for name in ("forest_src_collection", "forest_ground", "forest_count", "forest_seed",
                 "forest_path", "forest_path_margin",
                 "forest_scale_min", "forest_scale_max", "forest_band1", "forest_band2",
                 "forest_col_near", "forest_col_mid", "forest_col_far"):
        if hasattr(sc, name):
            delattr(sc, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

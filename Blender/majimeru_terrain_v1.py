# ============================================================
# __  __    _      _ ___ __  __ _____ ____  _   _
# |  \/  |  / \    | |_ _|  \/  | ____|  _ \| | | |
# | |\/| | / _ \ _ | || || |\/| |  _| | |_) | | | |
# | |  | |/ ___ \| || || || |  | | |___|  _ <| |_| |
# |_|  |_/_/   \_\\___/|___|_|  |_|_____|_| \\_\\___/
#
# Author: majimeru + tobiuo-pyonpyon
# Tool: majimeru_terrain  v1
# What    : Blender tool: one-click stage builder. From a seed number it
#           makes a mountain slope, a winding downhill path and a lake.
#           Change the seed and press again for a different stage.
# YouTube: https://www.youtube.com/@3DCGいろいろ
# License: GPL-3.0
# ============================================================
import bpy
import math
import random
from mathutils import Vector
from bpy.props import IntProperty, FloatProperty
from bpy.types import Operator, Panel

bl_info = {
    "name": "Majimeru Terrain",
    "author": "majimeru + tobiuo-pyonpyon",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar (N) > Majimeru",
    "description": "Seed-based stage builder: mountain slope, winding path, lake",
    "category": "Object",
}

COLL_NAME = "MajimeruTerrain"


def _hash2(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 974634211) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _vnoise(x, y, seed):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx = fx * fx * (3 - 2 * fx)
    sy = fy * fy * (3 - 2 * fy)
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy


def _fbm(x, y, seed, octaves=4):
    v = 0.0
    amp = 0.5
    f = 1.0
    for o in range(octaves):
        v += amp * _vnoise(x * f, y * f, seed + o * 101)
        f *= 2.03
        amp *= 0.5
    return v


def _smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def make_mat(name, color, rough=1.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    return mat


def make_terrain_mat():
    name = "MajimeruTerrainMat"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 1.0
    return mat


class MAJIMERU_OT_build_terrain(Operator):
    bl_idname = "majimeru_terrain.build"
    bl_label = "地面を作る"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        seed = sc.terrain_seed
        size = sc.terrain_size
        height = sc.terrain_height
        half_path = sc.terrain_path_width / 2.0
        res = 110
        rng = random.Random(seed * 7919 + 13)

        # ---------- path centreline ----------
        n = 150
        a1 = rng.uniform(13.0, 26.0)
        f1 = rng.uniform(0.7, 1.2)
        p1 = rng.uniform(0.0, 6.28)
        a2 = rng.uniform(3.0, 9.0)
        f2 = rng.uniform(2.0, 3.2)
        p2 = rng.uniform(0.0, 6.28)
        centre = []
        for i in range(n):
            t = i / (n - 1)
            y = (0.46 - 0.80 * t) * size
            x = a1 * math.sin(6.2832 * f1 * t + p1) + a2 * math.sin(6.2832 * f2 * t + p2)
            centre.append([x, y, 0.0])

        def base_height(x, y):
            u = (y + size / 2.0) / size
            h = height * (max(0.0, u) ** 1.35)
            h += (_fbm(x * 0.012 + 40, y * 0.012 + 40, seed) - 0.5) * 13.0
            h += (_fbm(x * 0.05, y * 0.05, seed + 7) - 0.5) * 2.0
            lake_w = _smoothstep(-0.20 * size, -0.34 * size, y)
            h = h * (1.0 - lake_w) + 0.3 * lake_w
            return h

        for c in centre:
            c[2] = base_height(c[0], c[1])
        for _pass in range(3):
            zs = [c[2] for c in centre]
            for i in range(n):
                lo = max(0, i - 6)
                hi = min(n, i + 7)
                centre[i][2] = sum(zs[lo:hi]) / (hi - lo)

        def nearest_path(x, y):
            best = None
            bestd = 1e18
            for c in centre:
                d = (c[0] - x) ** 2 + (c[1] - y) ** 2
                if d < bestd:
                    bestd = d
                    best = c
            return best, math.sqrt(bestd)

        # ---------- collection ----------
        coll = bpy.data.collections.get(COLL_NAME)
        if coll is None:
            coll = bpy.data.collections.new(COLL_NAME)
            sc.collection.children.link(coll)
        else:
            for ob in list(coll.objects):
                data = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                if data is not None and data.users == 0:
                    if isinstance(data, bpy.types.Mesh):
                        bpy.data.meshes.remove(data)
                    elif isinstance(data, bpy.types.Curve):
                        bpy.data.curves.remove(data)
                    elif isinstance(data, bpy.types.Light):
                        bpy.data.lights.remove(data)
                    elif isinstance(data, bpy.types.Camera):
                        bpy.data.cameras.remove(data)

        # ---------- terrain mesh ----------
        verts = []
        colors = []
        step = size / (res - 1)
        for j in range(res):
            y = -size / 2.0 + j * step
            for i in range(res):
                x = -size / 2.0 + i * step
                h = base_height(x, y)
                c, d = nearest_path(x, y)
                w = _smoothstep(half_path, half_path + 7.0, d)
                z = c[2] * (1.0 - w) + h * w
                verts.append((x, y, z))
                nz = (_fbm(x * 0.03 + 90, y * 0.03 + 90, seed + 3) - 0.5) * 0.10
                if d < half_path + 0.5:
                    col = (0.45 + nz, 0.36 + nz, 0.22)
                elif z < 2.0:
                    col = (0.16 + nz, 0.34 + nz, 0.10)
                elif z < height * 0.55:
                    col = (0.05 + nz, 0.32 + nz, 0.06)
                else:
                    col = (0.25 + nz, 0.38 + nz, 0.30)
                colors.append((col[0], col[1], col[2], 1.0))
        faces = []
        for j in range(res - 1):
            for i in range(res - 1):
                a = j * res + i
                faces.append((a, a + 1, a + 1 + res, a + res))
        tmesh = bpy.data.meshes.new("TerrainMesh")
        tmesh.from_pydata(verts, [], faces)
        tmesh.update()
        attr = tmesh.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        for idx, cval in enumerate(colors):
            attr.data[idx].color = cval
        tob = bpy.data.objects.new("Terrain", tmesh)
        tob.data.materials.append(make_terrain_mat())
        coll.objects.link(tob)

        # ---------- path ribbon ----------
        rverts = []
        rfaces = []
        for i in range(0, n - 1, 2):
            c = centre[i]
            c2 = centre[min(i + 2, n - 1)]
            dx, dy = c2[0] - c[0], c2[1] - c[1]
            ln = math.hypot(dx, dy) or 1.0
            px, py = -dy / ln, dx / ln
            rverts.append((c[0] - px * half_path, c[1] - py * half_path, c[2] + 0.07))
            rverts.append((c[0] + px * half_path, c[1] + py * half_path, c[2] + 0.07))
        rows = len(rverts) // 2
        for i in range(rows - 1):
            a = i * 2
            rfaces.append((a, a + 1, a + 3, a + 2))
        pmesh = bpy.data.meshes.new("PathMesh")
        pmesh.from_pydata(rverts, [], rfaces)
        pmesh.update()
        pob = bpy.data.objects.new("Path", pmesh)
        pob.data.materials.append(make_mat("MajimeruPathMat", (0.48, 0.38, 0.23)))
        coll.objects.link(pob)

        # ---------- path curve (for the forest addon's keep-clear) ----------
        cu = bpy.data.curves.new("PathCurveData", "CURVE")
        cu.dimensions = "3D"
        sp = cu.splines.new("POLY")
        sp.points.add(n - 1)
        for i, c in enumerate(centre):
            sp.points[i].co = (c[0], c[1], c[2] + 0.1, 1.0)
        cob = bpy.data.objects.new("PathCurve", cu)
        coll.objects.link(cob)

        # ---------- lake ----------
        lverts = [(0.0, -0.40 * size, 0.35)]
        lfaces = []
        seg = 40
        lr = 0.24 * size
        for i in range(seg):
            ang = 6.2832 * i / seg
            lverts.append((math.cos(ang) * lr, -0.40 * size + math.sin(ang) * lr * 0.7, 0.35))
        for i in range(seg):
            lfaces.append((0, 1 + i, 1 + (i + 1) % seg))
        lmesh = bpy.data.meshes.new("LakeMesh")
        lmesh.from_pydata(lverts, [], lfaces)
        lmesh.update()
        lob = bpy.data.objects.new("Lake", lmesh)
        lob.data.materials.append(make_mat("MajimeruLakeMat", (0.45, 0.60, 0.80), rough=0.15))
        coll.objects.link(lob)

        # ---------- sun and camera ----------
        sun_data = bpy.data.lights.new("SunData", "SUN")
        sun_data.energy = 3.0
        sun_data.color = (1.0, 0.72, 0.45)
        sun = bpy.data.objects.new("Sun", sun_data)
        sun.rotation_euler = (math.radians(58), 0, math.radians(-38))
        coll.objects.link(sun)

        cam_data = bpy.data.cameras.new("CamData")
        cam = bpy.data.objects.new("Camera", cam_data)
        start = centre[18]
        look = centre[70]
        cam.location = (start[0] - 6.0, start[1] + 10.0, start[2] + 4.0)
        direction = Vector((look[0], look[1], look[2])) - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        coll.objects.link(cam)
        sc.camera = cam

        self.report({"INFO"}, "地面を作った（シード %d）" % seed)
        return {"FINISHED"}


class MAJIMERU_PT_terrain(Panel):
    bl_idname = "MAJIMERU_PT_terrain"
    bl_label = "地面づくり"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        box = layout.box()
        box.label(text="舞台をまるごと作る", icon="WORLD")
        box.prop(sc, "terrain_seed", text="シード（地形のタネ）")
        box.prop(sc, "terrain_size", text="大きさ (m)")
        box.prop(sc, "terrain_height", text="山の高さ (m)")
        box.prop(sc, "terrain_path_width", text="道の幅 (m)")
        big = box.row()
        big.scale_y = 1.5
        big.operator("majimeru_terrain.build", text="地面を作る", icon="MESH_PLANE")
        box.label(text="シードを変えて押し直すと、別の地形になる")
        box.label(text="山の斜面＋うねる下り道＋湖がセット")
        box.label(text="道のカーブ (PathCurve) は森づくりの")
        box.label(text="「道よけ」にそのまま使えるよ")


classes = (
    MAJIMERU_OT_build_terrain,
    MAJIMERU_PT_terrain,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    sc = bpy.types.Scene
    sc.terrain_seed = IntProperty(name="Seed", default=1, min=0)
    sc.terrain_size = FloatProperty(name="Size", default=240.0, min=40.0, max=1000.0)
    sc.terrain_height = FloatProperty(name="Height", default=26.0, min=1.0, max=200.0)
    sc.terrain_path_width = FloatProperty(name="PathWidth", default=3.6, min=1.0, max=20.0)


def unregister():
    sc = bpy.types.Scene
    for name in ("terrain_seed", "terrain_size", "terrain_height", "terrain_path_width"):
        if hasattr(sc, name):
            delattr(sc, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

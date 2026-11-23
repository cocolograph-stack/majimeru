# ============================================================
# __  __    _      _ ___ __  __ _____ ____  _   _
# |  \/  |  / \    | |_ _|  \/  | ____|  _ \| | | |
# | |\/| | / _ \ _ | || || |\/| |  _| | |_) | | | |
# | |  | |/ ___ \| || || || |  | | |___|  _ <| |_| |
# |_|  |_/_/   \_\\___/|___|_|  |_|_____|_| \\_\\___/
#
# Author: majimeru + tobiuo-pyonpyon
# Tool: majimeru_pop  v1
# What    : Blender tool: pop-out helper. Place an animal where it should
#           appear, press one button, and the addon keys it hidden behind
#           cover, popping out at your frame and slipping back later.
# YouTube: https://www.youtube.com/@3DCGいろいろ
# License: GPL-3.0
# ============================================================
import bpy
from mathutils import Vector
from bpy.props import IntProperty, FloatVectorProperty
from bpy.types import Operator, Panel

bl_info = {
    "name": "Majimeru Pop",
    "author": "majimeru + tobiuo-pyonpyon",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar (N) > Majimeru",
    "description": "One-click pop-out keyframes for animals appearing briefly",
    "category": "Animation",
}


def action_channelbags(action):
    """All channelbags of an action (Blender 5.x layered actions)."""
    bags = []
    for layer in action.layers:
        for strip in layer.strips:
            bags.extend(list(strip.channelbags))
    return bags


def action_fcurves(action):
    fcs = []
    for cb in action_channelbags(action):
        fcs.extend(list(cb.fcurves))
    return fcs


def _key(ob, path, frame):
    ob.keyframe_insert(data_path=path, frame=frame)


class MAJIMERU_OT_pop_dir(Operator):
    bl_idname = "majimeru_pop.dir"
    bl_label = "方向"
    bl_options = {"REGISTER", "UNDO"}
    offset: bpy.props.FloatVectorProperty(size=3)

    def execute(self, context):
        context.scene.pop_offset = self.offset
        return {"FINISHED"}


class MAJIMERU_OT_pop_set(Operator):
    bl_idname = "majimeru_pop.set"
    bl_label = "ポップを設定"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        ob = context.active_object
        if ob is None:
            self.report({"ERROR"}, "動物を選んで")
            return {"CANCELLED"}
        shown = ob.location.copy()
        off = sc.pop_offset
        hidden = shown - Vector(off)
        f_out = sc.pop_frame
        f_in = sc.pop_hide_frame
        move = max(1, sc.pop_move_frames)
        f_start = f_out - move
        # visibility: hidden until the pop starts, visible while out, hidden after back
        ob.hide_viewport = True
        ob.hide_render = True
        _key(ob, "hide_viewport", f_start - 1)
        _key(ob, "hide_render", f_start - 1)
        ob.hide_viewport = False
        ob.hide_render = False
        _key(ob, "hide_viewport", f_start)
        _key(ob, "hide_render", f_start)
        # movement: hidden spot -> shown spot -> hidden spot
        ob.location = hidden
        _key(ob, "location", f_start)
        ob.location = shown
        _key(ob, "location", f_out)
        ob.location = hidden
        _key(ob, "location", f_in)
        ob.hide_viewport = True
        ob.hide_render = True
        _key(ob, "hide_viewport", f_in + 1)
        _key(ob, "hide_render", f_in + 1)
        ob.hide_viewport = False
        ob.hide_render = False
        ob.location = shown
        if ob.animation_data and ob.animation_data.action:
            for fc in action_fcurves(ob.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "BACK"
        self.report({"INFO"}, "%d で出て %d で戻るよ" % (f_out, f_in))
        return {"FINISHED"}


class MAJIMERU_OT_pop_clear(Operator):
    bl_idname = "majimeru_pop.clear"
    bl_label = "ポップを消す"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ob = context.active_object
        if ob is None or ob.animation_data is None or ob.animation_data.action is None:
            self.report({"ERROR"}, "選んだ物にキーが無い")
            return {"CANCELLED"}
        action = ob.animation_data.action
        for cb in action_channelbags(action):
            for fc in list(cb.fcurves):
                if fc.data_path in ("location", "hide_viewport", "hide_render"):
                    cb.fcurves.remove(fc)
        ob.hide_viewport = False
        ob.hide_render = False
        self.report({"INFO"}, "ポップのキーを消した")
        return {"FINISHED"}


class MAJIMERU_PT_pop(Panel):
    bl_idname = "MAJIMERU_PT_pop"
    bl_label = "動物ポップ"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        box = layout.box()
        box.label(text="使い方", icon="INFO")
        box.label(text="1. 動物を「出る場所」に置く")
        box.label(text="2. 隠れる方向と距離を決める")
        box.label(text="3. ボタンを押すだけ")
        box = layout.box()
        box.label(text="隠れる方向（出る時は逆向き）", icon="ORIENTATION_GLOBAL")
        row = box.row(align=True)
        op = row.operator("majimeru_pop.dir", text="左から")
        op.offset = (-2.0, 0.0, 0.0)
        op = row.operator("majimeru_pop.dir", text="右から")
        op.offset = (2.0, 0.0, 0.0)
        row = box.row(align=True)
        op = row.operator("majimeru_pop.dir", text="地面から")
        op.offset = (0.0, 0.0, -1.5)
        op = row.operator("majimeru_pop.dir", text="上から")
        op.offset = (0.0, 0.0, 2.0)
        box.prop(sc, "pop_offset", text="隠れる量 (X,Y,Z)")
        box = layout.box()
        box.label(text="タイミング", icon="TIME")
        box.prop(sc, "pop_frame", text="出るフレーム")
        box.prop(sc, "pop_hide_frame", text="戻るフレーム")
        box.prop(sc, "pop_move_frames", text="出るのに使うフレーム数")
        big = box.row()
        big.scale_y = 1.5
        big.operator("majimeru_pop.set", text="ポップを設定", icon="HIDE_OFF")
        box.operator("majimeru_pop.clear", text="ポップを消す", icon="TRASH")


classes = (
    MAJIMERU_OT_pop_dir,
    MAJIMERU_OT_pop_set,
    MAJIMERU_OT_pop_clear,
    MAJIMERU_PT_pop,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    sc = bpy.types.Scene
    sc.pop_frame = IntProperty(name="Out", default=48, min=1)
    sc.pop_hide_frame = IntProperty(name="Back", default=96, min=2)
    sc.pop_move_frames = IntProperty(name="Move", default=6, min=1, max=60)
    sc.pop_offset = FloatVectorProperty(name="Offset", size=3, default=(-2.0, 0.0, 0.0))


def unregister():
    sc = bpy.types.Scene
    for name in ("pop_frame", "pop_hide_frame", "pop_move_frames", "pop_offset"):
        if hasattr(sc, name):
            delattr(sc, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

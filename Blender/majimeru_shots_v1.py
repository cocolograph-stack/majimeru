# ============================================================
# __  __    _      _ ___ __  __ _____ ____  _   _
# |  \/  |  / \    | |_ _|  \/  | ____|  _ \| | | |
# | |\/| | / _ \ _ | || || |\/| |  _| | |_) | | | |
# | |  | |/ ___ \| || || || |  | | |___|  _ <| |_| |
# |_|  |_/_/   \_\\___/|___|_|  |_|_____|_| \\_\\___/
#
# Author: majimeru + tobiuo-pyonpyon
# Tool: majimeru_shots  v1
# What    : Blender tool: shot (cut) list for a short film. Each shot keeps
#           its camera and frame range; switch shots with one click and
#           render all shots in a row, one file set per shot.
# YouTube: https://www.youtube.com/@3DCGいろいろ
# License: GPL-3.0
# ============================================================
import bpy
import os
from bpy.props import (
    IntProperty, StringProperty, PointerProperty, CollectionProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, UIList

bl_info = {
    "name": "Majimeru Shots",
    "author": "majimeru + tobiuo-pyonpyon",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar (N) > Majimeru",
    "description": "Shot (cut) list: per-shot camera and frame range, switch and render all",
    "category": "Render",
}


class MajimeruShot(PropertyGroup):
    shot_name: StringProperty(name="カット名", default="C01")
    camera: PointerProperty(name="カメラ", type=bpy.types.Object)
    frame_start: IntProperty(name="開始", default=1)
    frame_end: IntProperty(name="終了", default=24)
    memo: StringProperty(name="メモ", default="")


class MAJIMERU_OT_shot_add(Operator):
    bl_idname = "majimeru_shots.add"
    bl_label = "今の設定でカットを追加"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        shot = sc.majimeru_shots.add()
        shot.shot_name = "C%02d" % len(sc.majimeru_shots)
        shot.camera = sc.camera
        shot.frame_start = sc.frame_start
        shot.frame_end = sc.frame_end
        sc.majimeru_shot_index = len(sc.majimeru_shots) - 1
        return {"FINISHED"}


class MAJIMERU_OT_shot_remove(Operator):
    bl_idname = "majimeru_shots.remove"
    bl_label = "選んだカットを消す"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        idx = sc.majimeru_shot_index
        if 0 <= idx < len(sc.majimeru_shots):
            sc.majimeru_shots.remove(idx)
            sc.majimeru_shot_index = max(0, idx - 1)
        return {"FINISHED"}


class MAJIMERU_OT_shot_apply(Operator):
    bl_idname = "majimeru_shots.apply"
    bl_label = "このカットに切り替え"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        sc = context.scene
        idx = sc.majimeru_shot_index
        if not (0 <= idx < len(sc.majimeru_shots)):
            self.report({"ERROR"}, "カットが選ばれてへん")
            return {"CANCELLED"}
        shot = sc.majimeru_shots[idx]
        if shot.camera:
            sc.camera = shot.camera
        sc.frame_start = shot.frame_start
        sc.frame_end = shot.frame_end
        sc.frame_set(shot.frame_start)
        self.report({"INFO"}, "カット %s に切り替えた" % shot.shot_name)
        return {"FINISHED"}


class MAJIMERU_OT_shots_render_all(Operator):
    bl_idname = "majimeru_shots.render_all"
    bl_label = "全カットを連続レンダー"
    bl_options = {"REGISTER"}

    def execute(self, context):
        sc = context.scene
        if not sc.majimeru_shots:
            self.report({"ERROR"}, "カットが無い")
            return {"CANCELLED"}
        base = bpy.path.abspath(sc.render.filepath)
        base_dir = os.path.dirname(base)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        orig_cam, orig_s, orig_e = sc.camera, sc.frame_start, sc.frame_end
        done = 0
        for shot in sc.majimeru_shots:
            if shot.camera:
                sc.camera = shot.camera
            sc.frame_start = shot.frame_start
            sc.frame_end = shot.frame_end
            sc.render.filepath = os.path.join(base_dir, shot.shot_name + "_")
            try:
                bpy.ops.render.render(animation=True)
                done += 1
            except Exception as e:
                self.report({"WARNING"}, "%s 失敗: %s" % (shot.shot_name, e))
        sc.camera, sc.frame_start, sc.frame_end = orig_cam, orig_s, orig_e
        sc.render.filepath = base
        self.report({"INFO"}, "連続レンダー終わり: %d カット" % done)
        return {"FINISHED"}


class MAJIMERU_UL_shots(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.shot_name, icon="CAMERA_DATA")
        if item.camera:
            layout.label(text=item.camera.name)
        layout.label(text="%d-%d" % (item.frame_start, item.frame_end))


class MAJIMERU_PT_shots(Panel):
    bl_idname = "MAJIMERU_PT_shots"
    bl_label = "カット管理"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        sc = context.scene
        box = layout.box()
        box.label(text="カット一覧", icon="SEQUENCE")
        row = box.row()
        row.template_list("MAJIMERU_UL_shots", "", sc, "majimeru_shots", sc, "majimeru_shot_index", rows=4)
        col = row.column(align=True)
        col.operator("majimeru_shots.add", text="", icon="ADD")
        col.operator("majimeru_shots.remove", text="", icon="REMOVE")
        idx = sc.majimeru_shot_index
        if 0 <= idx < len(sc.majimeru_shots):
            shot = sc.majimeru_shots[idx]
            box.prop(shot, "shot_name", text="名前")
            box.prop(shot, "camera", text="カメラ")
            r = box.row(align=True)
            r.prop(shot, "frame_start", text="開始")
            r.prop(shot, "frame_end", text="終了")
            box.prop(shot, "memo", text="メモ")
        big = box.row()
        big.scale_y = 1.5
        big.operator("majimeru_shots.apply", text="このカットに切り替え", icon="CAMERA_DATA")
        box = layout.box()
        box.label(text="レンダー", icon="RENDER_ANIMATION")
        box.prop(sc.render, "filepath", text="保存先")
        box.label(text="カット名で分けて保存されるよ")
        big = box.row()
        big.scale_y = 1.5
        big.operator("majimeru_shots.render_all", text="全カットを連続レンダー", icon="RENDER_ANIMATION")
        box.label(text="レンダー中は画面が止まるよ")


classes = (
    MajimeruShot,
    MAJIMERU_OT_shot_add,
    MAJIMERU_OT_shot_remove,
    MAJIMERU_OT_shot_apply,
    MAJIMERU_OT_shots_render_all,
    MAJIMERU_UL_shots,
    MAJIMERU_PT_shots,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.majimeru_shots = CollectionProperty(type=MajimeruShot)
    bpy.types.Scene.majimeru_shot_index = IntProperty(default=0)


def unregister():
    del bpy.types.Scene.majimeru_shots
    del bpy.types.Scene.majimeru_shot_index
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

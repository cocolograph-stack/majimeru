# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_render_simple_blender  v1
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Blender tool: simple render settings in one panel
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

bl_info = {
    "name": "Majimeru Render Simple",
    "description": "Simple render settings in one panel (Blender version of the Maya tool)",
    "author": "majimeru + tobiuo pyonpyon",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "category": "Render",
    "location": "3D View > Sidebar (N) > Majimeru",
}

import bpy


class MAJIMERU_OT_res_preset(bpy.types.Operator):
    bl_idname = "majimeru.res_preset"
    bl_label = "大きさプリセット"
    bl_description = "解像度をこの大きさにする"
    bl_options = {"REGISTER", "UNDO"}

    width: bpy.props.IntProperty(default=1280, options={"HIDDEN"})
    height: bpy.props.IntProperty(default=720, options={"HIDDEN"})

    def execute(self, context):
        render = context.scene.render
        render.resolution_x = self.width
        render.resolution_y = self.height
        render.resolution_percentage = 100
        self.report({"INFO"}, f"大きさ {self.width} x {self.height} にしたよ")
        return {"FINISHED"}


class MAJIMERU_PT_render_simple(bpy.types.Panel):
    bl_idname = "MAJIMERU_PT_render_simple"
    bl_label = "簡易レンダー設定"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        render = scene.render

        box = layout.box()
        box.label(text="レンダラーとカメラ", icon="RENDER_ANIMATION")
        box.prop(render, "engine", text="レンダラー")
        box.prop(scene, "camera", text="カメラ")
        if render.engine == "CYCLES":
            box.prop(scene.cycles, "samples", text="画質（サンプル数）")
            box.prop(scene.cycles, "use_denoising", text="ノイズを消す")
        elif render.engine in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"}:
            box.prop(scene.eevee, "taa_render_samples", text="画質（サンプル数）")
        box.prop(render, "use_motion_blur", text="モーションブラー")
        box.prop(render, "film_transparent", text="背景を透明にする")

        box = layout.box()
        box.label(text="大きさ", icon="IMAGE_DATA")
        row = box.row(align=True)
        for w, h, label in (
            (1280, 720, "1280×720"),
            (1920, 1080, "1920×1080"),
            (3840, 2160, "4K"),
            (1024, 1024, "1024□"),
        ):
            op = row.operator("majimeru.res_preset", text=label)
            op.width = w
            op.height = h
        col = box.column(align=True)
        col.prop(render, "resolution_x", text="横")
        col.prop(render, "resolution_y", text="縦")
        col.prop(render, "resolution_percentage", text="％")

        box = layout.box()
        box.label(text="フレーム", icon="FRAME")
        col = box.column(align=True)
        col.prop(scene, "frame_start", text="開始")
        col.prop(scene, "frame_end", text="終了")
        col.prop(scene, "frame_step", text="何フレームおき")
        col.prop(render, "fps", text="FPS")

        box = layout.box()
        box.label(text="出力", icon="EXPORT")
        box.prop(render, "filepath", text="保存先")
        box.prop(render.image_settings, "file_format", text="形式")
        if render.image_settings.file_format == "FFMPEG":
            box.prop(render.ffmpeg, "format", text="動画の形式")
        box.label(text="連番（0001など）は自動で付くよ")

        layout.separator()
        op = layout.operator("render.render", text="今の1枚をレンダー", icon="RENDER_STILL")
        op.write_still = True
        op = layout.operator("render.render", text="アニメーションをレンダー", icon="RENDER_ANIMATION")
        op.animation = True


classes = (
    MAJIMERU_OT_res_preset,
    MAJIMERU_PT_render_simple,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

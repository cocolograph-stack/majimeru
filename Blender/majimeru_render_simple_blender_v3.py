# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_render_simple_blender  v3
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Blender tool: simple render settings (output + render buttons on top) + sequential multi-file render
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

bl_info = {
    "name": "Majimeru Render Simple",
    "description": "Simple render settings in one panel + sequential multi-file rendering",
    "author": "majimeru + tobiuo pyonpyon",
    "version": (3, 0, 0),
    "blender": (4, 2, 0),
    "category": "Render",
    "location": "3D View > Sidebar (N) > Majimeru",
}

import json
import os
import subprocess
import tempfile

import bpy
from bpy.props import CollectionProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList


# ---------------------------------------------------------------- settings

def collect_settings(context):
    scene = context.scene
    render = scene.render
    return {
        "engine": render.engine,
        "camera_name": scene.camera.name if scene.camera else "",
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_step": scene.frame_step,
        "fps": render.fps,
        "filepath": render.filepath,
        "file_format": render.image_settings.file_format,
        "ffmpeg_format": render.ffmpeg.format,
        "cycles_samples": scene.cycles.samples if hasattr(scene, "cycles") else 128,
        "cycles_denoising": scene.cycles.use_denoising if hasattr(scene, "cycles") else True,
        "eevee_samples": scene.eevee.taa_render_samples if hasattr(scene, "eevee") else 64,
        "use_motion_blur": render.use_motion_blur,
        "film_transparent": render.film_transparent,
        "mode": scene.majimeru_seq_mode,
    }


CHILD_SCRIPT = r'''
import bpy, json, os, sys

argv = sys.argv[sys.argv.index("--") + 1:]
with open(argv[0], encoding="utf-8") as f:
    cfg = json.load(f)

scene = bpy.context.scene
render = scene.render
render.engine = cfg["engine"]
if cfg["camera_name"] and cfg["camera_name"] in bpy.data.objects:
    scene.camera = bpy.data.objects[cfg["camera_name"]]
render.resolution_x = cfg["resolution_x"]
render.resolution_y = cfg["resolution_y"]
render.resolution_percentage = cfg["resolution_percentage"]
scene.frame_start = cfg["frame_start"]
scene.frame_end = cfg["frame_end"]
scene.frame_step = cfg["frame_step"]
render.fps = cfg["fps"]
render.image_settings.file_format = cfg["file_format"]
if cfg["file_format"] == "FFMPEG":
    render.ffmpeg.format = cfg["ffmpeg_format"]
if hasattr(scene, "cycles"):
    scene.cycles.samples = cfg["cycles_samples"]
    scene.cycles.use_denoising = cfg["cycles_denoising"]
if hasattr(scene, "eevee"):
    scene.eevee.taa_render_samples = cfg["eevee_samples"]
render.use_motion_blur = cfg["use_motion_blur"]
render.film_transparent = cfg["film_transparent"]

stem = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
out_base = bpy.path.abspath(cfg["filepath"])
if out_base and not out_base.endswith(os.sep) and "." not in os.path.basename(out_base):
    out_dir = out_base
    out_name = stem + "_"
elif out_base:
    out_dir = os.path.dirname(out_base)
    out_name = stem + "_" + os.path.splitext(os.path.basename(out_base))[0] + "_"
else:
    out_dir = os.path.dirname(bpy.data.filepath)
    out_name = stem + "_"
os.makedirs(out_dir, exist_ok=True)
render.filepath = os.path.join(out_dir, out_name)

if cfg["mode"] == "STILL":
    scene.frame_set(cfg["frame_start"])
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("MAJIMERU_SEQ_DONE", render.filepath)
'''


# ---------------------------------------------------------------- operators

class MAJIMERU_OT_res_preset(Operator):
    bl_idname = "majimeru.res_preset"
    bl_label = "大きさプリセット"
    bl_description = "解像度をこの大きさにする"
    bl_options = {"REGISTER", "UNDO"}

    width: IntProperty(default=1280, options={"HIDDEN"})
    height: IntProperty(default=720, options={"HIDDEN"})

    def execute(self, context):
        render = context.scene.render
        render.resolution_x = self.width
        render.resolution_y = self.height
        render.resolution_percentage = 100
        self.report({"INFO"}, f"大きさ {self.width} x {self.height} にしたよ")
        return {"FINISHED"}


class MAJIMERU_FileItem(PropertyGroup):
    filepath: StringProperty(name="ファイル", subtype="FILE_PATH")


class MAJIMERU_UL_files(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.filepath or "(未設定)", icon="FILE_BLEND")


class MAJIMERU_OT_file_add(Operator):
    bl_idname = "majimeru.file_add"
    bl_label = "ファイルを追加"
    bl_description = "連続レンダーする .blend ファイルを追加する"

    filepath: StringProperty(subtype="FILE_PATH", options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}
        item = context.scene.majimeru_files.add()
        item.filepath = self.filepath
        context.scene.majimeru_files_index = len(context.scene.majimeru_files) - 1
        return {"FINISHED"}


class MAJIMERU_OT_file_remove(Operator):
    bl_idname = "majimeru.file_remove"
    bl_label = "選んだファイルを外す"
    bl_description = "リストで選んでいるファイルを外す"

    def execute(self, context):
        scene = context.scene
        idx = scene.majimeru_files_index
        if 0 <= idx < len(scene.majimeru_files):
            scene.majimeru_files.remove(idx)
            scene.majimeru_files_index = max(0, idx - 1)
        return {"FINISHED"}


class MAJIMERU_OT_file_clear(Operator):
    bl_idname = "majimeru.file_clear"
    bl_label = "リストを空にする"
    bl_description = "連続レンダーのリストを全部外す"

    def execute(self, context):
        context.scene.majimeru_files.clear()
        context.scene.majimeru_files_index = 0
        return {"FINISHED"}


class MAJIMERU_OT_render_sequence(Operator):
    bl_idname = "majimeru.render_sequence"
    bl_label = "連続レンダーを開始"
    bl_description = "リストの .blend ファイルを、このパネルの設定で1個ずつ順番にレンダーする"

    def execute(self, context):
        scene = context.scene
        files = [item.filepath for item in scene.majimeru_files if item.filepath]
        if not files:
            self.report({"ERROR"}, "リストにファイルが無いよ")
            return {"CANCELLED"}

        cfg = collect_settings(context)
        tmpdir = tempfile.mkdtemp(prefix="majimeru_seq_")
        cfg_path = os.path.join(tmpdir, "settings.json")
        script_path = os.path.join(tmpdir, "child_render.py")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(CHILD_SCRIPT)

        blender_bin = bpy.app.binary_path
        done, failed = 0, []
        for path in files:
            full = bpy.path.abspath(path)
            if not os.path.exists(full):
                failed.append(path)
                continue
            print(f"[Majimeru] rendering: {full}")
            try:
                result = subprocess.run(
                    [blender_bin, "-b", full, "--python", script_path, "--", cfg_path],
                    capture_output=True, text=True, timeout=7200,
                )
                if "MAJIMERU_SEQ_DONE" in (result.stdout or ""):
                    done += 1
                else:
                    failed.append(path)
                    print(result.stdout[-2000:] if result.stdout else "")
                    print(result.stderr[-2000:] if result.stderr else "")
            except Exception as e:
                failed.append(path)
                print(f"[Majimeru] error: {e}")

        if failed:
            self.report({"WARNING"}, f"{done} 個できた。失敗: {len(failed)} 個（コンソールを見て）")
        else:
            self.report({"INFO"}, f"全部できたよ: {done} 個のファイル")
        return {"FINISHED"}


# ---------------------------------------------------------------- panel

class MAJIMERU_PT_render_simple(Panel):
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
        box.label(text="保存場所とレンダー実行", icon="RENDER_STILL")
        box.prop(render, "filepath", text="保存先")
        box.prop(render.image_settings, "file_format", text="形式")
        if render.image_settings.file_format == "FFMPEG":
            box.prop(render.ffmpeg, "format", text="動画の形式")
        box.label(text="連番（0001など）は自動で付くよ")
        big = box.row()
        big.scale_y = 1.5
        op = big.operator("render.render", text="今の1枚をレンダー", icon="RENDER_STILL")
        op.write_still = True
        big2 = box.row()
        big2.scale_y = 1.5
        op = big2.operator("render.render", text="アニメーションをレンダー", icon="RENDER_ANIMATION")
        op.animation = True

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
        box.label(text="連続レンダー（複数の .blend）", icon="FILE_BLEND")
        box.template_list("MAJIMERU_UL_files", "", scene, "majimeru_files",
                          scene, "majimeru_files_index", rows=3)
        row = box.row(align=True)
        row.operator("majimeru.file_add", text="追加", icon="ADD")
        row.operator("majimeru.file_remove", text="外す", icon="REMOVE")
        row.operator("majimeru.file_clear", text="空に", icon="TRASH")
        box.prop(scene, "majimeru_seq_mode", text="種類", expand=True)
        box.label(text="上のパネルの設定で、順番に描くよ")
        box.label(text="終わるまで Blender は固まる。長めの時は注意")
        box.operator("majimeru.render_sequence", text="連続レンダーを開始", icon="PLAY")


classes = (
    MAJIMERU_OT_res_preset,
    MAJIMERU_FileItem,
    MAJIMERU_UL_files,
    MAJIMERU_OT_file_add,
    MAJIMERU_OT_file_remove,
    MAJIMERU_OT_file_clear,
    MAJIMERU_OT_render_sequence,
    MAJIMERU_PT_render_simple,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.majimeru_files = CollectionProperty(type=MAJIMERU_FileItem)
    bpy.types.Scene.majimeru_files_index = IntProperty(default=0)
    bpy.types.Scene.majimeru_seq_mode = EnumProperty(
        name="種類",
        items=(
            ("ANIMATION", "アニメーション", "フレーム範囲を全部描く"),
            ("STILL", "1枚だけ", "開始フレームの1枚だけ描く"),
        ),
        default="ANIMATION",
    )


def unregister():
    del bpy.types.Scene.majimeru_files
    del bpy.types.Scene.majimeru_files_index
    del bpy.types.Scene.majimeru_seq_mode
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

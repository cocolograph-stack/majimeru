# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_project  v5
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Blender tool: Maya-style project folders; compact panel, main buttons on top; auto-finds project (Mac/Windows friendly); incremental save (_v001, _v002, ...)
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

bl_info = {
    "name": "Majimeru Project",
    "description": "Maya-style project system for Blender: project folders, set project, save scene into project",
    "author": "majimeru + tobiuo pyonpyon",
    "version": (5, 0, 0),
    "blender": (4, 2, 0),
    "category": "Scene",
    "location": "3D View > Sidebar (N) > Majimeru",
}

import json
import os
import re

import bpy
from bpy.props import StringProperty
from bpy.types import Operator, Panel

SUBFOLDERS = ("scenes", "textures", "models", "assets", "renders", "cache", "exports")
MARKER = "majimeru_project.json"


# ---------------------------------------------------------------- storage

def config_path():
    cfg_dir = bpy.utils.user_resource("CONFIG")
    return os.path.join(cfg_dir, "majimeru_project.json")


def get_current_project():
    try:
        with open(config_path(), encoding="utf-8") as f:
            path = json.load(f).get("current", "")
        if path and os.path.isdir(path):
            return path
    except Exception:
        pass
    return ""


def set_current_project(path):
    try:
        os.makedirs(os.path.dirname(config_path()), exist_ok=True)
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump({"current": path}, f)
    except Exception as e:
        print(f"[Majimeru Project] cannot save current project: {e}")


def make_project_folders(root):
    for sub in SUBFOLDERS:
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    marker = os.path.join(root, MARKER)
    if not os.path.exists(marker):
        with open(marker, "w", encoding="utf-8") as f:
            json.dump({"name": os.path.basename(root), "tool": "majimeru_project v1"}, f)


def find_project_root(start_dir):
    """Walk up from start_dir looking for the project marker file.
    This is what makes a project work across Mac and Windows: the folder
    is found from the opened file's location, not from a saved path."""
    d = os.path.abspath(start_dir)
    for _ in range(9):
        if os.path.exists(os.path.join(d, MARKER)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return ""


# ---------------------------------------------------------------- operators

class MAJIMERU_OT_project_create(Operator):
    bl_idname = "majimeru.project_create"
    bl_label = "プロジェクトを作る"
    bl_description = "選んだフォルダに、プロジェクトのフォルダ一式を作って、それを今のプロジェクトにする"

    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        root = bpy.path.abspath(self.directory)
        if not root:
            self.report({"ERROR"}, "フォルダを選んでね")
            return {"CANCELLED"}
        os.makedirs(root, exist_ok=True)
        make_project_folders(root)
        set_current_project(root)
        context.scene.majimeru_project_root = root
        self.report({"INFO"}, f"プロジェクト作ったよ: {root}")
        return {"FINISHED"}


class MAJIMERU_OT_project_set(Operator):
    bl_idname = "majimeru.project_set"
    bl_label = "プロジェクトを設定"
    bl_description = "既にあるプロジェクトフォルダを、今のプロジェクトにする（Maya の Set Project）"

    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        root = bpy.path.abspath(self.directory)
        if not root or not os.path.isdir(root):
            self.report({"ERROR"}, "フォルダが見つからへん")
            return {"CANCELLED"}
        make_project_folders(root)
        set_current_project(root)
        context.scene.majimeru_project_root = root
        self.report({"INFO"}, f"プロジェクト設定したよ: {root}")
        return {"FINISHED"}


class MAJIMERU_OT_project_save_scene(Operator):
    bl_idname = "majimeru.project_save_scene"
    bl_label = "シーンをプロジェクトに保存"
    bl_description = "今のシーンを、プロジェクトの scenes フォルダに保存する"
    bl_options = {"REGISTER"}

    def execute(self, context):
        root = get_current_project()
        if not root:
            self.report({"ERROR"}, "先にプロジェクトを作るか設定してね")
            return {"CANCELLED"}
        name = context.scene.majimeru_scene_name.strip() or "scene_01"
        if not name.endswith(".blend"):
            name += ".blend"
        path = os.path.join(root, "scenes", name)
        bpy.ops.wm.save_as_mainfile(filepath=path)
        context.scene.majimeru_project_root = root
        bpy.ops.wm.save_as_mainfile(filepath=path)
        try:
            bpy.ops.file.make_paths_relative()
        except Exception:
            pass
        self.report({"INFO"}, f"保存したよ: {path}")
        return {"FINISHED"}


class MAJIMERU_OT_project_save_incremental(Operator):
    bl_idname = "majimeru.project_save_incremental"
    bl_label = "番号を増やして保存"
    bl_description = "scenes フォルダに _v001, _v002 と番号を増やして保存する（上書きされへん、Maya のインクリメンタルセーブ式）"
    bl_options = {"REGISTER"}

    def execute(self, context):
        root = get_current_project()
        if not root:
            self.report({"ERROR"}, "先にプロジェクトを作るか設定してね")
            return {"CANCELLED"}
        raw = context.scene.majimeru_scene_name.strip() or "scene_01"
        if raw.endswith(".blend"):
            raw = raw[: -len(".blend")]
        base = re.sub(r"_v\d+$", "", raw)
        scenes_dir = os.path.join(root, "scenes")
        os.makedirs(scenes_dir, exist_ok=True)
        pat = re.compile(r"^" + re.escape(base) + r"_v(\d+)\.blend$")
        highest = 0
        for fname in os.listdir(scenes_dir):
            m = pat.match(fname)
            if m:
                highest = max(highest, int(m.group(1)))
        new_name = f"{base}_v{highest + 1:03d}"
        path = os.path.join(scenes_dir, new_name + ".blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        context.scene.majimeru_project_root = root
        bpy.ops.wm.save_as_mainfile(filepath=path)
        context.scene.majimeru_scene_name = new_name
        try:
            bpy.ops.file.make_paths_relative()
        except Exception:
            pass
        self.report({"INFO"}, f"保存したよ: {path}")
        return {"FINISHED"}


class MAJIMERU_OT_project_render_output(Operator):
    bl_idname = "majimeru.project_render_output"
    bl_label = "出力先をプロジェクトにする"
    bl_description = "レンダーの保存先を、プロジェクトの renders フォルダにする"

    def execute(self, context):
        root = get_current_project()
        if not root:
            self.report({"ERROR"}, "先にプロジェクトを作るか設定してね")
            return {"CANCELLED"}
        context.scene.render.filepath = os.path.join(root, "renders", "render_")
        self.report({"INFO"}, "出力先を renders フォルダにしたよ")
        return {"FINISHED"}


class MAJIMERU_OT_project_make_relative(Operator):
    bl_idname = "majimeru.project_make_relative"
    bl_label = "パスを相対にする"
    bl_description = "テクスチャなどのパスを、このファイルからの相対パスにする（フォルダごと移しても切れへん）"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, "先にファイルを保存してね")
            return {"CANCELLED"}
        try:
            bpy.ops.file.make_paths_relative()
            self.report({"INFO"}, "パスを相対にしたよ")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"できへんかった: {e}")
            return {"CANCELLED"}


class MAJIMERU_OT_project_open(Operator):
    bl_idname = "majimeru.project_open"
    bl_label = "フォルダを開く"
    bl_description = "プロジェクトのフォルダをファイルブラウザで開く"

    sub: StringProperty(default="", options={"HIDDEN"})

    def execute(self, context):
        root = get_current_project()
        if not root:
            self.report({"ERROR"}, "プロジェクトが未設定やで")
            return {"CANCELLED"}
        path = os.path.join(root, self.sub) if self.sub else root
        try:
            bpy.ops.wm.path_open(filepath=path)
        except Exception as e:
            self.report({"ERROR"}, f"開けへんかった: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


# ---------------------------------------------------------------- handler

@bpy.app.handlers.persistent
def on_load(_dummy):
    scene = bpy.context.scene
    if scene is None:
        return
    root = getattr(scene, "majimeru_project_root", "")
    if root and os.path.isdir(root):
        set_current_project(root)
        return
    # The saved path may be written in another OS's style (Mac vs Windows).
    # In that case, find the project from the opened file's own location.
    fp = bpy.data.filepath
    if fp:
        found = find_project_root(os.path.dirname(bpy.path.abspath(fp)))
        if found:
            set_current_project(found)
            scene.majimeru_project_root = found


# ---------------------------------------------------------------- panel

class MAJIMERU_PT_project(Panel):
    bl_idname = "MAJIMERU_PT_project"
    bl_label = "プロジェクト"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        root = get_current_project()

        box = layout.box()
        box.label(text="今のプロジェクト", icon="FILE_FOLDER")
        if root:
            box.label(text=os.path.basename(root))
            box.label(text=root)
        else:
            box.label(text="まだ設定されてへん")

        big = layout.row()
        big.scale_y = 1.5
        big.operator("majimeru.project_create", text="プロジェクトを作る", icon="NEWFOLDER_HLT")
        big2 = layout.row()
        big2.scale_y = 1.5
        big2.operator("majimeru.project_set", text="プロジェクトを設定（Set Project）", icon="FILE_FOLDER")

        box = layout.box()
        box.label(text="シーンの保存", icon="FILE_BLEND")
        box.prop(scene, "majimeru_scene_name", text="シーン名")
        inc = box.row()
        inc.scale_y = 1.4
        inc.operator("majimeru.project_save_incremental", text="番号を増やして保存", icon="FILE_TICK")
        box.operator("majimeru.project_save_scene", text="同じ名前で保存（上書き）", icon="FILE_BLEND")
        box.label(text="番号付きは _v001, _v002 と増えて上書きされへん")
        box.label(text="ファイルを開くと、周りから自動で探すよ")


class MAJIMERU_PT_project_more(Panel):
    bl_idname = "MAJIMERU_PT_project_more"
    bl_label = "その他（出力・パス・フォルダ）"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"
    bl_parent_id = "MAJIMERU_PT_project"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="出力とパス", icon="EXPORT")
        box.operator("majimeru.project_render_output", text="出力先をプロジェクトにする", icon="RENDER_ANIMATION")
        box.operator("majimeru.project_make_relative", text="パスを相対にする", icon="FILE_REFRESH")

        box = layout.box()
        box.label(text="フォルダを開く", icon="FILE_FOLDER")
        row = box.row(align=True)
        for sub, label in (("", "全体"), ("scenes", "scenes"), ("textures", "textures")):
            op = row.operator("majimeru.project_open", text=label)
            op.sub = sub
        row = box.row(align=True)
        for sub, label in (("models", "models"), ("assets", "assets"), ("renders", "renders")):
            op = row.operator("majimeru.project_open", text=label)
            op.sub = sub
        box.label(text="中身: scenes / textures / models /")
        box.label(text="assets / renders / cache / exports")


classes = (
    MAJIMERU_OT_project_create,
    MAJIMERU_OT_project_set,
    MAJIMERU_OT_project_save_scene,
    MAJIMERU_OT_project_save_incremental,
    MAJIMERU_OT_project_render_output,
    MAJIMERU_OT_project_make_relative,
    MAJIMERU_OT_project_open,
    MAJIMERU_PT_project,
    MAJIMERU_PT_project_more,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.majimeru_project_root = StringProperty(
        name="プロジェクト", subtype="DIR_PATH", default=""
    )
    bpy.types.Scene.majimeru_scene_name = StringProperty(
        name="シーン名", default="scene_01"
    )
    if on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_load)


def unregister():
    if on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_load)
    del bpy.types.Scene.majimeru_project_root
    del bpy.types.Scene.majimeru_scene_name
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

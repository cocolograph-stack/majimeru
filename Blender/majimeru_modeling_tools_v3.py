# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_modeling_tools  v3
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Blender tool: modeling essentials (extrude, cut, connect, merge, join, separate, mirror)
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

bl_info = {
    "name": "Majimeru Modeling Tools",
    "description": "Modeling helper buttons in one panel, plain words, Maya-user friendly",
    "author": "majimeru + tobiuo pyonpyon",
    "version": (3, 0, 0),
    "blender": (4, 2, 0),
    "category": "Mesh",
    "location": "3D View > Sidebar (N) > Majimeru",
}

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, Panel


class MAJIMERU_OT_select_mode(Operator):
    bl_idname = "majimeru.select_mode"
    bl_label = "選択モード切替"
    bl_description = "頂点 / 辺 / 面 の選択モードを切り替える"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(
        items=(
            ("VERT", "頂点", ""),
            ("EDGE", "辺", ""),
            ("FACE", "面", ""),
        ),
        options={"HIDDEN"},
    )

    def execute(self, context):
        ts = context.scene.tool_settings
        ts.mesh_select_mode = (
            self.mode == "VERT",
            self.mode == "EDGE",
            self.mode == "FACE",
        )
        return {"FINISHED"}


class MAJIMERU_OT_apply_all(Operator):
    bl_idname = "majimeru.apply_all"
    bl_label = "全部適用"
    bl_description = "場所・回転・大きさを全部適用する（Maya のフリーズ＋ヒストリ削除に近い）"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        self.report({"INFO"}, "全部適用したよ")
        return {"FINISHED"}


class MAJIMERU_OT_add_mirror(Operator):
    bl_idname = "majimeru.add_mirror"
    bl_label = "ミラーを付ける"
    bl_description = "ミラーモディファイア（X・左右）を付ける"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "メッシュを選んでね")
            return {"CANCELLED"}
        mod = obj.modifiers.new(name="MajimeruMirror", type="MIRROR")
        self.report({"INFO"}, "ミラー（X）を付けたよ")
        return {"FINISHED"}


class MAJIMERU_PT_modeling(Panel):
    bl_idname = "MAJIMERU_PT_modeling"
    bl_label = "モデリングお助け"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Majimeru"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        if obj and obj.type == "MESH":
            box = layout.box()
            box.label(text="対称で編集", icon="MOD_MIRROR")
            box.prop(obj.data, "use_mirror_x", text="左右対称（X）")
            box.prop(obj.data, "use_mirror_y", text="前後対称（Y）")
            box.prop(obj.data, "use_mirror_z", text="上下対称（Z）")

        if context.mode == "OBJECT":
            box = layout.box()
            box.label(text="原点（ピボット）", icon="PIVOT_CURSOR")
            box.operator("view3d.snap_cursor_to_selected", text="カーソルを選んだ物へ")
            op = box.operator("object.origin_set", text="原点をカーソルへ")
            op.type = "ORIGIN_CURSOR"
            op.center = "MEDIAN"
            op = box.operator("object.origin_set", text="原点を物の中心へ")
            op.type = "ORIGIN_GEOMETRY"
            op.center = "MEDIAN"

            box = layout.box()
            box.label(text="まずこれ（基本セット）", icon="STAR")
            box.operator("object.join", text="一つにする（選んだ物を結合）（Ctrl+J）")
            box.operator("majimeru.add_mirror", text="ミラーを付ける（X）", icon="MOD_MIRROR")

            box = layout.box()
            box.label(text="見た目と確定", icon="SHADING_RENDERED")
            box.operator("object.shade_smooth", text="スムーズ表示")
            box.operator("object.shade_auto_smooth", text="角度でスムーズ（おすすめ）")
            box.operator("object.shade_flat", text="フラット表示")
            box.operator("majimeru.apply_all", text="全部適用（場所・回転・大きさ）（Ctrl+A）")

        elif context.mode == "EDIT_MESH":
            box = layout.box()
            box.label(text="選択モード", icon="EDITMODE_HLT")
            row = box.row(align=True)
            for mode, label in (("VERT", "頂点（1）"), ("EDGE", "辺（2）"), ("FACE", "面（3）")):
                op = row.operator("majimeru.select_mode", text=label)
                op.mode = mode

            box = layout.box()
            box.label(text="まずこれ（基本セット）", icon="STAR")
            col = box.column(align=True)
            col.operator("mesh.extrude_region_move", text="押し出し（E）")
            op = col.operator("wm.tool_set_by_id", text="切る（ナイフ）（K）")
            op.name = "builtin.knife"
            op = col.operator("wm.tool_set_by_id", text="ループカット（ぐるっと切る）（Ctrl+R）")
            op.name = "builtin.loop_cut"
            col.operator("mesh.bridge_edge_loops", text="つなぐ（ブリッジ）")
            col.operator("mesh.vert_connect_path", text="点と点をつなぐ（J）")
            op = col.operator("mesh.separate", text="選んだ面を別の物に分ける（逆の結合）（P）")
            op.type = "SELECTED"

            box = layout.box()
            box.label(text="その次によく使う", icon="TOOL_SETTINGS")
            col = box.column(align=True)
            col.operator("mesh.inset", text="インセット（内側に面を作る）（I）")
            col.operator("mesh.bevel", text="ベベル（角を落とす）（Ctrl+B）")
            col.operator("mesh.subdivide", text="分割")

            box = layout.box()
            box.label(text="点をくっつける", icon="AUTOMERGE_OFF")
            col = box.column(align=True)
            op = col.operator("mesh.merge", text="中心にマージ（M）")
            op.type = "CENTER"
            op = col.operator("mesh.merge", text="最後の点にマージ（M）")
            op.type = "LAST"
            col.operator("mesh.remove_doubles", text="近い点をくっつける（M）")

            box = layout.box()
            box.label(text="お掃除", icon="BRUSH_DATA")
            col = box.column(align=True)
            op = col.operator("mesh.normals_make_consistent", text="法線を外向きに揃える（Shift+N）")
            op.inside = False
            col.operator("mesh.delete_loose", text="バラバラの点・辺を消す")
        else:
            layout.label(text="オブジェクトか編集モードで使ってね")


classes = (
    MAJIMERU_OT_select_mode,
    MAJIMERU_OT_apply_all,
    MAJIMERU_OT_add_mirror,
    MAJIMERU_PT_modeling,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

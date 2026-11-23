# ============================================================
# __  __    _      _ ___ __  __ _____ ____  _   _
# |  \/  |  / \    | |_ _|  \/  | ____|  _ \| | | |
# | |\/| | / _ \ _ | || || |\/| |  _| | |_) | | | |
# | |  | |/ ___ \| || || || |  | | |___|  _ <| |_| |
# |_|  |_/_/   \_\\___/|___|_|  |_|_____|_| \_\\___/
#
# Author: majimeru + とびうおぴょんぴょん
# Tool: majimeru_maya_style  v1 (addon / always-on version)
# What    : Makes Blender feel like Maya (Alt navigation, G/R/S gizmo tools,
#           D pivot, F/A frame, Q select, Ctrl+D duplicate, B proportional,
#           P parent, snap GRID+VERTEX, inverted zoom drag).
#           Addon version: applies everything automatically at every
#           Blender start and on every file load, so it never gets lost.
# YouTube: https://www.youtube.com/@3DCGいろいろ
# License: GPL-3.0
# ============================================================
import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "Majimeru Maya Style (always-on)",
    "author": "majimeru + tobiuo-pyonpyon",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Always on (no panel)",
    "description": "Maya-style navigation and keys, re-applied at every start and file load",
    "category": "Interface",
}


NAV_MAP = {
    "view3d.rotate": "LEFTMOUSE",
    "view3d.move": "MIDDLEMOUSE",
    "view3d.zoom": "RIGHTMOUSE",
    "image.view_pan": "MIDDLEMOUSE",
    "image.view_zoom": "RIGHTMOUSE",
    "view2d.pan": "MIDDLEMOUSE",
    "view2d.zoom": "RIGHTMOUSE",
    "clip.view_pan": "MIDDLEMOUSE",
    "clip.view_zoom": "RIGHTMOUSE",
}

SKIP_TYPES = {
    "WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE",
    "MOUSEPAN", "MOUSEROTATE", "MOUSEZOOM",
    "TRACKPADPAN", "TRACKPADZOOM", "MOUSESMARTZOOM",
}

GRS_MAP = {
    "G": ("transform.translate", "builtin.move"),
    "R": ("transform.rotate", "builtin.rotate"),
    "S": ("transform.resize", "builtin.scale"),
}

ANIME_WORDS = ("Graph", "Dope", "Timeline", "NLA", "Sequencer", "Action")

TOOL_TO_OP = {
    "builtin.move": "transform.translate",
    "builtin.rotate": "transform.rotate",
    "builtin.scale": "transform.resize",
}


def do_nav(kc):
    for km in kc.keymaps:
        try:
            if km.is_modal:
                continue
        except Exception:
            pass
        done = set()
        for kmi in km.keymap_items:
            if kmi.idname not in NAV_MAP or kmi.idname in done:
                continue
            if kmi.type in SKIP_TYPES:
                continue
            if kmi.type not in ("MIDDLEMOUSE", "LEFTMOUSE", "RIGHTMOUSE"):
                continue
            try:
                kmi.type = NAV_MAP[kmi.idname]
                kmi.value = "PRESS"
                kmi.alt = True
                kmi.shift = False
                kmi.ctrl = False
                kmi.oskey = False
                kmi.active = True
                done.add(kmi.idname)
                print("[NAV]", km.name, kmi.idname, "-> Alt +", kmi.type)
            except Exception as e:
                print("[NAV ERROR]", km.name, kmi.idname, e)


def do_grs_gizmo(kc):
    for km in kc.keymaps:
        try:
            if km.is_modal:
                continue
        except Exception:
            pass
        if any(w in km.name for w in ANIME_WORDS):
            continue
        for kmi in km.keymap_items:
            if kmi.type not in GRS_MAP:
                continue
            if kmi.shift or kmi.ctrl or kmi.alt or kmi.oskey:
                continue
            expected_op, tool_name = GRS_MAP[kmi.type]
            is_target = (kmi.idname == expected_op)
            if kmi.idname == "transform.transform" and kmi.type in ("R", "S"):
                is_target = True
            if not is_target:
                continue
            try:
                key = kmi.type
                kmi.idname = "wm.tool_set_by_id"
                kmi.properties.name = tool_name
                kmi.active = True
                print("[GRS]", km.name, key, "-> gizmo:", tool_name)
            except Exception as e:
                print("[GRS ERROR]", km.name, kmi.type, e)


def do_revert_anime(kc):
    for km in kc.keymaps:
        if not any(w in km.name for w in ANIME_WORDS):
            continue
        try:
            if km.is_modal:
                continue
        except Exception:
            pass
        for kmi in km.keymap_items:
            if kmi.type not in ("G", "R", "S"):
                continue
            if kmi.idname != "wm.tool_set_by_id":
                continue
            try:
                tool_name = kmi.properties.name
            except Exception:
                continue
            if tool_name not in TOOL_TO_OP:
                continue
            try:
                kmi.idname = TOOL_TO_OP[tool_name]
                kmi.active = True
                print("[ANIME MODOSU]", km.name, kmi.type, "->", kmi.idname)
            except Exception as e:
                print("[ANIME ERROR]", km.name, kmi.type, e)


def do_conflicts(kc):
    for km in kc.keymaps:
        for kmi in km.keymap_items:
            try:
                if "loop" in kmi.idname and kmi.type == "LEFTMOUSE" and kmi.alt:
                    kmi.active = False
                    print("[OFF conflict]", km.name, kmi.idname)
            except Exception:
                pass


def do_d_pivot(kc):
    km = kc.keymaps.get("3D View")
    if km is None:
        return
    found = None
    for kmi in km.keymap_items:
        if kmi.type == "D" and not (kmi.shift or kmi.ctrl or kmi.alt or kmi.oskey):
            if kmi.idname == "wm.context_toggle":
                found = kmi
                break
    if found is None:
        found = km.keymap_items.new("wm.context_toggle", "D", "PRESS")
    found.active = True
    try:
        found.properties.data_path = "scene.tool_settings.use_transform_data_origin"
        print("[D] pivot ON/OFF -> D key")
    except Exception as e:
        print("[D ERROR]", e)


def set_item(km, idname, key, shift=False, ctrl=False, alt=False, props=None):
    if km is None:
        return
    for kmi in km.keymap_items:
        if kmi.type == key and kmi.shift == shift and kmi.ctrl == ctrl and kmi.alt == alt and kmi.oskey is False:
            try:
                kmi.idname = idname
                if props:
                    for pk, pv in props.items():
                        setattr(kmi.properties, pk, pv)
                kmi.active = True
                print("[SET]", km.name, key, "->", idname)
                return
            except Exception as e:
                print("[SET ERROR]", km.name, key, e)
                return
    try:
        kmi = km.keymap_items.new(idname, key, "PRESS", shift=shift, ctrl=ctrl, alt=alt)
        if props:
            for pk, pv in props.items():
                setattr(kmi.properties, pk, pv)
        kmi.active = True
        print("[NEW]", km.name, key, "->", idname)
    except Exception as e:
        print("[NEW ERROR]", km.name, key, e)


def do_extra_maya(kc):
    km_view = kc.keymaps.get("3D View")
    km_obj = kc.keymaps.get("Object Mode")
    km_mesh = kc.keymaps.get("Mesh")
    km_uv = kc.keymaps.get("UV Editor")
    km_img = kc.keymaps.get("Image")

    # F = Frame Selected, A = Frame All (Object Mode nomi. Henshuu mode no
    # A=zenbu sentaku to F=men wo haru wa modelingu no inochizuna nanode nokosu)
    set_item(km_view, "view3d.view_selected", "F")
    set_item(km_obj, "view3d.view_selected", "F")
    set_item(km_obj, "view3d.view_all", "A")
    set_item(km_img, "image.view_selected", "F")

    # Q = Sentaku tool ni modoru (Maya no Q)
    for km in (km_obj, km_mesh, km_uv):
        set_item(km, "wm.tool_set_by_id", "Q", props={"name": "builtin.select_box"})

    # Ctrl+D = Fukusei (Maya to onaji, Shift+D mo nokosu)
    set_item(km_obj, "object.duplicate_move", "D", ctrl=True)
    set_item(km_mesh, "mesh.duplicate_move", "D", ctrl=True)

    # B = Proportional henshuu ON/OFF (Maya no soft sentaku ni chikai)
    for km in (km_obj, km_mesh):
        set_item(km, "wm.context_toggle", "B",
                 props={"data_path": "scene.tool_settings.use_proportional_editing"})

    # Oyako: P = oyako dzuke (Maya to onaji, menu nashi de sokuji,
    #         sekai no ichi wa sono mama = Keep Transform)
    #        Shift+P = hazusu (sekai no ichi wa sono mama)
    set_item(km_obj, "object.parent_set", "P",
             props={"type": "OBJECT", "keep_transform": True})
    set_item(km_obj, "object.parent_clear", "P", shift=True,
             props={"type": "CLEAR_KEEP_TRANSFORM"})



def do_snap_and_zoom():
    ts = bpy.context.scene.tool_settings
    try:
        ts.use_snap = False
    except Exception:
        pass
    for prop in ("snap_elements_base", "snap_elements"):
        try:
            setattr(ts, prop, {"GRID", "VERTEX"})
            print("[SNAP] element -> VERTEX via", prop)
            break
        except Exception:
            continue
    try:
        bpy.context.preferences.inputs.invert_mouse_zoom = True
        print("[ZOOM] invert_mouse_zoom = True")
    except Exception as e:
        print("[ZOOM ERROR]", e)


def do_show_gizmo():
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type not in ("VIEW_3D", "IMAGE_EDITOR"):
                    continue
                for space in area.spaces:
                    if hasattr(space, "show_gizmo"):
                        space.show_gizmo = True
    except Exception as e:
        print("[gizmo display]", e)



# ---------------------------------------------------------------- addon glue

def _apply_keymaps_and_prefs():
    try:
        kc = bpy.context.window_manager.keyconfigs.active
        do_nav(kc)
        do_grs_gizmo(kc)
        do_revert_anime(kc)
        do_conflicts(kc)
        do_d_pivot(kc)
        do_extra_maya(kc)
    except Exception as e:
        print("[Majimeru Maya Style] keymap apply error:", e)
    try:
        bpy.context.preferences.inputs.invert_mouse_zoom = True
    except Exception:
        pass


def _apply_scene():
    try:
        do_snap_and_zoom()
    except Exception:
        pass
    try:
        do_show_gizmo()
    except Exception:
        pass


def apply_all():
    _apply_keymaps_and_prefs()
    _apply_scene()
    try:
        bpy.ops.wm.save_userpref()
    except Exception:
        pass
    print("[Majimeru Maya Style] applied")


@persistent
def _on_load(_dummy):
    _apply_scene()


def register():
    apply_all()
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)


def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)


if __name__ == "__main__":
    register()

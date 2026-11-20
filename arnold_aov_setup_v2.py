# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : arnold_aov_setup_v2  v2
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya tool: Arnold AOV setup for After Effects compositing
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

import maya.cmds as cmds
import mtoa.aovs as aovs
import mtoa.core as core

WINDOW_NAME = "arnoldAOVSetupTool_V2_Win"

# ---- AOVグループ定義 ----
# ビューティー完全分解（volumeを含む完全版。これらを全部足すと beauty に戻る）
BEAUTY_SPLIT_AOVS = [
    "diffuse_direct", "diffuse_indirect",
    "specular_direct", "specular_indirect",
    "coat_direct", "coat_indirect",
    "transmission", "sss", "volume", "emission", "background"
]
# テクニカルパス（合成用：深度・法線・モーションベクター）
TECHNICAL_AOVS = ["Z", "N", "motionvector"]
# Cryptomatte（マスク抜き用）
CRYPTO_AOVS = ["crypto_asset", "crypto_material", "crypto_object"]
# グレード用（分解しない合算パス）
GRADE_AOVS = ["diffuse", "specular", "coat", "transmission", "sss"]

# プリセット定義
AOV_PRESETS = {
    "full": {
        "label": "フル合成セット (完全分解+テクニカル+Crypto+AO)",
        "aovs": BEAUTY_SPLIT_AOVS + TECHNICAL_AOVS + CRYPTO_AOVS,
        "crypto": True,
        "ao": True
    },
    "quick": {
        "label": "クイックチェック (beautyのみ)",
        "aovs": [],
        "crypto": False,
        "ao": False
    },
    "preview": {
        "label": "コンポ下見 (beauty + Cryptomatte + Z)",
        "aovs": CRYPTO_AOVS + ["Z"],
        "crypto": True,
        "ao": False
    },
    "grade": {
        "label": "グレード用セット (合算パス)",
        "aovs": GRADE_AOVS,
        "crypto": False,
        "ao": False
    },
    "ao_only": {
        "label": "AO (アンビエントオクルージョン) 追加",
        "aovs": [],
        "crypto": False,
        "ao": True
    }
}

def _ensure_arnold_loaded():
    if not cmds.pluginInfo("mtoa", query=True, loaded=True):
        cmds.loadPlugin("mtoa")
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    core.createOptions()

def _setup_multichannel_exr():
    """マルチチャンネルEXR出力・Merge AOVs・ZIP圧縮を強制適用"""
    if cmds.objExists("defaultArnoldDriver"):
        cmds.setAttr("defaultArnoldDriver.ai_translator", "exr", type="string")
        cmds.setAttr("defaultArnoldDriver.mergeAOVs", 1)
        cmds.setAttr("defaultArnoldDriver.exrCompression", 3)  # 3 = zip (scanline)
        cmds.setAttr("defaultArnoldDriver.halfPrecision", 1)   # 16-bit half float
        cmds.setAttr("defaultArnoldDriver.autocrop", 1)

def _clear_aovs(aov_interface):
    for a in aov_interface.getAOVs():
        aov_interface.removeAOV(a.name)

def _setup_cryptomatte():
    """cryptomatteシェーダーを作成し、crypto系AOVへ自動接続する"""
    crypto_shader = "aiCryptomatte_AOV_Shader"
    if not cmds.objExists(crypto_shader):
        crypto_shader = cmds.shadingNode("cryptomatte", asShader=True, name=crypto_shader)
    for cname in CRYPTO_AOVS:
        cnode = "aiAOV_" + cname
        if cmds.objExists(cnode) and not cmds.isConnected(crypto_shader + ".outColor", cnode + ".defaultValue"):
            cmds.connectAttr(crypto_shader + ".outColor", cnode + ".defaultValue", force=True)

def _setup_ao_aov(ao_samples=3, ao_distance=10.0):
    """aiAmbientOcclusionを作成し、カスタムAOV 'AO' に接続する"""
    aov_name = "AO"
    shader_name = "aiAO_AOV_Shader"

    aov_interface = aovs.AOVInterface()
    existing = [a.name for a in aov_interface.getAOVs()]
    if aov_name not in existing:
        aov_interface.addAOV(aov_name)

    aov_node = "aiAOV_" + aov_name
    if not cmds.objExists(shader_name):
        shader_name = cmds.shadingNode("aiAmbientOcclusion", asShader=True, name=shader_name)

    cmds.setAttr(shader_name + ".samples", ao_samples)
    cmds.setAttr(shader_name + ".farClip", ao_distance)

    if cmds.objExists(aov_node):
        if not cmds.isConnected(shader_name + ".outColor", aov_node + ".defaultValue"):
            cmds.connectAttr(shader_name + ".outColor", aov_node + ".defaultValue", force=True)

def _get_ao_params():
    """UIスライダーからAO設定を読む（無ければデフォルト値）"""
    samples, dist = 3, 10.0
    try:
        if cmds.intSliderGrp("aoSamplesSlider", q=True, exists=True):
            samples = cmds.intSliderGrp("aoSamplesSlider", q=True, v=True)
        if cmds.floatSliderGrp("aoDistSlider", q=True, exists=True):
            dist = cmds.floatSliderGrp("aoDistSlider", q=True, v=True)
    except Exception:
        pass
    return samples, dist

def clear_all_aovs(*args):
    cmds.undoInfo(openChunk=True)
    try:
        _ensure_arnold_loaded()
        aov_interface = aovs.AOVInterface()
        _clear_aovs(aov_interface)
        for shader_name in ("aiAO_AOV_Shader", "aiCryptomatte_AOV_Shader"):
            if cmds.objExists(shader_name):
                cmds.delete(shader_name)
        cmds.inViewMessage(amg="既存のAOVをすべてクリアしました。", pos="topCenter", fade=True)
    finally:
        cmds.undoInfo(closeChunk=True)

def apply_aov_preset(preset_key, *args):
    cmds.undoInfo(openChunk=True)
    try:
        _ensure_arnold_loaded()
        _setup_multichannel_exr()

        clear_before = cmds.checkBox("clearExistingAOV_chk", q=True, value=True)
        if clear_before and preset_key != "ao_only":
            aov_interface = aovs.AOVInterface()
            _clear_aovs(aov_interface)

        preset = AOV_PRESETS[preset_key]
        aov_interface = aovs.AOVInterface()
        existing = [a.name for a in aov_interface.getAOVs()]

        for aov_name in preset["aovs"]:
            if aov_name not in existing:
                aov_interface.addAOV(aov_name)

        if preset["crypto"]:
            _setup_cryptomatte()

        if preset["ao"]:
            samples, dist = _get_ao_params()
            _setup_ao_aov(ao_samples=samples, ao_distance=dist)

        cmds.inViewMessage(
            amg="AOVセット適用完了: <hl>{}</hl> (Merge AOVs: ON)".format(preset["label"]),
            pos="topCenter", fade=True
        )
    finally:
        cmds.undoInfo(closeChunk=True)

# ---- ライトグループ ----
def _collect_light_groups():
    """シーン内のライトに設定された AOV Light Group 名を集める"""
    groups = []
    shapes = cmds.ls(dag=True, lights=True) or []
    for node_type in ("aiSkyDomeLight", "aiAreaLight", "aiPhotometricLight"):
        shapes += cmds.ls(type=node_type) or []
    for shp in shapes:
        for attr in ("aovLightGroup", "aiAovLightGroup"):
            if cmds.attributeQuery(attr, node=shp, exists=True):
                try:
                    val = cmds.getAttr(shp + "." + attr)
                except Exception:
                    val = None
                if val and val not in groups:
                    groups.append(val)
    return groups

def _add_light_group_aov(base_name, group):
    """ライトグループ付きAOVを1個追加する。成功したら True"""
    aov_interface = aovs.AOVInterface()
    # 本命: AOVInterface の lightGroup 引数
    try:
        aov_interface.addAOV(base_name, lightGroup=group)
        return True
    except TypeError:
        pass
    except Exception:
        pass
    # 代替: 通常追加してから aiAOV ノードの属性で設定
    existing = [a.name for a in aov_interface.getAOVs()]
    if base_name not in existing:
        try:
            aov_interface.addAOV(base_name)
        except Exception:
            return False
    node = "aiAOV_" + base_name
    if cmds.objExists(node):
        for attr in ("lightGroup", "aiLightGroup"):
            if cmds.attributeQuery(attr, node=node, exists=True):
                try:
                    cmds.setAttr(node + "." + attr, group, type="string")
                    return True
                except Exception:
                    pass
    return False

def apply_light_groups(*args):
    cmds.undoInfo(openChunk=True)
    try:
        _ensure_arnold_loaded()
        _setup_multichannel_exr()

        groups = _collect_light_groups()
        if not groups:
            cmds.confirmDialog(
                title="ライトグループが見つかりません",
                message="ライトに AOV Light Group 名が設定されていません。\n各ライトのアトリビュートエディタ（Arnold欄）で\nAOV Light Group に名前（例: key / fill / rim）を付けてから実行してください。",
                button=["OK"]
            )
            return

        clear_before = cmds.checkBox("clearExistingAOV_chk", q=True, value=True)
        if clear_before:
            aov_interface = aovs.AOVInterface()
            _clear_aovs(aov_interface)

        made = []
        failed = []
        for group in groups:
            for base_name in ("diffuse", "specular"):
                if _add_light_group_aov(base_name, group):
                    made.append("{} ({})".format(base_name, group))
                else:
                    failed.append("{} ({})".format(base_name, group))

        msg = "ライトグループAOV適用: " + ("、".join(made) if made else "作成できませんでした")
        if failed:
            msg += " / 失敗: " + "、".join(failed)
        cmds.inViewMessage(amg=msg, pos="topCenter", fade=True)
    finally:
        cmds.undoInfo(closeChunk=True)

def show_arnold_aov_ui():
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME, window=True)

    cmds.window(WINDOW_NAME, title="Arnold AOV セットアップ V2", widthHeight=(420, 560), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnOffset=("both", 12))

    cmds.separator(height=6, style="none")
    cmds.text(label="Arnold AOV & マルチチャンネルEXR 自動設定 V2", font="boldLabelFont", align="center")
    cmds.text(label="※適用時に EXR / Merge AOVs / ZIP圧縮 が自動で有効になります", font="smallPlainLabelFont", align="center")
    cmds.separator(height=8, style="in")

    cmds.checkBox("clearExistingAOV_chk", label="適用前に既存のAOVをクリアして入れ替える（AO追加時は維持）", value=True)
    cmds.separator(height=4, style="none")

    cmds.button(label="① フル合成セット (完全分解+テクニカル+Crypto+AO)", height=32, bgc=(0.25, 0.55, 0.8),
                command=lambda *x: apply_aov_preset("full"))
    cmds.button(label="② クイックチェック (beautyのみ)", height=32, bgc=(0.45, 0.45, 0.45),
                command=lambda *x: apply_aov_preset("quick"))
    cmds.button(label="②' コンポ下見 (beauty + Cryptomatte + Z)", height=32, bgc=(0.35, 0.6, 0.65),
                command=lambda *x: apply_aov_preset("preview"))
    cmds.button(label="③ グレード用セット (合算パス)", height=32, bgc=(0.25, 0.7, 0.55),
                command=lambda *x: apply_aov_preset("grade"))
    cmds.button(label="④ ライトグループ (ライト別 diffuse/specular)", height=32, bgc=(0.65, 0.45, 0.8),
                command=apply_light_groups)
    cmds.text(label="※④は各ライトの「AOV Light Group」に名前が付いている時だけ有効", font="smallPlainLabelFont", align="left")

    cmds.separator(height=8, style="in")
    cmds.text(label="アンビエントオクルージョン (AO) カスタム設定", font="boldLabelFont", align="left")
    cmds.intSliderGrp("aoSamplesSlider", label="AO サンプル数", field=True, minValue=1, maxValue=16, value=3, cw3=(95, 50, 180))
    cmds.floatSliderGrp("aoDistSlider", label="AO 距離 (Far Clip)", field=True, minValue=0.1, maxValue=500.0, value=10.0, cw3=(95, 50, 180))
    cmds.button(label="⑤ AO パスを追加・自動接続する", height=32, bgc=(0.4, 0.75, 0.35),
                command=lambda *x: apply_aov_preset("ao_only"))

    cmds.separator(height=8, style="in")
    cmds.button(label="すべてのAOVを削除・リセット", height=26, bgc=(0.75, 0.3, 0.3), command=clear_all_aovs)

    cmds.showWindow(WINDOW_NAME)

show_arnold_aov_ui()

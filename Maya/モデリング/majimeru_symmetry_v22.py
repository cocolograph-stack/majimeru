# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_symmetry_v22  v22
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya Python tool
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

# -*- coding: utf-8 -*-
"""
Symmetry (半分モデリング + ロック付きインスタンス方式)
- majimeru_symmetry_v22.py
majimeru

[v22 変更点] (確定の言い方を差し替え)
  「1つにくっつける」を、ユーザーの言い方「一つのモデルに
  してしまう」に差し替えた。確定ボタン、解除の説明、
  下の説明文、確定後の結果表示をそろえた。ロジック不変。

[v21 変更点] (説明文をやさしい言葉に)
  初めての人には難しいという指摘で、グレーの説明文を
  全部やさしい言葉に書き直した。「溶接」は「くっつける」、
  「しきい値」は「真ん中とみなす幅」に変更。ボタンや
  結果表示の「溶接」表記もそろえた。ロジックは不変。

[v20 変更点] (解除の説明文を差し替え)
  解除の説明を「やめるのは確定の前まで」という要点が
  伝わる文に変えた (ユーザー指定の趣旨)。確定すると
  1つに溶接され、解除では戻せないことを明記。
  ロジックは v19 のまま。

[v19 変更点] (解除ボタンに説明を追加)
  解除ボタンの文言を「解除 (シンメトリーをやめる)」にし、
  ボタンの下に説明文を追加した: 確定せずに終了すること、
  押すと「開始前の形に戻す」か「半分のまま残す」かを
  選べること。ロジックは v18 のまま。

[v18 変更点] (v17 の起動エラー修正)
  残す側ボタンのスタイル指定で、CSS の波括弧と Python の
  str.format のプレースホルダが衝突し、起動時に
  KeyError: ' padding' で落ちていた。文字列連結で組み立てる
  方式に変えて修正。見た目とロジックは v17 のまま。

[v17 変更点] (見た目だけ: ウィンドウをカラフルに)
  ロジックは v16 と同一。対称軸の X/Y/Z を Maya の軸色
  (X=赤、Y=緑、Z=青) のピル型ボタンにし、残す側の +/- にも
  色を付けた。開始ボタンは緑、確定ボタンは黄色、解除は
  赤のアウトライン。押した状態が色で分かるようにしている。
  あわせて、ウィンドウ上部に「何ができるツールか」を
  説明するタイトル見出しを追加した。

[v16 変更点] (切断を kk_symmetry 方式に変更)
  実験3で、この Maya では頂点削除コマンド (cmds.delete /
  選択して delete / polyDelVertex) が例外もなく無言で
  効かないことが判明した。そこで切断を、頂点を消さず
  polyCut 自身の deleteFaces で捨て側を切り捨てる方式
  (Highend3d の kk_symmetry と同方式) に変えた。実験5で
  実証済み: 立方体が頂点8のきれいな半分になり、回転なし
  = +側が残る / 180度回転 = -側が残る。切断後の残存検証
  とバックアップ自動復旧は v15 から引き継いでいる。

[v15 変更点] (不具合修正: 開始しても半分にならない)
  v14 の実機診断で判明: 開始直後の本体が「切断だけされた全体」
  (頂点12・範囲そのまま) になっており、捨て側の頂点削除が
  効いていなかった。その全体に鏡像インスタンスが重なり、
  全体が二重に見えていた。対策として、切断直後にヒストリを
  消して形を確定させてから頂点を削除するようにし、削除後に
  捨て側の残存頂点を検証して、残っていたら開始を失敗として
  バックアップから自動復旧するようにした。

[v14 の方式転換] (ユーザー提案 2026-11-18)
  Maya のシンメトリ機能 (symmetricModelling) は使わない。
  押し出しが効かない等、ツール側の制約が多く、全体設定の
  ON/OFF 事故も起きたため、方式そのものを変えた。

  開始: メッシュを真ん中で切って反対側を捨て、捨てた側に
        同じ形のインスタンスを置く。インスタンスはロック
        (参照表示 + 移動/回転/スケール固定) され、選択も
        移動もできない。編集は残した半分だけに行い、通常の
        モデリング操作 (押し出し等) がそのまま使える。
  確定: インスタンスを消し、半分を実際に鏡像化して
        1つのメッシュに溶接する。
  解除: インスタンスを消す。開始前の形 (バックアップ) に
        戻すか、半分のままにするかを選べる。

  切断 (polyCut の deleteFaces、kk_symmetry 方式) と
  鏡像 (polyMirrorFace) と
  シーム溶接 (polyMergeVertex) は、いずれも過去バージョンで
  実機確認済みの手順をそのまま使っている。
  モデルはセンター (原点) に置く前提。対象はメッシュのみ。

使い方 (Maya の Script Editor で実行):
    import majimeru_symmetry_v22
    majimeru_symmetry_v22.show_ui()
"""

import traceback

from maya import cmds
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
    except ImportError:
        import qtpy.QtWidgets as QtWidgets
        import qtpy.QtCore as QtCore


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

AXIS_NAMES = ("x", "y", "z")


def get_maya_window():
    try:
        from shiboken6 import wrapInstance
    except ImportError:
        try:
            from shiboken2 import wrapInstance
        except ImportError:
            return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _short_name(node):
    return node.rsplit("|", 1)[-1] if node else ""


def _long_name(node):
    found = cmds.ls(node, long=True) or []
    return found[0] if found else node


def _selected_mesh_transform():
    sel = cmds.ls(selection=True, long=True) or []
    for node in sel:
        base = node.split(".")[0]
        if not cmds.objExists(base):
            continue
        if cmds.nodeType(base) == "transform" and cmds.listRelatives(
                base, shapes=True, type="mesh"):
            return base
        parents = cmds.listRelatives(base, parent=True, fullPath=True) or []
        if parents:
            return parents[0]
    return None


def _safe_base(tf):
    base = _short_name(tf)
    for ch in ("|", ":", " "):
        base = base.replace(ch, "_")
    return base or "mesh"


# ---------------------------------------------------------------------------
# 状態アトリビュート (半分側のトランスフォームに記録)
# ---------------------------------------------------------------------------

SETUP_ATTRS = (
    ("symActive",   "bool",   False),
    ("symInstance", "string", ""),
    ("symBackup",   "string", ""),
    ("symAxis",     "long",   0),
    ("symKeepPos",  "bool",   True),
)


def _ensure_attrs(tf):
    for name, attr_type, default in SETUP_ATTRS:
        if not cmds.attributeQuery(name, node=tf, exists=True):
            kwargs = {"attributeType": attr_type} \
                if attr_type != "string" else {"dataType": "string"}
            cmds.addAttr(tf, longName=name, **kwargs)
        try:
            if attr_type == "string":
                if cmds.getAttr(tf + "." + name) is None:
                    cmds.setAttr(tf + "." + name, "", type="string")
            else:
                cmds.getAttr(tf + "." + name)
        except Exception:
            try:
                if attr_type == "string":
                    cmds.setAttr(tf + "." + name, str(default),
                                 type="string")
                else:
                    cmds.setAttr(tf + "." + name, default)
            except Exception:
                pass


def _is_active(tf):
    if not tf or not cmds.objExists(tf):
        return False
    _ensure_attrs(tf)
    try:
        return bool(cmds.getAttr(tf + ".symActive"))
    except Exception:
        return False


def _get_str(tf, name):
    try:
        value = cmds.getAttr(tf + "." + name)
        return value if value else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 切断 (kk_symmetry 方式、実験5で実証済み)
# ---------------------------------------------------------------------------

def _slice_and_snap(mesh, axis_index, keep_pos, offset, threshold):
    """kk_symmetry 方式で切断する: polyCut の deleteFaces で
    捨て側を切り捨て、中央付近の頂点を対称面へスナップする。
    戻り値: 切断で減った頂点数。

    頂点削除コマンドは使わない。実験3で、この Maya では
    頂点削除 (cmds.delete / 選択して delete / polyDelVertex)
    が例外もなく無言で効かないことが判明したため。kk 方式は
    実験5で実証済み: 立方体が頂点8のきれいな半分になり、
    回転なし = +側が残る、180度回転 = -側が残る。切断後は
    捨て側に頂点が残っていないか検証し、残っていたら例外に
    して開始全体を失敗扱いにする (黙って成功しない)。"""
    direction = AXIS_NAMES[axis_index]
    before = cmds.polyEvaluate(mesh, vertex=True)
    node = cmds.polyCut(mesh, cuttingDirection=direction,
                        deleteFaces=True)
    node = node[0] if isinstance(node, (list, tuple)) else node
    center = [0.0, 0.0, 0.0]
    center[axis_index] = offset
    cmds.setAttr(node + ".cutPlaneCenterX", center[0])
    cmds.setAttr(node + ".cutPlaneCenterY", center[1])
    cmds.setAttr(node + ".cutPlaneCenterZ", center[2])
    if not keep_pos:
        # 捨て側を反転させる (kk_symmetry の対応表:
        # X は cutPlaneRotateX、Y は cutPlaneRotateZ、
        # Z は cutPlaneRotateY。X は実験5で実証済み)
        flip_attr = ("cutPlaneRotateX", "cutPlaneRotateZ",
                     "cutPlaneRotateY")[axis_index]
        cmds.setAttr(node + "." + flip_attr, 180.0)
    try:
        cmds.delete(mesh, constructionHistory=True)
    except Exception as exc:
        print("[majimeru Symmetry] ヒストリ削除に失敗: "
              "{}".format(exc))
    # 中央付近の頂点を対称面へスナップ (切断で生じた点は面の
    # 上にできているが、元の頂点の誤差を吸収する)
    keep_sign = 1.0 if keep_pos else -1.0
    for vtx in cmds.ls(mesh + ".vtx[*]", flatten=True) or []:
        pos = cmds.pointPosition(vtx, world=True)
        if abs(pos[axis_index] - offset) <= threshold:
            new_pos = list(pos)
            new_pos[axis_index] = offset
            cmds.xform(vtx, worldSpace=True, translation=new_pos)
    # 検証: 捨て側に頂点が残っていたら切断が効いていない
    leftovers = 0
    for vtx in cmds.ls(mesh + ".vtx[*]", flatten=True) or []:
        pos = cmds.pointPosition(vtx, world=True)
        if (pos[axis_index] - offset) * keep_sign < -threshold:
            leftovers += 1
    if leftovers:
        raise RuntimeError(
            "切断が効きませんでした (捨て側に {} 点残存)。"
            .format(leftovers))
    after = cmds.polyEvaluate(mesh, vertex=True)
    return before - after


def _weld_seam(mesh, axis_index, offset, threshold):
    """対称面付近の頂点を polyMergeVertex で溶接する"""
    tol = max(threshold, 1e-4)
    verts = cmds.ls(mesh + ".vtx[*]", flatten=True) or []
    seam = []
    for vtx in verts:
        pos = cmds.pointPosition(vtx, world=True)
        if abs(pos[axis_index] - offset) <= tol * 2.0:
            seam.append(vtx)
    if len(seam) < 2:
        return
    cmds.select(seam, replace=True)
    try:
        cmds.polyMergeVertex(distance=tol, alwaysMergeTwoVertices=False,
                             worldSpace=True, constructionHistory=False)
    finally:
        cmds.select(mesh, replace=True)


# ---------------------------------------------------------------------------
# 開始 / 確定 / 解除
# ---------------------------------------------------------------------------

def start_symmetry(tf, axis_index, keep_pos, threshold):
    """半分に切って、反対側にロック付きインスタンスを置く"""
    if _is_active(tf):
        raise RuntimeError("このメッシュは既に対称モード中です: "
                           + _short_name(tf))
    base = _safe_base(tf)
    backup = cmds.duplicate(tf, name=base + "_SYM_backup",
                            returnRootsOnly=True)[0]
    backup_long = _long_name(backup)
    try:
        cmds.setAttr(backup_long + ".visibility", False)
    except Exception:
        pass
    try:
        _slice_and_snap(tf, axis_index, keep_pos, 0.0,
                        max(threshold, 0.0))
        # 反対側にインスタンスを置く (軸方向に -1 スケール)
        result = cmds.instance(tf, name=base + "_SYM_LOCK")
        inst = result[0] if isinstance(result, (list, tuple)) else result
        inst_long = _long_name(inst)
        scale = [1.0, 1.0, 1.0]
        scale[axis_index] = -1.0
        cmds.setAttr(inst_long + ".scale",
                     scale[0], scale[1], scale[2], type="double3")
        # ロック: 参照表示 (ビューポートで選択不可) + 変形を固定
        try:
            cmds.setAttr(inst_long + ".overrideEnabled", 1)
            cmds.setAttr(inst_long + ".overrideDisplayType", 2)
        except Exception as exc:
            print("[majimeru Symmetry] 参照表示の設定に失敗: "
                  "{}".format(exc))
        for attr in ("translateX", "translateY", "translateZ",
                     "rotateX", "rotateY", "rotateZ",
                     "scaleX", "scaleY", "scaleZ"):
            try:
                cmds.setAttr(inst_long + "." + attr, lock=True)
            except Exception:
                pass
    except Exception:
        # 失敗したらバックアップから元に戻す
        src_short = _short_name(tf)
        if cmds.objExists(tf):
            cmds.delete(tf)
        if cmds.objExists(backup_long):
            try:
                cmds.setAttr(backup_long + ".visibility", True)
            except Exception:
                pass
            try:
                renamed = cmds.rename(backup_long, src_short)
                backup_long = _long_name(renamed)
            except Exception:
                pass
            cmds.select(backup_long, replace=True)
        raise
    _ensure_attrs(tf)
    cmds.setAttr(tf + ".symInstance", inst_long, type="string")
    cmds.setAttr(tf + ".symBackup", backup_long, type="string")
    cmds.setAttr(tf + ".symAxis", axis_index)
    cmds.setAttr(tf + ".symKeepPos", bool(keep_pos))
    cmds.setAttr(tf + ".symActive", True)
    cmds.select(tf, replace=True)
    return inst_long


def _delete_recorded(tf, attr_name):
    name = _get_str(tf, attr_name)
    if name and cmds.objExists(name):
        try:
            cmds.delete(name)
            return True
        except Exception:
            pass
    return False


def apply_symmetry(tf, threshold):
    """インスタンスを消し、半分を鏡像化して1つに溶接する。
    戻り値: 完成したメッシュのシェル数"""
    if not _is_active(tf):
        raise RuntimeError("このメッシュは対称モード中ではありません: "
                           + _short_name(tf))
    axis_index = int(cmds.getAttr(tf + ".symAxis"))
    keep_pos = bool(cmds.getAttr(tf + ".symKeepPos"))
    _delete_recorded(tf, "symInstance")
    direction = axis_index * 2 + (1 if keep_pos else 0)
    pivot = [0.0, 0.0, 0.0]
    result = cmds.polyMirrorFace(
        tf,
        constructionHistory=True,
        direction=direction,
        mergeMode=1,
        mergeThreshold=max(threshold, 0.0),
        pivot=tuple(pivot),
        worldSpace=True)
    node = result[0] if isinstance(result, (list, tuple)) else result
    if not node or not cmds.objExists(node):
        raise RuntimeError("polyMirrorFace ノードが作れませんでした")
    cmds.delete(tf, constructionHistory=True)
    # mergeMode 任せで溶接されないケースが実機であったため、
    # 中央シームを明示的に溶接する
    _weld_seam(tf, axis_index, 0.0, max(threshold, 0.0))
    _delete_recorded(tf, "symBackup")
    cmds.setAttr(tf + ".symActive", False)
    cmds.setAttr(tf + ".symInstance", "", type="string")
    cmds.setAttr(tf + ".symBackup", "", type="string")
    cmds.select(tf, replace=True)
    try:
        return int(cmds.polyEvaluate(tf, shell=True))
    except Exception:
        return 0


def remove_symmetry(tf, restore):
    """インスタンスを消して対称モードを終える。
    restore=True なら開始前の形に戻す。False なら半分のまま。"""
    if not _is_active(tf):
        raise RuntimeError("このメッシュは対称モード中ではありません: "
                           + _short_name(tf))
    backup_long = _get_str(tf, "symBackup")
    _delete_recorded(tf, "symInstance")
    if restore and backup_long and cmds.objExists(backup_long):
        src_short = _short_name(tf)
        cmds.delete(tf)
        try:
            cmds.setAttr(backup_long + ".visibility", True)
        except Exception:
            pass
        try:
            renamed = cmds.rename(backup_long, src_short)
            backup_long = _long_name(renamed)
        except Exception:
            pass
        cmds.select(backup_long, replace=True)
        return backup_long
    _delete_recorded(tf, "symBackup")
    if cmds.objExists(tf):
        cmds.setAttr(tf + ".symActive", False)
        cmds.setAttr(tf + ".symInstance", "", type="string")
        cmds.setAttr(tf + ".symBackup", "", type="string")
        cmds.select(tf, replace=True)
    return tf


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

WINDOW_NAME = "majimeruSymmetryWindow"
WINDOW_TITLE = "シンメトリー (半分モデリング+鏡像表示) v22 - majimeru"


class SymmetryWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SymmetryWindow, self).__init__(parent)
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        # 常に最前面 (この1回だけ。setWindowFlags は上書き式)
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(350)
        self._build_ui()
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._refresh_target)
        self._timer.start(600)
        self._refresh_target()

    def _build_ui(self):
        self.setStyleSheet(
            "QGroupBox { font-weight: bold; }")
        layout = QtWidgets.QVBoxLayout(self)

        header_title = QtWidgets.QLabel(
            "シンメトリー (半分モデリング)")
        header_title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #e6b93d;")
        layout.addWidget(header_title)
        header_desc = QtWidgets.QLabel(
            "半分だけ作れば、もう半分は鏡に映したように"
            "見えます。ふだん通りのモデリングで大丈夫です。")
        header_desc.setWordWrap(True)
        header_desc.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(header_desc)

        self.target_label = QtWidgets.QLabel("対象: (未選択)")
        self.target_label.setWordWrap(True)
        self.target_label.setStyleSheet(
            "font-weight: bold; font-size: 13px;")
        layout.addWidget(self.target_label)

        axis_box = QtWidgets.QGroupBox("対称軸 (Mirror Axis)")
        axis_layout = QtWidgets.QHBoxLayout(axis_box)
        self.axis_group = QtWidgets.QButtonGroup(self)
        self.axis_buttons = []
        for i, name in enumerate(("X", "Y", "Z")):
            btn = QtWidgets.QRadioButton(name)
            self.axis_group.addButton(btn, i)
            self.axis_buttons.append(btn)
            axis_layout.addWidget(btn)
        self.axis_buttons[0].setChecked(True)
        axis_layout.setSpacing(8)
        _axis_colors = (
            ("#e05555", "#c93b3b"),
            ("#5dbb63", "#3f9142"),
            ("#5b8dd9", "#3a68ad"),
        )
        for _btn, (_text_color, _bg_color) in zip(
                self.axis_buttons, _axis_colors):
            _btn.setStyleSheet(
                "QRadioButton {"
                " padding: 6px 16px;"
                " border: 2px solid " + _bg_color + ";"
                " border-radius: 12px;"
                " color: " + _text_color + ";"
                " font-weight: bold;"
                " font-size: 14px;"
                "}"
                "QRadioButton::indicator {"
                " width: 0px; height: 0px;"
                "}"
                "QRadioButton:checked {"
                " background-color: " + _bg_color + ";"
                " color: white;"
                "}")
        layout.addWidget(axis_box)

        keep_box = QtWidgets.QGroupBox("残す側 (編集する側)")
        keep_layout = QtWidgets.QHBoxLayout(keep_box)
        self.keep_plus_btn = QtWidgets.QRadioButton("+ 側を残す")
        self.keep_minus_btn = QtWidgets.QRadioButton("- 側を残す")
        self.keep_plus_btn.setChecked(True)
        keep_layout.setSpacing(8)

        def _keep_pill(border, text):
            return (
                "QRadioButton {"
                " padding: 5px 12px;"
                " border: 2px solid " + border + ";"
                " border-radius: 11px;"
                " color: " + text + ";"
                " font-weight: bold;"
                "}"
                "QRadioButton::indicator {"
                " width: 0px; height: 0px;"
                "}"
                "QRadioButton:checked {"
                " background-color: " + border + ";"
                " color: white;"
                "}")

        self.keep_plus_btn.setStyleSheet(
            _keep_pill("#c98a3d", "#e0a458"))
        self.keep_minus_btn.setStyleSheet(
            _keep_pill("#4a7fa5", "#7fb2e0"))
        keep_layout.addWidget(self.keep_plus_btn)
        keep_layout.addWidget(self.keep_minus_btn)
        layout.addWidget(keep_box)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("真ん中とみなす幅:"))
        self.threshold_spin = QtWidgets.QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setDecimals(4)
        self.threshold_spin.setSingleStep(0.01)
        self.threshold_spin.setValue(0.01)
        row.addWidget(self.threshold_spin)
        layout.addLayout(row)

        self.start_btn = QtWidgets.QPushButton("対称モード開始")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.clicked.connect(self._on_start)
        self.start_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #3f9142;"
            " color: white;"
            " border: none;"
            " border-radius: 8px;"
            " font-weight: bold;"
            " font-size: 13px;"
            " padding: 6px;"
            "}"
            "QPushButton:hover { background-color: #47a34b; }"
            "QPushButton:pressed { background-color: #357a38; }")
        layout.addWidget(self.start_btn)

        self.apply_btn = QtWidgets.QPushButton(
            "確定 (一つのモデルにしてしまう)")
        self.apply_btn.setMinimumHeight(38)
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #e6b93d;"
            " color: #2b2b2b;"
            " border: none;"
            " border-radius: 8px;"
            " font-weight: bold;"
            " font-size: 13px;"
            " padding: 6px;"
            "}"
            "QPushButton:hover { background-color: #f0c44e; }"
            "QPushButton:pressed { background-color: #cfa32f; }")
        layout.addWidget(self.apply_btn)

        self.remove_btn = QtWidgets.QPushButton("解除 (シンメトリーをやめる)")
        self.remove_btn.setMinimumHeight(30)
        self.remove_btn.clicked.connect(self._on_remove)
        self.remove_btn.setStyleSheet(
            "QPushButton {"
            " background-color: transparent;"
            " color: #e08a8a;"
            " border: 1px solid #b05555;"
            " border-radius: 8px;"
            " font-weight: bold;"
            " padding: 5px;"
            "}"
            "QPushButton:hover { background-color: #4a3232; }"
            "QPushButton:pressed {"
            " background-color: #7a3a3a; color: white; }")
        layout.addWidget(self.remove_btn)

        remove_note = QtWidgets.QLabel(
            "やめたい時は、確定を押す前に押してください。"
            "確定すると一つのモデルになって、元に戻せなくなります。"
            "押すと「切る前の形に戻す」か「半分のままにする」かを"
            "選べます。")
        remove_note.setWordWrap(True)
        remove_note.setStyleSheet("color: #9a9a9a;")
        layout.addWidget(remove_note)

        note = QtWidgets.QLabel(
            "「対称モード開始」を押すと、モデルが真ん中で"
            "半分になります。消えた側は、鏡に映した姿で"
            "見えていて、触れません。作るのは残った半分だけです。"
            "真ん中にある点は、真ん中から動かさないでください。"
            "動かすと、一つのモデルにした時にすき間が"
            "できてしまいます。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #9a9a9a;")
        layout.addWidget(note)

        self.result_label = QtWidgets.QLabel("【結果】まだ実行していません。")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

    # -- 表示更新 ------------------------------------------------------
    def _refresh_target(self):
        target = _selected_mesh_transform()
        if not target:
            self.target_label.setText("対象: (未選択)")
            return
        if _is_active(target):
            self.target_label.setText(
                "対象: {} (対称モード中)".format(_short_name(target)))
        else:
            self.target_label.setText(
                "対象: {}".format(_short_name(target)))

    def _set_result(self, text, is_error=False):
        self.result_label.setText(text)
        self.result_label.setStyleSheet(
            "color: #ff6666;" if is_error else "color: #7dd87d;")
        if is_error:
            cmds.warning(text)
        else:
            print("[majimeru Symmetry] " + text)

    def _threshold(self):
        return max(float(self.threshold_spin.value()), 0.0)

    # -- ボタン --------------------------------------------------------
    def _on_start(self):
        target = _selected_mesh_transform()
        if not target:
            self._set_result("メッシュを選択してから押してください。",
                             True)
            return
        axis_index = self.axis_group.checkedId()
        if axis_index < 0:
            axis_index = 0
        keep_pos = self.keep_plus_btn.isChecked()
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymStart")
        try:
            start_symmetry(target, axis_index, keep_pos,
                           self._threshold())
        except Exception as exc:
            traceback.print_exc()
            self._set_result("開始に失敗: {}".format(exc), True)
        else:
            self._set_result(
                "対称モード開始: {} を半分にし、反対側にロック済み"
                "インスタンスを表示しました。編集は残した側だけに"
                "行ってください。".format(_short_name(target)))
        finally:
            cmds.undoInfo(closeChunk=True)
        self._refresh_target()

    def _on_apply(self):
        target = _selected_mesh_transform()
        if not target:
            self._set_result("メッシュを選択してから押してください。",
                             True)
            return
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymApply")
        try:
            shells = apply_symmetry(target, self._threshold())
        except Exception as exc:
            traceback.print_exc()
            self._set_result("確定に失敗: {}".format(exc), True)
        else:
            msg = ("確定しました: {} は一つのモデルになりました。"
                   .format(_short_name(target)))
            if shells and shells != 1:
                msg += (" (真ん中がくっついていないかも"
                        "しれません: かたまり数 {})".format(shells))
            self._set_result(msg)
        finally:
            cmds.undoInfo(closeChunk=True)
        self._refresh_target()

    def _on_remove(self):
        target = _selected_mesh_transform()
        if not target:
            self._set_result("メッシュを選択してから押してください。",
                             True)
            return
        if not _is_active(target):
            self._set_result(
                "このメッシュは対称モード中ではありません: "
                + _short_name(target), True)
            return
        answer = cmds.confirmDialog(
            title="解除の方法",
            message="開始前の形に戻しますか？\n"
                    "「元に戻す」: 編集を捨てて開始前の形に復元\n"
                    "「半分のまま」: 今の半分を残して終了",
            button=["元に戻す", "半分のまま", "キャンセル"],
            defaultButton="元に戻す",
            cancelButton="キャンセル",
            dismissString="キャンセル")
        if answer == "キャンセル":
            return
        restore = (answer == "元に戻す")
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymRemove")
        try:
            result = remove_symmetry(target, restore)
        except Exception as exc:
            traceback.print_exc()
            self._set_result("解除に失敗: {}".format(exc), True)
        else:
            if restore:
                self._set_result(
                    "解除しました: {} を開始前の形に戻しました。"
                    .format(_short_name(result)))
            else:
                self._set_result(
                    "解除しました: {} は半分のままです。"
                    .format(_short_name(result)))
        finally:
            cmds.undoInfo(closeChunk=True)
        self._refresh_target()


_window = None


def show_ui():
    global _window
    parent = get_maya_window()
    if parent is not None:
        for child in parent.findChildren(QtWidgets.QDialog, WINDOW_NAME):
            child.close()
            child.deleteLater()
    if _window is not None:
        try:
            _window.close()
            _window.deleteLater()
        except Exception:
            pass
    _window = SymmetryWindow(parent)
    _window.show()
    _window.raise_()
    _window.activateWindow()
    return _window


if __name__ == "__main__":
    show_ui()

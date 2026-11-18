# -*- coding: utf-8 -*-
"""
Symmetry (3ds Max Symmetry モディファイヤー風) - majimeru_symmetry_v10.py
majimeru

[v10 変更点] (ユーザー要望: 真ん中の線が入ってへん / 実験2で確認)
  v9 は実機で反射が効くことを確認できたが、中央にエッジループ
  が無かった。実験2 (majimeru_symmetry_test2.py) で、polyCut で
  中央に線だけを入れる工程は反射ペアリングを壊さないことを
  実機確認した (頂点数 8->12、対称選択 -sym も効き、ドラッグに
  反対側が追随)。よって v10 の ON は:
    (1) 真ん中に線を入れる (polyCut のみ、チェックで OFF 可)
    (2) 頂点位置の左右そろえ
    (3) symmetricModelling ON
  の順に全部やる。ベイクは引き続き無し。

[v9 変更点] (実機の切り分けで原因確定, 2026-11-18)
  スクショ2枚で確定した事実:
  - 素の立方体 + symmetricModelling ON: 外向きドラッグで左右
    両側に開く。対称選択 (-sym) も効く。反射は正常。
  - ベイク (切断+polyMirrorFace+溶接) した立方体 + ON: 見た目は
    綺麗な立方体・シェル数1 でも、ドラッグで片側だけが伸びて
    反射のペアリングが効かない。
  つまりベイクで作ったメッシュの頂点構成が Maya の対称
  ペアリングと相性が悪い。よって v9 では ON の経路から
  ベイクを完全に外した:
  - ON = 頂点位置の左右そろえ (トポロジ・ヒストリ不変) +
    symmetricModelling ON。素のプリミティブと全く同じ構成の
    まま反射を効かせる。
  - 「片側から全体を作る」は廃止 (半分だけのメッシュは Maya
    標準の Mesh > Mirror で一度フルにしてから本ツールを使う)。
  - 自動カットのチェックは「ON の前に左右をそろえる」に変更。

[v8 変更点] (ユーザー実機: v7 でも「二つできる」)
  ユーザーの補足で判明: アウトライナでは1つだけ。動かすと
  二つになる = オブジェクトは1つだが中央シームが溶接されて
  おらず、中に2シェル入っていた。polyMirrorFace の mergeMode
  任せでは実機で溶接されないケースがあるため、ベイク後に
  対称面付近の頂点を polyMergeVertex で明示的に溶接する工程を
  追加し、結果欄にシェル数 (polyEvaluate shell) を表示する
  ようにした (1 が正常)。あわせて開始前に過去の *_SYM_backup
  残骸を掃除し、バックアップは名前で直接消すよう強化。

[v7 変更点] (ユーザー指摘: 真ん中が自動で切れた方が作りやすい)
  「対称編集 ON」を押した時に、真ん中で切って鏡像して対称形に
  作り直すところまで自動でやるようにした (Max でモディファイヤー
  を足した時の動き)。チェックを外せば、作り直しなしで ON だけ
  することもできる。既に ON のメッシュで ON を押し直すと
  作り直し (リベース) になる。単独の「片側から全体を作る」
  ボタンは ON に統合して廃止。作り直しはヒストリを消すが、
  ON 全体が1つの Undo で戻せる。

[設計: 最初から作り直し (2026-11-18)]
  v1〜v5 の継ぎ接ぎを捨て、実機で確定した事実だけから再設計した。

  実機で確定した事実:
  - ウィンドウ最前面は setWindowFlags 1回指定で効く (v2〜)。
  - 対称面で切って半分にする処理は動く (v3)。
  - 2オブジェクト方式は、センター配置のキャラでは使えない (却下)。
  - ヒストリに polyMirrorFace ノードを挟んでも、後の頂点編集は
    ノードの下流に入るので鏡像は追随しない (v4 で実証、却下)。
  - Maya 標準の対称編集 (cmds.symmetricModelling) は、素の立方体で
    「頂点を動かすと反対側が付いてくる」ことを実験スクリプト
    (majimeru_symmetry_test.py) で実機確認した (2026-11-18)。
    -> ライブ編集はこれを使う。これが本命。

  このツールの仕事は3つだけ:
  1) 対称編集 ON/OFF: symmetricModelling を軸つきで ON にし、
     OFF で元の設定に戻す。設定は対象メッシュに記録する。
  2) 左右をそろえる: 残す側の頂点位置を反対側へコピーして完全
     対称にする (ズレたモデルの修正 / ON 前の準備)。
  3) 片側から全体を作る: 切って鏡像してベイクし、対称な1メッシュ
     を作る (ワンショット。ヒストリは消える)。半分だけ作った
     モデルや、片側だけ作り直したい時に使う。

  前提: モデルはセンター (ワールド原点) に置く。対称面は原点の
  軸平面。対称編集は Maya 全体のツール設定なので、ON の間は
  他のメッシュにも効く (OFF で元に戻る)。
  対象はモデル (ポリゴンメッシュ) のみ。ウェイト/ジョイント用
  ではない。

[使い方]
    import majimeru_symmetry_v10
    majimeru_symmetry_v10.show_ui()
  ファイルを直接実行してもウィンドウが開く。
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


# ---------------------------------------------------------------------------
# 小物
# ---------------------------------------------------------------------------

AXES = ("X", "Y", "Z")
AXIS_LETTERS = ("x", "y", "z")

SETUP_ATTRS = (
    ("symAxis",      "long",   0),
    ("symKeepPos",   "bool",   True),
    ("symOffset",    "double", 0.0),
    ("symSlice",     "bool",   True),
    ("symCenterLine", "bool",  True),
    ("symWeld",      "bool",   True),
    ("symThreshold", "double", 0.01),
    ("symLive",      "bool",   False),
    ("symPrevSym",   "long",   0),
    ("symPrevAxis",  "string", "x"),
    ("symPrevAbout", "string", "world"),
)


def _short_name(long_name):
    return long_name.split("|")[-1]


def _safe_base(long_name):
    base = _short_name(long_name)
    for ch in (":", " ", "-", "."):
        base = base.replace(ch, "_")
    return base


def _mesh_transform_from_node(node):
    if not node or not cmds.objExists(node):
        return None
    node_type = cmds.nodeType(node)
    if node_type == "mesh":
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        return parents[0] if parents else None
    if node_type == "transform":
        shapes = cmds.listRelatives(
            node, shapes=True, fullPath=True, type="mesh") or []
        return node if shapes else None
    return None


def _selected_mesh_transform():
    sel = cmds.ls(selection=True, long=True) or []
    for node in sel:
        result = _mesh_transform_from_node(node.split(".")[0])
        if result:
            return result
    return None


def _ensure_setup_attrs(tf):
    for attr_name, attr_type, default in SETUP_ATTRS:
        if cmds.attributeQuery(attr_name, node=tf, exists=True):
            continue
        if attr_type == "string":
            cmds.addAttr(tf, longName=attr_name, dataType="string")
        elif attr_type == "bool":
            cmds.addAttr(tf, longName=attr_name, attributeType="bool",
                         defaultValue=1 if default else 0)
        elif attr_type == "long":
            cmds.addAttr(tf, longName=attr_name, attributeType="long",
                         defaultValue=default)
        else:
            cmds.addAttr(tf, longName=attr_name, attributeType="double",
                         defaultValue=default)


def _tf_extra(tf, attr):
    if not tf or not cmds.objExists(tf):
        return None
    if not cmds.attributeQuery(attr, node=tf, exists=True):
        return None
    try:
        return cmds.getAttr(tf + "." + attr)
    except Exception:
        return None


def _read_settings(tf):
    return {
        "axis":      int(cmds.getAttr(tf + ".symAxis")),
        "keep_pos":  bool(cmds.getAttr(tf + ".symKeepPos")),
        "offset":    float(cmds.getAttr(tf + ".symOffset")),
        "slice":     bool(cmds.getAttr(tf + ".symSlice")),
        "center_line": bool(cmds.getAttr(tf + ".symCenterLine")),
        "weld":      bool(cmds.getAttr(tf + ".symWeld")),
        "threshold": float(cmds.getAttr(tf + ".symThreshold")),
    }


def _write_settings(tf, settings):
    _ensure_setup_attrs(tf)
    cmds.setAttr(tf + ".symAxis", settings["axis"])
    cmds.setAttr(tf + ".symKeepPos", settings["keep_pos"])
    cmds.setAttr(tf + ".symOffset", settings["offset"])
    cmds.setAttr(tf + ".symSlice", settings["slice"])
    if "center_line" in settings:
        cmds.setAttr(tf + ".symCenterLine", settings["center_line"])
    cmds.setAttr(tf + ".symWeld", settings["weld"])
    cmds.setAttr(tf + ".symThreshold", settings["threshold"])


def _is_live(tf):
    return bool(_tf_extra(tf, "symLive"))


def _resolve_live(any_node):
    """選択ノードが対称編集 ON 中のメッシュなら transform を返す"""
    if not any_node or not cmds.objExists(any_node):
        return None
    tf = _mesh_transform_from_node(any_node.split(".")[0])
    if tf and _is_live(tf):
        return tf
    return None


# ---------------------------------------------------------------------------
# 対称編集 (symmetricModelling) — 実験で実証済みの部分
# ---------------------------------------------------------------------------

def _reflection_state_text():
    def _q(**kw):
        try:
            return cmds.symmetricModelling(query=True, **kw)
        except Exception as exc:
            return "ERR:{}".format(exc)
    return "symmetry={} / axis={} / about={}".format(
        _q(symmetry=True), _q(axis=True), _q(about=True))


def _sweep_sym_leftovers():
    """過去バージョンの実行で残った *_SYM_backup 系の残骸を消す"""
    removed = []
    for tf in cmds.ls(type="transform", long=True) or []:
        if "_SYM_backup" in _short_name(tf):
            try:
                cmds.delete(tf)
                removed.append(_short_name(tf))
            except Exception:
                pass
    return removed


def _insert_plane_cut(mesh, axis_index, offset):
    """polyCut で対称面の位置にエッジループ (真ん中の線) だけを
    入れる。頂点削除も鏡像もしない。成功したら True。
    実験2 (majimeru_symmetry_test2.py) で、この工程を入れても
    反射のペアリングが生きることを実機確認済み。"""
    center = [0.0, 0.0, 0.0]
    center[axis_index] = offset
    rotate = [(0.0, 90.0, 0.0),
              (90.0, 0.0, 0.0),
              (0.0, 0.0, 0.0)][axis_index]
    try:
        cmds.polyCut(mesh, constructionHistory=False, deleteFaces=False,
                     cutPlaneCenter=tuple(center),
                     cutPlaneRotate=tuple(rotate))
        return True
    except Exception as exc:
        print("[majimeru Symmetry] 中央の線入れに失敗 (線なしで続行): "
              "{}".format(exc))
        return False


def symmetry_on(tf, settings):
    """対称編集を ON にする。順序は実機で検証した通り:
    (1) settings["center_line"] が ON なら真ん中に線を入れる
        (polyCut のみ。実験2でペアリングが生きることを確認済み)
    (2) settings["slice"] が ON なら頂点位置を左右にそろえる
    (3) symmetricModelling を ON にする
    ベイク (切断+鏡像で作り直す) はペアリングを壊すのでしない。
    既に ON のメッシュでは、そろえ直しだけを行う。
    前の設定はメッシュに記録する。戻り値: (何をしたか
    "prepped" / "plain" / "reprepped", シェル数, 線を入れたか)"""
    _sweep_sym_leftovers()
    if _is_live(tf):
        if settings["slice"]:
            symmetrize_positions(tf, settings["axis"],
                                 settings["keep_pos"], settings["offset"],
                                 max(settings["threshold"], 0.0))
            _write_settings(tf, settings)
            return "reprepped", _shell_count(tf), False
        raise RuntimeError("このメッシュは既に対称編集 ON です: "
                           + _short_name(tf))
    cut_done = False
    if settings.get("center_line", True):
        cut_done = _insert_plane_cut(tf, settings["axis"],
                                     settings["offset"])
    prepped = False
    if settings["slice"]:
        symmetrize_positions(tf, settings["axis"],
                             settings["keep_pos"], settings["offset"],
                             max(settings["threshold"], 0.0))
        prepped = True
    prev = {
        "symmetry": cmds.symmetricModelling(query=True, symmetry=True),
        "axis": cmds.symmetricModelling(query=True, axis=True),
        "about": cmds.symmetricModelling(query=True, about=True),
    }
    _write_settings(tf, settings)
    cmds.setAttr(tf + ".symPrevSym", int(bool(prev["symmetry"])))
    cmds.setAttr(tf + ".symPrevAxis", str(prev["axis"]), type="string")
    cmds.setAttr(tf + ".symPrevAbout", str(prev["about"]), type="string")
    # 実験スクリプトと同じく、1項目ずつ確実にセットする
    cmds.symmetricModelling(about="world")
    cmds.symmetricModelling(axis=AXIS_LETTERS[settings["axis"]])
    cmds.symmetricModelling(symmetry=True)
    cmds.setAttr(tf + ".symLive", True)
    cmds.select(tf, replace=True)
    return ("prepped" if prepped else "plain"), _shell_count(tf), cut_done


def _shell_count(tf):
    try:
        return int(cmds.polyEvaluate(tf, shell=True))
    except Exception:
        return 0


def symmetry_off(tf):
    """対称編集を OFF にして、ON にする前の設定へ戻す"""
    prev_sym = _tf_extra(tf, "symPrevSym")
    prev_axis = _tf_extra(tf, "symPrevAxis") or "x"
    prev_about = _tf_extra(tf, "symPrevAbout") or "world"
    try:
        cmds.symmetricModelling(about=str(prev_about))
        cmds.symmetricModelling(axis=str(prev_axis))
        cmds.symmetricModelling(symmetry=bool(prev_sym))
    except Exception:
        try:
            cmds.symmetricModelling(symmetry=False)
        except Exception:
            pass
    if cmds.attributeQuery("symLive", node=tf, exists=True):
        cmds.setAttr(tf + ".symLive", False)
    if tf and cmds.objExists(tf):
        cmds.select(tf, replace=True)


# ---------------------------------------------------------------------------
# 左右をそろえる (頂点位置の完全対称化)
# ---------------------------------------------------------------------------

def symmetrize_positions(mesh, axis_index, keep_pos, offset, tol):
    """残す側の頂点位置を反対側へコピーして左右を一致させる。
    相方は鏡像位置に近い頂点をグリッドハッシュで探す。
    中央付近の頂点は対称面へスナップ。戻り値: (ペア数, 中央数)"""
    tol = max(tol, 1e-6)
    verts = cmds.ls(mesh + ".vtx[*]", flatten=True) or []
    positions = [cmds.pointPosition(v, world=True) for v in verts]

    grid = {}
    for i, pos in enumerate(positions):
        key = tuple(int(round(c / tol)) for c in pos)
        grid.setdefault(key, []).append(i)

    def _find_near(target):
        base_key = tuple(int(round(c / tol)) for c in target)
        best = None
        best_d2 = tol * tol
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    key = (base_key[0] + dx, base_key[1] + dy,
                           base_key[2] + dz)
                    for j in grid.get(key, ()):
                        pos = positions[j]
                        d2 = sum((pos[k] - target[k]) ** 2 for k in range(3))
                        if d2 <= best_d2:
                            best_d2 = d2
                            best = j
        return best

    keep_sign = 1.0 if keep_pos else -1.0
    pairs = 0
    centers = 0
    for i, vtx in enumerate(verts):
        pos = positions[i]
        signed = (pos[axis_index] - offset) * keep_sign
        if abs(pos[axis_index] - offset) <= tol:
            if abs(pos[axis_index] - offset) > 1e-9:
                new_pos = list(pos)
                new_pos[axis_index] = offset
                cmds.xform(vtx, worldSpace=True, translation=new_pos)
                centers += 1
            continue
        if signed < 0:
            continue
        target = list(pos)
        target[axis_index] = 2.0 * offset - pos[axis_index]
        j = _find_near(target)
        if j is not None and j != i:
            cmds.xform(verts[j], worldSpace=True, translation=target)
            pairs += 1
    return pairs, centers


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

WINDOW_NAME = "majimeruSymmetryWindow"
WINDOW_TITLE = "Symmetry (Max風) v10 - majimeru"


class SymmetryWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SymmetryWindow, self).__init__(parent)
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        # 常に最前面 (この1回だけ。setWindowFlags は上書き式)
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(350)
        self._updating = False
        self._build_ui()
        self._refresh_labels()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.state_label = QtWidgets.QLabel("現在の設定: ...")
        self.state_label.setWordWrap(True)
        layout.addWidget(self.state_label)

        self.target_label = QtWidgets.QLabel("対象: (未選択)")
        self.target_label.setWordWrap(True)
        layout.addWidget(self.target_label)

        axis_box = QtWidgets.QGroupBox("対称軸 (Mirror Axis)")
        axis_layout = QtWidgets.QHBoxLayout(axis_box)
        self.axis_buttons = []
        for i, label in enumerate(AXES):
            btn = QtWidgets.QRadioButton(label)
            btn.setChecked(i == 0)
            btn.toggled.connect(self._on_axis_changed)
            axis_layout.addWidget(btn)
            self.axis_buttons.append(btn)
        layout.addWidget(axis_box)

        side_box = QtWidgets.QGroupBox("残す側 (そろえる 用)")
        side_layout = QtWidgets.QHBoxLayout(side_box)
        self.keep_plus_btn = QtWidgets.QRadioButton("+ 側を残す")
        self.keep_plus_btn.setChecked(True)
        self.keep_minus_btn = QtWidgets.QRadioButton("- 側を残す")
        side_layout.addWidget(self.keep_plus_btn)
        side_layout.addWidget(self.keep_minus_btn)
        layout.addWidget(side_box)

        opt_layout = QtWidgets.QHBoxLayout()
        opt_layout.addWidget(QtWidgets.QLabel("そろえる しきい値:"))
        self.threshold_spin = QtWidgets.QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 100.0)
        self.threshold_spin.setDecimals(4)
        self.threshold_spin.setSingleStep(0.001)
        self.threshold_spin.setValue(0.01)
        opt_layout.addWidget(self.threshold_spin)
        layout.addLayout(opt_layout)

        self.center_line_check = QtWidgets.QCheckBox(
            "ON の時に真ん中に線を入れる")
        self.center_line_check.setChecked(True)
        layout.addWidget(self.center_line_check)

        self.slice_check = QtWidgets.QCheckBox(
            "ON の前に左右をそろえる (頂点位置のみ。形は壊しません)")
        self.slice_check.setChecked(True)
        layout.addWidget(self.slice_check)

        self.on_btn = QtWidgets.QPushButton("対称編集 ON")
        self.on_btn.setMinimumHeight(38)
        self.on_btn.clicked.connect(self._on_on)
        layout.addWidget(self.on_btn)

        self.off_btn = QtWidgets.QPushButton("対称編集 OFF")
        self.off_btn.clicked.connect(self._on_off)
        layout.addWidget(self.off_btn)

        self.sym_btn = QtWidgets.QPushButton("左右をそろえる (完全に対称化)")
        self.sym_btn.clicked.connect(self._on_symmetrize)
        layout.addWidget(self.sym_btn)

        note = QtWidgets.QLabel(
            "オブジェクトは1つのままです。モデルはセンター (原点) "
            "に置く前提。そろえる処理は頂点位置だけを動かし、"
            "トポロジもヒストリも変えません。ON の間は他のメッシュ"
            "にも対称編集が効きます (Maya 全体の設定のため)。")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.result_label = QtWidgets.QLabel(
            "【結果】まだ実行していません。メッシュを選んで"
            "「対称編集 ON」を押してください。")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

    # ----- UI <-> 設定 --------------------------------------------------
    def _ui_settings(self):
        axis = 0
        for i, btn in enumerate(self.axis_buttons):
            if btn.isChecked():
                axis = i
                break
        return {
            "axis":      axis,
            "keep_pos":  self.keep_plus_btn.isChecked(),
            "offset":    0.0,
            "slice":     self.slice_check.isChecked(),
            "center_line": self.center_line_check.isChecked(),
            "weld":      True,
            "threshold": float(self.threshold_spin.value()),
        }

    def _set_ui_settings(self, settings):
        self._updating = True
        try:
            self.axis_buttons[settings["axis"]].setChecked(True)
            (self.keep_plus_btn if settings["keep_pos"]
             else self.keep_minus_btn).setChecked(True)
            self.slice_check.setChecked(settings["slice"])
            if "center_line" in settings:
                self.center_line_check.setChecked(settings["center_line"])
            pass  # weld は v9 では使わない (互換のため読み捨て)
            self.threshold_spin.setValue(settings["threshold"])
        finally:
            self._updating = False

    def _refresh_labels(self):
        self.state_label.setText("現在の設定: " + _reflection_state_text())
        sel = cmds.ls(selection=True, long=True) or []
        live_tf = _resolve_live(sel[0]) if sel else None
        target = _selected_mesh_transform()
        if live_tf:
            self.target_label.setText(
                "対象: {} (対称編集 ON 中)".format(_short_name(live_tf)))
            self._set_ui_settings(_read_settings(live_tf))
        elif target:
            self.target_label.setText(
                "対象: {}".format(_short_name(target)))
        else:
            self.target_label.setText("対象: (メッシュを選択してください)")

    def _set_result(self, text, is_error=False):
        self.result_label.setText(text)
        self.result_label.setStyleSheet(
            "color: #ff6666;" if is_error else "color: #7dd87d;")
        if is_error:
            cmds.warning(text)
        else:
            print("[majimeru Symmetry] " + text)
        self._refresh_labels()

    def _on_axis_changed(self, *args):
        if self._updating:
            return
        sel = cmds.ls(selection=True, long=True) or []
        live_tf = _resolve_live(sel[0]) if sel else None
        if not live_tf:
            return
        settings = self._ui_settings()
        try:
            _write_settings(live_tf, settings)
            cmds.symmetricModelling(axis=AXIS_LETTERS[settings["axis"]])
        except Exception:
            pass
        self._refresh_labels()

    # ----- ボタン --------------------------------------------------------
    def _on_on(self):
        target = _selected_mesh_transform()
        if not target:
            self._set_result("メッシュを選択してから押してください。", True)
            return
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymmetryOn")
        try:
            mode, shells, cut_done = symmetry_on(target,
                                                 self._ui_settings())
        except Exception as exc:
            traceback.print_exc()
            self._set_result("ON に失敗: {}".format(exc), True)
        else:
            messages = {
                "prepped":   ("対称編集 ON: {} の左右をそろえてから"
                              " ON にしました。頂点を動かすと反対側も"
                              "動きます。"),
                "plain":     ("対称編集 ON: {}。頂点を動かすと反対側も"
                              "動きます。"),
                "reprepped": ("{} の左右をそろえ直しました"
                              " (対称編集は ON のまま)。"),
            }
            msg = messages[mode].format(_short_name(target))
            if cut_done:
                msg += " 真ん中に線を入れました。"
            if shells:
                msg += " (シェル数: {})".format(shells)
            if shells > 1:
                msg += ("【注意】シェルが複数あるメッシュです。"
                        "反射が効かない部分があるかもしれません。")
            self._set_result(msg, is_error=False)
        finally:
            cmds.undoInfo(closeChunk=True)

    def _on_off(self):
        sel = cmds.ls(selection=True, long=True) or []
        live_tf = _resolve_live(sel[0]) if sel else None
        if not live_tf:
            self._set_result(
                "対称編集 ON 中のメッシュを選択してください。", True)
            return
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymmetryOff")
        try:
            symmetry_off(live_tf)
        except Exception as exc:
            traceback.print_exc()
            self._set_result("OFF に失敗: {}".format(exc), True)
        else:
            self._set_result("対称編集 OFF (元の設定に戻しました)。")
        finally:
            cmds.undoInfo(closeChunk=True)

    def _on_symmetrize(self):
        target = _selected_mesh_transform()
        if not target:
            self._set_result("メッシュを選択してから押してください。", True)
            return
        live_tf = _resolve_live(target)
        settings = (_read_settings(live_tf) if live_tf
                    else self._ui_settings())
        cmds.undoInfo(openChunk=True, chunkName="majimeruSymmetrize")
        try:
            pairs, centers = symmetrize_positions(
                target, settings["axis"], settings["keep_pos"],
                settings["offset"], max(settings["threshold"], 0.0))
        except Exception as exc:
            traceback.print_exc()
            self._set_result("そろえるのに失敗: {}".format(exc), True)
        else:
            self._set_result(
                "左右をそろえました: ペア {} 組を一致、中央 {} 点を"
                "スナップ。".format(pairs, centers))
        finally:
            cmds.undoInfo(closeChunk=True)

_window = None


def show_ui():
    """ウィンドウを開く (既に開いていれば作り直す)"""
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

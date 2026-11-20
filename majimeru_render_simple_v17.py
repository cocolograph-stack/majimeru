# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_render_simple_v17  v17
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya Python tool
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

# -*- coding: utf-8 -*-
"""
majimeru_render_simple.py
「簡易レンダー設定」ツール V17  by majimeru
（V17: 最前面フラグが後続の setWindowFlags で上書きされて消えていた
　　　バグを修正 — 1行にまとめて指定）
（V10〜V13: 保存先フォルダの設定方法を確立（fileRule「images」）
　V14: ファイル名形式 name.#.ext の設定を追加
　V15: 連続レンダリングで、保存先の中にシーンファイル名の
　　　サブフォルダを作ってファイルごとに分けて保存するように
　V16: ウィンドウを常に最前面に表示するように）
（V7: 「レンダリング実行」を一番上に移動し黄色に
　V8: レイアウトを横並びに組み替えて縦を短くした
　V9: 「連続レンダリング実行」ボタンをオレンジ色にした）
（V2: モーションブラー / V3: 出力フォルダ初期値の堅牢化
　V4: 複数シーンファイルの連続レンダリングを追加
　V5: 設定を項目ごとに個別適用に変更し、結果を項目別に表示。
　　　解像度は書き込み後に読み戻して確認
　V6: サイズの初期値を 1280×720 に、解像度(dpi)欄を追加（初期値 72））

Maya の Render Settings でよく使う項目だけを、小さなウィンドウにまとめた
初心者向けの簡易ツールです。

できること:
- レンダラー選択（シーンで使えるものだけ表示）
- レンダリングカメラの選択
- フレーム範囲（単一フレーム／範囲／By frame ステップ）
- 画像フォーマット（PNG / JPEG / EXR / TIFF / Targa）
- 解像度（数値入力＋プリセット 1280x720 / 1920x1080 / 3840x2160）
- 出力フォルダとファイル名プレフィックス
- フレームパディング（桁数）
- 「設定を反映」: defaultRenderGlobals 等へ書き込み
- 「レンダリング実行」: 反映した上でレンダリング
    - 単一フレーム … cmds.render() でレンダービューに表示
    - 範囲 … cmds.RenderSequence() でシーケンスレンダリング（ファイル出力）

注意:
- Arnold の場合、画像フォーマットは defaultRenderGlobals.imageFormat では
  なく defaultArnoldDriver.aiTranslator で決まります。このツールは両方を
  設定します（ドライバノードが無い場合はスキップして案内文に残します）。
- 出力フォルダはワークスペースの fileRule「images」に書き込みます
  （プロジェクトの画像出力先が変わります）。

起動方法:
    import majimeru_render_simple
    majimeru_render_simple.show_ui()

対応: Maya 2022 以降想定（PySide6 → PySide2 フォールバック）
"""

import os

import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:  # Maya 2024 以前
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance


WINDOW_TITLE = u"簡易レンダー設定  - majimeru"
WINDOW_OBJECT_NAME = "MajimeruRenderSimpleWindow"

# defaultRenderGlobals.imageFormat の値（Maya 標準）
IMAGE_FORMATS = [
    (u"PNG", 32, "png"),
    (u"JPEG", 8, "jpg"),
    (u"OpenEXR", 40, "exr"),
    (u"TIFF", 3, "tif"),
    (u"Targa", 19, "tga"),
]

# レンダラー候補: (currentRenderer の値, 表示名, 読み込み判定に使うプラグイン名 or None)
RENDERER_CANDIDATES = [
    ("mayaSoftware", u"Maya Software", None),
    ("mayaHardware2", u"Maya Hardware 2.0", None),
    ("arnold", u"Arnold", "mtoa"),
    ("vray", u"V-Ray", "vrayformaya"),
    ("redshift", u"Redshift", "redshift4maya"),
    ("renderman", u"RenderMan", "RenderMan_for_Maya"),
]

RESOLUTION_PRESETS = [
    (u"1280 × 720 (HD)", 1280, 720),
    (u"1920 × 1080 (Full HD)", 1920, 1080),
    (u"3840 × 2160 (4K)", 3840, 2160),
    (u"960 × 540", 960, 540),
]


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _available_renderers():
    """シーンで使えるレンダラーだけを返す [(値, 表示名), ...]"""
    result = []
    for value, label, plugin in RENDERER_CANDIDATES:
        if plugin is None:
            result.append((value, label))
            continue
        try:
            if cmds.pluginInfo(plugin, query=True, loaded=True):
                result.append((value, label))
        except Exception:
            pass
    # 現在のレンダラーが候補に無ければ（プラグイン未読込など）先頭に追加
    try:
        current = cmds.getAttr("defaultRenderGlobals.currentRenderer")
    except Exception:
        current = None
    if current and current not in [v for v, _ in result]:
        result.insert(0, (current, current))
    return result


def _list_cameras():
    """[(トランスフォーム名, レンダリング可能か), ...] 既定カメラも含む"""
    cams = []
    for shape in cmds.ls(type="camera") or []:
        parent = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if not parent:
            continue
        name = parent[0]
        try:
            renderable = bool(cmds.getAttr(shape + ".renderable"))
        except Exception:
            renderable = False
        cams.append((name, renderable))
    return cams


class RenderSimpleWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(RenderSimpleWindow, self).__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        # 常に最前面（WindowStaysOnTopHint）も同じ行で指定する
        # ※ setWindowFlags は上書き式なので、分けると前の指定が消える
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(430)
        self._build_ui()
        self._load_current_settings()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setSpacing(5)
        main.setContentsMargins(8, 8, 8, 8)

        # --- レンダリング実行（一番上・黄色） ---
        self.render_btn = QtWidgets.QPushButton(u"レンダリング実行")
        self.render_btn.setMinimumHeight(40)
        self.render_btn.setStyleSheet(
            "QPushButton { background-color: #ffd83d; color: #000;"
            " font-weight: bold; font-size: 15px; border: 1px solid #a8860a;"
            " border-radius: 4px; }"
            "QPushButton:pressed { background-color: #e0b62a; }"
        )
        self.render_btn.clicked.connect(self.render_now)
        main.addWidget(self.render_btn)

        # --- レンダラー | カメラ（横並び） ---
        row = QtWidgets.QHBoxLayout()
        box = QtWidgets.QGroupBox(u"レンダラー")
        lay = QtWidgets.QVBoxLayout(box)
        self.renderer_combo = QtWidgets.QComboBox()
        for value, label in _available_renderers():
            self.renderer_combo.addItem(label, value)
        lay.addWidget(self.renderer_combo)
        row.addWidget(box)
        box = QtWidgets.QGroupBox(u"カメラ")
        lay = QtWidgets.QHBoxLayout(box)
        self.camera_combo = QtWidgets.QComboBox()
        self._refresh_cameras()
        lay.addWidget(self.camera_combo, 1)
        reload_btn = QtWidgets.QPushButton(u"更新")
        reload_btn.clicked.connect(self._refresh_cameras)
        lay.addWidget(reload_btn)
        row.addWidget(box, 1)
        main.addLayout(row)

        # --- フレーム範囲（1行に圧縮） ---
        box = QtWidgets.QGroupBox(u"フレーム範囲")
        lay = QtWidgets.QHBoxLayout(box)
        self.mode_single = QtWidgets.QRadioButton(u"単一")
        self.mode_range = QtWidgets.QRadioButton(u"範囲")
        self.mode_single.setChecked(True)
        lay.addWidget(self.mode_single)
        lay.addWidget(self.mode_range)
        self.start_spin = QtWidgets.QSpinBox()
        self.start_spin.setRange(-100000, 100000)
        self.start_spin.setValue(1)
        self.end_spin = QtWidgets.QSpinBox()
        self.end_spin.setRange(-100000, 100000)
        self.end_spin.setValue(48)
        lay.addWidget(QtWidgets.QLabel(u"開始:"))
        lay.addWidget(self.start_spin)
        lay.addWidget(QtWidgets.QLabel(u"終了:"))
        lay.addWidget(self.end_spin)
        lay.addWidget(QtWidgets.QLabel(u"By:"))
        self.by_spin = QtWidgets.QSpinBox()
        self.by_spin.setRange(1, 1000)
        self.by_spin.setValue(1)
        lay.addWidget(self.by_spin)
        lay.addStretch(1)
        self.mode_single.toggled.connect(self._update_mode_enabled)
        self.mode_range.toggled.connect(self._update_mode_enabled)
        main.addWidget(box)

        # --- 画像 | モーションブラー（横並び） ---
        row = QtWidgets.QHBoxLayout()
        box = QtWidgets.QGroupBox(u"画像")
        lay = QtWidgets.QFormLayout(box)
        self.format_combo = QtWidgets.QComboBox()
        for label, _code, _ext in IMAGE_FORMATS:
            self.format_combo.addItem(label)
        lay.addRow(u"形式:", self.format_combo)
        self.padding_spin = QtWidgets.QSpinBox()
        self.padding_spin.setRange(1, 10)
        self.padding_spin.setValue(4)
        lay.addRow(u"パディング桁:", self.padding_spin)
        self.nameext_check = QtWidgets.QCheckBox(u"name.#.ext にする（推奨）")
        self.nameext_check.setChecked(True)
        lay.addRow(u"ファイル名:", self.nameext_check)
        row.addWidget(box)
        box = QtWidgets.QGroupBox(u"モーションブラー")
        lay = QtWidgets.QVBoxLayout(box)
        self.mb_check = QtWidgets.QCheckBox(u"有効にする")
        lay.addWidget(self.mb_check)
        mb_row = QtWidgets.QHBoxLayout()
        mb_row.addWidget(QtWidgets.QLabel(u"長さ:"))
        self.mb_length_spin = QtWidgets.QDoubleSpinBox()
        self.mb_length_spin.setRange(0.0, 2.0)
        self.mb_length_spin.setSingleStep(0.1)
        self.mb_length_spin.setValue(0.5)
        mb_row.addWidget(self.mb_length_spin)
        mb_row.addWidget(QtWidgets.QLabel(u"（Arnoldのみ）"))
        mb_row.addStretch(1)
        lay.addLayout(mb_row)
        self.mb_check.toggled.connect(self.mb_length_spin.setEnabled)
        self.mb_length_spin.setEnabled(False)
        row.addWidget(box, 1)
        main.addLayout(row)

        # --- 解像度 ---
        box = QtWidgets.QGroupBox(u"解像度")
        lay = QtWidgets.QVBoxLayout(box)
        size_row = QtWidgets.QHBoxLayout()
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(16, 16384)
        self.width_spin.setValue(1280)
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(16, 16384)
        self.height_spin.setValue(720)
        size_row.addWidget(QtWidgets.QLabel(u"幅:"))
        size_row.addWidget(self.width_spin)
        size_row.addWidget(QtWidgets.QLabel(u"高さ:"))
        size_row.addWidget(self.height_spin)
        size_row.addWidget(QtWidgets.QLabel(u"dpi:"))
        self.dpi_spin = QtWidgets.QSpinBox()
        self.dpi_spin.setRange(1, 1200)
        self.dpi_spin.setValue(72)
        size_row.addWidget(self.dpi_spin)
        size_row.addStretch(1)
        lay.addLayout(size_row)
        preset_row = QtWidgets.QHBoxLayout()
        for label, w, h in RESOLUTION_PRESETS:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda _=False, w=w, h=h: self._set_resolution(w, h))
            preset_row.addWidget(btn)
        lay.addLayout(preset_row)
        main.addWidget(box)

        # --- 出力 ---
        box = QtWidgets.QGroupBox(u"出力")
        lay = QtWidgets.QFormLayout(box)
        folder_row = QtWidgets.QHBoxLayout()
        self.folder_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton(u"参照...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse_btn)
        lay.addRow(u"保存先:", folder_row)
        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText(u"例: shot01_beauty（空欄でも可）")
        lay.addRow(u"プレフィックス:", self.prefix_edit)
        main.addWidget(box)

        # --- 複数ファイル連続レンダリング ---
        box = QtWidgets.QGroupBox(u"複数ファイル連続レンダリング")
        lay = QtWidgets.QVBoxLayout(box)
        note = QtWidgets.QLabel(
            u".ma / .mb を並べて1つずつ開いてレンダリング。今のシーンは閉じるので先に保存を。"
            u"単一の時は「開始」のフレームを描画。プレフィックスにはファイル名が付きます。"
            u"保存先の中にシーンファイル名のフォルダを作って分けて保存します。"
        )
        note.setWordWrap(True)
        lay.addWidget(note)
        self.file_list = QtWidgets.QListWidget()
        self.file_list.setFixedHeight(52)
        lay.addWidget(self.file_list)
        file_btn_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton(u"ファイルを追加")
        add_btn.clicked.connect(self._add_files)
        del_btn = QtWidgets.QPushButton(u"選択を削除")
        del_btn.clicked.connect(self._remove_files)
        clear_btn = QtWidgets.QPushButton(u"全部消す")
        clear_btn.clicked.connect(lambda: self.file_list.clear())
        file_btn_row.addWidget(add_btn)
        file_btn_row.addWidget(del_btn)
        file_btn_row.addWidget(clear_btn)
        lay.addLayout(file_btn_row)
        self.multi_render_btn = QtWidgets.QPushButton(u"連続レンダリング実行")
        self.multi_render_btn.setMinimumHeight(34)
        self.multi_render_btn.setStyleSheet(
            "QPushButton { background-color: #ff9f2e; color: #000;"
            " font-weight: bold; border: 1px solid #a35f08;"
            " border-radius: 4px; }"
            "QPushButton:pressed { background-color: #e08616; }"
        )
        self.multi_render_btn.clicked.connect(self.render_multiple)
        lay.addWidget(self.multi_render_btn)
        main.addWidget(box)

        # --- 設定を反映 ---
        self.apply_btn = QtWidgets.QPushButton(u"設定を反映")
        self.apply_btn.clicked.connect(self.apply_settings)
        main.addWidget(self.apply_btn)

        # --- 案内文 ---
        self.status_label = QtWidgets.QLabel(
            u"「設定を反映」で Render Settings に書き込みます。\n"
            u"「レンダリング実行」は、反映した上でそのままレンダリングします。"
        )
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #9fc6ee;")
        main.addWidget(self.status_label)

        self._update_mode_enabled()

    # ------------------------------------------------------------- helpers
    def _set_status(self, text):
        self.status_label.setText(text)

    def _set_resolution(self, w, h):
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)

    def _update_mode_enabled(self):
        is_range = self.mode_range.isChecked()
        self.start_spin.setEnabled(is_range)
        self.end_spin.setEnabled(is_range)
        self.by_spin.setEnabled(is_range)

    def _refresh_cameras(self):
        current = self.camera_combo.currentData() if self.camera_combo.count() else None
        self.camera_combo.clear()
        first_renderable = 0
        for i, (name, renderable) in enumerate(_list_cameras()):
            short = name.split("|")[-1]
            label = short + (u"（レンダリング可能）" if renderable else u"")
            self.camera_combo.addItem(label, name)
            if renderable and first_renderable == 0:
                first_renderable = i
        if current:
            idx = self.camera_combo.findData(current)
            if idx >= 0:
                self.camera_combo.setCurrentIndex(idx)
                return
        self.camera_combo.setCurrentIndex(first_renderable)

    def _browse_folder(self):
        start = self.folder_edit.text() or os.path.expanduser("~")
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, u"保存先フォルダを選ぶ", start)
        if folder:
            self.folder_edit.setText(folder)

    def _load_current_settings(self):
        """シーンの現在の Render Settings を UI に読み込む"""
        notes = []
        try:
            current = cmds.getAttr("defaultRenderGlobals.currentRenderer")
            idx = self.renderer_combo.findData(current)
            if idx >= 0:
                self.renderer_combo.setCurrentIndex(idx)
        except Exception:
            pass
        try:
            start = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
            end = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
            by = int(cmds.getAttr("defaultRenderGlobals.byFrameStep"))
            anim = bool(cmds.getAttr("defaultRenderGlobals.animation"))
            self.start_spin.setValue(start)
            self.end_spin.setValue(end)
            self.by_spin.setValue(max(1, by))
            if anim:
                self.mode_range.setChecked(True)
        except Exception:
            pass
        try:
            fmt = int(cmds.getAttr("defaultRenderGlobals.imageFormat"))
            for i, (_label, code, _ext) in enumerate(IMAGE_FORMATS):
                if code == fmt:
                    self.format_combo.setCurrentIndex(i)
                    break
        except Exception:
            pass
        try:
            self.padding_spin.setValue(int(cmds.getAttr("defaultRenderGlobals.extensionPadding")))
        except Exception:
            pass
        try:
            self.width_spin.setValue(int(cmds.getAttr("defaultResolution.width")))
            self.height_spin.setValue(int(cmds.getAttr("defaultResolution.height")))
        except Exception:
            pass
        try:
            self.dpi_spin.setValue(int(cmds.getAttr("defaultResolution.resolution")))
        except Exception:
            pass
        # モーションブラーの現在値（取れるレンダラーだけ）
        try:
            if cmds.objExists("defaultArnoldRenderOptions"):
                self.mb_check.setChecked(bool(cmds.getAttr("defaultArnoldRenderOptions.motion_blur_enable")))
                self.mb_length_spin.setValue(float(cmds.getAttr("defaultArnoldRenderOptions.motion_blur_length")))
            else:
                self.mb_check.setChecked(bool(cmds.getAttr("defaultRenderGlobals.motionBlur")))
        except Exception:
            pass
        try:
            prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix") or ""
            self.prefix_edit.setText(prefix)
        except Exception:
            pass
        # 出力フォルダの初期値: プロジェクトの images ルール → 取れなければ
        # プロジェクト直下の images フォルダを標準として入れる（エラー表示はしない）
        folder = ""
        try:
            root = cmds.workspace(query=True, rootDirectory=True)
        except Exception:
            root = ""
        if root:
            images_rule = ""
            try:
                images_rule = cmds.workspace(query=True, fileRuleEntry="images") or ""
            except Exception:
                images_rule = ""
            if images_rule:
                folder = images_rule
                if not os.path.isabs(folder):
                    folder = os.path.join(root, folder)
            else:
                folder = os.path.join(root, "images")
        if folder:
            self.folder_edit.setText(os.path.normpath(folder))
        self._update_mode_enabled()
        if notes:
            self._set_status(u"\n".join(notes))

    # ---------------------------------------------------------------- core
    def collect_settings(self):
        fmt_label, fmt_code, fmt_ext = IMAGE_FORMATS[self.format_combo.currentIndex()]
        return {
            "renderer": self.renderer_combo.currentData(),
            "renderer_label": self.renderer_combo.currentText(),
            "camera": self.camera_combo.currentData(),
            "camera_label": self.camera_combo.currentText(),
            "single": self.mode_single.isChecked(),
            "start": self.start_spin.value(),
            "end": self.end_spin.value(),
            "by": self.by_spin.value(),
            "format_label": fmt_label,
            "format_code": fmt_code,
            "format_ext": fmt_ext,
            "motion_blur": self.mb_check.isChecked(),
            "mb_length": self.mb_length_spin.value(),
            "padding": self.padding_spin.value(),
            "name_sharp_ext": self.nameext_check.isChecked(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "dpi": self.dpi_spin.value(),
            "folder": self.folder_edit.text().strip(),
            "prefix": self.prefix_edit.text().strip(),
        }

    def apply_settings(self, batch=False, prefix_override=None, folder_override=None):
        """UI の内容を Maya の Render Settings に書き込む。(ok, messages)

        V5: 設定ごとに個別に try で守り、1つ失敗しても他は続ける。
        結果は項目ごとに案内文へ出す。解像度は書き込み後に読み戻して確認する。
        batch=True の時は連続レンダリング用（カメラ無しは各ファイルの設定を使用、
        単一フレームは「開始」の数字、prefix_override でプレフィックス差し替え）。
        """
        s = self.collect_settings()
        msgs = []
        if not s["camera"] and not batch:
            msgs.append(u"カメラが選ばれていません")
            self._set_status(u"\n".join(msgs))
            return False, msgs

        def _try(label, func):
            try:
                func()
                return True
            except Exception as exc:
                msgs.append(u"{0}: × 失敗（{1}）".format(label, exc))
                return False

        cmds.undoInfo(openChunk=True, chunkName="MajimeruRenderSimpleApply")
        try:
            # レンダラー
            if _try(u"レンダラー", lambda: cmds.setAttr(
                    "defaultRenderGlobals.currentRenderer", s["renderer"], type="string")):
                msgs.append(u"レンダラー: {0}".format(s["renderer_label"]))

            # カメラ: 選んだものだけ renderable にする
            # （参照ファイル由来などでロックされたカメラは個別にスキップ）
            if s["camera"] and cmds.objExists(s["camera"]):
                skipped = []

                def _cameras():
                    for shape in cmds.ls(type="camera") or []:
                        parent = cmds.listRelatives(shape, parent=True, fullPath=True) or []
                        if not parent:
                            continue
                        try:
                            cmds.setAttr(shape + ".renderable", parent[0] == s["camera"])
                        except Exception:
                            skipped.append(parent[0].split("|")[-1])

                _cameras()
                msgs.append(u"カメラ: {0}".format(s["camera_label"]))
                if skipped:
                    msgs.append(u"カメラ: ロック等で変更できなかったもの: {0}".format(u", ".join(skipped)))
            elif batch:
                msgs.append(u"カメラ: 各ファイルの設定をそのまま使用")

            # フレーム範囲
            def _frames():
                if s["single"]:
                    cur = s["start"] if batch else cmds.currentTime(query=True)
                    cmds.setAttr("defaultRenderGlobals.animation", 0)
                    cmds.setAttr("defaultRenderGlobals.startFrame", cur)
                    cmds.setAttr("defaultRenderGlobals.endFrame", cur)
                    msgs.append(u"フレーム: 現在のフレーム {0:g} のみ".format(cur))
                else:
                    cmds.setAttr("defaultRenderGlobals.animation", 1)
                    cmds.setAttr("defaultRenderGlobals.startFrame", s["start"])
                    cmds.setAttr("defaultRenderGlobals.endFrame", s["end"])
                    cmds.setAttr("defaultRenderGlobals.byFrameStep", s["by"])
                    msgs.append(u"フレーム: {0} 〜 {1}（{2} フレームおき）".format(s["start"], s["end"], s["by"]))
                cmds.setAttr("defaultRenderGlobals.extension", 1)

            _try(u"フレーム範囲", _frames)

            # ファイル名形式: 範囲レンダリングの時は name.#.ext にそろえる
            # （Render Settings の Frame/Animation ext と同じ処理を呼ぶ）
            if s["name_sharp_ext"] and not s["single"]:
                if _try(u"ファイル名形式", lambda: mel.eval('setMayaSoftwareFrameExt("3", 0)')):
                    msgs.append(u"ファイル名形式: name.#.ext")

            # 画像フォーマット
            if _try(u"画像フォーマット", lambda: cmds.setAttr(
                    "defaultRenderGlobals.imageFormat", s["format_code"])):
                msgs.append(u"画像フォーマット: {0}".format(s["format_label"]))
            if s["renderer"] == "arnold" and cmds.objExists("defaultArnoldDriver"):
                _try(u"Arnold ドライバ形式", lambda: cmds.setAttr(
                    "defaultArnoldDriver.aiTranslator", s["format_ext"], type="string"))

            # モーションブラー（レンダラーごとに書き込み先が違う）
            if s["renderer"] == "arnold" and cmds.objExists("defaultArnoldRenderOptions"):
                def _mb_arnold():
                    cmds.setAttr("defaultArnoldRenderOptions.motion_blur_enable", 1 if s["motion_blur"] else 0)
                    if s["motion_blur"]:
                        cmds.setAttr("defaultArnoldRenderOptions.motion_blur_length", s["mb_length"])

                if _try(u"モーションブラー", _mb_arnold):
                    msgs.append(u"モーションブラー: {0}".format(
                        u"ON（長さ {0}）".format(s["mb_length"]) if s["motion_blur"] else u"OFF"))
            elif s["renderer"] == "mayaSoftware":
                if _try(u"モーションブラー", lambda: cmds.setAttr(
                        "defaultRenderGlobals.motionBlur", 1 if s["motion_blur"] else 0)):
                    msgs.append(u"モーションブラー: {0}（Software は ON/OFF のみ）".format(
                        u"ON" if s["motion_blur"] else u"OFF"))
            else:
                msgs.append(u"モーションブラー: このレンダラーでは自動設定未対応（手動で設定してください）")

            # パディング
            _try(u"フレームパディング", lambda: cmds.setAttr(
                "defaultRenderGlobals.extensionPadding", s["padding"]))

            # 解像度（書き込み後に読み戻して確認）
            def _resolution():
                cmds.setAttr("defaultResolution.width", s["width"])
                cmds.setAttr("defaultResolution.height", s["height"])
                try:
                    cmds.setAttr(
                        "defaultResolution.deviceAspectRatio",
                        float(s["width"]) / float(s["height"]),
                    )
                except Exception:
                    pass

            if _try(u"解像度", _resolution):
                try:
                    actual_w = int(cmds.getAttr("defaultResolution.width"))
                    actual_h = int(cmds.getAttr("defaultResolution.height"))
                    if actual_w == s["width"] and actual_h == s["height"]:
                        msgs.append(u"解像度: {0} × {1} に設定（確認済み）".format(actual_w, actual_h))
                    else:
                        msgs.append(u"解像度: 書き込みましたが実際は {0} × {1} でした（Render Settings 側で固定されている可能性）".format(actual_w, actual_h))
                except Exception:
                    msgs.append(u"解像度: {0} × {1} に設定".format(s["width"], s["height"]))
            if _try(u"解像度(dpi)", lambda: cmds.setAttr("defaultResolution.resolution", s["dpi"])):
                msgs.append(u"解像度(dpi): {0}".format(s["dpi"]))

            # プレフィックス
            prefix_value = prefix_override if prefix_override is not None else s["prefix"]
            _try(u"プレフィックス", lambda: cmds.setAttr(
                "defaultRenderGlobals.imageFilePrefix", prefix_value, type="string"))

            # 出力フォルダ: 保存先の設定は fileRule「images」
            # （fileRuleEntry は読み取り専用、renderType は現行 Maya で廃止され
            # 　fileRule に統合された — 実機の警告で確認済み）
            # 設定 → workspace.mel に保存 → 読み戻して確認
            folder_value = folder_override if folder_override is not None else s["folder"]
            if folder_value:
                folder = folder_value.replace("\\", "/")

                def _set_folder():
                    cmds.workspace(fileRule=["images", folder])
                    try:
                        cmds.workspace(saveWorkspace=True)
                    except Exception:
                        pass

                if _try(u"保存先", _set_folder):
                    shown = folder
                    try:
                        rule = cmds.workspace(query=True, fileRuleEntry="images") or ""
                        if rule:
                            if os.path.isabs(rule):
                                shown = os.path.normpath(rule)
                            else:
                                root = cmds.workspace(query=True, rootDirectory=True)
                                shown = os.path.normpath(os.path.join(root, rule))
                    except Exception:
                        pass
                    msgs.append(u"保存先: {0}（設定を確認済み）".format(shown))

            msgs.append(u"―― 設定の反映が終わりました ――")
        finally:
            cmds.undoInfo(closeChunk=True)

        self._set_status(u"\n".join(msgs))
        return True, msgs

    def render_now(self):
        s = self.collect_settings()
        if s["single"]:
            desc = u"現在のフレームをレンダービューでレンダリングします。"
        else:
            desc = u"{0} 〜 {1} フレームをシーケンスレンダリングします。\n保存先: {2}\n時間がかかる場合があります。".format(
                s["start"], s["end"], s["folder"] or u"（プロジェクトの images）"
            )
        answer = QtWidgets.QMessageBox.question(
            self,
            u"レンダリング実行の確認",
            desc + u"\nよろしいですか？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            self._set_status(u"レンダリングを中止しました")
            return

        ok, _msgs = self.apply_settings()
        if not ok:
            return

        try:
            if s["single"]:
                # レンダービューを開いて現在のフレームを描く
                mel.eval("RenderViewWindow")
                cmds.render(s["camera"])
                self._set_status(u"レンダリングしました（レンダービューを確認してください）")
            else:
                try:
                    cmds.RenderSequence()
                except Exception:
                    mel.eval("RenderSequence")
                self._set_status(u"シーケンスレンダリングを実行しました（保存先フォルダを確認してください）")
        except Exception as exc:
            self._set_status(u"レンダリングでエラーが出ました: {0}".format(exc))


    # -------------------------------------------------- 複数ファイル連続
    def _add_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, u"レンダリングするシーンファイルを選ぶ", "",
            u"Maya シーン (*.ma *.mb);;すべてのファイル (*)",
        )
        existing = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        for f in files:
            if f not in existing:
                self.file_list.addItem(f)

    def _remove_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def render_multiple(self):
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not files:
            self._set_status(u"ファイルが1つも入っていません。「ファイルを追加」で選んでください")
            return
        # 未保存の変更があるシーンは閉じられないので先に止める
        try:
            if cmds.file(query=True, modified=True):
                QtWidgets.QMessageBox.warning(
                    self, u"保存してください",
                    u"今開いているシーンに未保存の変更があります。\n"
                    u"連続レンダリングではシーンを開き直すので、先に保存してから実行してください。",
                )
                return
        except Exception:
            pass

        s = self.collect_settings()
        if s["single"]:
            frame_desc = u"単一フレーム（{0} フレーム目）".format(s["start"])
        else:
            frame_desc = u"{0} 〜 {1} フレーム（{2} おき）".format(s["start"], s["end"], s["by"])
        answer = QtWidgets.QMessageBox.question(
            self,
            u"連続レンダリングの確認",
            u"{0} 個のファイルを順番にレンダリングします。\n"
            u"フレーム: {1}\n保存先: {2}\n\n"
            u"実行中は Maya が操作できなくなります。終わるまで待ってください。\n"
            u"よろしいですか？".format(len(files), frame_desc, s["folder"] or u"（プロジェクトの images）"),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            self._set_status(u"連続レンダリングを中止しました")
            return

        # 実行前のシーンを覚えておき、終わったら開き直す
        original_scene = ""
        try:
            original_scene = cmds.file(query=True, sceneName=True) or ""
        except Exception:
            original_scene = ""

        results = []
        for i, path in enumerate(files):
            base = os.path.splitext(os.path.basename(path))[0]
            self._set_status(u"連続レンダリング中: {0} / {1} 件目\n{2}".format(i + 1, len(files), path))
            QtWidgets.QApplication.processEvents()
            try:
                cmds.file(path, open=True, force=True)
                # プレフィックス: 指定があれば「指定_ファイル名」、無ければファイル名
                prefix = (s["prefix"] + "_" + base) if s["prefix"] else base
                # 保存先: 指定フォルダの中に、シーンファイル名のサブフォルダを作って分ける
                base_folder = s["folder"]
                if not base_folder:
                    try:
                        root = cmds.workspace(query=True, rootDirectory=True)
                        rule = cmds.workspace(query=True, fileRuleEntry="images") or "images"
                        base_folder = rule if os.path.isabs(rule) else os.path.join(root, rule)
                    except Exception:
                        base_folder = ""
                folder_override = None
                if base_folder:
                    sub_folder = os.path.join(base_folder, base)
                    try:
                        if not os.path.isdir(sub_folder):
                            os.makedirs(sub_folder)
                        folder_override = sub_folder
                    except Exception:
                        folder_override = None
                ok, _msgs = self.apply_settings(
                    batch=True, prefix_override=prefix, folder_override=folder_override)
                if not ok:
                    results.append(u"× {0}: 設定の反映に失敗".format(base))
                    continue
                try:
                    cmds.RenderSequence()
                except Exception:
                    mel.eval("RenderSequence")
                results.append(u"○ {0}: 完了".format(base))
            except Exception as exc:
                results.append(u"× {0}: エラー（{1}）".format(base, exc))

        # 元のシーンに戻る
        if original_scene and os.path.exists(original_scene):
            try:
                cmds.file(original_scene, open=True, force=True)
            except Exception:
                pass

        self._set_status(u"連続レンダリングが終わりました。\n" + u"\n".join(results))


def show_ui():
    """既存ウィンドウを閉じてから開く"""
    app = QtWidgets.QApplication.instance()
    if app:
        for widget in app.topLevelWidgets():
            if widget.objectName() == WINDOW_OBJECT_NAME:
                widget.close()
                widget.deleteLater()
    window = RenderSimpleWindow(parent=_maya_main_window())
    window.show()
    return window


if __name__ == "__main__":
    show_ui()

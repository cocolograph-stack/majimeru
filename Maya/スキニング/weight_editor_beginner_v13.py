# -*- coding: utf-8 -*-
"""
やさしいウエイト調整 (BeginnerWeightEditor) v13 - 初心者向け大改造版
majimeru

hybrid_weight_editor_fixed の計算ロジック（配分・ホールド・スムーズ・
スケルトン絞り込み・高速化）はそのままに、UIと案内を初心者向けに総入れ替え。

[やさしさのポイント]
- ウエイトは全部「%」表示（0.5 ではなく 50%）
- 専門用語をやさしい言葉に（ホールド→固定、インフルエンス→ジョイント）
- 画面上部に「いま何を選んでいて、次に何をすればいいか」の案内文を常時表示
- スムーズは「弱く／ふつう／強く」のプリセットボタン（数値設定は
  「細かく設定する」の中）
- 「ポーズを元に戻す」ボタンを画面の一番上に配置（v4〜）
- 全ての入力欄に名前ラベルを付け、ボタンは大きめに

[v2 で足したもの]
SDDウェイトツール（SunDongDong v4.4.7）の良い所だけを取り入れた。
元のSDDは古い作りで、存在しないノード名の決め打ち・比較ミス・
スムーズボタンの未実装などバグが複数あったため、機能の考え方だけを
このツールの作りで実装し直してある。
- 「お助け」ボタン行：選択を広げる／狭める、ウエイトのコピー／貼り付け

[v3 で足したもの]（2026-11-24 マジメルの要望）
- バインドの「1つの頂点に影響する骨の最大数」の初期値を 4 → 3 に変更
- 「ポーズを元に戻す（コントローラー全部ゼロ）」ボタンを追加。
  コントローラーを選ばなくても、名前（CTRL等）から自動で全部見つけて、
  移動と回転を全部 0 に戻す。押すだけでバインド時のポーズ（Tスタンス）に戻る。
  ロック中・接続済みのチャンネルは触らずに飛ばす。Ctrl+Z でも戻せる。

[v4 で直したもの]（2026-11-24 マジメルの指摘）
- 「ポーズを元に戻す」ボタンの位置が分かりにくかったので、タブの中から
  画面の一番上（「もとに戻す」「やり直し」の隣）へ移動した。
  どのタブを開いていても常に見える・押せる。結果の案内も上の案内文に出る。

[v5 で直したもの]（2026-11-24 マジメルの指摘）
- 上部の「もとに戻す」「やり直し」ボタンを削除した。Maya本体の
  Ctrl+Z / Ctrl+Y で同じことができるため（学生にはそちらを覚えてもらう）。

[v6 で直したもの]（2026-11-24 マジメルの要望）
- Mayaの画面に組み込める「ドッキング対応」にした
  （MayaQWidgetDockableMixin を使用）。起動すると浮いたパネルで開き、
  端へドラッグするとビューポートの横などにくっつく。外して浮かせることもできる。
  それに伴い「常に手前に表示」は廃止（組み込むのが目的なので）。

[v13 で直したもの]（2026-11-24 マジメルの報告：ウインドウが出ない）
- v11 の「土台ごと差し替え」が原因だった。QScrollArea.setWidget() は
  前の土台を自分で消す仕様で、その後にこちらがもう一度消そうとして
  「already deleted」エラーになり、起動が止まっていた。
  前の土台には触らないようにした（setWidget に任せる）。
- ついでに、起動時の読み込みでエラーが出ても、ウインドウ自体は
  開くようにした（エラーはコンソールに出る）。

[v12 で直したもの]（2026-11-24 マジメルの報告：キャラを選ぶとエラー）
- 「Internal C++ object (QCheckBox) already deleted」対策。
  スクリプトを再実行したり、ドッキングしたパネルを閉じたりすると、
  古いウインドウの実体（Qt側）だけ消えて、選択変更の監視（scriptJob）が
  残ることがある。その状態で選択が変わると、消えた部品を触ってエラーに
  なっていた。監視側で「実体が消えている」と分かったら、自分で監視を
  止めるようにした（エラーで止まらず、静かに片付く）。

[v11 で直したもの]（2026-11-24 マジメルの指摘「更新ボタンを押してもすぐ反応しない」）
- 「更新」を押した瞬間に「読み込み中…」と出して、ボタンも押せなくする
  （反応が無いように見えるのを解消）。
- カードの作り方を「土台ごと作って差し替え」に変えた。今までは
  表示中のレイアウトにカードを1個足すたびに配置計算が全部やり直しに
  なっていて、カード数×カード数で重くなっていた。
- 「頂点ごと」タブのカード表示は最大30個まで（それ以上選んでいる時は
  注意書きを出す）。全部まとめて直す作業は「まとめて」タブが速い。

[v10 で直したもの]（2026-11-24 マジメルの指摘「1秒ほどラグがある」）
- ウエイトの読み取りを OpenMaya API（MFnSkinCluster.getWeights）で
  全頂点まとめて1回に変えた（今までは頂点ごとに skinPercent を呼んでいた）。
  APIが使えない場面では今までの方式に自動で戻る（フォールバック付き）。
- 骨の構成（インフルエンス一覧・骨格・表示名）を毎回調べ直さず、
  ツールを開いている間は使い回すようにした。ジョイントを足した時と
  バインドし直した時だけ調べ直す。

[v9 で直したもの]（2026-11-24 マジメルの指摘「0%のジョイントを出すのが遅い」）
- 0%のジョイントを、スライダー付きの行で全部出すのをやめた。
  SDD の ALL と同じ考え方で、名前だけの小さなボタンの一覧にした
  （ボタン1個＝ウィジェット1個だけなので、100個あっても一瞬で出る）。
  ボタンを押すと、その頂点に 10% で入って、すぐ調整できる行になる。
- 全ジョイントの名前リストを作る処理も、頂点ごとに繰り返さず
  使い回すようにした（キャッシュ）。

[v8 で直したもの]（2026-11-24 マジメルの要望「選択のたびの自動更新が遅い」）
- 頂点を選ぶたびに表示を全部作り直していたのをやめた。標準では
  選択が変わっても表示は作り直さず、上部の「更新」ボタンを押した時に
  まとめて1回だけ作り直す（＝「まとめて更新」）。たくさん選んでも重くならない。
- 更新待ちの間は「更新」ボタンがオレンジ色に変わり、案内文にも出る。
- 今までの動きが良い人向けに「頂点を選んだら自動で更新」の
  チェックも残した（入れると v7 と同じ動き）。

[v7 で直したもの]（2026-11-24 マジメルの指摘「説明が初心者には難しい」）
- 画面の文を全部、超かみ砕いた言い方に書き直した。1つの案内は短く、
  専門用語はできるだけ日常の言葉に（バインド→くっつける、等）。
- v5で消した「もとに戻す」ボタンへの言及が案内文に残っていたのを
  Ctrl+Z の案内に直した。
"""

from maya import cmds
import maya.mel as mel
import maya.OpenMayaUI as omui
import traceback

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore
    except ImportError:
        import qtpy.QtWidgets as QtWidgets
        import qtpy.QtCore as QtCore

try:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
    DOCKABLE = True
except Exception:
    MayaQWidgetDockableMixin = object
    DOCKABLE = False

def get_maya_window():
    try:
        from shiboken6 import wrapInstance
    except ImportError:
        try:
            from shiboken2 import wrapInstance
        except:
            return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None

class BeginnerWeightEditor(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(BeginnerWeightEditor, self).__init__(parent)
        self.setWindowTitle("やさしいウエイト調整 v13")
        # v6: ドッキング対応（Mayaの画面に組み込める）。「常に手前」は廃止した
        self.resize(820, 640)
        self.is_loading = False
        self.current_vertices = []
        self.copied_weights = None
        self.selection_dirty = False
        self._all_joints_cache = {}
        self._sc_cache = {}
        self._inf_cache = {}
        self.init_ui()

        try:
            self.update_selection_from_maya()
            self.load_weights()
        except Exception:
            traceback.print_exc()

        self.job_num = cmds.scriptJob(event=["SelectionChanged", self.on_selection_changed], protected=True)

    def closeEvent(self, event):
        if hasattr(self, 'job_num') and cmds.scriptJob(exists=self.job_num):
            cmds.scriptJob(kill=self.job_num, force=True)
        super(BeginnerWeightEditor, self).closeEvent(event)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QtWidgets.QLabel("やさしいウエイト調整 v13")
        title_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(title_label)

        # 案内文（いま何を選んでいて、次に何をすればいいか）
        self.guide_label = QtWidgets.QLabel("まずは直したい頂点を選んでね。")
        self.guide_label.setWordWrap(True)
        self.guide_label.setStyleSheet("background: #fff8e1; color: #333; border: 1px solid #e0c97a; border-radius: 4px; padding: 7px; font-size: 12px;")
        layout.addWidget(self.guide_label)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(8)

        pose_all_reset_btn = QtWidgets.QPushButton("ポーズを元に戻す（コントローラー全部ゼロ）")
        pose_all_reset_btn.setFixedHeight(26)
        pose_all_reset_btn.setStyleSheet("QPushButton { font-size: 12px; color: #000; background: #c8e6c9; border: 1px solid #81c784; border-radius: 4px; font-weight: bold; } QPushButton:pressed { background: #a5d6a7; }")
        pose_all_reset_btn.setToolTip("コントローラーを選ばなくてOK。自動で全部見つけて、全部0に戻す（最初のポーズに戻る）。Ctrl+Zでも戻せるよ")
        pose_all_reset_btn.clicked.connect(self.do_reset_all_controllers)
        top_layout.addWidget(pose_all_reset_btn)

        self.refresh_btn = QtWidgets.QPushButton("更新")
        self.refresh_btn.setFixedHeight(30)
        self.refresh_btn.setToolTip("今選んでいる頂点の表示に作り直す。たくさん選んでも、このボタンを押すまで表示は作り直さないので軽いよ")
        self.refresh_btn.clicked.connect(self.do_refresh)
        top_layout.addWidget(self.refresh_btn)
        self._update_refresh_btn_style()

        top_layout.addStretch()

        self.auto_update_chk = QtWidgets.QCheckBox("頂点を選んだら自動で更新")
        self.auto_update_chk.setStyleSheet("font-size: 12px;")
        self.auto_update_chk.setToolTip("入れると、頂点を選ぶたびに表示が自動で新しくなる（たくさん選ぶと重くなることがある）。標準はOFFで、「更新」ボタンを押す時にまとめて作り直す")
        self.auto_update_chk.stateChanged.connect(self.on_auto_update_toggled)
        top_layout.addWidget(self.auto_update_chk)

        self.show_zero_chk = QtWidgets.QCheckBox("0%のジョイントも全部出す")
        self.show_zero_chk.setStyleSheet("font-size: 12px;")
        self.show_zero_chk.setToolTip("割合が0%のジョイントを、ボタンの一覧で出す。ボタンを押すと10%で入る。軽い作りなので、たくさんあってもすぐ出るよ")
        self.show_zero_chk.stateChanged.connect(lambda *args: self.load_weights(True))
        top_layout.addWidget(self.show_zero_chk)

        layout.addLayout(top_layout)

        # お助けボタン行（SDDウェイトツールの便利機能をやさしく実装し直したもの）
        help_layout = QtWidgets.QHBoxLayout()
        help_layout.setSpacing(6)
        help_label = QtWidgets.QLabel("お助け：")
        help_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        help_layout.addWidget(help_label)

        grow_btn = QtWidgets.QPushButton("選択を広げる")
        grow_btn.setFixedHeight(26)
        grow_btn.setToolTip("選んだ頂点の周り1段分まで、選択を広げる")
        grow_btn.clicked.connect(self.do_grow_selection)
        help_layout.addWidget(grow_btn)

        shrink_btn = QtWidgets.QPushButton("選択を狭める")
        shrink_btn.setFixedHeight(26)
        shrink_btn.setToolTip("選択を1段分せばめる")
        shrink_btn.clicked.connect(self.do_shrink_selection)
        help_layout.addWidget(shrink_btn)

        copy_btn = QtWidgets.QPushButton("ウエイトをコピー")
        copy_btn.setFixedHeight(26)
        copy_btn.setToolTip("選んだ頂点の割合を覚える")
        copy_btn.clicked.connect(self.do_copy_weights)
        help_layout.addWidget(copy_btn)

        paste_btn = QtWidgets.QPushButton("貼り付け")
        paste_btn.setFixedHeight(26)
        paste_btn.setToolTip("覚えた割合を、今選んでいる頂点に写す")
        paste_btn.clicked.connect(self.do_paste_weights)
        help_layout.addWidget(paste_btn)

        help_layout.addStretch()
        layout.addLayout(help_layout)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.tab_widget)

        # Tab 1: 頂点ごと
        self.tab_card = QtWidgets.QWidget()
        card_l = QtWidgets.QVBoxLayout(self.tab_card)
        card_l.setContentsMargins(4, 4, 4, 4)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        card_l.addWidget(self.scroll_area)
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_content)
        self.tab_widget.addTab(self.tab_card, "1. 頂点ごと")

        # Tab 2: まとめて
        self.tab_batch = QtWidgets.QWidget()
        batch_l = QtWidgets.QVBoxLayout(self.tab_batch)
        batch_l.setContentsMargins(4, 4, 4, 4)
        self.batch_scroll = QtWidgets.QScrollArea()
        self.batch_scroll.setWidgetResizable(True)
        batch_l.addWidget(self.batch_scroll)
        self.batch_content = QtWidgets.QWidget()
        self.batch_layout = QtWidgets.QVBoxLayout(self.batch_content)
        self.batch_layout.setAlignment(QtCore.Qt.AlignTop)
        self.batch_layout.setContentsMargins(4, 4, 4, 4)
        self.batch_layout.setSpacing(8)
        self.batch_scroll.setWidget(self.batch_content)
        self.tab_widget.addTab(self.tab_batch, "2. まとめて")

        # Tab 0: はじめから（先頭に挿入）
        self.tab_start = QtWidgets.QWidget()
        start_l = QtWidgets.QVBoxLayout(self.tab_start)
        start_l.setContentsMargins(10, 10, 10, 10)
        start_l.setSpacing(8)
        steps = QtWidgets.QLabel(
            "<b>やること</b><br>"
            "1. 骨とメッシュを、両方選ぶ<br>"
            "2. 下のボタンを押す → 骨とメッシュがくっつく<br>"
            "3. 「自動で動かす」で、曲がり具合をチェック<br>"
            "4. おかしい所は「1. 頂点ごと」「2. まとめて」で直す")
        steps.setWordWrap(True)
        steps.setStyleSheet("font-size: 12px;")
        start_l.addWidget(steps)
        self.start_status_label = QtWidgets.QLabel("今の選択：まだ何も選ばれてないよ")
        self.start_status_label.setWordWrap(True)
        self.start_status_label.setStyleSheet("background: #eef4fb; color: #000; border: 1px solid #b0c4de; border-radius: 4px; padding: 7px; font-size: 12px;")
        start_l.addWidget(self.start_status_label)
        bind_btn = QtWidgets.QPushButton("バインドする（選んだ骨とメッシュをくっつける）")
        bind_btn.setFixedHeight(32)
        bind_btn.setStyleSheet("QPushButton { font-size: 13px; color: #000; background: #c8e6c9; border: 1px solid #81c784; border-radius: 4px; font-weight: bold; } QPushButton:pressed { background: #a5d6a7; }")
        bind_btn.clicked.connect(self.do_bind)
        start_l.addWidget(bind_btn)
        # バインドの細かい設定：初期値（最大3つ / Dropoff 4.0）。
        # 数字を変えるだけでバインドに反映される。変えなければ今までと全く同じ。
        bind_opt_row = QtWidgets.QHBoxLayout()
        bind_opt_row.setSpacing(6)
        bind_opt_label = QtWidgets.QLabel("1つの頂点がついていく骨の数（最大）：")
        bind_opt_label.setStyleSheet("font-size: 11px; color: #ddd;")
        bind_opt_row.addWidget(bind_opt_label)
        self.bind_max_spin = QtWidgets.QSpinBox()
        self.bind_max_spin.setRange(1, 8)
        self.bind_max_spin.setValue(3)
        self.bind_max_spin.setFixedWidth(48)
        self.bind_max_spin.setToolTip("最初は3のままでOK。数字を大きくすると、1つの頂点がたくさんの骨についていくよ")
        bind_opt_row.addWidget(self.bind_max_spin)
        dropoff_label = QtWidgets.QLabel("なめらかさ：")
        dropoff_label.setStyleSheet("font-size: 11px; color: #ddd;")
        bind_opt_row.addWidget(dropoff_label)
        self.bind_dropoff_spin = QtWidgets.QDoubleSpinBox()
        self.bind_dropoff_spin.setRange(0.0, 10.0)
        self.bind_dropoff_spin.setSingleStep(0.5)
        self.bind_dropoff_spin.setValue(4.0)
        self.bind_dropoff_spin.setFixedWidth(56)
        self.bind_dropoff_spin.setToolTip("最初は4.0のままでOK。大きくすると、なめらかさが遠くまで広がるよ")
        bind_opt_row.addWidget(self.bind_dropoff_spin)
        bind_opt_row.addStretch()
        start_l.addLayout(bind_opt_row)
        ctrl_row = QtWidgets.QHBoxLayout()
        ctrl_row.setSpacing(6)
        auto_btn = QtWidgets.QPushButton("コントローラーを自動で動かす")
        auto_btn.setFixedHeight(28)
        auto_btn.setStyleSheet("QPushButton { font-size: 12px; color: #000; background: #ffe0b2; border: 1px solid #ffb74d; border-radius: 3px; font-weight: bold; } QPushButton:pressed { background: #ffcc80; }")
        auto_btn.setToolTip("コントローラーを順番に1つずつ曲げて、具合を見る")
        auto_btn.clicked.connect(self.do_auto_test)
        ctrl_row.addWidget(auto_btn)
        test_clear_btn = QtWidgets.QPushButton("テストを消す")
        test_clear_btn.setFixedHeight(28)
        test_clear_btn.clicked.connect(self.do_test_clear)
        ctrl_row.addWidget(test_clear_btn)
        ctrl_row.addStretch()
        start_l.addLayout(ctrl_row)
        bend_row = QtWidgets.QHBoxLayout()
        bend_row.setSpacing(6)
        bend_btn = QtWidgets.QPushButton("選んだ関節を曲げてみる（30°）")
        bend_btn.setFixedHeight(28)
        bend_btn.setStyleSheet("font-size: 12px; color: #000; background: #e8f4fd; border: 1px solid #b0c4de; border-radius: 3px; font-weight: bold;")
        bend_btn.clicked.connect(self.do_bend)
        bend_row.addWidget(bend_btn)
        pose_reset_btn = QtWidgets.QPushButton("戻す")
        pose_reset_btn.setFixedHeight(28)
        pose_reset_btn.clicked.connect(self.do_pose_reset)
        bend_row.addWidget(pose_reset_btn)
        bend_row.addStretch()
        start_l.addLayout(bend_row)
        start_note = QtWidgets.QLabel("※ 数字は最初そのままでOK。割合の合計はいつも100%になるよ。")
        start_note.setWordWrap(True)
        start_note.setStyleSheet("font-size: 11px; color: #aaa;")
        start_l.addWidget(start_note)
        start_l.addStretch()
        self.tab_widget.insertTab(0, self.tab_start, "0. はじめから")

    # --- お助け機能（SDDの便利機能のやさしい実装） ---
    def do_grow_selection(self):
        try:
            mel.eval('GrowPolygonSelectionRegion;')
        except Exception:
            self.guide_label.setText("選択を広げられなかったよ。頂点や面を選んでいるか確認してね。")

    def do_shrink_selection(self):
        try:
            mel.eval('ShrinkPolygonSelectionRegion;')
        except Exception:
            self.guide_label.setText("選択を狭められなかったよ。頂点や面を選んでいるか確認してね。")

    def do_copy_weights(self):
        if not self.current_vertices:
            self.guide_label.setText("コピーするには、まず頂点を1つ選んでね。")
            return
        vtx = self.current_vertices[0]
        mesh = vtx.split('.')[0]
        sc, infs, display_names, skel_joints = self._get_skin_data(mesh, {}, {})
        if not sc:
            self.guide_label.setText("この頂点は、まだ骨とくっついてないみたい。くっつけたメッシュの頂点を選んでね。")
            return
        values = cmds.skinPercent(sc, vtx, q=True, v=True) or []
        pairs = [(j, v) for j, v in zip(infs, values) if v > 0.0001]
        if not pairs:
            self.guide_label.setText("この頂点には割合が付いてなかったよ。別の頂点を選んでね。")
            return
        self.copied_weights = (sc, pairs)
        self.guide_label.setText(f"{vtx} の割合をコピーしたよ。次に、写したい頂点を選んで「貼り付け」を押してね。")

    def do_paste_weights(self):
        if not self.copied_weights:
            self.guide_label.setText("まだ何もコピーしてないよ。先に、見本にしたい頂点を選んで「ウエイトをコピー」を押してね。")
            return
        if not self.current_vertices:
            self.guide_label.setText("貼り付けるには、写したい頂点を選んでね。")
            return
        sc_src, pairs = self.copied_weights
        done, skipped = 0, 0
        cmds.undoInfo(openChunk=True)
        try:
            for vtx in self.current_vertices:
                mesh = vtx.split('.')[0]
                sc, infs, display_names, skel_joints = self._get_skin_data(mesh, {}, {})
                if not sc or sc != sc_src:
                    skipped += 1
                    continue
                # コピー元に無いジョイントは 0 にして、組み合わせをそのまま再現する
                tv = [(j, dict(pairs).get(j, 0.0)) for j in infs]
                cmds.skinPercent(sc, vtx, tv=tv)
                done += 1
        finally:
            cmds.undoInfo(closeChunk=True)
        self.load_weights(True)
        if done and not skipped:
            self.guide_label.setText(f"{done} 個の頂点に貼り付けたよ。Ctrl+Zで戻せるよ。")
        elif done and skipped:
            self.guide_label.setText(f"{done} 個の頂点に貼り付けたよ（{skipped} 個は別のメッシュやったから飛ばした）。")
        else:
            self.guide_label.setText("貼り付けできなかったよ。コピーしたのと同じメッシュの頂点を選んでね。")

    def update_start_status(self):
        if not hasattr(self, 'start_status_label'):
            return
        sel = cmds.ls(sl=True) or []
        jcount = 0
        mcount = 0
        bound = False
        for n in sel:
            if cmds.nodeType(n) == 'joint':
                jcount += 1
            else:
                shapes = cmds.listRelatives(n, shapes=True, type='mesh') or []
                if cmds.nodeType(n) == 'mesh' or shapes:
                    mcount += 1
                    hist = cmds.listHistory(n) or []
                    if any(cmds.nodeType(h) == 'skinCluster' for h in hist):
                        bound = True
        if jcount == 0 and mcount == 0:
            txt = "今の選択：まだ何も選ばれてないよ。骨とメッシュを選んでね。"
        else:
            txt = f"今の選択：骨 {jcount} 個、メッシュ {mcount} 個"
            if bound:
                txt += "（もう骨とくっついてるよ。割合は次のタブで変えられる）"
            elif jcount and mcount:
                txt += " → 「バインドする」を押せるよ"
            elif not jcount:
                txt += "。あと骨も選んでね"
            elif not mcount:
                txt += "。あとメッシュも選んでね"
        self.start_status_label.setText(txt)

    def do_bind(self):
        self._sc_cache = {}
        self._inf_cache = {}
        sel = cmds.ls(sl=True) or []
        joints = []
        meshes = []
        for n in sel:
            if cmds.nodeType(n) == 'joint':
                joints.append(n)
                joints += cmds.listRelatives(n, allDescendents=True, type='joint', fullPath=True) or []
            elif cmds.nodeType(n) == 'mesh':
                meshes.append(n)
            else:
                shapes = cmds.listRelatives(n, shapes=True, type='mesh', fullPath=True) or []
                if shapes:
                    meshes.append(n)
        joints = list(dict.fromkeys(cmds.ls(joints, long=True)))
        meshes = list(dict.fromkeys(meshes))

        if not meshes:
            QtWidgets.QMessageBox.warning(self, "メッシュを選んでね", "くっつけたいメッシュが選ばれてないよ。骨とメッシュの両方を選んだ状態で押してね。")
            return
        if not joints:
            QtWidgets.QMessageBox.warning(self, "骨を選んでね", "骨（ジョイント）が選ばれてないよ。骨とメッシュの両方を選んだ状態で押してね。")
            return

        mesh = meshes[0]
        hist = cmds.listHistory(mesh) or []
        if any(cmds.nodeType(h) == 'skinCluster' for h in hist):
            QtWidgets.QMessageBox.information(self, "もうくっついてるよ", "このメッシュは、もう骨とくっついてるよ。割合を変えるのは「1. 頂点ごと」「2. まとめて」のタブで。")
            return

        cmds.undoInfo(openChunk=True, chunkName="YasashiiBind")
        try:
            sc = cmds.skinCluster(*(joints + [mesh]), toSelectedBones=True, skinMethod=0,
                                  normalizeWeights=1, maximumInfluences=self.bind_max_spin.value(),
                                  obeyMaxInfluences=True, dropoffRate=self.bind_dropoff_spin.value())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "バインドできなかった", f"うまくいかなかった:\n{e}")
            return
        finally:
            cmds.undoInfo(closeChunk=True)

        self.guide_label.setText("くっついたよ！関節を動かすと、メッシュがついてくるはず。曲がり具合は『曲げてみる』でも見れるよ。")
        self.update_start_status()
        self.load_weights()

    def do_bend(self):
        joints = [n for n in (cmds.ls(sl=True) or []) if cmds.nodeType(n) == 'joint']
        if not joints:
            QtWidgets.QMessageBox.warning(self, "関節を選んでね", "曲げたい関節（ジョイント）を1つ選んでから押してね。")
            return
        j = joints[0]
        if not hasattr(self, '_pose_backup'):
            self._pose_backup = {}
        if j not in self._pose_backup:
            self._pose_backup[j] = cmds.getAttr(j + ".rotate")[0]
        cur = cmds.getAttr(j + ".rotateZ")
        cmds.setAttr(j + ".rotateZ", cur + 30.0)
        short = j.split('|')[-1]
        self.start_status_label.setText(f"{short} を30°曲げたよ。変に引っ張られてないか見てみて。終わったら「戻す」で元通り。")

    def do_pose_reset(self):
        backup = getattr(self, '_pose_backup', {})
        for j, (x, y, z) in backup.items():
            if cmds.objExists(j):
                cmds.setAttr(j + ".rotateX", x)
                cmds.setAttr(j + ".rotateY", y)
                cmds.setAttr(j + ".rotateZ", z)
        self._pose_backup = {}
        self.start_status_label.setText("ポーズを戻したよ。")

    def do_reset_all_controllers(self):
        # 選択に頼らず、シーン全体から名前でコントローラーを自動検出する
        def is_ctrl(n):
            if cmds.nodeType(n) == 'joint':
                return False
            shapes = cmds.listRelatives(n, shapes=True) or []
            return any(cmds.nodeType(sh) == 'nurbsCurve' for sh in shapes)
        ctrls = []
        for n in cmds.ls(type='transform') or []:
            low = n.lower()
            if ('ctrl' in low or '_con' in low or 'ctl' in low or 'controller' in low) and is_ctrl(n):
                ctrls.append(n)
        if not ctrls:
            # 名前で見つからなければ、選ばれているコントローラーで代用する
            ctrls = [n for n in (cmds.ls(sl=True) or []) if is_ctrl(n)]
        if not ctrls:
            QtWidgets.QMessageBox.warning(self, "コントローラーが見つからない", "コントローラーが見つからなかったよ。見つからなければ、コントローラーを選んでから押してね。")
            return
        done = 0
        skipped_nodes = 0
        cmds.undoInfo(openChunk=True, chunkName="YasashiiPoseResetAll")
        try:
            for node in ctrls:
                touched = False
                for attr in ('translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ'):
                    a = node + "." + attr
                    try:
                        if cmds.getAttr(a, lock=True):
                            continue
                        if not cmds.getAttr(a, settable=True):
                            continue
                        if abs(cmds.getAttr(a)) < 1e-9:
                            touched = True
                            continue
                        cmds.setAttr(a, 0.0)
                        touched = True
                    except Exception:
                        continue
                if touched:
                    done += 1
                else:
                    skipped_nodes += 1
        finally:
            cmds.undoInfo(closeChunk=True)
        msg = f"{done} 個のコントローラーを全部0に戻したよ。最初のポーズ（Tスタンス）に戻ったはず。違ったら Ctrl+Z で戻せるよ。"
        if skipped_nodes:
            msg += f"（{skipped_nodes} 個はロック等で触れなかった）"
        self.start_status_label.setText(msg)
        self.guide_label.setText(msg)

    # ------------------------------------------------------------------
    # コントローラーの自動テストアニメ
    # ------------------------------------------------------------------
    def _find_controllers(self):
        def is_ctrl(n):
            if cmds.nodeType(n) == 'joint':
                return False
            shapes = cmds.listRelatives(n, shapes=True) or []
            return any(cmds.nodeType(sh) == 'nurbsCurve' for sh in shapes)
        sel = cmds.ls(sl=True) or []
        picked = [n for n in sel if is_ctrl(n)]
        if picked:
            return picked
        found = []
        for n in cmds.ls(type='transform') or []:
            low = n.lower()
            if ('ctrl' in low or '_con' in low or 'ctl' in low or 'controller' in low) and is_ctrl(n):
                found.append(n)
        return found

    def _pick_bend_attr(self, node):
        for attr in ('rotateZ', 'rotateX', 'rotateY'):
            a = node + "." + attr
            try:
                if cmds.getAttr(a, lock=True):
                    continue
                if not cmds.getAttr(a, keyable=True):
                    continue
                if not cmds.getAttr(a, settable=True):
                    continue
            except Exception:
                continue
            return attr
        return None

    def do_auto_test(self):
        ctrls = self._find_controllers()
        if not ctrls:
            QtWidgets.QMessageBox.warning(self, "コントローラーが見つからない", "コントローラーが見つからなかったよ。見つからなければ、コントローラーを選んでから押してね。")
            return
        ctrls.sort(key=lambda n: n.count('|'))
        SEG = 12
        GAP = 2
        created = []
        backup = {}
        skipped = 0
        cur = 1
        for node in ctrls:
            attr = self._pick_bend_attr(node)
            if not attr:
                skipped += 1
                continue
            if cmds.keyframe(node, attribute=attr, q=True, keyframeCount=True):
                skipped += 1
                continue
            a = node + "." + attr
            base = cmds.getAttr(a)
            backup[a] = base
            try:
                cmds.setKeyframe(node, attribute=attr, time=cur, value=base)
                cmds.setKeyframe(node, attribute=attr, time=cur + SEG // 2, value=base + 35.0)
                cmds.setKeyframe(node, attribute=attr, time=cur + SEG, value=base)
            except Exception:
                skipped += 1
                continue
            created.append((node, attr, cur, cur + SEG))
            cur += SEG + GAP
        if not created:
            QtWidgets.QMessageBox.warning(self, "テストを作れなかった", "動かせるコントローラーがなかったよ。（ロック中か、もうアニメが入ってる所は飛ばしてる）")
            return
        self._test_keys = created
        self._test_backup = backup
        self._test_prev_range = (cmds.playbackOptions(q=True, minTime=True),
                                 cmds.playbackOptions(q=True, maxTime=True),
                                 cmds.currentTime(q=True))
        cmds.playbackOptions(minTime=1, maxTime=cur - GAP, loop='continuous')
        cmds.currentTime(1)
        cmds.play(state=True)
        msg = f"{len(created)} 個のコントローラーを順番に動かしてるよ。引っ張りや潰れがないか見てみて。"
        if skipped:
            msg += f"（{skipped} 個はロックや既存アニメのため飛ばした）"
        msg += " 終わったら「テストを消す」で元通り。"
        self.start_status_label.setText(msg)

    def do_test_clear(self):
        try:
            if cmds.play(q=True, state=True):
                cmds.play(state=False)
        except Exception:
            pass
        keys = getattr(self, '_test_keys', [])
        backup = getattr(self, '_test_backup', {})
        for node, attr, t0, t1 in keys:
            try:
                cmds.cutKey(node, attribute=attr, time=(t0, t1))
            except Exception:
                pass
        for a, v in backup.items():
            try:
                cmds.setAttr(a, v)
            except Exception:
                pass
        prev = getattr(self, '_test_prev_range', None)
        if prev:
            try:
                cmds.playbackOptions(minTime=prev[0], maxTime=prev[1], loop='once')
                cmds.currentTime(prev[2])
            except Exception:
                pass
        self._test_keys = []
        self._test_backup = {}
        self.start_status_label.setText("テストを消したよ。元に戻ってるはず。")

    # ------------------------------------------------------------------
    # 選択の取得（頂点 / エッジ / フェイス → 頂点に変換）
    # ------------------------------------------------------------------
    def update_selection_from_maya(self):
        sel = cmds.ls(sl=True, fl=True) or []
        if not sel:
            self.current_vertices = []
            return

        vtxs = [v for v in sel if ".vtx[" in v]
        if vtxs:
            self.current_vertices = vtxs
            return

        others = [c for c in sel if ".e[" in c or ".f[" in c]
        if others:
            try:
                converted = cmds.polyListComponentConversion(others, tv=True)
                expanded = cmds.ls(converted, fl=True) or []
                self.current_vertices = [v for v in expanded if ".vtx[" in v]
            except Exception:
                self.current_vertices = []

    def on_selection_changed(self):
        try:
            self._on_selection_changed_inner()
        except RuntimeError:
            # ウインドウの実体が既に消えている（再実行・ドック解除時など）。
            # 消えた部品を触り続けないよう、自分の監視を止めて終わる。
            try:
                if hasattr(self, 'job_num') and cmds.scriptJob(exists=self.job_num):
                    cmds.scriptJob(kill=self.job_num, force=True)
            except Exception:
                pass

    def _on_selection_changed_inner(self):
        self.update_selection_from_maya()
        if getattr(self, 'auto_update_chk', None) is not None and self.auto_update_chk.isChecked():
            self.selection_dirty = False
            self._update_refresh_btn_style()
            self.load_weights()
            return
        # 標準：表示は作り直さない。「更新」ボタンを押した時にまとめて作り直す
        self.selection_dirty = True
        self._update_refresh_btn_style()
        n = len(self.current_vertices)
        if n:
            self.guide_label.setText(f"頂点 {n} 個を選んだよ。表示はまだ古いまま。「更新」ボタンを押すと新しい表示になるよ。")
        else:
            self.guide_label.setText("選択が変わったよ。「更新」ボタンを押すと表示が新しくなるよ。")

    # --- まとめて更新（v8） ---
    def _update_refresh_btn_style(self):
        if not hasattr(self, 'refresh_btn'):
            return
        if getattr(self, 'selection_dirty', False):
            self.refresh_btn.setText("更新（新しい選択あり）")
            self.refresh_btn.setStyleSheet("QPushButton { font-size: 13px; color: #000; background: #ffcc80; border: 1px solid #fb8c00; border-radius: 4px; font-weight: bold; padding: 0 14px; } QPushButton:pressed { background: #ffb74d; }")
        else:
            self.refresh_btn.setText("更新")
            self.refresh_btn.setStyleSheet("QPushButton { font-size: 13px; color: #fff; background: #42a5f5; border: 1px solid #1e88e5; border-radius: 4px; font-weight: bold; padding: 0 14px; } QPushButton:pressed { background: #1e88e5; }")

    def do_refresh(self):
        # 押した瞬間に反応を見せる（重い読み込みはその後）
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("読み込み中…")
        self.guide_label.setText("読み込み中…")
        QtWidgets.QApplication.processEvents()
        try:
            self.update_selection_from_maya()
            self.selection_dirty = False
            self.load_weights()
        finally:
            self.refresh_btn.setEnabled(True)
            self._update_refresh_btn_style()

    def on_auto_update_toggled(self, *args):
        if self.auto_update_chk.isChecked():
            self.do_refresh()

    def clear_layouts(self):
        # 土台（スクロールの中身）ごと新しいものに差し替える。
        # 表示中のレイアウトにカードを1個ずつ足すと、そのたびに配置計算が
        # 全部やり直しになって「カード数×カード数」で重くなるため。
        # 前の土台は setWidget() が消してくれるので、こちらからは触らない
        # （触ると「already deleted」エラーで起動が止まる。v11〜v12 のバグ）
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_content)

        self.batch_content = QtWidgets.QWidget()
        self.batch_layout = QtWidgets.QVBoxLayout(self.batch_content)
        self.batch_layout.setAlignment(QtCore.Qt.AlignTop)
        self.batch_layout.setContentsMargins(4, 4, 4, 4)
        self.batch_layout.setSpacing(8)
        self.batch_scroll.setWidget(self.batch_content)

    def get_unique_display_names(self, infs):
        short_names = [j.split('|')[-1] for j in infs]
        display_names = []
        for i, j in enumerate(infs):
            short = short_names[i]
            if short_names.count(short) > 1:
                parts = [p for p in j.split('|') if p]
                disp = f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else j
            else:
                disp = short
            display_names.append(disp)
        return display_names

    def load_weights(self, force=False):
        self.is_loading = True
        self.setUpdatesEnabled(False)
        try:
            self._load_weights_inner()
        finally:
            self.setUpdatesEnabled(True)
            self.is_loading = False
        n = len(self.current_vertices)
        if n == 0:
            self.guide_label.setText("まずは直したい頂点を選んでね。面や辺でもOK、その頂点になるよ。")
        else:
            self.guide_label.setText(f"頂点 {n} 個。下のバーで割合を変えると形が変わるよ。ガタガタは、2つ目のタブの「なめらかに」で直せるよ。")
        self.update_start_status()
        self.selection_dirty = False
        self._update_refresh_btn_style()

    def _get_skin_data(self, mesh, sc_cache, inf_cache):
        if mesh in sc_cache:
            sc = sc_cache[mesh]
        else:
            sc = next((n for n in cmds.listHistory(mesh) or [] if cmds.nodeType(n) == 'skinCluster'), None)
            sc_cache[mesh] = sc
        if not sc:
            return None, None, None, None
        if sc not in inf_cache:
            infs = cmds.skinCluster(sc, q=True, inf=True) or []
            infs = [cmds.ls(j, long=True)[0] if cmds.ls(j) else j for j in infs]
            skel = set(infs)
            roots = set()
            for j in infs:
                path = ''
                for p in j.split('|'):
                    if not p: continue
                    path += '|' + p
                    if cmds.nodeType(path) == 'joint':
                        roots.add(path)
                        break
            for r in roots:
                skel.update(cmds.listRelatives(r, allDescendents=True, type='joint', fullPath=True) or [])
            inf_cache[sc] = (infs, self.get_unique_display_names(infs), skel)
        infs, display_names, skel = inf_cache[sc]
        return sc, infs, display_names, skel

    def _build_data(self, infs, display_names, weights, show_zero, skel_joints):
        # 0%でないジョイントだけを「行」にする。0%は重い行にせず、
        # 名前だけのボタン一覧で出す（SDDのALLと同じ考え方）。
        rows = [{'joint': j, 'display_name': d, 'weight': w, 'is_influence': True}
                for j, d, w in zip(infs, display_names, weights) if w >= 0.001]
        zeros = []
        if show_zero:
            key = (tuple(infs), len(skel_joints))
            cached = self._all_joints_cache.get(key)
            if cached is None:
                inf_set = set(infs)
                extra = sorted([j for j in skel_joints if j not in inf_set],
                               key=lambda x: x.split('|')[-1])
                joints_all = list(infs) + extra
                disp_all = self.get_unique_display_names(joints_all)
                cached = (joints_all, disp_all)
                self._all_joints_cache[key] = cached
            joints_all, disp_all = cached
            wmap = dict(zip(infs, weights))
            zeros = [{'joint': j, 'display_name': d}
                     for j, d in zip(joints_all, disp_all) if wmap.get(j, 0.0) < 0.001]
        return rows, zeros

    def _prefetch_weights(self, vertices, sc_cache, inf_cache):
        """全頂点のウエイトを先に読んで {頂点: [ウエイト]} で返す。
        OpenMaya API でまとめて読む（速い）。ダメなら頂点ごとに読む。"""
        result = {}
        by_mesh = {}
        for v in vertices:
            by_mesh.setdefault(v.split('.')[0], []).append(v)
        for mesh, vtxs in by_mesh.items():
            sc, infs, display_names, skel_joints = self._get_skin_data(mesh, sc_cache, inf_cache)
            if not sc:
                continue
            fast = self._get_weights_fast(sc, mesh, vtxs, infs)
            if fast is not None:
                result.update(fast)
                continue
            for v in vtxs:
                result[v] = cmds.skinPercent(sc, v, q=True, v=True) or []
        return result

    def _get_weights_fast(self, sc, mesh, vtxs, infs):
        """MFnSkinCluster.getWeights で全頂点分を1回で読む。失敗したら None。"""
        try:
            import re
            import maya.api.OpenMaya as om
            import maya.api.OpenMayaAnim as oma
            shapes = cmds.listRelatives(mesh, shapes=True, type='mesh', fullPath=True) or []
            if not shapes:
                return None
            idxs = []
            for v in vtxs:
                m = re.search(r"\.vtx\[(\d+)\]", v)
                if not m:
                    return None
                idxs.append(int(m.group(1)))
            sel = om.MSelectionList()
            sel.add(shapes[0])
            dag = sel.getDagPath(0)
            comp_fn = om.MFnSingleIndexedComponent()
            comp = comp_fn.create(om.MFn.kMeshVertComponent)
            comp_fn.addElements(idxs)
            sel2 = om.MSelectionList()
            sel2.add(sc)
            fn = oma.MFnSkinCluster(sel2.getDependNode(0))
            w, n_inf = fn.getWeights(dag, comp)
            if len(w) != len(idxs) * n_inf:
                return None
            api_infs = [p.fullPathName() for p in fn.influenceObjects()]
            out = {}
            for i, v in enumerate(vtxs):
                row = list(w[i * n_inf:(i + 1) * n_inf])
                by_joint = dict(zip(api_infs, row))
                out[v] = [by_joint.get(j, 0.0) for j in infs]
            return out
        except Exception:
            return None

    def _load_weights_inner(self):
        self._all_joints_cache = {}
        self.clear_layouts()

        if not self.current_vertices:
            return

        vertices = self.current_vertices
        show_zero = self.show_zero_chk.isChecked()
        pastel = ["#e6f0ff", "#e6ffe6", "#fff0e6", "#f5e6ff", "#ffffe6"]
        sc_cache, inf_cache = self._sc_cache, self._inf_cache
        weights_map = self._prefetch_weights(vertices, sc_cache, inf_cache)

        # 1. 頂点ごとタブ（カードは最大30個まで。それ以上は作るだけで重い）
        if len(vertices) > 30:
            note = QtWidgets.QLabel(f"頂点が {len(vertices)} 個あるので、表示は最初の30個だけ。全部まとめて直すなら「2. まとめて」タブが速いよ。")
            note.setWordWrap(True)
            note.setStyleSheet("font-size: 12px; color: #b26a00;")
            self.scroll_layout.addWidget(note)
        for idx, vtx in enumerate(vertices[:30]):
            mesh = vtx.split('.')[0]
            sc, infs, display_names, skel_joints = self._get_skin_data(mesh, sc_cache, inf_cache)
            if not sc: continue

            weights = weights_map.get(vtx) or []
            data, zero_data = self._build_data(infs, display_names, weights, show_zero, skel_joints)
            if not data and not show_zero: continue

            card = QtWidgets.QFrame()
            card.vtx, card.skin_cluster, card.rows = vtx, sc, []
            card.setStyleSheet(f"QFrame {{ background-color: {pastel[idx % len(pastel)]}; border: 1px solid #b0b0b0; border-radius: 4px; }} QLabel {{ color: #000; background: transparent; border: none; font-size: 12px; }}")

            cl_sub = QtWidgets.QVBoxLayout(card)
            cl_sub.setContentsMargins(9, 7, 9, 7); cl_sub.setSpacing(5)

            vtx_label = QtWidgets.QLabel(f"<span style='color: #d32f2f;'><b>頂点：{vtx}</b></span>")
            cl_sub.addWidget(vtx_label)

            for item in data:
                cl_sub.addLayout(self.create_row(card, item, is_batch=False))

            if zero_data:
                cl_sub.addWidget(QtWidgets.QLabel("<b>0%のジョイント（押すと10%で入る）</b>"))
                grid = QtWidgets.QGridLayout()
                grid.setSpacing(4)
                for i, z in enumerate(zero_data):
                    pb = QtWidgets.QPushButton(z['display_name'])
                    pb.setFixedHeight(22)
                    pb.setToolTip(z['display_name'])
                    pb.setStyleSheet("font-size: 11px; color: #000; background: #fff; border: 1px solid #a0a0a0; border-radius: 3px;")
                    pb.clicked.connect(lambda *args, c=card, j=z['joint']: self.add_joint_direct(c, j))
                    grid.addWidget(pb, i // 3, i % 3)
                cl_sub.addLayout(grid)

            search_layout = QtWidgets.QHBoxLayout()
            search_layout.setSpacing(4)
            search_layout.setContentsMargins(0, 5, 0, 0)

            search_label = QtWidgets.QLabel("ジョイントを足す：")
            search_layout.addWidget(search_label)

            search_input = QtWidgets.QLineEdit()
            search_input.setPlaceholderText("足したいジョイントの名前")
            search_input.setFixedHeight(24)
            search_input.setStyleSheet("background: #fff; color: #000; font-size: 11px; border: 1px solid #b0b0b0; border-radius: 2px;")

            add_btn = QtWidgets.QPushButton("＋ 追加（10%で入れる）")
            add_btn.setFixedHeight(24)
            add_btn.setStyleSheet("font-size: 11px; color: #000; background: #e8f4fd; border: 1px solid #b0c4de; border-radius: 3px; font-weight: bold;")

            search_layout.addWidget(search_input)
            search_layout.addWidget(add_btn)
            cl_sub.addLayout(search_layout)

            add_btn.clicked.connect(lambda *args, c=card, si=search_input: self.add_joint_by_search(c, si))
            search_input.returnPressed.connect(lambda c=card, si=search_input: self.add_joint_by_search(c, si))

            self.scroll_layout.addWidget(card)

        # 2. まとめてタブ
        if vertices:
            mesh = vertices[0].split('.')[0]
            sc, infs, display_names, skel_joints = self._get_skin_data(mesh, sc_cache, inf_cache)
            self.batch_sc = sc
            if sc:
                weights = weights_map.get(vertices[0]) or []
                b_data, b_zero_data = self._build_data(infs, display_names, weights, show_zero, skel_joints)

                if b_data or b_zero_data:
                    self.batch_rows = []
                    panel = QtWidgets.QFrame()
                    panel.setStyleSheet("QFrame { background: #f0f4f8; border: 1px solid #b0c4de; border-radius: 4px; } QLabel { color: #000; background: transparent; border: none; font-size: 12px; }")
                    pl = QtWidgets.QVBoxLayout(panel)
                    pl.setContentsMargins(9, 7, 9, 7); pl.setSpacing(6)
                    pl.addWidget(QtWidgets.QLabel(f"<b>選んだ {len(vertices)} 個の頂点を、全部おんなじ割合にできるよ</b>"))

                    # なめらかにする（プリセット＋細かい設定）
                    pl.addWidget(QtWidgets.QLabel("ガタガタをなめらかにする"))
                    preset_row = QtWidgets.QHBoxLayout()
                    preset_row.setSpacing(6)
                    for label, iters, strength in [("弱く", 1, 0.3), ("ふつう", 3, 0.5), ("強く", 6, 0.8)]:
                        p_btn = QtWidgets.QPushButton(label)
                        p_btn.setFixedHeight(26)
                        p_btn.setStyleSheet("QPushButton { font-size: 12px; color: #000; background: #e8f4fd; border: 1px solid #b0c4de; border-radius: 3px; font-weight: bold; } QPushButton:pressed { background: #9fc6ee; }")
                        p_btn.clicked.connect(lambda *args, i=iters, s=strength: self.smooth_selected_weights(i, s))
                        preset_row.addWidget(p_btn)
                    preset_row.addStretch()
                    pl.addLayout(preset_row)

                    detail_chk = QtWidgets.QCheckBox("細かく設定する")
                    detail_chk.setStyleSheet("font-size: 11px;")
                    pl.addWidget(detail_chk)

                    detail_widget = QtWidgets.QWidget()
                    detail_widget.setVisible(False)
                    detail_row = QtWidgets.QHBoxLayout(detail_widget)
                    detail_row.setContentsMargins(0, 0, 0, 0)
                    detail_row.setSpacing(5)
                    detail_row.addWidget(QtWidgets.QLabel("回数"))
                    self.smooth_iter_spin = QtWidgets.QSpinBox()
                    self.smooth_iter_spin.setRange(1, 20); self.smooth_iter_spin.setValue(3)
                    self.smooth_iter_spin.setFixedWidth(50); self.smooth_iter_spin.setFixedHeight(24)
                    self.smooth_iter_spin.setToolTip("回数。多いほど、なめらかになる")
                    detail_row.addWidget(self.smooth_iter_spin)
                    detail_row.addWidget(QtWidgets.QLabel("強さ"))
                    self.smooth_strength_spin = QtWidgets.QSpinBox()
                    self.smooth_strength_spin.setRange(5, 100); self.smooth_strength_spin.setValue(50)
                    self.smooth_strength_spin.setSuffix(" %")
                    self.smooth_strength_spin.setFixedWidth(62); self.smooth_strength_spin.setFixedHeight(24)
                    self.smooth_strength_spin.setToolTip("強さ。100%で、周りの頂点とおんなじ割合になる")
                    detail_row.addWidget(self.smooth_strength_spin)
                    detail_btn = QtWidgets.QPushButton("この設定でなめらかにする")
                    detail_btn.setFixedHeight(24)
                    detail_btn.setStyleSheet("font-size: 11px; color: #000; background: #e8f4fd; border: 1px solid #b0c4de; border-radius: 3px; font-weight: bold;")
                    detail_btn.clicked.connect(lambda *args: self.smooth_selected_weights(self.smooth_iter_spin.value(), self.smooth_strength_spin.value() / 100.0))
                    detail_row.addWidget(detail_btn)
                    detail_row.addStretch()
                    pl.addWidget(detail_widget)
                    detail_chk.toggled.connect(detail_widget.setVisible)

                    for item in b_data:
                        pl.addLayout(self.create_row(panel, item, is_batch=True))

                    if b_zero_data:
                        pl.addWidget(QtWidgets.QLabel("<b>0%のジョイント（押すと全部の頂点に10%で入る）</b>"))
                        grid = QtWidgets.QGridLayout()
                        grid.setSpacing(4)
                        for i, z in enumerate(b_zero_data):
                            pb = QtWidgets.QPushButton(z['display_name'])
                            pb.setFixedHeight(22)
                            pb.setToolTip(z['display_name'])
                            pb.setStyleSheet("font-size: 11px; color: #000; background: #fff; border: 1px solid #a0a0a0; border-radius: 3px;")
                            pb.clicked.connect(lambda *args, j=z['joint']: self.add_joint_direct_batch(j))
                            grid.addWidget(pb, i // 3, i % 3)
                        pl.addLayout(grid)

                    self.batch_layout.addWidget(panel)

    def add_joint_by_search(self, card, line_edit):
        query = line_edit.text().strip()
        if not query:
            return

        joints = cmds.ls(query, type='joint')
        if not joints:
            joints = cmds.ls("*" + query + "*", type='joint')

        if not joints:
            QtWidgets.QMessageBox.warning(self, "見つからなかった", f"「{query}」というジョイントはなかったよ。名前を見直してね。")
            return

        target_joint = joints[0]
        vtx = card.vtx
        sc = card.skin_cluster

        try:
            existing = cmds.skinCluster(sc, q=True, inf=True) or []
            existing_long = [cmds.ls(e, long=True)[0] if cmds.ls(e) else e for e in existing]
            target_long = cmds.ls(target_joint, long=True)[0]

            if target_long not in existing_long:
                cmds.skinCluster(sc, edit=True, addInfluence=target_joint, weight=0.0, lockWeights=False)

            self._inf_cache.pop(sc, None)
            cmds.skinPercent(sc, vtx, transformValue=[(target_joint, 0.1)], normalize=True)

            self.show_zero_chk.blockSignals(True)
            self.show_zero_chk.setChecked(False)
            self.show_zero_chk.blockSignals(False)
            self.load_weights(force=True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "エラー", f"うまくいかなかった:\n{e}")

    def _add_joint_core(self, sc, vtxs, joint_long):
        existing = cmds.skinCluster(sc, q=True, inf=True) or []
        existing_long = set(cmds.ls(e, long=True)[0] if cmds.ls(e) else e for e in existing)
        if joint_long not in existing_long:
            cmds.skinCluster(sc, edit=True, addInfluence=joint_long, weight=0.0, lockWeights=False)
        self._inf_cache.pop(sc, None)
        cmds.undoInfo(openChunk=True)
        try:
            for v in vtxs:
                cmds.skinPercent(sc, v, transformValue=[(joint_long, 0.1)], normalize=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def _after_add_joint(self, msg):
        self.show_zero_chk.blockSignals(True)
        self.show_zero_chk.setChecked(False)
        self.show_zero_chk.blockSignals(False)
        self.load_weights(force=True)
        self.guide_label.setText(msg)

    def add_joint_direct(self, card, joint_long):
        try:
            self._add_joint_core(card.skin_cluster, [card.vtx], joint_long)
            self._after_add_joint("ジョイントを10%で入れたよ。バーで割合を調整してね。Ctrl+Zで戻せるよ。")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "エラー", f"うまくいかなかった:\n{e}")

    def add_joint_direct_batch(self, joint_long):
        sc = getattr(self, 'batch_sc', None)
        if not sc or not self.current_vertices:
            return
        mesh0 = self.current_vertices[0].split('.')[0]
        vtxs = [v for v in self.current_vertices if v.split('.')[0] == mesh0]
        try:
            self._add_joint_core(sc, vtxs, joint_long)
            self._after_add_joint(f"{len(vtxs)} 個の頂点に、ジョイントを10%で入れたよ。バーで割合を調整してね。Ctrl+Zで戻せるよ。")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "エラー", f"うまくいかなかった:\n{e}")

    def create_row(self, parent_widget, item, is_batch):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 4, 0, 4)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(6)
        top_row.setContentsMargins(0, 0, 0, 0)

        hold_btn = QtWidgets.QPushButton("固定")
        hold_btn.setFixedSize(46, 24)
        hold_btn.setCheckable(True)
        hold_btn.setToolTip("押すと、このジョイントの割合が変わらなくなる")
        hold_btn.setStyleSheet("""
            QPushButton { color: #333; background: #e0e0e0; border: 1px solid #adadad; border-radius: 3px; font-size: 11px; font-weight: bold; }
            QPushButton:checked { background-color: #ff5252; color: #fff; border: 1px solid #c62828; }
        """)
        top_row.addWidget(hold_btn)

        lbl = QtWidgets.QLabel(item['display_name'])
        lbl.setStyleSheet("color: #000; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        lbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        top_row.addWidget(lbl)

        layout.addLayout(top_row)

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setSpacing(4)
        bottom_row.setContentsMargins(0, 0, 0, 0)

        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 1000)
        slider.setValue(int(round(item['weight'] * 1000)))
        slider.setFixedHeight(20)
        slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #d0d0d0; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #00c853; border-radius: 2px; }
            QSlider::add-page:horizontal { background: #e0e0e0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; border: 1px solid #999999; width: 12px; margin: -4px 0; border-radius: 3px; }
            QSlider::handle:horizontal:hover { background: #f0f0f0; border: 1px solid #666666; }
            QSlider:disabled { background: transparent; }
            QSlider::sub-page:horizontal:disabled { background: #b0b0b0; }
            QSlider::add-page:horizontal:disabled { background: #e0e0e0; }
        """)
        bottom_row.addWidget(slider)

        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(0.0, 100.0); spin.setSingleStep(1.0); spin.setDecimals(1)
        spin.setSuffix(" %")
        spin.setValue(item['weight'] * 100.0)
        spin.setFixedWidth(76); spin.setFixedHeight(24)
        spin.setStyleSheet("background: #fff; color: #000; font-size: 12px;")
        bottom_row.addWidget(spin)

        r_info = {'joint': item['joint'], 'display_name': item['display_name'], 'slider': slider, 'spin': spin, 'hold': hold_btn, 'buttons': [], 'is_influence': item.get('is_influence', True)}
        if not is_batch: parent_widget.rows.append(r_info)
        else: self.batch_rows.append(r_info)

        slider.valueChanged.connect(lambda v, r=r_info: self._on_slider_changed(r, v))
        spin.valueChanged.connect(lambda v, r=r_info: self._on_spin_changed(r, v, parent_widget, is_batch))

        for qv in [0, 25, 50, 75, 100]:
            q_btn = QtWidgets.QPushButton(f"{qv}%")
            q_btn.setFixedSize(38, 24)
            q_btn.setStyleSheet("color: #000; background: #fff; border: 1px solid #a0a0a0; border-radius: 3px; font-size: 10px;")
            q_btn.clicked.connect(lambda *args, r=r_info, val=float(qv): r['spin'].setValue(val))
            bottom_row.addWidget(q_btn)
            r_info['buttons'].append(q_btn)

        layout.addLayout(bottom_row)

        def on_hold_toggled(checked):
            slider.setEnabled(not checked)
            spin.setEnabled(not checked)
            for btn in r_info['buttons']:
                btn.setEnabled(not checked)
            if not self.is_loading:
                self.on_value_changed(parent_widget, r_info, spin.value() / 100.0, is_batch)

        hold_btn.toggled.connect(on_hold_toggled)

        return layout

    def _on_slider_changed(self, r_info, val):
        if self.is_loading: return
        r_info['spin'].setValue(val / 10.0)

    def _on_spin_changed(self, r_info, pct, parent_widget, is_batch):
        if self.is_loading: return
        r_info['slider'].setValue(int(round(pct * 10.0)))
        self.on_value_changed(parent_widget, r_info, pct / 100.0, is_batch)

    def on_value_changed(self, parent, changed, new_val, is_batch):
        # 内部の計算は 0.0〜1.0、画面は % 表示。spin の読み書きは gw/sw 経由。
        if self.is_loading: return
        self.is_loading = True

        rows = parent.rows if not is_batch else self.batch_rows

        if changed['hold'].isChecked():
            self.is_loading = False
            return

        def gw(r):
            return r['spin'].value() / 100.0

        def sw(r, v):
            r['spin'].setValue(v * 100.0)
            r['slider'].setValue(int(round(v * 1000)))

        held_sum = sum(gw(r) for r in rows if r['hold'].isChecked())
        non_held = [r for r in rows if not r['hold'].isChecked()]

        target_remaining = max(0.0, 1.0 - held_sum)
        new_val = max(0.0, min(new_val, target_remaining))
        sw(changed, new_val)

        other_active = [r for r in non_held if r != changed]
        current_other_sum = sum(gw(r) for r in other_active)
        target_other_sum = max(0.0, target_remaining - new_val)

        if other_active:
            if current_other_sum > 0.00001:
                allocated = 0.0
                for i, r in enumerate(other_active):
                    if i == len(other_active) - 1:
                        val = target_other_sum - allocated
                    else:
                        val = target_other_sum * (gw(r) / current_other_sum)
                        allocated += val
                    sw(r, max(0.0, min(1.0, val)))
            else:
                eq = target_other_sum / len(other_active)
                allocated = 0.0
                for i, r in enumerate(other_active):
                    if i == len(other_active) - 1:
                        val = target_other_sum - allocated
                    else:
                        val = eq
                        allocated += val
                    sw(r, max(0.0, min(1.0, val)))

        total_val = sum(gw(r) for r in rows)
        diff = 1.0 - total_val
        if abs(diff) > 0.00001 and other_active:
            r = other_active[0]
            sw(r, max(0.0, min(1.0, gw(r) + diff)))

        target_sc = self.batch_sc if is_batch else parent.skin_cluster
        need_add = [r for r in rows if not r.get('is_influence', True) and gw(r) > 0.0]
        vals = [(r['joint'], gw(r)) for r in rows
                if r.get('is_influence', True) or gw(r) > 0.0]
        cmds.undoInfo(openChunk=True, chunkName="YasashiiWeightEdit")
        try:
            for r in need_add:
                cmds.skinCluster(target_sc, edit=True, addInfluence=r['joint'], weight=0.0, lockWeights=False)
                r['is_influence'] = True
            if need_add:
                self._inf_cache.pop(target_sc, None)
            if not is_batch:
                cmds.skinPercent(target_sc, parent.vtx, transformValue=vals)
            else:
                cmds.skinPercent(target_sc, *self.current_vertices, transformValue=vals)
        except Exception as e:
            print(f"SkinPercent Error: {e}")
            traceback.print_exc()
        finally:
            cmds.undoInfo(closeChunk=True)

        self.is_loading = False

    def smooth_selected_weights(self, iterations=3, strength=0.5):
        # 選択頂点のウエイトを隣接頂点との平均に寄せる（なめらかにする）
        if not self.current_vertices:
            return
        import maya.api.OpenMaya as om
        import re

        mesh = self.current_vertices[0].split('.')[0]
        sc = next((n for n in cmds.listHistory(mesh) or [] if cmds.nodeType(n) == 'skinCluster'), None)
        if not sc:
            return
        infs = cmds.skinCluster(sc, q=True, inf=True) or []
        if not infs:
            return
        shapes = cmds.listRelatives(mesh, shapes=True, type='mesh', fullPath=True) or []
        if not shapes:
            return

        def vtx_index(v):
            m = re.search(r"\.vtx\[(\d+)\]", v)
            return int(m.group(1)) if m else None

        sel_idx = []
        for v in self.current_vertices:
            if v.split('.')[0] != mesh:
                continue
            i = vtx_index(v)
            if i is not None:
                sel_idx.append(i)
        if not sel_idx:
            return

        sel_list = om.MSelectionList()
        sel_list.add(shapes[0])
        dag = sel_list.getDagPath(0)
        it = om.MItMeshVertex(dag)

        neighbors = {}
        need = set(sel_idx)
        for i in sel_idx:
            it.setIndex(i)
            conn = list(it.getConnectedVertices())
            neighbors[i] = conn
            need.update(conn)

        weights = {}
        for i in need:
            w = cmds.skinPercent(sc, f"{mesh}.vtx[{i}]", q=True, v=True) or []
            weights[i] = list(w) + [0.0] * (len(infs) - len(w))
        orig_weights = {i: list(weights[i]) for i in sel_idx}

        n_inf = len(infs)
        for _ in range(iterations):
            snapshot = {i: list(weights[i]) for i in need}
            for i in sel_idx:
                conn = neighbors.get(i) or []
                if not conn:
                    continue
                avg = [0.0] * n_inf
                for c in conn:
                    cw = snapshot[c]
                    for k in range(n_inf):
                        avg[k] += cw[k]
                avg = [a / len(conn) for a in avg]
                cur = snapshot[i]
                new = [cur[k] + (avg[k] - cur[k]) * strength for k in range(n_inf)]
                s = sum(new)
                if s > 1e-8:
                    new = [v / s for v in new]
                weights[i] = new

        cmds.undoInfo(openChunk=True, chunkName="YasashiiWeightSmooth")
        try:
            for i in sel_idx:
                vals = [(infs[k], weights[i][k]) for k in range(n_inf)]
                cmds.skinPercent(sc, f"{mesh}.vtx[{i}]", transformValue=vals)
        except Exception as e:
            print(f"Smooth Error: {e}")
            traceback.print_exc()
        finally:
            cmds.undoInfo(closeChunk=True)

        self.load_weights()
        max_diff = 0.0
        for i in sel_idx:
            for k in range(n_inf):
                d = abs(weights[i][k] - orig_weights[i][k])
                if d > max_diff:
                    max_diff = d
        if max_diff < 0.005:
            self.guide_label.setText("「なめらかにする」は実行したよ。でも、もう十分なめらかで、ほとんど変わらなかったよ。")
        else:
            self.guide_label.setText(f"なめらかにしたよ（頂点 {len(sel_idx)} 個）。一番大きい所で {max_diff * 100:.1f}% 変わったよ。")

global beginner_weight_win
try: beginner_weight_win.close(); beginner_weight_win.deleteLater()
except: pass
# 前回のドッキング用コントロールが残っていたら消す（状態のゴミ対策）
try:
    if cmds.workspaceControl("BeginnerWeightEditorWorkspaceControl", exists=True):
        cmds.deleteUI("BeginnerWeightEditorWorkspaceControl")
except Exception:
    pass

if DOCKABLE:
    beginner_weight_win = BeginnerWeightEditor()
    beginner_weight_win.show(dockable=True, floating=True, area="right")
else:
    beginner_weight_win = BeginnerWeightEditor(get_maya_window())
    beginner_weight_win.show()
    beginner_weight_win.raise_()
    beginner_weight_win.activateWindow()

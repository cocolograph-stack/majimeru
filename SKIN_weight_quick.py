from maya import cmds
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

class HybridVertexWeightEditor(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(HybridVertexWeightEditor, self).__init__(parent)
        self.setWindowTitle("少し便利なウエイト調整")
        self.resize(800, 580)
        self.is_loading = False
        self.current_vertices = []
        self.init_ui()
        
        self.update_selection_from_maya()
        self.load_weights()
        
        self.job_num = cmds.scriptJob(event=["SelectionChanged", self.on_selection_changed], protected=True)
        
    def closeEvent(self, event):
        if hasattr(self, 'job_num') and cmds.scriptJob(exists=self.job_num):
            cmds.scriptJob(kill=self.job_num, force=True)
        super(HybridVertexWeightEditor, self).closeEvent(event)
        
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 上部全体の縦レイアウト
        top_v_layout = QtWidgets.QVBoxLayout()
        top_v_layout.setSpacing(6)
        top_v_layout.setContentsMargins(0, 0, 0, 0)
        
        # タイトルと案内文を横並びにしてセンター配置
        title_h_layout = QtWidgets.QHBoxLayout()
        title_h_layout.setSpacing(8)
        title_h_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        title_label = QtWidgets.QLabel("少し便利なウエイト調整")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        title_h_layout.addWidget(title_label)
        
        tip_label = QtWidgets.QLabel("（エッジ選択でも自動頂点選択できるよ）")
        tip_label.setStyleSheet("font-size: 11px; color: #cccccc;")
        title_h_layout.addWidget(tip_label)
        
        top_v_layout.addLayout(title_h_layout)
        
        # コントロール行（ウエイト0も表示 ＋ インフォ）
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(8)
        
        self.show_zero_chk = QtWidgets.QCheckBox("ウエイト0も表示")
        self.show_zero_chk.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.show_zero_chk.stateChanged.connect(lambda *args: self.load_weights(True))
        top_layout.addWidget(self.show_zero_chk)
        
        top_layout.addStretch()
        
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("font-size: 11px;")
        top_layout.addWidget(self.info_label)
        
        top_v_layout.addLayout(top_layout)
        layout.addLayout(top_v_layout)
        
        # タブ
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tab 1: 個別頂点
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
        self.scroll_layout.setSpacing(6)
        self.scroll_area.setWidget(self.scroll_content)
        self.tab_widget.addTab(self.tab_card, "1. 個別頂点")
        
        # Tab 2: 一括頂点編集
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
        self.batch_layout.setSpacing(6)
        self.batch_scroll.setWidget(self.batch_content)
        self.tab_widget.addTab(self.tab_batch, "2. 一括頂点編集")

    def update_selection_from_maya(self):
        sel = cmds.ls(sl=True, fl=True) or []
        if not sel:
            self.current_vertices = []
            return
            
        vtxs = [v for v in sel if ".vtx[" in v]
        if vtxs:
            self.current_vertices = vtxs
            return
            
        edges = [e for e in sel if ".e[" in e]
        if edges:
            try:
                converted_vtxs = cmds.polyListComponentConversion(edges, tv=True)
                expanded = cmds.ls(converted_vtxs, fl=True) or []
                self.current_vertices = [v for v in expanded if ".vtx[" in v]
            except Exception:
                self.current_vertices = []

    def on_selection_changed(self):
        self.update_selection_from_maya()
        if self.current_vertices:
            self.load_weights()

    def clear_layouts(self):
        for layout in [self.scroll_layout, self.batch_layout]:
            while layout.count():
                w = layout.takeAt(0).widget()
                if w: w.deleteLater()

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
        self.clear_layouts()
            
        if not self.current_vertices:
            self.info_label.setText("エラー: 頂点が選択されていません")
            self.is_loading = False
            return
            
        vertices = self.current_vertices
        show_zero = self.show_zero_chk.isChecked()
        pastel = ["#e6f0ff", "#e6ffe6", "#fff0e6", "#f5e6ff", "#ffffe6"]
        loaded = 0
        
        # 1. 個別タブ構築
        for idx, vtx in enumerate(vertices):
            mesh = vtx.split('.')[0]
            sc = next((n for n in cmds.listHistory(mesh) or [] if cmds.nodeType(n) == 'skinCluster'), None)
            if not sc: continue
            
            raw_infs = cmds.skinPercent(sc, vtx, q=True, t=None) or []
            infs = [cmds.ls(j, long=True)[0] if cmds.ls(j) else j for j in raw_infs]
            weights = cmds.skinPercent(sc, vtx, q=True, v=True) or []
            display_names = self.get_unique_display_names(infs)
            
            if show_zero:
                data = [{'joint': j, 'display_name': disp, 'weight': w} for j, disp, w in zip(infs, display_names, weights)]
            else:
                data = [{'joint': j, 'display_name': disp, 'weight': w} for j, disp, w in zip(infs, display_names, weights) if w >= 0.001]
                
            if not data and not show_zero: continue
            
            loaded += 1
            card = QtWidgets.QFrame()
            card.vtx, card.skin_cluster, card.rows = vtx, sc, []
            card.setStyleSheet(f"QFrame {{ background-color: {pastel[idx % len(pastel)]}; border: 1px solid #b0b0b0; border-radius: 3px; }} QLabel {{ color: #000; background: transparent; border: none; font-size: 11px; }}")
            
            cl_sub = QtWidgets.QVBoxLayout(card)
            cl_sub.setContentsMargins(8, 6, 8, 6); cl_sub.setSpacing(4)
            
            # 頂点名を赤色に変更
            vtx_label = QtWidgets.QLabel(f"<span style='color: #ff5252;'><b>{vtx}</b></span>")
            cl_sub.addWidget(vtx_label)
            
            for item in data:
                cl_sub.addLayout(self.create_row(card, item, is_batch=False))
                
            search_layout = QtWidgets.QHBoxLayout()
            search_layout.setSpacing(4)
            search_layout.setContentsMargins(0, 4, 0, 0)
            
            search_input = QtWidgets.QLineEdit()
            search_input.setPlaceholderText("ジョイント名で検索して追加...")
            search_input.setFixedHeight(20)
            search_input.setStyleSheet("background: #fff; color: #000; font-size: 10px; border: 1px solid #b0b0b0; border-radius: 2px;")
            
            add_btn = QtWidgets.QPushButton("+0.1")
            add_btn.setFixedSize(35, 20)
            add_btn.setToolTip("入力したジョイントをウエイト0.1で追加・設定します")
            add_btn.setStyleSheet("font-size: 10px; background: #e8f4fd; border: 1px solid #b0c4de; border-radius: 2px; font-weight: bold;")
            
            search_layout.addWidget(search_input)
            search_layout.addWidget(add_btn)
            cl_sub.addLayout(search_layout)
            
            add_btn.clicked.connect(lambda *args, c=card, si=search_input: self.add_joint_by_search(c, si))
            search_input.returnPressed.connect(lambda c=card, si=search_input: self.add_joint_by_search(c, si))
                
            self.scroll_layout.addWidget(card)

        # 2. 一括頂点編集タブ構築
        if vertices:
            mesh = vertices[0].split('.')[0]
            self.batch_sc = next((n for n in cmds.listHistory(mesh) or [] if cmds.nodeType(n) == 'skinCluster'), None)
            if self.batch_sc:
                raw_infs = cmds.skinPercent(self.batch_sc, vertices[0], q=True, t=None) or []
                infs = [cmds.ls(j, long=True)[0] if cmds.ls(j) else j for j in raw_infs]
                weights = cmds.skinPercent(self.batch_sc, vertices[0], q=True, v=True) or []
                display_names = self.get_unique_display_names(infs)
                
                if show_zero:
                    b_data = [{'joint': j, 'display_name': disp, 'weight': w} for j, disp, w in zip(infs, display_names, weights)]
                else:
                    b_data = [{'joint': j, 'display_name': disp, 'weight': w} for j, disp, w in zip(infs, display_names, weights) if w >= 0.001]
                
                if b_data:
                    self.batch_rows = []
                    panel = QtWidgets.QFrame()
                    panel.setStyleSheet("QFrame { background: #f0f4f8; border: 1px solid #b0c4de; border-radius: 3px; } QLabel {{ color: #000; background: transparent; border: none; font-size: 11px; }}")
                    pl = QtWidgets.QVBoxLayout(panel)
                    pl.setContentsMargins(8, 6, 8, 6); pl.setSpacing(4)
                    pl.addWidget(QtWidgets.QLabel(f"<b>選択中の全 {len(vertices)} 頂点を一括制御</b>"))
                    
                    for item in b_data:
                        pl.addLayout(self.create_row(panel, item, is_batch=True))
                    self.batch_layout.addWidget(panel)

        self.info_label.setText(f"完了: {loaded}頂点")
        self.is_loading = False

    def add_joint_by_search(self, card, line_edit):
        query = line_edit.text().strip()
        if not query:
            return
            
        joints = cmds.ls(query, type='joint')
        if not joints:
            joints = cmds.ls("*" + query + "*", type='joint')
            
        if not joints:
            QtWidgets.QMessageBox.warning(self, "警告", f"ジョイント '{query}' が見つかりませんでした。")
            return
            
        target_joint = joints[0]
        vtx = card.vtx
        sc = card.skin_cluster
        
        try:
            existing = cmds.skinPercent(sc, vtx, q=True, t=None) or []
            existing_long = [cmds.ls(e, long=True)[0] for e in existing]
            target_long = cmds.ls(target_joint, long=True)[0]
            
            if target_long not in existing_long:
                cmds.skinCluster(sc, edit=True, addInfluence=target_joint, weight=0.0, lockWeights=False)
                
            cmds.skinPercent(sc, vtx, transformValue=[(target_joint, 0.1)], normalize=True)
            
            self.show_zero_chk.setChecked(False)
            self.load_weights(force=True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "エラー", f"エラーが発生しました:\n{e}")

    def create_row(self, parent_widget, item, is_batch):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 3, 0, 3)
        
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(6)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        hold_btn = QtWidgets.QPushButton("H")
        hold_btn.setFixedSize(20, 20)
        hold_btn.setCheckable(True)
        hold_btn.setToolTip("ウエイトをホールド（固定）する")
        hold_btn.setStyleSheet("""
            QPushButton { color: #333; background: #e0e0e0; border: 1px solid #adadad; border-radius: 3px; font-size: 9px; font-weight: bold; }
            QPushButton:checked { background-color: #ff5252; color: #fff; border: 1px solid #c62828; }
        """)
        top_row.addWidget(hold_btn)
        
        lbl = QtWidgets.QLabel(item['display_name'])
        lbl.setStyleSheet("color: #000; background: transparent; border: none; font-size: 11px; font-weight: bold;")
        lbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        top_row.addWidget(lbl)
        
        layout.addLayout(top_row)
        
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.setSpacing(4)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100); slider.setValue(int(round(item['weight'] * 100))); slider.setFixedHeight(18)
        slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 5px; background: #d0d0d0; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #00e676; border-radius: 2px; }
            QSlider::add-page:horizontal { background: #e0e0e0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; border: 1px solid #999999; width: 10px; margin: -4px 0; border-radius: 3px; }
            QSlider::handle:horizontal:hover { background: #f0f0f0; border: 1px solid #666666; }
            QSlider:disabled { background: transparent; }
            QSlider::sub-page:horizontal:disabled { background: #b0b0b0; }
            QSlider::add-page:horizontal:disabled { background: #e0e0e0; }
        """)
        bottom_row.addWidget(slider)
        
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(0.0, 1.0); spin.setSingleStep(0.01); spin.setDecimals(2); spin.setValue(item['weight'])
        spin.setFixedWidth(50); spin.setFixedHeight(20)
        spin.setStyleSheet("background: #fff; color: #000; font-size: 11px;")
        bottom_row.addWidget(spin)
        
        r_info = {'joint': item['joint'], 'display_name': item['display_name'], 'slider': slider, 'spin': spin, 'hold': hold_btn, 'buttons': []}
        if not is_batch: parent_widget.rows.append(r_info)
        else: self.batch_rows.append(r_info)
        
        cb = lambda val, r=r_info, b=is_batch, pw=parent_widget: self.on_value_changed(pw, r, val, b)
        slider.valueChanged.connect(lambda v, r=r_info: r['spin'].setValue(v / 100.0))
        spin.valueChanged.connect(lambda v, r=r_info: r['slider'].setValue(int(round(v * 100))))
        spin.valueChanged.connect(cb)
        
        for qv in [0.0, 0.25, 0.5, 0.75, 1.0]:
            q_btn = QtWidgets.QPushButton(str(qv))
            q_btn.setFixedSize(26, 20)
            q_btn.setStyleSheet("color: #000; background: #fff; border: 1px solid #a0a0a0; border-radius: 3px; font-size: 9px;")
            q_btn.clicked.connect(lambda *args, r=r_info, val=qv: r['spin'].setValue(val))
            bottom_row.addWidget(q_btn)
            r_info['buttons'].append(q_btn)
            
        layout.addLayout(bottom_row)
        
        def on_hold_toggled(checked):
            slider.setEnabled(not checked)
            spin.setEnabled(not checked)
            for btn in r_info['buttons']:
                btn.setEnabled(not checked)
            if not self.is_loading:
                self.on_value_changed(parent_widget, r_info, spin.value(), is_batch)

        hold_btn.toggled.connect(on_hold_toggled)
            
        return layout

    def on_value_changed(self, parent, changed, new_val, is_batch):
        if self.is_loading: return
        self.is_loading = True
        new_val = round(new_val, 2)
        changed['spin'].setValue(new_val)
        
        rows = parent.rows if not is_batch else self.batch_rows
        
        held_sum = sum(r['spin'].value() for r in rows if r['hold'].isChecked())
        active_others = [r for r in rows if r != changed and not r['hold'].isChecked()]
        
        if changed['hold'].isChecked():
            self.is_loading = False
            return

        fixed_sum = held_sum + new_val
        
        if not active_others:
            max_allowed = round(max(0.0, 1.0 - held_sum), 2)
            changed['spin'].setValue(max_allowed)
            self.is_loading = False
            return
            
        remaining = round(max(0.0, 1.0 - fixed_sum), 2)
        old_active_sum = sum(r['spin'].value() for r in active_others)
        
        if old_active_sum > 0.0001:
            allocated = 0.0
            for i, r in enumerate(active_others):
                if i == len(active_others) - 1:
                    val = round(remaining - allocated, 2)
                else:
                    ratio = r['spin'].value() / old_active_sum
                    val = round(remaining * ratio, 2)
                    allocated += val
                r['spin'].setValue(max(0.0, val))
        else:
            eq = round(remaining / len(active_others), 2)
            allocated = 0.0
            for i, r in enumerate(active_others):
                if i == len(active_others) - 1:
                    val = round(remaining - allocated, 2)
                else:
                    val = eq
                    allocated += val
                r['spin'].setValue(max(0.0, val))
                
        vals = [(r['joint'], r['spin'].value()) for r in rows]
        
        total_val = sum(v for j, v in vals)
        if abs(total_val - 1.0) > 0.00001 and active_others:
            diff = round(1.0 - total_val, 2)
            for r in active_others:
                new_adj = round(r['spin'].value() + diff, 2)
                if 0.0 <= new_adj <= 1.0:
                    r['spin'].setValue(new_adj)
                    break
            vals = [(r['joint'], r['spin'].value()) for r in rows]

        if not is_batch:
            cmds.skinPercent(parent.skin_cluster, parent.vtx, transformValue=vals)
        else:
            for vtx in self.current_vertices:
                cmds.skinPercent(self.batch_sc, vtx, transformValue=vals)
        self.is_loading = False

global hybrid_weight_win
try: hybrid_weight_win.close(); hybrid_weight_win.deleteLater()
except: pass

hybrid_weight_win = HybridVertexWeightEditor(get_maya_window())
hybrid_weight_win.show()
hybrid_weight_win.raise_()
hybrid_weight_win.activateWindow()
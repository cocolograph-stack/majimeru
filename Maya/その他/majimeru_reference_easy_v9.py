# -*- coding: utf-8 -*-
"""
リファレンス かんたん管理 (ReferenceEasy) v9
majimeru

Maya標準の「リファレンス エディタ」が分かりにくいので、
よく使う操作だけを、やさしい言葉のボタンで並べたツール。

[できること]
- いま読み込んでいるリファレンス（別のファイルから借りてきたモデル）が
  一覧で見える。ファイル名・置き場所・「読み込み中／外してある」が分かる
- 「一時的に消す（戻せる）」＝シーンから隠すだけ。ファイルは消えない
- 「戻す（また表示）」＝一時的に消してあったものを戻す
- 「読み直す（元の更新を反映）」＝元のファイルが新しくなった時に読み直す
- 「このシーンのものにする（戻せない）」＝借り物でなく自分のものにする
- 「完全に外す」＝このシーンから完全に外す（元のファイル自体は消えない）
- 「選んだモデルの元はどのファイル？」＝選んだものがどのファイルから来たか調べる
- 「元のファイルを別のMayaで開く」＝元ファイルをもう1つのMayaで開いて直せる。
  向こうで保存したら、こっちで「読み直す」を押すと反映される
- 「ファイルを追加で読み込む」＝新しいリファレンスを足す

ドッキング対応（MayaQWidgetDockableMixin）。
"""

# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : ReferenceEasy (リファレンス かんたん管理)  v9
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : リファレンス エディタのよく使う操作を、やさしい言葉のボタンで並べたツール
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

from maya import cmds
import maya.OpenMayaUI as omui
import os
import subprocess
import sys
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
        except Exception:
            return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def pill(bg):
    return (
        "QPushButton { border-radius: 12px; padding: 6px 14px; "
        "background-color: %s; color: #ffffff; border: 1px solid #666; }"
        "QPushButton:hover { background-color: #5a5a5a; }"
        "QPushButton:pressed { background-color: #222222; }" % bg)


PILL = pill("#4a4a4a")          # ふつうのボタン（グレー）
PILL_GREEN = pill("#3d8b4f")    # 戻す
PILL_BLUE = pill("#2f6db3")     # 読み直す
PILL_ORANGE = pill("#b36a2f")   # 一時的に消す
PILL_PURPLE = pill("#6d4fa1")   # このシーンのものにする
PILL_RED = pill("#a83a3a")      # 完全に外す（デリート）
PILL_TEAL = pill("#2e8b8b")     # ファイルを追加で読み込む
PILL_ROSE = pill("#a14f7d")     # 選んだモデルの元はどのファイル？
PILL_GOLD = pill("#9c7c1e")     # 一覧を更新
PILL_OLIVE = pill("#5f7029")    # 元のファイルを別のMayaで開く


class ReferenceEasy(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    WINDOW_TITLE = "リファレンス かんたん管理 v9"
    OBJECT_NAME = "MajimeruReferenceEasy"

    def __init__(self, parent=get_maya_window()):
        super(ReferenceEasy, self).__init__(parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(430)
        self._build_ui()
        self.refresh()

    # ---------- UI ----------
    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(8)

        ver = QtWidgets.QLabel("バージョン: v9")
        ver.setStyleSheet("color: #999999; font-size: 11px;")
        ver.setAlignment(QtCore.Qt.AlignRight)
        main.addWidget(ver)

        self.guide = QtWidgets.QLabel(
            "このシーンが借りてきているファイル（リファレンス）の一覧です。\n"
            "ボタンを押すと、ここに結果が出ます。")
        self.guide.setWordWrap(True)
        self.guide.setStyleSheet(
            "background-color: #333; border-radius: 8px; padding: 8px;")
        main.addWidget(self.guide)

        help_lab = QtWidgets.QLabel(
            "言葉のちがい：\n"
            "・一時的に消す … 隠すだけ。あとで「戻す」で復活できる\n"
            "・読み直す … 元のファイルが新しくなっていたら、その状態で読み直す\n"
            "・このシーンのものにする … 借り物を自分のシーンに取り込む。"
            "元のファイルとのつながりは切れて、元には戻せない\n"
            "・完全に外す … このシーンとのつながりを切る。元のファイル自体は消えない")
        help_lab.setWordWrap(True)
        help_lab.setStyleSheet("color: #cccccc; font-size: 11px;")
        main.addWidget(help_lab)

        top = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("ファイルを追加で読み込む")
        self.btn_add.setStyleSheet(PILL_TEAL)
        self.btn_add.clicked.connect(self.add_reference)
        top.addWidget(self.btn_add)
        self.btn_which = QtWidgets.QPushButton("選んだモデルの元はどのファイル？")
        self.btn_which.setStyleSheet(PILL_ROSE)
        self.btn_which.clicked.connect(self.which_reference)
        top.addWidget(self.btn_which)
        self.btn_refresh = QtWidgets.QPushButton("一覧を更新")
        self.btn_refresh.setStyleSheet(PILL_GOLD)
        self.btn_refresh.clicked.connect(self.refresh)
        top.addWidget(self.btn_refresh)
        main.addLayout(top)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        self.list_host = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(2, 2, 2, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.list_host)
        main.addWidget(scroll, 1)

    def say(self, text):
        self.guide.setText(text)

    def _true_node(self, ref):
        """file コマンドが返すのはファイル名なので、本物のリファレンスノード名に直す。"""
        try:
            node = cmds.referenceQuery(ref, referenceNode=True)
            if node:
                return node
        except Exception:
            pass
        return ref

    # ---------- data ----------
    def _ref_nodes(self):
        try:
            return cmds.file(q=True, reference=True) or []
        except Exception:
            return []

    def _ref_info(self, rn):
        info = {"path": "", "loaded": False, "ns": ""}
        try:
            info["path"] = cmds.referenceQuery(rn, filename=True) or ""
        except Exception:
            pass
        try:
            info["loaded"] = bool(cmds.referenceQuery(rn, isLoaded=True))
        except Exception:
            pass
        try:
            info["ns"] = cmds.referenceQuery(rn, namespace=True) or ""
        except Exception:
            pass
        return info

    # ---------- list ----------
    def refresh(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        refs = self._ref_nodes()
        if not refs:
            lab = QtWidgets.QLabel(
                "いま、このシーンにリファレンスはありません。\n"
                "「ファイルを追加で読み込む」から足せます。")
            lab.setWordWrap(True)
            self.list_layout.insertWidget(0, lab)
            return
        for rn in refs:
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, self._make_card(self._true_node(rn)))

    def _make_card(self, rn):
        info = self._ref_info(rn)
        card = QtWidgets.QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #3a3a3a; border-radius: 10px; }")
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(4)

        short = os.path.basename(info["path"]) or "(名前が取れませんでした)"
        state = "読み込み中" if info["loaded"] else "外してある"
        title = QtWidgets.QLabel("%s　［%s］" % (short, state))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        v.addWidget(title)

        sub = QtWidgets.QLabel(info["path"])
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #bbbbbb; font-size: 11px;")
        v.addWidget(sub)
        if info["ns"]:
            nsl = QtWidgets.QLabel("名前の頭（名前空間）: %s" % info["ns"])
            nsl.setStyleSheet("color: #bbbbbb; font-size: 11px;")
            v.addWidget(nsl)

        row = QtWidgets.QGridLayout()
        if info["loaded"]:
            b = QtWidgets.QPushButton("一時的に消す（戻せる）")
            b.clicked.connect(lambda _=False, r=rn: self.unload_ref(r))
            b.setStyleSheet(PILL_ORANGE)
        else:
            b = QtWidgets.QPushButton("戻す（また表示）")
            b.clicked.connect(lambda _=False, r=rn: self.load_ref(r))
            b.setStyleSheet(PILL_GREEN)
        row.addWidget(b, 0, 0)

        b2 = QtWidgets.QPushButton("読み直す（元の更新を反映）")
        b2.setStyleSheet(PILL_BLUE)
        b2.clicked.connect(lambda _=False, r=rn: self.reload_ref(r))
        row.addWidget(b2, 0, 1)

        b3 = QtWidgets.QPushButton("このシーンのものにする（戻せない）")
        b3.setStyleSheet(PILL_PURPLE)
        b3.clicked.connect(lambda _=False, r=rn: self.import_ref(r))
        row.addWidget(b3, 1, 0)

        b4 = QtWidgets.QPushButton("完全に外す（デリート）")
        b4.setStyleSheet(PILL_RED)
        b4.clicked.connect(lambda _=False, r=rn: self.remove_ref(r))
        row.addWidget(b4, 1, 1)

        v.addLayout(row)

        b5 = QtWidgets.QPushButton("元のファイルを別のMayaで開く")
        b5.setStyleSheet(PILL_OLIVE)
        b5.clicked.connect(lambda _=False, r=rn: self.open_in_new_maya(r))
        v.addWidget(b5)
        return card

    # ---------- actions ----------
    def load_ref(self, rn):
        try:
            cmds.file(loadReference=rn)
            self.say("戻しました。また表示されています。")
        except Exception:
            self.say("戻せませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def unload_ref(self, rn):
        try:
            cmds.file(unloadReference=rn)
            self.say("一時的に消しました。シーンから隠れていますが、元のファイルは無事です。「戻す」で復活できます。")
        except Exception:
            self.say("一時的に消せませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def reload_ref(self, rn):
        try:
            if cmds.referenceQuery(rn, isLoaded=True):
                cmds.file(unloadReference=rn)
            cmds.file(loadReference=rn)
            self.say("読み直しました。元のファイルの新しい状態になっています。")
        except Exception:
            self.say("読み直せませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def import_ref(self, rn):
        ret = QtWidgets.QMessageBox.question(
            self, "このシーンのものにする",
            "このリファレンスを、このシーンのものに取り込みます。\n"
            "取り込むと、元のファイルとのつながりは切れます（元には戻せません）。\n"
            "よろしいですか？")
        if ret != QtWidgets.QMessageBox.Yes:
            return
        try:
            cmds.file(referenceNode=rn, importReference=True)
            self.say("このシーンのものにしました。もうリファレンスではなく、このシーンのものです。")
        except Exception:
            self.say("取り込めませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def remove_ref(self, rn):
        ret = QtWidgets.QMessageBox.question(
            self, "完全に外す（デリート）",
            "このリファレンスを、このシーンから完全に外します。\n"
            "（元のファイル自体は消えません）\nよろしいですか？")
        if ret != QtWidgets.QMessageBox.Yes:
            return
        try:
            cmds.file(referenceNode=rn, removeReference=True)
            self.say("完全に外しました。元のファイル自体は消えていません。")
        except Exception:
            self.say("完全に外せませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def open_in_new_maya(self, rn):
        try:
            path = cmds.referenceQuery(rn, filename=True) or ""
        except Exception:
            path = ""
        if not path or not os.path.exists(path):
            self.say("元のファイルが見つかりませんでした。\n%s" % path)
            return
        try:
            subprocess.Popen([sys.executable, path])
            self.say("別のMayaで開いています: %s\n"
                     "向こうで直して保存したら、この画面の「読み直す（元の更新を反映）」"
                     "を押すと反映されます。" % os.path.basename(path))
        except Exception:
            self.say("別のMayaで開けませんでした。\n"
                     + traceback.format_exc(limit=1).strip().splitlines()[-1])

    def add_reference(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "読み込むファイルを選んでください", "",
            "Mayaファイル (*.ma *.mb)")
        if not path:
            return
        ns = os.path.splitext(os.path.basename(path))[0]
        try:
            cmds.file(path, reference=True, namespace=ns, options="v=0;")
            self.say("追加しました: %s" % os.path.basename(path))
        except Exception:
            self.say("追加できませんでした。\n" + traceback.format_exc(limit=1).strip().splitlines()[-1])
        self.refresh()

    def which_reference(self):
        sel = cmds.ls(selection=True) or []
        if not sel:
            self.say("先に、調べたいモデルを1つ選んでください。")
            return
        node = sel[0]
        found = None
        try:
            found = cmds.referenceQuery(node, referenceNode=True)
        except Exception:
            found = None
        if not found:
            # 名前空間（名前の頭の「○○:」）から推測する
            if ":" in node:
                ns = node.split(":")[0]
                for rn in self._ref_nodes():
                    if self._ref_info(rn)["ns"] == ns:
                        found = rn
                        break
        if found:
            path = ""
            try:
                path = cmds.referenceQuery(found, filename=True) or ""
            except Exception:
                pass
            self.say("「%s」は、このファイルのリファレンスです。\n%s"
                     % (node, path))
        else:
            self.say("「%s」はリファレンスのものではありません。\n"
                     "このシーンで直接作られたものです。" % node)


def show_reference_easy():
    ctrl = ReferenceEasy.OBJECT_NAME + "WorkspaceControl"
    if cmds.workspaceControl(ctrl, exists=True):
        cmds.deleteUI(ctrl)
    win = ReferenceEasy()
    if DOCKABLE:
        win.show(dockable=True, floating=True)
    else:
        win.show()
    return win


if __name__ == "__main__":
    show_reference_easy()
else:
    show_reference_easy()

# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ## ##    ##  ##  ##     ## ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_shelf_installer  v13
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : スクリプトをシェルフに登録する。持ち帰りファイルで家でも同じシェルフが作れる。
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================
# -*- coding: utf-8 -*-
"""
シェルフを作るスクリプト v13

できること:
  - スクリプトを登録して、シェルフのボタンにする
  - 登録の仕方は2通り: ファイルから選ぶ / 文字を貼り付ける
  - シェルフの名前は自由に変えられる（半角の英字・数字と _ だけ）
  - 作り方は2通り: 新しいシェルフを作る（押した時に名前を聞く） /
    今開いているシェルフにボタンを追加する（追加先は Maya で開いているタブ）
    追加する時は、同じ名前のボタンは二重に作らない。
  - 「持ち帰りファイルを作る」で、今の登録を1個の .py に書き出せる。
    家の Maya にそのファイルをドラッグ＆ドロップすれば、同じ窓が出て、
    「シェルフを作る」を押すだけで学校と同じシェルフが作れる。

決めていること:
  - 同じ名前のシェルフがある時は、いきなり消さない。確認してから作り直す。
  - 登録していないスクリプトは、勝手にシェルフには出ない。
"""
import os
import re
import io
import json
import shutil
import base64
import hashlib
import zipfile
import traceback
import ast

import maya.cmds as cmds
import maya.mel as mel

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

try:
    import maya.OpenMayaUI as omui
except Exception:
    omui = None


OPT_ROOT = "majimeruShelfKitRoot"
OPT_NAME = "majimeruShelfName"
LIST_FILE = "shelf_list.json"
WINDOW_OBJECT_NAME = "MajimeruShelfInstallerWindowV13"
HOME_DIR_NAME = "majimeru_shelf_home"

try:
    _SELF_PATH = os.path.abspath(__file__)
except NameError:
    _SELF_PATH = None

# __PAYLOAD_START__
PAYLOAD_ID = ""
PAYLOAD_B64_PARTS = []
# __PAYLOAD_END__

CATEGORIES = {
    u"スキニング": "#E86A92",
    u"リギング": "#4A90D9",
    u"モデリング": "#58B368",
    u"レンダー": "#F0A13C",
    u"アニメーション": "#9B7ED9",
    u"その他": "#8A94A6",
}

DEFAULT_ENTRIES = [
    {"id": "weight_editor", "label": u"やさしいウエイト調整",
     "file": "weight_editor_beginner_v26.py", "category": u"スキニング",
     "short": u"ウエ", "note": u"スキンのウエイトをやさしい言葉で調整する窓を開きます"},
    {"id": "reference_easy", "label": u"リファレンス かんたん管理",
     "file": "majimeru_reference_easy_v10.py", "category": u"その他",
     "short": u"リフ", "note": u"リファレンスの読み込みと管理をする窓を開きます"},
    {"id": "benri_rig", "label": u"べんりリグ",
     "file": "benri_rig_V28.py", "category": u"リギング",
     "short": u"リグ", "note": u"リグ作りの窓を開きます"},
    {"id": "symmetry", "label": u"シンメトリー",
     "file": "majimeru_symmetry_v22.py", "category": u"モデリング",
     "short": u"左右", "note": u"左右対称モデリングの窓を開きます"},
    {"id": "dup_along_path", "label": u"パス沿いに複製",
     "file": "dup_along_path_v4.py", "category": u"モデリング",
     "short": u"パス", "note": u"カーブに沿って物を並べる窓を開きます"},
    {"id": "render_simple", "label": u"かんたんレンダー設定",
     "file": "majimeru_render_simple_v17.py", "category": u"レンダー",
     "short": u"画", "note": u"レンダーの設定をかんたんにする窓を開きます"},
]


# ----------------------------------------------------------------------
# 置き場所の解決
# ----------------------------------------------------------------------
def home_root():
    return os.path.join(cmds.internalVar(userAppDir=True), HOME_DIR_NAME)


def ensure_home_root():
    root = home_root()
    for sub in ("scripts", "icons"):
        folder = os.path.join(root, sub)
        if not os.path.isdir(folder):
            os.makedirs(folder)
    return root


def extract_payload_to(root, payload_id, parts):
    """持ち帰りファイルの中身（zip）を、指定の場所に展開する。"""
    for sub in ("scripts", "icons"):
        folder = os.path.join(root, sub)
        if not os.path.isdir(folder):
            os.makedirs(folder)
    data = base64.b64decode("".join(parts))
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        zf.extractall(root)
    with open(os.path.join(root, ".payload_id"), "w", encoding="utf-8") as f:
        f.write(payload_id)
    return root


def ensure_extracted():
    """このファイル自体が持ち帰りファイルの時、中身を展開する。"""
    root = ensure_home_root()
    marker = os.path.join(root, ".payload_id")
    current = ""
    if os.path.isfile(marker):
        with open(marker, "r", encoding="utf-8") as f:
            current = f.read().strip()
    if current == PAYLOAD_ID and PAYLOAD_ID:
        return root
    return extract_payload_to(root, PAYLOAD_ID, PAYLOAD_B64_PARTS)


def parse_payload(source_text):
    """持ち帰りファイルの文字から、中身のデータを抜き出す。無ければ None。"""
    m_id = re.search(r"PAYLOAD_ID = '([^']+)'", source_text)
    m_parts = re.search(r"PAYLOAD_B64_PARTS = \[(.*?)\]", source_text, re.DOTALL)
    if not m_id or not m_parts:
        return None
    try:
        parts = ast.literal_eval("[" + m_parts.group(1) + "]")
    except Exception:
        return None
    if not parts:
        return None
    return m_id.group(1), parts


def load_takehome_file(path):
    """持ち帰りファイルを読み込んで、中身を使える状態にする。(場所, 本数) を返す。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    parsed = parse_payload(text)
    if parsed is None:
        raise ValueError(u"これは持ち帰りファイルではありません（スクリプトが中に入っていません）。")
    payload_id, parts = parsed
    root = ensure_home_root()
    extract_payload_to(root, payload_id, parts)
    entries = load_entries(root)
    return root, len(entries)
    data = base64.b64decode("".join(PAYLOAD_B64_PARTS))
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        zf.extractall(root)
    for sub in ("scripts", "icons"):
        folder = os.path.join(root, sub)
        if not os.path.isdir(folder):
            os.makedirs(folder)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(PAYLOAD_ID)
    return root


def detect_kit_root():
    # 1. このファイルの隣に scripts がある（キットとして置かれている）
    if _SELF_PATH:
        here = os.path.dirname(_SELF_PATH)
        if os.path.isdir(os.path.join(here, "scripts")):
            return here
    # 2. 持ち帰りファイル（中身入り）の時は、展開した場所
    if PAYLOAD_ID:
        try:
            return ensure_extracted()
        except Exception:
            traceback.print_exc()
    # 3. 前に覚えた場所
    if cmds.optionVar(exists=OPT_ROOT):
        saved = cmds.optionVar(q=OPT_ROOT)
        if saved and os.path.isdir(os.path.join(saved, "scripts")):
            return saved
    # 4. 自分専用の置き場所（Maya のフォルダの中）
    return ensure_home_root()


def remember_root(root):
    if root:
        cmds.optionVar(sv=(OPT_ROOT, root))


# ----------------------------------------------------------------------
# 登録リスト
# ----------------------------------------------------------------------
def load_entries(root):
    path = os.path.join(root, LIST_FILE) if root else None
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("entries"), list):
                return data["entries"]
        except Exception:
            cmds.warning(u"登録リストが読めませんでした。")
            return []
    # リストが無い時: 最初の6本のファイルが揃っている場所だけ、6本を出す
    scripts_dir = os.path.join(root, "scripts") if root else ""
    if scripts_dir and all(
        os.path.isfile(os.path.join(scripts_dir, e["file"])) for e in DEFAULT_ENTRIES
    ):
        return list(DEFAULT_ENTRIES)
    return []


def save_entries(root, entries):
    path = os.path.join(root, LIST_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f, ensure_ascii=False, indent=2)


def make_entry(file_name, label, category):
    stem = re.sub(r"[^A-Za-z0-9_]", "_", os.path.splitext(file_name)[0])
    return {
        "id": stem,
        "label": label,
        "file": file_name,
        "category": category,
        "short": label[:2],
        "note": label + u" の窓を開きます",
    }


def add_entry(root, entries, entry):
    entries = [e for e in entries if e["file"] != entry["file"]]
    entries.append(entry)
    save_entries(root, entries)
    return entries


def save_pasted_script(root, file_name, code_text, label, category):
    """貼り付けた文字を .py ファイルとして保存して、登録する。"""
    if not re.match(r"^[A-Za-z0-9_]+\.py$", file_name or ""):
        raise ValueError(u"ファイル名は半角の英字・数字と _ だけにして、最後に .py を付けてください。")
    if not code_text or not code_text.strip():
        raise ValueError(u"スクリプトの文字が空っぽです。")
    compile(code_text, file_name, "exec")  # 書き方の間違いがあればここで止まる
    dest = os.path.join(root, "scripts", file_name)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(code_text)
    entries = load_entries(root)
    entry = make_entry(file_name, label, category)
    entries = add_entry(root, entries, entry)
    return entry, entries


# ----------------------------------------------------------------------
# アイコンを自動で作る（カテゴリの色 ＋ 短い文字）
# ----------------------------------------------------------------------
def icon_path_for(root, entry):
    name = entry["id"] + ".png"
    folder = os.path.join(root, "icons") if root else ""
    if folder and os.path.isdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return path
    bmp_dir = cmds.internalVar(userBitmapsDir=True)
    return os.path.join(bmp_dir, "majimeru_" + name)


def ensure_icon(root, entry):
    path = icon_path_for(root, entry)
    if os.path.isfile(path):
        return path
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception:
            pass
    color = CATEGORIES.get(entry.get("category", u"その他"), "#8A94A6")
    text = entry.get("short", u"?")[:2]
    size = 64
    pix = QtGui.QPixmap(size, size)
    pix.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QtGui.QColor(color))
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 16, 16)
    painter.setPen(QtGui.QColor("#FFFFFF"))
    font = QtGui.QFont()
    font.setBold(True)
    font.setPixelSize(26 if len(text) > 1 else 32)
    painter.setFont(font)
    painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, text)
    painter.end()
    pix.save(path, "PNG")
    return path


# ----------------------------------------------------------------------
# シェルフを作る／消す
# ----------------------------------------------------------------------
def button_command(root, filename):
    lines = [
        "import os",
        "import maya.cmds as _c",
        "_root = _c.optionVar(q='majimeruShelfKitRoot') "
        "if _c.optionVar(exists='majimeruShelfKitRoot') else ''",
        "if not _root or not os.path.isdir(os.path.join(_root, 'scripts')):",
        "    _root = " + repr(root),
        "_p = os.path.join(_root, 'scripts', " + repr(filename) + ")",
        "exec(compile(open(_p, encoding='utf-8').read(), _p, 'exec'), "
        "{'__name__': '__main__', '__file__': _p})",
    ]
    return "\n".join(lines)


def valid_shelf_name(name):
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name or ""))


def build_shelf(root, name):
    if not valid_shelf_name(name):
        cmds.warning(u"シェルフの名前は、半角の英字で始めて、英字・数字と _ だけで付けてください。")
        return False
    if not root or not os.path.isdir(os.path.join(root, "scripts")):
        cmds.warning(u"スクリプトの場所が分かりません。持ち帰りファイルを読み込むか、スクリプトを加えてください。")
        return False
    remember_root(root)
    cmds.optionVar(sv=(OPT_NAME, name))
    top = mel.eval("$tmpVar = $gShelfTopLevel")
    if cmds.shelfLayout(name, exists=True):
        answer = cmds.confirmDialog(
            title=u"確認",
            message=u"同じ名前のシェルフ「" + name + u"」があります。\n消して作り直しますか？",
            button=[u"作り直す", u"やめる"],
            defaultButton=u"やめる", cancelButton=u"やめる", dismissString=u"やめる",
        )
        if answer != u"作り直す":
            return False
        cmds.deleteUI(name)
    cmds.shelfLayout(name, parent=top)
    try:
        cmds.shelfTabLayout(top, edit=True, selectTab=name)
    except Exception:
        pass
    msg = (u"空のシェルフ「" + name + u"」を作りました。ボタンはまだ入っていません。\n"
           u"入れる時は、そのシェルフのタブを開いたまま「今開いているシェルフに追加する」を押してください。")
    cmds.inViewMessage(amg=u"<hl>空のシェルフを作りました</hl>", pos="topCenter", fade=True)
    print(msg)
    return True


def delete_shelf(name):
    if not cmds.shelfLayout(name, exists=True):
        cmds.warning(u"その名前のシェルフはありません。")
        return False
    answer = cmds.confirmDialog(
        title=u"確認",
        message=u"シェルフ「" + name + u"」を消しますか？\n（スクリプトのファイルは消えません）",
        button=[u"消す", u"やめる"],
        defaultButton=u"やめる", cancelButton=u"やめる", dismissString=u"やめる",
    )
    if answer != u"消す":
        return False
    cmds.deleteUI(name)
    print(u"シェルフ「" + name + u"」を消しました。")
    return True


# ----------------------------------------------------------------------
# 今あるシェルフにボタンを追加する
# ----------------------------------------------------------------------
def list_shelves():
    """今あるシェルフの名前を全部返す。"""
    try:
        top = mel.eval("$tmpVar = $gShelfTopLevel")
        children = cmds.shelfTabLayout(top, query=True, childArray=True)
        return list(children) if children else []
    except Exception:
        return []


def current_shelf_name():
    """今 Maya で開いている（選ばれている）シェルフの名前を返す。"""
    try:
        top = mel.eval("$tmpVar = $gShelfTopLevel")
        name = cmds.shelfTabLayout(top, query=True, selectTab=True)
        return name or ""
    except Exception:
        return ""


def existing_button_labels(shelf_name):
    labels = set()
    try:
        children = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    except Exception:
        children = []
    for child in children:
        try:
            label = cmds.shelfButton(child, query=True, label=True)
        except Exception:
            label = None
        if label:
            labels.add(label)
    return labels


def add_to_shelf(root, target):
    """今あるシェルフに、登録リストのボタンを追加する。既にあるボタンは飛ばす。"""
    if not target or not cmds.shelfLayout(target, exists=True):
        cmds.warning(u"追加するシェルフが見つかりません。先に一覧を更新してください。")
        return False
    if not root or not os.path.isdir(os.path.join(root, "scripts")):
        cmds.warning(u"スクリプトの場所が分かりません。持ち帰りファイルを読み込むか、スクリプトを加えてください。")
        return False
    remember_root(root)
    entries = load_entries(root)
    labels = existing_button_labels(target)
    added = 0
    dup = []
    skipped = []
    for entry in entries:
        if entry["label"] in labels:
            dup.append(entry["label"])
            continue
        script_path = os.path.join(root, "scripts", entry["file"])
        if not os.path.isfile(script_path):
            skipped.append(entry["label"])
            continue
        icon = ensure_icon(root, entry)
        cmds.shelfButton(
            parent=target, label=entry["label"],
            annotation=entry.get("note", entry["label"]),
            image=icon, imageOverlayLabel=entry.get("short", "")[:2],
            command=button_command(root, entry["file"]), sourceType="python",
        )
        labels.add(entry["label"])
        added += 1
    try:
        top = mel.eval("$tmpVar = $gShelfTopLevel")
        cmds.shelfTabLayout(top, edit=True, selectTab=target)
    except Exception:
        pass
    msg = (u"シェルフ「" + target + u"」にボタンを " + str(added) + u" 個追加しました。")
    if dup:
        msg += u"\nもうあったので飛ばしたもの: " + u"、".join(dup)
    if skipped:
        msg += u"\nファイルが無くて飛ばしたもの: " + u"、".join(skipped)
    cmds.inViewMessage(amg=u"<hl>ボタンを追加しました</hl>", pos="topCenter", fade=True)
    print(msg)
    return True


TAKEHOME_TEMPLATE = r'''
# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ## ##    ##  ##  ##     ## ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_shelf_takehome  v1
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : take-home file. Drop it on Maya, then make the same shelf.
#  License : GPL-3.0
# ============================================================
# -*- coding: utf-8 -*-
import os
import re
import io
import json
import base64
import zipfile
import traceback

import maya.cmds as cmds
import maya.mel as mel

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

try:
    import maya.OpenMayaUI as omui
except Exception:
    omui = None

OPT_ROOT = "majimeruShelfKitRoot"
OPT_NAME = "majimeruShelfName"
LIST_FILE = "shelf_list.json"
HOME_DIR_NAME = "majimeru_shelf_home"
WINDOW_OBJECT_NAME = "MajimeruShelfTakehomeWindow"

# __PAYLOAD_START__
PAYLOAD_ID = ""
PAYLOAD_B64_PARTS = []
# __PAYLOAD_END__

CATEGORIES = {
    u"スキニング": "#E86A92",
    u"リギング": "#4A90D9",
    u"モデリング": "#58B368",
    u"レンダー": "#F0A13C",
    u"アニメーション": "#9B7ED9",
    u"その他": "#8A94A6",
}


def home_root():
    return os.path.join(cmds.internalVar(userAppDir=True), HOME_DIR_NAME)


def ensure_extracted():
    root = home_root()
    for sub in ("scripts", "icons"):
        folder = os.path.join(root, sub)
        if not os.path.isdir(folder):
            os.makedirs(folder)
    marker = os.path.join(root, ".payload_id")
    current = ""
    if os.path.isfile(marker):
        with open(marker, "r", encoding="utf-8") as f:
            current = f.read().strip()
    if current == PAYLOAD_ID and PAYLOAD_ID:
        cmds.optionVar(sv=(OPT_ROOT, root))
        return root
    if not PAYLOAD_ID:
        return root
    data = base64.b64decode("".join(PAYLOAD_B64_PARTS))
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        zf.extractall(root)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(PAYLOAD_ID)
    cmds.optionVar(sv=(OPT_ROOT, root))
    return root


def load_entries(root):
    path = os.path.join(root, LIST_FILE)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("entries"), list):
                return data["entries"]
        except Exception:
            pass
    return []


def ensure_icon(root, entry):
    name = entry["id"] + ".png"
    folder = os.path.join(root, "icons")
    path = os.path.join(folder, name)
    if os.path.isfile(path):
        return path
    color = CATEGORIES.get(entry.get("category", u"その他"), "#8A94A6")
    text = entry.get("short", u"?")[:2]
    size = 64
    pix = QtGui.QPixmap(size, size)
    pix.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pix)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QtGui.QColor(color))
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 16, 16)
    painter.setPen(QtGui.QColor("#FFFFFF"))
    font = QtGui.QFont()
    font.setBold(True)
    font.setPixelSize(26 if len(text) > 1 else 32)
    painter.setFont(font)
    painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, text)
    painter.end()
    pix.save(path, "PNG")
    return path


def button_command(root, filename):
    lines = [
        "import os",
        "import maya.cmds as _c",
        "_root = _c.optionVar(q='majimeruShelfKitRoot') "
        "if _c.optionVar(exists='majimeruShelfKitRoot') else ''",
        "if not _root or not os.path.isdir(os.path.join(_root, 'scripts')):",
        "    _root = " + repr(root),
        "_p = os.path.join(_root, 'scripts', " + repr(filename) + ")",
        "exec(compile(open(_p, encoding='utf-8').read(), _p, 'exec'), "
        "{'__name__': '__main__', '__file__': _p})",
    ]
    return "\n".join(lines)


def valid_shelf_name(name):
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name or ""))


def create_empty_shelf(name):
    if not valid_shelf_name(name):
        cmds.warning(u"シェルフの名前は、半角の英字で始めて、英字・数字と _ だけで付けてください。")
        return False
    top = mel.eval("$tmpVar = $gShelfTopLevel")
    if cmds.shelfLayout(name, exists=True):
        answer = cmds.confirmDialog(
            title=u"確認",
            message=u"同じ名前のシェルフ「" + name + u"」があります。\n消して作り直しますか？",
            button=[u"作り直す", u"やめる"],
            defaultButton=u"やめる", cancelButton=u"やめる", dismissString=u"やめる")
        if answer != u"作り直す":
            return False
        cmds.deleteUI(name)
    cmds.shelfLayout(name, parent=top)
    cmds.optionVar(sv=(OPT_NAME, name))
    try:
        cmds.shelfTabLayout(top, edit=True, selectTab=name)
    except Exception:
        pass
    return True


def existing_button_labels(shelf_name):
    labels = set()
    try:
        children = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    except Exception:
        children = []
    for child in children:
        try:
            label = cmds.shelfButton(child, query=True, label=True)
        except Exception:
            label = None
        if label:
            labels.add(label)
    return labels


def add_buttons(root, target):
    if not target or not cmds.shelfLayout(target, exists=True):
        cmds.warning(u"追加するシェルフが見つかりません。")
        return False
    entries = load_entries(root)
    labels = existing_button_labels(target)
    added = 0
    for entry in entries:
        if entry["label"] in labels:
            continue
        script_path = os.path.join(root, "scripts", entry["file"])
        if not os.path.isfile(script_path):
            continue
        icon = ensure_icon(root, entry)
        cmds.shelfButton(
            parent=target, label=entry["label"],
            annotation=entry.get("note", entry["label"]),
            image=icon, imageOverlayLabel=entry.get("short", "")[:2],
            command=button_command(root, entry["file"]), sourceType="python")
        labels.add(entry["label"])
        added += 1
    try:
        top = mel.eval("$tmpVar = $gShelfTopLevel")
        cmds.shelfTabLayout(top, edit=True, selectTab=target)
    except Exception:
        pass
    print(u"シェルフ「" + target + u"」にボタンを " + str(added) + u" 個入れました。")
    return True


def current_shelf_name():
    try:
        top = mel.eval("$tmpVar = $gShelfTopLevel")
        name = cmds.shelfTabLayout(top, query=True, selectTab=True)
        return name or ""
    except Exception:
        return ""


def maya_main_window():
    if omui is None:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None



# 共作の印: とびうおぴょんぴょんのアイコン (64px PNG, base64)
ICON_B64_PARTS = [
    "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"
    "a9wAAAAASUVORK5CYII="
]
ICON_DISPLAY_PX = 32  # 約8mm角


def author_icon_label():
    label = QtWidgets.QLabel()
    label.setAlignment(QtCore.Qt.AlignCenter)
    try:
        pix = QtGui.QPixmap()
        pix.loadFromData(base64.b64decode("".join(ICON_B64_PARTS)))
        pix = pix.scaled(ICON_DISPLAY_PX, ICON_DISPLAY_PX,
                         QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label.setPixmap(pix)
    except Exception:
        pass
    return label

PILL_STYLE = """
QPushButton {
    border-radius: 16px; padding: 8px 14px; font-weight: bold;
    border: 2px solid #54606E; background: #C9D9EE; color: #17202A;
}
QPushButton:hover { background: #AEC6E6; }
QPushButton:pressed { background: #8FB0DC; }
QPushButton#primary { background: #4E9A51; border-color: #2F6B33; color: #FFFFFF; }
QPushButton#primary:hover { background: #438747; }
QTextEdit {
    background: #FFFFFF; color: #17202A;
    border: 1px solid #54606E; border-radius: 8px; padding: 6px;
}
"""


class TakehomeWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TakehomeWindow, self).__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(u"シェルフを戻す - 持ち帰りファイル")
        self.setWindowFlags(QtCore.Qt.Window)
        self.setStyleSheet(PILL_STYLE)
        self.root = ensure_extracted()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(author_icon_label())
        title = QtWidgets.QLabel(u"持ち帰ったスクリプトを、シェルフに入れます")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        lay.addWidget(title)
        row = QtWidgets.QHBoxLayout()
        new_btn = QtWidgets.QPushButton(u"新しいシェルフを作って入れる")
        new_btn.setObjectName("primary")
        new_btn.setStyleSheet(PILL_STYLE)
        new_btn.clicked.connect(self._new_and_fill)
        row.addWidget(new_btn)
        add_btn = QtWidgets.QPushButton(u"今開いているシェルフに追加する")
        add_btn.setStyleSheet(PILL_STYLE)
        add_btn.clicked.connect(self._add_current)
        row.addWidget(add_btn)
        lay.addLayout(row)
        self.status = QtWidgets.QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(100)
        lay.addWidget(self.status)
        self.resize(560, 300)
        self._refresh()

    def _refresh(self):
        entries = load_entries(self.root)
        lines = [u"入っているスクリプト: " + str(len(entries)) + u" 本"]
        for e in entries:
            lines.append(u"・" + e["label"])
        self.status.setPlainText("\n".join(lines))

    def _new_and_fill(self):
        saved = cmds.optionVar(q=OPT_NAME) if cmds.optionVar(exists=OPT_NAME) else "majimeru"
        name, ok = QtWidgets.QInputDialog.getText(
            self, u"新しいシェルフの名前",
            u"名前を入れてください（半角の英字で始めて、英字・数字と _ だけ）:",
            text=saved or "majimeru")
        if not ok or not name.strip():
            return
        try:
            if create_empty_shelf(name.strip()):
                add_buttons(self.root, name.strip())
                self._refresh()
        except Exception:
            traceback.print_exc()

    def _add_current(self):
        target = current_shelf_name()
        if not target:
            cmds.warning(u"今開いているシェルフが分かりませんでした。タブを1回クリックしてから押してください。")
            return
        answer = cmds.confirmDialog(
            title=u"確認",
            message=u"今開いている「" + target + u"」シェルフに追加しますか？",
            button=[u"追加する", u"やめる"],
            defaultButton=u"追加する", cancelButton=u"やめる", dismissString=u"やめる")
        if answer != u"追加する":
            return
        try:
            add_buttons(self.root, target)
            self._refresh()
        except Exception:
            traceback.print_exc()


def prompt_flow(win):
    entries = load_entries(win.root)
    answer = cmds.confirmDialog(
        title=u"持ち帰りファイル",
        message=u"スクリプト " + str(len(entries)) + u" 本が入っています。\nどうしますか？",
        button=[u"新しいシェルフを作って入れる", u"今開いているシェルフに追加する", u"後で"],
        defaultButton=u"新しいシェルフを作って入れる",
        cancelButton=u"後で", dismissString=u"後で")
    if answer == u"新しいシェルフを作って入れる":
        win._new_and_fill()
    elif answer == u"今開いているシェルフに追加する":
        win._add_current()


def show_ui():
    app = QtWidgets.QApplication.instance()
    if app:
        for w in app.topLevelWidgets():
            if w.objectName() == WINDOW_OBJECT_NAME:
                w.close()
                w.deleteLater()
    win = TakehomeWindow(parent=maya_main_window())
    win.show()
    win.raise_()
    win.activateWindow()
    try:
        QtCore.QTimer.singleShot(300, lambda: prompt_flow(win))
    except Exception:
        pass
    return win


def onMayaDroppedPythonFile(*args, **kwargs):
    show_ui()


if __name__ == "__main__":
    show_ui()
'''


# ----------------------------------------------------------------------
# ファイル名には必ずバージョン番号を付ける
# ----------------------------------------------------------------------
def versioned_path(dest):
    """ファイル名に _v番号 が無ければ付け、同じ名前がある時は番号を上げる。"""
    folder = os.path.dirname(dest)
    base = os.path.basename(dest)
    stem, ext = os.path.splitext(base)
    if not ext:
        ext = ".py"
    m = re.search(r"_v(\d+)$", stem)
    if m:
        n = int(m.group(1))
        root_stem = stem[:m.start()]
    else:
        n = 1
        root_stem = stem
    while True:
        candidate = os.path.join(folder, "%s_v%d%s" % (root_stem, n, ext))
        if not os.path.exists(candidate):
            return candidate
        n += 1


# ----------------------------------------------------------------------
# 持ち帰りファイル（書き出し）
# ----------------------------------------------------------------------
def make_payload_bytes(root, entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            p = os.path.join(root, "scripts", entry["file"])
            if os.path.isfile(p):
                zf.write(p, "scripts/" + entry["file"])
        zf.writestr(LIST_FILE, json.dumps({"entries": entries}, ensure_ascii=False, indent=2))
    return buf.getvalue()


def build_export_text(source_text, payload_bytes):
    payload_id = hashlib.md5(payload_bytes).hexdigest()
    b64 = base64.b64encode(payload_bytes).decode("ascii")
    parts = [b64[i:i + 76] for i in range(0, len(b64), 76)]
    block_lines = ["PAYLOAD_ID = " + repr(payload_id), "PAYLOAD_B64_PARTS = ["]
    block_lines += ["    " + repr(p) + "," for p in parts]
    block_lines.append("]")
    block = "\n".join(block_lines)
    pattern = re.compile(
        r"# __PAYLOAD_START__\n.*?# __PAYLOAD_END__", re.DOTALL)
    replacement = "# __PAYLOAD_START__\n" + block + "\n# __PAYLOAD_END__"
    new_text, count = pattern.subn(lambda m: replacement, source_text, count=1)
    if count == 0:
        raise ValueError(u"書き出しに失敗しました（PAYLOAD の場所が見つかりません）。")
    return new_text


def export_takehome(root, dest_path):
    entries = load_entries(root)
    if not entries:
        raise ValueError(u"登録されているスクリプトがありません。先に加えてください。")
    source_text = TAKEHOME_TEMPLATE
    payload = make_payload_bytes(root, entries)
    new_text = build_export_text(source_text, payload)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return len(entries)


# ----------------------------------------------------------------------
# 窓
# ----------------------------------------------------------------------
def maya_main_window():
    if omui is None:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None



# 共作の印: とびうおぴょんぴょんのアイコン (64px PNG, base64)
ICON_B64_PARTS = [
    "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"
    "a9wAAAAASUVORK5CYII="
]
ICON_DISPLAY_PX = 32  # 約8mm角


def author_icon_label():
    label = QtWidgets.QLabel()
    label.setAlignment(QtCore.Qt.AlignCenter)
    try:
        pix = QtGui.QPixmap()
        pix.loadFromData(base64.b64decode("".join(ICON_B64_PARTS)))
        pix = pix.scaled(ICON_DISPLAY_PX, ICON_DISPLAY_PX,
                         QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label.setPixmap(pix)
    except Exception:
        pass
    return label

PILL_STYLE = """
QPushButton {
    border-radius: 16px; padding: 8px 14px; font-weight: bold;
    border: 2px solid #54606E; background: #C9D9EE; color: #17202A;
}
QPushButton:hover { background: #AEC6E6; }
QPushButton:pressed { background: #8FB0DC; }
QPushButton#primary { background: #4E9A51; border-color: #2F6B33; color: #FFFFFF; }
QPushButton#primary:hover { background: #438747; }
QPushButton#primary:pressed { background: #35703A; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #FFFFFF; color: #17202A;
    border: 1px solid #54606E; border-radius: 8px; padding: 6px;
}
QRadioButton { color: #E8E8E8; padding: 4px; }
QComboBox {
    background: #FFFFFF; color: #17202A;
    border: 1px solid #54606E; border-radius: 8px; padding: 4px 8px;
}
"""


class PasteAddDialog(QtWidgets.QDialog):
    def __init__(self, parent, root):
        super(PasteAddDialog, self).__init__(parent)
        self.root = root
        self.setWindowTitle(u"貼り付けて加える - スクリプトの文字を貼ってください")
        self.setStyleSheet(PILL_STYLE)
        self.resize(560, 480)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(QtWidgets.QLabel(u"ボタンの名前（シェルフに出る名前）:"))
        self.label_edit = QtWidgets.QLineEdit()
        lay.addWidget(self.label_edit)
        lay.addWidget(QtWidgets.QLabel(u"ファイル名（半角の英字・数字と _ だけ、最後は .py）:"))
        self.file_edit = QtWidgets.QLineEdit(self._next_file_name())
        lay.addWidget(self.file_edit)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(u"色のグループ:"))
        self.cat_combo = QtWidgets.QComboBox()
        self.cat_combo.addItems(list(CATEGORIES.keys()))
        self.cat_combo.setCurrentText(u"その他")
        row.addWidget(self.cat_combo)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(QtWidgets.QLabel(u"スクリプトの文字（ここに貼り付け）:"))
        self.code_edit = QtWidgets.QPlainTextEdit()
        lay.addWidget(self.code_edit, 1)
        btn_row = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton(u"保存して加える")
        save_btn.setObjectName("primary")
        save_btn.setStyleSheet(PILL_STYLE)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        cancel_btn = QtWidgets.QPushButton(u"やめる")
        cancel_btn.setStyleSheet(PILL_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _next_file_name(self):
        scripts_dir = os.path.join(self.root, "scripts")
        n = 1
        while os.path.exists(os.path.join(scripts_dir, "my_script_v%d.py" % n)):
            n += 1
        return "my_script_v%d.py" % n

    def _save(self):
        label = self.label_edit.text().strip()
        if not label:
            cmds.warning(u"ボタンの名前を入れてください。")
            return
        try:
            save_pasted_script(
                self.root, self.file_edit.text().strip(),
                self.code_edit.toPlainText(), label,
                self.cat_combo.currentText())
        except SyntaxError as e:
            cmds.warning(u"スクリプトの書き方に間違いがありそうです:\n" + str(e))
            return
        except ValueError as e:
            cmds.warning(str(e))
            return
        self.accept()


class ShelfInstallerWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShelfInstallerWindow, self).__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(u"シェルフを作る v13 - スクリプトをシェルフに登録します")
        self.setStyleSheet(PILL_STYLE)
        self.setWindowFlags(QtCore.Qt.Window)
        self.root = detect_kit_root()
        if self.root:
            remember_root(self.root)
        self._build_ui()
        self._refresh_status()
        if PAYLOAD_ID:
            try:
                QtCore.QTimer.singleShot(
                    300, lambda: self._after_load_prompt(len(load_entries(self.root))))
            except Exception:
                pass

    def _pill(self, text, func, primary=False):
        btn = QtWidgets.QPushButton(text)
        if primary:
            btn.setObjectName("primary")
        btn.setStyleSheet(PILL_STYLE)
        btn.clicked.connect(func)
        return btn

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.addWidget(author_icon_label())
        title = QtWidgets.QLabel(u"スクリプトを、シェルフのボタンにします")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        main.addWidget(title)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self._pill(u"新しいシェルフを作る", self._make_new, primary=True))
        btn_row.addWidget(self._pill(u"今開いているシェルフに追加する", self._make_add))
        btn_row.addWidget(self._pill(u"シェルフを消す", self._delete))
        main.addLayout(btn_row)

        btn_row2 = QtWidgets.QHBoxLayout()
        btn_row2.addWidget(self._pill(u"ファイルから加える", self._add_from_file))
        btn_row2.addWidget(self._pill(u"貼り付けて加える", self._add_from_paste))
        btn_row2.addWidget(self._pill(u"スクリプトを外す", self._remove_script))
        main.addLayout(btn_row2)

        btn_row3 = QtWidgets.QHBoxLayout()
        btn_row3.addWidget(self._pill(u"持ち帰りファイルを作る（家で同じシェルフが作れます）",
                                      self._export, primary=True))
        main.addLayout(btn_row3)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(u"持ち帰りファイル:"))
        self.root_label = QtWidgets.QLabel(u"")
        self.root_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        row.addWidget(self.root_label, 1)
        row.addWidget(self._pill(u"持ち帰りファイルを読み込む", self._load_takehome))
        main.addLayout(row)


        self.status = QtWidgets.QTextEdit()
        self.status.setReadOnly(True)
        self.status.setMinimumHeight(120)
        main.addWidget(self.status)
        self.resize(600, 380)

    def _refresh_status(self):
        if self.root:
            self.root_label.setText(self.root)
        entries = load_entries(self.root) if self.root else []
        lines = [u"登録リストに入っているスクリプト: " + str(len(entries)) + u" 本"]
        for e in entries:
            exists = u""
            if self.root:
                p = os.path.join(self.root, "scripts", e["file"])
                exists = u"OK" if os.path.isfile(p) else u"ファイルがありません"
            lines.append(u"・" + e["label"] + u"（" + e.get("category", "") + u"） " + exists)
        lines.append(u"")
        lines.append(u"新しいスクリプトは、加えないとシェルフには出ません。")
        lines.append(u"追加する時は、先に Maya で追加したいシェルフのタブを開いておいてください。")
        self.status.setPlainText("\n".join(lines))

    def _load_takehome(self):
        result = cmds.fileDialog2(
            fileMode=1, fileFilter="Python (*.py)",
            caption=u"持ち帰りファイルを選んでください")
        if not result:
            return
        try:
            root, count = load_takehome_file(result[0])
        except ValueError as e:
            cmds.warning(str(e))
            return
        except Exception:
            traceback.print_exc()
            cmds.warning(u"読み込む途中で止まりました。")
            return
        self.root = root
        remember_root(root)
        self._refresh_status()
        self._after_load_prompt(count)

    def _prompt_new_shelf_name(self):
        saved = cmds.optionVar(q=OPT_NAME) if cmds.optionVar(exists=OPT_NAME) else "majimeru"
        name, ok = QtWidgets.QInputDialog.getText(
            self, u"新しいシェルフの名前",
            u"名前を入れてください（半角の英字で始めて、英字・数字と _ だけ）:",
            text=saved or "majimeru")
        if not ok or not name.strip():
            return None
        return name.strip()

    def _make_new(self):
        name = self._prompt_new_shelf_name()
        if not name:
            return
        try:
            if build_shelf(self.root, name):
                self._refresh_status()
        except Exception:
            traceback.print_exc()
            cmds.warning(u"シェルフを作る途中で止まりました。スクリプトエディタの表示を見てください。")

    def _after_load_prompt(self, count):
        """持ち帰りファイルを読み込んだ直後に、どうするか聞く。"""
        answer = cmds.confirmDialog(
            title=u"読み込みました",
            message=u"持ち帰りファイルを読み込みました（スクリプト " + str(count) + u" 本）。\n"
                    u"どうしますか？",
            button=[u"新しいシェルフを作る", u"今開いているシェルフに追加する", u"後で"],
            defaultButton=u"新しいシェルフを作る",
            cancelButton=u"後で", dismissString=u"後で")
        if answer == u"新しいシェルフを作る":
            name = self._prompt_new_shelf_name()
            if not name:
                return
            try:
                if build_shelf(self.root, name):
                    add_to_shelf(self.root, name)
                    self._refresh_status()
            except Exception:
                traceback.print_exc()
                cmds.warning(u"シェルフを作る途中で止まりました。")
        elif answer == u"今開いているシェルフに追加する":
            self._make_add()

    def _make_add(self):
        target = current_shelf_name()
        if not target:
            cmds.warning(u"今開いているシェルフが分かりませんでした。Maya のシェルフのタブを1回クリックしてから押してください。")
            return
        answer = cmds.confirmDialog(
            title=u"確認",
            message=u"今開いている「" + target + u"」シェルフに追加しますか？",
            button=[u"追加する", u"やめる"],
            defaultButton=u"追加する", cancelButton=u"やめる", dismissString=u"やめる")
        if answer != u"追加する":
            return
        try:
            if add_to_shelf(self.root, target):
                self._refresh_status()
        except Exception:
            traceback.print_exc()
            cmds.warning(u"追加する途中で止まりました。スクリプトエディタの表示を見てください。")

    def _delete(self):
        shelves = list_shelves()
        if not shelves:
            cmds.warning(u"シェルフが見つかりませんでした。")
            return
        chosen, ok = QtWidgets.QInputDialog.getItem(
            self, u"シェルフを消す", u"どのシェルフを消しますか:",
            shelves, 0, False)
        if not ok:
            return
        try:
            delete_shelf(chosen)
        except Exception:
            traceback.print_exc()

    def _after_add(self, entry):
        ensure_icon(self.root, entry)
        self._refresh_status()
        answer = cmds.confirmDialog(
            title=u"加えました",
            message=u"登録リストに加えました。\n今すぐシェルフに入れますか？",
            button=[u"今開いているシェルフに追加", u"新しいシェルフを作る", u"後で"],
            defaultButton=u"今開いているシェルフに追加",
            cancelButton=u"後で", dismissString=u"後で")
        if answer == u"今開いているシェルフに追加":
            self._make_add()
        elif answer == u"新しいシェルフを作る":
            self._make_new()

    def _add_from_file(self):
        if not self.root:
            cmds.warning(u"場所が決まっていません。")
            return
        result = cmds.fileDialog2(
            fileMode=1, fileFilter="Python (*.py)",
            caption=u"シェルフに加えるスクリプトを選んでください")
        if not result:
            return
        src = result[0]
        label, ok = QtWidgets.QInputDialog.getText(
            self, u"ボタンの名前", u"シェルフに出す名前を入れてください:")
        if not ok or not label.strip():
            return
        category, ok = QtWidgets.QInputDialog.getItem(
            self, u"色のグループ", u"どのグループの色にしますか:",
            list(CATEGORIES.keys()), 5, False)
        if not ok:
            return
        filename = os.path.basename(src)
        dest = os.path.join(self.root, "scripts", filename)
        if os.path.abspath(src) != os.path.abspath(dest):
            shutil.copyfile(src, dest)
        entry = make_entry(filename, label.strip(), category)
        add_entry(self.root, load_entries(self.root), entry)
        self._after_add(entry)

    def _add_from_paste(self):
        if not self.root:
            cmds.warning(u"場所が決まっていません。")
            return
        dlg = PasteAddDialog(self, self.root)
        if dlg.exec_() if hasattr(dlg, "exec_") else dlg.exec():
            entries = load_entries(self.root)
            if entries:
                self._after_add(entries[-1])

    def _remove_script(self):
        entries = load_entries(self.root)
        if not entries:
            cmds.warning(u"登録されているスクリプトがありません。")
            return
        labels = [e["label"] for e in entries]
        chosen, ok = QtWidgets.QInputDialog.getItem(
            self, u"スクリプトを外す",
            u"どれを外しますか（ファイルは消えません、リストから外れるだけです）:",
            labels, 0, False)
        if not ok:
            return
        entries = [e for e in entries if e["label"] != chosen]
        save_entries(self.root, entries)
        self._refresh_status()

    def _export(self):
        try:
            result = cmds.fileDialog2(
                fileMode=0, fileFilter="Python (*.py)",
                caption=u"持ち帰りファイルの保存場所と名前を選んでください",
                dialogStyle=2)
            if not result:
                return
            dest = result[0]
            if not dest.lower().endswith(".py"):
                dest += ".py"
            dest = versioned_path(dest)
            count = export_takehome(self.root, dest)
            cmds.confirmDialog(
                title=u"できました",
                message=u"持ち帰りファイルを作りました（スクリプト " + str(count) + u" 本入り）。\n"
                        u"保存先: " + dest + u"\n\n"
                        u"家では、このファイルを Maya にドラッグ＆ドロップして、\n"
                        u"「シェルフを作る」を押せば、同じシェルフが作れます。",
                button=[u"OK"])
        except ValueError as e:
            cmds.warning(str(e))
        except Exception:
            traceback.print_exc()
            cmds.warning(u"持ち帰りファイルを作る途中で止まりました。")


def show_ui():
    app = QtWidgets.QApplication.instance()
    if app:
        for w in app.topLevelWidgets():
            if w.objectName() == WINDOW_OBJECT_NAME:
                w.close()
                w.deleteLater()
    win = ShelfInstallerWindow(parent=maya_main_window())
    win.show()
    win.raise_()
    win.activateWindow()
    return win


def onMayaDroppedPythonFile(*args, **kwargs):
    """Maya の画面にファイルを落とした時に呼ばれる。窓を開く。"""
    show_ui()


if __name__ == "__main__":
    show_ui()

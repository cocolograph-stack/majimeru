# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ## ##    ##  ##  ##     ## ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_shelf_installer  v12
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : スクリプトをシェルフに登録する。持ち帰りファイルで家でも同じシェルフが作れる。
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================
# -*- coding: utf-8 -*-
"""
シェルフを作るスクリプト v12

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
WINDOW_OBJECT_NAME = "MajimeruShelfInstallerWindowV12"
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
        title = QtWidgets.QLabel(u"持ち帰ったスクリプトを、シェルフに入れます")
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
        self.setWindowTitle(u"シェルフを作る v12 - スクリプトをシェルフに登録します")
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
        title = QtWidgets.QLabel(u"スクリプトを、シェルフのボタンにします")
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

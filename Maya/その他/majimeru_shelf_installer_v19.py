# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ## ##    ##  ##  ##     ## ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_shelf_installer  v19
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : スクリプトをシェルフに登録する。持ち帰りファイルで家でも同じシェルフが作れる。
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================
# -*- coding: utf-8 -*-
"""
シェルフを作るスクリプト v19

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
WINDOW_OBJECT_NAME = "MajimeruShelfInstallerWindowV19"
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
    """貼り付けた文字を .py か .mel ファイルとして保存して、登録する。"""
    if not re.match(r"^[A-Za-z0-9_]+\.(py|mel)$", file_name or ""):
        raise ValueError(u"ファイル名は半角の英字・数字と _ だけにして、最後に .py か .mel を付けてください。")
    if not code_text or not code_text.strip():
        raise ValueError(u"スクリプトの文字が空っぽです。")
    if file_name.lower().endswith(".py"):
        compile(code_text, file_name, "exec")  # Pythonは書き方の間違いがあればここで止まる
    # MELはここでは書き方チェックができないので、そのまま保存する
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
    head = [
        "import os",
        "import maya.cmds as _c",
        "_root = _c.optionVar(q='majimeruShelfKitRoot') "
        "if _c.optionVar(exists='majimeruShelfKitRoot') else ''",
        "if not _root or not os.path.isdir(os.path.join(_root, 'scripts')):",
        "    _root = " + repr(root),
        "_p = os.path.join(_root, 'scripts', " + repr(filename) + ")",
    ]
    if filename.lower().endswith(".mel"):
        lines = head + [
            "import maya.mel as _m",
            "_q = chr(34)",
            "_m.eval('source ' + _q + _p.replace(chr(92), '/') + _q)",
            "_proc = os.path.splitext(os.path.basename(_p))[0]",
            "try:",
            "    if 'Unknown' not in str(_m.eval('whatIs ' + _q + _proc + _q)):",
            "        _m.eval(_proc)",
            "except Exception:",
            "    pass",
        ]
    else:
        lines = head + [
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


def shelves_for_delete():
    """消すシェルフの候補。自分のシェルフ（最後に使った名前）を先頭にする。"""
    names = list_shelves()
    own = cmds.optionVar(q=OPT_NAME) if cmds.optionVar(exists=OPT_NAME) else ""
    if own and own in names:
        names = [own] + [n for n in names if n != own]
    return names

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
    head = [
        "import os",
        "import maya.cmds as _c",
        "_root = _c.optionVar(q='majimeruShelfKitRoot') "
        "if _c.optionVar(exists='majimeruShelfKitRoot') else ''",
        "if not _root or not os.path.isdir(os.path.join(_root, 'scripts')):",
        "    _root = " + repr(root),
        "_p = os.path.join(_root, 'scripts', " + repr(filename) + ")",
    ]
    if filename.lower().endswith(".mel"):
        lines = head + [
            "import maya.mel as _m",
            "_q = chr(34)",
            "_m.eval('source ' + _q + _p.replace(chr(92), '/') + _q)",
            "_proc = os.path.splitext(os.path.basename(_p))[0]",
            "try:",
            "    if 'Unknown' not in str(_m.eval('whatIs ' + _q + _proc + _q)):",
            "        _m.eval(_proc)",
            "except Exception:",
            "    pass",
        ]
    else:
        lines = head + [
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



# 共作の印: とびうおぴょんぴょんのアイコン 6種 (64px PNG, base64)
# 窓を開くたびに、この中からランダムで1つ出る
ICON_SET_PARTS = [
    [
        "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"
    ],
    [
        "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",
        "x7FWMQDEsXJdN45irUwun/NcLwiC4eEBepMpE81mS2szs3Xa8zwhhSVkJ/78IEBkRHC8xMLiUi6T2rJlS7vRvFKEEbFzj4WgjZYk",
        "ssWi53iWJaQQtmUJgdKSlpRRGGnmZqP5yF/89befenr3rh3JZNIohQDMptFoEiGR+OtHv/DA/XeXS6WVldVWqwWIftvP5rLr1Wou",
        "mw3D0G+3n332e9u3zZS6uy3beeyxJ4IgQEQZa91phJAIgYWQtm3FseoqFk+eWi92dR89duoXf+EDTz39Pc929l59VbPR0OrKxUDH",
        "0lLIz/+vL62urm2dni5XyrlsplmvZ/PZRqN58sxZrXQ6nX78ye8AwB9/8t9JKeM4BDTaoEAodxVX1qp/9Mk/nD1x4n0/8+6VtfVC",
        "oTB76tTY6Ojo2IhSCgw7jhMEQazidtvXSlmW3KhtNJvNTjtI42NjURyHQXDleIONZdlCUDqd3tiod3cVenorJ2dnb9l/05NPP/OX",
        "n/3LVqOezWQcx2WGztBj2LzvPe/q7eubv3Tp81/44pe/9nVNVK23VtY3MpksI7786qu3337z//j0f7GlUHHEWgkSXYViKpX+my9+",
        "6bd+7w9mT53ZunULGxMFYSKR6OmprK6tdvAjpfR9v9Vq2ZZ9eXkljGNj2BjTGYsRUbzznQ888cST5Up569REFAaWtJiBWVu2jGO1",
        "sVnL53ItP1xcXLr19tvPnLvwzDPfUyqSiL29vY7rqDhWSllSXHvttdfecN1d+2+emd7SXSg2NuuSYHJivLdSmpnZcvXVexv1TTY6",
        "k0ymU8mNWv0rX//6n/73R46emB0eGQLm0dGRocEBx3GRqLvU/flHvzA2Orq0tEyItVq1q6srmUweOXJk965dPZWKEPTEE99ptVuI",
        "KIvFLgA8ePDVu26/OY4C27I7aDLGjE+Mff3rswMD/dlMJp1JnTt3fv/+m9dW1w4dOvz4t787Mjy8ZWri2quuyhe7dBg2NjaVVkDC",
        "dhNszPSWSSDW2thWl5BSa91VLIZ+8NLB144eP3Hwtde9RPKmm66vVaulUimO4uHhYbIsw0wI58+f7y6VSNDI6NDpU2eKhWIulwuC",
        "8I47b5/euqXVamUymVQ6ubIKiCjrjfrg4MC58+cXl1bLpQIzG60BBLNJet7MzMzsydM7tk2nU0nLcl566eDWrVuvu+H6VnMnsvqv",
        "f/Lpz9AjP/v+94yMjE6Mjyc8N1YqlU4ZbToxCjYvXrywUau1/OiNI8e+8s0nXz74mus5D/3cB3bu3Lm5UduyZQsSJVy33N1NiNK2",
        "jx8/vrFR7+3tazRaA/39j5954j3veVAplUol65v1o0ePbpuZ2dio1WobnRiQXV3FLdNTzUbfN77x2G/82seazZY2WkobgZUKd+zY",
        "9twPXhTSWV5e27Zta73ZPj9/saenpIxKeu59D9z33NPPvPrKwU995n8mvEQmnQLg3Tt3TkxNOLYTheHq8qVnn3nm+Onzm42WtJ04",
        "VqVyyff9Rz//Ra31HXfc5rruwqVFIATCeqNRLBRWV9cSicTy0lIi4Rx46eXBgcFCIb+2upZKJjOZdCFfyGVzf/6l/1Or1ToK/F+o",
        "i65c5d2dsgAAAABJRU5ErkJggg=="
    ],
    [
        "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"
    ],
    [
        "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",
        "aXFxcXtr+8jRO7Z3dr71re+MDw/HLGvu0KGDBw9GUuq6BiAq5XKn0223WvF4olZrBEEoFQlNi1Tkex4p2fX8ruemMqlLFy9tbVe/",
        "8Y1vPvPMM5sbmwAgBAegVCq9Xa0mEkkpZXlwMJ9LfOm/f3Fre/Ov5gLvqIBt2wfn5hKJRCqVKvYVNM6brdbQ0FAumxkZHgp8f21t",
        "7Wf/3k/9gyc/jkCc8yAMGWKz2QaA4eFhAJJK2ba9tr7hxJwoCpGxeDxx7rXXrly+BEBc6FMze37xU58cGRm+//h958+9JqNQhhEg",
        "er6fy2U7nY7neZzxixcublergwP95187+25bSsaYEOLq1YWxkRHP95OphOu5U1PTA+Xy5MSkaZmdTpuBKvcXFUmOUG/UNU3rut7l",
        "hQUAlS8W89mc4zi2bSmlGo1mLBaLpCJiq2trC4vXLEPLZbNuu5NLp3er1crg4NjocH9fMZfNNOsNpZTjONPTU7Xd3WQiccfhwwcO",
        "7M9k0x/76BNE1Ju+vIMCSqmbN1cG+osjI0NbW5sDA6XrN27kclmpVK1RbzdbqVQqlUikkklENjw0eGV+ngteGigtLCzKoJNJp4uF",
        "AkgaHxp+/4MPvHrqNAIKwf3A3dnd3dyqZnN523FarXo2k0TAzY3Nqcmps6++SlK+fOLlWq1mmsbU1JSuG5VKZahSmZ6eEpqYGB8f",
        "KJV6w8l3yEKze/fedefRQ3NzrVZrbHRUScWA5bI5XYhkIgmIURg6lq1pmuD8J977YMw0l5dvzs7O7N8/GwWRxlmlPPDiiy8amjiw",
        "d8/wSOWLX/zC5uYWEfUVCs1mc3x8wguCfD4XLw4cnTs4XB7oL+QfOHbs5Csnk4n41uZmEIT5fG5za8vz3FjcBsSZmelLl+crg4NE",
        "9MNjX/7G/GNZ5r/6l//ife97cP7KFanU+MTEjWvXhcbHRkYR0dD1Trvtee7c7L7K1J4v/dmfffb3Pr+2vvHH//FPpsbHDu7bOzQ4",
        "6LlueXCQANbWVsfGRkv9pUa98d1nv3fg4IGl6zeymdTjjz3y4osv/dpv/PZLL7x4fXm5Ui5lM6lDdx/3W41XTp1WisqDZdu2FhYW",
        "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"
    ],
    [
        "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"
    ],
    [
        "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",
        "KmCpQGleXF5cuXp1eXFxYmxUyTiK/EwmxUq1W52h4eFms7W5vlXI5y9fvuz7vmmag4ODN1x/favVKpdLb7n33jcdumFwqL68vPTI",
        "w+/9W/d6euKJJ+69587B+uDi4uL+fbOXL11hAMu2AaDT6Zw/d6E+OLC9tTkyVHcdJwyjPXt2rSwtSimjKN63b/b8hYvMIGW8a/cu",
        "EsZIvT5Urtx9682bG2tXFhcc11HAjNDudBzHDvz+yMiwH0ZSSsdxa5Xq2spVZJ4cH3/22WcMwzh69MVLly87jgMA0zNTURxXy1XH",
        "ssMw2rt37/nzF0ZHx+bm9idVa8eBYrEwMTnearVK5XK+UFhaXBobHbdNy7GsQi5vW7YpRBSFtUpZKhVrNTk7t3/v3rOvnPM8b/fu",
        "XZNjIwDgh9H4+HgcyRMnXvY8r1Iq33bLTc888+yf/emXkDCMglKx1O70TFNkM2lDGKVySaQyc/v2To4MuZZ15y033nbz4a8/+cSu",
        "XdNXV1aDIAjDsFKpHPn6kW6n6zouEVmWNTYx/idf+MLMzMzfqEI/9uPvP3nypO/7oyOjgR80m+16fVAguY4zWKnum90rDBGGYbVW",
        "ZcBup/fo7/5eNpv9i6/8xUd+6aOWSTOTE6CUQaSi+P63f3cY+s89/wIQToyO3Hfv3efOnTtx4mQ6k7MsK5V2Dx08YNjWHzz6uU9+",
        "+nce++yjX/vrJ/bM7HItK4rju+68q5DJra2uR3HU6/UEiUwmMzY2trC0JEyRDA6zs7NK63K5ODY2mjAVAGD0ur0rl+cnxse7vW6n",
        "3fE81/XcOI4REE1aW1v1/V4+mylVay88+9xDD//o6TNnhRBaayEEMHz7fXejIAaOoyjjeR/+mZ86e/Zs0O+lHHff9OT7fuSff+w3",
        "Pw6Ii0vLfrc7PjF6/tzFX/zIr5555VwSv4/9xn9773ve7XleFATvfMfbf/4//tLy8tLGxsbo6Kjj2I3G0JX5eddzJiYm0+n0k08+",
        "+a53fu9v/dZvf/vb3vo/fvcz29vbiCiklMVScXp6yrSshYVFKdXU1GQQBkm5PfvKKwvzixvrG4vzC//p137zzNlzSqlEJaGZT5x4",
        "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",
        "SUVORK5CYII="
    ]
]
ICON_DISPLAY_PX = 32  # 約8mm角


def author_icon_label():
    import random
    label = QtWidgets.QLabel()
    label.setAlignment(QtCore.Qt.AlignCenter)
    try:
        pix = QtGui.QPixmap()
        pix.loadFromData(base64.b64decode("".join(random.choice(ICON_SET_PARTS))))
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



# 共作の印: とびうおぴょんぴょんのアイコン 6種 (64px PNG, base64)
# 窓を開くたびに、この中からランダムで1つ出る
ICON_SET_PARTS = [
    [
        "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"
    ],
    [
        "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",
        "x7FWMQDEsXJdN45irUwun/NcLwiC4eEBepMpE81mS2szs3Xa8zwhhSVkJ/78IEBkRHC8xMLiUi6T2rJlS7vRvFKEEbFzj4WgjZYk",
        "ssWi53iWJaQQtmUJgdKSlpRRGGnmZqP5yF/89befenr3rh3JZNIohQDMptFoEiGR+OtHv/DA/XeXS6WVldVWqwWIftvP5rLr1Wou",
        "mw3D0G+3n332e9u3zZS6uy3beeyxJ4IgQEQZa91phJAIgYWQtm3FseoqFk+eWi92dR89duoXf+EDTz39Pc929l59VbPR0OrKxUDH",
        "0lLIz/+vL62urm2dni5XyrlsplmvZ/PZRqN58sxZrXQ6nX78ye8AwB9/8t9JKeM4BDTaoEAodxVX1qp/9Mk/nD1x4n0/8+6VtfVC",
        "oTB76tTY6Ojo2IhSCgw7jhMEQazidtvXSlmW3KhtNJvNTjtI42NjURyHQXDleIONZdlCUDqd3tiod3cVenorJ2dnb9l/05NPP/OX",
        "n/3LVqOezWQcx2WGztBj2LzvPe/q7eubv3Tp81/44pe/9nVNVK23VtY3MpksI7786qu3337z//j0f7GlUHHEWgkSXYViKpX+my9+",
        "6bd+7w9mT53ZunULGxMFYSKR6OmprK6tdvAjpfR9v9Vq2ZZ9eXkljGNj2BjTGYsRUbzznQ888cST5Up569REFAaWtJiBWVu2jGO1",
        "sVnL53ItP1xcXLr19tvPnLvwzDPfUyqSiL29vY7rqDhWSllSXHvttdfecN1d+2+emd7SXSg2NuuSYHJivLdSmpnZcvXVexv1TTY6",
        "k0ymU8mNWv0rX//6n/73R46emB0eGQLm0dGRocEBx3GRqLvU/flHvzA2Orq0tEyItVq1q6srmUweOXJk965dPZWKEPTEE99ptVuI",
        "KIvFLgA8ePDVu26/OY4C27I7aDLGjE+Mff3rswMD/dlMJp1JnTt3fv/+m9dW1w4dOvz4t787Mjy8ZWri2quuyhe7dBg2NjaVVkDC",
        "dhNszPSWSSDW2thWl5BSa91VLIZ+8NLB144eP3Hwtde9RPKmm66vVaulUimO4uHhYbIsw0wI58+f7y6VSNDI6NDpU2eKhWIulwuC",
        "8I47b5/euqXVamUymVQ6ubIKiCjrjfrg4MC58+cXl1bLpQIzG60BBLNJet7MzMzsydM7tk2nU0nLcl566eDWrVuvu+H6VnMnsvqv",
        "f/Lpz9AjP/v+94yMjE6Mjyc8N1YqlU4ZbToxCjYvXrywUau1/OiNI8e+8s0nXz74mus5D/3cB3bu3Lm5UduyZQsSJVy33N1NiNK2",
        "jx8/vrFR7+3tazRaA/39j5954j3veVAplUol65v1o0ePbpuZ2dio1WobnRiQXV3FLdNTzUbfN77x2G/82seazZY2WkobgZUKd+zY",
        "9twPXhTSWV5e27Zta73ZPj9/saenpIxKeu59D9z33NPPvPrKwU995n8mvEQmnQLg3Tt3TkxNOLYTheHq8qVnn3nm+Onzm42WtJ04",
        "VqVyyff9Rz//Ra31HXfc5rruwqVFIATCeqNRLBRWV9cSicTy0lIi4Rx46eXBgcFCIb+2upZKJjOZdCFfyGVzf/6l/1Or1ToK/F+o",
        "i65c5d2dsgAAAABJRU5ErkJggg=="
    ],
    [
        "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"
    ],
    [
        "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",
        "aXFxcXtr+8jRO7Z3dr71re+MDw/HLGvu0KGDBw9GUuq6BiAq5XKn0223WvF4olZrBEEoFQlNi1Tkex4p2fX8ruemMqlLFy9tbVe/",
        "8Y1vPvPMM5sbmwAgBAegVCq9Xa0mEkkpZXlwMJ9LfOm/f3Fre/Ov5gLvqIBt2wfn5hKJRCqVKvYVNM6brdbQ0FAumxkZHgp8f21t",
        "7Wf/3k/9gyc/jkCc8yAMGWKz2QaA4eFhAJJK2ba9tr7hxJwoCpGxeDxx7rXXrly+BEBc6FMze37xU58cGRm+//h958+9JqNQhhEg",
        "er6fy2U7nY7neZzxixcublergwP95187+25bSsaYEOLq1YWxkRHP95OphOu5U1PTA+Xy5MSkaZmdTpuBKvcXFUmOUG/UNU3rut7l",
        "hQUAlS8W89mc4zi2bSmlGo1mLBaLpCJiq2trC4vXLEPLZbNuu5NLp3er1crg4NjocH9fMZfNNOsNpZTjONPTU7Xd3WQiccfhwwcO",
        "7M9k0x/76BNE1Ju+vIMCSqmbN1cG+osjI0NbW5sDA6XrN27kclmpVK1RbzdbqVQqlUikkklENjw0eGV+ngteGigtLCzKoJNJp4uF",
        "AkgaHxp+/4MPvHrqNAIKwf3A3dnd3dyqZnN523FarXo2k0TAzY3Nqcmps6++SlK+fOLlWq1mmsbU1JSuG5VKZahSmZ6eEpqYGB8f",
        "KJV6w8l3yEKze/fedefRQ3NzrVZrbHRUScWA5bI5XYhkIgmIURg6lq1pmuD8J977YMw0l5dvzs7O7N8/GwWRxlmlPPDiiy8amjiw",
        "d8/wSOWLX/zC5uYWEfUVCs1mc3x8wguCfD4XLw4cnTs4XB7oL+QfOHbs5Csnk4n41uZmEIT5fG5za8vz3FjcBsSZmelLl+crg4NE",
        "9MNjX/7G/GNZ5r/6l//ife97cP7KFanU+MTEjWvXhcbHRkYR0dD1Trvtee7c7L7K1J4v/dmfffb3Pr+2vvHH//FPpsbHDu7bOzQ4",
        "6LlueXCQANbWVsfGRkv9pUa98d1nv3fg4IGl6zeymdTjjz3y4osv/dpv/PZLL7x4fXm5Ui5lM6lDdx/3W41XTp1WisqDZdu2FhYW",
        "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"
    ],
    [
        "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"
    ],
    [
        "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",
        "KmCpQGleXF5cuXp1eXFxYmxUyTiK/EwmxUq1W52h4eFms7W5vlXI5y9fvuz7vmmag4ODN1x/favVKpdLb7n33jcdumFwqL68vPTI",
        "w+/9W/d6euKJJ+69587B+uDi4uL+fbOXL11hAMu2AaDT6Zw/d6E+OLC9tTkyVHcdJwyjPXt2rSwtSimjKN63b/b8hYvMIGW8a/cu",
        "EsZIvT5Urtx9682bG2tXFhcc11HAjNDudBzHDvz+yMiwH0ZSSsdxa5Xq2spVZJ4cH3/22WcMwzh69MVLly87jgMA0zNTURxXy1XH",
        "ssMw2rt37/nzF0ZHx+bm9idVa8eBYrEwMTnearVK5XK+UFhaXBobHbdNy7GsQi5vW7YpRBSFtUpZKhVrNTk7t3/v3rOvnPM8b/fu",
        "XZNjIwDgh9H4+HgcyRMnXvY8r1Iq33bLTc888+yf/emXkDCMglKx1O70TFNkM2lDGKVySaQyc/v2To4MuZZ15y033nbz4a8/+cSu",
        "XdNXV1aDIAjDsFKpHPn6kW6n6zouEVmWNTYx/idf+MLMzMzfqEI/9uPvP3nypO/7oyOjgR80m+16fVAguY4zWKnum90rDBGGYbVW",
        "ZcBup/fo7/5eNpv9i6/8xUd+6aOWSTOTE6CUQaSi+P63f3cY+s89/wIQToyO3Hfv3efOnTtx4mQ6k7MsK5V2Dx08YNjWHzz6uU9+",
        "+nce++yjX/vrJ/bM7HItK4rju+68q5DJra2uR3HU6/UEiUwmMzY2trC0JEyRDA6zs7NK63K5ODY2mjAVAGD0ur0rl+cnxse7vW6n",
        "3fE81/XcOI4REE1aW1v1/V4+mylVay88+9xDD//o6TNnhRBaayEEMHz7fXejIAaOoyjjeR/+mZ86e/Zs0O+lHHff9OT7fuSff+w3",
        "Pw6Ii0vLfrc7PjF6/tzFX/zIr5555VwSv4/9xn9773ve7XleFATvfMfbf/4//tLy8tLGxsbo6Kjj2I3G0JX5eddzJiYm0+n0k08+",
        "+a53fu9v/dZvf/vb3vo/fvcz29vbiCiklMVScXp6yrSshYVFKdXU1GQQBkm5PfvKKwvzixvrG4vzC//p137zzNlzSqlEJaGZT5x4",
        "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",
        "SUVORK5CYII="
    ]
]
ICON_DISPLAY_PX = 32  # 約8mm角


def author_icon_label():
    import random
    label = QtWidgets.QLabel()
    label.setAlignment(QtCore.Qt.AlignCenter)
    try:
        pix = QtGui.QPixmap()
        pix.loadFromData(base64.b64decode("".join(random.choice(ICON_SET_PARTS))))
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
        row_lang = QtWidgets.QHBoxLayout()
        row_lang.addWidget(QtWidgets.QLabel(u"スクリプトの種類:"))
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItems([u"Python (.py)", u"MEL (.mel)"])
        self.lang_combo.currentTextChanged.connect(self._on_lang_change)
        row_lang.addWidget(self.lang_combo)
        row_lang.addStretch(1)
        lay.addLayout(row_lang)
        lay.addWidget(QtWidgets.QLabel(u"ファイル名（半角の英字・数字と _ だけ、最後は .py か .mel）:"))
        self.file_edit = QtWidgets.QLineEdit(self._next_file_name(".py"))
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

    def _next_file_name(self, ext):
        scripts_dir = os.path.join(self.root, "scripts")
        n = 1
        while os.path.exists(os.path.join(scripts_dir, "my_script_v%d%s" % (n, ext))):
            n += 1
        return "my_script_v%d%s" % (n, ext)

    def _on_lang_change(self, text):
        ext = ".mel" if "MEL" in text else ".py"
        current = self.file_edit.text().strip()
        base = current
        for old_ext in (".py", ".mel"):
            if base.lower().endswith(old_ext):
                base = base[: -len(old_ext)]
                break
        if not base or base.startswith("my_script_v"):
            self.file_edit.setText(self._next_file_name(ext))
        else:
            self.file_edit.setText(base + ext)

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
        self.setWindowTitle(u"シェルフを作る v19 - スクリプトをシェルフに登録します")
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
        btn_row2.addWidget(self._pill(u"スクリプトを全部外す", self._clear_all))
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
        shelves = shelves_for_delete()
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
            fileMode=1, fileFilter="Script (*.py *.mel)",
            caption=u"シェルフに加えるスクリプトを選んでください（Python か MEL）")
        if not result:
            return
        src = result[0]
        if not src.lower().endswith((".py", ".mel")):
            cmds.warning(u"加えられるのは .py か .mel のファイルだけです。")
            return
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

    def _clear_all(self):
        entries = load_entries(self.root)
        if not entries:
            cmds.warning(u"登録されているスクリプトがありません。")
            return
        answer = cmds.confirmDialog(
            title=u"全部外しますか？",
            message=u"下のリストに出ているスクリプト（今は " + str(len(entries)) + u" 本）を、全部リストから外します。\n"
                    u"外したスクリプトは、シェルフにも持ち帰りファイルにも入りません。\n"
                    u"スクリプトのファイル自体は消えません。",
            button=[u"全部外す", u"やめる"],
            defaultButton=u"やめる", cancelButton=u"やめる", dismissString=u"やめる")
        if answer != u"全部外す":
            return
        save_entries(self.root, [])
        self._refresh_status()
        cmds.inViewMessage(amg=u"<hl>全部外しました</hl>",
                           pos="topCenter", fade=True)

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

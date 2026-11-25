# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : dup_along_path
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya tool: duplicate objects along a curve
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

# -*- coding: utf-8 -*-
"""
Duplicate Along Path (Python版) - dup_along_path.py
majimeru

HighEnd3D の無料MELスクリプト「Duplicate Along Path v1.5.1」
(作者: John Germann、起動コマンド DupAlongPathToolbox) の
Duplicate タブ相当機能を、Python (maya.cmds + PySide) で
クリーンに再実装したもの。元の .mel は参照のみで変更していない。

[元のMEL版との違い = バグ修正ポイント]
1. 配置計算は「弧長 (arc length)」基準。
   位置は MFnNurbsCurve.findParamFromLength() で
   「距離 -> カーブパラメータ」に変換してから取得する
   (いわゆる getPointAtDistance 相当)。元は motionPath の
   uValue とフレーム番号 (startTimeU/endTimeU) 経由の配置で、
   バッファ計算も uValue のパラメータ空間で index 依存の
   補正をかけるなど不整合が多かった。
2. オブジェクト参照は全てフルパス (long name) で保持。
   同名オブジェクトやネームスペースがあっても壊れない。
   (元は短い名前 + グローバル変数 $gGroup 頼みで、名前の
    衝突や別シーンでは Delete/Detach が空振りした。
    motionPath のリネーム先も毎回同じ名前で、連番カウンタと
    Maya の自動ユニーク化が一致する前提で setAttr していた)
3. motionPath を使わない。各複製の位置・回転・スケールを
   カーブ上の点と接線から直接計算して xform で設定する。
   タイムラインの現在時刻を複製数まで動かす、グローバルの
   キータンジェント設定を書き換える、といった元の副作用もない。
4. 全処理を1つの undo チャンクにまとめた。エラー時は
   作りかけのグループを削除して途中状態を残さない。
5. ランダムは random.Random(seed) で再現可能。
   (元は MEL の rand でシード指定不可。回転ランダムは
    int にキャストされて整数度単位に丸まっていた)
6. Start % / End % の対応を正しくした。
   (元は UI の「Start %」スライダが DAPfloatSliderBufferEnd、
    「End %」が DAPfloatSliderBufferStart を編集する
    入れ替わりバグがあった。また Distance モードでは
    開始位置に BufferStart でなく BufferEnd を足していた)
7. Reverse はカーブ自体を reverseCurve で書き換える破壊的な
   元仕様ではなく、配置順を逆にする非破壊トグルにした。

[未実装]
- Deform タブ (メッシュをマージしてカーブに沿って変形させる
  flow path) は未実装。本ツールは Duplicate 機能のみ。
- 元の Shelf ボタン作成メニュー、ヘルプ系リンクは未実装。
- 設定のカーブ保存 (DAPoptions 属性) は元の28項目と同じ
  並びで保存するが、元のUI入れ替わりバグの影響で、MEL版が
  保存したバッファ値はラベルと逆になっている場合がある。

[使い方]
    import dup_along_path
    dup_along_path.show_ui()
  モジュール読み込み後に DupAlongPathToolbox() でも起動できる
  (元のMEL版の起動コマンド名に合わせた互換関数)。
"""

import bisect
import math
import random
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
# ベクトル演算 (タプルベース)
# ---------------------------------------------------------------------------

def _v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _v_len(a):
    return math.sqrt(_v_dot(a, a))


def _v_norm(a, fallback=(1.0, 0.0, 0.0)):
    length = _v_len(a)
    if length < 1e-10:
        return fallback
    return (a[0] / length, a[1] / length, a[2] / length)


# ---------------------------------------------------------------------------
# カーブの弧長サンプリング
# ---------------------------------------------------------------------------

class CurveSampler(object):
    """カーブ上の「弧長ベース」サンプリング (getPointAtDistance 相当)。

    本命は OpenMaya2 の MFnNurbsCurve.findParamFromLength()。
    「距離 -> パラメータ」変換をカーブ自身の弧長計算で行うため、
    CV 間隔が不均一なカーブでも等間隔に配置できる。
    OpenMaya2 が使えない場合は cmds.pointOnCurve の密サンプリング
    + 累積弦長テーブルによる逆引きにフォールバックする。
    """

    SAMPLE_COUNT = 512

    def __init__(self, curve_shape):
        self.shape = curve_shape
        self._fn = None
        self._om = None
        self._cum = None
        self._pts = None
        try:
            import maya.api.OpenMaya as om2
            sel = om2.MSelectionList()
            sel.add(curve_shape)
            self._fn = om2.MFnNurbsCurve(sel.getDagPath(0))
            self._om = om2
            self.length = float(self._fn.length())
        except Exception:
            self._fn = None
            self._build_table()
            self.length = float(self._cum[-1]) if self._cum else 0.0

    def _build_table(self):
        pts = []
        count = self.SAMPLE_COUNT
        for i in range(count + 1):
            t = i / float(count)
            p = cmds.pointOnCurve(self.shape, turnOnPercentage=True,
                                  parameter=t, position=True)
            pts.append((float(p[0]), float(p[1]), float(p[2])))
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + _v_len(_v_sub(pts[i], pts[i - 1])))
        self._pts = pts
        self._cum = cum

    def point_at_distance(self, dist):
        """始点から弧長 dist の点 (ワールド座標) を返す。"""
        d = min(max(float(dist), 0.0), self.length)
        if self._fn is not None:
            param = self._fn.findParamFromLength(d)
            p = self._fn.getPointAtParam(param, self._om.MSpace.kWorld)
            return (float(p.x), float(p.y), float(p.z))
        idx = bisect.bisect_left(self._cum, d)
        if idx <= 0:
            return self._pts[0]
        if idx >= len(self._cum):
            return self._pts[-1]
        seg = self._cum[idx] - self._cum[idx - 1]
        t = 0.0 if seg <= 0 else (d - self._cum[idx - 1]) / seg
        a, b = self._pts[idx - 1], self._pts[idx]
        return (a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t)

    def tangent_at_distance(self, dist):
        """弧長 dist における接線 (正規化済み)。中心差分で求める。"""
        h = max(self.length * 0.0005, 1e-4)
        p1 = self.point_at_distance(dist - h)
        p2 = self.point_at_distance(dist + h)
        return _v_norm(_v_sub(p2, p1), fallback=(1.0, 0.0, 0.0))

    def normal_at_distance(self, dist):
        """弧長 dist における曲率方向 (法線の近似)。直線部では None。"""
        h = max(self.length * 0.0005, 1e-4)
        p0 = self.point_at_distance(dist)
        p1 = self.point_at_distance(dist - h)
        p2 = self.point_at_distance(dist + h)
        n = (p1[0] - 2.0 * p0[0] + p2[0],
             p1[1] - 2.0 * p0[1] + p2[1],
             p1[2] - 2.0 * p0[2] + p2[2])
        if _v_len(n) < 1e-8:
            return None
        return _v_norm(n)


# ---------------------------------------------------------------------------
# フレーム計算 (点 + 接線から回転を作る)
# ---------------------------------------------------------------------------

def _scene_up_vector():
    axis = cmds.upAxis(query=True, axis=True)
    return (0.0, 0.0, 1.0) if axis == "z" else (0.0, 1.0, 0.0)


def compute_transform_on_curve(sampler, dist, front_axis, up_axis,
                              invert_front, invert_up, world_up,
                              twists, flip_front=False):
    """弧長 dist の点における (位置, Euler角[度・XYZ]) を返す。

    twists = (front, up, side) の各軸まわりの追加回転 (度)。
    motionPath の frontTwist / upTwist / sideTwist に相当する。
    flip_front は Reverse 用 (進行方向を逆向きにする)。
    """
    import maya.api.OpenMaya as om2

    pos = sampler.point_at_distance(dist)
    front = sampler.tangent_at_distance(dist)
    if flip_front:
        front = _v_scale(front, -1.0)
    if invert_front:
        front = _v_scale(front, -1.0)

    if world_up == "normal":
        up_ref = sampler.normal_at_distance(dist)
        if up_ref is None:
            up_ref = _scene_up_vector()
    else:
        up_ref = _scene_up_vector()
    if invert_up:
        up_ref = _v_scale(up_ref, -1.0)

    side = _v_cross(up_ref, front)
    if _v_len(side) < 1e-6:
        # 接線とアップ参照が平行な場合のフォールバック
        alt = (1.0, 0.0, 0.0) if abs(front[0]) < 0.9 else (0.0, 0.0, 1.0)
        side = _v_cross(alt, front)
    side = _v_norm(side)
    up = _v_cross(front, side)

    f = front_axis
    u = up_axis
    s = 3 - f - u
    images = {f: front, u: up, s: _v_cross(front, up)}

    # 配置回転: ローカル軸 col の像が images[col] になる行列
    vals = [0.0] * 16
    for col in range(3):
        img = images[col]
        for row in range(3):
            vals[row * 4 + col] = img[row]
    vals[15] = 1.0
    q_align = om2.MTransformationMatrix(om2.MMatrix(vals)).rotation(
        asQuaternion=True)

    # ツイスト回転: ローカル軸まわり (front -> up -> side の順に適用)
    axis_vecs = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]

    def axis_quat(axis_index, degrees):
        return om2.MQuaternion(math.radians(degrees),
                               om2.MVector(*axis_vecs[axis_index]))

    q_twist = (axis_quat(s, twists[2]) * axis_quat(u, twists[1])
               * axis_quat(f, twists[0]))
    q_total = q_align * q_twist
    euler = om2.MTransformationMatrix(q_total.asMatrix()).rotation()
    return pos, (math.degrees(euler.x), math.degrees(euler.y),
                 math.degrees(euler.z))


# ---------------------------------------------------------------------------
# 配置距離の計算
# ---------------------------------------------------------------------------

class DAPError(Exception):
    """ユーザーに見せるためのエラー。"""


def _short_name(long_name):
    return long_name.rsplit("|", 1)[-1]


def _curve_shape(node):
    """トランスフォーム/シェイプから nurbsCurve シェイプのフルパスを返す。"""
    if not node or not cmds.objExists(node):
        return None
    if cmds.nodeType(node) == "nurbsCurve":
        return cmds.ls(node, long=True)[0]
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
    for sh in shapes:
        if cmds.nodeType(sh) == "nurbsCurve":
            return sh
    return None


def compute_distances(length, quantity, distance, buf_start, buf_end,
                      reverse):
    """配置する弧長位置のリストを返す (全て弧長ベース)。

    distance == 0: Quantity 個を [Start%, End%] 区間に均等配置。
    distance > 0: Start% 位置から distance 間隔で配置し、
                  Quantity を上限とする (元の仕様と同じ)。
    """
    start_d = length * buf_start
    end_d = length * (1.0 - buf_end)
    span = end_d - start_d
    if span < 0:
        raise DAPError("Start % + End % が大きすぎて配置区間がありません。")
    if distance > 0:
        n = int(span / distance) + 1
        n = max(1, min(n, int(quantity)))
        dists = [start_d + i * distance for i in range(n)]
    else:
        n = max(1, int(quantity))
        if n == 1:
            dists = [start_d]
        else:
            dists = [start_d + span * i / float(n - 1) for i in range(n)]
    if reverse:
        # カーブを書き換えず、反対側の端から配置したのと同じ結果にする
        dists = [length - d for d in reversed(dists)]
    return dists


# ---------------------------------------------------------------------------
# 複製の実行
# ---------------------------------------------------------------------------

def build_along_path(settings, previous_group=None):
    """複製を実行し、作成したグループのフルパスを返す。

    settings (dict):
        object, curve        : フルパス
        quantity, distance   : 個数 / 間隔 (distance=0 で均等割り)
        buffer_start, buffer_end : 0.0 - 0.999 の割合
        reverse              : 配置順反転
        rotate_values        : (front, up, side) 度
        rotate_behavior      : 'fixed' / 'additive' / 'random'
        rotate_constrain     : (x, y, z) bool (元の回転をその軸だけ維持)
        scale_values         : (x, y, z) 倍率 (元のローカルスケールに乗算)
        scale_behavior       : 'fixed' / 'additive' / 'random'
        scale_constrain      : (x, y, z) bool (軸同士を連動させる)
        scatter_range        : 散らし範囲
        scatter_axes         : (x, y, z) bool
        seed                 : ランダムシード
        dup_type             : 'copy' / 'instance'
        front_axis, up_axis  : 0=X, 1=Y, 2=Z
        invert_front, invert_up : bool
        world_up             : 'scene' / 'normal'
    """
    source = settings["object"]
    curve = settings["curve"]
    if not source or not cmds.objExists(source):
        raise DAPError("Object が未登録か、シーンに存在しません。"
                       "対象を選んで「Object」ボタンで登録してください。")
    shape = _curve_shape(curve)
    if shape is None:
        raise DAPError("Curve が未登録か、NURBSカーブではありません。"
                       "カーブを選んで「Curve」ボタンで登録してください。")

    sampler = CurveSampler(shape)
    if sampler.length <= 0:
        raise DAPError("カーブの長さが 0 です。")

    dists = compute_distances(sampler.length, settings["quantity"],
                              settings["distance"],
                              settings["buffer_start"],
                              settings["buffer_end"],
                              settings["reverse"])
    rng = random.Random(settings["seed"])
    src_scale = cmds.getAttr(source + ".scale")[0]
    src_rot = cmds.xform(source, query=True, rotation=True)

    group = None
    cmds.undoInfo(openChunk=True, chunkName="DupAlongPathPy")
    try:
        if previous_group and cmds.objExists(previous_group):
            cmds.delete(previous_group)
        base = _short_name(source) + "_on_" + _short_name(curve)
        group = cmds.ls(cmds.group(empty=True, name=base), long=True)[0]

        for i, d in enumerate(dists):
            if settings["dup_type"] == "instance":
                new = cmds.instance(source)[0]
            else:
                new = cmds.duplicate(source)[0]
            parented = cmds.parent(new, group)
            if parented:
                new = parented[0]
            new = cmds.ls(new, long=True)[0]

            # --- 回転ツイスト (元の挙動に合わせた Fixed/Additive/Random) ---
            base_tw = settings["rotate_values"]
            if settings["rotate_behavior"] == "random":
                twists = tuple(rng.uniform(-v, v) for v in base_tw)
            elif settings["rotate_behavior"] == "additive":
                # 元: 1個目は値そのもの、以降は値ずつ加算されていく
                twists = tuple((i + 1) * v for v in base_tw)
            else:
                twists = tuple(base_tw)

            pos, euler = compute_transform_on_curve(
                sampler, d,
                settings["front_axis"], settings["up_axis"],
                settings["invert_front"], settings["invert_up"],
                settings["world_up"], twists,
                flip_front=settings["reverse"])

            # Constrain 指定軸は元のオブジェクトの回転を維持する
            if any(settings["rotate_constrain"]):
                euler = tuple(src_rot[a] if settings["rotate_constrain"][a]
                              else euler[a] for a in range(3))

            # --- スケール ---
            v = tuple(settings["scale_values"][a] * src_scale[a]
                      for a in range(3))
            if settings["scale_behavior"] == "random":
                sc = [rng.uniform(min(1.0, v[a]), max(1.0, v[a]))
                      for a in range(3)]
            elif settings["scale_behavior"] == "additive":
                # 元: scale_i = v + i * (v - 1)
                sc = [v[a] + i * (v[a] - 1.0) for a in range(3)]
            else:
                sc = [v[0], v[1], v[2]]
            cx, cy, cz = settings["scale_constrain"]
            if cx and cy:
                sc[1] = sc[0]
            if cy and cz:
                sc[2] = sc[1]
            if cx and cz:
                sc[2] = sc[0]

            # --- スキャッター (ワールド軸方向のランダム移動) ---
            off = tuple(
                rng.uniform(-settings["scatter_range"],
                            settings["scatter_range"])
                if settings["scatter_axes"][a] else 0.0
                for a in range(3))
            pos = _v_add(pos, off)

            cmds.xform(new, worldSpace=True, translation=pos,
                       rotation=euler, scale=tuple(sc))
        cmds.select(group)
    except Exception:
        # 途中状態を残さない (undo でも戻せるが、その場でも片付ける)
        if group and cmds.objExists(group):
            cmds.delete(group)
        raise
    finally:
        cmds.undoInfo(closeChunk=True)
    return group


# ---------------------------------------------------------------------------
# 設定の保存/読み込み (カーブ属性 DAPoptions + optionVar)
# ---------------------------------------------------------------------------

# 元のMEL版 AddAttributeOptions と同じ並び (28項目)。
# 末尾に Python版独自の seed / reverse を追加している
# (MEL版は先頭28項目しか読まないので互換性は保たれる)。
def settings_to_dap_list(s):
    return [
        s["quantity"], s["distance"], s["buffer_start"], s["buffer_end"],
        s["rotate_values"][0], s["rotate_values"][1], s["rotate_values"][2],
        int(s["rotate_constrain"][0]), int(s["rotate_constrain"][1]),
        int(s["rotate_constrain"][2]),
        {"fixed": 1, "additive": 2, "random": 3}[s["rotate_behavior"]],
        s["scale_values"][0], s["scale_values"][1], s["scale_values"][2],
        int(s["scale_constrain"][0]), int(s["scale_constrain"][1]),
        int(s["scale_constrain"][2]),
        {"fixed": 1, "additive": 2, "random": 3}[s["scale_behavior"]],
        s["scatter_range"],
        int(s["scatter_axes"][0]), int(s["scatter_axes"][1]),
        int(s["scatter_axes"][2]),
        1 if s["dup_type"] == "copy" else 2,
        s["front_axis"] + 1, s["up_axis"] + 1,
        2 if s["invert_front"] else 1, 2 if s["invert_up"] else 1,
        1 if s["world_up"] == "scene" else 2,
        s["seed"], 1 if s["reverse"] else 0,
    ]


def dap_list_to_settings(values):
    if len(values) < 28:
        return None
    behavior = {1: "fixed", 2: "additive", 3: "random"}
    s = {
        "quantity": int(values[0]),
        "distance": float(values[1]),
        "buffer_start": float(values[2]),
        "buffer_end": float(values[3]),
        "rotate_values": (float(values[4]), float(values[5]),
                          float(values[6])),
        "rotate_constrain": (bool(int(values[7])), bool(int(values[8])),
                             bool(int(values[9]))),
        "rotate_behavior": behavior.get(int(values[10]), "fixed"),
        "scale_values": (float(values[11]), float(values[12]),
                         float(values[13])),
        "scale_constrain": (bool(int(values[14])), bool(int(values[15])),
                            bool(int(values[16]))),
        "scale_behavior": behavior.get(int(values[17]), "fixed"),
        "scatter_range": float(values[18]),
        "scatter_axes": (bool(int(values[19])), bool(int(values[20])),
                         bool(int(values[21]))),
        "dup_type": "copy" if int(values[22]) == 1 else "instance",
        "front_axis": int(values[23]) - 1,
        "up_axis": int(values[24]) - 1,
        "invert_front": int(values[25]) == 2,
        "invert_up": int(values[26]) == 2,
        "world_up": "scene" if int(values[27]) == 1 else "normal",
        "seed": 1,
        "reverse": False,
    }
    if len(values) >= 30:
        s["seed"] = int(values[28])
        s["reverse"] = bool(int(values[29]))
    return s


def save_settings_to_curve(curve, settings):
    if not curve or not cmds.objExists(curve):
        return
    if not cmds.attributeQuery("DAPoptions", node=curve, exists=True):
        cmds.addAttr(curve, longName="DAPoptions", dataType="string")
    text = " ".join(str(v) for v in settings_to_dap_list(settings))
    cmds.setAttr(curve + ".DAPoptions", text, type="string")


def load_settings_from_curve(curve):
    if not curve or not cmds.objExists(curve):
        return None
    if not cmds.attributeQuery("DAPoptions", node=curve, exists=True):
        return None
    text = cmds.getAttr(curve + ".DAPoptions") or ""
    if not text.strip():
        return None
    try:
        values = [float(tok) for tok in text.split()]
    except ValueError:
        return None
    return dap_list_to_settings(values)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

DEFAULT_SETTINGS = {
    "quantity": 10,
    "distance": 0.0,
    "buffer_start": 0.0,
    "buffer_end": 0.0,
    "reverse": False,
    "rotate_values": (0.0, 0.0, 0.0),
    "rotate_behavior": "fixed",
    "rotate_constrain": (False, False, False),
    "scale_values": (1.0, 1.0, 1.0),
    "scale_behavior": "fixed",
    "scale_constrain": (False, False, False),
    "scatter_range": 0.0,
    "scatter_axes": (False, False, False),
    "seed": 1,
    "dup_type": "copy",
    "front_axis": 0,          # X
    "up_axis": 1,             # Y (Z-up シーンでは show_ui 側で 2 にする)
    "invert_front": False,
    "invert_up": False,
    "world_up": "scene",
}


class DupAlongPathWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DupAlongPathWindow, self).__init__(parent)
        self.setWindowTitle("Duplicate Along Path (Python) v1.0")
        self.setObjectName("DupAlongPathPyWindow")
        self.resize(330, 720)
        self.object_path = ""
        self.curve_path = ""
        self.last_group = None
        self._init_ui()
        self._restore_state()

    # -- UI 構築 ------------------------------------------------------------
    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Duplicate Along Path (Python版)")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        note = QtWidgets.QLabel(
            "MEL版 Duplicate Along Path v1.5.1 の Python 再実装。"
            "Deform 機能は未実装です。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note)

        # Object / Curve 登録
        grid = QtWidgets.QGridLayout()
        self.object_field = QtWidgets.QLineEdit()
        self.object_field.setReadOnly(True)
        self.object_field.setPlaceholderText("Assign Object")
        obj_btn = QtWidgets.QPushButton("Object")
        obj_btn.setToolTip("複製したい対象 (メッシュ/ライト/グループ等) "
                           "を選んで登録")
        obj_btn.clicked.connect(self.assign_object)
        grid.addWidget(self.object_field, 0, 0)
        grid.addWidget(obj_btn, 0, 1)
        self.curve_field = QtWidgets.QLineEdit()
        self.curve_field.setReadOnly(True)
        self.curve_field.setPlaceholderText("Assign Curve")
        curve_btn = QtWidgets.QPushButton("Curve")
        curve_btn.setToolTip("パスにする NURBS カーブを選んで登録")
        curve_btn.clicked.connect(self.assign_curve)
        load_btn = QtWidgets.QPushButton("Load")
        load_btn.setToolTip("カーブに保存された設定 (DAPoptions) を読み込む")
        load_btn.clicked.connect(self.load_from_curve)
        grid.addWidget(self.curve_field, 1, 0)
        curve_row = QtWidgets.QHBoxLayout()
        curve_row.addWidget(curve_btn)
        curve_row.addWidget(load_btn)
        grid.addLayout(curve_row, 1, 1)
        layout.addLayout(grid)

        # Quantity / Distance / Buffers
        form = QtWidgets.QFormLayout()
        form.setSpacing(4)
        self.quantity_spin = QtWidgets.QSpinBox()
        self.quantity_spin.setRange(1, 1000)
        self.quantity_spin.setValue(DEFAULT_SETTINGS["quantity"])
        form.addRow("Quantity", self.quantity_spin)
        self.distance_spin = QtWidgets.QDoubleSpinBox()
        self.distance_spin.setRange(0.0, 100000.0)
        self.distance_spin.setDecimals(2)
        self.distance_spin.setValue(DEFAULT_SETTINGS["distance"])
        self.distance_spin.setToolTip("0 のとき Quantity で均等割り")
        form.addRow("Distance", self.distance_spin)
        self.buffer_start_spin = QtWidgets.QDoubleSpinBox()
        self.buffer_start_spin.setRange(0.0, 0.999)
        self.buffer_start_spin.setDecimals(3)
        self.buffer_start_spin.setSingleStep(0.01)
        form.addRow("Start %", self.buffer_start_spin)
        self.buffer_end_spin = QtWidgets.QDoubleSpinBox()
        self.buffer_end_spin.setRange(0.0, 0.999)
        self.buffer_end_spin.setDecimals(3)
        self.buffer_end_spin.setSingleStep(0.01)
        form.addRow("End %", self.buffer_end_spin)
        layout.addLayout(form)

        self.reverse_check = QtWidgets.QCheckBox("Reverse (配置順を逆に)")
        layout.addWidget(self.reverse_check)

        # 実行ボタン群
        btn_row = QtWidgets.QHBoxLayout()
        dup_btn = QtWidgets.QPushButton("Duplicate / Refresh")
        dup_btn.setToolTip("複製を実行。再実行すると前回の複製を作り直す")
        dup_btn.clicked.connect(self.run_duplicate)
        del_btn = QtWidgets.QPushButton("Delete")
        del_btn.setToolTip("このツールが作った複製グループを削除")
        del_btn.clicked.connect(self.delete_duplicates)
        detach_btn = QtWidgets.QPushButton("Detach")
        detach_btn.setToolTip("複製をグループから出して通常オブジェクト"
                              "として確定 (配置結果はそのまま残る)")
        detach_btn.clicked.connect(self.detach_duplicates)
        btn_row.addWidget(dup_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(detach_btn)
        layout.addLayout(btn_row)

        # ROTATE
        layout.addWidget(self._make_twist_group())
        # SCALE
        layout.addWidget(self._make_scale_group())
        # SCATTER
        layout.addWidget(self._make_scatter_group())
        # OPTIONS
        layout.addWidget(self._make_options_group())

        reset_btn = QtWidgets.QPushButton("Reset Settings")
        reset_btn.clicked.connect(lambda: self.apply_settings(
            dict(DEFAULT_SETTINGS)))
        layout.addWidget(reset_btn)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "background: #fff8e1; color: #333; border: 1px solid #e0c97a;"
            " border-radius: 4px; padding: 6px; font-size: 11px;")
        layout.addWidget(self.status_label)
        layout.addStretch(1)

    def _radio_row(self, labels, default_index=0):
        widget = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        group = QtWidgets.QButtonGroup(widget)
        buttons = []
        for i, label in enumerate(labels):
            btn = QtWidgets.QRadioButton(label)
            group.addButton(btn, i)
            row.addWidget(btn)
            buttons.append(btn)
        buttons[default_index].setChecked(True)
        row.addStretch(1)
        return widget, group, buttons

    def _check_row(self, labels=("X", "Y", "Z")):
        widget = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        checks = []
        for label in labels:
            chk = QtWidgets.QCheckBox(label)
            row.addWidget(chk)
            checks.append(chk)
        row.addStretch(1)
        return widget, checks

    def _make_twist_group(self):
        box = QtWidgets.QGroupBox("ROTATE")
        v = QtWidgets.QVBoxLayout(box)
        self.twist_spins = []
        for label in ("Front", "Up", "Side"):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(0.0, 360.0)
            spin.setDecimals(1)
            spin.setValue(0.0)
            row.addWidget(spin)
            self.twist_spins.append(spin)
            v.addLayout(row)
        con_widget, self.rotate_constrain_checks = self._check_row()
        con_row = QtWidgets.QHBoxLayout()
        con_row.addWidget(QtWidgets.QLabel("Constrain"))
        con_row.addWidget(con_widget)
        v.addLayout(con_row)
        type_widget, self.rotate_behavior_group, _ = self._radio_row(
            ("Fixed", "Additive", "Random"))
        type_row = QtWidgets.QHBoxLayout()
        type_row.addWidget(QtWidgets.QLabel("Type"))
        type_row.addWidget(type_widget)
        v.addLayout(type_row)
        return box

    def _make_scale_group(self):
        box = QtWidgets.QGroupBox("SCALE")
        v = QtWidgets.QVBoxLayout(box)
        self.scale_spins = []
        for label in ("X", "Y", "Z"):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(0.0, 10.0)
            spin.setDecimals(2)
            spin.setSingleStep(0.1)
            spin.setValue(1.0)
            row.addWidget(spin)
            self.scale_spins.append(spin)
            v.addLayout(row)
        con_widget, self.scale_constrain_checks = self._check_row()
        con_row = QtWidgets.QHBoxLayout()
        con_row.addWidget(QtWidgets.QLabel("Constrain"))
        con_row.addWidget(con_widget)
        v.addLayout(con_row)
        type_widget, self.scale_behavior_group, _ = self._radio_row(
            ("Fixed", "Additive", "Random"))
        type_row = QtWidgets.QHBoxLayout()
        type_row.addWidget(QtWidgets.QLabel("Type"))
        type_row.addWidget(type_widget)
        v.addLayout(type_row)
        return box

    def _make_scatter_group(self):
        box = QtWidgets.QGroupBox("SCATTER")
        v = QtWidgets.QVBoxLayout(box)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Range"))
        self.scatter_spin = QtWidgets.QDoubleSpinBox()
        self.scatter_spin.setRange(0.0, 1000.0)
        self.scatter_spin.setDecimals(2)
        self.scatter_spin.setValue(0.0)
        row.addWidget(self.scatter_spin)
        v.addLayout(row)
        dir_widget, self.scatter_checks = self._check_row()
        dir_row = QtWidgets.QHBoxLayout()
        dir_row.addWidget(QtWidgets.QLabel("Direction"))
        dir_row.addWidget(dir_widget)
        v.addLayout(dir_row)
        seed_row = QtWidgets.QHBoxLayout()
        seed_row.addWidget(QtWidgets.QLabel("Seed"))
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(DEFAULT_SETTINGS["seed"])
        self.seed_spin.setToolTip("ランダム (回転/スケール/散らし) のシード。"
                                  "同じ値なら同じ結果になる")
        seed_row.addWidget(self.seed_spin)
        v.addLayout(seed_row)
        return box

    def _make_options_group(self):
        box = QtWidgets.QGroupBox("OPTIONS")
        v = QtWidgets.QVBoxLayout(box)

        def add_row(label, labels, default_index=0):
            widget, group, buttons = self._radio_row(labels, default_index)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label))
            row.addWidget(widget)
            v.addLayout(row)
            return group, buttons

        self.dup_type_group, _ = add_row("Duplicate", ("Copy", "Instance"))
        self.front_axis_group, self.front_axis_buttons = add_row(
            "Front Axis", ("X", "Y", "Z"), DEFAULT_SETTINGS["front_axis"])
        up_default = DEFAULT_SETTINGS["up_axis"]
        if cmds.upAxis(query=True, axis=True) == "z":
            up_default = 2
        self.up_axis_group, self.up_axis_buttons = add_row(
            "Up Axis", ("X", "Y", "Z"), up_default)
        self.invert_front_group, _ = add_row("Front Invert", ("No", "Yes"))
        self.invert_up_group, _ = add_row("Up Invert", ("No", "Yes"))
        self.world_up_group, _ = add_row("World Up", ("Scene", "Normal"))
        # Front と Up が同じ軸にならないようにする (元の SwitchAxis 相当)
        self.front_axis_group.idClicked.connect(self._on_front_axis_changed)
        self.up_axis_group.idClicked.connect(self._on_up_axis_changed)
        return box

    def _on_front_axis_changed(self, axis_id):
        if self.up_axis_group.checkedId() == axis_id:
            other = (axis_id + 1) % 3
            self.up_axis_buttons[other].setChecked(True)

    def _on_up_axis_changed(self, axis_id):
        if self.front_axis_group.checkedId() == axis_id:
            other = (axis_id + 1) % 3
            self.front_axis_buttons[other].setChecked(True)

    # -- 状態の復元 ---------------------------------------------------------
    def _restore_state(self):
        if cmds.optionVar(exists="DAP_Object"):
            path = cmds.optionVar(query="DAP_Object")
            if path and cmds.objExists(path):
                self.object_path = cmds.ls(path, long=True)[0]
                self._update_fields()
        if cmds.optionVar(exists="DAP_Curve"):
            path = cmds.optionVar(query="DAP_Curve")
            if path and cmds.objExists(path):
                self.curve_path = cmds.ls(path, long=True)[0]
                self._update_fields()
        if cmds.optionVar(exists="DAPpy_LastGroup"):
            group = cmds.optionVar(query="DAPpy_LastGroup")
            if group and cmds.objExists(group):
                self.last_group = cmds.ls(group, long=True)[0]

    def _update_fields(self):
        if self.object_path:
            self.object_field.setText(_short_name(self.object_path))
            self.object_field.setToolTip(self.object_path)
        if self.curve_path:
            self.curve_field.setText(_short_name(self.curve_path))
            self.curve_field.setToolTip(self.curve_path)

    def _set_status(self, text):
        self.status_label.setText(text)
        cmds.inViewMessage(assistMessage=text, position="topCenter",
                           fade=True)

    # -- 登録 ---------------------------------------------------------------
    def assign_object(self):
        sel = cmds.ls(selection=True, long=True)
        if not sel:
            self._set_status("対象が未選択です。複製したいオブジェクト"
                             "(メッシュ/ライト/グループ等) を選んでください。")
            cmds.warning("No object selected.")
            return
        self.object_path = sel[0]
        cmds.optionVar(stringValue=("DAP_Object", self.object_path))
        self._update_fields()

    def assign_curve(self):
        sel = cmds.ls(selection=True, long=True)
        if not sel:
            self._set_status("カーブが未選択です。NURBSカーブを選んでください。")
            cmds.warning("No curve selected.")
            return
        if _curve_shape(sel[0]) is None:
            self._set_status("選択オブジェクトに NURBS カーブが含まれていません。")
            cmds.warning("Selected object has no nurbsCurve shape.")
            return
        self.curve_path = sel[0]
        cmds.optionVar(stringValue=("DAP_Curve", self.curve_path))
        self._update_fields()

    # -- 設定の収集/反映 ------------------------------------------------------
    def collect_settings(self):
        behavior = ["fixed", "additive", "random"]
        return {
            "object": self.object_path,
            "curve": self.curve_path,
            "quantity": self.quantity_spin.value(),
            "distance": self.distance_spin.value(),
            "buffer_start": self.buffer_start_spin.value(),
            "buffer_end": self.buffer_end_spin.value(),
            "reverse": self.reverse_check.isChecked(),
            "rotate_values": tuple(s.value() for s in self.twist_spins),
            "rotate_behavior": behavior[self.rotate_behavior_group
                                        .checkedId()],
            "rotate_constrain": tuple(c.isChecked() for c in
                                      self.rotate_constrain_checks),
            "scale_values": tuple(s.value() for s in self.scale_spins),
            "scale_behavior": behavior[self.scale_behavior_group
                                       .checkedId()],
            "scale_constrain": tuple(c.isChecked() for c in
                                     self.scale_constrain_checks),
            "scatter_range": self.scatter_spin.value(),
            "scatter_axes": tuple(c.isChecked() for c in self.scatter_checks),
            "seed": self.seed_spin.value(),
            "dup_type": "copy" if self.dup_type_group.checkedId() == 0
                        else "instance",
            "front_axis": self.front_axis_group.checkedId(),
            "up_axis": self.up_axis_group.checkedId(),
            "invert_front": self.invert_front_group.checkedId() == 1,
            "invert_up": self.invert_up_group.checkedId() == 1,
            "world_up": "scene" if self.world_up_group.checkedId() == 0
                        else "normal",
        }

    def apply_settings(self, s):
        self.quantity_spin.setValue(int(s["quantity"]))
        self.distance_spin.setValue(float(s["distance"]))
        self.buffer_start_spin.setValue(float(s["buffer_start"]))
        self.buffer_end_spin.setValue(float(s["buffer_end"]))
        self.reverse_check.setChecked(bool(s["reverse"]))
        for spin, val in zip(self.twist_spins, s["rotate_values"]):
            spin.setValue(float(val))
        behavior = {"fixed": 0, "additive": 1, "random": 2}
        self.rotate_behavior_group.button(
            behavior[s["rotate_behavior"]]).setChecked(True)
        for chk, val in zip(self.rotate_constrain_checks,
                            s["rotate_constrain"]):
            chk.setChecked(bool(val))
        for spin, val in zip(self.scale_spins, s["scale_values"]):
            spin.setValue(float(val))
        self.scale_behavior_group.button(
            behavior[s["scale_behavior"]]).setChecked(True)
        for chk, val in zip(self.scale_constrain_checks,
                            s["scale_constrain"]):
            chk.setChecked(bool(val))
        self.scatter_spin.setValue(float(s["scatter_range"]))
        for chk, val in zip(self.scatter_checks, s["scatter_axes"]):
            chk.setChecked(bool(val))
        self.seed_spin.setValue(int(s["seed"]))
        self.dup_type_group.button(
            0 if s["dup_type"] == "copy" else 1).setChecked(True)
        self.front_axis_buttons[int(s["front_axis"])].setChecked(True)
        self.up_axis_buttons[int(s["up_axis"])].setChecked(True)
        self.invert_front_group.button(
            1 if s["invert_front"] else 0).setChecked(True)
        self.invert_up_group.button(
            1 if s["invert_up"] else 0).setChecked(True)
        self.world_up_group.button(
            0 if s["world_up"] == "scene" else 1).setChecked(True)

    def load_from_curve(self):
        if not self.curve_path:
            self._set_status("先にカーブを登録してください。")
            return
        settings = load_settings_from_curve(self.curve_path)
        if settings is None:
            self._set_status("このカーブに保存された設定はありません。")
            return
        self.apply_settings(settings)
        self._set_status("カーブに保存された設定を読み込みました。")

    # -- 実行系 -------------------------------------------------------------
    def run_duplicate(self):
        settings = self.collect_settings()
        try:
            group = build_along_path(settings,
                                     previous_group=self.last_group)
        except DAPError as e:
            self._set_status(str(e))
            cmds.warning(str(e))
            return
        except Exception:
            detail = traceback.format_exc()
            cmds.warning("Duplicate Along Path failed:\n" + detail)
            self._set_status("エラーで失敗しました。Script Editor の"
                             "エラーを確認してください。")
            return
        self.last_group = group
        cmds.optionVar(stringValue=("DAPpy_LastGroup", group))
        try:
            save_settings_to_curve(self.curve_path, settings)
        except Exception:
            pass  # 設定保存の失敗で本処理を失敗扱いにしない
        count = len(cmds.listRelatives(group, children=True) or [])
        self._set_status("複製しました: {0} 個 (グループ: {1})".format(
            count, _short_name(group)))

    def delete_duplicates(self):
        if not self.last_group or not cmds.objExists(self.last_group):
            self._set_status("削除できる複製がありません。")
            return
        cmds.undoInfo(openChunk=True, chunkName="DupAlongPathPyDelete")
        try:
            cmds.delete(self.last_group)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.last_group = None
        cmds.optionVar(remove="DAPpy_LastGroup")
        self._set_status("複製を削除しました。")

    def detach_duplicates(self):
        if not self.last_group or not cmds.objExists(self.last_group):
            self._set_status("Detach できる複製がありません。")
            return
        children = cmds.listRelatives(self.last_group, children=True,
                                      fullPath=True) or []
        cmds.undoInfo(openChunk=True, chunkName="DupAlongPathPyDetach")
        try:
            if children:
                cmds.parent(children, world=True)
            cmds.delete(self.last_group)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.last_group = None
        cmds.optionVar(remove="DAPpy_LastGroup")
        self._set_status("Detach しました。複製は通常オブジェクトとして"
                         "確定しています (配置はそのまま)。")


# ---------------------------------------------------------------------------
# 起動
# ---------------------------------------------------------------------------

_window = None


def show_ui():
    global _window
    if _window is not None:
        try:
            _window.close()
            _window.deleteLater()
        except Exception:
            pass
        _window = None
    _window = DupAlongPathWindow(parent=get_maya_window())
    _window.show()
    return _window


def DupAlongPathToolbox():
    """元のMEL版の起動コマンド名に合わせた互換エントリポイント。"""
    return show_ui()

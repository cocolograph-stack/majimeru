# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : benri_rig_V24  v24
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya Python tool
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

# -*- coding: utf-8 -*-
"""
誰でもリグ作れるよツール V24 - majimeru
benri_rig V24 (V23 が土台)

[V24 変更点] (Maya の UI にドッキング可能に)
  ユーザー要望: いつもフローティングになるので、Maya の画面に
  はめ込めたら最高。mayaMixin の MayaQWidgetDockableMixin を土台に
  追加し、show(dockable=True) で出すようにした。上のバーをドラッグ
  すればチャンネルボックス等の横にドッキングできる。ドッキング時は
  最前面固定フラグを外す (枠は Maya が管理)。再表示時は前回の
  workspaceControl を消してから作り直す。使い方ダイアログにも
  ドッキングの一文を追加。mixin が無い環境では従来表示にフォールバック。

[V23 変更点] (軽量化: 図をパレット量子化 + 内蔵データを zlib 圧縮)
  読み込みが少し遅いとの指摘を受けて計測: Python のコンパイル時間は
  V21 (PDFなし) と V22 で実測同等 (約0.05秒)。重さの主因はファイル
  サイズ自体と判断し、図の量子化で PDF を 274KB→239KB に、内蔵は
  zlib 圧縮してから Base64 にし、全体を 480KB→約370KB に削減。
  開くときは展開してから書き出す (処理は一瞬)。

[V22 変更点] (マニュアルPDFをスクリプトに内蔵)
  ユーザー実機で V21 のボタンが「PDFが見つからない」になったため、
  置き場所を探す方式をやめ、PDF そのものを Base64 で内蔵した。
  「マニュアルを開く」を押すと一時フォルダに書き出して開くので、
  ファイル1個だけで必ず開く (初心者が迷わない)。

[V21 変更点] (図解マニュアルPDFと「マニュアルを開く」ボタン)
  図入りの詳しいマニュアル benri_rig_manual.pdf を同梱。
  タイトル横に「マニュアルを開く」ボタンを追加し、PDF を探して
  既定のビューアで開く。探す場所: スクリプトと同じフォルダ →
  デスクトップ → Maya ワークスペース → ホーム。見つからなければ
  下の欄に置き場所を案内し、代わりに短い使い方ダイアログを出す。
  使い方ダイアログの末尾にもマニュアルへの一文を追加。

[V20 変更点] (使い方の見出しから「左の/右の」を削除)
  ユーザー指摘: 「右の」が意味不明。場所の言葉は外して、
  ウィンドウに表示されるグループ名だけで案内する形にした。

[V19 変更点] (「使い方を見る」の文章を箇条書きに)
  ユーザー指示: 使い方の文章を、優しく・初心者向けに・
  箇条書きで・順番が分かるように書き直した。

[V18 変更点] (FKタイトルの注釈を修正)
  ユーザー指摘: （全部の骨に作らなくてもええよ）は違う。
  正しくは「コントローラーも自動で作るよ！」という前向きな一言。
  FKグループのタイトルと、使い方ダイアログの③の文言を直した。

[V17 変更点] (初めての人向け改造)
  - 結果メッセージ欄をウィンドウ下部に追加。成功は緑、失敗は赤で
    理由を表示 (今まではスクリプトエディタに出るだけだった)。
  - タイトル横に「使い方を見る」ボタン (全体の流れを説明)。
  - 流れガイド (①ガイド→②骨→③コントローラ→④くっつける) を追加。
  - 「スキニング」→「モデルを骨にくっつける（スキニング）」、
    「IKツール」→「IKツール（腕や足用）」に改名。

[V16 変更点] (FKグループのタイトルに注釈追加)
  ユーザー指示で「FKコントロール作成」のタイトルに
  （全部の骨に作らなくてもええよ）を追加。

[V15 変更点] (「コントローラー作成」を先頭へ + 骨の場所に作るボタン)
  ユーザー指示: 「コントローラー作成」は FK より前に置く。中身も拡張:
  新ボタン「選んだ骨の場所にコントローラを作る」(makeCtrlAtJoint) =
  選んだ骨と同じ位置・向きに、選んだ形状で作り、フリーズと
  ヒストリ削除まで自動。ミラーボタンもこのグループに取り込んだ
  (単独のミラーグループは廃止)。

[V14 変更点] (FKは四角固定 + 「コントローラー作成」グループ新設)
  ユーザー判断: FK は四角 (キューブ) で十分なので、FK グループから
  形状と軸の選択を外し、FK 作成はキューブ/X軸に固定した。
  形状/軸の選択と「選択した形状に合わせて作る」ボタンは新グループ
  「コントローラー作成」へ移動 (IK と形状合わせはこちらを使う)。
  「IK・形状合わせツール」は「IKツール」に改名。

[V13 変更点] (上部の取り消しボタン行を削除)
  キー (Z / Ctrl+Z) でスマート取り消しができるようになったため、
  ウィンドウ上部の取り消し/やり直し/トグルのボタン行は不要と
  ユーザーが判断し、削除した。キーの割当と復帰の仕組みは V12 のまま。

[V12 変更点] (ホットキーセットの切替を追加し、キー版を完成)
  実機診断で判明: Maya_Default セットは cmds.hotkey の編集を
  黙って捨てるため、V11 の割り当ては反映されなかった。対策:
  開く時に現在のセットのコピー「MajimeruKeys」を作って切り替え、
  そこに割り当てる。閉じたら元のセットに戻す。実機で
  ビューポート Ctrl+Z のスマート取り消しが成功 (2026-11-19)。

[V11 変更点] (Z / Ctrl+Z キー自体をスマートUndoに)
  V10 でボタンは成功。ユーザーはビューポートの Ctrl+Z でも
  同じ動きが必要とのこと。Maya のホットキー (runTimeCommand +
  nameCommand + hotkey) で Z / Shift+Z / Ctrl+Z / Cmd+Z 等を
  スマートUndo/Redo に割り当てるようにした。ウィンドウを
  開いている間だけ有効で、閉じると Maya 標準に戻す。
  ウィンドウ内のトグルボタンでも ON/OFF できる。

[V10 変更点] (スマートUndoのスキップ上限を大幅アップ)
  V9 のログで判明: 作成 (makeFKTR) は取り消せたが、その上に
  選択・無変化のステップが22個以上積もっていて、3個で止まる
  V9 の上限では届かなかった。対策: スキップ上限を 300 ステップ /
  無変化100回まで引き上げ、判定順序も「ノード変化 → 選択変化 →
  座標変化」に直して、選択ステップを座標変化と誤判定しないようにした。

[V9 変更点] (スマートUndoの強化とログ出力)
  V8 のボタンでも取り消せないとの報告を受け、判定を強化:
  選択だけのステップに加えて「何も変化しないステップ」も
  最大3つまで飛ばす。移動/回転の検出も追加 (選択中オブジェクトの
  ワールド座標・回転を比較)。各ステップで何が起きたかを
  スクリプトエディタに print するようにした (切り分け用)。

[V8 変更点] (真の原因への対策: 選択ステップを飛ばす Undo)
  切り分けテスト第3弾で確定した真の原因: Maya は「選択の変更」も
  Undo 履歴に積むため、作成の前後のクリック選択が履歴に挟まり、
  取り消しても選択が戻るだけで作成が消えたように見えなかった
  (実際は3回目の取り消しで親コントローラが消えることを確認)。
  対策: ウィンドウ内の取り消し/やり直しボタンと、ダイアログ表示中の
  Ctrl+Z 等を「スマートUndo」に変更。選択だけが変わるステップは
  自動で飛ばし、実のある操作 (作成/削除/回転など) を1回で取り消す。
  Maya 本体側の通常の取り消し動作はそのまま。

[V7 変更点] (Ctrl+Z が効かない感じの対策)
  ユーザー報告: ツールで作ったものが Ctrl+Z で取り消せない感じ
  (他のオブジェクトは取り消せる)。Qtダイアログにキーボード
  フォーカスが残り、Ctrl+Z がダイアログ側に食われるのが疑い。
  対策: (1) 全ボタンを NoFocus にしてフォーカスを奪わない
        (2) ボタン実行後に Maya 本体へフォーカスを戻す
        (3) ダイアログにフォーカスがあっても Ctrl+Z / Ctrl+Y と
            Z / Shift+Z (文字入力中を除く) を Maya の undo/redo
            へ回すキー処理を追加
        (4) ウィンドウ内に「取り消し」「やり直し」ボタンを追加
        (5) 全ての undoInfo チャンクに名前を付けた (メニューの
            取り消し項目に処理名が出る + まとまりを明示)
        (6) ボタン実行後に undoInfo(state=True) で Undo 有効を保証
        (7) 【本命の修正】createChainFromGuides のチャンクの中で
            autoOrientJoints がもう1つチャンクを開いていた入れ子を解消
            (実処理を _auto_orient_joints_impl に分離)。入れ子チャンクは
            Maya の Undo キューを壊すことが実機スクショで判明:
            キューは空でないのに printQueue が無出力、取り消し履歴が
            名前なしで何も戻らない状態になっていた
        (8) ボタン実行の前後で開きっぱなしチャンクを閉じる救済処理

[V6 変更点] (FKの親子関係と単体作成)
  - FK作成時、親ジョイントのコントローラが既にシーンにあれば、
    今回作ったコントローラをその下に親子付けするようにした
    (今までは同じ回に一緒に作った分同士でしか親子にならなかった)
  - 「FKを1個だけ作る」ボタンを追加: 選んだジョイントだけに作り、
    子ジョイントへは広げない。親子付けは上と同じ

[V5 変更点] (見た目だけ大改造、機能・内容は fix3 と同じ)
  UI を maya.cmds の素のボタンから PySide (Qt) に変えて、
  シンメトリー v22 と同じ様式にそろえた:
  - 全ボタンを丸いピル型 (border-radius) にし、色をやさしい
    パステル系にして、押した時の色変化も付けた
  - レイアウトをコンパクトに (余白・ボタン高さ・間隔を縮小、
    スクロール付き 2 カラム、ウィンドウは小さめ)
  - 区切りは白い線で表示 (fix3 の白区切りを Qt で再現)
  - オフセット階層の注釈は fix3 のまま:
    「オフセット階層は、指コントローラのときに特によく使う」
  ロジック (ガイド/骨/FK/IK/スキニング等) は V4 から不変。
  UI の値読み取りは _UI_STATE 経由に差し替えただけ。

使い方 (Maya の Script Editor で実行):
    exec(open(r"benri_rig_V24.py", encoding="utf-8").read())
  もしくは import して show_ui()
"""

import math
import traceback
import maya.cmds as cmds

try:
    import maya.OpenMayaUI as omui
except Exception:
    omui = None

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui
    except ImportError:
        QtWidgets = None
        QtCore = None
        QtGui = None

# Maya の UI にドッキングするための土台 (無い環境では None = 従来表示)
try:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
except Exception:
    MayaQWidgetDockableMixin = None


# ---------------------------------------------------------------------------
# UI 状態 (Qt ウィジェットの値をロジックから読むための置き場所)
# ---------------------------------------------------------------------------

_UI_STATE = {
    "guidePreset": "🦴 背骨〜頭のガイドセット (6個)",
    "renamePreset": "root",
    "sidePreset": "なし",
    "fingerPreset": "th",
    "fingerSidePreset": "なし",
    "controlShape": "正六面体（キューブ）",
    "controlAxis": "X軸（骨の標準）",
    "controlSize": 1.0,
    "controlColorRGB": (0.3, 0.7, 1.0),
    "colorPreset": "青",
    "controlPrefix": "",
    "controlName": "_CTRL",
    "useOffsetGrp": False,
    "applyColorRGB": (0.3, 0.7, 1.0),
}

_window = None


def _ui_get(key, default=None):
    return _UI_STATE.get(key, default)


def _ui_set(key, value):
    _UI_STATE[key] = value



def _create_control(rgb_color, shape_type=None, axis=None):
    if shape_type is None:
        shape_type = _ui_get("controlShape", "正六面体（キューブ）")

    if axis is None:
        axis_val = _ui_get("controlAxis", "X軸（骨の標準）")
        if "X" in axis_val:
            axis = "X"
        elif "Z" in axis_val:
            axis = "Z"
        else:
            axis = "Y"

    if shape_type == "球（スフィア）":
        pts = []
        for i in range(17):
            a = math.radians(i * 22.5)
            pts.append((math.cos(a) * 0.5, 0.0, math.sin(a) * 0.5))
        for i in range(1, 17):
            a = math.radians(i * 22.5)
            pts.append((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.0))
        pts.append((0.0, 0.5, 0.0))
        for i in range(1, 17):
            a = math.radians(i * 22.5)
            pts.append((0.0, math.cos(a) * 0.5, math.sin(a) * 0.5))
        ctrl = cmds.curve(d=1, p=pts)

    elif shape_type == "円錐（コーン）":
        pts = []
        for i in range(17):
            a = math.radians(i * 22.5)
            pts.append((math.cos(a) * 0.5, -0.5, math.sin(a) * 0.5))
        pts.extend([
            (0.0, 0.5, 0.0), (-0.5, -0.5, 0.0),
            (0.0, 0.5, 0.0), (0.0, -0.5, 0.5),
            (0.0, 0.5, 0.0), (0.0, -0.5, -0.5)
        ])
        ctrl = cmds.curve(d=1, p=pts)
        if axis == "X":
            cmds.rotate(0, 0, -90, ctrl, r=True)
            cmds.makeIdentity(ctrl, apply=True, t=1, r=1, s=1, n=0)
        elif axis == "Z":
            cmds.rotate(90, 0, 0, ctrl, r=True)
            cmds.makeIdentity(ctrl, apply=True, t=1, r=1, s=1, n=0)

    elif shape_type == "円（サークル）":
        pts = []
        for i in range(17):
            a = math.radians(i * 22.5)
            if axis == "X":
                pts.append((0.0, math.cos(a) * 0.5, math.sin(a) * 0.5))
            elif axis == "Z":
                pts.append((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.0))
            else:
                pts.append((math.cos(a) * 0.5, 0.0, math.sin(a) * 0.5))
        ctrl = cmds.curve(d=1, p=pts)

    elif shape_type == "ダイヤ（八面体）":
        pts = [
            (0.5, 0.0, 0.0), (0.0, 0.0, 0.5), (-0.5, 0.0, 0.0), (0.0, 0.0, -0.5), (0.5, 0.0, 0.0),
            (0.0, 0.5, 0.0), (-0.5, 0.0, 0.0), (0.0, -0.5, 0.0), (0.5, 0.0, 0.0),
            (0.0, 0.5, 0.0), (0.0, 0.0, 0.5), (0.0, -0.5, 0.0), (0.0, 0.0, -0.5), (0.0, 0.5, 0.0)
        ]
        ctrl = cmds.curve(d=1, p=pts)

    else:
        ctrl = cmds.curve(d=1, p=[
            (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
            (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5),
            (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5),
            (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5)
        ])

    shapes = cmds.listRelatives(ctrl, shapes=True, fullPath=True)
    if shapes:
        for shape in shapes:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideRGBColors", 1)
            cmds.setAttr(shape + ".overrideColorRGB", rgb_color[0], rgb_color[1], rgb_color[2])
    return ctrl

def _make_guide_sphere_node(name, pos, radius=0.3, color=(1.0, 1.0, 0.0)):
    sphere = cmds.polySphere(radius=radius, subdivisionsX=10, subdivisionsY=10, name=name)[0]
    cmds.xform(sphere, ws=True, t=pos)
    
    # べた塗り用のランバートマテリアルを作成してアサイン
    mat_name = "majimeru_guideMat_" + str(int(color[0]*100)) + "_" + str(int(color[1]*100)) + "_" + str(int(color[2]*100))
    sg_name = mat_name + "_SG"
    
    if not cmds.objExists(mat_name):
        mat = cmds.shadingNode("lambert", asShader=True, name=mat_name)
        cmds.setAttr(mat + ".color", color[0], color[1], color[2])
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
        cmds.connectAttr(mat + ".outColor", sg_name + ".surfaceShader", force=True)
    
    try:
        cmds.sets(sphere, edit=True, forceElement=sg_name)
    except Exception:
        pass
        
    return sphere

def _create_guide_link_lines(guides, parent_grp=None):
    if len(guides) < 2:
        return []
    line_nodes = []
    for i in range(len(guides) - 1):
        g1 = guides[i]
        g2 = guides[i + 1]
        p1 = cmds.xform(g1, q=True, ws=True, t=True)
        p2 = cmds.xform(g2, q=True, ws=True, t=True)
        
        line = cmds.curve(d=1, p=[p1, p2], name="majimeru_guideLine_01")
        shapes = cmds.listRelatives(line, shapes=True, fullPath=True) or []
        for s in shapes:
            cmds.setAttr(s + ".overrideEnabled", 1)
            cmds.setAttr(s + ".overrideDisplayType", 2)
            
        c1 = cmds.cluster(line + ".cv[0]", name=g1.split("|")[-1] + "_cls")[1]
        c2 = cmds.cluster(line + ".cv[1]", name=g2.split("|")[-1] + "_cls")[1]
        cmds.setAttr(c1 + ".visibility", 0)
        cmds.setAttr(c2 + ".visibility", 0)
        
        cmds.pointConstraint(g1, c1, mo=False)
        cmds.pointConstraint(g2, c2, mo=False)
        
        link_grp = cmds.group(line, c1, c2, name="majimeru_guideLink_GRP")
        if parent_grp and cmds.objExists(parent_grp):
            cmds.parent(link_grp, parent_grp)
        line_nodes.append(link_grp)
    return line_nodes

def connectSelectedGuidesWithLines(*args):
    cmds.undoInfo(openChunk=True, chunkName="connectSelectedGuidesWithLines")
    try:
        sel = cmds.ls(sl=True, long=True)
        if len(sel) < 2:
            cmds.error("ガイドラインで繋ぎたいガイド球を、必ず【根元（親）から先端（子）の順番】に2つ以上選択してください。")
        _create_guide_link_lines(sel)
        cmds.select(sel)
    finally:
        cmds.undoInfo(closeChunk=True)

def _get_side_tag():
    side_val = _ui_get("sidePreset", "なし")
    if side_val == "_L":
        return "", "_L"
    elif side_val == "_R":
        return "", "_R"
    elif side_val == "L_":
        return "L_", ""
    elif side_val == "R_":
        return "R_", ""
    return "", ""

def _get_finger_side_tag():
    side_val = _ui_get("fingerSidePreset", "なし")
    if side_val == "_L":
        return "", "_L"
    elif side_val == "_R":
        return "", "_R"
    elif side_val == "L_":
        return "L_", ""
    elif side_val == "R_":
        return "R_", ""
    return "", ""

def _auto_orient_joints_impl():
    # チャンクなしの実処理。createChainFromGuides のチャンク内からも
    # 呼ばれるため、ここで undoInfo を開くとチャンクが入れ子になって
    # Maya の Undo キューが壊れる (V7で修正した不具合の原因)
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("向きを整えるジョイント（根元など）を選択してください。")
            
        cmds.makeIdentity(selection, apply=True, t=0, r=1, s=1, n=0)
        
        for jnt in selection:
            descendants = cmds.listRelatives(jnt, allDescendents=True, type="joint", fullPath=True) or []
            if descendants:
                descendants.reverse()
            all_joints = [jnt] + descendants
            
            sec_axis = "yup"
            children_first = cmds.listRelatives(jnt, children=True, type="joint", fullPath=True)
            if children_first:
                p1 = cmds.xform(jnt, q=True, ws=True, t=True)
                p2 = cmds.xform(children_first[0], q=True, ws=True, t=True)
                dx = abs(p2[0] - p1[0])
                dy = abs(p2[1] - p1[1])
                dz = abs(p2[2] - p1[2])
                if dy >= dx and dy >= dz:
                    sec_axis = "zup"
            
            for d in all_joints:
                cmds.setAttr(d + ".rotateX", 0)
                cmds.setAttr(d + ".rotateY", 0)
                cmds.setAttr(d + ".rotateZ", 0)

                children = cmds.listRelatives(d, children=True, type="joint", fullPath=True)
                if children:
                    cmds.joint(d, e=True, orientJoint="xyz", secondaryAxisOrient=sec_axis, children=False, zeroScaleOrient=True)
                else:
                    cmds.joint(d, e=True, orientJoint="none", zeroScaleOrient=True)
                    cmds.setAttr(d + ".jointOrientX", 0)
                    cmds.setAttr(d + ".jointOrientY", 0)
                    cmds.setAttr(d + ".jointOrientZ", 0)
    except Exception:
        raise


def autoOrientJoints(*args):
    cmds.undoInfo(openChunk=True, chunkName="autoOrientJoints")
    try:
        _auto_orient_joints_impl()
    finally:
        cmds.undoInfo(closeChunk=True)

def zeroJointOrientAndRotate(*args):
    cmds.undoInfo(openChunk=True, chunkName="zeroJointOrientAndRotate")
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("角度を0にしたいジョイントを選択してください。")
            
        target_joints = list(selection)
        for jnt in selection:
            descendants = cmds.listRelatives(jnt, allDescendents=True, type="joint", fullPath=True)
            if descendants:
                target_joints.extend(descendants)
                
        for jnt in set(target_joints):
            cmds.setAttr(jnt + ".rotateX", 0)
            cmds.setAttr(jnt + ".rotateY", 0)
            cmds.setAttr(jnt + ".rotateZ", 0)
            cmds.setAttr(jnt + ".jointOrientX", 0)
            cmds.setAttr(jnt + ".jointOrientY", 0)
            cmds.setAttr(jnt + ".jointOrientZ", 0)
    finally:
        cmds.undoInfo(closeChunk=True)

def toggleJointLocalAxis(*args):
    cmds.undoInfo(openChunk=True, chunkName="toggleJointLocalAxis")
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("軸を表示/非表示するジョイントを選択してください。")
            
        target_joints = list(selection)
        for jnt in selection:
            descendants = cmds.listRelatives(jnt, allDescendents=True, type="joint", fullPath=True)
            if descendants:
                target_joints.extend(descendants)
                
        target_joints = list(set(target_joints))
        current_state = cmds.getAttr(target_joints[0] + ".displayLocalAxis")
        new_state = not current_state
        for jnt in target_joints:
            cmds.setAttr(jnt + ".displayLocalAxis", new_state)
    finally:
        cmds.undoInfo(closeChunk=True)

def spawnGuideSphere(*args):
    cmds.undoInfo(openChunk=True, chunkName="spawnGuideSphere")
    try:
        g = _make_guide_sphere_node("majimeru_guideSPHERE_01", (0, 0, 0), radius=0.4, color=(1.0, 1.0, 0.0))
        cmds.select(g)
    finally:
        cmds.undoInfo(closeChunk=True)

def spawnPresetGuides(*args):
    cmds.undoInfo(openChunk=True, chunkName="spawnPresetGuides")
    try:
        preset = _ui_get("guidePreset", "🦴 背骨〜頭のガイドセット (6個)")
        
        if "背骨" in preset:
            grp = cmds.group(em=True, name="majimeru_Spine_Guides_GRP")
            data = [
                ("pelvis_GUIDE", (0, 10, 0)),
                ("spine01_GUIDE", (0, 11.5, 0)),
                ("spine02_GUIDE", (0, 13, 0)),
                ("chest_GUIDE", (0, 14.5, 0)),
                ("neck_GUIDE", (0, 16, 0)),
                ("head_GUIDE", (0, 17.5, 0))
            ]
            created = []
            for name, pos in data:
                g = _make_guide_sphere_node(name, pos, radius=0.4, color=(1.0, 0.9, 0.0))
                cmds.parent(g, grp)
                created.append(g)
            _create_guide_link_lines(created, parent_grp=grp)
            cmds.select(created)
            
        elif "腕" in preset:
            grp = cmds.group(em=True, name="majimeru_Arm_L_Guides_GRP")
            data = [
                ("clavicle_L_GUIDE", (1.0, 14.5, 0)),
                ("uarm_L_GUIDE", (2.5, 14.5, 0)),
                ("elbow_L_GUIDE", (5.0, 14.5, -0.5)),
                ("wrist_L_GUIDE", (7.5, 14.5, 0))
            ]
            created = []
            for name, pos in data:
                g = _make_guide_sphere_node(name, pos, radius=0.35, color=(1.0, 0.85, 0.0))
                cmds.parent(g, grp)
                created.append(g)
            _create_guide_link_lines(created, parent_grp=grp)
            cmds.select(created)

        elif "脚" in preset:
            grp = cmds.group(em=True, name="majimeru_Leg_L_Guides_GRP")
            data = [
                ("hip_L_GUIDE", (1.2, 9.5, 0)),
                ("knee_L_GUIDE", (1.2, 5.5, 0.5)),
                ("ankle_L_GUIDE", (1.2, 1.5, 0)),
                ("ball_L_GUIDE", (1.2, 0.5, 1.2)),
                ("toe_L_GUIDE", (1.2, 0.5, 2.2))
            ]
            created = []
            for name, pos in data:
                g = _make_guide_sphere_node(name, pos, radius=0.4, color=(1.0, 0.85, 0.0))
                cmds.parent(g, grp)
                created.append(g)
            _create_guide_link_lines(created, parent_grp=grp)
            cmds.select(created)

        elif "指" in preset:
            main_grp = cmds.group(em=True, name="majimeru_Fingers_L_Guides_GRP")
            fingers = [
                ("th", 0.8, [(8.0, 14.2, 0.8), (8.4, 14.2, 1.2), (8.8, 14.2, 1.5), (9.2, 14.2, 1.8)]),
                ("in", 0.5, [(8.2, 14.5, 0.5), (8.8, 14.5, 0.5), (9.3, 14.5, 0.5), (9.7, 14.5, 0.5)]),
                ("mi", 0.0, [(8.2, 14.5, 0.0), (8.9, 14.5, 0.0), (9.5, 14.5, 0.0), (10.0, 14.5, 0.0)]),
                ("ri", -0.5, [(8.2, 14.5, -0.5), (8.8, 14.5, -0.5), (9.3, 14.5, -0.5), (9.7, 14.5, -0.5)]),
                ("p", -1.0, [(8.1, 14.5, -1.0), (8.6, 14.5, -1.0), (9.0, 14.5, -1.0), (9.3, 14.5, -1.0)])
            ]
            for fname, z_off, pts in fingers:
                f_grp = cmds.group(em=True, name="majimeru_" + fname + "_L_Guides_GRP", parent=main_grp)
                f_guides = []
                for idx, pos in enumerate(pts):
                    g_name = "{}_{}_L_GUIDE".format(fname, str(idx+1).zfill(2))
                    g = _make_guide_sphere_node(g_name, pos, radius=0.12, color=(1.0, 0.95, 0.2))
                    cmds.parent(g, f_grp)
                    f_guides.append(g)
                _create_guide_link_lines(f_guides, parent_grp=f_grp)
            cmds.select(main_grp)
    finally:
        cmds.undoInfo(closeChunk=True)

def _is_valid_guide_sphere(node):
    short = node.split("|")[-1]
    if "guideLink_GRP" in short or "guideLine" in short or "_cls" in short:
        return False
    shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
    return len(shapes) > 0

def _build_joint_chain_from_guide_list(guide_list, controlPref):
    positions = []
    names = []
    for obj in guide_list:
        pos = cmds.xform(obj, q=True, ws=True, t=True)
        positions.append(pos)
        short = obj.split("|")[-1]
        if "_GUIDE" in short:
            base = short.split("_GUIDE")[0]
            names.append(controlPref + base + "_JNT")
        else:
            names.append(None)
            
    cmds.select(clear=True)
    created_joints = []
    for i, pos in enumerate(positions):
        j_name = names[i] if names[i] else (controlPref + "guideJoint_" + str(i+1).zfill(2) + "_JNT")
        if cmds.objExists(j_name):
            j_name = j_name + "#"
        jnt = cmds.joint(p=pos, name=j_name)
        created_joints.append(jnt)
        
    if created_joints:
        cmds.select(created_joints[0])
        _auto_orient_joints_impl()
        all_j = [created_joints[0]] + (cmds.listRelatives(created_joints[0], allDescendents=True, type="joint", fullPath=True) or [])
        for j in all_j:
            cmds.setAttr(j + ".rotateX", 0)
            cmds.setAttr(j + ".rotateY", 0)
            cmds.setAttr(j + ".rotateZ", 0)
    return created_joints

def createChainFromGuides(*args):
    cmds.undoInfo(openChunk=True, chunkName="createChainFromGuides")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("配置したガイド球（またはグループ）を選択してください。\n※自分で置いた球を繋ぐときは、必ず【根元（親）から先端（子）の順番】にポチポチ選択してね！")
            
        controlPref = _ui_get("controlPrefix", "")
        
        chains_to_build = []
        nodes_to_cleanup = []

        if len(selection) == 1 and not cmds.listRelatives(selection[0], shapes=True):
            sub_children = cmds.listRelatives(selection[0], children=True, type="transform", fullPath=True) or []
            sub_grps = [c for c in sub_children if "_Guides_GRP" in c.split("|")[-1]]
            if sub_grps:
                for sub_grp in sub_grps:
                    raw_children = cmds.listRelatives(sub_grp, children=True, type="transform", fullPath=True) or []
                    guides = [g for g in raw_children if _is_valid_guide_sphere(g)]
                    if len(guides) >= 2:
                        chains_to_build.append(guides)
                nodes_to_cleanup.append(selection[0])
            else:
                guides = [g for g in sub_children if _is_valid_guide_sphere(g)]
                if len(guides) >= 2:
                    chains_to_build.append(guides)
                    nodes_to_cleanup.append(selection[0])
        else:
            guides = [g for g in selection if _is_valid_guide_sphere(g)]
            if len(guides) < 2:
                cmds.error("ガイド球を2つ以上選んでね。\n※自分で置いた球は、必ず【根元（親）から先端（子）の順番】で選択してね！")
            chains_to_build.append(guides)
            nodes_to_cleanup.extend(guides)
            for obj in guides:
                parents = cmds.listRelatives(obj, parent=True, fullPath=True)
                if parents and "_Guides_GRP" in parents[0]:
                    nodes_to_cleanup.append(parents[0])
                    top_p = cmds.listRelatives(parents[0], parent=True, fullPath=True)
                    if top_p and "_Guides_GRP" in top_p[0]:
                        nodes_to_cleanup.append(top_p[0])

        for g in [item for sublist in chains_to_build for item in sublist]:
            conns = cmds.listConnections(g, type="pointConstraint") or []
            for c in conns:
                p_list = cmds.listRelatives(c, parent=True, fullPath=True) or []
                for p in p_list:
                    top_link = cmds.listRelatives(p, parent=True, fullPath=True) or []
                    for tl in top_link:
                        if "guideLink_GRP" in tl:
                            nodes_to_cleanup.append(tl)

        root_joints = []
        for guide_list in chains_to_build:
            created = _build_joint_chain_from_guide_list(guide_list, controlPref)
            if created:
                root_joints.append(created[0])

        for item in set(nodes_to_cleanup):
            if cmds.objExists(item):
                try:
                    cmds.delete(item)
                except Exception:
                    pass

        if root_joints:
            cmds.select(root_joints)
            cmds.confirmDialog(title="やったね！", message="ガイドから綺麗な骨ができたよ！角度もすべて0にリセットして、ガイドは自動で消去したで！", button=["OK"])
    finally:
        cmds.undoInfo(closeChunk=True)

def mirrorJointsCmd(*args):
    cmds.undoInfo(openChunk=True, chunkName="mirrorJointsCmd")
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("ミラーコピーしたい「骨の根元」を選択してね。")
            
        for jnt in selection:
            short_name = jnt.split("|")[-1]
            search_str, replace_str = "_L", "_R"
            if "_R" in short_name:
                search_str, replace_str = "_R", "_L"
            elif short_name.startswith("L_"):
                search_str, replace_str = "L_", "R_"
            elif short_name.startswith("R_"):
                search_str, replace_str = "R_", "L_"
                
            cmds.mirrorJoint(jnt, mirrorYZ=True, mirrorBehavior=True, searchReplace=(search_str, replace_str))
    finally:
        cmds.undoInfo(closeChunk=True)

def quickBindSkin(*args):
    cmds.undoInfo(openChunk=True, chunkName="quickBindSkin")
    try:
        sel = cmds.ls(sl=True, long=True)
        if len(sel) < 2:
            cmds.error("「骨の根元」と「モデル（メッシュ）」の両方を選択してね。")
            
        joints = []
        meshes = []
        for obj in sel:
            if cmds.nodeType(obj) == "joint":
                joints.append(obj)
            else:
                shapes = cmds.listRelatives(obj, shapes=True, type="mesh", fullPath=True)
                if shapes:
                    meshes.append(obj)
                else:
                    desc_jnts = cmds.listRelatives(obj, allDescendents=True, type="joint", fullPath=True)
                    if desc_jnts:
                        joints.extend(desc_jnts)
                        
        if not joints or not meshes:
            cmds.error("選択範囲に「骨」と「モデル」の両方が含まれているか確認してね。")
            
        for m in meshes:
            cmds.skinCluster(joints, m, toSelectedBones=False, bindMethod=0, skinMethod=0, normalizeWeights=1, maximumInfluences=4)
        cmds.confirmDialog(title="バインド成功！", message="骨とモデルが綺麗にくっついたよ（スキニング完了）！", button=["OK"])
    finally:
        cmds.undoInfo(closeChunk=True)

def mirrorSkinWeightsCmd(*args):
    cmds.undoInfo(openChunk=True, chunkName="mirrorSkinWeightsCmd")
    try:
        sel = cmds.ls(sl=True, long=True)
        if not sel:
            cmds.error("ウェイトをミラーしたいモデルを選択してね。")
        for obj in sel:
            cmds.copySkinWeights(obj, mirrorMode="YZ", surfaceAssociation="closestPoint", influenceAssociation=("label", "closestJoint", "oneToOne"))
        cmds.confirmDialog(title="完了", message="スキンウェイトを反対側に綺麗にコピーしたよ！", button=["OK"])
    finally:
        cmds.undoInfo(closeChunk=True)

def mirrorControls(*args):
    cmds.undoInfo(openChunk=True, chunkName="mirrorControls")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("ミラーしたいコントローラーを選んでね。")
            
        def get_opp_name(n):
            if "_L" in n:
                return n.replace("_L", "_R")
            elif "_R" in n:
                return n.replace("_R", "_L")
            elif n.startswith("L_"):
                return "R_" + n[2:]
            elif n.startswith("R_"):
                return "L_" + n[2:]
            else:
                return n + "_mirror"

        for obj in selection:
            short_name = obj.split("|")[-1]
            
            target_to_dup = obj
            parents = cmds.listRelatives(obj, parent=True, fullPath=True)
            if short_name.endswith("_CTRL") and parents and parents[0].split("|")[-1].endswith("_GRP"):
                target_to_dup = parents[0]
            
            target_short = target_to_dup.split("|")[-1]
            opp_root_name = get_opp_name(target_short)
            
            if cmds.objExists(opp_root_name):
                cmds.warning("ミラー先のオブジェクト '" + opp_root_name + "' はすでに存在します。スキップするね。")
                continue
                
            dup_root = cmds.duplicate(target_to_dup, upstreamNodes=False)[0]
            
            old_Trash = cmds.listRelatives(dup_root, allDescendents=True, type=("constraint", "ikHandle"), fullPath=True) or []
            if old_Trash:
                cmds.delete(old_Trash)

            mir_grp = cmds.group(dup_root, name=dup_root + "_mirror_temp")
            cmds.xform(mir_grp, ws=True, piv=(0, 0, 0))
            cmds.setAttr(mir_grp + ".scaleX", -1)
            
            cmds.parent(dup_root, world=True)
            cmds.delete(mir_grp)
            
            new_root = cmds.rename(dup_root, opp_root_name)
            
            all_nodes = [new_root] + (cmds.listRelatives(new_root, allDescendents=True, type="transform", fullPath=True) or [])
            all_nodes.sort(key=lambda x: x.count('|'), reverse=True)
            
            for node in all_nodes:
                node_short = node.split("|")[-1]
                if node != new_root:
                    opp_sub_name = get_opp_name(node_short)
                    if not cmds.objExists(opp_sub_name):
                        node = cmds.rename(node, opp_sub_name)
                try:
                    cmds.select(node)
                    cmds.makeIdentity(apply=True, t=0, r=0, s=1, n=0)
                except Exception:
                    pass
                    
            controls = [new_root] + (cmds.listRelatives(new_root, allDescendents=True, type="transform", fullPath=True) or [])
            for ctrl in controls:
                ctrl_short = ctrl.split("|")[-1]
                if ctrl_short.endswith("_CTRL"):
                    jnt_name = ctrl_short.replace("_CTRL", "_JNT")
                    if cmds.objExists(jnt_name):
                        cmds.parentConstraint(ctrl, jnt_name, mo=True)
    finally:
        cmds.undoInfo(closeChunk=True)

def _find_existing_fk_ctrl(jnt, controlPref, controlSuff):
    # 親ジョイント用に既にあるコントローラを探す (今回作った分は除く想定で呼ぶ側が判定)
    short_name = jnt.split("|")[-1]
    base_name = short_name.replace("_JNT", "").replace("_jnt", "")
    expected = controlPref + base_name + controlSuff
    if cmds.objExists(expected):
        found = cmds.ls(expected, long=True, type="transform") or []
        if found:
            return found[0]
        return expected
    # 接頭辞が違って作られていた場合の保険: 名前の末尾が一致するものを探す
    try:
        candidates = cmds.ls("*" + base_name + controlSuff, long=True, type="transform") or []
    except Exception:
        candidates = []
    for cand in candidates:
        if cand.split("|")[-1] == base_name + controlSuff or cand.split("|")[-1].endswith(base_name + controlSuff):
            return cand
    return None


def _build_fk_controls(target_joints):
    # FKコントローラを実際に作る共通処理 (チェーン用も単体用もここを使う)
    controlSize = _ui_get("controlSize", 1.0)
    controlPref = _ui_get("controlPrefix", "")
    controlSuff = _ui_get("controlName", "_CTRL")
    rgbColor = _ui_get("controlColorRGB", (0.3, 0.7, 1.0))
    useOffsetGrp = _ui_get("useOffsetGrp", False)

    for jnt in target_joints:
        short_name = jnt.split("|")[-1]
        base_name = short_name.replace("_JNT", "").replace("_jnt", "")
        full_name = controlPref + base_name + controlSuff
        if cmds.objExists(full_name):
            cmds.error("同じ名前のコントローラーがすでに存在するよ。名前を変えてね。")
        if useOffsetGrp and cmds.objExists(full_name + "_GRP"):
            cmds.error("同じ名前のオフセットグループがすでに存在するよ。")

    created_ctrls = {}
    created_grps = {}

    for jnt in target_joints:
        short_name = jnt.split("|")[-1]
        base_name = short_name.replace("_JNT", "").replace("_jnt", "")

        ctrl = _create_control(rgbColor, "正六面体（キューブ）", "X")
        ctrl_name = cmds.rename(ctrl, controlPref + base_name + controlSuff)

        cmds.select(ctrl_name)
        cmds.scale(controlSize, controlSize, controlSize, r=True)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)

        if useOffsetGrp:
            grp_name = cmds.group(ctrl_name, name=ctrl_name + "_GRP")
            temp_orient = cmds.orientConstraint(jnt, grp_name)
            cmds.delete(temp_orient)
            temp_point = cmds.pointConstraint(jnt, grp_name)
            cmds.delete(temp_point)
            created_grps[jnt] = grp_name
        else:
            temp_orient = cmds.orientConstraint(jnt, ctrl_name)
            cmds.delete(temp_orient)
            temp_point = cmds.pointConstraint(jnt, ctrl_name)
            cmds.delete(temp_point)
            cmds.select(ctrl_name)
            cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)

        cmds.parentConstraint(ctrl_name, jnt, mo=True)
        created_ctrls[jnt] = ctrl_name

    # 親子付け 1: 今回一緒に作った分同士 (今までの動き)
    for jnt in target_joints:
        parent_jnt = cmds.listRelatives(jnt, parent=True, fullPath=True)
        if parent_jnt and parent_jnt[0] in created_ctrls:
            parent_ctrl = created_ctrls[parent_jnt[0]]
            child_node = created_grps[jnt] if useOffsetGrp else created_ctrls[jnt]
            if cmds.objExists(parent_ctrl) and cmds.objExists(child_node):
                try:
                    cmds.parent(child_node, parent_ctrl)
                except Exception:
                    pass

    # 親子付け 2 (V6で追加): 親ジョイントのコントローラが既にシーンにある場合、
    # そっちの下に付ける。別々に作っても階層がつながるようにするため
    created_nodes = set(created_ctrls.values()) | set(created_grps.values())
    for jnt in target_joints:
        child_node = created_grps[jnt] if useOffsetGrp else created_ctrls[jnt]
        current_parent = cmds.listRelatives(child_node, parent=True, fullPath=True) or []
        if current_parent and current_parent[0] in created_nodes:
            continue
        if current_parent and current_parent[0].split("|")[-1] in [c.split("|")[-1] for c in created_ctrls.values()]:
            continue
        parent_jnt = cmds.listRelatives(jnt, parent=True, type="joint", fullPath=True)
        if not parent_jnt:
            continue
        if parent_jnt[0] in created_ctrls:
            continue
        parent_ctrl = _find_existing_fk_ctrl(parent_jnt[0], controlPref, controlSuff)
        if not parent_ctrl:
            continue
        if parent_ctrl.split("|")[-1] == child_node.split("|")[-1]:
            continue
        if cmds.objExists(parent_ctrl) and cmds.objExists(child_node):
            try:
                cmds.parent(child_node, parent_ctrl)
            except Exception:
                pass
    return created_ctrls


def makeCtrlAtJoint(*args):
    # V15で追加: 選んだ骨の場所にコントローラを作る (一般用)
    # 形状は「コントローラー作成」の選択を使う。
    # 位置合わせのあと、フリーズとヒストリ削除まで自動でやる
    cmds.undoInfo(openChunk=True, chunkName="makeCtrlAtJoint")
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("コントローラーを作りたい骨（ジョイント）を選んでね。")
        controlSize = _ui_get("controlSize", 1.0)
        controlPref = _ui_get("controlPrefix", "")
        controlSuff = _ui_get("controlName", "_CTRL")
        rgbColor = _ui_get("controlColorRGB", (0.3, 0.7, 1.0))

        for jnt in selection:
            base_name = jnt.split("|")[-1].replace("_JNT", "").replace("_jnt", "")
            if cmds.objExists(controlPref + base_name + controlSuff):
                cmds.error("同じ名前のコントローラーがすでに存在するよ。名前を変えてね。")

        created = []
        for jnt in selection:
            base_name = jnt.split("|")[-1].replace("_JNT", "").replace("_jnt", "")
            ctrl = _create_control(rgbColor)
            ctrl_name = cmds.rename(ctrl, controlPref + base_name + controlSuff)
            cmds.select(ctrl_name)
            cmds.scale(controlSize, controlSize, controlSize, r=True)
            cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
            temp_orient = cmds.orientConstraint(jnt, ctrl_name)
            cmds.delete(temp_orient)
            temp_point = cmds.pointConstraint(jnt, ctrl_name)
            cmds.delete(temp_point)
            cmds.select(ctrl_name)
            cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
            cmds.delete(ctrl_name, constructionHistory=True)
            created.append(ctrl_name)
        if created:
            cmds.select(created)
    finally:
        cmds.undoInfo(closeChunk=True)


def makeFKTR(*args):
    cmds.undoInfo(openChunk=True, chunkName="makeFKTR")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("コントロールを作りたい骨やジョイントを選んでね。")

        target_joints = []
        if len(selection) == 1:
            target_joints.append(selection[0])
            descendants = cmds.listRelatives(selection[0], allDescendents=True, type="joint", fullPath=True)
            if descendants:
                descendants.reverse()
                target_joints.extend(descendants)
        elif len(selection) == 2:
            start_jnt = selection[0]
            end_jnt = selection[1]
            current = end_jnt
            chain = [current]
            while current != start_jnt:
                parent = cmds.listRelatives(current, parent=True, type="joint", fullPath=True)
                if not parent:
                    break
                current = parent[0]
                chain.append(current)
            chain.reverse()
            if chain and chain[0] == start_jnt:
                target_joints = chain
            else:
                target_joints = selection
        else:
            target_joints = selection

        _build_fk_controls(target_joints)
    finally:
        cmds.undoInfo(closeChunk=True)


def makeFKTRSingle(*args):
    # V6で追加: 選んだジョイントだけにFKを1個作る (子へは広げない)
    cmds.undoInfo(openChunk=True, chunkName="makeFKTRSingle")
    try:
        selection = cmds.ls(sl=True, type="joint", long=True)
        if not selection:
            cmds.error("FKを1個だけ作りたいジョイントを1つ選んでね。")
        if len(selection) > 1:
            cmds.warning("複数選ばれているので、選んだジョイントそれぞれに1個ずつ作るね（子へは広げないよ）。")
        _build_fk_controls(list(selection))
    finally:
        cmds.undoInfo(closeChunk=True)


def makeIKTR(*args):
    cmds.undoInfo(openChunk=True, chunkName="makeIKTR")
    try:
        selection = cmds.ls(sl=True, long=True)
        if len(selection) != 2:
            cmds.error("IKを作るために、ジョイントを正確に2つ（根元と先端）選んでね。")
            
        start_joint = selection[0]
        end_joint = selection[1]
        base_end_joint = end_joint.split("|")[-1].replace("_JNT", "").replace("_jnt", "")
        
        controlSize = _ui_get("controlSize", 1.0)
        controlPref = _ui_get("controlPrefix", "")
        controlSuff = _ui_get("controlName", "_CTRL")
        rgbColor = _ui_get("controlColorRGB", (0.3, 0.7, 1.0))
        useOffsetGrp = _ui_get("useOffsetGrp", False)
        
        ctrl = _create_control(rgbColor)
        ctrl_name = cmds.rename(ctrl, controlPref + base_end_joint + controlSuff)
        
        cmds.select(ctrl_name)
        cmds.scale(controlSize, controlSize, controlSize, r=True)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)

        if useOffsetGrp:
            grp_name = cmds.group(ctrl_name, name=ctrl_name + "_GRP")
            temp_orient = cmds.orientConstraint(end_joint, grp_name)
            cmds.delete(temp_orient)
            temp_point = cmds.pointConstraint(end_joint, grp_name)
            cmds.delete(temp_point)
        else:
            temp_orient = cmds.orientConstraint(end_joint, ctrl_name)
            cmds.delete(temp_orient)
            temp_point = cmds.pointConstraint(end_joint, ctrl_name)
            cmds.delete(temp_point)
            cmds.select(ctrl_name)
            cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        
        ik_handle, ik_effector = cmds.ikHandle(
            startJoint=start_joint,
            endEffector=end_joint,
            sol="ikRPsolver"
        )
        short_start = start_joint.split("|")[-1]
        ik_handle_name = cmds.rename(ik_handle, short_start + "_ikHandle")
        cmds.parent(ik_handle_name, ctrl_name)
    finally:
        cmds.undoInfo(closeChunk=True)

def makeMeshFitCtrl(*args):
    cmds.undoInfo(openChunk=True, chunkName="makeMeshFitCtrl")
    try:
        sel = cmds.ls(sl=True, flatten=True, long=True)
        if not sel:
            cmds.error("コントローラーを合わせたいモデルや頂点を選んでね。")
            
        bbox = cmds.xform(sel, q=True, ws=True, boundingBox=True)
        if not bbox:
            cmds.error("選択範囲からサイズを計算できなかったよ。")
            
        center_x = (bbox[0] + bbox[3]) / 2.0
        center_y = (bbox[1] + bbox[4]) / 2.0
        center_z = (bbox[2] + bbox[5]) / 2.0
        
        size_x = max(bbox[3] - bbox[0], 0.1)
        size_y = max(bbox[4] - bbox[1], 0.1)
        size_z = max(bbox[5] - bbox[2], 0.1)

        controlSize = _ui_get("controlSize", 1.0)
        controlPref = _ui_get("controlPrefix", "")
        controlSuff = _ui_get("controlName", "_CTRL")
        rgbColor = _ui_get("controlColorRGB", (0.3, 0.7, 1.0))
        useOffsetGrp = _ui_get("useOffsetGrp", False)
        
        base_name = cmds.ls(sel[0], o=True)[0].split("|")[-1]
        if "." in base_name:
            base_name = base_name.split(".")[0]

        ctrl = _create_control(rgbColor)
        ctrl_name = cmds.rename(ctrl, controlPref + base_name + "_Fit" + controlSuff)
        
        cmds.select(ctrl_name)
        cmds.scale(size_x * controlSize, size_y * controlSize, size_z * controlSize, r=True)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        
        if useOffsetGrp:
            grp_name = cmds.group(ctrl_name, name=ctrl_name + "_GRP")
            cmds.xform(grp_name, ws=True, t=(center_x, center_y, center_z))
        else:
            cmds.xform(ctrl_name, ws=True, t=(center_x, center_y, center_z))
    finally:
        cmds.undoInfo(closeChunk=True)

def applyColorPreset(*args):
    preset_name = _ui_get("colorPreset", "青")
    color_dict = {
        "青": (0.2, 0.6, 1.0),
        "ピンク": (1.0, 0.5, 0.8),
        "赤": (1.0, 0.2, 0.2),
        "黄": (1.0, 0.9, 0.2),
        "緑": (0.2, 0.8, 0.4),
        "白": (1.0, 1.0, 1.0),
        "黒": (0.2, 0.2, 0.2)
    }
    if preset_name in color_dict:
        rgb = color_dict[preset_name]
        _ui_set("controlColorRGB", rgb)
        if _window is not None:
            try:
                _window._refresh_color_buttons()
            except Exception:
                pass

def applyColorToSelected(*args):
    cmds.undoInfo(openChunk=True, chunkName="applyColorToSelected")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("カラーを塗りたいオブジェクトをえらんでね。")
            
        rgbColor = _ui_get("applyColorRGB", (0.3, 0.7, 1.0))
        
        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
            if not shapes:
                if cmds.nodeType(obj) in ['nurbsCurve', 'mesh', 'joint']:
                    shapes = [obj]
                else:
                    continue
                
            for shape in shapes:
                cmds.setAttr(shape + ".overrideEnabled", 1)
                cmds.setAttr(shape + ".overrideRGBColors", 1)
                cmds.setAttr(shape + ".overrideColorRGB", rgbColor[0], rgbColor[1], rgbColor[2])
    finally:
        cmds.undoInfo(closeChunk=True)

def renameJoints(*args):
    cmds.undoInfo(openChunk=True, chunkName="renameJoints")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("名前を変えたいジョイントを選んでね。")
            
        selected_name = _ui_get("renamePreset", "root")
        controlPref = _ui_get("controlPrefix", "")
        prefix_side, suffix_side = _get_side_tag()
        
        if len(selection) == 1:
            new_name = controlPref + prefix_side + selected_name + suffix_side + "_JNT"
            cmds.rename(selection[0], new_name)
        else:
            for i, obj in enumerate(selection):
                new_name = controlPref + prefix_side + selected_name + "_" + str(i+1).zfill(2) + suffix_side + "_JNT"
                cmds.rename(obj, new_name)
    finally:
        cmds.undoInfo(closeChunk=True)

def renameFingerJoints(*args):
    cmds.undoInfo(openChunk=True, chunkName="renameFingerJoints")
    try:
        selection = cmds.ls(sl=True, long=True)
        if not selection:
            cmds.error("指の根元のジョイントを選んでね。")
            
        finger_name = _ui_get("fingerPreset", "th")
        controlPref = _ui_get("controlPrefix", "")
        prefix_side, suffix_side = _get_finger_side_tag()
        
        for sel in selection:
            chain = [sel]
            current = sel
            while True:
                children = cmds.listRelatives(current, children=True, type='joint', fullPath=True)
                if children and len(children) > 0:
                    current = children[0]
                    chain.append(current)
                else:
                    break
            
            rename_pairs = [(obj, i) for i, obj in enumerate(chain)]
            rename_pairs.reverse()
            
            for obj, i in rename_pairs:
                new_name = controlPref + prefix_side + finger_name + "_" + str(i+1).zfill(2) + suffix_side + "_JNT"
                cmds.rename(obj, new_name)
    finally:
        cmds.undoInfo(closeChunk=True)
# ---------------------------------------------------------------------------
# UI (PySide / Qt) — シンメトリー v22 と同じ丸いピルボタン様式
# ---------------------------------------------------------------------------

WINDOW_NAME = "majimeruBenriRigV24Window"
WINDOW_TITLE = "誰でもリグ作れるよツール V24 - majimeru"

_GUIDE_PRESETS = [
    "🦴 背骨〜頭のガイドセット (6個)",
    "💪 左腕のガイドセット (4個)",
    "🦵 左脚のガイドセット (5個)",
    "🖐️ 左手5本指のガイドセット (20個)",
]
_RENAME_PRESETS = ["root", "pelvis", "clavicle", "uarm", "elbow", "wrist",
                   "hip", "knee", "ankle", "ball", "toe", "spine",
                   "spine01", "spine02", "chest", "neck", "head", "twist"]
_SIDE_PRESETS = ["なし", "_L", "_R", "L_", "R_"]
_FINGER_PRESETS = ["th", "in", "mi", "ri", "p"]
_SHAPE_PRESETS = ["正六面体（キューブ）", "球（スフィア）", "円錐（コーン）",
                  "円（サークル）", "ダイヤ（八面体）"]
_AXIS_PRESETS = ["X軸（骨の標準）", "Y軸", "Z軸"]
_COLOR_PRESETS = ["青", "ピンク", "赤", "黄", "緑", "白", "黒"]


def get_maya_window():
    if omui is None or QtWidgets is None:
        return None
    try:
        from shiboken6 import wrapInstance
    except ImportError:
        try:
            from shiboken2 import wrapInstance
        except ImportError:
            return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


def _pill_style(bg, fg, hover, pressed, radius):
    return (
        "QPushButton {"
        " background-color: " + bg + ";"
        " color: " + fg + ";"
        " border: none;"
        " border-radius: " + str(radius) + "px;"
        " font-weight: bold;"
        " font-size: 12px;"
        " padding: 4px 10px;"
        "}"
        "QPushButton:hover { background-color: " + hover + "; }"
        "QPushButton:pressed { background-color: " + pressed + "; }")


# (背景, 文字, ホバー, 押下) のやさしい色セット
_C_YELLOW = ("#e6b93d", "#2b2b2b", "#f0c44e", "#cfa32f")
_C_GREEN = ("#4da653", "#ffffff", "#5ab361", "#3f9142")
_C_BLUE = ("#6b9bd8", "#ffffff", "#7fb0e8", "#4a7fc1")
_C_SKY = ("#6fc3d9", "#1f2f38", "#85d0e4", "#52a8bf")
_C_PURPLE = ("#b07cc6", "#ffffff", "#c08fd4", "#9663ab")
_C_PINK = ("#e08bb0", "#ffffff", "#eba3c0", "#c96f96")
_C_ORANGE = ("#e8a04c", "#2b2118", "#f2b264", "#cf8a35")
_C_RED = ("#e08a8a", "#2b1d1d", "#eda0a0", "#c96f6f")
_C_GRAY = ("#9a9a9a", "#1f1f1f", "#ababab", "#7f7f7f")
_C_TEAL = ("#5db8a6", "#ffffff", "#71c9b8", "#439e8b")


# ボタンを押したあと、下のメッセージ欄に出す「できた」文言
_DONE_MESSAGES = {
    "spawnPresetGuides": "ガイド球を出したよ。球を動かして関節の場所に合わせてね",
    "spawnGuideSphere": "ガイド球を1個追加したよ",
    "connectSelectedGuidesWithLines": "ガイド球同士を線でつないだよ",
    "createChainFromGuides": "骨を作ったよ！",
    "mirrorJointsCmd": "骨を反対側にミラーコピーしたよ",
    "renameJoints": "ジョイントの名前を付け直したよ",
    "renameFingerJoints": "指の名前を付け直したよ",
    "autoOrientJoints": "骨の向きを自動で直したよ",
    "zeroJointOrientAndRotate": "骨の角度を全部0にしたよ",
    "toggleJointLocalAxis": "ローカル軸の表示を切り替えたよ",
    "makeCtrlAtJoint": "骨の場所にコントローラを作ったよ",
    "makeMeshFitCtrl": "形に合わせたコントローラを作ったよ",
    "mirrorControls": "コントローラーを反対側にミラーコピーしたよ",
    "makeFKTR": "FKコントローラを作ったよ",
    "makeFKTRSingle": "FKコントローラを1個作ったよ",
    "makeIKTR": "IKコントローラを作ったよ",
    "quickBindSkin": "モデルを骨にくっつけたよ（スキニング完了）",
    "mirrorSkinWeightsCmd": "ウェイトを反対側にコピーしたよ",
    "applyColorToSelected": "色をつけたよ",
}


if MayaQWidgetDockableMixin is not None and QtWidgets is not None:
    class _BenriRigBase(MayaQWidgetDockableMixin, QtWidgets.QDialog):
        """ドッキング対応の土台 (workspaceControl に入る)。"""
        pass
elif QtWidgets is not None:
    class _BenriRigBase(QtWidgets.QDialog):
        pass
else:
    class _BenriRigBase(object):
        pass


class BenriRigWindow(_BenriRigBase):
    def __init__(self, parent=None):
        super(BenriRigWindow, self).__init__(parent)
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        if MayaQWidgetDockableMixin is None:
            # ドッキング土台が無い環境だけ、今まで通り最前面に固定する
            self.setWindowFlags(
                self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(720)
        self.resize(780, 660)
        self._build_ui()

    # -- 部品づくり ----------------------------------------------------
    def _focus_maya(self):
        # ボタン実行後、キーボードを Maya 本体へ戻す (Ctrl+Z 等が効くように)
        try:
            self.clearFocus()
        except Exception:
            pass
        try:
            if hasattr(cmds, "setFocusToMainWindow"):
                cmds.setFocusToMainWindow()
                return
        except Exception:
            pass
        parent = get_maya_window()
        if parent is not None:
            try:
                parent.activateWindow()
            except Exception:
                pass
            try:
                parent.setFocus()
            except Exception:
                pass

    def _run_command(self, command):
        # 前回の処理でチャンクが開きっぱなしだった場合の救済
        # (開いたままやと Maya の Undo キュー全体が壊れるため)
        try:
            cmds.undoInfo(closeChunk=True)
        except Exception:
            pass
        error_text = None
        try:
            command()
        except Exception as e:
            error_text = str(e)
        finally:
            # 処理側で閉じ忘れたチャンクがあってもここで必ず閉じる
            try:
                cmds.undoInfo(closeChunk=True)
            except Exception:
                pass
            try:
                cmds.undoInfo(state=True)
            except Exception:
                pass
            self._focus_maya()
        if error_text:
            print("エラー: " + error_text)
            self._set_status("⚠ " + error_text.strip(), True)
        else:
            done = _DONE_MESSAGES.get(getattr(command, "__name__", ""),
                                      "できたよ ✓")
            self._set_status(done, False)

    def _set_status(self, text, is_error=False):
        lab = getattr(self, "status_label", None)
        if lab is None:
            return
        lab.setText(text)
        bg = "#5a2e2e" if is_error else "#2e4a2e"
        lab.setStyleSheet(
            "background-color: " + bg + "; color: #ffffff;"
            " border-radius: 10px; padding: 6px 10px; font-size: 12px;")

    def _open_manual(self):
        """内蔵の図解マニュアル PDF を一時フォルダに書き出して開く。"""
        import base64
        import os
        import tempfile
        import zlib
        try:
            data = zlib.decompress(base64.b64decode(_MANUAL_PDF_ZLIB_B64))
            try:
                out_dir = cmds.internalVar(userTmpDir=True)
            except Exception:
                out_dir = None
            if not out_dir:
                out_dir = tempfile.gettempdir()
            path = os.path.join(out_dir, "benri_rig_manual.pdf")
            with open(path, "wb") as fh:
                fh.write(data)
        except Exception:
            self._set_status(
                "マニュアルを取り出せなかったよ… 使い方ダイアログを出すね",
                True)
            self._show_help()
            return
        if QtGui is not None and QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(path)):
            self._set_status("マニュアルを開いたよ 📖")
            return
        self._set_status(
            "マニュアルが開けなかったよ… 使い方ダイアログを出すね", True)
        self._show_help()

    def _show_help(self):
        text = (
            "【使い方】この順番でやればできるよ\n\n"
            "1. ガイドを置く（「Step 1」）\n"
            "・作りたい部位を選んで、ボタンを押す\n"
            "・目印の球が出てくる\n"
            "・球を動かして、関節の場所に合わせる\n\n"
            "2. 骨を作る（「Step 2」）\n"
            "・球を選んで「骨を作る」ボタンを押す\n"
            "・反対側は「ミラーコピー」で同じように作れる\n"
            "・名前は自動で付くよ（直したいときだけ、下のリネームを使う）\n\n"
            "3. コントローラーを作る（「コントローラー作成」「FK」）\n"
            "・骨を選んで、ボタンを押すだけ\n"
            "・動かすためのコントローラーが、自動で作られる\n"
            "・色や大きさは、先に選んでおける\n\n"
            "4. モデルにくっつける（「モデルを骨にくっつける」）\n"
            "・骨とモデルを選んで、ボタンを押す\n"
            "・これで、骨を動かすとモデルもついてくる\n\n"
            "※ ウィンドウの下の欄が緑なら成功。\n"
            "　赤くなったら、できなかった理由が書いてあるから読んでみてね。\n\n"
            "※ もっと詳しくは「マニュアルを開く」ボタンの PDF を見てね。\n"
            "※ ウィンドウは、上のバーをドラッグすると Maya の画面の"
            "横にくっつけられるよ（ドッキング）。")
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("使い方")
        box.setText(text)
        try:
            box.exec()
        except AttributeError:
            box.exec_()

    def _btn(self, label, command, colors, height=27):
        btn = QtWidgets.QPushButton(label)
        btn.setFixedHeight(height)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setStyleSheet(_pill_style(
            colors[0], colors[1], colors[2], colors[3], height // 2))
        if command is not None:
            btn.clicked.connect(
                lambda _=False, c=command: self._run_command(c))
        return btn

    def _sel_xform_sig(self, sel):
        sig = []
        for n in sel:
            try:
                tr = cmds.xform(n, q=True, ws=True, t=True) or []
                ro = cmds.xform(n, q=True, ws=True, ro=True) or []
                sig.append((n,
                            tuple(round(float(v), 4) for v in tr),
                            tuple(round(float(v), 4) for v in ro)))
            except Exception:
                sig.append((n, None, None))
        return sig

    def _smart_step(self, is_redo):
        # 1ステップだけ undo/redo して、何が変わったか文字列で返す
        nodes_before = set(cmds.ls(long=True) or [])
        sel_before = cmds.ls(sl=True, long=True) or []
        sig_before = self._sel_xform_sig(sel_before)
        if is_redo:
            cmds.redo()
        else:
            cmds.undo()
        nodes_after = set(cmds.ls(long=True) or [])
        sel_after = cmds.ls(sl=True, long=True) or []
        sig_after = self._sel_xform_sig(sel_after)
        if nodes_after != nodes_before:
            removed = sorted(nodes_before - nodes_after)
            added = sorted(nodes_after - nodes_before)
            return ("nodes", removed, added)
        if sel_after != sel_before:
            return ("selection", None, None)
        if sig_after != sig_before:
            return ("transform", None, None)
        return ("none", None, None)

    def _smart_undo(self):
        # 選択だけのステップと「何も変わらない」ステップ (最大3連続) を
        # 飛ばして、実のある操作を1回で取り消す。各ステップを print する
        print("[smartUndo] 開始")
        phantoms = 0
        did_something = False
        for i in range(300):
            try:
                if cmds.undoInfo(q=True, undoQueueEmpty=True):
                    print("[smartUndo] キューが空です")
                    break
            except Exception:
                pass
            try:
                kind, removed, added = self._smart_step(False)
            except Exception as e:
                print("[smartUndo] undo実行エラー:", e)
                break
            did_something = True
            if kind == "nodes":
                print("[smartUndo] step%d: ノード変化 (消えた %d / 増えた %d) -> ここまで"
                      % (i + 1, len(removed or []), len(added or [])))
                for n in (removed or [])[:5]:
                    print("    消えた:", n)
                for n in (added or [])[:5]:
                    print("    増えた:", n)
                break
            if kind == "transform":
                print("[smartUndo] step%d: 移動/回転が戻った -> ここまで" % (i + 1))
                break
            if kind == "selection":
                print("[smartUndo] step%d: 選択だけ変化 -> 飛ばす" % (i + 1))
                continue
            phantoms += 1
            print("[smartUndo] step%d: 変化なし (%d回目) -> 飛ばす" % (i + 1, phantoms))
            if phantoms >= 100:
                print("[smartUndo] 変化なしが100回続いたので停止")
                break
        if not did_something:
            print("[smartUndo] 何も取り消せませんでした")
        print("[smartUndo] 終了")

    def _smart_redo(self):
        print("[smartRedo] 開始")
        phantoms = 0
        for i in range(300):
            try:
                if cmds.undoInfo(q=True, redoQueueEmpty=True):
                    print("[smartRedo] やり直しキューが空です")
                    break
            except Exception:
                pass
            try:
                kind, removed, added = self._smart_step(True)
            except Exception as e:
                print("[smartRedo] redo実行エラー:", e)
                break
            if kind == "nodes":
                print("[smartRedo] step%d: ノード変化 (消えた %d / 増えた %d) -> ここまで"
                      % (i + 1, len(removed or []), len(added or [])))
                break
            if kind == "transform":
                print("[smartRedo] step%d: 移動/回転が進んだ -> ここまで" % (i + 1))
                break
            if kind == "selection":
                print("[smartRedo] step%d: 選択だけ変化 -> 飛ばす" % (i + 1))
                continue
            phantoms += 1
            print("[smartRedo] step%d: 変化なし (%d回目) -> 飛ばす" % (i + 1, phantoms))
            if phantoms >= 100:
                print("[smartRedo] 変化なしが100回続いたので停止")
                break
        print("[smartRedo] 終了")

    def closeEvent(self, event):
        # ウィンドウを閉じたらホットキーを Maya 標準に戻す
        try:
            remove_smart_hotkeys()
        except Exception:
            pass
        super(BenriRigWindow, self).closeEvent(event)

    def keyPressEvent(self, event):
        # ダイアログ側にフォーカスがあっても、文字入力中でなければ
        # Ctrl+Z / Z を Maya の取り消し、Ctrl+Y / Shift+Z をやり直しへ回す
        try:
            focus_w = QtWidgets.QApplication.focusWidget()
            editing = (QtWidgets.QLineEdit, QtWidgets.QAbstractSpinBox,
                       QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)
            if not isinstance(focus_w, editing):
                mods = event.modifiers()
                ctrl = bool(mods & QtCore.Qt.ControlModifier) or bool(mods & QtCore.Qt.MetaModifier)
                shift = bool(mods & QtCore.Qt.ShiftModifier)
                key = event.key()
                if key == QtCore.Qt.Key_Z and (ctrl or not shift):
                    if ctrl and shift:
                        self._smart_redo()
                    elif ctrl:
                        self._smart_undo()
                    elif shift:
                        self._smart_redo()
                    else:
                        self._smart_undo()
                    event.accept()
                    return
                if key == QtCore.Qt.Key_Z and shift and not ctrl:
                    self._smart_redo()
                    event.accept()
                    return
                if key == QtCore.Qt.Key_Y and ctrl:
                    self._smart_redo()
                    event.accept()
                    return
        except Exception:
            pass
        super(BenriRigWindow, self).keyPressEvent(event)

    def _combo(self, items, key):
        box = QtWidgets.QComboBox()
        box.addItems(items)
        box.setFixedHeight(24)
        current = _ui_get(key)
        if current in items:
            box.setCurrentIndex(items.index(current))
        box.currentTextChanged.connect(
            lambda text, k=key: _ui_set(k, text))
        return box

    def _edit(self, key):
        field = QtWidgets.QLineEdit()
        field.setFixedHeight(24)
        field.setText(_ui_get(key, ""))
        field.textChanged.connect(lambda text, k=key: _ui_set(k, text))
        return field

    def _group(self, title):
        grp = QtWidgets.QGroupBox(title)
        lay = QtWidgets.QVBoxLayout(grp)
        lay.setSpacing(5)
        lay.setContentsMargins(8, 6, 8, 8)
        return grp, lay

    def _white_line(self, layout):
        line = QtWidgets.QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #ffffff; border: none;")
        layout.addWidget(line)

    def _note(self, text):
        lab = QtWidgets.QLabel(text)
        lab.setWordWrap(True)
        lab.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        return lab

    def _color_button(self, key):
        btn = QtWidgets.QPushButton()
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setFixedSize(44, 24)
        btn.clicked.connect(lambda _=False, k=key: self._pick_color(k))
        return btn

    def _refresh_color_buttons(self):
        for key, btn in (("controlColorRGB", self.create_color_btn),
                         ("applyColorRGB", self.apply_color_btn)):
            rgb = _ui_get(key, (0.3, 0.7, 1.0))
            r, g, b = [int(max(0.0, min(1.0, c)) * 255) for c in rgb]
            btn.setStyleSheet(
                "QPushButton {"
                " background-color: rgb(" + str(r) + "," + str(g) + "," + str(b) + ");"
                " border: 1px solid #888888;"
                " border-radius: 12px;"
                "}"
                "QPushButton:hover { border: 2px solid #ffffff; }")

    def _pick_color(self, key):
        rgb = _ui_get(key, (0.3, 0.7, 1.0))
        init = QtGui.QColor(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        color = QtWidgets.QColorDialog.getColor(init, self, "色を選ぶ")
        if color.isValid():
            _ui_set(key, (color.red() / 255.0,
                          color.green() / 255.0,
                          color.blue() / 255.0))
            self._refresh_color_buttons()

    def _on_color_preset(self, text):
        _ui_set("colorPreset", text)
        applyColorPreset()

    # -- 本体 ----------------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #666666;"
            " border-radius: 8px; margin-top: 10px; padding-top: 6px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px;"
            " padding: 0 4px; }"
            "QComboBox, QLineEdit, QDoubleSpinBox {"
            " background-color: #3a3a3a; color: #ffffff;"
            " border: 1px solid #666666; border-radius: 10px;"
            " padding: 2px 8px; }"
            "QCheckBox { font-size: 12px; }")
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(8, 8, 8, 8)

        title_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("✨ 誰でもリグ作れるよツール V24 ✨")
        title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #e6b93d;")
        title_row.addWidget(title)
        title_row.addStretch(1)
        help_btn = self._btn("使い方を見る", None, _C_SKY, 26)
        help_btn.clicked.connect(self._show_help)
        title_row.addWidget(help_btn)
        manual_btn = self._btn("マニュアルを開く", None, _C_GREEN, 26)
        manual_btn.clicked.connect(self._open_manual)
        title_row.addWidget(manual_btn)
        root.addLayout(title_row)
        root.addWidget(self._note(
            "リギングが苦手なあなたへ。この順番どおりにやれば絶対できるよ！"
            "それじゃあ骨、作ろうか！"))
        root.addWidget(self._note(
            "流れ： ①ガイドを置く → ②骨を作る → ③コントローラーを作る "
            "→ ④モデルにくっつける"))

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        root.addWidget(scroll)

        self.status_label = QtWidgets.QLabel(
            "ボタンを押すと、ここに結果が出るよ")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "background-color: #2e2e2e; color: #ffffff;"
            " border-radius: 10px; padding: 6px 10px; font-size: 12px;")
        root.addWidget(self.status_label)
        content = QtWidgets.QWidget()
        scroll.setWidget(content)
        cols = QtWidgets.QHBoxLayout(content)
        cols.setSpacing(8)
        cols.setContentsMargins(2, 2, 2, 2)
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(6)
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(6)
        cols.addLayout(left)
        cols.addLayout(right)

        # ===== 左カラム =====
        grp, lay = self._group("【Step 1】部位のガイド球を一括配置")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("つくりたい部位"))
        row.addWidget(self._combo(_GUIDE_PRESETS, "guidePreset"))
        lay.addLayout(row)
        lay.addWidget(self._btn("① 選んだ部位のガイド球を画面に出す",
                                spawnPresetGuides, _C_YELLOW, 30))
        lay.addWidget(self._btn("好きな場所にガイド球を1個追加する",
                                spawnGuideSphere, _C_SKY))
        lay.addWidget(self._btn("追加した球同士を【根元→先端】の順に選んで線を引く",
                                connectSelectedGuidesWithLines, _C_TEAL))
        left.addWidget(grp)

        self._white_line(left)
        grp, lay = self._group("【Step 2】位置を合わせて骨を一撃作成")
        lay.addWidget(self._note(
            "💡 自分で置いた球を繋ぐときは【根元（親）→先端（子）】の順に選んでね！"))
        lay.addWidget(self._btn("② ガイド球（またはグループ）を選んで骨を作る",
                                createChainFromGuides, _C_GREEN, 30))
        lay.addWidget(self._btn("③ 反対側へワンクリックミラーコピー",
                                mirrorJointsCmd, _C_BLUE))
        left.addWidget(grp)

        self._white_line(left)
        grp, lay = self._group("ジョイントのリネーム（手動用）")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("ジョイント名"))
        row.addWidget(self._combo(_RENAME_PRESETS, "renamePreset"))
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("左右（サイド）"))
        row.addWidget(self._combo(_SIDE_PRESETS, "sidePreset"))
        lay.addLayout(row)
        lay.addWidget(self._btn("選択したジョイント名を上で選んでこのボタン押して",
                                renameJoints, _C_PURPLE))
        left.addWidget(grp)

        self._white_line(left)
        grp, lay = self._group("指のリネーム")
        lay.addWidget(self._note(
            "th=親指 / in=人差し指 / mi=中指 / ri=薬指 / p=小指"))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("指の名前"))
        row.addWidget(self._combo(_FINGER_PRESETS, "fingerPreset"))
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("指の左右"))
        row.addWidget(self._combo(_SIDE_PRESETS, "fingerSidePreset"))
        lay.addLayout(row)
        lay.addWidget(self._btn("根元だけ選択して指を一括リネーム",
                                renameFingerJoints, _C_PINK))
        left.addWidget(grp)

        self._white_line(left)
        grp, lay = self._group("ジョイントの軸（向き）の自動整列")
        lay.addWidget(self._btn("選択した根元から骨の向き（ローカル軸）を自動で正す",
                                autoOrientJoints, _C_ORANGE))
        lay.addWidget(self._btn("選択した骨の角度数値（Rotate / Orient）を全て0にする",
                                zeroJointOrientAndRotate, _C_ORANGE))
        lay.addWidget(self._btn("ローカル軸（XYZ）の表示 / 非表示を切り替え",
                                toggleJointLocalAxis, _C_GRAY))
        left.addWidget(grp)
        left.addStretch(1)

        # ===== 右カラム =====
        grp, lay = self._group("コントローラー作成")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("コントロール形状"))
        row.addWidget(self._combo(_SHAPE_PRESETS, "controlShape"))
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("形状の向き（軸）"))
        row.addWidget(self._combo(_AXIS_PRESETS, "controlAxis"))
        lay.addLayout(row)
        lay.addWidget(self._btn("選んだ骨の場所にコントローラを作る",
                                makeCtrlAtJoint, _C_YELLOW, 32))
        lay.addWidget(self._btn("選択した形状（頂点など）に合わせてコントローラを作る",
                                makeMeshFitCtrl, _C_GREEN))
        lay.addWidget(self._btn("選択したコントローラーを反対側にミラーコピー",
                                mirrorControls, _C_SKY))
        lay.addWidget(self._note(
            "💡 「骨の場所に作る」はフリーズとヒストリ削除まで自動でやるよ。"
            "ミラーすると名前の L/R も骨に合わせて入れ替わるよ。"))
        right.addWidget(grp)

        self._white_line(right)
        grp, lay = self._group("FKコントロール作成（コントローラーも自動で作るよ！）")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("サイズ"))
        self.size_spin = QtWidgets.QDoubleSpinBox()
        self.size_spin.setRange(0.1, 50.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setValue(float(_ui_get("controlSize", 1.0)))
        self.size_spin.setFixedHeight(24)
        self.size_spin.valueChanged.connect(
            lambda v: _ui_set("controlSize", float(v)))
        row.addWidget(self.size_spin)
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("作成時カラー"))
        self.create_color_btn = self._color_button("controlColorRGB")
        row.addWidget(self.create_color_btn)
        preset_box = QtWidgets.QComboBox()
        preset_box.addItems(_COLOR_PRESETS)
        preset_box.setFixedHeight(24)
        preset_box.currentTextChanged.connect(self._on_color_preset)
        row.addWidget(preset_box)
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("コントロール接頭辞"))
        row.addWidget(self._edit("controlPrefix"))
        lay.addLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("コントロール接尾辞"))
        row.addWidget(self._edit("controlName"))
        lay.addLayout(row)
        self.offset_check = QtWidgets.QCheckBox(
            "オフセット階層：オフセットグループ（_GRP）を挟む")
        self.offset_check.setChecked(bool(_ui_get("useOffsetGrp", False)))
        self.offset_check.toggled.connect(
            lambda v: _ui_set("useOffsetGrp", bool(v)))
        lay.addWidget(self.offset_check)
        lay.addWidget(self._note(
            "💡 オフセット階層は、指コントローラのときに特によく使う（指ではON推奨）"))
        lay.addWidget(self._btn("FKコントローラを作る",
                                makeFKTR, _C_YELLOW, 32))
        lay.addWidget(self._btn("FKを1個だけ作る（選んだジョイントのみ）",
                                makeFKTRSingle, _C_TEAL, 30))
        lay.addWidget(self._note(
            "💡 1個だけの方は子ジョイントへ広げないよ。どっちで作っても、"
            "親ジョイントのコントローラが既にあれば、その下に付けます。"))
        right.addWidget(grp)

        self._white_line(right)
        grp, lay = self._group("IKツール（腕や足用）")
        lay.addWidget(self._btn("腕用のIKコントローラーを作る",
                                makeIKTR, _C_BLUE))
        right.addWidget(grp)

        self._white_line(right)
        grp, lay = self._group("モデルを骨にくっつける（スキニング）")
        lay.addWidget(self._btn("選択した「骨」と「モデル」を一発バインド（スキニング）",
                                quickBindSkin, _C_RED))
        lay.addWidget(self._btn("選択モデルのスキンウェイトを左から右へミラー",
                                mirrorSkinWeightsCmd, _C_PINK))
        right.addWidget(grp)

        self._white_line(right)
        grp, lay = self._group("カラー変更・適用")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("適用カラー"))
        self.apply_color_btn = self._color_button("applyColorRGB")
        row.addWidget(self.apply_color_btn)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(self._btn("選択したオブジェクトにカラーを適用",
                                applyColorToSelected, _C_GRAY))
        right.addWidget(grp)
        right.addStretch(1)

        self._refresh_color_buttons()


# ==== スマートUndo/Redo のホットキー割り当て (V11〜V12) ====
# ウィンドウを開いている間だけ、Z / Ctrl+Z 等をスマート版に差し替える

def majimeru_smart_undo():
    if _window is not None:
        _window._smart_undo()
    else:
        cmds.undo()


def majimeru_smart_redo():
    if _window is not None:
        _window._smart_redo()
    else:
        cmds.redo()


_SMART_HOTKEY_STATE = {"installed": False, "previous_set": None}
_HOTKEY_SET_NAME = "MajimeruKeys"

_UNDO_RTC = "majimeruSmartUndoRTC"
_REDO_RTC = "majimeruSmartRedoRTC"
_UNDO_NC = "majimeruSmartUndoNC"
_REDO_NC = "majimeruSmartRedoNC"

_UNDO_FALLBACK = ("try:\n    majimeru_smart_undo()\nexcept NameError:\n"
                  "    import maya.cmds as _mc\n    _mc.undo()")
_REDO_FALLBACK = ("try:\n    majimeru_smart_redo()\nexcept NameError:\n"
                  "    import maya.cmds as _mc\n    _mc.redo()")

# (key, modifiers, "undo"/"redo", Maya標準の戻し先)
_HOTKEY_SPECS = [
    ("z", {}, "undo", "Undo"),
    ("z", {"shiftModifier": True}, "redo", "Redo"),
    ("z", {"ctrlModifier": True}, "undo", "Undo"),
    ("z", {"ctrlModifier": True, "shiftModifier": True}, "redo", "Redo"),
    ("z", {"commandModifier": True}, "undo", "Undo"),
    ("z", {"commandModifier": True, "shiftModifier": True}, "redo", "Redo"),
]


def _ensure_rtc(name, annotation, command_str):
    try:
        cmds.runTimeCommand(name, edit=True, annotation=annotation,
                            commandLanguage="python", command=command_str)
        return
    except Exception:
        pass
    try:
        cmds.runTimeCommand(name, annotation=annotation,
                            commandLanguage="python", command=command_str)
    except Exception:
        pass


def _ensure_nc(name, annotation, rtc_name):
    try:
        cmds.nameCommand(name, edit=True, annotation=annotation, command=rtc_name)
        return
    except Exception:
        pass
    try:
        cmds.nameCommand(name, annotation=annotation, command=rtc_name)
    except Exception:
        pass


def install_smart_hotkeys():
    # Maya_Default セットは cmds.hotkey の編集が反映されないため、
    # コピーの専用セットに切り替えてから割り当てる
    try:
        cur = cmds.hotkeySet(q=True, current=True)
    except Exception:
        cur = None
    if cur and cur != _HOTKEY_SET_NAME:
        _SMART_HOTKEY_STATE["previous_set"] = cur
    if not _SMART_HOTKEY_STATE.get("previous_set"):
        _SMART_HOTKEY_STATE["previous_set"] = "Maya_Default"
    try:
        sets = cmds.hotkeySet(q=True, hotkeySetArray=True) or []
    except Exception:
        sets = []
    try:
        if _HOTKEY_SET_NAME in sets:
            cmds.hotkeySet(_HOTKEY_SET_NAME, edit=True, current=True)
        else:
            cmds.hotkeySet(_HOTKEY_SET_NAME, current=True)
    except Exception:
        pass
    _ensure_rtc(_UNDO_RTC, "Smart Undo (skip selection-only steps)", _UNDO_FALLBACK)
    _ensure_rtc(_REDO_RTC, "Smart Redo (skip selection-only steps)", _REDO_FALLBACK)
    _ensure_nc(_UNDO_NC, "Smart Undo", _UNDO_RTC)
    _ensure_nc(_REDO_NC, "Smart Redo", _REDO_RTC)
    for key, mods, kind, _default in _HOTKEY_SPECS:
        nc = _UNDO_NC if kind == "undo" else _REDO_NC
        try:
            cmds.hotkey(keyShortcut=key, name=nc, **mods)
        except Exception:
            pass
    _SMART_HOTKEY_STATE["installed"] = True


def remove_smart_hotkeys():
    if not _SMART_HOTKEY_STATE.get("installed"):
        return
    prev = _SMART_HOTKEY_STATE.get("previous_set") or "Maya_Default"
    try:
        cmds.hotkeySet(prev, edit=True, current=True)
    except Exception:
        pass
    _SMART_HOTKEY_STATE["installed"] = False


def show_ui():
    global _window
    if QtWidgets is None:
        cmds.warning("PySide が見つからないため、ウィンドウを開けませんでした。")
        return None
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
    # 前回のドッキング枠 (workspaceControl) が残っていたら消す
    try:
        ctrl_name = WINDOW_NAME + "WorkspaceControl"
        if cmds.workspaceControl(ctrl_name, q=True, exists=True):
            cmds.deleteUI(ctrl_name, control=True)
    except Exception:
        pass
    _window = BenriRigWindow(parent)
    if MayaQWidgetDockableMixin is not None:
        _window.show(dockable=True)
    else:
        _window.show()
    install_smart_hotkeys()
    _window.raise_()
    _window.activateWindow()
    return _window


def createFKControls():
    # V4 までの入口名との互換用 (中身は V24 の Qt ウィンドウ)
    return show_ui()


try:
    show_ui()
except Exception:
    traceback.print_exc()

# ==== 内蔵マニュアル (benri_rig_manual.pdf を zlib 圧縮して Base64) ====
_MANUAL_PDF_ZLIB_B64 = (
    "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"
)

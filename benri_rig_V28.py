# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : benri_rig_V28  v28
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Maya Python tool
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================

# -*- coding: utf-8 -*-
"""
誰でもリグ作れるよツール V28 - majimeru
benri_rig V28 (V27 が土台)

[V28 変更点] (足箱の大きさを参考画像どおりに修正)
  足コントローラの箱が大きすぎてボールコントローラとかぶるとの指摘。
  ユーザーの参考画像に合わせ、赤い箱は「かかと→ボールまで」、
  青い箱は「ボール→つま先まで」と前後に並ぶ比率に変更
  (重なりはボールの周りの少しだけ)。ピボットや配線は変更なし。

[V27 変更点] (マニュアルと使い方ボタンを削除して軽量化)
  ユーザー判断で「マニュアルを開く」と「使い方を見る」を両方削除。
  内蔵 PDF (zlib+Base64) も丸ごと外したので、ファイルは約390KB から
  約98KB に軽くなった。マニュアル PDF 自体は別ファイルとして残る。

[V26 変更点] (取り消しの高速化)
  スマートアンドゥが重い (カーソルが回り続ける) との指摘。原因は、
  飛ばし処理の間もステップごとに画面を再描画していたことと、
  変化検出に全ノード一覧 (cmds.ls) を毎ステップ作っていたこと。
  対策: (1) 処理中は cmds.refresh(suspend=True) で再描画を止める
  (終わったら finally で必ず戻す)。(2) ノード一覧は DAG オブジェクト
  だけに絞る。挙動 (選択だけ/変化なしステップを飛ばす) は従来どおり。

[V25 変更点] (IK を腕用/足用に分割、足は箱まで自動)
  IK を「腕用」と「足用」の 2 ボタンに分けた (腕にはボールが無いので
  別々が分かりやすい、というユーザー判断)。足用は根元＋足首を選んで
  押すだけで、ユーザーの手作業リグを再現する: 足コントローラは
  ピボットが足首のまま、形だけ足全体を囲む大きい箱に変形 (サイズは
  足首→ボールの距離から自動。底は地面すれすれ)。ボールコントローラは
  足コントローラの子で、ピボットはボール、形はつま先の小さい箱。
  ボールへ orient + point コンストレイン (両方メインテンオフセット ON)
  を自動で付ける。腕用は従来どおり。

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
    exec(open(r"benri_rig_V28.py", encoding="utf-8").read())
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


# ---------------------------------------------------------------------------
# 足IK用ヘルパー (V25)
# ---------------------------------------------------------------------------

# _create_control のキューブと同じ並びの単位キューブ頂点 (形の作り替え用)
_CUBE_PTS = [
    (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
    (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5),
    (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
    (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, -0.5),
    (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
]


def _snap_ctrl_to_joint(ctrl, joint):
    """コントローラをジョイントの位置と向きに合わせる。

    フリーズ (makeIdentity) はしないので、コントローラの回転中心
    (ピボット) はジョイントの位置に残る。
    """
    tmp = cmds.orientConstraint(joint, ctrl)
    cmds.delete(tmp)
    tmp = cmds.pointConstraint(joint, ctrl)
    cmds.delete(tmp)


def _reshape_ctrl_box(ctrl, center, right, up, fwd, size):
    """キューブ型コントローラの「形だけ」をワールド空間の箱に作り替える。

    コントローラの移動・回転には一切触らない (ピボットは不変)。
    center / right / up / fwd / size はワールド空間で指定する。
    size は (幅, 高さ, 長さ)。コントローラのワールド行列は
    回転＋移動のみ (スケールなし) である前提。
    """
    m = cmds.xform(ctrl, q=True, ws=True, matrix=True)
    ax = (m[0], m[1], m[2])
    ay = (m[4], m[5], m[6])
    az = (m[8], m[9], m[10])
    org = (m[12], m[13], m[14])
    for i, (ux, uy, uz) in enumerate(_CUBE_PTS):
        w = (
            center[0] + right[0] * ux * size[0] + up[0] * uy * size[1] + fwd[0] * uz * size[2],
            center[1] + right[1] * ux * size[0] + up[1] * uy * size[1] + fwd[1] * uz * size[2],
            center[2] + right[2] * ux * size[0] + up[2] * uy * size[1] + fwd[2] * uz * size[2],
        )
        d = (w[0] - org[0], w[1] - org[1], w[2] - org[2])
        local = (
            d[0] * ax[0] + d[1] * ax[1] + d[2] * ax[2],
            d[0] * ay[0] + d[1] * ay[1] + d[2] * ay[2],
            d[0] * az[0] + d[1] * az[1] + d[2] * az[2],
        )
        cmds.xform("%s.cv[%d]" % (ctrl, i), t=local)


def makeFootIKTR(*args):
    """足用IK: 根元＋足首を選んで実行。足箱＋つま先箱まで自動で作る。"""
    cmds.undoInfo(openChunk=True, chunkName="makeFootIKTR")
    try:
        selection = cmds.ls(sl=True, long=True)
        if len(selection) != 2:
            cmds.error("足のIKを作るために、ジョイントを正確に2つ（根元と足首）選んでね。")

        start_joint = selection[0]
        ankle_joint = selection[1]

        children = cmds.listRelatives(
            ankle_joint, children=True, type="joint", fullPath=True) or []
        ball_joint = None
        for c in children:
            if "ball" in c.split("|")[-1].lower():
                ball_joint = c
                break
        if ball_joint is None and children:
            ball_joint = children[0]
        if ball_joint is None:
            cmds.error("足首の先にボールの骨が見つからなかったよ。"
                       "足用のIKは、ボールのある脚専用だよ。")

        controlPref = _ui_get("controlPrefix", "")
        controlSuff = _ui_get("controlName", "_CTRL")
        rgbColor = _ui_get("controlColorRGB", (0.3, 0.7, 1.0))
        useOffsetGrp = _ui_get("useOffsetGrp", False)
        ballColor = (0.3, 0.85, 0.9)

        ankle_pos = cmds.xform(ankle_joint, q=True, ws=True, t=True)
        ball_pos = cmds.xform(ball_joint, q=True, ws=True, t=True)

        fwd = (ball_pos[0] - ankle_pos[0], 0.0, ball_pos[2] - ankle_pos[2])
        d = math.sqrt(fwd[0] * fwd[0] + fwd[2] * fwd[2])
        if d < 0.001:
            cmds.error("足首とボールの位置が近すぎて、足の向きが分からなかったよ。")
        fwd = (fwd[0] / d, 0.0, fwd[2] / d)
        right = (fwd[2], 0.0, -fwd[0])
        up = (0.0, 1.0, 0.0)

        # 箱の大きさは足首→ボールの距離 d から決める (スケール非依存)
        sole_y = ball_pos[1] - d * 0.02
        box_h = (ankle_pos[1] - sole_y) * 1.10

        # ---- 足コントローラ (ピボットは足首、形は足全体の箱) ----
        base_ankle = ankle_joint.split("|")[-1].replace("_JNT", "").replace("_jnt", "")
        ctrl = _create_control(rgbColor, "正六面体（キューブ）", "X")
        ctrl_name = cmds.rename(ctrl, controlPref + base_ankle + controlSuff)
        if useOffsetGrp:
            grp_name = cmds.group(ctrl_name, name=ctrl_name + "_GRP")
            _snap_ctrl_to_joint(grp_name, ankle_joint)
        else:
            _snap_ctrl_to_joint(ctrl_name, ankle_joint)

        # 参考画像どおり: 赤い箱は かかと→ボールまで
        box_size = (d * 0.62, box_h, d * 1.4)
        box_center = (
            ankle_pos[0] + fwd[0] * d * 0.35,
            sole_y + box_h / 2.0,
            ankle_pos[2] + fwd[2] * d * 0.35,
        )
        _reshape_ctrl_box(ctrl_name, box_center, right, up, fwd, box_size)

        ik_handle, ik_effector = cmds.ikHandle(
            startJoint=start_joint, endEffector=ankle_joint, sol="ikRPsolver")
        short_start = start_joint.split("|")[-1]
        ik_handle_name = cmds.rename(ik_handle, short_start + "_ikHandle")
        cmds.parent(ik_handle_name, ctrl_name)

        # ---- ボールコントローラ (ピボットはボール、足コントローラの子) ----
        base_ball = ball_joint.split("|")[-1].replace("_JNT", "").replace("_jnt", "")
        bctrl = _create_control(ballColor, "正六面体（キューブ）", "X")
        bctrl_name = cmds.rename(bctrl, controlPref + base_ball + controlSuff)
        _snap_ctrl_to_joint(bctrl_name, ball_joint)

        b_h = box_h * 0.5
        # 青い箱は ボール→つま先まで (赤との重なりは少しだけ)
        b_size = (box_size[0] * 0.92, b_h, d * 0.65)
        b_center = (
            ball_pos[0] + fwd[0] * d * 0.175,
            sole_y + b_h / 2.0,
            ball_pos[2] + fwd[2] * d * 0.175,
        )
        _reshape_ctrl_box(bctrl_name, b_center, right, up, fwd, b_size)

        cmds.parent(bctrl_name, ctrl_name)
        cmds.orientConstraint(bctrl_name, ball_joint, maintainOffset=True)
        cmds.pointConstraint(bctrl_name, ball_joint, maintainOffset=True)
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

WINDOW_NAME = "majimeruBenriRigV28Window"
WINDOW_TITLE = "誰でもリグ作れるよツール V28 - majimeru"

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
    "makeFootIKTR": "足のIKコントローラを作ったよ（つま先の箱つき）",
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
        # V26: 全ノードではなく DAG だけに絞って軽くする
        nodes_before = set(cmds.ls(dagObjects=True, long=True) or [])
        sel_before = cmds.ls(sl=True, long=True) or []
        sig_before = self._sel_xform_sig(sel_before)
        if is_redo:
            cmds.redo()
        else:
            cmds.undo()
        nodes_after = set(cmds.ls(dagObjects=True, long=True) or [])
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
        # 高速化 (V26): まとめて取り消す間は画面の再描画を止める。
        # ステップごとの再描画が一番重かった。終わったら必ず戻す。
        try:
            cmds.refresh(suspend=True)
        except Exception:
            pass
        try:
            self._smart_undo_loop()
        finally:
            try:
                cmds.refresh(suspend=False)
            except Exception:
                pass

    def _smart_undo_loop(self):
        # 選択だけのステップと「何も変わらない」ステップを
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
        # 高速化 (V26): undo と同じく、処理中は画面の再描画を止める
        try:
            cmds.refresh(suspend=True)
        except Exception:
            pass
        try:
            self._smart_redo_loop()
        finally:
            try:
                cmds.refresh(suspend=False)
            except Exception:
                pass

    def _smart_redo_loop(self):
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
        title = QtWidgets.QLabel("✨ 誰でもリグ作れるよツール V28 ✨")
        title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #e6b93d;")
        title_row.addWidget(title)
        title_row.addStretch(1)
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
        lay.addWidget(self._btn("足用のIKコントローラーを作る",
                                makeFootIKTR, _C_TEAL))
        lay.addWidget(self._note(
            "💡 足用は「根元＋足首」の2つを選んで押してね。足首の先に"
            "ボールの骨がある脚専用だよ。足全体の箱と、つま先の箱が"
            "自動でできるよ。"))
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
    # V4 までの入口名との互換用 (中身は V28 の Qt ウィンドウ)
    return show_ui()


try:
    show_ui()
except Exception:
    traceback.print_exc()


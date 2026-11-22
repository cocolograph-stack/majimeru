# ============================================================
# ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
# ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
# #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
# ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
# ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
# ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
# ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
#
#  Tool    : majimeru_gentle_ui  v1
#  Author  : majimeru + とびうおぴょんぴょん
#  What    : Blender setup script: rounded pill buttons + gentle colours (theme)
#  YouTube : https://www.youtube.com/@3DCGいろいろ
#  License : GPL-3.0 - free to use, modify and share.
#            Keep this note when you share it.
# ============================================================
#
# 使い方: Scripting タブで開いて ▶ Run Script を1回押すだけ。
# Blender 全体のボタンの角を丸くして、色を優しくする（テーマ変更）。
# 戻したい時は Preferences > Themes の左上メニューから
# 「Reset to Default Theme」で初期状態に戻る。

import bpy

theme = bpy.context.preferences.themes[0]
ui = theme.user_interface

# 角を最大まで丸く（ピル型）する対象
for name in ("wcol_tool", "wcol_regular", "wcol_radio", "wcol_toggle",
             "wcol_option", "wcol_num", "wcol_menu", "wcol_list_item"):
    wcol = getattr(ui, name, None)
    if wcol is not None:
        wcol.roundness = 1.0

# 道具ボタン（パネルの実行ボタン）の色を優しく
tool = ui.wcol_tool
tool.inner = (0.36, 0.39, 0.46, 1.0)       # 柔らかい青グレー
tool.inner_sel = (0.85, 0.47, 0.22, 1.0)   # 選んだ時は優しいオレンジ
tool.text = (0.94, 0.95, 0.97)
tool.text_sel = (1.0, 1.0, 1.0)

# 通常ボタンも少しだけ明るく柔らかく
regular = ui.wcol_regular
regular.inner = (0.37, 0.37, 0.37, 1.0)
regular.inner_sel = (0.85, 0.47, 0.22, 1.0)

# ラジオボタン（並んだ切替）の選択色もオレンジに揃える
radio = ui.wcol_radio
radio.inner_sel = (0.85, 0.47, 0.22, 1.0)

bpy.ops.wm.save_userpref()
print("[Majimeru Gentle UI] ボタンを丸くして、色を優しくしたよ（保存済み）")

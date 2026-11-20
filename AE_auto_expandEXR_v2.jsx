// ============================================================
// ##     ##    ###          ## #### ##     ## ######## ########  ##     ##
// ###   ###   ## ##         ##  ##  ###   ### ##       ##     ## ##     ##
// #### ####  ##   ##        ##  ##  #### #### ##       ##     ## ##     ##
// ## ### ## ##     ##       ##  ##  ## ### ## ######   ########  ##     ##
// ##     ## ######### ##    ##  ##  ##     ## ##       ##   ##   ##     ##
// ##     ## ##     ## ##    ##  ##  ##     ## ##       ##    ##  ##     ##
// ##     ## ##     ##  ######  #### ##     ## ######## ##     ##  #######
//
//  Tool    : AE_auto_expandEXR_v2  v2
//  Author  : majimeru + とびうおぴょんぴょん
//  What    : After Effects script
//  YouTube : https://www.youtube.com/@3DCGいろいろ
//  License : GPL-3.0 - free to use, modify and share.
//            Keep this note when you share it.
// ============================================================

// AE_auto_expandEXR_v2.jsx
// ============================================================
// Maya (Arnold) マルチチャンネルEXR → After Effects 自動展開・合成 v2
//
// 対象: arnold_aov_setup_v2.py の「①フル合成セット」で出したEXR専用
// (完全分解 + テクニカル + Cryptomatte + AO、計18 AOV)
// ②クイック / ②'コンポ下見 / ③グレード用のEXRには使えません
// (チャンネル数が違うので番号がずれます)
//
// v1 (AE_auto_expandEXR_fixed.jsx) からの変更点:
// 1. V2 ①の出力に合わせてレイヤーを 13 → 19 に増やした
// (追加: volume, N, motionvector, crypto_asset/material/object)
// v1の13層のままだと、V2 ①で出した volume / N / motionvector /
// Crypto がコンポに入らず、足しても beauty に戻りません。
// 2. 重ね順と表示を直した
// v1は beauty を NORMAL で一番上に置いていたので、下の ADD 層が
// 全部隠れていました。v2では beauty は参照用に非表示、
// Z / N / motionvector / Crypto はユーティリティとして非表示、
// 合成に使うのは background + ADD層 + AO だけです。
// 3. EXtractoR のチャンネル割り当てを入れた (本丸)
// 各レイヤーの EXtractoR に「お前はこのAOVを取り出せ」と指定します。
//
//
// チャンネル番号 (CHANNELS表) は、Arnold の書き出し順と AE の読み込み順が
// 「beauty → プリセットのAOV追加順」で並ぶという推定で計算しています。
// AE実機では未検証です。もし分離結果がおかしかったら、
// エフェクトコントロールの EXtractoR のドロップダウンが各レイヤーで
// 何を示しているか教えてください。CHANNELS表の1か所だけ直せば全部直ります。
// また、Red/Green/Blue/Alpha というパラメータ名が見つからない場合は
// スクリプトが実際のパラメータ名をアラートで出すので、その文言を教えてください。
// ============================================================
(function () {

var proj = app.project;
if (!proj) {
alert("プロジェクトが開かれていません。");
return;
}

// 1. プロジェクトパネルで選択されているアイテムを取得
var targetFootage = null;
var selection = proj.selection;
if (selection && selection.length > 0) {
for (var i = 0; i < selection.length; i++) {
if (selection[i] instanceof FootageItem) {
targetFootage = selection[i];
break;
}
}
}
if (!targetFootage) {
alert("プロジェクトパネルでマルチEXRフッテージ（または連番）を直接選択してください。\n（タイムライン上のレイヤーではなく、左側の素材一覧です）");
return;
}

// 2. EXRのチャンネル構成表 (推定。1始まりの通し番号)
// beauty RGBA → 各AOVはプリセットの追加順。
// カラーAOVは R/G/B の3ch、Zは1ch、Nは3ch(X/Y/Z)、
// motionvectorは2ch(X/Y)、Cryptomatteは RGBA の4chと想定。
// Alpha に使うのは beauty の A (4番)。AOV自体に A が無いため。
var BEAUTY_ALPHA = 4;
var CHANNELS = {
"beauty": { r: 1, g: 2, b: 3, a: 4},
"diffuse_direct": { r: 5, g: 6, b: 7, a: BEAUTY_ALPHA},
"diffuse_indirect": { r: 8, g: 9, b: 10, a: BEAUTY_ALPHA},
"specular_direct": { r: 11, g: 12, b: 13, a: BEAUTY_ALPHA},
"specular_indirect":{ r: 14, g: 15, b: 16, a: BEAUTY_ALPHA},
"coat_direct": { r: 17, g: 18, b: 19, a: BEAUTY_ALPHA},
"coat_indirect": { r: 20, g: 21, b: 22, a: BEAUTY_ALPHA},
"transmission": { r: 23, g: 24, b: 25, a: BEAUTY_ALPHA},
"sss": { r: 26, g: 27, b: 28, a: BEAUTY_ALPHA},
"volume": { r: 29, g: 30, b: 31, a: BEAUTY_ALPHA},
"emission": { r: 32, g: 33, b: 34, a: BEAUTY_ALPHA},
"background": { r: 35, g: 36, b: 37, a: BEAUTY_ALPHA},
"Z": { r: 38, g: 38, b: 38, a: BEAUTY_ALPHA},
"N": { r: 39, g: 40, b: 41, a: BEAUTY_ALPHA},
"motionvector": { r: 42, g: 43, b: 43, a: BEAUTY_ALPHA},
"crypto_asset": { r: 44, g: 45, b: 46, a: 47},
"crypto_material": { r: 48, g: 49, b: 50, a: 51},
"crypto_object": { r: 52, g: 53, b: 54, a: 55},
"AO": { r: 56, g: 57, b: 58, a: BEAUTY_ALPHA}
};

// 3. レイヤー構成 (上から下の順。ADD層を足すと beauty に戻る)
// enabled:false = 非表示 (合成には混ぜない。参照・ユーティリティ用)
var LAYERS = [
{ name: "beauty", mode: BlendingMode.NORMAL, enabled: false},
{ name: "AO", mode: BlendingMode.MULTIPLY, enabled: true},
{ name: "emission", mode: BlendingMode.ADD, enabled: true},
{ name: "volume", mode: BlendingMode.ADD, enabled: true},
{ name: "sss", mode: BlendingMode.ADD, enabled: true},
{ name: "transmission", mode: BlendingMode.ADD, enabled: true},
{ name: "coat_indirect", mode: BlendingMode.ADD, enabled: true},
{ name: "coat_direct", mode: BlendingMode.ADD, enabled: true},
{ name: "specular_indirect",mode: BlendingMode.ADD, enabled: true},
{ name: "specular_direct", mode: BlendingMode.ADD, enabled: true},
{ name: "diffuse_indirect", mode: BlendingMode.ADD, enabled: true},
{ name: "diffuse_direct", mode: BlendingMode.ADD, enabled: true},
{ name: "background", mode: BlendingMode.NORMAL, enabled: true},
{ name: "Z", mode: BlendingMode.NORMAL, enabled: false},
{ name: "N", mode: BlendingMode.NORMAL, enabled: false},
{ name: "motionvector", mode: BlendingMode.NORMAL, enabled: false},
{ name: "crypto_asset", mode: BlendingMode.NORMAL, enabled: false},
{ name: "crypto_material", mode: BlendingMode.NORMAL, enabled: false},
{ name: "crypto_object", mode: BlendingMode.NORMAL, enabled: false}
];

app.beginUndoGroup("Unpack EXR to Comp v2");

try {
// 4. フロートAOVの加算合成のためプロジェクトを32bpcに
// (8bpcのままだと加算でクリップして beauty に戻りません)
try {
if (proj.bitsPerChannel!== 32) {
proj.bitsPerChannel = 32;
}
} catch (bpcErr) {}

var w = targetFootage.width > 0? targetFootage.width: 1920;
var h = targetFootage.height > 0? targetFootage.height: 1080;
var par = targetFootage.pixelAspect > 0? targetFootage.pixelAspect: 1.0;
var dur = targetFootage.duration > 0? targetFootage.duration: 10.0;
var fps = targetFootage.frameRate > 0? targetFootage.frameRate: 24.0;
var compName = targetFootage.name.replace(/\.[^\.]+$/, "") + "_Comp";
var comp = proj.items.addComp(compName, w, h, par, dur, fps);

// 5. EXtractoR のパラメータ名を確認 (無ければ実際の名前を報告して中断)
var probeLayer = comp.layers.add(targetFootage);
probeLayer.name = "__probe__";
var probeFx = null;
try {
probeFx = probeLayer.property("ADBE Effect Parade").addProperty("ADBE EXtractoR");
} catch (fxErr) {}
var chanProps = null;
if (probeFx) {
var pR = null, pG = null, pB = null, pA = null;
try { pR = probeFx.property("Red");} catch (e1) {}
try { pG = probeFx.property("Green");} catch (e2) {}
try { pB = probeFx.property("Blue");} catch (e3) {}
try { pA = probeFx.property("Alpha");} catch (e4) {}
if (pR && pG && pB && pA) {
chanProps = { r: "Red", g: "Green", b: "Blue", a: "Alpha"};
} else {
var names = [];
try {
for (var pi = 1; pi <= probeFx.numProperties; pi++) {
names.push(probeFx.property(pi).name);
}
} catch (e5) {}
probeLayer.remove();
comp.remove();
alert("EXtractoR のチャンネル指定がこのAEでは Red/Green/Blue/Alpha という名前で見つかりませんでした。\n実際のパラメータ名:\n" + names.join("\n") + "\n\nこの文言をそのまま教えてください。CHANNELS表と合わせて直します。");
return;
}
}
probeLayer.remove();

// 6. 各AOVレイヤーを生成 (下から積むので逆順に追加)
for (var j = LAYERS.length - 1; j >= 0; j--) {
var def = LAYERS[j];
var layer = comp.layers.add(targetFootage);
layer.name = def.name;
layer.blendingMode = def.mode;
layer.enabled = def.enabled;

var fx = null;
try {
fx = layer.property("ADBE Effect Parade").addProperty("ADBE EXtractoR");
} catch (fxErr2) {}
if (fx && chanProps) {
var ch = CHANNELS[def.name];
if (ch) {
try { fx.property(chanProps.r).setValue(ch.r);} catch (e6) {}
try { fx.property(chanProps.g).setValue(ch.g);} catch (e7) {}
try { fx.property(chanProps.b).setValue(ch.b);} catch (e8) {}
try { fx.property(chanProps.a).setValue(ch.a);} catch (e9) {}
}
}
}

comp.openInViewer();
alert("19レイヤーでコンポを作成しました。\n表示されているのは background + ADD層 + AO の合成結果です。\nbeauty 層は非表示の参照用です。\n\n合成結果と beauty 層の絵を見比べてください。\n合わなければ、EXtractoR のチャンネル番号がずれています。");

} catch (e) {
alert("処理中にエラーが発生しました:\n" + e.toString());
} finally {
app.endUndoGroup();
}
})();

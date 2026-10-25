"""原理用語辞典を作る: _tools/jisho/terms.json → jisho/index.html

    python -I -X utf8 _tools/jisho/build_jisho.py

ポケ辞書（pokejisho.com）のように、日本語・韓国語・英語のどれで引いても3つが並んで出る辞書。
語と訳語は『原理講論』の三か国語対訳（taiyaku/genri_kouron/data）から、同じ段落に出てくる形を
採った（作り方は _tools/jisho/README.md）。辞書の行は全部ページに書き出し、絞り込みは JS で行う
（JS が無くても全部読める・検索エンジンにも載る）。

terms.json の1件:
    id     通し番号（付け直さない。リンク #t123 に使う）
    cat    P=原理 F=信仰・聖書 H=歴史・思想 N=人名 L=地名・国・民族
    ja     日本語訳に出る形          yomi  そのよみ（ひらがな。カタカナだけの語は空）
    ko     韓国語の原典に出る形      hanja 原典で添えてある漢字（無ければ空）
    en     英語訳に出る形            en_alt ほかの言い方（任意）
    ja_alt / ko_alt                  表記の揺れ（任意）
    ref    "1-1-2:3" 3つがそろって出る段落（対訳の節の鍵:段落。段落は0始まり）
    n      原典で漢字が添えてある回数（並べる順に使う。人名・地名は英語に出る段落の数）
"""

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "seika"))
sys.path.insert(0, str(HERE.parent / "root"))
from hangul_kana import to_kana  # noqa: E402
from lighten_pages import BOOT as THEME_BOOT  # noqa: E402
from build_seika import THEME_V, KO_FONT_MARK, ko_font_link, TYPO_BOX  # noqa: E402

OUT = ROOT / "jisho"
URL = "https://maydra.github.io/mimune-no-uraniwa/jisho/"
CATS = [("P", "原理"), ("F", "信仰・聖書"), ("H", "歴史・思想"), ("N", "人名"), ("L", "地名・民族")]
CAT_NAME = dict(CATS)

SINO = "영일이삼사오육칠팔구"


def sino(n):
    """1〜99 を漢数字の韓国語の読みに（3대 → 삼대、12소선지 → 십이소선지）"""
    t, o = divmod(n, 10)
    s = ("" if t == 1 else SINO[t]) + "십" if t else ""
    return s + (SINO[o] if o else "") or "영"


def ko_kana(ko):
    return to_kana(re.sub(r"\d+", lambda m: sino(int(m.group())), ko))


# パッチムの小さいカナ（ㇰ ㇺ ㇽ ㇷ゚ など、U+31F0〜）は NFKC でも普通のカナにならないので、ここで直す
EXT_KANA = str.maketrans({chr(0x31F0 + i): c for i, c in enumerate("クシストヌハヒフヘホムラリルレロ")})


def norm(s):
    """検索の鍵。JS の norm() と同じにする（小さいカナを直す・NFKC・小文字・カタカナ→ひらがな・空白や記号を外す）"""
    import unicodedata
    s = unicodedata.normalize("NFKC", s.translate(EXT_KANA)).lower()
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    return re.sub(r"[\s\-‐・·'’.,、。()（）]", "", s)


def ref_link(ref):
    """対訳のビューアは #節の鍵-段落（段落は1始まり）でその段落へ飛ぶ"""
    sec, r = ref.split(":")
    return f"../taiyaku/genri_kouron/index.html#{sec}-{int(r) + 1}"


def esc(s):
    return html.escape(s, quote=True)


# 韓国語の発音のカナでも引けるようにする（説教で耳にした「チョンドリョン」から引く）。
# パッチムの小さいカナ（ㇰ ㇺ ㇽ ㇷ゚）は NFKC で ク ム ル プ になる。ㄱ・ㅂ のパッチムは
# 「ポックィ」と ッ で書く人も多いので、その形も鍵に入れる
SOKUON = str.maketrans({"ㇰ": "ッ", "ㇷ": "ッ"})


def kana_keys(ko):
    kana = ko_kana(ko)
    return [kana, kana.replace("ㇷ゚", "ㇷ").translate(SOKUON)]


def row(t):
    keys = [t["ja"], t.get("yomi", ""), t["ko"], t.get("hanja", ""), t["en"]]
    keys += t.get("en_alt", []) + t.get("ja_alt", []) + t.get("ko_alt", [])
    for ko in [t["ko"]] + t.get("ko_alt", []):
        keys += kana_keys(ko)
    k = "|".join(dict.fromkeys(norm(x) for x in keys if x))
    ja = esc(t["ja"])
    if t.get("yomi"):
        ja = f'<ruby>{ja}<rt>{esc(t["yomi"])}</rt></ruby>'
    hz = f'<span class="hz" lang="ko-Hani">{esc(t["hanja"])}</span>' if t.get("hanja") else ""
    alt_ja = "".join(f'<span class="alt">{esc(a)}</span>' for a in t.get("ja_alt", []))
    alt_ko = "".join(f'<span class="alt" lang="ko">{esc(a)}</span>' for a in t.get("ko_alt", []))
    alt_en = "".join(f'<span class="alt">{esc(a)}</span>' for a in t.get("en_alt", []))
    return (
        f'<li id="t{t["id"]}" data-c="{t["cat"]}" data-k="{esc(k)}">'
        f'<span class="cat c-{t["cat"]}">{CAT_NAME[t["cat"]]}</span>'
        f'<div class="l ja"><span class="w" lang="ja">{ja}</span>{alt_ja}</div>'
        f'<div class="l ko"><span class="w" lang="ko">{esc(t["ko"])}</span>{hz}'
        f'<span class="kana">{esc(ko_kana(t["ko"]))}</span>{alt_ko}</div>'
        f'<div class="l en"><span class="w" lang="en">{esc(t["en"])}</span>{alt_en}</div>'
        f'<a class="src" href="{ref_link(t["ref"])}">原理講論で読む</a>'
        "</li>"
    )


HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google tag (gtag.js)。本体は表示し終えてから読む（ホーム・聖歌と同じ） -->
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());

    gtag('config', 'G-XXQ0QTBYTR');
    function afterPaint(fn) {{
      var done = false;
      var run = function () {{ if (!done) {{ done = true; setTimeout(fn, 0); }} }};
      var onLoad = function () {{
        try {{
          if (performance.getEntriesByName('first-contentful-paint').length) return run();
          new PerformanceObserver(function (list) {{
            if (list.getEntriesByName('first-contentful-paint').length) run();
          }}).observe({{ type: 'paint', buffered: true }});
        }} catch (e) {{ }}
        setTimeout(run, 1000);
      }};
      if (document.readyState === 'complete') onLoad();
      else window.addEventListener('load', onLoad);
    }}
    afterPaint(function () {{
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=G-XXQ0QTBYTR';
      document.head.appendChild(s);
    }});
  </script>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>原理用語辞典（日・韓・英） | み旨の裏庭</title>
  <meta name="description" content="{desc}" />
  <meta property="og:title" content="原理用語辞典（日・韓・英） | み旨の裏庭" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="https://maydra.github.io/mimune-no-uraniwa/og-image.jpg" />
  <link rel="canonical" href="{url}" />
  <link rel="icon" href="/mimune-no-uraniwa/favicon.png?v={theme_v}" type="image/png" />
  {ko_font}
  <link rel="stylesheet" href="../theme/style.css?v={theme_v}">
  <link rel="stylesheet" href="../theme/pages/e631ced897.css?v={theme_v}">
  <style>{css}</style>
</head>
"""

CSS = """
.jisho{--ink:#ece9f6;--sub:#b9b3d6;--rule:rgba(255,255,255,.14);--panel:rgba(255,255,255,.05);
  --accent:#f0a6fb;--ko:#5eead4;--en:#fcd34d;--P:#c4b5fd;--F:#f9a8d4;--H:#93c5fd;--N:#fdba74;--L:#86efac}
body.light-mode .jisho{--ink:#161616;--sub:#5b5670;--rule:rgba(0,0,0,.12);--panel:#f6f5fa;
  --accent:#8a3ea8;--ko:#0f766e;--en:#92400e;--P:#6d28d9;--F:#be185d;--H:#1d4ed8;--N:#c2410c;--L:#15803d}
*{box-sizing:border-box}
body{margin:0;font-family:"Hiragino Mincho ProN","BIZ UDPMincho","Yu Mincho",YuMincho,"Noto Serif CJK JP","Noto Serif JP",serif;
  background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%) #211c4a;min-height:100vh;color:#e0e0e0;
  padding:2.5rem 1rem;line-height:1.7}
.container{max-width:1000px;margin:0 auto;background:rgba(255,255,255,.05);padding:2.6rem 3rem;border-radius:24px;
  border:1px solid rgba(255,255,255,.1);box-shadow:0 25px 60px rgba(0,0,0,.5)}
[lang="ko"]{font-family:AppleMyungjo,Batang,"Noto Serif KR","Hiragino Mincho ProN","BIZ UDPMincho","Yu Mincho",YuMincho,"Noto Serif CJK KR",serif}
[lang="en"]{font-family:Georgia,"Times New Roman",serif}
.jisho .home{font-size:.85rem;margin:0 0 1rem}
.jisho .home a{color:var(--sub)!important;text-decoration:none}
.jisho h1{text-align:center;font-size:1.9rem;margin:0;color:var(--ink)!important;letter-spacing:.06em}
.jisho h1 small{display:block;font-size:.5em;letter-spacing:.2em;color:var(--sub)!important;-webkit-text-fill-color:var(--sub)!important;margin-top:.2em}
.jisho .beta-tag{font-size:.4em;vertical-align:middle;padding:.1rem .7rem;border-radius:999px;border:1px solid var(--accent);
  color:var(--accent)!important;-webkit-text-fill-color:var(--accent)!important;font-weight:400;letter-spacing:0}
.jisho .lead{text-align:center;color:var(--sub)!important;font-size:.92rem;margin:.8rem 0 1.4rem}
.jisho .search{position:sticky;top:.5rem;z-index:5;max-width:36rem;margin:0 auto 1rem}
.jisho #q{width:100%;font:inherit;font-size:1.15rem;padding:.75rem 1.2rem;border-radius:999px;border:1px solid var(--rule);
  background:#1b1838;color:var(--ink)!important;box-shadow:0 6px 24px rgba(0,0,0,.35);-webkit-appearance:none;appearance:none}
body.light-mode .jisho #q{background:#fff;box-shadow:0 4px 16px rgba(0,0,0,.12)}
.jisho #q:focus{outline:2px solid var(--accent);outline-offset:1px}
.jisho .cats{display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin:0 0 .6rem}
.jisho .cats button{font:inherit;font-size:.82rem;padding:.2rem .8rem;border-radius:999px;border:1px solid var(--rule);
  background:none;color:var(--sub)!important;cursor:pointer}
.jisho .cats button[aria-pressed="true"]{background:var(--panel);border-color:var(--accent);color:var(--ink)!important}
.jisho .cats button span{opacity:.6;font-size:.85em;margin-left:.3em}
.jisho .count{text-align:center;font-size:.8rem;color:var(--sub)!important;margin:0 0 .8rem;min-height:1.2em}
.jisho .terms{list-style:none;margin:0;padding:0}
.jisho .terms li{display:grid;grid-template-columns:6.2rem minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.2fr);gap:.4rem 1rem;
  align-items:baseline;padding:.75rem .3rem .7rem;border-top:1px solid var(--rule);position:relative;min-height:5.2rem}
.jisho .terms li[hidden]{display:none}
/* 590 行を一度に組むとスマホで重い（Lighthouse の TBT 0.7〜1.6秒）。画面の外の行は組むのを後回しにする */
.jisho .terms li{content-visibility:auto;contain-intrinsic-size:auto 5.6rem;scroll-margin-top:5.5rem}
.jisho .terms li:target{background:var(--panel);outline:2px solid var(--accent);border-radius:10px}
.jisho .cat{font-size:.72rem;justify-self:start;padding:.05rem .55rem;border-radius:999px;border:1px solid currentColor;white-space:nowrap}
.jisho .c-P{color:var(--P)!important}.jisho .c-F{color:var(--F)!important}.jisho .c-H{color:var(--H)!important}
.jisho .c-N{color:var(--N)!important}.jisho .c-L{color:var(--L)!important}
.jisho .l{min-width:0}
.jisho .w{cursor:copy;border-radius:4px;color:var(--ink)!important;font-size:1.12rem}
.jisho .w:hover{background:var(--panel)}
.jisho .ja .w{font-weight:700}
.jisho .ko .w{color:var(--ko)!important}
.jisho .en .w{color:var(--en)!important;font-size:1.05rem}
.jisho ruby rt{font-size:.55em;font-weight:400;color:var(--sub);letter-spacing:.04em}
.jisho .hz,.jisho .kana,.jisho .alt{display:block;font-size:.78rem;color:var(--sub)!important;line-height:1.5}
.jisho .hz{font-family:"Hiragino Mincho ProN","BIZ UDPMincho","Yu Mincho",serif}
.jisho .alt::before{content:"＝ ";opacity:.6}
.jisho .src{position:absolute;left:.3rem;bottom:.7rem;font-size:.72rem;color:var(--sub)!important;text-decoration:none;white-space:nowrap}
.jisho .src::after{content:" ›"}
.jisho .src:hover{color:var(--accent)!important}
.jisho .none{text-align:center;color:var(--sub)!important;padding:1.5rem 0}
.jisho .note{margin-top:2rem;font-size:.8rem;color:var(--sub)!important;line-height:1.8}
.jisho .note p{color:var(--sub)!important;margin:.4rem 0}
.jisho .note a{color:var(--accent)!important}
#jisho-toast{position:fixed;left:50%;bottom:1.4rem;transform:translate(-50%,1rem);opacity:0;pointer-events:none;
  background:rgba(20,18,40,.94);color:#fff!important;padding:.5rem 1.1rem;border-radius:999px;font-size:.9rem;
  transition:opacity .2s,transform .2s;z-index:50;max-width:90vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#jisho-toast.on{opacity:1;transform:translate(-50%,0)}
@media (max-width:720px){
  body{padding:1rem .6rem}
  .container{padding:1.4rem .9rem;border-radius:16px}
  .jisho h1{font-size:1.5rem}
  .jisho .terms li{grid-template-columns:minmax(0,1fr);gap:.1rem;padding:.7rem .2rem .55rem;min-height:0}
  .jisho .cat{position:absolute;right:.2rem;top:.75rem}
  .jisho .l{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:.6rem}
  .jisho .hz,.jisho .kana,.jisho .alt{display:inline}
  .jisho .ja{padding-right:5.5rem}
  .jisho .en{padding-right:6.5rem}
  .jisho .src{left:auto;right:.2rem;bottom:.65rem}
}
"""

BODY = """<body>
{boot}
  <div class="container">
    <main class="jisho">
      <p class="home"><a href="../index.html">← み旨の裏庭</a></p>
      <h1>原理用語辞典 <span class="beta-tag">試験中</span><small>日本語・한국어・English</small></h1>
      <p class="lead">日本語・韓国語・英語のどれで引いても、3つの言葉が並んで出ます。<br>語を押すとコピーできます。</p>
      <div class="search">
        <input type="search" id="q" placeholder="{placeholder}" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="search" aria-label="原理用語を引く（日本語・韓国語・英語・ローマ字）">
      </div>
      <div class="cats" role="group" aria-label="分類">
        <button type="button" data-c="" aria-pressed="true">すべて<span>{total}</span></button>
{cat_buttons}
      </div>
      <p class="count" id="count" aria-live="polite"></p>
      <ol class="terms" id="terms">
{rows}
      </ol>
      <p class="none" id="none" hidden>見つかりませんでした。別の言い方（漢字・ひらがな・ハングル・英語）でも試してください。</p>
      <div class="note">
        <p>語と訳語は『原理講論』の日本語訳・韓国語の原典『원리강론』・英語訳 <i>Exposition of the Divine Principle</i>（1996年）から、同じ段落に出てくる形を採りました。「原理講論で読む」から、その段落を<a href="../taiyaku/genri_kouron/index.html">三か国語の対訳</a>で読めます。</p>
        <p>韓国語の下のカナは発音の目安です。漢字は原典で添えてあるものです。並びは分類ごとに、原典に多く出る語から。ローマ字（fukki）や、韓国語の発音のカナ（チョンドリョン、ポックィソムニ）でも引けます。</p>
        <p>辞典は試験中です。訳語の違い・足りない語など、気づいたことは下の「誤植・修正提案」から送ってください。</p>
      </div>
{typo}
    </main>
  </div>
  <div id="jisho-toast" role="status"></div>
  <script>{js}</script>
  <script src="../theme/script.js?v={theme_v}" defer></script>
</body>
</html>
"""

JS = r"""
(function () {
  var q = document.getElementById('q'), list = document.getElementById('terms');
  var items = Array.prototype.slice.call(list.children);
  var none = document.getElementById('none'), count = document.getElementById('count');
  var cat = '';
  items.forEach(function (li, i) { li._k = li.getAttribute('data-k').split('|'); li._i = i; });

  // 入力欄の見本は、よく出る語から毎回ちがうものを（ポケ辞書と同じ）
  function word(li, sel) {
    var w = li.querySelector(sel + ' .w').cloneNode(true);
    Array.prototype.forEach.call(w.querySelectorAll('rt'), function (r) { r.remove(); });
    return w.textContent.trim();
  }
  var pick = items[Math.floor(Math.random() * Math.min(items.length, 60))];
  if (pick) q.placeholder = word(pick, '.ja') + '、' + word(pick, '.ko') + '、' + word(pick, '.en') + '…';

  // build_jisho.py の norm() と同じ
  var EXT = 'クシストヌハヒフヘホムラリルレロ';
  function norm(s) {
    s = s.replace(/[ㇰ-ㇿ]/g, function (c) { return EXT[c.charCodeAt(0) - 0x31f0]; });
    s = s.normalize('NFKC').toLowerCase();
    s = s.replace(/[ァ-ヶ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
    return s.replace(/[\s\-‐・·'’.,、。()（）]/g, '');
  }

  // ローマ字 → ひらがな（fukki → ふっき、setsuri / seturi → せつり）
  var ROMA = {a:'あ',i:'い',u:'う',e:'え',o:'お',ka:'か',ki:'き',ku:'く',ke:'け',ko:'こ',sa:'さ',si:'し',shi:'し',su:'す',se:'せ',so:'そ',
    ta:'た',ti:'ち',chi:'ち',tu:'つ',tsu:'つ',te:'て',to:'と',na:'な',ni:'に',nu:'ぬ',ne:'ね',no:'の',ha:'は',hi:'ひ',hu:'ふ',fu:'ふ',he:'へ',ho:'ほ',
    ma:'ま',mi:'み',mu:'む',me:'め',mo:'も',ya:'や',yu:'ゆ',yo:'よ',ra:'ら',ri:'り',ru:'る',re:'れ',ro:'ろ',wa:'わ',wo:'を',
    ga:'が',gi:'ぎ',gu:'ぐ',ge:'げ',go:'ご',za:'ざ',zi:'じ',ji:'じ',zu:'ず',ze:'ぜ',zo:'ぞ',da:'だ',di:'ぢ',du:'づ',de:'で',do:'ど',
    ba:'ば',bi:'び',bu:'ぶ',be:'べ',bo:'ぼ',pa:'ぱ',pi:'ぴ',pu:'ぷ',pe:'ぺ',po:'ぽ',
    kya:'きゃ',kyu:'きゅ',kyo:'きょ',sya:'しゃ',syu:'しゅ',syo:'しょ',sha:'しゃ',shu:'しゅ',sho:'しょ',she:'しぇ',
    tya:'ちゃ',tyu:'ちゅ',tyo:'ちょ',cha:'ちゃ',chu:'ちゅ',cho:'ちょ',nya:'にゃ',nyu:'にゅ',nyo:'にょ',hya:'ひゃ',hyu:'ひゅ',hyo:'ひょ',
    mya:'みゃ',myu:'みゅ',myo:'みょ',rya:'りゃ',ryu:'りゅ',ryo:'りょ',gya:'ぎゃ',gyu:'ぎゅ',gyo:'ぎょ',
    ja:'じゃ',ju:'じゅ',jo:'じょ',je:'じぇ',zya:'じゃ',zyu:'じゅ',zyo:'じょ',jya:'じゃ',jyu:'じゅ',jyo:'じょ',
    bya:'びゃ',byu:'びゅ',byo:'びょ',pya:'ぴゃ',pyu:'ぴゅ',pyo:'ぴょ',fa:'ふぁ',fi:'ふぃ',fe:'ふぇ',fo:'ふぉ',nn:'ん',"n'":'ん',xtu:'っ',ltu:'っ'};
  function toKana(s) {
    var out = '', i = 0;
    while (i < s.length) {
      var c = s[i], d = s[i + 1];
      if (c === d && /[bcdfghjkmpqrstvwxyz]/.test(c)) { out += 'っ'; i++; continue; }
      if (c === 'n' && d && !/[aiueoyn']/.test(d)) { out += 'ん'; i++; continue; }
      var hit = '';
      for (var L = 3; L >= 1; L--) { if (ROMA[s.substr(i, L)]) { hit = s.substr(i, L); break; } }
      if (!hit) {
        if (c === 'n' && i === s.length - 1) { out += 'ん'; i++; continue; }
        // 打ちかけの子音（fukk の k）だけなら、そこまでを使う。途中で読めないもの（chongdoryong）は
        // ローマ字ではないとみなす（ちょん… だけで関係ない語まで出ていた）
        return /^[a-z]{1,2}$/.test(s.slice(i)) ? out : '';
      }
      out += ROMA[hit]; i += hit.length;
    }
    return out;
  }

  function score(keys, a, b) {
    var best = 0;
    for (var j = 0; j < keys.length; j++) {
      var k = keys[j];
      for (var t = 0; t < 2; t++) {
        var x = t ? b : a;
        if (!x) continue;
        if (k === x) return 4;
        if (k.indexOf(x) === 0) best = Math.max(best, 3);
        else if (k.indexOf(x) > 0) best = Math.max(best, 2);
      }
    }
    return best;
  }

  var last = null;
  function run() {
    var raw = q.value.trim(), a = norm(raw), b = /^[a-z' ]+$/i.test(raw) ? toKana(a) : '';
    if (b.length < 2) b = '';
    var shown = [];
    items.forEach(function (li) {
      var ok = !cat || li.getAttribute('data-c') === cat;
      li._s = ok ? (a ? score(li._k, a, b) : 1) : 0;
      li.hidden = !li._s;
      if (li._s) shown.push(li);
    });
    // 当たりの強い順。同じなら元の並び（分類の順・多く出る順）
    shown.sort(function (x, y) { return y._s - x._s || x._i - y._i; });
    var key = shown.map(function (li) { return li._i; }).join(',');
    if (key !== last) { shown.forEach(function (li) { list.appendChild(li); }); last = key; }
    none.hidden = shown.length > 0;
    count.textContent = a || cat ? shown.length + ' 語' : '';
    var p = new URLSearchParams();
    if (raw) p.set('q', raw);
    if (cat) p.set('c', cat);
    var s = p.toString();
    try { history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + location.hash); } catch (e) { }
  }

  var t = null;
  q.addEventListener('input', function () { clearTimeout(t); t = setTimeout(run, 80); });
  q.addEventListener('keydown', function (e) { if (e.key === 'Enter') q.blur(); });
  Array.prototype.forEach.call(document.querySelectorAll('.cats button'), function (btn) {
    btn.addEventListener('click', function () {
      cat = btn.getAttribute('data-c');
      Array.prototype.forEach.call(document.querySelectorAll('.cats button'), function (o) { o.setAttribute('aria-pressed', o === btn ? 'true' : 'false'); });
      run();
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); q.focus(); }
  });

  // 語を押すとコピー（ルビの読みは入れない）
  var toast = document.getElementById('jisho-toast'), tt = null;
  function say(msg) {
    toast.textContent = msg; toast.classList.add('on');
    clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove('on'); }, 1600);
  }
  list.addEventListener('click', function (e) {
    var w = e.target.closest('.w');
    if (!w || (window.getSelection && String(window.getSelection()).length)) return;
    var c = w.cloneNode(true);
    Array.prototype.forEach.call(c.querySelectorAll('rt'), function (r) { r.remove(); });
    var text = c.textContent.trim();
    var done = function () { say('コピーしました：' + text); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { say(text); });
    else say(text);
  });

  var p = new URLSearchParams(location.search);
  if (p.get('c')) {
    var b0 = document.querySelector('.cats button[data-c="' + p.get('c') + '"]');
    if (b0) b0.click();
  }
  if (p.get('q')) q.value = p.get('q');
  if (p.get('q') || p.get('c')) run();
})();
"""


def main():
    terms = json.loads((HERE / "terms.json").read_text(encoding="utf-8"))
    # 並びは分類の順（原理 → 信仰・聖書 → …）、その中で多く出る順。n の数え方が用語（原典で漢字が
    # 添えてある回数）と人名・地名（英語に出る段落の数）で違うので、混ぜると人名が先頭に来る
    order = {c: i for i, (c, _) in enumerate(CATS)}
    terms.sort(key=lambda t: (order[t["cat"]], -t.get("n", 0), t["id"]))
    rows = "\n".join("        " + row(t) for t in terms)
    by_cat = {c: sum(1 for t in terms if t["cat"] == c) for c, _ in CATS}
    cat_buttons = "\n".join(
        f'        <button type="button" data-c="{c}" aria-pressed="false">{name}<span>{by_cat[c]}</span></button>'
        for c, name in CATS if by_cat[c])
    top = terms[0]
    placeholder = f'{top["ja"]}、{top["ko"]}、{top["en"]}…'
    desc = (f"原理講論に出てくる用語 {len(terms)} 語を、日本語・韓国語・英語のどれでも引ける辞典。"
            "『原理講論』の三か国語の本文に出てくる形で並べています。")
    page = HEAD.format(desc=esc(desc), url=URL, theme_v=THEME_V, ko_font=KO_FONT_MARK, css=CSS.strip()) + BODY.format(
        boot=THEME_BOOT, placeholder=esc(placeholder), total=len(terms), cat_buttons=cat_buttons, rows=rows,
        typo=TYPO_BOX.replace("例：〇番の2行目の読みが違う、訳の行がずれている…", "例：〇〇の英語は△△のほうがよい、□□が載っていない…")
        .replace("該当の行をコピペ（任意）", "該当の語をコピペ（任意）"),
        js=JS.strip(), theme_v=THEME_V)
    page = ko_font_link(page)
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print("jisho/index.html", len(terms), "語", len(page.encode("utf-8")) // 1024, "KB")


if __name__ == "__main__":
    main()

"""原理原本 日韓対訳を作る: _tools/genbon/units.json → taiyaku/genri_genbon/

    python -I -X utf8 _tools/genbon/build_genbon.py

ビューアは原理講論の三か国語対訳（taiyaku/genri_kouron/index.html）をそのまま写し、言語を韓・日の2つにし、
画面の言葉・出典の説明・設定の保存先（dp. → wb.）を差し替える。原理講論の対訳のビューアを直したら、
これを回し直せば同じ直しが届く。

units.json の1件（段落）:
    id      通し番号
    vol     巻（1〜3）
    parts   [[原稿のページ, 原文]]。段落の途中で原稿のページが替わると2つ以上になる
    ja      日本語訳（原文からの AI 訳）。段落の途中のページの替わり目に〔ページ〕の印
    heading 見出し（節の題）なら true。ここから新しい節
    sub     節の中の小見出しなら true（節は分けず、節の目次にだけ出す）
    note    訳の断り（任意。訳文の後ろに ※ で出す）

節は見出しごと（巻が替わる所でも切る）。原稿の 398ページは掲示板に投稿されていないので、その旨の行を入れる。
"""

import html
import json
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "taiyaku" / "genri_kouron" / "index.html"
OUT = ROOT / "taiyaku" / "genri_genbon"
SITE = "https://maydra.github.io/mimune-no-uraniwa/taiyaku/genri_genbon/"
BOARD = "https://cafe.daum.net/ckatkfkdrhdqn/WD3Y"
MISSING_PAGES = {398}
MARK = re.compile(r"〔(\d+)〕")
SPLIT = 1500          # これより長い段落（原文の字数）は原稿のページの切れ目で行を分ける


# 画面の言葉が韓国語・英語のときに配るリンクの入口（原理講論の対訳の ko.html・en.html と同じ作り）
ENTRY = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}{lang}.html">
<meta property="og:locale" content="{loc}">
<meta name="twitter:card" content="summary">
<script>location.replace("index.html" + location.search + location.hash);</script>
</head>
<body>
<p><a href="index.html">{title}</a></p>
</body>
</html>
"""


def esc(s):
    return html.escape(s, quote=False)


def pg(n):
    return f'<span class="pg">〔{n}〕</span>'


def ja_html(t):
    return MARK.sub(lambda m: pg(m.group(1)), esc(t))


def sections(units):
    """見出しと巻の替わり目で節に分ける"""
    out, cur, title = [], None, None
    for u in units:
        new_vol = cur is not None and u["vol"] != cur["vol"]
        if u.get("heading") or cur is None or new_vol:
            if u.get("heading"):
                title = (u["ja"], u["parts"][0][1])
            elif title is None:
                title = ("原理原本", "원리원본")
            cur = {"vol": u["vol"], "title": title, "cont": not u.get("heading") and cur is not None, "units": []}
            out.append(cur)
        cur["units"].append(u)
    return out


def build_rows(sec, last_page):
    ko_cells, ja_cells = [], []
    r = 0
    for u in sec["units"]:
        first = u["parts"][0][0]
        # 原稿の欠けているページ（掲示板に無い）は、その前に断りの行を入れる
        for miss in sorted(MISSING_PAGES):
            if last_page < miss < first:
                ko_cells.append({"r": r, "h": pg(miss) + "（이 쪽은 게시판에 올라와 있지 않습니다）"})
                ja_cells.append({"r": r, "h": pg(miss) + "（このページは掲示板に投稿されていません）"})
                r += 1
        lead = pg(first) if first != last_page else ""
        # 長すぎる段落（掲示板が原稿の1ページを1かたまりで載せ、どのページも文の途中で終わっている所。
        # 371〜392ページは1万2千字の1段落になる）は、原稿のページの切れ目で行を分ける
        ja_parts = MARK.split(u["ja"])[0::2]
        if sum(len(t) for _, t in u["parts"]) > SPLIT and len(ja_parts) == len(u["parts"]) > 1:
            pieces = [(pg(p) if j else lead, esc(t), ja_html(ja_parts[j])) for j, (p, t) in enumerate(u["parts"])]
        else:
            ko = "".join((pg(p) if j else "") + esc(t) for j, (p, t) in enumerate(u["parts"]))
            pieces = [(lead, ko, ja_html(u["ja"]))]
        for j, (head, ko, ja) in enumerate(pieces):
            if u.get("note") and j == len(pieces) - 1:
                ja += f'<span class="note">※ {esc(u["note"])}</span>'
            kc, jc = {"r": r, "h": head + ko}, {"r": r, "h": head + ja}
            if u.get("heading") or u.get("sub"):
                kc["k"] = jc["k"] = 1
            ko_cells.append(kc)
            ja_cells.append(jc)
            r += 1
        last_page = u["parts"][-1][0]
    return ko_cells, ja_cells, r, last_page


# 段落の後ろの断り書き（※）と原稿のページの印（〔2〕）は、本文をまとめてコピーするときに混ざらないようにする
# （2026-10-26、ユーザー「訓読箇所としてまとめてコピペする時、※ 原文「惟測」は…とかまで選択されるとオジャマ」、ページの印も外してよい）。
# 画面では選べないようにし（.note と .pg の user-select）、それでも拾うブラウザのために、コピーする文字からも抜く
COPY_JS = r'''  document.addEventListener("copy", (e) => {
    const sel = getSelection();
    if (!e.clipboardData || !sel || !sel.rangeCount) return;
    const box = document.createElement("div");
    for (let i = 0; i < sel.rangeCount; i++) box.appendChild(sel.getRangeAt(i).cloneContents());
    const notes = [...box.querySelectorAll(".note, .pg")];
    if (!notes.length) return;
    let text = sel.toString();
    notes.forEach((n) => { text = text.replace(n.textContent, ""); });
    box.querySelectorAll(".note, .pg, rt, rp").forEach((n) => n.remove());
    e.clipboardData.setData("text/plain", text.replace(/\n{3,}/g, "\n\n").trim());
    e.clipboardData.setData("text/html", box.innerHTML);
    e.preventDefault();
  });

'''


def patch_viewer(src):
    """原理講論の対訳のビューアを、原理原本の日韓2言語用に書き換える。当たらない所があれば止める"""
    reps = [
        ('<title>原理講論 三か国語対訳</title>', '<title>原理原本 日韓対訳</title>'),
        ('content="韓国語・日本語・英語を段落ごとに並べて読める対訳です。"',
         'content="『原理原本』の韓国語の原文と日本語訳（AI 訳）を段落ごとに並べて読める対訳です。"'),
        ('content="原理講論 三か国語対訳"', 'content="原理原本 日韓対訳"'),
        ('taiyaku/genri_kouron/index.html"', 'taiyaku/genri_genbon/index.html"'),
        ('localStorage.getItem("dp.theme")', 'localStorage.getItem("wb.theme")'),
        ('localStorage.getItem("dp." + k)', 'localStorage.getItem("wb." + k)'),
        ('localStorage.setItem("dp." + k', 'localStorage.setItem("wb." + k'),
        ('    { id: "en", label: "English", tag: "EN" },\n', ''),
        ('store.get("langs", ["ko", "ja", "en"])', 'store.get("langs", ["ko", "ja"])'),
        ('title: "原理講論 三か国語対訳", brand: "原理講論 対訳"', 'title: "原理原本 日韓対訳", brand: "原理原本 対訳",\n'
         '      noticeSum: "お断り　日本語訳は AI による機械翻訳です", noticeX: "このお断りを消す",\n'
         '      notice: "『原理原本』の原文は韓国語だけで、公式の日本語訳はないと管理者は認識しています。'
         'このページの日本語訳は、あくまで AI による機械翻訳です。原文の意味を正しく受け取りたい方は、韓国語を学んで原文で読むことをおすすめします。"'),
        ('rows: "横3列", cols: "縦3列", layoutT: "縦3列（横並び） / 横3列（縦積み）"',
         'rows: "横2列", cols: "縦2列", layoutT: "縦2列（横並び） / 横2列（縦積み）"'),
        ('title: "원리강론 3개국어 대역", brand: "원리강론 대역"', 'title: "원리원본 한일 대역", brand: "원리원본 대역",\n'
         '      noticeSum: "안내　일본어 번역은 AI 기계 번역입니다", noticeX: "이 안내 닫기",\n'
         '      notice: "『원리원본』은 원문이 한국어뿐이며, 공식 일본어 번역은 없는 것으로 관리자는 알고 있습니다. '
         '이 페이지의 일본어 번역은 어디까지나 AI 기계 번역입니다. 원문의 뜻을 바르게 이해하시려면 한국어 원문으로 읽으시기를 권합니다."'),
        ('rows: "가로 3줄", cols: "세로 3단", layoutT: "세로 3단(나란히) / 가로 3줄(쌓기)"',
         'rows: "가로 2줄", cols: "세로 2단", layoutT: "세로 2단(나란히) / 가로 2줄(쌓기)"'),
        ('title: "Divine Principle — Three-Language Parallel", brand: "Divine Principle"',
         'title: "Wolli Wonbon — Korean-Japanese Parallel", brand: "Wolli Wonbon",\n'
         '      noticeSum: "Note: the Japanese is an AI machine translation", noticeX: "Dismiss this note",\n'
         '      notice: "The Wolli Wonbon exists only in the Korean original; as far as the site administrator knows, there is no official Japanese translation. '
         'The Japanese on this page is only a machine translation by AI. To understand what the original means, we recommend learning Korean and reading it in Korean."'),
        # 機械翻訳のお断り。節の題の上に毎回出す（2026-10-26、ユーザー「ポップアップとまではいかないけど明確に読まれるように」）。
        # 右上の×で消せて、消したことはその端末で覚える（同、「お断りの左上か右上に×で消えるやつほしい」）
        ('<div class="sechead">\n  <h1 id="secTitle">',
         '<div class="sechead">\n  <div class="notice" id="notice" role="note">\n'
         '    <button class="notice-x" id="noticeX" type="button"><svg viewBox="0 0 10 10" width="11" height="11" aria-hidden="true">'
         '<path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>\n'
         '    <b id="noticeSum"></b>\n    <div id="noticeBody"></div>\n  </div>\n  <h1 id="secTitle">'),
        ('  // ---- 画面の言葉を貼り替える ----\n  function applyUI() {',
         '  if (store.get("noticeHidden", false)) $("#notice").hidden = true;\n'
         '  $("#noticeX").addEventListener("click", () => { $("#notice").hidden = true; store.set("noticeHidden", true); });\n\n'
         + COPY_JS +
         '  // ---- 画面の言葉を貼り替える ----\n  function applyUI() {'),
        ('    $("#hint").textContent = touch() ? t.hintTouch : t.hint;\n  }',
         '    $("#hint").textContent = touch() ? t.hintTouch : t.hint;\n'
         '    $("#noticeSum").textContent = t.noticeSum;\n    $("#noticeBody").textContent = t.notice;\n'
         '    $("#noticeX").title = t.noticeX;\n    $("#noticeX").setAttribute("aria-label", t.noticeX);\n  }'),
        ('rows: "3 rows", cols: "3 columns", layoutT: "3 columns (side by side) / 3 rows (stacked)"',
         'rows: "2 rows", cols: "2 columns", layoutT: "2 columns (side by side) / 2 rows (stacked)"'),
    ]
    s = src
    for a, b in reps:
        if a not in s:
            raise SystemExit(f"ビューアの書き換えが当たらない: {a[:60]}")
        s = s.replace(a, b)
    # 出典の説明（言語ごと）
    foot = {
        "ja": ("`原文: <a href=\"" + BOARD + "\" target=\"_blank\" rel=\"noopener\">Daum カフェ「천일국 경전방」の原理原本の掲示板</a>"
               "（原稿の写し。〔数字〕は原稿のページ）。日本語訳: AI による訳です。韓国語の原文から訳し、掲示板にある 김현주 さんの訳を参考にしました。"
               "公式の訳ではありません。原稿のページの切れ目で途中になった文は、つないで1つの段落にしています。`"),
        "ko": ("`원문: <a href=\"" + BOARD + "\" target=\"_blank\" rel=\"noopener\">Daum 카페 「천일국 경전방」 원리원본 게시판</a>"
               "(원고 필사. 〔숫자〕는 원고의 쪽). 일본어 번역: AI 번역입니다. 한국어 원문에서 옮기고, 게시판의 김현주 님 번역을 참고했습니다. "
               "공식 번역이 아닙니다.`"),
        "en": ("`Korean text: <a href=\"" + BOARD + "\" target=\"_blank\" rel=\"noopener\">the Wolli Wonbon board of the Daum cafe 천일국 경전방</a>"
               " (a transcription of the manuscript; 〔n〕 marks a manuscript page). Japanese: an AI translation from the Korean, "
               "made with reference to the Japanese translation by 김현주 on the same board. Not an official translation.`"),
    }
    for lang, text in foot.items():
        m = re.search(r"(\n    " + lang + r": \{.*?\n      foot: \(links\) => )`.*?`(?:\n        \+ `.*?`)?,", s, re.S)
        if not m:
            raise SystemExit(f"foot が見つからない: {lang}")
        s = s[:m.start()] + m.group(1) + text + "," + s[m.end():]
    # 原稿のページの印・訳の断り
    css = ("  .pg{font-size:.72em;color:var(--muted);margin:0 .15em;white-space:nowrap;font-variant-numeric:tabular-nums;\n"
           "    user-select:none;-webkit-user-select:none}\n"
           "  .note{display:block;margin-top:.4em;font-size:.82em;color:var(--muted);user-select:none;-webkit-user-select:none}\n"
           "  .notice{position:relative;margin:0 0 16px;padding:9px 14px 11px;border:1px solid var(--markline);\n"
           "    border-radius:10px;background:var(--mark);font-size:14px;line-height:1.8}\n"
           "  .notice[hidden]{display:none}\n"
           "  .notice b{display:block;margin-bottom:2px;padding-right:30px}\n"
           "  .notice-x{position:absolute;top:6px;right:6px;width:32px;height:32px;padding:0;border:none;border-radius:50%;\n"
           "    background:transparent;color:var(--muted);display:grid;place-items:center}\n"
           "  .notice-x:hover{color:var(--ink);background:color-mix(in srgb,var(--markline) 28%,transparent)}\n")
    s = s.replace("</style>", css + "</style>", 1)
    return s


def main():
    units = json.loads((HERE / "units.json").read_text(encoding="utf-8"))
    secs = sections(units)
    OUT.mkdir(exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)
    for old in (OUT / "data").glob("*.js"):
        old.unlink()
    book = {"book": {"ko": "원리원본", "ja": "原理原本", "en": "Wolli Wonbon"}, "sections": [],
            "v": datetime.now().strftime("%Y%m%d%H%M%S")}
    last_page = 0
    for i, sec in enumerate(secs, 1):
        key = str(i)
        p1 = sec["units"][0]["parts"][0][0]
        ko_cells, ja_cells, n, last_page = build_rows(sec, last_page)
        p2 = last_page
        ja_t, ko_t = sec["title"]
        cont = "（続き）" if sec["cont"] else ""
        kcont = " (계속)" if sec["cont"] else ""
        # 節を選ぶ欄は「label　names」と並べて出す。label は巻と原稿のページ、names が題
        label_ja = f"{sec['vol']}巻〔{p1}〜{p2}〕"
        book["sections"].append({
            "key": key, "label": label_ja,
            "labels": {"ja": label_ja, "ko": f"{sec['vol']}권〔{p1}〜{p2}〕", "en": f"Vol. {sec['vol']}〔{p1}–{p2}〕"},
            "titles": {"ja": f"原理原本 {sec['vol']}巻 {ja_t}{cont}", "ko": f"원리원본 {sec['vol']}권 {ko_t}{kcont}"},
            "names": {"ja": ja_t + cont, "ko": ko_t + kcont}, "header": {}, "urls": {}, "n": n, "src": "wonbon",
        })
        payload = {"cells": {"ko": ko_cells, "ja": ja_cells}, "miss": []}
        (OUT / "data" / f"{key}.js").write_text(
            f"window.DP.put({json.dumps(key)}, {json.dumps(payload, ensure_ascii=False)});\n", encoding="utf-8", newline="\n")
    (OUT / "book.js").write_text("window.DPBOOK = " + json.dumps(book, ensure_ascii=False) + ";\n", encoding="utf-8", newline="\n")
    page = patch_viewer(SRC.read_text(encoding="utf-8"))
    (OUT / "index.html").write_text(page, encoding="utf-8", newline="\n")
    # 画面の言葉が韓国語・英語のときに配るリンクの入口（LINE などのプレビューは JS を動かさず head だけ読む）
    for lang, title, desc, loc in (
            ("ko", "원리원본 한일 대역", "『원리원본』의 한국어 원문과 일본어 번역(AI 번역)을 문단별로 나란히 읽는 대역입니다.", "ko_KR"),
            ("en", "Wolli Wonbon — Korean-Japanese Parallel",
             "The Korean text of the Wolli Wonbon side by side with a Japanese AI translation, paragraph by paragraph.", "en_US")):
        (OUT / f"{lang}.html").write_text(ENTRY.format(lang=lang, title=title, desc=desc, loc=loc, site=SITE),
                                          encoding="utf-8", newline="\n")
    print("節", len(secs), "段落", len(units), "→", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()

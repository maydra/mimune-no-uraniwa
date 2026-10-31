"""図を本文のどの文のあとに出すかを決め、charts.json の "after"（目印の字の並び）に書く。

python -I -X utf8 _tools/dpcharts/anchors.py <OCR の突き合わせ map_zen.json> [--page 11sozo]

- map_zen.json は extract/map_paragraphs.py の出力（スライドの説明文と、いちばん近い段落）
- 図は、その図を映していた最後のスライドの説明文が終わる文のあとに出す（ユーザー「刻んで配置して欲しい
  『ロマ書で～記録している』→スライド１、『～対象として展開されたものである』→スライド２」、2026-10-30）。
  説明文の最後の一文を、段落とその後ろ2段落の文と3字の組で突き合わせ、いちばん重なる文の終わりを取る
- 説明文の無い図（字だけの図など）は、前の図のすぐあとに出す
- 目印は、その文の終わりで終わる字の並びのうち、ページの本文に1回しか出てこない最も短いもの（8字以上）。
  空白は数えない。ページで探すときの決まりは dp/charts.js の pageText() と同じにする
"""
import argparse, json, os, re, sys
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKIP = ("rt, rp, script, style, nav, .toc-collapsible, #toc, .page-nav, #typo-report, "
        "#stacked-header-container, .color-filter-container, .dpc-fig, .dpc-note, #reader-ui, #reader-drawer")
WS = re.compile(r"\s+")
# 突き合わせのときだけ使う正規化（句読点・記号を落とし、漢数字を算用数字に。OCR は「〇」を読み落とす）
DROP = re.compile(r"[\s　●○◎〇・■□◆◇▼▲▶►※「」『』（）()〔〕、。，．,.:：;；!！?？\-－―—…‥＝=～〜]")
KANJI_NUM = str.maketrans("一二三四五六七八九", "123456789")
CLOSE = "」』）)"


def page_text(page):
    soup = BeautifulSoup(open(os.path.join(ROOT, "dp", page + ".html"), encoding="utf-8").read(), "html.parser")
    for t in soup.select(SKIP):
        t.decompose()
    return WS.sub("", soup.body.get_text(""))


def norm(t):
    return DROP.sub("", t).translate(KANJI_NUM)


def grams(t, n=3):
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def sentence_spans(text):
    """「。」（と、すぐ後ろの閉じ括弧）までを1文とする。(始め, 終わりの次) の並び。
    引用（「」『』）の中の「。」では切らない（堕落論の「…どこにいるか。彼らを…」で、図が引用の途中に入った）"""
    spans, s, i, depth = [], 0, 0, 0
    while i < len(text):
        ch = text[i]
        if ch in "「『":
            depth += 1
        elif ch in "」』":
            depth = max(0, depth - 1)
        elif ch == "。" and depth == 0:
            j = i + 1
            while j < len(text) and text[j] in CLOSE:
                j += 1
            spans.append((s, j))
            s = i = j
            continue
        i += 1
    if s < len(text):
        spans.append((s, len(text)))
    return spans


def paragraph_spans(paras, text):
    """段落ごとの、本文の中での (始め, 終わり)。見つからない段落は前の段落の終わりに置く"""
    out, pos = [], 0
    for p in paras:
        t = WS.sub("", p["text"])
        i = text.find(t, pos)
        if i < 0:
            out.append((pos, pos))
            continue
        out.append((i, i + len(t)))
        pos = i + len(t)
    return out


def ocr_sentences(ocr):
    parts = [p for p in re.split(r"(?<=。)", ocr) if len(norm(p)) >= 8]
    return parts


def ending(ns, n):
    """言い終わりの n 字。本文は「…するようになるのである」と結び、講義は「のである」を落とすので除いてから取る"""
    for suf in ("のであった", "のである"):
        if ns.endswith(suf) and len(ns) > len(suf) + n:
            ns = ns[:-len(suf)]
            break
    return ns[-n:]


def find_end(ocr, para_i, pspans, sspans, text):
    """説明文の最後の一文にいちばん近い本文の文の終わり。(位置, 一致度)
    講義の一文が本文では2文に分かれていることがある（「…作用体をつくるのだが、これが人間の心である」と
    本文の「…作用体をつくる。これが正に人間の心である。」、「…仲保となられるのである（ヨハネ3:16）」と
    本文の「…仲保となられると同時に、…命でもあるのである。…永遠の命を得るのである（ヨハネ三・16）。」）。
    図は後ろの文のあとに置きたい。そこで、一文全体がいちばん重なる文を選び、そのすぐ次の文の終わり（10字）が
    説明文の言い終わり（8字）とほぼそのまま重なるとき（3字の組の8割以上）だけ、次の文の終わりにする。
    言い終わりだけで選ぶと、「…存在している」「…できるようになる」のようなよくある結びに引っぱられる
    （191枚目の「…感ずることができるようになる」が、次の文の「…感じて分かるようになる」に引っぱられた）。
    最後の一文がどの文ともあまり重ならないとき（ルビの読みを OCR が拾った字の並びなど）は、一つ前の文で探す"""
    lo = pspans[para_i][0]
    hi = pspans[min(para_i + 2, len(pspans) - 1)][1]
    cands = [sp for sp in sspans if sp[1] > lo and sp[0] < hi]
    for q in reversed(ocr_sentences(ocr)[-3:]):
        nq = norm(q)
        qg, tg = grams(nq), grams(ending(nq, 8))
        if len(qg) < 4 or not tg:
            continue
        scored = []
        for s, e in cands:
            ns = norm(text[s:e])
            # (終わりの位置, 一文全体の重なり, 言い終わりの重なり)
            scored.append((e, len(qg & grams(ns)) / len(qg), len(tg & grams(ending(ns, 10))) / len(tg)))
        if not scored:
            break
        i = max(range(len(scored)), key=lambda k: scored[k][1])
        e, full, end_sc = scored[i]
        if full < 0.3:
            continue
        if i + 1 < len(scored) and scored[i + 1][2] >= 0.8 and scored[i + 1][2] > end_sc:
            return scored[i + 1][0], full
        return e, full
    return None, 0.0


def snippet_ending_at(end, text):
    for n in range(8, 80):
        s = text[max(0, end - n):end]
        if text.count(s) == 1:
            return s
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("--page", default="11sozo")
    ap.add_argument("--min", type=float, default=0.45)
    a = ap.parse_args()
    reg_path = os.path.join(HERE, "charts.json")
    reg = json.load(open(reg_path, encoding="utf-8"))
    m = json.load(open(a.map, encoding="utf-8"))
    paras = m["pages"][a.page]
    by_slide = {s["slide"]: s for s in m["slides"]}
    text = page_text(a.page)
    pspans = paragraph_spans(paras, text)
    sspans = sentence_spans(text)
    prev_end = None
    problems = 0
    for c in reg["charts"]:
        if c["page"] != a.page:
            continue
        c.pop("at", None)
        c.pop("para", None)
        # 手で決めた置き場所（"fixed": true）は計算し直さない。目印がページに1回だけあるかだけ確かめる
        if c.get("fixed"):
            if text.count(c.get("after", "")) != 1:
                print("手で決めた目印がページに1回だけではない:", c["id"]); problems += 1
                continue
            end = text.index(c["after"]) + len(c["after"])
            if prev_end is not None and end < prev_end:
                print(f"  順番が前に戻る: {c['id']}（手で決めた所）")
            prev_end = end
            continue
        # その図を映していた最後のスライドで、説明文が本文と結びつくもの
        hit = None
        for sl in reversed(c["slides"]):
            s = by_slide.get(sl)
            ms = [x for x in (s["match"] if s else []) if x["page"] == a.page and x["score"] >= a.min]
            if ms:
                hit = (s, ms[0])
                break
        if hit is None:
            if prev_end is None:
                print("置く所が決まらない:", c["id"]); problems += 1
                continue
            end, how = prev_end, "説明文が無いので前の図のあと"
        else:
            s, mt = hit
            end, sc = find_end(s["ocr"], mt["para"], pspans, sspans, text)
            if end is None:
                print("文が見つからない:", c["id"]); problems += 1
                continue
            how = f"{s['slide']}枚目の最後の文 一致 {sc:.2f}"
            if sc < 0.6:
                print(f"  一致が低い: {c['id']}（{how}）…{text[end - 30:end]}")
        if prev_end is not None and end < prev_end:
            print(f"  順番が前に戻る: {c['id']}（{how}）")
        snip = snippet_ending_at(end, text)
        if not snip:
            print("目印が作れない:", c["id"]); problems += 1
            continue
        c["after"] = snip
        c["how"] = how
        prev_end = end
    json.dump(reg, open(reg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(1 for c in reg["charts"] if c["page"] == a.page and c.get("after"))
    print(f"{a.page}: {n} 枚の置き場所を決めた。問題 {problems}")


if __name__ == "__main__":
    main()

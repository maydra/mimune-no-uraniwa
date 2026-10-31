"""スライドの説明文（OCR）を、サイトの原理講論の段落と突き合わせる。
python -I -X utf8 map_paragraphs.py <work> <site> <zen|kou> <out.json>

段落 = ページの本文を <br> とブロック要素の切れ目で分けた1行（ルビの読みは除く）。
一致の度合い = スライドの文の3文字の組のうち、その段落にも出てくるものの割合。
"""
import json, os, re, sys
from bs4 import BeautifulSoup

PAGES = {
    "zen": ["10sojo", "11sozo", "12daraku", "13shuma", "14meshia", "15fukka", "16yotei", "17kirisu"],
    "kou": ["20sho", "21kidai", "22mose", "23kaku", "24douji", "25saiko", "26sairi"],
}
BLOCK = {"div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li", "ul", "ol", "table", "tr", "blockquote"}
DROP = re.compile(r"[\s　●○◎・■□◆◇▼▲▶►※「」『』（）()〔〕、。，．,.:：;；!！?？\-－―—…‥・＝=～〜]")
KANJI_NUM = str.maketrans("〇一二三四五六七八九", "0123456789")


def norm(t):
    return DROP.sub("", t).translate(KANJI_NUM)


def grams(t, n=3):
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def page_paragraphs(path):
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    for tag in soup.find_all(["rt", "rp", "script", "style", "nav"]):
        tag.decompose()
    for tag in soup.select(".toc-collapsible, #toc, .page-nav, #typo-report, .typo-box"):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(BLOCK):
        tag.insert_before("\n")
        tag.insert_after("\n")
    heading = ""
    paras = []
    # 見出しは id で覚えておく（どの節の段落かを出すため）
    heads = {h.get_text("", strip=True): h.get("id") for h in soup.find_all(re.compile(r"^h[1-4]$")) if h.get("id")}
    for tag in soup.select("#stacked-header-container, .page-title, footer, .footer, .color-filter-container"):
        tag.decompose()
    # 閉じタグの崩れで本文の後半が .container の外に出るページがある（12daraku・13shuma など）ので body 全体から取る
    for line in soup.body.get_text("").split("\n"):
        s = line.strip().strip("　")
        if not s:
            continue
        if s in heads:
            heading = heads[s] + " " + s
            continue
        if len(norm(s)) < 4:
            continue
        paras.append({"i": len(paras), "head": heading, "text": s, "norm": norm(s)})
    return paras


def main(work, site, part, out):
    rows = json.load(open(os.path.join(work, "slides", f"{part}_map.json"), encoding="utf-8"))
    ocr = json.load(open(os.path.join(work, "ocr", f"texts_{part}.json"), encoding="utf-8"))
    pages = {p: page_paragraphs(os.path.join(site, "dp", p + ".html")) for p in PAGES[part]}
    for p, ps in pages.items():
        for q in ps:
            q["g"] = grams(q["norm"])
    result = []
    for r in rows:
        lines = []
        for m in r["text"]:
            lines += ocr.get(os.path.splitext(m)[0], [])
        text = "".join(lines)
        g = grams(norm(text))
        best = []
        if len(g) >= 4:
            for p, ps in pages.items():
                for q in ps:
                    hit = len(g & q["g"])
                    if hit:
                        best.append((hit / len(g), p, q["i"]))
            best.sort(reverse=True)
        top = best[:3]
        result.append({
            "slide": r["slide"], "chart": r["chart"], "ocr": text,
            "match": [{"score": round(s, 3), "page": p, "para": i,
                       "head": pages[p][i]["head"], "text": pages[p][i]["text"][:60]} for s, p, i in top],
        })
    json.dump({"pages": {p: [{k: v for k, v in q.items() if k != "g"} for q in ps] for p, ps in pages.items()},
               "slides": result}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for x in result if x["match"] and x["match"][0]["score"] >= 0.5)
    print(part, "slides", len(result), "matched>=0.5", ok)


if __name__ == "__main__":
    main(*sys.argv[1:5])

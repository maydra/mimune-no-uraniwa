"""章ごとに、元の画像と描き直した SVG を OCR にかける準備をし、終わったら字の差を出す。
python -I -X utf8 ocr_check.py prep <page>   … ocrcheck/<page>/orig と svg に2倍の PNG を作る
python -I -X utf8 ocr_check.py diff <page>   … OCR の結果（orig.json・svg.json）を比べ、元にだけある字を出す
"""
import json, os, re, sys, collections
from concurrent.futures import ThreadPoolExecutor

SITE = "E:/mimune-no-uraniwa/mimune-no-uraniwa"
W = "E:/mimune-no-uraniwa/dpcharts-work"
sys.path.insert(0, SITE + "/_tools/dpcharts")


def charts(page):
    reg = json.load(open(SITE + "/_tools/dpcharts/charts.json", encoding="utf-8"))
    return [c for c in reg["charts"] if c["page"] == page]


def prep(page):
    from PIL import Image
    from render import render
    out = f"{W}/ocrcheck/{page}"
    os.makedirs(out + "/orig", exist_ok=True)
    os.makedirs(out + "/svg", exist_ok=True)

    def job(c):
        raw = f"{out}/svg/{c['id']}_raw.png"
        render(f"{SITE}/_tools/dpcharts/svg/{c['id']}.svg", raw)
        for src, dst in ((raw, f"{out}/svg/{c['id']}.png"), (f"{W}/charts/{c.get('part', 'zen')}/{c['image']}.png", f"{out}/orig/{c['id']}.png")):
            im = Image.open(src).convert("RGB")
            k = 2 if im.width < 2000 else 1
            im.resize((im.width * k, im.height * k), Image.LANCZOS).save(dst)
        os.remove(raw)

    cs = charts(page)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(job, cs))
    print(page, len(cs))


def diff(page):
    out = f"{W}/ocrcheck/{page}"
    O = json.load(open(out + "/orig.json", encoding="utf-8"))
    R = json.load(open(out + "/svg.json", encoding="utf-8"))
    cjk = lambda s: collections.Counter(ch for ch in s if 0x3040 <= ord(ch) <= 0x30FF or 0x4E00 <= ord(ch) <= 0x9FFF)
    for c in charts(page):
        i = c["id"]
        svg = open(f"{SITE}/_tools/dpcharts/svg/{i}.svg", encoding="utf-8").read()
        T = cjk("".join(re.findall(r">([^<>]+)<", re.sub(r"<title>.*?</title>", "", svg, flags=re.S))))
        o, r = cjk("".join(O.get(i, []))), cjk("".join(R.get(i, [])))
        missing = "".join(ch for ch in o if ch not in T and ch not in r)
        if missing:
            print(i, "元にだけ:", missing)


if __name__ == "__main__":
    {"prep": prep, "diff": diff}[sys.argv[1]](sys.argv[2])

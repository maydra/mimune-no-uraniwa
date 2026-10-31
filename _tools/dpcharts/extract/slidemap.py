"""pptx の各スライドから、上の図の画像・下の文の画像・その上に描いた図形の数を拾う。"""
import json, re, sys, zipfile, collections

EMU = 12700  # 1pt

def slide_pics(z, n):
    xml = z.read(f"ppt/slides/slide{n}.xml").decode("utf-8")
    rels = z.read(f"ppt/slides/_rels/slide{n}.xml.rels").decode("utf-8")
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./media/([^"]+)"', rels))
    rid.update({a: b for b, a in re.findall(r'Target="\.\./media/([^"]+)"[^>]*Id="(rId\d+)"', rels)})
    pics = []
    for m in re.finditer(r"<p:pic>.*?</p:pic>", xml, re.S):
        p = m.group(0)
        e = re.search(r'r:embed="(rId\d+)"', p)
        off = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/>', p)
        ext = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"/>', p)
        if not (e and off and ext):
            continue
        pics.append({
            "media": rid.get(e.group(1)),
            "x": int(off.group(1)) / EMU, "y": int(off.group(2)) / EMU,
            "w": int(ext.group(1)) / EMU, "h": int(ext.group(2)) / EMU,
        })
    nsp = len(re.findall(r"<p:sp>", xml)) + len(re.findall(r"<p:cxnSp>", xml))
    return pics, nsp

def main(pptx, out):
    z = zipfile.ZipFile(pptx)
    names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    count = len(names)
    rows = []
    for n in range(1, count + 1):
        pics, nsp = slide_pics(z, n)
        chart = [p for p in pics if p["y"] < 120 and p["w"] > 400 and p["h"] > 150]
        text = [p for p in pics if p["y"] >= 300 and p["w"] > 400]
        rows.append({
            "slide": n,
            "chart": chart[0]["media"] if chart else None,
            "text": [t["media"] for t in text],
            "pics": len(pics),
            "shapes": nsp,
        })
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    charts = [r["chart"] for r in rows if r["chart"]]
    runs = 0
    prev = None
    for r in rows:
        if r["chart"] and r["chart"] != prev:
            runs += 1
        prev = r["chart"]
    print(pptx)
    print(" slides", count, "with chart", len(charts), "unique chart images", len(set(charts)), "runs", runs)
    print(" unique text images", len({t for r in rows for t in r["text"]}))
    print(" slides without chart", [r["slide"] for r in rows if not r["chart"]][:60])
    print(" shapes-on-top histogram", dict(collections.Counter(min(r["shapes"], 10) for r in rows)))

main(sys.argv[1], sys.argv[2])

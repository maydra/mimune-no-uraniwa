"""描き直した図の SVG を確かめ、ページごとの dp/charts/<page>.json にまとめる。
ページの <script src="charts.js" data-charts="…"> も足す・直す（?v= は中身のハッシュ）。

python -I -X utf8 _tools/dpcharts/build_charts.py

- 図の一覧と、出す所の目印（その字の並びで終わる文のあと）は _tools/dpcharts/charts.json（目印は anchors.py が書く）
- SVG は _tools/dpcharts/svg/<id>.svg。決まりは STYLE.md。まだ無い図は飛ばす
"""
import hashlib, json, os, re, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from anchors import page_text  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"
BANNED = {"script", "image", "foreignObject", "style", "iframe", "video", "audio", "use"}


def check_svg(cid, src):
    """決まりに合わない所を並べて返す"""
    errs = []
    try:
        root = ET.fromstring(src)
    except ET.ParseError as e:
        return [f"XML として読めない: {e}"]
    if root.tag != SVG_NS + "svg":
        errs.append("ルートが svg でない")
    if not root.get("viewBox"):
        errs.append("viewBox が無い")
    if root.get("class") != "dpc-svg":
        errs.append('class="dpc-svg" が無い')
    if root.get("width") or root.get("height"):
        errs.append("width・height は書かない")
    if root.find(SVG_NS + "title") is None:
        errs.append("title が無い")
    ids = set()
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag in BANNED:
            errs.append(f"<{tag}> は使わない")
        i = el.get("id")
        if i:
            if not i.startswith(cid + "-"):
                errs.append(f'id="{i}" が「{cid}-」で始まらない')
            ids.add(i)
        cls = el.get("class")
        if cls and el is not root and cls != "paper":
            errs.append(f'class="{cls}" は使わない（paper だけ）')
        for k, v in el.attrib.items():
            if k.endswith("href") and not v.startswith("#"):
                errs.append(f"外への参照 {v}")
    for ref in re.findall(r'url\(#([^)]+)\)', src) + re.findall(r'href="#([^"]+)"', src):
        if ref not in ids:
            errs.append(f"#{ref} が定義されていない")
    return errs


def minify(src):
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    src = re.sub(r">[ \t\r\n]+<", "><", src)          # タグの間の空白だけ。全角の空白（字の中身）は残す
    src = re.sub(r"[ \t\r\n]+", " ", src)
    return src.strip()


def short_hash(b):
    return hashlib.sha1(b).hexdigest()[:10]


def measure(svgs):
    """図ごとに、描いてある物の範囲（getBBox）を Chrome で測る。{id: [x, y, w, h]}
    元の画像の余白を viewBox から外すため（スマホの幅で図が小さくならないように）"""
    import shutil, subprocess, tempfile
    from render import CHROME
    tmp = tempfile.mkdtemp(prefix="dpc-fit-")
    try:
        html = os.path.join(tmp, "fit.html")
        body = "".join(f'<div data-id="{i}">{s}</div>' for i, s in svgs.items())
        script = ("document.fonts.ready.then(function(){var o={};"
                  "document.querySelectorAll('div[data-id]').forEach(function(d){"
                  "var b=d.querySelector('svg').getBBox();o[d.dataset.id]=[b.x,b.y,b.width,b.height];});"
                  "document.getElementById('out').textContent=JSON.stringify(o);});")
        open(html, "w", encoding="utf-8").write(
            '<!doctype html><html><head><meta charset="utf-8"><style>svg{width:1303px;display:block}</style></head>'
            f'<body>{body}<pre id="out"></pre><script>{script}</script></body></html>')
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                            f"--user-data-dir={os.path.join(tmp, 'profile')}", "--virtual-time-budget=8000",
                            "--dump-dom", "file:///" + html.replace("\\", "/")],
                           capture_output=True, timeout=120)
        m = re.search(rb'<pre id="out">(.*?)</pre>', r.stdout, re.S)
        if not m or not m.group(1).strip():
            sys.exit("図の範囲を測れなかった")
        return json.loads(m.group(1).decode("utf-8"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fit_viewbox(src, box, pad=16):
    """viewBox を、描いてある物の範囲＋余白に詰める（元の viewBox からははみ出さない）"""
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', src)
    x0, y0, w0, h0 = map(float, m.groups())
    x, y, w, h = box
    nx, ny = max(x0, x - pad), max(y0, y - pad)
    nw = min(x0 + w0, x + w + pad) - nx
    nh = min(y0 + h0, y + h + pad) - ny
    vb = " ".join(str(int(round(v))) for v in (nx, ny, nw, nh))
    return src.replace(m.group(0), f'viewBox="{vb}"', 1)


def set_script_tag(page, js_hash, json_name, json_hash):
    path = os.path.join(ROOT, "dp", page + ".html")
    html = open(path, encoding="utf-8").read()
    tag = f'<script src="charts.js?v={js_hash}" data-charts="charts/{json_name}?v={json_hash}"></script>'
    if re.search(r'<script src="charts\.js[^"]*"[^>]*></script>', html):
        new = re.sub(r'<script src="charts\.js[^"]*"[^>]*></script>', tag, html, count=1)
    else:
        m = re.search(r'<script src="color_filter\.js[^"]*"></script>\n?', html)
        if not m:
            sys.exit(f"{page}.html に color_filter.js の script が無い")
        new = html[:m.end()] + tag + "\n" + html[m.end():]
    if new != html:
        open(path, "w", encoding="utf-8", newline="").write(new)
        return True
    return False


def main():
    reg = json.load(open(os.path.join(HERE, "charts.json"), encoding="utf-8"))
    js_hash = short_hash(open(os.path.join(ROOT, "dp", "charts.js"), "rb").read())
    pages = {}
    for c in reg["charts"]:
        pages.setdefault(c["page"], []).append(c)
    bad = 0
    for page, charts in pages.items():
        text = page_text(page)
        out, missing = [], []
        for c in charts:
            p = os.path.join(HERE, "svg", c["id"] + ".svg")
            if not os.path.exists(p):
                missing.append(c["id"])
                continue
            src = open(p, encoding="utf-8").read()
            errs = check_svg(c["id"], src)
            after = c.get("after")
            if not after:
                errs.append("目印（after）が無い。anchors.py を回す")
            elif text.count(after) != 1:
                errs.append(f"目印がページに {text.count(after)} 回ある: {after}")
            if errs:
                bad += 1
                print(f"  {c['id']}: " + " / ".join(errs))
                continue
            o = {"id": c["id"], "after": after, "svg": minify(src)}
            # ページでの大きさ（図の 1 単位が何 px か）。後編の元の画像は前編（幅 1303）より小さい（幅 822）ので、
            # 同じ割合のままだと後編の図だけ小さく出る。元の画像の幅で割り戻して、前編と同じ見た目の大きさにする
            if c.get("part") == "kou":
                o["u"] = round(0.55 * 1303 / 822, 4)
            out.append(o)
        if not out:
            print(f"{page}: 図がまだ無い")
            continue
        boxes = measure({o["id"]: o["svg"] for o in out})
        for o in out:
            o["svg"] = fit_viewbox(o["svg"], boxes[o["id"]])
        os.makedirs(os.path.join(ROOT, "dp", "charts"), exist_ok=True)
        data = json.dumps({"v": 1, "charts": out}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        name = page + ".json"
        open(os.path.join(ROOT, "dp", "charts", name), "wb").write(data)
        changed = set_script_tag(page, js_hash, name, short_hash(data))
        print(f"{page}: {len(out)} 枚（{len(data):,} バイト）"
              + (f"、まだ無い {len(missing)} 枚" if missing else "")
              + ("、script タグを直した" if changed else ""))
    if bad:
        sys.exit(f"決まりに合わない図が {bad} 枚")


if __name__ == "__main__":
    main()

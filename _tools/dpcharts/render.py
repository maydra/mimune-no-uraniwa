"""図の SVG をヘッドレス Chrome で PNG に描き、元の画像と並べた見比べ図を作る。

python -I -X utf8 _tools/dpcharts/render.py <svg> <out.png> [--ref <元の画像.png>] [--dark] [--scale 2]

--ref を付けると「描いた SVG・重ねた図」を縦に並べ、幅 1000 に縮める（--full で元の画像も上に足す）。
重ねた図は、元の画像にだけある線が赤、SVG にだけある線が水色、両方にある線が黒になる。
元の画像の外枠の四角は SVG では描かない（ページの枠が代わりをする）ので、赤く残ってよい。
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, time
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = next((p for p in (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
) if os.path.exists(p)), None)

# ページの CSS（dp/charts.js の injectStyles）と同じ色。暗い配色の見え方も確かめられるように
CSS = """
html,body{margin:0;padding:0;background:#fff;color:#111}
body.dark{background:#1f1d36;color:#e6e6ef}
svg{display:block}
body.dark .paper{fill:#2c2a48}
"""


def view_box(svg):
    m = re.search(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*"', svg)
    if not m:
        sys.exit("viewBox が無い")
    return float(m.group(3)), float(m.group(4))


def render(svg_path, out, dark=False, scale=1):
    svg = open(svg_path, encoding="utf-8").read()
    w, h = view_box(svg)
    W, H = int(round(w)), int(round(h))
    tmp = tempfile.mkdtemp(prefix="dpc-")
    try:
        html = os.path.join(tmp, "page.html")
        body = re.sub(r"<svg\b", f'<svg width="{W}" height="{H}"', svg, count=1)
        open(html, "w", encoding="utf-8").write(
            f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body class="{"dark" if dark else ""}">{body}</body></html>')
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               f"--user-data-dir={os.path.join(tmp, 'profile')}",
               f"--force-device-scale-factor={scale}", f"--window-size={W},{H}",
               f"--screenshot={out}", "file:///" + html.replace("\\", "/")]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        for _ in range(20):
            if os.path.exists(out):
                break
            time.sleep(0.2)
    finally:
        time.sleep(0.3)
        shutil.rmtree(tmp, ignore_errors=True)
    if not os.path.exists(out):
        sys.exit("描けなかった: " + svg_path)
    return out


def compare(ref_path, rendered, out, full=False, width=1000):
    """SVG と重ねた図を縦に並べる（--full なら元の画像も上に足す）。幅は width に縮める"""
    ref = Image.open(ref_path).convert("RGB")
    got = Image.open(rendered).convert("RGB").resize(ref.size, Image.LANCZOS)
    a = ImageOps.grayscale(ref)
    b = ImageOps.grayscale(got)
    over = Image.merge("RGB", (b, a, a))
    panels = [(got, "SVG"), (over, "重ねた図（赤=元だけ、水色=SVGだけ、黒=両方）")]
    if full:
        panels.insert(0, (ref, "元の画像"))
    k = min(1.0, width / ref.width)
    W, H = int(ref.width * k), int(ref.height * k)
    pad = 24
    sheet = Image.new("RGB", (W, (H + pad) * len(panels)), "#666")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 15)
    except Exception:
        font = ImageFont.load_default()
    for i, (im, label) in enumerate(panels):
        y = i * (H + pad)
        d.text((6, y + 3), label, fill="white", font=font)
        sheet.paste(im.resize((W, H), Image.LANCZOS), (0, y + pad))
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("out")
    ap.add_argument("--ref")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--scale", type=float, default=1)
    ap.add_argument("--full", action="store_true", help="見比べ図に元の画像も入れる")
    a = ap.parse_args()
    if a.ref:
        raw = a.out + ".raw.png"
        render(a.svg, raw, a.dark, 1)
        compare(a.ref, raw, a.out, a.full)
        os.remove(raw)
    else:
        render(a.svg, a.out, a.dark, a.scale)
    print(a.out)


if __name__ == "__main__":
    main()

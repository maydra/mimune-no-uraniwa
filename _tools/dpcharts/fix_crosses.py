"""描いた図の十字架を、新しい型（幅 100×高さ 180）に置き換え、元の画像の十字架の寸法に合わせる。

python -I -X utf8 _tools/dpcharts/fix_crosses.py [id ...]   … id を省くと charts.json の全部
元の画像は E:/mimune-no-uraniwa/dpcharts-work/charts/zen/<image>.png（リポジトリの外）

古い型（幅 110×高さ 160、縦横同じ倍率）は、元の十字架より幅が 40〜60px 広かった（2026-10-31）。
古い型の置き場所の真ん中にいちばん近い、元の画像の濃い茶のかたまりを十字架とみなし、その外形に合わせる。
"""
import json, os, re, sys
from collections import deque

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "E:/mimune-no-uraniwa/dpcharts-work"
OLD = "M42,0 H68 V34 H110 V58 H68 V160 H42 V58 H0 V34 H42 Z"
NEW = "M40,0 H60 V42 H100 V60 H60 V180 H40 V60 H0 V42 H40 Z"
GROUP = re.compile(r'<g\b([^>]*?)transform="translate\(([-\d.]+)[ ,]+([-\d.]+)\)\s*scale\(([-\d.]+)(?:[ ,]+([-\d.]+))?\)"([^>]*)>(\s*)<path d="'
                   + re.escape(OLD) + r'"\s*/>(\s*)</g>')


def brown_blobs(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mask = (r < 150) & (r > 55) & (g < 105) & (g > 25) & (b < 75) & (r - b > 30)
    H, W = mask.shape
    seen = np.zeros_like(mask)
    out = []
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; xs = []; ys = []
                while q:
                    cy, cx = q.popleft(); xs.append(cx); ys.append(cy)
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if len(xs) > 600:
                    out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def fix(cid, image, part="zen"):
    p = os.path.join(HERE, "svg", cid + ".svg")
    src = open(p, encoding="utf-8").read()
    if OLD not in src:
        return 0
    blobs = brown_blobs(os.path.join(WORK, "charts", part, image + ".png"))
    n = 0

    def repl(m):
        nonlocal n
        pre, x, y, sx, sy, post, sp1, sp2 = m.groups()
        x, y, sx = float(x), float(y), float(sx)
        sy = float(sy) if sy else sx
        cx, cy = x + 55 * sx, y + 80 * sy
        # 元の十字架の外形は、黒い縁（約 3px）のぶん茶のかたまりより少し大きい
        best = min(blobs, key=lambda b: ((b[0] + b[2]) / 2 - cx) ** 2 + ((b[1] + b[3]) / 2 - cy) ** 2, default=None)
        if best is None or abs((best[0] + best[2]) / 2 - cx) > 80 or abs((best[1] + best[3]) / 2 - cy) > 80:
            print(f"  {cid}: 元の十字架が見つからない（{cx:.0f},{cy:.0f}）。古い寸法のまま形だけ替える")
            w, h, x0, y0 = 110 * sx * 0.82, 160 * sy * 1.1, cx - 55 * sx * 0.82, y
        else:
            x0, y0, x1, y1 = best[0] - 2, best[1] - 2, best[2] + 2, best[3] + 2
            w, h = x1 - x0, y1 - y0
        nsx, nsy = w / 100, h / 180
        sw = 3 / ((nsx + nsy) / 2)
        post = re.sub(r'\s*stroke-width="[^"]*"', "", post)
        pre = re.sub(r'\s*stroke-width="[^"]*"', "", pre)
        n += 1
        return (f'<g{pre}transform="translate({x0:.1f},{y0:.1f}) scale({nsx:.4f},{nsy:.4f})" stroke-width="{sw:.3f}"{post}>'
                f'{sp1}<path d="{NEW}"/>{sp2}</g>')

    out = GROUP.sub(repl, src)
    if OLD in out:
        print(f"  {cid}: 置き換えられない十字架が残った（書き方が型と違う）")
    if out != src:
        open(p, "w", encoding="utf-8", newline="\n").write(out)
    return n


def main():
    reg = json.load(open(os.path.join(HERE, "charts.json"), encoding="utf-8"))
    want = set(sys.argv[1:])
    total = 0
    for c in reg["charts"]:
        if want and c["id"] not in want:
            continue
        p = os.path.join(HERE, "svg", c["id"] + ".svg")
        if os.path.exists(p):
            k = fix(c["id"], c["image"], c.get("part", "zen"))
            if k:
                print(c["id"], k)
                total += k
    print("十字架", total)


if __name__ == "__main__":
    main()

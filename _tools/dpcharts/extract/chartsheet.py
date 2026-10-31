"""図の画像だけを一覧にする（スライド番号と画像名つき）。
python -I -X utf8 chartsheet.py <work> <zen|kou> <first_slide> <last_slide> <out_prefix>"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

work, part, first, last, prefix = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
rows = json.load(open(os.path.join(work, "slides", f"{part}_map.json"), encoding="utf-8"))
seq = []  # (最初のスライド, 最後のスライド, 画像)
for r in rows:
    if first <= r["slide"] <= last and r["chart"]:
        if seq and seq[-1][2] == r["chart"]:
            seq[-1][1] = r["slide"]
        else:
            seq.append([r["slide"], r["slide"], r["chart"]])
cols, per, tw, th = 4, 20, 420, 236
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
from PIL import ImageChops, ImageStat
def _th(m):
    return Image.open(os.path.join(work, "charts", part, os.path.splitext(m)[0] + ".png")).convert("L").resize((160, 85))
near = set()
for i in range(1, len(seq)):
    if ImageStat.Stat(ImageChops.difference(_th(seq[i - 1][2]), _th(seq[i][2]))).mean[0] < 6:
        near.add(i)
for k in range(0, len(seq), per):
    chunk = seq[k:k + per]
    rows_n = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows_n * th), "#888")
    d = ImageDraw.Draw(sheet)
    for i, (a, b, m) in enumerate(chunk):
        gi = k + i
        im = Image.open(os.path.join(work, "charts", part, os.path.splitext(m)[0] + ".png"))
        im.thumbnail((tw - 8, th - 30))
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (x + 4, y + 26))
        label = f"{a}" + (f"-{b}" if b != a else "") + f"  {os.path.splitext(m)[0]}" + ("  ≈前" if gi in near else "")
        d.rectangle([x + 4, y + 2, x + tw - 4, y + 24], fill="black")
        d.text((x + 8, y + 3), label, fill="yellow", font=font)
    out = f"{prefix}_{k // per + 1:02d}.png"
    sheet.save(out)
    print(out, len(chunk))
json.dump(seq, open(prefix + "_seq.json", "w"), indent=0)

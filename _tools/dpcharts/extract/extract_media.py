"""pptx の図と説明文の画像を RGB の PNG にして取り出す。説明文は OCR 用に2倍にする。
python -I extract_media.py <work> <zen|kou>"""
import json, sys, zipfile, io, os
from PIL import Image

work, part = sys.argv[1], sys.argv[2]
rows = json.load(open(os.path.join(work, "slides", f"{part}_map.json"), encoding="utf-8"))
z = zipfile.ZipFile(os.path.join(work, "pptx", f"{part}.pptx"))
charts, texts = set(), set()
for r in rows:
    if r["chart"]:
        charts.add(r["chart"])
    texts.update(r["text"])
for names, sub, scale in ((charts, "charts", 1), (texts, "texts", 2)):
    for m in sorted(names):
        out = os.path.join(work, sub, part, os.path.splitext(m)[0] + ".png")
        if os.path.exists(out):
            continue
        im = Image.open(io.BytesIO(z.read("ppt/media/" + m))).convert("RGB")
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
        im.save(out)
    print(part, sub, len(names))

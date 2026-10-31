"""図の字に使うフォント（BIZ UDPゴシック）を、図に出てくる字だけに絞って dp/fonts/ に書く。

python -X utf8 _tools/dpcharts/build_font.py [--src <フォントのフォルダ>]（fonttools を pip --user で入れたので -I は付けない）

- 図は Windows に入っている BIZ UDPゴシックで寸法を合わせて描いた。iPhone・Android・Mac には無く、
  ヒラギノなどで代わりに描くと、かなの幅と縦の位置が違って字が箱からはみ出す（2026-10-31、ユーザーのスマホのスクショ）。
  そこで、自由に配ってよい版（SIL OFL、Google Fonts の ofl/bizudpgothic）を図の字だけに絞ってサイトに置く
- 元のフォント（BIZUDPGothic-Regular.ttf・BIZUDPGothic-Bold.ttf・OFL.txt）はリポジトリに入れない。
  https://github.com/google/fonts/tree/main/ofl/bizudpgothic から取る。既定の置き場所は dpcharts-work/fontsrc
- 太字（700）は図の全部の字、細字（400）は font-weight="400" の所に出てくる字だけ
- 図を足したり字を直したりしたら、これを回してから build_charts.py（JSON にフォントのハッシュが入る）
- 要るもの: pip install fonttools brotli
"""
import argparse, html, os, re, shutil, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "dp", "fonts")
SVG_NS = "{http://www.w3.org/2000/svg}"
FILES = {"700": "BIZUDPGothic-Bold.ttf", "400": "BIZUDPGothic-Regular.ttf"}


def weight_of(v):
    if v in (None, ""):
        return None
    if v == "bold":
        return "700"
    if v == "normal":
        return "400"
    return "700" if int(v) >= 600 else "400"


def collect():
    """{"700": 字の集合, "400": 字の集合}。title と注釈は数えない"""
    chars = {"700": set(), "400": set()}

    def walk(el, w):
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("title", "desc"):
            return
        w = weight_of(el.get("font-weight")) or w
        if tag in ("text", "tspan") and el.text:
            chars[w].update(c for c in html.unescape(el.text) if not c.isspace())
        for ch in el:
            walk(ch, w)
            ctag = ch.tag.replace(SVG_NS, "")
            if ch.tail and tag in ("text", "tspan") and ctag in ("tspan",):
                chars[w].update(c for c in html.unescape(ch.tail) if not c.isspace())

    for name in sorted(os.listdir(os.path.join(HERE, "svg"))):
        if name.endswith(".svg"):
            root = ET.parse(os.path.join(HERE, "svg", name)).getroot()
            walk(root, weight_of(root.get("font-weight")) or "400")
    return chars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(os.path.dirname(ROOT), "dpcharts-work", "fontsrc"))
    a = ap.parse_args()
    from fontTools import subset
    from fontTools.ttLib import TTFont

    chars = collect()
    os.makedirs(OUT, exist_ok=True)
    for w, fname in FILES.items():
        src = os.path.join(a.src, fname)
        if not os.path.exists(src):
            sys.exit(f"{src} が無い（{__doc__.splitlines()[0]}）")
        text = "".join(sorted(chars[w]))
        cmap = TTFont(src, lazy=True).getBestCmap()
        missing = [c for c in text if ord(c) not in cmap]
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.hinting = False
        opts.desubroutinize = True
        opts.name_IDs = [0, 1, 2, 3, 4, 5, 6]   # 著作権とライセンスの名前は残す
        opts.notdef_outline = True
        font = subset.load_font(src, opts)
        s = subset.Subsetter(opts)
        s.populate(text=text)
        s.subset(font)
        out = os.path.join(OUT, f"dpc-gothic-{w}.woff2")
        subset.save_font(font, out, opts)
        print(f"{w}: {len(text)} 字 → {os.path.getsize(out):,} バイト"
              + (f"、フォントに無い字 {''.join(missing)}" if missing else ""))
    shutil.copyfile(os.path.join(a.src, "OFL.txt"), os.path.join(OUT, "OFL.txt"))


if __name__ == "__main__":
    main()

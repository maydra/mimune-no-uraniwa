"""日本の聖歌の歌詞（公式の訳詞）を、静岡家庭教会のページのアーカイブから取り出す → ja_official.json

    python -I -X utf8 _tools/seika/parse_ja_official.py <song_p01.html> <song_p02.html>

元のページ（今は閉じている。Internet Archive に残っている）:
  第一部 1〜70番 http://www.u-ch.org/contents_song/song_p01.html （2020-02-19 の保存）
  第二部 2〜9番  http://www.u-ch.org/contents_song/song_p02.html （2020-02-11 の保存）
番号は日本の聖歌の番号（videos.tsv の ja_no と同じ。第二部は「2部2」）。
"""

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "1": "https://web.archive.org/web/20200219211424/http://www.u-ch.org/contents_song/song_p01.html",
    "2": "https://web.archive.org/web/20200211153532/http://www.u-ch.org/contents_song/song_p02.html",
}
SONG = re.compile(r'<h3><a name="L(\d+)"[^>]*></a>\s*(\d+)\.(.+?)</h3>\s*<p class="line">(.*?)</p>', re.S)


def parse(path, part):
    text = Path(path).read_text(encoding="utf-8")
    out = {}
    for m in SONG.finditer(text):
        no, title, body = m.group(2), html.unescape(m.group(3)).strip(), m.group(4)
        key = no if part == "1" else f"2部{no}"
        ab = re.search(r"（([ＡＢ])）$", title)  # 13番は（Ａ）（Ｂ）の2つの版がある
        if ab:
            key += "(" + "AB"["ＡＢ".index(ab.group(1))] + ")"
        lines = [html.unescape(re.sub(r"<[^>]+>", "", ln)).strip() for ln in re.split(r"<br\s*/?>", body)]
        credit, verses, cur = "", [], None
        for ln in lines:
            if not ln:
                continue
            if ln.startswith("作詞") or ln.startswith("作曲"):
                credit = ln
                continue
            if re.fullmatch(r"\d+\.?", ln):  # 節の番号だけの行（第二部は「.」が無い）
                cur = []
                verses.append(cur)
                continue
            mm = re.match(r"^(\d+)\.\s*(.+)$", ln)  # 「1.善き闘いを…」のように番号と同じ行
            if mm and (cur is None or len(cur) > 0):
                cur = [mm.group(2)]
                verses.append(cur)
                continue
            if cur is None:
                cur = []
                verses.append(cur)
            cur.append(ln)
        # 題に付いた読み「我は供物（くもつ）」は題としては外す
        out[key] = {"title": title, "credit": credit, "verses": verses, "source": SOURCES[part] + f"#L{m.group(1)}"}
    return out


def main(p01, p02):
    data = {**parse(p01, "1"), **parse(p02, "2")}
    dest = HERE / "ja_official.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(data), "songs ->", dest.name)
    for k, v in data.items():
        print(k, v["title"], [len(x) for x in v["verses"]])


if __name__ == "__main__":
    main(*sys.argv[1:3])

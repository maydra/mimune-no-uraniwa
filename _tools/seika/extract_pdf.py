"""聖歌集の PDF から、曲ごとのハングルの歌詞を取り出して歌のファイルの下書きを作る

    python -I -X utf8 _tools/seika/extract_pdf.py "<Holy Songbook_full.pdf>"

songs/NNN.txt が既にある曲は書き換えない（手で直したものを守る）。
PDF の作り: 1曲は「ページ番号」「N. 題」「1. 1節目…」と並び、折り返しは「*」の行から
空行まで。同じページの下にロシア語の解説が続くことがあるので、キリル文字の行で切る。
コード（G D7 Em…）だけの行は捨てる。
"""

import csv
import difflib
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
SONGS = HERE / "songs"
CYR = re.compile(r"[Ѐ-ӿ]")
HANGUL = re.compile(r"[가-힣]")
CHORD = re.compile(r"^[A-G](#|b)?(m|maj|dim|aug|sus)?\d*(/[A-G](#|b)?)?$")
VERSE = re.compile(r"^(\d+[ab]?)\.\s*(.*)$")
POPULAR = {"48", "55", "56", "57"}  # 流行歌。全文は載せず、紹介のページを手で作る


def is_chord_line(line):
    toks = line.split()
    return bool(toks) and all(CHORD.match(t) for t in toks)


def korean_lines(page_text):
    """ページのうち、ハングルの歌詞の部分の行（ページ番号とコードの行を除く）"""
    out = []
    for raw in re.sub(r"[\x00-\x08\x0b-\x1f]", "", page_text).splitlines():
        line = raw.strip()
        if CYR.search(line):
            break
        if re.fullmatch(r"\d+", line) or is_chord_line(line):
            continue
        out.append(line)
    return out


def parse_song(lines):
    verses = []  # [{"no": "1", "lines": [...]}]
    refrain = None
    cur = None
    in_refrain = False
    for line in lines:
        if not line:
            in_refrain = False
            continue
        m = VERSE.match(line)
        if m:
            cur = {"no": m.group(1), "lines": []}
            verses.append(cur)
            in_refrain = False
            if m.group(2):
                cur["lines"].append(m.group(2).strip())
            continue
        if line.startswith("*"):
            refrain = {"no": "*", "lines": [line.lstrip("* ").strip()], "after": len(verses)}
            in_refrain = True
            continue
        if in_refrain:
            refrain["lines"].append(line)
            continue
        if cur is None:  # 節の番号の無い曲（32 응답하소서）
            cur = {"no": "1", "lines": []}
            verses.append(cur)
        cur["lines"].append(line)
    return verses, refrain


def write_draft(no, title, page, ja_title, verses, refrain):
    out = [f"no: {no}", f"ko: {title}", f"ja: {ja_title}", f"page: {page}", ""]
    for i, v in enumerate(verses, 1):
        out.append(f"[{v['no']}]")
        out.extend(v["lines"])
        # 折り返しは最初に出てきた節の後ろに1回だけ書き、あとの節には (*) を付ける
        if refrain and i == refrain["after"]:
            out += ["", "[*]"] + refrain["lines"]
        elif refrain and i > refrain["after"]:
            out.append("(*)")
        out.append("")
    (SONGS / f"{int(no):03d}.txt").write_text("\n".join(out), encoding="utf-8", newline="\n")


def find_starts(doc, toc):
    """曲の始まりのページを、ページの頭の「N. 題」で見つける。
    目次のページ番号はずれていることがある（4 영광의 은사 は目次で19、実際は16）"""
    titles = {s["no"]: re.sub(r"\s+", "", s["ko"]) for s in toc}
    starts = {}
    for p in range(1, doc.page_count + 1):
        kl = [x for x in korean_lines(doc[p - 1].get_text()) if x]
        if not kl:
            continue
        m = VERSE.match(kl[0])
        if m and m.group(1) in titles:
            head = re.sub(r"\s+", "", m.group(2))
            want = titles[m.group(1)]
            # 題の誤植（북귀의 동산）があるので、ほぼ同じなら同じ曲とみなす
            if difflib.SequenceMatcher(None, head, want).ratio() >= 0.75:
                starts.setdefault(m.group(1), p)
    return starts


def main(pdf):
    doc = pymupdf.open(pdf)
    toc = list(csv.DictReader(open(HERE / "songs_index.tsv", encoding="utf-8"), delimiter="\t"))
    videos = {r["no"]: r for r in csv.DictReader(open(HERE / "videos.tsv", encoding="utf-8"), delimiter="\t")}
    starts = find_starts(doc, toc)
    order = sorted(starts.items(), key=lambda kv: kv[1])
    for i, (no, page) in enumerate(order):
        end = order[i + 1][1] if i + 1 < len(order) else page + 1
        s = next(x for x in toc if x["no"] == no)
        dest = SONGS / f"{int(no):03d}.txt"
        if no in POPULAR or dest.exists():
            continue
        lines = []
        for p in range(page, end):
            kl = korean_lines(doc[p - 1].get_text())
            if p == page:
                kl = kl[1:]  # 題の行
            elif not any(HANGUL.search(x) for x in kl[:2]):
                continue  # ロシア語だけのページ
            lines += kl + [""]
        verses, refrain = parse_song(lines)
        write_draft(no, s["ko"], page, videos.get(no, {}).get("ja_title", ""), verses, refrain)
        print(no, s["ko"], [f"{v['no']}:{len(v['lines'])}" for v in verses], "refrain", len(refrain["lines"]) if refrain else 0)


if __name__ == "__main__":
    main(sys.argv[1])

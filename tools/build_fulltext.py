# -*- coding: utf-8 -*-
"""サイト内検索の本文をまとめて data/fulltext/ に書き出す。

検索は「打った文字列をそのまま探す」方式（ブラウザの Ctrl+F と同じ）。
そのためにサイトの本文を全部ブラウザに持っていく。18,663,329字・gzip で
約15MB。1回落として Cache API に置けば、次からは通信なしで動く。

分かち書きの索引（pagefind）を使わないので、「み旨」のように語の切れ目と
合わない言葉でも取りこぼさない。抜粋も手元にあるので、結果の表示に通信は
一切いらない。

書き出す形（1シャード = 1ファイル）:
    1行目  {"docs":[[URL, タイトル, 文字数], ...]}
    2行目以降  本文を "\n" でつないだもの（順番は docs と同じ）
本文から改行は抜いてあるので、"\n" は必ずページの切れ目になる。

目次ページ（data-pagefind-ignore が付いているもの）は入れない。何を探しても
目次が先に出てしまうため。付ける役目は tools/mark_search_ignore.py。

使い方:
    python tools/mark_search_ignore.py
    python tools/build_fulltext.py
"""
import hashlib
import json
import os
import pathlib
import re
import sys
import unicodedata
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "fulltext"

SKIP_DIRS = {".git", "pagefind", "node_modules", "__pycache__", "theme",
             "data", "tools", "Bible_out_backup", "out"}

# 読み物ではないページ。検索ページ自身が結果に出ると邪魔になる。
SKIP_NAMES = {"search-all.html", "gacha.html", "random.html",
              "test_output.html", "404.html"}
SKIP_NAME_RE = re.compile(r"^google[0-9a-f]{16}\.html$", re.IGNORECASE)

# これより短い本文は中身が無い（「ランダムページに移動中...」など）
MIN_CHARS = 60

# 本文ではない部分
SKIP_TAGS = {"script", "style", "noscript", "iframe", "nav", "header",
             "footer", "aside", "select", "template"}
SKIP_CLASSES = {"toc", "sidebar", "typo-box", "nav-link", "breadcrumb"}

# 何個のファイルに分けるか。1個あたり 800KB ほど。
#
# どのファイルに入れるかは URL のハッシュで決める。文字数で順に詰めると、
# 前の方のページを1行直しただけで以降のページがずれて全ファイルが変わり、
# git の履歴が毎回15MB増えてしまう。ハッシュなら直したページの入った
# 1ファイルだけが変わり、読者も落とし直すのはその1個で済む。
SHARD_COUNT = 24

# ページとページの区切り。本文から改行は抜いてあるので、探している文字列が
# ページをまたいで当たることはない。
SEP = chr(10)

WS = re.compile(r"\s+")


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.title = ""
        self.in_title = False
        self.skip_depth = 0
        self.skip_tag = None
        self.ignored = False   # ページごと検索から外す
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
            return
        if "data-pagefind-ignore" in a and tag == "body":
            self.ignored = True

        self.depth += 1
        if self.skip_depth:
            return
        cls = set((a.get("class") or "").split())
        if (tag in SKIP_TAGS or "data-pagefind-ignore" in a
                or cls & SKIP_CLASSES):
            self.skip_depth = self.depth
            self.skip_tag = tag

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
            return
        if self.skip_depth and self.depth <= self.skip_depth and tag == self.skip_tag:
            self.skip_depth = 0
            self.skip_tag = None
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skip_depth:
            self.parts.append(data)

    # <br> などの単独タグで語がつながらないように
    def handle_startendtag(self, tag, attrs):
        self.parts.append(" ")


def clean(text):
    # 全角英数などを揃える（NFKC）。ゼロ幅文字は消す。改行は空白に。
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("​", "").replace("﻿", "")
    return WS.sub(" ", text).strip()


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(filenames):
            if not name.lower().endswith((".html", ".htm")):
                continue
            if name.lower() in SKIP_NAMES or SKIP_NAME_RE.match(name):
                continue
            yield pathlib.Path(dirpath) / name


def main():
    docs = []
    skipped = 0
    skipped_thin = 0

    for path in walk(ROOT):
        try:
            html = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        p = Extract()
        try:
            p.feed(html)
        except Exception:
            continue
        if p.ignored:
            skipped += 1
            continue

        text = clean("".join(p.parts))
        if len(text) < MIN_CHARS:
            skipped_thin += 1
            continue

        url = path.relative_to(ROOT).as_posix()
        docs.append((url, clean(p.title) or url, text))

    docs.sort(key=lambda d: d[0])

    # シャードに分ける
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("ft-*.txt"):
        old.unlink()

    buckets = [[] for _ in range(SHARD_COUNT)]
    for doc in docs:
        h = hashlib.sha1(doc[0].encode("utf-8")).hexdigest()
        buckets[int(h[:8], 16) % SHARD_COUNT].append(doc)

    shards = []
    for i, batch in enumerate(buckets):
        header = json.dumps(
            {"docs": [[u, t, len(c)] for u, t, c in batch]},
            ensure_ascii=False, separators=(",", ":"))
        body = SEP.join(c for _, _, c in batch)
        data = (header + SEP + body).encode("utf-8")
        name = f"ft-{i:02d}.txt"
        (OUT_DIR / name).write_bytes(data)
        shards.append({
            "file": name,
            "hash": hashlib.sha1(data).hexdigest()[:10],
            "pages": len(batch),
            "chars": sum(len(c) for _, _, c in batch),
            "bytes": len(data),
        })

    total_chars = sum(len(c) for _, _, c in docs)
    manifest = {
        "pages": len(docs),
        "chars": total_chars,
        "shards": shards,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    total_bytes = sum(s["bytes"] for s in shards)
    print(f"{len(docs)} ページ / {total_chars:,} 字 / "
          f"{len(shards)} シャード / {total_bytes/1024/1024:.1f} MB")
    print(f"  目次として外したページ: {skipped}")
    print(f"  中身が無くて外したページ: {skipped_thin}")


if __name__ == "__main__":
    main()

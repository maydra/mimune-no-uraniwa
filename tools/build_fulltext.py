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

**シャードは書籍（一番上のフォルダ）ごとに分ける。**
「この書籍の中で検索」を1冊ぶんの読み込みだけで済ませるため。
以前は URL のハッシュで24個に散らしていたが、それだと1冊を探すにも
全ファイルが要る。書籍ごとなら git の差分も小さくなる（dp を直しても
変わるのは ft-dp.txt だけ）。大きい書籍は SHARD_MAX_BYTES で分割する。

目次ページ（data-pagefind-ignore が付いているもの）は入れない。何を探しても
目次が先に出てしまうため。付ける役目は tools/mark_search_ignore.py。

使い方:
    python tools/mark_search_ignore.py
    python tools/build_fulltext.py
"""
import hashlib
import html as html_mod
import json
import os
import pathlib
import re
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

# 1ファイルの上限。超える書籍は ft-<書籍>-00.txt のように分ける。
# 全文検索は全部を並べて落とすので、1個が大きすぎると進み具合が飛び飛びに
# なるし、途中で失敗したときの落とし直しも重くなる。
SHARD_MAX_BYTES = 1_200_000

# サイトのトップに置いてあるページ（index.html など）をまとめる先
ROOT_BOOK = "_root"

# ページとページの区切り。本文から改行は抜いてあるので、探している文字列が
# ページをまたいで当たることはない。
SEP = chr(10)

WS = re.compile(r"\s+")

# トップページの書籍一覧から、フォルダ名 → 表示名を拾う
BOOK_LINK_RE = re.compile(
    r'href="(?:https://maydra\.github\.io/mimune-no-uraniwa/)?'
    r'([A-Za-z0-9_.&;-]+)/(?:index|mokuji)\.html"[^>]*>\s*([^<]+?)\s*<')

# ファイル名に使えない文字を落とす（syuku_&_risoutengoku など）
UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


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


def page_title(path):
    """そのページの <title> を、後ろの飾り（| み旨の裏庭 など）を落として返す。"""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if not m:
        return ""
    title = clean(html_mod.unescape(m.group(1)))
    title = re.split(r"\s*(?:[|｜]|//)\s*", title)[0].strip()
    # 「聖書 - 目次」の後ろ半分は書籍名ではない
    return re.sub(r"\s*[-‐−–—]\s*(?:目次|もくじ|index)\s*$", "", title,
                  flags=re.IGNORECASE).strip()


def book_titles():
    """フォルダ名 → 表示名。トップページの一覧が本命、無ければ各書籍の <title>。"""
    titles = {}
    try:
        top = (ROOT / "index.html").read_text(encoding="utf-8")
    except OSError:
        top = ""
    for slug, title in BOOK_LINK_RE.findall(top):
        slug = html_mod.unescape(slug)
        titles.setdefault(slug, clean(html_mod.unescape(title)))

    for d in sorted(ROOT.iterdir()):
        if not d.is_dir() or d.name in SKIP_DIRS or d.name.startswith("."):
            continue
        if titles.get(d.name):
            continue
        for entry in ("index.html", "mokuji.html"):
            if (d / entry).exists():
                t = page_title(d / entry)
                if t:
                    titles[d.name] = t
                    break
    return titles


def shard_names(book, count):
    """1冊ぶんのファイル名。分けないときは番号を付けない。"""
    safe = UNSAFE.sub("_", book)
    if count == 1:
        return [f"ft-{safe}.txt"]
    return [f"ft-{safe}-{i:02d}.txt" for i in range(count)]


def split_book(docs):
    """SHARD_MAX_BYTES を超えないように、ページ単位で山分けする。"""
    groups = [[]]
    size = 0
    for doc in docs:
        # 本文は日本語なので UTF-8 では1字およそ3バイト
        n = len(doc[2]) * 3
        if groups[-1] and size + n > SHARD_MAX_BYTES:
            groups.append([])
            size = 0
        groups[-1].append(doc)
        size += n
    return groups


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

    # 書籍（一番上のフォルダ）ごとにまとめる
    by_book = {}
    for doc in docs:
        parts = doc[0].split("/")
        book = parts[0] if len(parts) > 1 else ROOT_BOOK
        by_book.setdefault(book, []).append(doc)

    titles = book_titles()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("ft-*.txt"):
        old.unlink()

    used = {}
    shards = []
    books = []

    for book in sorted(by_book):
        batch = by_book[book]
        groups = split_book(batch)
        names = shard_names(book, len(groups))

        # ファイル名は記号を潰しているので、別の書籍とぶつからないか見ておく
        for name in names:
            if name in used:
                raise SystemExit(
                    f"シャード名がぶつかった: {name} ({used[name]} と {book})")
            used[name] = book

        files = []
        for name, group in zip(names, groups):
            header = json.dumps(
                {"docs": [[u, t, len(c)] for u, t, c in group]},
                ensure_ascii=False, separators=(",", ":"))
            body = SEP.join(c for _, _, c in group)
            data = (header + SEP + body).encode("utf-8")
            (OUT_DIR / name).write_bytes(data)
            files.append(name)
            shards.append({
                "file": name,
                "book": book,
                "hash": hashlib.sha1(data).hexdigest()[:10],
                "pages": len(group),
                "chars": sum(len(c) for _, _, c in group),
                "bytes": len(data),
            })

        books.append({
            "id": book,
            "title": titles.get(book) or book,
            "pages": len(batch),
            "chars": sum(len(c) for _, _, c in batch),
            "files": files,
        })

    total_chars = sum(len(c) for _, _, c in docs)
    manifest = {
        "pages": len(docs),
        "chars": total_chars,
        "books": books,
        "shards": shards,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    total_bytes = sum(s["bytes"] for s in shards)
    biggest = max(shards, key=lambda s: s["bytes"])
    print(f"{len(docs)} ページ / {total_chars:,} 字 / "
          f"{len(books)} 書籍 / {len(shards)} シャード / "
          f"{total_bytes/1024/1024:.1f} MB")
    print(f"  一番大きいファイル: {biggest['file']} "
          f"{biggest['bytes']/1024/1024:.1f} MB")
    print(f"  目次として外したページ: {skipped}")
    print(f"  中身が無くて外したページ: {skipped_thin}")
    no_title = [b["id"] for b in books if b["title"] == b["id"]]
    if no_title:
        print(f"  表示名が見つからなかった書籍: {', '.join(no_title)}")


if __name__ == "__main__":
    main()

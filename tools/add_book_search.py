# -*- coding: utf-8 -*-
"""各書籍の index.html に「この書籍の中で検索」ボタンを入れる。

飛び先は search-all.html?book=<フォルダ名>。本文は書籍ごとに分けてあるので
（tools/build_fulltext.py）、押しても読むのはその1冊ぶんだけで済む。

置き場所は最初の </h1> の直後。h1 が無いページは <body> の直後。
見た目は theme/style.css の .book-search-btn。theme/style.css を読んで
いない少数のページには、そのぶんだけ style を添える。

何度流しても増えない（すでに入っていれば URL だけ直す）。

使い方:
    python tools/build_fulltext.py
    python tools/add_book_search.py
"""
import json
import pathlib
import re
import sys
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "fulltext" / "manifest.json"

MARK = "book-search"

# theme/style.css を読んでいないページ用。同じ見た目を最低限だけ。
FALLBACK_STYLE = (
    '<style id="book-search-style">'
    '.book-search{margin:1.2rem 0 2rem}'
    '.book-search-btn{display:inline-flex;align-items:center;gap:.5em;'
    'padding:.7em 1.4em;border-radius:50px;font-size:1rem;font-weight:600;'
    'text-decoration:none;border:1px solid rgba(128,128,128,.35);'
    'background:rgba(128,128,128,.12);color:inherit}'
    '.book-search-btn::before{content:"\\1F50D";font-size:1.05em;line-height:1}'
    '</style>'
)

BODY_RE = re.compile(r"<body[^>]*>", re.IGNORECASE)
H1_END_RE = re.compile(r"</h1>", re.IGNORECASE)
EXISTING_RE = re.compile(
    r'\s*<div class="book-search">.*?</div>', re.IGNORECASE | re.DOTALL)


def button(slug):
    href = "../search-all.html?book=" + quote(slug, safe="")
    return ('<div class="book-search">'
            f'<a class="book-search-btn" href="{href}">この書籍の中で検索</a>'
            '</div>')


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    if not MANIFEST.exists():
        raise SystemExit("先に python tools/build_fulltext.py を流してください")
    books = json.loads(MANIFEST.read_text(encoding="utf-8"))["books"]

    added = updated = skipped = 0
    for book in books:
        slug = book["id"]
        path = ROOT / slug / "index.html"
        if not path.exists():
            # _root など、目次ページを持たないもの
            skipped += 1
            continue

        s = path.read_text(encoding="utf-8")
        html = button(slug)

        if MARK in s:
            # 入れ直し（URL が変わったときのため）
            new = EXISTING_RE.sub("\n" + html, s, count=1)
            if new != s:
                path.write_text(new, encoding="utf-8", newline="")
                updated += 1
            continue

        block = html
        if "theme/style.css" not in s:
            block = FALLBACK_STYLE + html

        m = H1_END_RE.search(s)
        if m:
            at = m.end()
        else:
            m = BODY_RE.search(s)
            if not m:
                print(f"  置き場所が見つからない: {slug}")
                skipped += 1
                continue
            at = m.end()

        path.write_text(s[:at] + "\n" + block + s[at:],
                        encoding="utf-8", newline="")
        added += 1

    print(f"追加 {added} / 入れ直し {updated} / 対象外 {skipped}")


if __name__ == "__main__":
    main()

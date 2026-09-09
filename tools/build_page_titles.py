# -*- coding: utf-8 -*-
"""検索結果を一気に出すための小さな対応表を作る。

pagefind は 1ページ = 1断片ファイルで持っていて、タイトルと URL を知るには
その断片を取りに行くしかない。1000件当たるクエリでは 1000 回・十数MB の通信に
なり、結果が出そろうまで10秒かかる。

断片の id（= ファイル名）から URL とタイトルだけを抜き出して
data/page-titles.json に置いておけば、検索結果は通信ゼロで全部並べられる。
本文の抜粋は、画面に入った項目だけ後から取りに行く。

pagefind の索引を作り直したら、これも作り直すこと:
    python tools/mark_search_ignore.py
    npx pagefind@1.3.0 --site .
    python tools/build_page_titles.py
"""
import gzip
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FRAGMENTS = ROOT / "pagefind" / "fragment"
OUT = ROOT / "data" / "page-titles.json"

# 断片は gzip の中身の頭に "pagefind_dcd" が付いた JSON
PREFIX = b"pagefind_dcd"


def main():
    pages = {}
    missing_title = 0

    for path in sorted(FRAGMENTS.glob("*.pf_fragment")):
        raw = gzip.decompress(path.read_bytes())
        if raw.startswith(PREFIX):
            raw = raw[len(PREFIX):]
        obj = json.loads(raw.decode("utf-8"))

        title = (obj.get("meta") or {}).get("title") or ""
        if not title:
            missing_title += 1
        # 先頭の / は付けない。ページ側で置き場所（/mimune-no-uraniwa/）を足す
        pages[path.stem] = [obj.get("url", "").lstrip("/"), title]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(pages, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    size = OUT.stat().st_size
    print(f"{len(pages)} pages -> {OUT.relative_to(ROOT)} ({size/1024:.0f}KB)")
    if missing_title:
        print(f"  title の無いページ: {missing_title}")


if __name__ == "__main__":
    main()

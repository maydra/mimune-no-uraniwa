# -*- coding: utf-8 -*-
"""data/offline-manifest.json を作り直す。

「この本をオフライン保存」(offline.js) が読む、書籍ごとの全ページ一覧。
pages.json はガチャ用に本文ページだけを選んだものなので使わない
(聖書・平和メッセージなどが丸ごと抜けている)。

ページを足したり消したりしたら、リポジトリの根からこれを回して commit:
    python _tools/root/build_offline_manifest.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'data' / 'offline-manifest.json'

SKIP_DIRS = {'_tools', 'data', 'theme', 'icons', 'music', '.git', 'Index', 'library'}

books = {}
for d in sorted(ROOT.iterdir()):
    if not d.is_dir() or d.name in SKIP_DIRS:
        continue
    idx = d / 'index.html'
    # 引っ越したあとの転送だけが残っているフォルダは、保存しても仕方がない
    if idx.exists() and 'location.replace(' in idx.read_text(encoding='utf-8', errors='ignore'):
        continue
    files = sorted(str(f.relative_to(ROOT)).replace('\\', '/')
                   for f in d.rglob('*.html'))
    if files:
        books[d.name] = files

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({'books': books}, ensure_ascii=False,
                          separators=(',', ':')), encoding='utf-8')
total = sum(len(v) for v in books.values())
print(f'{OUT.name}: {len(books)} books, {total} pages, '
      f'{OUT.stat().st_size:,} bytes')

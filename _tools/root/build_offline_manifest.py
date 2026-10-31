# -*- coding: utf-8 -*-
"""data/offline-manifest.json を作り直す。

「この本をオフライン保存」(offline.js) が読む、書籍ごとの全ページ一覧。
data/gacha.json はガチャ用に本文ページだけを選んだものなので使わない
(聖書・聖歌などが丸ごと抜けている)。

ページを足したり消したりしたら、リポジトリの根からこれを回して commit:
    python _tools/root/build_offline_manifest.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'data' / 'offline-manifest.json'

SKIP_DIRS = {'_tools', 'data', 'theme', 'icons', 'music', '.git', 'Index', 'library',
             'download'}  # download/ は build_downloads.py が書き出す1ファイル版

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
    # 原理講論の図（dp/charts.js と dp/charts/*.json）。図は「図」を ON にしたときだけ読むので、
    # 開いただけでは保存されない（2026-10-30）
    extra = [d / 'charts.js'] + sorted((d / 'charts').glob('*.json'))
    # 図の字のフォント（dp/fonts、2026-10-31）。BIZ UDPゴシックの無い端末で、オフラインでも図の字がずれないように
    extra += sorted((d / 'fonts').glob('*.woff2'))
    files += [str(f.relative_to(ROOT)).replace('\\', '/') for f in extra if f.exists()]
    if files:
        books[d.name] = files

# どの本のページからも読む共有ファイル（ページの <link> は本ごとに違うので、全部まとめて渡す）。
# ?v= は付けない。オフラインのときの SW は ?v= を無視して探す
shared = sorted(str(f.relative_to(ROOT)).replace('\\', '/')
                for f in (ROOT / 'theme' / 'pages').glob('*.css'))
shared += ['theme/reader.js', 'theme/gacha.js', 'data/gacha.json']  # 本ごとのランダム（random.html）が読む

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({'books': books, 'shared': shared}, ensure_ascii=False,
                          separators=(',', ':')), encoding='utf-8')
total = sum(len(v) for v in books.values())
print(f'{OUT.name}: {len(books)} books, {total} pages, '
      f'{OUT.stat().st_size:,} bytes')

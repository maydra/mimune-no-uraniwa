# -*- coding: utf-8 -*-
"""サイトマップ（sitemap-index.xml と書籍ごとの sitemap.xml）を作り直す。

以前は手書きで、本を足すたびに漏れていた（2026-10-26 に数えたら本文 1,400 ページ超が抜けていた）。
いまは GitHub Actions（.github/workflows/sitemap.yml）が push のたびにこれを回して
commit するので、ふだんは手で回さなくていい。手元で確かめたいときはリポジトリの根から:
    python _tools/root/build_sitemap.py

載せないもの:
- 転送ページ（meta refresh / location.replace）と noindex のページ
- 中身の無い仕組みのページ（random.html・offline.html・検索・Google の所有確認ファイル）
- Index/・library/（旧目次の転送）、download/（1ファイル版。noindex）

robots.txt の Sitemap: 行はサイトが maydra.github.io の下のフォルダにあるので Google に読まれない。
サイトマップは Search Console から sitemap-index.xml を送信して知らせる。
"""
import pathlib
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://maydra.github.io/mimune-no-uraniwa/'

SKIP_DIRS = {'_tools', 'data', 'theme', 'icons', 'music', '.git', '.github',
             'Index', 'library', 'download'}
SKIP_NAMES = {'random.html', 'offline.html', 'search-all.html', '404.html'}

REDIRECT = re.compile(r'http-equiv=["\']?refresh|location\.replace', re.I)
NOINDEX = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re.I)


def listable(path):
    if path.name in SKIP_NAMES or path.name.startswith('google'):
        return False
    # 聖書（Bible_out）は Shift_JIS。見たいのは ASCII のタグだけなので読み方は問わない
    head = path.read_bytes()[:4000].decode('ascii', 'ignore')
    return not (REDIRECT.search(head) or NOINDEX.search(head))


def url(path):
    return BASE + quote(path.relative_to(ROOT).as_posix(), safe='/')


def write(path, tag, child, locs):
    body = ''.join(f'<{child}><loc>{loc}</loc></{child}>\n' for loc in locs)
    text = (f"<?xml version='1.0' encoding='utf-8'?>\n"
            f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</{tag}>\n')
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old != text:
        path.write_text(text, encoding='utf-8', newline='\n')


maps = []
total = 0

# 根にあるページ（トップ・ガチャなど）は根の sitemap.xml へ
top = [url(p) for p in sorted(ROOT.glob('*.html')) if listable(p)]
write(ROOT / 'sitemap.xml', 'urlset', 'url', top)
maps.append(BASE + 'sitemap.xml')
total += len(top)

for d in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
    pages = [url(p) for p in sorted(d.rglob('*.html')) if listable(p)]
    if not pages:
        continue
    write(d / 'sitemap.xml', 'urlset', 'url', pages)
    maps.append(url(d / 'sitemap.xml'))
    total += len(pages)

write(ROOT / 'sitemap-index.xml', 'sitemapindex', 'sitemap', maps)
# 以前 Search Console に送った控え。中身は同じ XML にそろえておく
write(ROOT / 'sitemap-index.txt', 'sitemapindex', 'sitemap', maps)
print(f'{len(maps)} sitemaps, {total} pages')

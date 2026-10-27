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

<lastmod>（最終更新日）: Google は、日付が正確なサイトでは、これを見て見直しに来る順番を決める。
?v= の打ち直しのたびに全ページの日付が変わると当てにされなくなるので、title・description・本文の文字
だけを比べる。比べるための指紋と日付は sitemap-lastmod.json に置き、書き換えるのは Actions だけ
（--stamp）。手元で回したときは、記録してある日付をそのまま使う。
--changed FILE を付けると、日付が新しくなったページと消えたページの URL を FILE に書き出す
（indexnow.py が Bing などに知らせる）。
"""
import datetime
import hashlib
import html
import json
import pathlib
import re
import sys
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://maydra.github.io/mimune-no-uraniwa/'
LASTMOD = ROOT / '_tools' / 'root' / 'sitemap-lastmod.json'
# URL のパスにそのまま書いてよい記号は % にしない。Google は syuku_&_risoutengoku を & のまま登録していて、
# %26 にすると別の URL に数える（2026-10-27 に Search Console の API で確かめた）。空白は %20 にする
SAFE = "/!$&'()*+,;=:@~"
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()

SKIP_DIRS = {'_tools', 'data', 'theme', 'icons', 'music', '.git', '.github',
             'Index', 'library', 'download'}
SKIP_NAMES = {'random.html', 'offline.html', 'search-all.html', '404.html'}

REDIRECT = re.compile(r'http-equiv=["\']?refresh|location\.replace', re.I)
NOINDEX = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', re.I)
CANONICAL = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', re.I)


def listable(path):
    if path.name in SKIP_NAMES or path.name.startswith('google'):
        return False
    # 見たいのは ASCII のタグだけなので読み方は問わない
    head = path.read_bytes()[:6000].decode('ascii', 'ignore')
    if REDIRECT.search(head) or NOINDEX.search(head):
        return False
    # 「正はあっち」と canonical で指しているページ（父の祈りの framepage など、古い目次の写し）は載せない
    # 「jisho/」と「jisho/index.html」は同じページ
    canon = CANONICAL.search(head)
    return not canon or same(html.unescape(canon.group(1)), url(path))


def same(a, b):
    return re.sub(r'index\.html$', '', a) == re.sub(r'index\.html$', '', b)


def ordered(paths):
    # Windows の pathlib は大文字小文字を無視して並べるので、GitHub（Linux）とそろえて文字列で並べる
    return sorted(paths, key=lambda p: p.as_posix())


def url(path):
    # ホームは canonical（_tools/root/seo_titles.py）と同じく末尾の index.html なし
    if path == ROOT / 'index.html':
        return BASE
    return BASE + quote(path.relative_to(ROOT).as_posix(), safe=SAFE)


def fingerprint(path):
    """読む人に見える中身（title・description・本文の文字）の指紋。タグ・スクリプト・?v= は見ない。"""
    src = path.read_text(encoding='utf-8', errors='replace')
    desc = re.search(r'(?is)<meta[^>]+name=["\']description["\'][^>]*>', src)
    body = src[src.lower().find('<body'):]
    body = re.sub(r'(?is)<(script|style)\b.*?</\1>', '', body)
    words = [m.group(1) if (m := re.search(r'(?is)<title[^>]*>(.*?)</title>', src)) else '',
             desc.group(0) if desc else '', html.unescape(re.sub(r'<[^>]+>', ' ', body))]
    return hashlib.sha1(re.sub(r'\s+', ' ', '\n'.join(words)).encode('utf-8')).hexdigest()[:10]


def write(path, tag, child, entries):
    # XML の中なので & は &amp; と書く（URL は & のまま）
    body = ''.join(f'<{child}><loc>{html.escape(loc, quote=False)}</loc>'
                   + (f'<lastmod>{day}</lastmod>' if day else '') + f'</{child}>\n'
                   for loc, day in entries)
    text = (f"<?xml version='1.0' encoding='utf-8'?>\n"
            f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</{tag}>\n')
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old != text:
        path.write_text(text, encoding='utf-8', newline='\n')


args = sys.argv[1:]
stamp = '--stamp' in args
changed_out = args[args.index('--changed') + 1] if '--changed' in args else None
record = json.loads(LASTMOD.read_text(encoding='utf-8')) if LASTMOD.exists() else {}
seen = set()
changed = []


def entries(paths):
    out = []
    for p in paths:
        if not listable(p):
            continue
        rel = p.relative_to(ROOT).as_posix()
        seen.add(rel)
        if stamp:
            mark = fingerprint(p)
            if record.get(rel, [None])[0] != mark:
                record[rel] = [mark, TODAY]
                changed.append(url(p))
        out.append((url(p), record[rel][1] if rel in record else None))
    return out


maps = []
total = 0

# 根にあるページ（トップ・ガチャなど）は根の sitemap.xml へ
top = entries(ordered(ROOT.glob('*.html')))
write(ROOT / 'sitemap.xml', 'urlset', 'url', top)
maps.append((BASE + 'sitemap.xml', max((day for _, day in top if day), default=None)))
total += len(top)

for d in ordered(p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
    pages = entries(ordered(d.rglob('*.html')))
    if not pages:
        continue
    write(d / 'sitemap.xml', 'urlset', 'url', pages)
    # サイトマップ自体の日付は、中のページでいちばん新しい日
    maps.append((url(d / 'sitemap.xml'), max((day for _, day in pages if day), default=None)))
    total += len(pages)

write(ROOT / 'sitemap-index.xml', 'sitemapindex', 'sitemap', maps)
# 以前 Search Console に送った控え。中身は同じ XML にそろえておく
write(ROOT / 'sitemap-index.txt', 'sitemapindex', 'sitemap', maps)

if stamp:
    # 消えたページ・載せなくなったページも、なくなったと知らせる
    for rel in sorted(set(record) - seen):
        del record[rel]
        changed.append(url(ROOT / rel))
    # 1ページ1行（差分が読みやすいように）
    lines = ',\n'.join(f'{json.dumps(k, ensure_ascii=False)}: {json.dumps(record[k])}' for k in sorted(record))
    LASTMOD.write_text('{\n' + lines + '\n}\n', encoding='utf-8', newline='\n')
if changed_out:
    pathlib.Path(changed_out).write_text(''.join(u + '\n' for u in changed), encoding='utf-8')
print(f'{len(maps)} sitemaps, {total} pages' + (f', {len(changed)} changed' if stamp else ''))

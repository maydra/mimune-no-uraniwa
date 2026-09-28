# -*- coding: utf-8 -*-
"""1冊を1つのファイルにまとめて download/ に書き出す（HTML）。

「この本をオフライン保存」(sw.js) はブラウザの保存領域に頼るので、
iPhone では Safari とホーム画面のアイコンで保存先が別だったり、
しばらく開かないと消されたりして、機内で開けないことがある。
こちらは端末にファイルとして残るので、ファイルアプリから必ず開ける。

download/<book>.html は CSS も中に入った1ページ。目次・ルビ・蛍光ペンの色が残る。

ページの順番は、本の目次（index.html）に載っている順。
同じ本の中へのリンクはページ内リンクに直し、ほかの本へのリンクはサイトの URL にする。

リポジトリの根から:
    python _tools/root/build_downloads.py dp kitou   # 指定した本だけ
    python _tools/root/build_downloads.py            # 全部
"""
import hashlib
import json
import os
import pathlib
import re
import sys
from collections import Counter
from urllib.parse import quote, unquote, urljoin, urlparse

from html import escape

from bs4 import BeautifulSoup, Comment

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'download'
SITE = 'https://maydra.github.io/mimune-no-uraniwa/'

# 本文ではないページ
SKIP_PAGES = {'index.html', 'mokuji.html', 'random.html'}
# 本文から取り除くもの
DROP = [
    'script', 'style', 'link', 'iframe', 'form', 'input', 'button', 'textarea',
    'nav.page-nav', '#toc', '.toc', '.toc-collapsible', '.stacked-header-container',
    '.typo-box', '#typo-report', '.book-search', '.nav-links',
]
# 本の中を行き来するためのリンク（1ファイルでは要らない）
NAV_WORDS = re.compile(r'^(INDEXへ|目次|目次に戻る|目次へ|前へ|次へ|前のページに戻る|次のページに進む|[←→]\s*.*|.*\s*[←→])$')

CSS = """
:root { --bg:#fff; --fg:#111; --muted:#666; --line:#ddd; --link:#1a4f9c; --size:1.15rem; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#1b1b1f; --fg:#e8e6e3; --muted:#9a9a9a; --line:#3a3a40; --link:#8ab4f8; }
  /* 蛍光ペンは色を残したまま文字を読めるように */
  [style*="background"], [style*="background"] rt { color:#111; }
}
* { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--bg); color:var(--fg);
  font-family:'Noto Serif JP','Hiragino Mincho ProN','Yu Mincho',serif;
  font-size:var(--size); line-height:1.9; }
main { max-width:42rem; margin:0 auto; padding:1.5rem 1rem 6rem; }
a { color:var(--link); }
h1,h2,h3,h4 { line-height:1.5; }
.book-title { font-size:1.8rem; text-align:center; margin:1rem 0 .3rem; }
.book-note { text-align:center; color:var(--muted); font-size:.85rem; margin:0 0 2rem; }
.book-toc { border:1px solid var(--line); border-radius:8px; padding:.5rem 1rem; margin-bottom:3rem; }
.book-toc > summary { font-weight:bold; cursor:pointer; padding:.3rem 0; }
.book-toc ol { margin:.3rem 0; padding-left:1.2rem; }
.book-toc details summary { cursor:pointer; }
.book-toc ul { margin:.2rem 0 .5rem; padding-left:1.2rem; font-size:.9em; }
.chapter { border-top:1px solid var(--line); padding-top:2rem; margin-top:3rem; }
.chapter-title { font-size:1.5rem; }
.chapter-end { text-align:right; font-size:.85rem; margin-top:2rem; }
.no1 { text-indent:1em; margin:0 0 1em; }
rt { font-size:.5em; }
blockquote { margin:0; }
img { max-width:100%; height:auto; }
.tools { position:fixed; right:.7rem; bottom:.7rem; display:flex; gap:.4rem; }
.tools button, .tools a { font:inherit; font-size:.9rem; min-width:2.6rem; padding:.4rem .6rem;
  border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg);
  text-decoration:none; text-align:center; }
"""

JS = """
(function(){
  var k='mimune.dl.size', r=document.documentElement;
  function set(v){ v=Math.max(.8,Math.min(2,v)); r.style.setProperty('--size',v+'rem');
    try{localStorage.setItem(k,v)}catch(e){} }
  try{ var s=parseFloat(localStorage.getItem(k)); if(s) set(s); }catch(e){}
  document.getElementById('smaller').onclick=function(){ set(parseFloat(getComputedStyle(r).getPropertyValue('--size'))-.1) };
  document.getElementById('bigger').onclick=function(){ set(parseFloat(getComputedStyle(r).getPropertyValue('--size'))+.1) };
})();
"""


def read(path):
    return BeautifulSoup(path.read_text(encoding='utf-8', errors='ignore'), 'html.parser')


def slug(name):
    return re.sub(r'[^0-9A-Za-z_-]', '_', name.rsplit('.', 1)[0])


def rel(path):
    return path.relative_to(ROOT).as_posix()


def local_target(href, page, book_dir):
    """href が同じ本のページを指していれば (ファイル名, #の後) を返す。"""
    if not href or href.startswith(('mailto:', 'javascript:', 'tel:')):
        return None
    if href.startswith('#'):
        return page.name, unquote(href[1:])
    url = urljoin(SITE + quote(f'{rel(book_dir)}/{page.name}'), href)
    p = urlparse(url)
    if not url.startswith(SITE):
        return None
    path = unquote(p.path[len(urlparse(SITE).path):])
    target = ROOT / path
    if target.parent == book_dir and target.suffix == '.html':
        return target.name, unquote(p.fragment)
    return None


def absolute(href, page, book_dir):
    return urljoin(SITE + quote(f'{rel(book_dir)}/{page.name}'), href)


def moved(page):
    """引っ越したあとの転送だけが残っているページ"""
    head = page.read_text(encoding='utf-8', errors='ignore')[:4000]
    return 'location.replace(' in head or '移動しました' in head


def natural(name):
    """1.html, 2.html, …, 10.html の順に並べるためのキー"""
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', name)]


def reading_order(book_dir):
    """読む順番。本の目次（index.html）に載っている順が基本。

    各ページの「次へ」は途中で目次に戻ってしまう本が多いので、順番の
    よりどころにはしない。
    """
    pages = {p.name: p for p in book_dir.glob('*.html')
             if p.name not in SKIP_PAGES and not moved(p)}
    index = book_dir / 'index.html'
    linked = []
    if index.exists():
        for a in read(index).find_all('a', href=True):
            t = local_target(a['href'], index, book_dir)
            if t and t[0] in pages and t[0] not in linked:
                linked.append(t[0])

    # 中身がまったく同じページ（父の祈りの fp1_mokuji と framepage1 など）は1つにまとめ、
    # 目次に載っている方を残す。alias は元の名前 → 残した名前
    alias, first = {}, {}
    for n in linked + sorted((n for n in pages if n not in linked), key=natural):
        key = hashlib.sha1(text_of(read(pages[n]).body).encode('utf-8')).hexdigest()
        alias[n] = first.setdefault(key, n)
    pages = {n: p for n, p in pages.items() if alias[n] == n}
    order = []
    for n in linked:
        if alias[n] not in order:
            order.append(alias[n])

    # 目次に載っていないページは、そこへリンクしているページのすぐ後ろに差し込む。
    # 目次に載っているページ（父の祈りの各編の目次など）からはどのリンクでも、
    # 差し込んだページからは「次へ」だけをたどる（本文中の参照で先の章を
    # 引っぱってこないように）
    listed = set(order)
    i = 0
    while i < len(order):
        page = pages[order[i]]
        found = []
        for a in read(page).find_all('a', href=True):
            label = a.get_text()
            if '前' in label or (order[i] not in listed and ('次' not in label or '目次' in label)):
                continue
            t = local_target(a['href'], page, book_dir)
            n = alias.get(t[0]) if t else None
            if n and n not in order and n not in found:
                found.append(n)
        order[i + 1:i + 1] = found
        i += 1
    # それでも決まらないページは最後に名前順で足す（落とさない）
    order += [n for n in sorted(pages, key=natural) if n not in order]
    return [pages[n] for n in order], alias


def text_of(el):
    return re.sub(r'[\s　]+', ' ', el.get_text(' ', strip=True)).strip() if el else ''


def chapter_titles(soups, book_title):
    """各ページの章の名前。

    <title> と最初の h1 のうち、ページごとに違いのある方を元にする（統一思想要綱は
    h1 が全ページ本の名前で、<title> に章名がある）。全ページに共通する頭と尻
    （「訓教経/(上)」「 - 統一思想要綱」）を削り、「/」で区切った各部分と、
    ページ内の目次・見出しを候補にする。候補のうち、半分より多くのページに出てくる
    もの（「み旨の道」「文鮮明先生のみ言集」など）と、番号だけのものは使わない。
    """
    by_title = [text_of(s.title) for s in soups]
    by_h1 = [text_of(s.find('h1')) for s in soups]
    raw = by_title if len(set(by_title)) > len(set(by_h1)) else by_h1
    raw = [r or t for r, t in zip(raw, by_title)]
    trimmed = raw
    if len(raw) >= 3:
        # 語の途中で切らないよう、区切り（空白・/・-）のところまで戻す
        pre = re.sub(r'[^\s/／\-|｜]*$', '', os.path.commonprefix(raw))
        suf = re.sub(r'^[^\s/／\-|｜]*', '', os.path.commonprefix([r[::-1] for r in raw])[::-1])
        trimmed = [r[len(pre):len(r) - len(suf)] for r in raw]

    def clean(t):
        t = t.replace('◆', '').strip()
        t = re.sub(r'^' + re.escape(book_title) + r'[\s:：]*', '', t)
        return t.strip(' _-')

    cands = []
    for soup, t in zip(soups, trimmed):
        c = re.split(r'\s*(?:[/／|｜]| - )\s*', t)
        c += [text_of(a) for a in soup.select('#toc a[href^="#"], .toc a[href^="#"]')]
        c += [text_of(h) for h in soup.find_all(['h2', 'h3', 'h4'])]
        c = [clean(x) for x in c]
        cands.append([x for x in c if x and not re.fullmatch(r'[\d０-９]+', x)
                      and x not in ('目次', book_title, '誤植・修正提案')])
    common = set()
    if len(soups) >= 3:
        count = Counter(x for c in cands for x in set(c))
        common = {x for x, n in count.items() if n > len(soups) / 2}
    out = []
    for c, r in zip(cands, raw):
        good = [x for x in c if x not in common]
        out.append(good[0] if good else (c[0] if c else clean(r) or r))
    # 同じ名前が並ぶページ（生涯路程11の「第二節 …」が3ページ続くなど）は、
    # ページの中で最初に出てくる、その名前以外の見出しで区別する
    count = Counter(out)
    # 見出しタグが無いページ（父の祈り）は、太字の1行目を見出し代わりにする
    heads = [[clean(text_of(h)) for h in s.find_all(['h2', 'h3', 'h4'])]
             + [clean(text_of(b)) for b in s.find_all(['b', 'strong'])[:1]] for s in soups]
    seen_in = Counter(h for hs in heads for h in set(hs))
    for i, hs in enumerate(heads):
        if count[out[i]] > 1:
            # ほかのページには出てこない見出しだけを使う
            hs = [h for h in hs if h and seen_in[h] == 1 and h != out[i] and h != book_title]
            if hs:
                out[i] = hs[0]
    return out


def link_names(index):
    """目次のページで、フォルダ → リンクの文字（＝本の名前）"""
    names = {}
    for a in read(index).find_all('a', href=True):
        t = unquote(urlparse(urljoin(SITE + quote(rel(index)), a['href'])).path)
        name = a.get_text(' ', strip=True)
        if name and t.startswith(urlparse(SITE).path):
            folder = t[len(urlparse(SITE).path):].rsplit('/', 1)[0]
            names.setdefault(folder, name)
    return names


def build(book_dir, out, title):
    """book_dir の全ページを download/<out>.html にまとめる"""
    pages, alias = reading_order(book_dir)
    if not pages:
        print(f'{out}: ページが無い')
        return
    book = rel(book_dir)
    soups = [read(p) for p in pages]
    known = set(alias)
    titles = chapter_titles(soups, title)

    toc_items, chapters = [], []
    for page, soup, ptitle in zip(pages, soups, titles):
        heads = {text_of(soup.title), text_of(soup.find('h1')), title}
        sid = slug(page.name)
        # ページ内の目次（あれば）を小見出しとして使う
        subs = []
        for a in soup.select('#toc a[href^="#"], .toc a[href^="#"]'):
            subs.append((f'{sid}--{a["href"][1:]}', a.get_text(' ', strip=True)))

        body = soup.body
        for sel in DROP:
            for el in body.select(sel):
                el.decompose()
        for a in body.find_all('a', href=True):
            if NAV_WORDS.match(a.get_text(' ', strip=True)) and local_target(a['href'], page, book_dir):
                parent = a.parent
                a.decompose()
                # 案内リンクだけが入っていた箱は、箱ごと消す
                while parent is not None and parent.name in ('p', 'div', 'li') \
                        and not parent.get_text(strip=True) and not parent.find(['img', 'hr']):
                    nxt = parent.parent
                    parent.decompose()
                    parent = nxt
        for c in body.find_all(string=lambda s: isinstance(s, Comment)):
            c.extract()
        # ページ先頭の h1（＝章名）は自前で出すので外す
        first = body.find('h1')
        if first and text_of(first) in heads:
            first.decompose()
        # 見出しが自分自身へのリンクになっているもの（サイトの共有用）は、ただの見出しに
        for h in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            for a in h.find_all('a', href=True):
                if a['href'].lstrip('#') == h.get('id') or a['href'].endswith(f"#{h.get('id')}"):
                    a.unwrap()

        for el in body.find_all(id=True):
            el['id'] = f'{sid}--{el["id"]}'
        for a in body.find_all('a', href=True):
            t = local_target(a['href'], page, book_dir)
            if t and t[0] in known:
                a['href'] = f'#{slug(alias[t[0]])}' + (f'--{t[1]}' if t[1] else '')
            elif not a['href'].startswith('#'):
                a['href'] = absolute(a['href'], page, book_dir)
                a['target'] = '_blank'

        inner = ''.join(str(x) for x in body.contents)
        ptitle = escape(ptitle)
        chapters.append(
            f'<section class="chapter" id="{sid}">'
            f'<h2 class="chapter-title">{ptitle}</h2>{inner}'
            f'<p class="chapter-end"><a href="#top">▲ 目次へ</a></p></section>')
        if subs:
            lis = ''.join(f'<li><a href="#{i}">{escape(t)}</a></li>' for i, t in subs)
            toc_items.append(f'<li><details><summary><a href="#{sid}">{ptitle}</a></summary>'
                             f'<ul>{lis}</ul></details></li>')
        else:
            toc_items.append(f'<li><a href="#{sid}">{ptitle}</a></li>')

    # 元のページに無い場所（#top など）へのリンクは、その章の頭へ
    joined = ''.join(chapters)
    ids = set(re.findall(r' id="([^"]+)"', joined)) | {'top'}

    def fix(m):
        return m.group(0) if m.group(1) in ids else f'href="#{m.group(2)}"'
    joined = re.sub(r'href="#(([^"]+?)--[^"]*)"', fix, joined)
    toc = re.sub(r'href="#(([^"]+?)--[^"]*)"', fix, ''.join(toc_items))

    index = book_dir / 'index.html'
    online = SITE + quote(f'{book}/' + (index.name if index.exists() else pages[0].name))
    html = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{escape(title)}｜み旨の裏庭</title>
<style>{CSS}</style></head>
<body><main id="top">
<h1 class="book-title">{escape(title)}</h1>
<p class="book-note">み旨の裏庭 ｜ オフライン用の1ファイル版 ｜ <a href="{online}">サイトで開く</a></p>
<details class="book-toc" open><summary>目次</summary><ol>{toc}</ol></details>
{joined}
</main>
<div class="tools"><button id="smaller" aria-label="文字を小さく">A−</button><button id="bigger" aria-label="文字を大きく">A＋</button><a href="#top" aria-label="目次へ">▲</a></div>
<script>{JS}</script>
</body></html>
"""
    h = OUT / f'{out}.html'
    h.parent.mkdir(parents=True, exist_ok=True)
    h.write_text(html, encoding='utf-8')
    print(f'{out} [{title}]: {len(pages)} ページ → {h.stat().st_size / 1024:,.0f} KB')


def buttons(href_base, out, title, cls):
    name = re.sub(r'[\\/:*?"<>|]', '', title)  # 保存するときのファイル名
    return (f'<a class="{cls}" href="{href_base}{quote(out)}.html" download="{escape(name)}.html">📄 1ファイルで保存</a>')


def add_buttons(targets_list):
    """各本の目次ページに保存ボタンを置く（もう置いてあれば置き直す）。

    ふつうの本は「この本をオフライン保存」ボタンの後ろ。聖書は書ごとの
    章番号の並びの上に置く。
    """
    marker = re.compile(r'<a class="(?:book-search-btn(?: dl-file)?|dl-btn)" href="[^"]*download/[^"]*"[^>]*>[^<]*</a>')
    bible = {}
    for d, out, title in targets_list:
        if out.startswith('bible/'):
            bible[rel(d)] = (out, title)
            continue
        index = d / 'index.html'
        s = index.read_bytes().decode('utf-8')  # 改行コードを変えないように
        s2 = marker.sub('', s).replace(NO_ICON, '')
        m = re.search(r'<button class="book-search-btn" id="offline-save-btn"[^>]*>[^<]*</button>', s2)
        if not m:
            print(f'{out}: 保存ボタンの置き場所が見つからない')
            continue
        # 検索ボタン用の 🔍（a.book-search-btn::before）が付かないように打ち消す
        s2 = (s2[:m.end()] + buttons('../download/', out, title, 'book-search-btn dl-file')
              + NO_ICON + s2[m.end():])
        if s2 != s:
            index.write_bytes(s2.encode('utf-8'))
    if bible:
        index = ROOT / 'Bible_out' / 'index.html'
        s = index.read_bytes().decode('utf-8')  # 改行コードを変えないように
        s2 = re.sub(r'<div class="dl-row">.*?</div>', '', s)

        def put(m):
            first = re.search(r'href="([^"]+)"', m.group(0))
            folder = 'Bible_out/' + unquote(first.group(1)).rsplit('/', 1)[0] if first else ''
            if folder not in bible:
                return m.group(0)
            out, title = bible[folder]
            return f'<div class="dl-row">{buttons("../download/", out, title, "dl-btn")}</div>' + m.group(0)
        s2 = re.sub(r'<div class="chapter-links">.*?</a>', put, s2, flags=re.S)
        if 'dl-btn' not in s2.split('</style>')[0]:
            s2 = s2.replace('</style>', DL_CSS + '</style>', 1)
        if s2 != s:
            index.write_bytes(s2.encode('utf-8'))


NO_ICON = '<style>a.book-search-btn.dl-file::before{content:none!important}</style>'

DL_CSS = """
.dl-row { display:flex; gap:.5rem; flex-wrap:wrap; margin:.2rem 0 .6rem; }
.dl-btn { font-size:.85rem; padding:.3rem .7rem; border:1px solid currentColor; border-radius:6px;
  text-decoration:none; opacity:.85; }
"""


def clean_title(t):
    """index.html の <title> から「目次」などの飾りを外す（トップに名前が無い本の予備）"""
    t = re.split(r'[|｜]', t)[0]
    t = re.sub(r'[◆]', '', t)
    t = re.sub(r'_?Index\d*$|[\s　/／]*(総合)?(目次|もくじ)[\s　/／]*', ' ', t)
    return re.sub(r'[\s　]+', ' ', t).strip(' /／')


def targets():
    """(フォルダ, 出力名, 本の名前) の一覧。聖書は1書ずつ download/bible/ に分ける"""
    man = json.loads((ROOT / 'data' / 'offline-manifest.json').read_text(encoding='utf-8'))
    names = link_names(ROOT / 'index.html')
    for book in man['books']:
        d = ROOT / book
        if book == 'Bible_out':
            bible = {}  # 目次のリンクは章番号なので、書の名前は .book-title から
            for item in read(d / 'index.html').select('.book-item'):
                a = item.select_one('a.chapter-link')
                name = item.select_one('.book-title')
                if a and name:
                    bible[f'{book}/' + unquote(a['href']).rsplit('/', 1)[0]] = name.get_text(strip=True)
            for sub in sorted(p for p in d.glob('*/*') if p.is_dir()):
                yield sub, f'bible/{sub.name}', bible.get(rel(sub), sub.name)
            continue
        # 1ページだけの本（seikonmondou）と対訳ビューア（taiyaku）は対象外
        if book == 'taiyaku' or not (d / 'index.html').exists():
            continue
        index = read(d / 'index.html')
        own = clean_title(index.title.get_text()) if index.title else ''
        # 天聖經（増補版）の各篇は、トップでは篇の名前だけで並んでいる
        name = own if book.startswith('tenseikyou') and own else names.get(book)
        yield d, book, name or own or book


if __name__ == '__main__':
    want = set(sys.argv[1:])  # 本のフォルダ名（聖書は bible/01_genesis か Bible_out）
    todo = [t for t in targets()
            if not want or want & {t[1], rel(t[0]), rel(t[0]).split('/')[0]}]
    for d, out, title in todo:
        build(d, out, title)
    add_buttons(todo)

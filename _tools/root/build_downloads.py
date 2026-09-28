# -*- coding: utf-8 -*-
"""1冊を1つのファイルにまとめて download/ に書き出す（HTML と TXT）。

「この本をオフライン保存」(sw.js) はブラウザの保存領域に頼るので、
iPhone では Safari とホーム画面のアイコンで保存先が別だったり、
しばらく開かないと消されたりして、機内で開けないことがある。
こちらは端末にファイルとして残るので、ファイルアプリから必ず開ける。

- download/<book>.html … CSS も中に入った1ページ。目次・ルビ・蛍光ペンの色が残る
- download/<book>.txt  … 文字だけ。ルビは 暗闇《くらやみ》 の形

ページの順番は、各ページの「次へ」をたどって決める。
同じ本の中へのリンクはページ内リンクに直し、ほかの本へのリンクはサイトの URL にする。

リポジトリの根から:
    python _tools/root/build_downloads.py dp kitou   # 指定した本だけ
    python _tools/root/build_downloads.py            # 全部
"""
import json
import pathlib
import re
import sys
from urllib.parse import unquote, urljoin, urlparse

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


def local_target(href, page, book_dir):
    """href が同じ本のページを指していれば (ファイル名, #の後) を返す。"""
    if not href or href.startswith(('mailto:', 'javascript:', 'tel:')):
        return None
    if href.startswith('#'):
        return page.name, unquote(href[1:])
    url = urljoin(SITE + f'{book_dir.name}/{page.name}', href)
    p = urlparse(url)
    if not url.startswith(SITE):
        return None
    rel = unquote(p.path[len(urlparse(SITE).path):])
    target = ROOT / rel
    if target.parent == book_dir and target.suffix == '.html':
        return target.name, unquote(p.fragment)
    return None


def absolute(href, page, book_dir):
    return urljoin(SITE + f'{book_dir.name}/{page.name}', href)


def moved(page):
    """引っ越したあとの転送だけが残っているページ"""
    head = page.read_text(encoding='utf-8', errors='ignore')[:4000]
    return 'location.replace(' in head or '移動しました' in head


def reading_order(book_dir):
    pages = {p.name: p for p in book_dir.glob('*.html')
             if p.name not in SKIP_PAGES and not moved(p)}
    order = []

    def next_of(name):
        soup = read(pages[name])
        for a in soup.select('nav.page-nav a'):
            if '次へ' in a.get_text():
                t = local_target(a.get('href'), pages[name], book_dir)
                return t[0] if t else None
        return None

    # 目次（index.html）で最初に出てくる本文ページから、「次へ」をたどる
    start = None
    index = book_dir / 'index.html'
    if index.exists():
        for a in read(index).find_all('a', href=True):
            t = local_target(a['href'], index, book_dir)
            if t and t[0] in pages:
                start = t[0]
                break
    name = start or (sorted(pages)[0] if pages else None)
    while name and name in pages and name not in order:
        order.append(name)
        name = next_of(name)
    # 鎖から漏れたページは最後に名前順で足す（落とさない）
    order += sorted(n for n in pages if n not in order)
    return [pages[n] for n in order]


def page_title(soup):
    h = soup.select_one('.container h1, h1')
    if h and h.get_text(strip=True):
        return h.get_text(' ', strip=True)
    return soup.title.get_text(strip=True) if soup.title else ''


def short_title(t, book_title):
    """「原理講論 総序」「はじめに/天一国時代の祈祷」から本の名前を外す"""
    s = re.sub(r'^' + re.escape(book_title) + r'[\s　/／:：]*', '', t)
    s = re.sub(r'[\s　]*[/／|｜][\s　]*' + re.escape(book_title) + r'$', '', s)
    return s.strip() or t


def build(book):
    book_dir = ROOT / book
    pages = reading_order(book_dir)
    if not pages:
        print(f'{book}: ページが無い')
        return
    index = book_dir / 'index.html'
    title = ''
    if index.exists():
        t = read(index).title
        title = t.get_text(strip=True).split('|')[0].split('｜')[0].strip() if t else ''
    title = re.sub(r'\s*[/／]\s*目次$', '', title) or book
    known = {p.name for p in pages}

    toc_items, chapters, texts = [], [], []
    for page in pages:
        soup = read(page)
        raw_title = page_title(soup)
        ptitle = short_title(raw_title, title)
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
                while parent is not None and parent.name in ('p', 'div', 'li')                         and not parent.get_text(strip=True) and not parent.find(['img', 'hr']):
                    nxt = parent.parent
                    parent.decompose()
                    parent = nxt
        for c in body.find_all(string=lambda s: isinstance(s, Comment)):
            c.extract()
        # ページ先頭の h1（＝章名）は自前で出すので外す
        first = body.find('h1')
        if first and first.get_text(' ', strip=True) == raw_title:
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
                a['href'] = f'#{slug(t[0])}' + (f'--{t[1]}' if t[1] else '')
            elif not a['href'].startswith('#'):
                a['href'] = absolute(a['href'], page, book_dir)
                a['target'] = '_blank'

        inner = ''.join(str(x) for x in body.contents)
        chapters.append(
            f'<section class="chapter" id="{sid}">'
            f'<h2 class="chapter-title">{ptitle}</h2>{inner}'
            f'<p class="chapter-end"><a href="#top">▲ 目次へ</a></p></section>')
        if subs:
            lis = ''.join(f'<li><a href="#{i}">{t}</a></li>' for i, t in subs)
            toc_items.append(f'<li><details><summary><a href="#{sid}">{ptitle}</a></summary>'
                             f'<ul>{lis}</ul></details></li>')
        else:
            toc_items.append(f'<li><a href="#{sid}">{ptitle}</a></li>')
        texts.append(to_text(ptitle, body))

    online = SITE + f'{book}/index.html'
    html = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}｜み旨の裏庭</title>
<style>{CSS}</style></head>
<body><main id="top">
<h1 class="book-title">{title}</h1>
<p class="book-note">み旨の裏庭 ｜ オフライン用の1ファイル版 ｜ <a href="{online}">サイトで開く</a></p>
<details class="book-toc" open><summary>目次</summary><ol>{''.join(toc_items)}</ol></details>
{''.join(chapters)}
</main>
<div class="tools"><button id="smaller" aria-label="文字を小さく">A−</button><button id="bigger" aria-label="文字を大きく">A＋</button><a href="#top" aria-label="目次へ">▲</a></div>
<script>{JS}</script>
</body></html>
"""
    OUT.mkdir(exist_ok=True)
    (OUT / f'{book}.html').write_text(html, encoding='utf-8')
    txt = f'{title}\n（み旨の裏庭 {online}）\n\n' + '\n\n'.join(texts) + '\n'
    (OUT / f'{book}.txt').write_text(txt, encoding='utf-8')
    kb = lambda p: f'{p.stat().st_size / 1024:,.0f} KB'
    print(f'{book}: {len(pages)} ページ → {book}.html {kb(OUT / f"{book}.html")}, '
          f'{book}.txt {kb(OUT / f"{book}.txt")}')


def to_text(ptitle, body):
    body = BeautifulSoup(str(body), 'html.parser')
    for r in body.find_all('ruby'):
        rts = [rt.extract().get_text(strip=True) for rt in r.find_all('rt')]
        for rp in r.find_all('rp'):
            rp.extract()
        base = r.get_text()
        r.replace_with(f'{base}《{"".join(rts)}》' if rts else base)
    # 段落の切れ目と <br> に目印を置いてから文字を取り出す。ソースの改行は
    # 整形のためのものなので、和文の途中では詰める
    BR, BLOCK = ' ', ' '
    for br in body.find_all('br'):
        br.replace_with(BR)
    for el in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'p', 'li',
                             'blockquote', 'hr', 'tr', 'section', 'table']):
        el.insert_before(BLOCK)
        el.insert_after(BLOCK)
    s = re.sub(r'[ \t]*[\r\n]\s*', '', body.get_text())
    s = re.sub(r'[ \t]+', ' ', s)
    blocks = []
    for b in s.split(BLOCK):
        b = '\n'.join(x.strip() for x in b.split(BR)).strip()
        b = re.sub(r'\n{2,}', '\n', b)
        if b:
            blocks.append(b)
    bar = '━' * 20
    return f'{bar}\n{ptitle}\n{bar}\n\n' + '\n\n'.join(blocks)


if __name__ == '__main__':
    books = sys.argv[1:]
    if not books:
        man = json.loads((ROOT / 'data' / 'offline-manifest.json').read_text(encoding='utf-8'))
        books = list(man['books'])
    for b in books:
        build(b)

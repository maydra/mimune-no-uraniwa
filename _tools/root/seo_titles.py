# -*- coding: utf-8 -*-
"""ページの title を1枚ずつ見分けがつくようにし、description が無いページに本文の頭を入れる。

同じ本のページが全部「父の祈り　２　熱望編」のような本の名前だけだと、Google には
同じ名前のページが何十枚も並んでいるように見え、重複としてまとめて落とされやすい。
title が他のページと同じなら、そのページの最初の見出しを頭に足す:
    父の祈り　２　熱望編  →  お父様！　不足なる私たちを受け入れてください | 父の祈り　２　熱望編 | み旨の裏庭

見出しが取れないページは触らない（--dry-run の一覧に「見出しなし」で出る）。
目次ページ（title に「目次」）と、すでに description があるページの description は触らない。
何度回しても結果は同じ。

    python _tools/root/seo_titles.py --dry-run tf_inori   # 変更前後を表示するだけ
    python _tools/root/seo_titles.py tf_inori             # 書き換える（フォルダは複数可、--all で全部）
"""
import collections
import html
import pathlib
import re
import sys
import unicodedata
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://maydra.github.io/mimune-no-uraniwa/'
SITE = 'み旨の裏庭'
DESC_LEN = 120
MAX_HEAD = 60  # これより長いのは見出しではなく目次の一覧を拾っている

TITLE = re.compile(r'(?is)<title[^>]*>(.*?)</title>')
HAS_DESC = re.compile(r'(?is)<meta[^>]+name=["\']description["\']')
# 見出しの候補を上から順に試す。h2/h3 が無い本（父の祈りの一部）は、太字の1行＋<hr> が題になっている
HEADS = [re.compile(r'(?is)<h[234][^>]*>(.*?)</h[234]>'),
         re.compile(r'(?is)<b id=["\']?\d+["\']?[^>]*>(.*?)(?:<hr|</b>)'),
         re.compile(r'(?is)<b>(?:\s*<br\s*/?>)?([^<]{2,80})<br\s*/?>\s*</b>\s*<hr'),
         # 南北統一: 罫線のすぐ下の1行が見出し（タグが付いていない）
         re.compile(r'(?is)<hr[^>]*>\s*(?:<(?:br|p|b)\b[^>]*>\s*)*([^<]{2,60})<br\s*/?>'),
         # 最後の手段: 目次の改修でページの頭に入れた目次の項目
         re.compile(r'(?is)<li class="toc-b[^"]*"><a [^>]*>(.*?)</a>')]
SKIP_HEADS = {'目次', ''}
# 本文ではない部品。見出しにも説明文にも使わない
JUNK = [re.compile(r'(?is)<nav\b.*?</nav>'),
        re.compile(r'(?is)<div class="toc"[^>]*>.*?</ul></div>'),       # ページの頭の目次
        re.compile(r'(?is)<div class="book-search">.*?</div>'),          # 書籍内検索・オフライン保存
        re.compile(r'(?is)<section id="typo-report".*?</section>'),      # 誤植の投稿フォーム
        re.compile(r'(?is)<a\b[^>]*>\s*(?:目次に戻る|前のページに戻る|次のページに進む|（全面表示）|戻る)\s*</a>')]
NON_ASCII_GAP = re.compile(r'(?<=[^\x00-\x7f]) (?=[^\x00-\x7f])')


def text(fragment):
    t = re.sub(r'(?s)<(script|style)\b.*?</\1>', '', fragment)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    # 全角空白（「第一章　〇〇」の区切り）は残し、改行やタブだけ詰める
    return re.sub(r'[ \t\r\n\f\v]+', ' ', t).strip(' \u3000')


def sitemap_pages():
    idx = (ROOT / 'sitemap-index.xml').read_text(encoding='utf-8')
    for s in re.findall(r'<loc>(.*?)</loc>', idx):
        sub = (ROOT / unquote(s)[len(BASE):]).read_text(encoding='utf-8')
        for u in re.findall(r'<loc>(.*?)</loc>', sub):
            yield ROOT / unquote(u)[len(BASE):]


def body_after_h1(src):
    m = re.search(r'(?is)</h1>', src)
    body = src[m.end():] if m else src[src.lower().find('<body'):]
    for junk in JUNK:
        body = junk.sub('', body)
    return body


def squeeze(s):
    """比べるための形。全角半角をそろえ、空白と区切り記号（/ _ |）を落とす。"""
    return re.sub(r'[\s/_|]', '', unicodedata.normalize('NFKC', s))


def candidates(src):
    body = body_after_h1(src)
    for pat in HEADS:
        for m in pat.finditer(body):
            yield NON_ASCII_GAP.sub('', text(m.group(1))), m.end()


def heading(src, title='', common=frozenset()):
    # 本の名前と同じ見出し（各ページの頭に本の名前が h2 で入っている本がある）と、
    # 同じ本のページの半分以上に出てくる見出し（「文鮮明先生のみ言集」のようなシリーズ名）は飛ばして次を見る
    squeezed = squeeze(title)
    for h, end in candidates(src):
        if h in SKIP_HEADS or h in common or len(h) > MAX_HEAD or squeeze(h) in squeezed:
            continue
        return h, end
    return None, None


def common_heads(srcs):
    """本（フォルダ）ごとに、ページの半分以上に出てくる見出し。"""
    per_book = collections.defaultdict(collections.Counter)
    pages = collections.Counter()
    for p, src in srcs.items():
        book = p.relative_to(ROOT).parts[0]
        pages[book] += 1
        per_book[book].update({h for h, _ in candidates(src)})
    return {b: frozenset(h for h, n in c.items() if n >= 3 and n * 2 >= pages[b])
            for b, c in per_book.items()}


def drop_prefix(t, name):
    """t の頭が name と（空白・区切り・全角半角を無視して）同じなら、その分を落とす。"""
    want = squeeze(name)
    if not want:
        return t
    i = j = 0
    while i < len(t) and j < len(want):
        c = squeeze(t[i])
        if not c:
            i += 1
        elif c == want[j]:
            i += 1
            j += 1
        else:
            return t
    return t[i:] if j == len(want) else t


def description(src, start, names=()):
    body = body_after_h1(src)
    t = text(body[start:] if start else body)
    # 「2-13」のようなページ番号だけの頭は落とす
    t = re.sub(r'^\d+-\d+\s*', '', t)
    # 本文の頭に本の名前がもう一度入っている本が多い（南北統一・真の父母など）。説明文では落とす
    for name in names:
        t = drop_prefix(t, name)
    # 旧サイトの「(全面表示)」リンクと、原本のページ番号「P.121」
    t = re.sub(r'[（(]全面表示[)）]|\bP\.?\s?\d+\b', '', t)
    t = re.sub(r'^[\s　]+', '', t)
    # 行の切れ目（<br>）で入った空白は、日本語どうしのあいだでは詰める
    t = NON_ASCII_GAP.sub('', t)
    return t if len(t) <= DESC_LEN else t[:DESC_LEN].rstrip() + '…'


def main(args):
    dry = '--dry-run' in args
    folders = [a.strip('/') for a in args if not a.startswith('--')]
    pages = list(sitemap_pages())
    # 改行コード（CRLF）をそのまま保つ
    srcs = {p: open(p, encoding='utf-8', newline='').read() for p in pages}
    titles = {p: text(m.group(1)) if (m := TITLE.search(s)) else '' for p, s in srcs.items()}
    count = collections.Counter(titles.values())
    common = common_heads(srcs)

    changed = skipped = 0
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        if '--all' not in args and rel.split('/')[0] not in folders:
            continue
        title = titles[p]
        if '目次' in title:
            # 目次ページは別の手当てが要る（同じ巻の目次が2枚ある本もある）。今回は触らない
            continue
        src = old = srcs[p]
        head, end = heading(src, title, common.get(p.relative_to(ROOT).parts[0], frozenset()))
        # 元の title は全角空白などをそのまま残す
        raw = html.unescape(TITLE.search(src).group(1)).strip() if title else ''
        # ファイル名がそのまま入った title（「南北統一_1-1-1」「訓教経/(上)003」）は、ファイル名を外して本の名前だけにする
        weak = bool(raw) and re.search(re.escape(p.stem) + r'$', raw) and re.search(r'\d', p.stem)
        if weak:
            raw = re.sub(re.escape(p.stem) + r'$', '', raw).rstrip(' _/　')
        # 本の入口（index.html）は本の名前のままでいい。重複の相手のほうに見出しを足す
        if title and (count[title] > 1 or weak) and p.name != 'index.html':
            if head:
                new = f'{head} | {raw}' + ('' if SITE in raw else f' | {SITE}')
                src = TITLE.sub(lambda m: f'<title>{html.escape(new, quote=False)}</title>', src, count=1)
                print(f'T {rel}\n    {title}\n  → {new}')
            elif not head:
                skipped += 1
                print(f'- {rel}  見出しなし: {title}')
        if not HAS_DESC.search(src):
            h1 = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', src)
            names = [title, raw] + ([text(h1.group(1))] if h1 else [])
            d = description(src, end, names)
            if d and p.name == 'index.html':
                d = description(src, None, names)
                d = f'『{title}』の目次。{d}'[:DESC_LEN + 1]
            if d:
                tag = f'\n<meta name="description" content="{html.escape(d)}"/>'
                src = re.sub(r'(?is)</title>', lambda m: m.group(0) + tag, src, count=1)
                print(f'D {rel}  {d[:50]}…')
        if src != old:
            changed += 1
            if not dry:
                p.write_text(src, encoding='utf-8', newline='')
    print(f'\n{"(dry-run) " if dry else ""}{changed} pages changed, {skipped} duplicates left (no heading)')


if __name__ == '__main__':
    main(sys.argv[1:])

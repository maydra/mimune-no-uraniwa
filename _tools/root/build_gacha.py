# -*- coding: utf-8 -*-
"""data/gacha.json を作り直す。

ホームの「🎲 み言をランダムに見る」(gacha.html) と各本の「今日のみ言をこの本から
ランダムに探す」(<本>/random.html) が読む、本文ページと字数の一覧。振り分けは
theme/gacha.js で、字数に比例してページを選び、着いたページで reader.js が本文の中から
一節を選ぶ。どの字も同じ確率で当たるので、長い本ほどよく出る（ページ単位で選んで
いたころは、短いページが417枚ある『父の祈り』が5回に1回出ていた）。
本の名前は、着いたページの札（「🎲『真の父母』から」）に出す。ページの題は本によって
書き方がまちまちなので、ホームの本の一覧のリンクの文字を使う。

    {"books": {"<フォルダ>": "<本の名前>", ...},
     "solo": ["<本ごとのランダムだけに出す本>", ...],
     "pages": [["<フォルダ>/<ページ>", <字数>], ...]}

入れないもの: 目次・ランダム・検索・はじめに／序文、転送だけのページ、
聖書・聖歌・対訳・辞典。み言ではない信仰の証し（SOLO）は、ホームのガチャには出さず、
その本の random.html からだけ引く。

本を足したり消したりしたら、リポジトリの根からこれを回して commit:
    python _tools/root/build_gacha.py
"""
import json
import pathlib
import re

from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'data' / 'gacha.json'

SKIP_DIRS = {'_tools', 'data', 'theme', 'icons', 'music', '.git', 'Index', 'library',
             'download',            # build_downloads.py が書き出す1ファイル版
             'Bible_out',           # 聖書
             'seika',               # 聖歌
             'taiyaku', 'jisho'}    # 対訳・原理用語辞典
SOLO = {'kansha_suru_faith'}        # 先輩の信仰の証し。み言ではないので、本ごとのランダムだけ
# 目次（tf_inori の framepage も目次）・ランダム・検索・はじめに／序文
SKIP_NAMES = re.compile(r'index|mokuji|random|search|gacha|hajimeni|jyobunn|preface|framepage', re.I)
# reader.js が本文の字に数えない所（NOT_BODY と同じ）
NOT_BODY = 'script,style,nav,rt,rp,.page-nav,.typo-box,#reader-ui,#reader-drawer,#reader-gacha,#stacked-header-container,.toc,.hits'
MIN_CHARS = 50


def chars(html):
    """本文の字数。半分以上がリンクのページ（マルスムの sub2.html のような小目次）は 0"""
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body or soup
    for el in body.select(NOT_BODY):
        el.decompose()
    n = len(re.sub(r'\s', '', body.get_text()))
    links = sum(len(re.sub(r'\s', '', a.get_text())) for a in body.select('a[href]'))
    return 0 if links * 2 >= n else n


def book_names():
    """ホームの本の一覧から、フォルダ → 本の名前"""
    home = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    names = {}
    for a in home.select('main a[href]'):
        href = a['href']
        if '/' in href and not href.startswith(('http', '#', '..')):
            names.setdefault(href.split('/')[0], re.sub(r'\s+', ' ', a.get_text()).strip())
    # 天聖經（増補版）は、ホームでは篇の名前（「神様」）だけを並べている。篇の目次の題を使う
    for d in ROOT.glob('tenseikyou[0-9]*'):
        t = BeautifulSoup((d / 'index.html').read_text(encoding='utf-8'), 'html.parser').title
        if t:
            names[d.name] = re.sub(r'\s*[|｜]\s*目次.*$', '', t.get_text()).strip()
    return names


pages = []
for d in sorted(ROOT.iterdir()):
    if not d.is_dir() or d.name in SKIP_DIRS or d.name.startswith('.'):
        continue
    for f in sorted(d.glob('*.html')):
        if SKIP_NAMES.search(f.name):
            continue
        html = f.read_text(encoding='utf-8', errors='ignore')
        # 引っ越したあとの転送だけのページ
        if 'location.replace(' in html or 'http-equiv="refresh"' in html:
            continue
        n = chars(html)
        if n >= MIN_CHARS:
            pages.append([str(f.relative_to(ROOT)).replace('\\', '/'), n])

names = book_names()
books = {}
for p, _ in pages:
    d = p.split('/')[0]
    if d not in names:
        raise SystemExit(f'{d}: ホームの本の一覧に無い。index.html にリンクを足すか、SKIP_DIRS に入れる')
    books[d] = names[d]

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({'books': books, 'solo': sorted(SOLO & set(books)), 'pages': pages},
                          ensure_ascii=False, separators=(',', ':')),
               encoding='utf-8')
total = sum(n for _, n in pages)
print(f'{OUT.name}: {len(books)} books, {len(pages)} pages, {total:,} chars, {OUT.stat().st_size:,} bytes')

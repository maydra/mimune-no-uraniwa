# -*- coding: utf-8 -*-
"""天一国経典『平和経』の韓日（のちに英）対訳の材料を作る。講演ごとに1節（178節）。

韓国語: Daum カフェ「천일국 경전방」の掲示板 UYjn（2. 평화경。1記事＝1講演、182本）を
        _tools/cafe_books/crawl.py・parse.py で落とした raw/UYjn.jsonl の写し src/UYjn.jsonl（2026-10-31）
日本語: このサイトの heiwakyou/HHNN.html（掲示板 V1yi から組み、化けた字などを直した版）

記事の通し番号 [001]〜[182] は日本語版の講演の順と同じ。[062]〜[066]「천국을 여는 문 참가정 1〜5」だけは
日本語版では第四篇14 の1講演（0414）なので、5本をつなぐ。対応は日付の行で確かめる。

書き出すもの（work/sections/）:
    HHNN.json … {"key", "hen", "num", "title": {ko, ja}, "serials", "posts", "ko": [{n, t, kind}], "ja": [{s, p, t, kind}]}
                serials は記事の題の [001] の番号、posts は掲示板の記事の番号（m.cafe.daum.net/ckatkfkdrhdqn/UYjn/<番号>）
                kind は "meta"（日付・場所・行事の行）・"head"（小見出し）・"p"（本文）
    HHNN.txt  … 対応付けのための一覧（K1: …／J1 [p1]: …）

    python -I -X utf8 _tools/heiwakyou_taiyaku/prepare.py
"""
import json
import pathlib
import re

from bs4 import BeautifulSoup

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KO_SRC = HERE / 'src' / 'UYjn.jsonl'     # _tools/cafe_books/raw/UYjn.jsonl の写し（掲示板の記事が変わっても対応表がずれないように固定）
SITE = ROOT / 'heiwakyou'
OUT = HERE / 'work' / 'sections'
MERGE = {62: [62, 63, 64, 65, 66]}      # 天国を開く門 真の家庭 1〜5 → 0414
# 第六篇 6〜10 は、日本語版は日付の順、韓国語の掲示板は題の順に並んでいる。日付の行で対応を決めた（日本語のページ → 記事の通し番号）
ORDER_FIX = {'0606': 101, '0607': 100, '0608': 103, '0609': 104, '0610': 102}

META_KO = re.compile(r'^(날\s*짜|장\s*소|행\s*사)\s*[:：]')
ENDS = tuple('.?!。」’”)』…')
KN = dict(zip('〇一二三四五六七八九', range(10)))


def serial(r):
    return int(re.search(r'\[(\d+)\]', r['title']).group(1))


def ko_title(r):
    t = re.sub(r'^평화경\s*-\s*\[\d+\]\s*', '', r['title'])
    t = re.sub(r'^-\s*\d+\s*-\s*\d+\s*[.\-]\s*', '', t)
    t = re.sub(r'^-\s*제?\d+편\s*-\s*\d+\.\s*', '', t)
    # 「(完)」は外す。「①②③」は同じ題の講演を見分ける印なので残す（第六篇の「이상세계의 주역이 될 여성 ①〜③」など）
    return re.sub(r'\s*\(完\)\s*$', '', t).strip()


def ko_items(posts):
    """韓国語の記事（1本か、つなぐ5本）→ [{t, kind}]。頭の書名・篇・章の行は外す"""
    items = []
    for r in posts:
        lines = []
        for p in r['paras']:
            for l in p['text'].split('\n'):
                l = l.replace('​', '').strip()
                if l:
                    lines.append((l, p['bold']))
        k = next((i for i, (l, _) in enumerate(lines) if META_KO.match(l)), None)
        if k is not None and k <= 4:
            body = lines[k:]
        else:
            body = lines[1:]            # [062]〜[066]: 1行目は「천국을 여는 문 참가정 N」
        any_bold = any(b for l, b in body if not META_KO.match(l))
        for l, bold in body:
            if META_KO.match(l):
                kind = 'meta'
            elif ((bold or not any_bold) and len(l) < 60 and not l.endswith(ENDS)) or re.match(r'^제\d+장\s', l):
                kind = 'head'
            else:
                kind = 'p'
            items.append({'t': l, 'kind': kind})
    return items


OPEN, CLOSE = '「『（(〔【“‘', '」』）)〕】”’'


def ja_sentences(text):
    """日本語の段落を文に分ける。。！？ で切るが、「」などの括弧の中では切らない（heiwa_sekaijin と同じ）"""
    out = []
    for line in text.split('\n'):
        buf, depth = '', 0
        for ch in line:
            buf += ch
            if ch in OPEN:
                depth += 1
            elif ch in CLOSE:
                depth = max(0, depth - 1)
            elif ch in '。！？!?' and depth == 0:
                out.append(buf.strip())
                buf = ''
        if buf.strip():
            out.append(buf.strip())
    return [s for s in out if s]


def ja_page(path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    title = soup.select_one('.chapter-head h2').get_text(strip=True)
    paras = []
    for p in soup.select('.content-card > p'):
        cls = p.get('class') or []
        if 'typo-desc' in cls:
            continue
        for br in p.find_all('br'):
            br.replace_with('\n')
        t = p.get_text().strip()
        if t:
            paras.append((t, 'meta' if 'meta' in cls else 'head' if 'subhead' in cls else 'p'))
    return title, paras


def kdate(items):
    for x in items:
        m = re.search(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', x['t'])
        if x['kind'] == 'meta' and m:
            return tuple(map(int, m.groups()))


def jdate(paras):
    def k(x):
        if '十' in x:
            a, b = x.split('十')
            return (KN[a] if a else 1) * 10 + (KN[b] if b else 0)
        return int(''.join(str(KN[c]) for c in x))
    for t, kind in paras:
        m = re.search(r'([〇一二三四五六七八九]{4})年([〇一二三四五六七八九十]+)月([〇一二三四五六七八九十]+)日', t)
        if kind == 'meta' and m:
            return tuple(k(g) for g in m.groups())


def main():
    rows = sorted((json.loads(l) for l in KO_SRC.read_text(encoding='utf-8').splitlines() if l.strip()), key=serial)
    by_serial = {serial(r): r for r in rows}
    assert sorted(by_serial) == list(range(1, 183)), '記事の通し番号が 1〜182 でない'
    merged = {s for v in MERGE.values() for s in v[1:]}
    speeches = [[by_serial[s] for s in MERGE.get(s, [s])] for s in sorted(by_serial) if s not in merged]
    pages = sorted(SITE.glob('[0-9][0-9][0-9][0-9].html'))
    assert len(speeches) == len(pages) == 178, (len(speeches), len(pages))
    for i, page in enumerate(pages):
        if page.stem in ORDER_FIX:
            speeches[i] = [by_serial[ORDER_FIX[page.stem]]]
    OUT.mkdir(parents=True, exist_ok=True)
    report, total = [], {'ko': 0, 'ja': 0, 'ko_chars': 0, 'ja_chars': 0}
    for posts, page in zip(speeches, pages):
        key = page.stem
        title_ja, paras = ja_page(page)
        ko = [{'n': i, **x} for i, x in enumerate(ko_items(posts), 1)]
        ja, s = [], 0
        for pi, (t, kind) in enumerate(paras, 1):
            for sent in ([t] if kind != 'p' else ja_sentences(t)):
                s += 1
                ja.append({'s': s, 'p': pi, 't': sent, 'kind': kind})
        kd, jd = kdate(ko), jdate(paras)
        if kd and jd and kd != jd:
            report.append(f'{key} 日付が合わない: 韓 {kd} / 日 {jd}')
        elif not (kd and jd):
            report.append(f'{key} 日付で確かめられない（韓 {kd} / 日 {jd}）')
        nh = (sum(x['kind'] == 'head' for x in ko), sum(x['kind'] == 'head' for x in ja))
        if nh[0] != nh[1]:
            report.append(f'{key} 小見出しの数が違う: 韓 {nh[0]} / 日 {nh[1]}')
        sec = {'key': key, 'hen': int(key[:2]), 'num': int(key[2:]),
               # つないだ講演（0414）は、1本目の記事の題の後ろの「1」を外す
               'title': {'ko': re.sub(r'\s*\d+$', '', ko_title(posts[0])) if len(posts) > 1 else ko_title(posts[0]), 'ja': title_ja},
               'serials': [serial(r) for r in posts], 'posts': [r['n'] for r in posts], 'ko': ko, 'ja': ja}
        (OUT / f'{key}.json').write_text(json.dumps(sec, ensure_ascii=False, indent=1), encoding='utf-8')
        mark = {'meta': ' 頭', 'head': ' 見出し', 'p': ''}
        txt = [f'# {key}  第{sec["hen"]}篇 {sec["num"]}  {sec["title"]["ko"]} / {title_ja}', '',
               '## 韓国語（原文。[頭] は日付・場所・行事の行、[見出し] は小見出し）']
        txt += [f'K{x["n"]}{" [" + mark[x["kind"]].strip() + "]" if x["kind"] != "p" else ""}: {x["t"]}' for x in ko]
        txt += ['', '## 日本語（サイトの訳。[pN] は段落）']
        txt += [f'J{x["s"]} [p{x["p"]}{mark[x["kind"]]}]: {x["t"]}' for x in ja]
        (OUT / f'{key}.txt').write_text('\n'.join(txt) + '\n', encoding='utf-8')
        total['ko'] += len(ko)
        total['ja'] += len(ja)
        total['ko_chars'] += sum(len(x['t']) for x in ko)
        total['ja_chars'] += sum(len(x['t']) for x in ja)
    report.append(f'節 {len(pages)}、韓国語 {total["ko"]} かたまり（{total["ko_chars"]:,} 字）、'
                  f'日本語 {total["ja"]} 文（{total["ja_chars"]:,} 字）')
    (HERE / 'work' / 'prepare-report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report))


if __name__ == '__main__':
    main()

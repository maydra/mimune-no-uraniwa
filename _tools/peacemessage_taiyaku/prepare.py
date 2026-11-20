# -*- coding: utf-8 -*-
"""『平和神経』（平和メッセージ 1〜17）の韓日対訳の材料を作る。メッセージごとに1節（17節）。

韓国語: Daum カフェ「천일국 경전방」の掲示板 W7Yt（4. 평화신경。記事 1〜17 が平和メッセージ 1〜17）を
        _tools/cafe_books/crawl.py・parse.py で落とした raw/W7Yt.jsonl の写し src/W7Yt.jsonl（2026-11-21）
日本語: このサイトの peacemessage/N.html

記事 19〜24（カフェの番号で 18〜23 のメッセージ）は、サイトに日本語版が無いので扱わない。

書き出すもの（work/sections/）:
    NN.json … {"key", "num", "title": {ko, ja}, "posts", "ko": [{n, t, kind}], "ja": [{s, p, t, kind}]}
              kind は "meta"（題・日付・場所・行事の行）・"head"（小見出し）・"p"（本文）
    NN.txt  … 対応付けのための一覧（K1: …／J1 [p1]: …）

    python -I -X utf8 _tools/peacemessage_taiyaku/prepare.py
"""
import json
import pathlib
import re

from bs4 import BeautifulSoup

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KO_SRC = HERE / 'src' / 'W7Yt.jsonl'
SITE = ROOT / 'peacemessage'
OUT = HERE / 'work' / 'sections'
N = 17

ENDS = tuple('.?!。」’”)』…')
# 記事の頭の、本文ではない行。動画のリンクと「평화메시지 N」の行は落とす。題・日付・行事の説明は [頭] にする
DROP = re.compile(r'^(https?://\S+|(평화신경\s*-\s*)?평화메시지\s*[0-9ⅠⅡⅢⅣⅤⅥVIX]+\s*장?)$')
NOTE = re.compile(r'^[<(（〈＜]|^이\s*(글|말씀)은|^\d{4}년|^(날\s*짜|장\s*소|행\s*사)\s*[:：]|^천일국\s*\d+년|말씀\s*(\(|$)')
OPEN, CLOSE = '「『（(〔【“‘', '」』）)〕】”’'


def ko_title(r):
    t = re.sub(r'^평화신경\s*-\s*\d+\s*-\s*', '', r['title'])
    return t.strip()


def ko_items(r):
    lines = []
    for p in r['paras']:
        for l in p['text'].split('\n'):
            l = l.replace('​', '').strip()
            if l and not re.fullmatch(r'\d{1,3}', l):   # 数字だけの行は本の頁の番号（1〜3 の記事に残っている）
                lines.append((l, p['bold']))
    title = re.sub(r'\s', '', re.sub(r'[ⅠⅡⅢ123\-―–]', '', ko_title(r)))
    # 頭の行: 本文（長い文で、行事の説明でないもの）が始まるまで
    k = 0
    while k < len(lines) and k < 8:
        l = lines[k][0]
        short = len(l) < 70 and not l.endswith(('.', '!', '?'))
        if DROP.match(l) or NOTE.search(l) or short or title in re.sub(r'\s', '', l):
            k += 1
        else:
            break
    items = []
    for l, _ in lines[:k]:
        if not DROP.match(l):
            items.append({'t': l, 'kind': 'meta'})
    body = lines[k:]
    any_bold = any(b for _, b in body)
    for l, bold in body:
        head = (bold or not any_bold) and len(l) < 60 and not l.endswith(ENDS)
        items.append({'t': l, 'kind': 'head' if head else 'p'})
    return items


def ja_sentences(text):
    """日本語の段落を文に分ける。。！？ で切るが、「」などの括弧の中では切らない（heiwakyou_taiyaku と同じ）"""
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
    """[(text, kind)]。h1（平和メッセージN）と目次は外す。最初の段落（題）と（このメッセージは…）の段落は meta"""
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    box = soup.select_one('div.container')
    paras, body_started = [], False
    for el in box.find_all(['p', 'span'], recursive=False):
        for br in el.find_all('br'):
            br.replace_with('\n')
        t = el.get_text().replace('\xa0', ' ').strip()
        if not t:
            continue
        if el.name == 'span':
            if 'subheading' in (el.get('class') or []):
                paras.append((t, 'head'))
                body_started = True
            continue
        if not body_started and (not paras or t.startswith(('（', '(', '＜', '<', '〈')) or (len(t) < 60 and not t.endswith(('。', '！', '？')))):
            paras.append((t, 'meta'))
        else:
            body_started = True
            paras.append((t, 'p'))
    return paras


def main():
    rows = {r['n']: r for r in (json.loads(l) for l in KO_SRC.read_text(encoding='utf-8').splitlines() if l.strip())}
    OUT.mkdir(parents=True, exist_ok=True)
    report, total = [], {'ko': 0, 'ja': 0, 'ko_chars': 0, 'ja_chars': 0}
    for num in range(1, N + 1):
        key = f'{num:02d}'
        r = rows[num]
        assert re.match(rf'^평화신경\s*-\s*{num}\s*-', r['title']), r['title']
        paras = ja_page(SITE / f'{num}.html')
        title_ja = paras[0][0]
        ko = [{'n': i, **x} for i, x in enumerate(ko_items(r), 1)]
        ja, s = [], 0
        for pi, (t, kind) in enumerate(paras, 1):
            for sent in ([t] if kind != 'p' else ja_sentences(t)):
                s += 1
                ja.append({'s': s, 'p': pi, 't': sent, 'kind': kind})
        nh = (sum(x['kind'] == 'head' for x in ko), sum(x['kind'] == 'head' for x in ja))
        nm = (sum(x['kind'] == 'meta' for x in ko), sum(x['kind'] == 'meta' for x in ja))
        report.append(f'{key} 韓 {len(ko)} かたまり（頭 {nm[0]}・見出し {nh[0]}）/ 日 {len(ja)} 文（頭 {nm[1]}・見出し {nh[1]}）'
                      f'  {ko_title(r)} / {title_ja}')
        sec = {'key': key, 'num': num, 'title': {'ko': ko_title(r), 'ja': title_ja}, 'posts': [r['n']], 'ko': ko, 'ja': ja}
        (OUT / f'{key}.json').write_text(json.dumps(sec, ensure_ascii=False, indent=1), encoding='utf-8')
        mark = {'meta': ' 頭', 'head': ' 見出し', 'p': ''}
        txt = [f'# {key}  平和メッセージ {num}  {sec["title"]["ko"]} / {title_ja}', '',
               '## 韓国語（原文。[頭] は題・日付・場所・行事の行、[見出し] は小見出し）']
        txt += [f'K{x["n"]}{" [" + mark[x["kind"]].strip() + "]" if x["kind"] != "p" else ""}: {x["t"]}' for x in ko]
        txt += ['', '## 日本語（サイトの訳。[pN] は段落）']
        txt += [f'J{x["s"]} [p{x["p"]}{mark[x["kind"]]}]: {x["t"]}' for x in ja]
        (OUT / f'{key}.txt').write_text('\n'.join(txt) + '\n', encoding='utf-8')
        total['ko'] += len(ko)
        total['ja'] += len(ja)
        total['ko_chars'] += sum(len(x['t']) for x in ko)
        total['ja_chars'] += sum(len(x['t']) for x in ja)
    report.append(f'節 {N}、韓国語 {total["ko"]} かたまり（{total["ko_chars"]:,} 字）、日本語 {total["ja"]} 文（{total["ja_chars"]:,} 字）')
    (HERE / 'work' / 'prepare-report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report))


if __name__ == '__main__':
    main()

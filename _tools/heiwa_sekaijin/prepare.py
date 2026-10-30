# -*- coding: utf-8 -*-
"""『平和を愛する世界人として』の韓日（のちに英）対訳の材料を作る。

韓国語は src/ko-ja-en.txt（み言選集の Zip に入っていた「평화를 사랑하는 세계인으로 (한.日.Eng.).txt」の写し）。
節ごとに「韓国語 → 日本語 → 英語」の順で並び、韓国語の本文は番号の行と本文の行が交互に来る。
日本語はサイトの heiwa_sekaijin/（読み取りの誤りを直し、段落をつないである版）。

書き出すもの（work/sections/）:
    NN.json  … {"no", "ch", "sec", "title": {ko, ja}, "ko": [{n, t}], "ja": [{s, p, t}], "ko_missing"}
    NN.txt   … 対応付けのための一覧（K1: …／J1 [p1]: …）
NN は 00 が序文、01〜67 が本文の節（サイトの節の順。6章7節＝53 は元のファイルに無い）。

    python _tools/heiwa_sekaijin/prepare.py
"""
import json
import pathlib
import re
import difflib

from bs4 import BeautifulSoup

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = HERE / 'src' / 'ko-ja-en.txt'
SITE = ROOT / 'heiwa_sekaijin'
OUT = HERE / 'work' / 'sections'
MISSING = {53}          # 6章7節「銃剣を収めて真の愛で」。元のファイルに韓・英とも無い


def kind(s):
    """行の言語。ハングル・かな・ローマ字の数で決める"""
    t = s.strip()
    if not t:
        return '_'
    if re.fullmatch(r'\d+', t):
        return 'N'
    h = len(re.findall(r'[가-힣]', t))
    k = len(re.findall(r'[぀-ヿ]', t))
    l = len(re.findall(r'[A-Za-z]', t))
    if h and h >= k and h * 3 >= l:
        return 'ko'
    if k:
        return 'ja'
    if l:
        return 'en'
    return 'C'


def file_blocks(lines):
    """本文（目次のあと）を言語の塊に分け、韓・日・英の3つ組を返す"""
    # 目次のあとの、書名だけの行から（行によって空白などが混じるので「含む」で見る）
    start = next(i for i, l in enumerate(lines) if i > 20 and '평화를 사랑하는 세계인으로' in l and '목차' not in l)
    blocks = []
    for i in range(start, len(lines)):
        k = kind(lines[i])
        if k in ('ko', 'ja', 'en'):
            if not blocks or blocks[-1]['lang'] != k:
                blocks.append({'lang': k, 'line': i + 1, 'rows': []})
            blocks[-1]['rows'].append(lines[i].rstrip())
        elif k in ('N', 'C') and blocks:
            blocks[-1]['rows'].append(lines[i].rstrip())
    trios = [blocks[k:k + 3] for k in range(0, len(blocks), 3)]
    assert all([b['lang'] for b in t] == ['ko', 'ja', 'en'] for t in trios), 'ko/ja/en の順が崩れている'
    return trios


def ko_pieces(block):
    """韓国語の塊 → 節の題と、番号の付いたかたまり。番号の行のあとに本文が1行以上"""
    rows = [r.strip() for r in block['rows'] if r.strip()]
    title = None
    pieces = []
    i = 0
    while i < len(rows):
        r = rows[i]
        if re.fullmatch(r'\d+', r):
            pieces.append({'n': int(r), 'lines': []})
        elif pieces:
            pieces[-1]['lines'].append(r)
        elif re.match(r'^\d+\s*[.．]\s*\S', r):
            title = r
        i += 1
    probs = []
    for k, p in enumerate(pieces, 1):
        if p['n'] != k:
            probs.append(f'番号 {p["n"]} が {k} 番目')
        if not p['lines']:
            probs.append(f'番号 {p["n"]} に本文が無い')
    return title, [{'n': k, 't': '\n'.join(p['lines'])} for k, p in enumerate(pieces, 1)], probs


OPEN, CLOSE = '「『（(〔【“‘', '」』）)〕】”’'


def ja_sentences(text):
    """日本語の段落を文に分ける。。！？ で切るが、「」などの括弧の中では切らない。改行（<br>）でも切る"""
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


# 英語は PDF から写したときに合字（ff・fi・fl・ffi・ft）が抜けている。見つかったものだけを、表で直す
EN_FIX = [
    (re.compile(r'\b([Aa])\.er'), r'\1fter'),          # a.er・a.ernoon・a.erward
    (re.compile(r'\b([Oo])\.en\b'), r'\1ften'),
    (re.compile(r'\blo\.y\b'), 'lofty'),
    (re.compile(r'\ble\.ists\b'), 'leftists'),
    (re.compile(r'\bdi-cult'), 'difficult'),
    (re.compile(r'\bsu-cient'), 'sufficient'),
    (re.compile(r'\bo-ce\b'), 'office'),
    (re.compile('‎'), ''),                          # 見えない向きの印
]
EN_TITLE = 'As a peace-loving global citizen'
ABBR = {'Mr', 'Mrs', 'Ms', 'Dr', 'St', 'Jr', 'Sr', 'Rev', 'Prof', 'Gen', 'Col', 'Lt', 'Mt', 'No', 'vs', 'etc', 'Inc', 'Co'}


def en_fix(t):
    for pat, rep in EN_FIX:
        t = pat.sub(rep, t)
    return t


def en_paras(block):
    """英語の塊 → (節の題, [段落])。頭の書名・章・節の題の行を外し、小文字で始まる行は前の段落の続きとしてつなぐ"""
    rows = [en_fix(r.strip()) for r in block['rows'] if r.strip()]
    rows = [r for r in rows if r.lower() != EN_TITLE.lower()]
    title = None
    if rows and re.match(r'^CHAPTER\b', rows[0], re.I):
        rows = rows[1:]
    if rows and re.match(r'^\d+\s*[.．]\s*\S', rows[0]):
        title, rows = rows[0], rows[1:]
    paras = []
    for r in rows:
        if paras and re.match(r'^[a-z]', r) and not re.search(r'[.!?”"’:]$', paras[-1]):
            paras[-1] += ' ' + r
        else:
            paras.append(r)
    return title, paras


def en_sentences(text):
    """英語の段落を文に分ける。. ! ? のあと（引用符を挟んでもよい）、空白と大文字・引用符・数字が続く所で切る。
    Mr. などの略語と、イニシャル（Il S. など1字の大文字）では切らない"""
    out, start = [], 0
    for m in re.finditer(r'[.!?][”"’\')]*\s+(?=[“"‘(\[]?[A-Z0-9])', text):
        before = text[start:m.start()]
        word = re.search(r'([A-Za-z]+)$', before)
        if text[m.start()] == '.' and word and (word.group(1) in ABBR or len(word.group(1)) == 1):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def site_sections():
    """サイトの日本語: [(題, [段落の文字列])]。序文が先頭"""
    secs = []
    pre = BeautifulSoup((SITE / 'preface.html').read_text(encoding='utf-8'), 'html.parser')
    card = pre.select_one('article.preface-card')
    secs.append(('序文', [para_text(p) for p in card.find_all('p')]))
    for f in sorted(SITE.glob('chapter-*.html')):
        soup = BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser')
        for art in soup.select('article.article-section'):
            for note in art.select('details.editor-note'):
                note.decompose()                       # サイト管理人注は本文ではない
            title = art.find('h2').get_text(strip=True)
            secs.append((title, [para_text(p) for p in art.find_all('p')]))
    return secs


def para_text(p):
    for br in p.find_all('br'):
        br.replace_with('\n')
    return re.sub(r'[ \t]+\n', '\n', p.get_text()).strip()


def main():
    # 改行しない空白（ ）が書名や英語の題に混じっているので、ふつうの空白にそろえる
    lines = SRC.read_text(encoding='utf-8').replace(' ', ' ').splitlines()
    trios = file_blocks(lines)
    site = site_sections()
    assert len(site) == 68, len(site)
    # 序文の韓国語（ファイルの頭。題の行のあと、目次の手前まで）
    end = next(i for i, l in enumerate(lines) if '목차' in l)
    pre_ko = [l.strip() for l in lines[1:end] if l.strip()]
    report = []
    OUT.mkdir(parents=True, exist_ok=True)
    chap_sec = []
    for f in sorted(SITE.glob('chapter-*.html')):
        n = len(BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser').select('article.article-section'))
        chap_sec += [(int(f.stem[-2:]), k) for k in range(1, n + 1)]
    fi = 0
    total = {'ko': 0, 'ja': 0, 'en': 0}
    OUT_EN = HERE / 'work' / 'sections-en'
    OUT_EN.mkdir(parents=True, exist_ok=True)
    for no in range(0, 68):
        title_ja, paras = site[no]
        sec = {'no': no, 'ch': 0 if no == 0 else chap_sec[no - 1][0], 'sec': 0 if no == 0 else chap_sec[no - 1][1],
               'title': {'ja': title_ja, 'ko': '', 'en': ''}, 'ko': [], 'ja': [], 'en': [],
               'ko_missing': no in MISSING, 'en_missing': no in MISSING or no == 0}
        if no == 0:
            sec['title']['ko'] = '서문'
            sec['ko'] = [{'n': k, 't': t} for k, t in enumerate(pre_ko, 1)]
        elif no not in MISSING:
            ko, ja_file, en = trios[fi]
            fi += 1
            title, pieces, probs = ko_pieces(ko)
            sec['title']['ko'] = title or ''
            sec['ko'] = pieces
            # 英語（英語版）。文に分けて E1, E2 … と番号を振る。[pN] は英語版の段落
            en_title, en_ps = en_paras(en)
            sec['title']['en'] = en_title or ''
            s = 0
            for pi, para in enumerate(en_ps, 1):
                for t in en_sentences(para):
                    s += 1
                    sec['en'].append({'s': s, 'p': pi, 't': t})
            left = sorted({w for x in sec['en'] for w in re.findall(r'\b[a-z]+\.[a-z]+\b', x['t'])} - {'a.m', 'p.m'})
            if left:
                report.append(f'{no:02d} 英語に崩れの残り: {left}')
            for p in probs:
                report.append(f'{no:02d} {p}')
            # ファイルの日本語とサイトの日本語が同じ節か（本文の頭で比べる）
            fj = ''.join(r.strip() for r in ja_file['rows'] if kind(r) == 'ja')
            sj = ''.join(paras)
            r = difflib.SequenceMatcher(None, re.sub(r'\s', '', fj)[:600], re.sub(r'\s', '', sj)[:600], autojunk=False).ratio()
            if r < 0.6:
                report.append(f'{no:02d} ファイルとサイトの日本語の頭が合わない（{r:.2f}）: {title} / {title_ja}')
        s = 0
        for pi, para in enumerate(paras, 1):
            for t in ja_sentences(para):
                s += 1
                sec['ja'].append({'s': s, 'p': pi, 't': t})
        total['ko'] += len(sec['ko'])
        total['ja'] += len(sec['ja'])
        total['en'] += len(sec['en'])
        (OUT / f'{no:02d}.json').write_text(json.dumps(sec, ensure_ascii=False, indent=1), encoding='utf-8')
        # 韓英の対応付けのための一覧
        txt = [f'# {no:02d}  {sec["ch"]}章{sec["sec"]}節  {sec["title"]["ko"]} / {sec["title"]["en"]}', '',
               '## 韓国語（原文）' + ('  ※元のファイルに無い' if sec['ko_missing'] else '')]
        txt += [f'K{x["n"]}: {x["t"]}' for x in sec['ko']]
        txt += ['', '## 英語（英語版の訳。[pN] は段落）' + ('  ※元のファイルに無い' if sec['en_missing'] else '')]
        txt += [f'E{x["s"]} [p{x["p"]}]: {x["t"]}' for x in sec['en']]
        (OUT_EN / f'{no:02d}.txt').write_text('\n'.join(txt) + '\n', encoding='utf-8')
        txt = [f'# {no:02d}  {sec["ch"]}章{sec["sec"]}節  {sec["title"]["ko"]} / {sec["title"]["ja"]}', '',
               '## 韓国語（原文）' + ('  ※元のファイルに無い' if sec['ko_missing'] else '')]
        txt += [f'K{x["n"]}: {x["t"]}' for x in sec['ko']]
        txt += ['', '## 日本語（サイトの訳。[pN] は段落）']
        txt += [f'J{x["s"]} [p{x["p"]}]: {x["t"]}' for x in sec['ja']]
        (OUT / f'{no:02d}.txt').write_text('\n'.join(txt) + '\n', encoding='utf-8')
    assert fi == len(trios), (fi, len(trios))
    report.append(f'節 68（序文＋67）、韓国語 {total["ko"]} かたまり、日本語 {total["ja"]} 文、英語 {total["en"]} 文')
    (HERE / 'work' / 'prepare-report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report[-40:]))


if __name__ == '__main__':
    main()

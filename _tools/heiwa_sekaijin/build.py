# -*- coding: utf-8 -*-
"""『平和を愛する世界人として』の対訳を taiyaku/heiwa_sekaijin/ に書き出す。

ビューアは祝福家庭と理想天国の三か国語対訳（taiyaku/syuku_risoutengoku/index.html）をそのまま写し、
本の名前・出典・設定の保存先（localStorage の heiwa.〜）などを差し替える（patch_viewer）。
いまは韓・日の2列（第1段）。英語は第2段で足す。

行の作り方: 対応表（work/align/NN.json）の1組が1つの塊。日本語の欄は、公式の訳の文の続きと、
日本語に無い韓国語の AI 訳（work/trans/ja/*.json）を、それぞれ別の行（セル）にする。韓国語のセルは
その塊の行をまたぐ（span）。AI 訳のセルには ai 印（画面で札と「AI訳」ボタン）、韓国語の順に合わせて
動かした公式の訳のセルには mv 印（⇄ 順番移動）が付く。

    python _tools/heiwa_sekaijin/build.py
"""
import datetime
import json
import pathlib
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # python -I でも隣の frags.py を読む
import frags  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEC = HERE / 'work' / 'sections'
ALIGN = HERE / 'work' / 'align'
OUT = ROOT / 'taiyaku' / 'heiwa_sekaijin'
VIEWER = ROOT / 'taiyaku' / 'syuku_risoutengoku' / 'index.html'
SITE = ROOT / 'heiwa_sekaijin'
BOOK = {'ko': '평화를 사랑하는 세계인으로', 'ja': '平和を愛する世界人として', 'en': 'As a Peace-Loving Global Citizen'}
NUM = '〇一二三四五六七'
MISSING_WARN = {
    'ja': 'この節は、韓国語・英語の元データにありません（日本語の公式の訳だけです）',
    'ko': '이 절은 한국어·영어 원본 데이터에 없습니다 (일본어 공식 번역만 있습니다)',
    'en': 'This section is missing from the Korean and English source data (official Japanese only)',
}


def chapter_titles():
    """{章: {ko, ja}}。韓国語は元のファイルの目次、日本語はサイトの章のページの h1"""
    lines = (HERE / 'src' / 'ko-ja-en.txt').read_text(encoding='utf-8').replace('\xa0', ' ').splitlines()
    ko = {}
    for l in lines[:120]:
        m = re.match(r'^(\d)장\s+(.+)$', l.strip())
        if m:
            ko[int(m.group(1))] = l.strip()
    ja = {}
    for f in sorted(SITE.glob('chapter-*.html')):
        h = BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser').select_one('header.chapter-header h1')
        ja[int(f.stem[-2:])] = h.get_text(strip=True)
    return {c: {'ko': ko.get(c, ''), 'ja': ja.get(c, '')} for c in range(1, 8)}


def ko_toc_titles():
    """{(章, 節): 「1. 아버지 등에 업혀 배운 평화」}。元のファイルの頭の目次から。
    本文の韓国語の塊に節の題の行が無い節（1章3節〜2章1節）は、これを使う"""
    lines = (HERE / 'src' / 'ko-ja-en.txt').read_text(encoding='utf-8').replace('\xa0', ' ').splitlines()
    out, ch = {}, 0
    for l in lines[:120]:
        t = l.strip()
        m = re.match(r'^(\d)장\s', t)
        if m:
            ch = int(m.group(1))
            continue
        m = re.match(r'^(\d+)\.\s*(.+)$', t)
        if m and ch:
            out[(ch, int(m.group(1)))] = f'{m.group(1)}. {m.group(2).strip()}'
    return out


SKIP = re.compile(r'[\s"“”\'‘’]')       # check_align.py の flat() と同じく、空白と引用符は数えない
SENT_END = re.compile(r'[.?!。…]')


def ko_spans(flat, runs):
    """1つの組の韓国語（空白と引用符を抜いた flat）を、その組の訳の続き（runs）ごとに割り当てた範囲 [(a, b)]。
    AI 訳の続きには、そのもとの韓国語（{"ko"} の字）の範囲を、公式の訳の続きには、そのあいだの範囲を当てる。
    もとの韓国語が見つからない・順に並んでいない・どこにも当たらない韓国語が残るときは None"""
    spans, cur = [], 0
    for r in runs:
        if r['kind'] != 'ai':
            spans.append(None)
            continue
        start = None
        for x in r['items']:
            f = SKIP.sub('', x['ko'])
            k = flat.find(f, cur)
            if k < 0 or (start is not None and k != cur):
                return None
            if start is None:
                start = k
            cur = k + len(f)
        # 文の途中から始まる AI 訳で、文の頭が「나는」ほどしか残らないときは、その頭も AI 訳の行へ寄せる
        # （前の行の終わりに「나는」だけがぶら下がらないように）
        m = max((x.end() for x in SENT_END.finditer(flat, 0, start)), default=0)
        prev = next((s for s in reversed(spans) if s is not None), None)
        if 0 < start - m <= 3 and (prev is None or prev[1] <= m):
            start = m
        spans.append((start, cur))
    for i, sp in enumerate(spans):
        if sp is None:
            a = spans[i - 1][1] if i > 0 else 0
            b = spans[i + 1][0] if i + 1 < len(spans) and spans[i + 1] is not None else len(flat)
            if b < a:
                return None
            spans[i] = (a, b)
    if spans[0][0] != 0 or spans[-1][1] != len(flat):
        return None
    for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
        if b1 != a2:
            return None
    return spans


def lang_runs(groups, L):
    """訳の言語 L の組を、公式の訳（off）と AI 訳（ai）の続きに分ける。組をまたいではつながない"""
    runs = []
    for g in groups:
        cur = []
        for x in g[L]:
            kind = 'off' if isinstance(x, int) else 'ai'
            if cur and cur[-1]['kind'] == kind:
                cur[-1]['items'].append(x)
            else:
                cur.append({'kind': kind, 'items': [x], 'g': g})
        runs += cur or [{'kind': 'off', 'items': [], 'g': g}]
    return runs


def rows_of(sec, als, trans):
    """1節ぶんの cells（ko・ja・en）と行の数。
    韓国語は、日本語と英語の両方の AI 訳の切れ目で行に切る。訳の公式の訳・AI 訳のセルは、もとの韓国語の行をまたぐ。
    塊（block）は、日本語の組と英語の組の切れ目がそろう所まで"""
    langs = [L for L in ('ja', 'en') if als.get(L) and sec.get(L) is not None]
    ko = {x['n']: x['t'] for x in sec['ko']}
    cells = {'ko': [], 'ja': [], 'en': []}
    seen_max = {L: 0 for L in langs}
    if not sec['ko']:
        # 韓国語の無い節（6章7節）。訳の続きを1行ずつ並べるだけ
        r = 0
        for L in langs:
            r = 0
            for run in lang_runs(als[L]['groups'], L):
                cells[L].append(cell_of(sec, L, run, r, 1, trans, seen_max))
                r += 1
        return cells, max(r, 1)
    # 組の切れ目（韓国語の番号の最後）。両方の言語で切れる所が塊の切れ目
    ends = {L: {g['ko'][-1] for g in als[L]['groups'] if g['ko']} for L in langs}
    cut_at = set.intersection(*ends.values()) if ends else set()
    blocks, cur = [], []
    for n in sorted(ko):
        cur.append(n)
        if n in cut_at:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    # 組を塊に割り振る。韓国語の無い組（訳だけの組）は、直前の組と同じ塊に入れる
    block_of = {n: i for i, nums in enumerate(blocks) for n in nums}
    owned = {L: [[] for _ in blocks] for L in langs}
    for L in langs:
        last = 0
        for g in als[L]['groups']:
            b = block_of[g['ko'][0]] if g['ko'] else last
            owned[L][b].append(g)
            last = b
    r0 = 0
    for bi, nums in enumerate(blocks):
        whole = '\n'.join(ko[n] for n in nums)
        pos = [i for i, ch in enumerate(whole) if not SKIP.match(ch)]
        F = len(pos)
        flat_blk = ''.join(whole[i] for i in pos)
        # 言語ごとに、続きの範囲（塊の flat の座標）を出す
        lruns = {}
        for L in langs:
            runs_all, off = [], 0
            for g in owned[L][bi]:
                gflat = ''.join(SKIP.sub('', ko[n]) for n in g['ko'])
                runs = lang_runs([g], L)
                sp = ko_spans(gflat, runs) if g['ko'] else None
                if sp is None:
                    # 切り分けられない組は、最初の続きに組の韓国語ぜんぶ、残りは幅0（下へ並ぶ）
                    sp = [(0, len(gflat))] + [(len(gflat), len(gflat))] * (len(runs) - 1)
                for run, (a, b) in zip(runs, sp):
                    run['a'], run['b'] = off + a, off + b
                runs_all += runs
                off += len(gflat)
            # 文の途中の切れ目（訳書が語句だけを省いた所）では韓国語の文を切らない。
            # 前後の公式の訳と AI 訳を1つのセルにまとめ、AI 訳はセルの中に色を変えて差し込む
            merged = []
            for run in runs_all:
                prev = merged[-1] if merged else None
                if (prev and prev['g'] is run['g'] and 0 < run['a'] < F
                        and not SENT_END.match(flat_blk[run['a'] - 1])):
                    prev['kind'] = 'mix'
                    prev['items'] = prev['items'] + run['items']
                    prev['b'] = run['b']
                else:
                    merged.append(run)
            lruns[L] = merged
        # 行を作る。どちらかの言語の続きの切れ目で行を切る。幅0の続きは、それだけで1行
        rows = []                  # [(a, b)]
        span_of = {}               # id(run) -> [最初の行, 最後の行]
        idx = {L: 0 for L in langs}
        p = 0
        while any(idx[L] < len(lruns[L]) for L in langs):
            zero = [L for L in langs if idx[L] < len(lruns[L])
                    and lruns[L][idx[L]]['a'] == lruns[L][idx[L]]['b'] == p]
            if zero:
                rows.append((p, p))
                for L in langs:
                    if idx[L] < len(lruns[L]):
                        run = lruns[L][idx[L]]
                        span_of.setdefault(id(run), [len(rows) - 1, len(rows) - 1])[1] = len(rows) - 1
                for L in zero:
                    idx[L] += 1
                continue
            cut = min(lruns[L][idx[L]]['b'] for L in langs if idx[L] < len(lruns[L]))
            if cut <= p:
                cut = F if F > p else p + 1
            rows.append((p, cut))
            for L in langs:
                if idx[L] < len(lruns[L]):
                    run = lruns[L][idx[L]]
                    span_of.setdefault(id(run), [len(rows) - 1, len(rows) - 1])[1] = len(rows) - 1
                    if run['b'] <= cut:
                        idx[L] += 1
            p = cut
        if not rows:
            rows = [(0, F)]
        # 韓国語のセル。空の行は、すぐ上の韓国語のセルが受け持つ（先頭なら次のセル）
        texts = [whole[pos[a]:pos[b - 1] + 1].strip() if b > a else '' for a, b in rows]
        filled = [i for i, t in enumerate(texts) if t]
        ko_cells = []
        for k, i in enumerate(filled):
            start = 0 if k == 0 else i
            end = filled[k + 1] if k + 1 < len(filled) else len(rows)
            ko_cells.append({'r': r0 + start, 'span': end - start, 't': texts[i]})
        cells['ko'] += ko_cells
        # 訳のセル
        for L in langs:
            lastrow = -1
            for run in lruns[L]:
                a, b = span_of.get(id(run), [lastrow + 1, lastrow + 1])
                cells[L].append(cell_of(sec, L, run, r0 + a, b - a + 1, trans, seen_max))
                lastrow = b
            notes_of(L, lruns[L], cells[L], cells['ko'])
        r0 += len(rows)
    return cells, r0


ONLY_TAG = {'ja': '点線の文は日本語版のみ（原文に無い）', 'en': 'Dotted: English edition only (not in the Korean)'}
ONLY_BADGE = {'ja': '日本語版のみ', 'en': 'English edition only'}   # 点線の文の頭に付ける札
ONLY_KO = {'ja': '※ 일본어판에만 있는 문장 (일본어에서 AI 번역): ', 'en': '※ 영어판에만 있는 문장 (영어에서 AI 번역): '}
AISEG_TAG = {'ja': '色付きの所は韓国語からの AI訳', 'en': 'Shaded: AI translation from Korean'}


def cell_of(sec, L, run, r, span, trans, seen_max):
    """訳の続き1つのセル。公式の訳は文をつなぎ（段落が変われば改行）、その言語版にしか無い文に印。AI 訳は ai 印。
    公式の訳と AI 訳がまざる続き（mix）は、AI 訳の所を seg の ai で印す"""
    sep = '' if L == 'ja' else ' '
    if run['kind'] == 'ai':
        parts = [trans[L].get(frags.key(sec['no'], x['ko'])) for x in run['items']]
        c = {'r': r, 'span': span, 't': sep.join(p if p else '〔訳待ち〕' for p in parts), 'ai': 1}
        run['cell'] = c
        return c
    sents = {x['s']: x for x in sec[L]}
    only = set(run['g'].get(f'{L}_only', []))
    seg, prev_p, moved = [], None, False
    for x in run['items']:
        if isinstance(x, dict):
            t = trans[L].get(frags.key(sec['no'], x['ko'])) or '〔訳待ち〕'
            kind = 'ai'
            if seg:
                t = sep + t
        else:
            if x < seen_max[L]:
                moved = True
            seen_max[L] = max(seen_max[L], x)
            t = sents[x]['t']
            if prev_p is not None and sents[x]['p'] != prev_p:
                t = '\n' + t
            elif seg:
                t = sep + t
            kind = 'jo' if x in only else ''
            prev_p = sents[x]['p']
        if seg and seg[-1]['k'] == kind:
            seg[-1]['t'] += t
        else:
            seg.append({'t': t, 'k': kind})
    c = {'r': r, 'span': span, 't': ''.join(x['t'] for x in seg)}
    if any(x['k'] for x in seg):
        c['seg'] = [{'t': x['t'], x['k']: 1} if x['k'] else {'t': x['t']} for x in seg]
    if any(x['k'] == 'jo' for x in seg):
        c['jot'] = ONLY_TAG[L]
        c['jol'] = ONLY_BADGE[L]
    if any(x['k'] == 'ai' for x in seg):
        c['ait'] = AISEG_TAG[L]
    if moved:
        c['mv'] = 1
    run['cell'] = c
    return c


def notes_of(L, runs, lcells, kocells):
    """読む人向けの注。書き換え（diff）は、その組の最後の公式の訳のセルの下に。
    その言語版にしか無い文の韓国語訳は、その文のある行の韓国語のセルの下に"""
    by_group = {}
    for run in runs:
        by_group.setdefault(id(run['g']), (run['g'], []))[1].append(run)
    for g, rs in by_group.values():
        cs = [r['cell'] for r in rs if 'cell' in r]
        if not cs:
            continue
        if g.get('diff'):
            target = next((c for c in reversed(cs) if not c.get('ai')), cs[-1])
            target.setdefault('notes', []).extend('※' + d for d in g['diff'])
        if g.get(f'{L}_only_ko') and g['ko']:
            row = next((c['r'] for c in cs if any(x.get('jo') for x in c.get('seg', []))), cs[-1]['r'])
            home = next((c for c in kocells if c['r'] <= row < c['r'] + c['span']), None)
            if home:
                home.setdefault('notes', []).append(ONLY_KO[L] + g[f'{L}_only_ko'])


def section_key(sec):
    return 'pre' if sec['no'] == 0 else f'{sec["ch"]}-{sec["sec"]}'


def patch_viewer(src, with_en=False):
    """祝福家庭と理想天国のビューアを、この本向けに書き換える。どの差し替えも当たらなければ止まる"""
    s = src
    T_JA, T_KO, T_EN = (('韓日英 三か国語対訳', '한일영 3개국어 대역', 'Korean–Japanese–English Parallel') if with_en
                        else ('韓日対訳', '한일 대역', 'Korean–Japanese Parallel'))
    reps = [
        ('<title>祝福家庭と理想天国 三か国語対訳</title>', f'<title>平和を愛する世界人として {T_JA}</title>'),
        ('<meta property="og:title" content="祝福家庭と理想天国 三か国語対訳">',
         f'<meta property="og:title" content="平和を愛する世界人として {T_JA}">'),
        ('title: "祝福家庭と理想天国 三か国語対訳", brand: "訓読 対訳",',
         f'title: "平和を愛する世界人として {T_JA}", brand: "自叙伝 対訳",'),
        ('title: "축복가정과 이상천국 3개국어 대역", brand: "훈독 대역",',
         f'title: "평화를 사랑하는 세계인으로 {T_KO}", brand: "자서전 대역",'),
        ('title: "Blessing and Ideal Family — Three-Language Parallel", brand: "Hoondok Parallel",',
         f'title: "As a Peace-Loving Global Citizen — {T_EN}", brand: "Autobiography Parallel",'),
        ('foot: (links) => `出典: Daum カフェ「천일국 경전방」の各記事（${links}）。`\n'
         '        + `段落の対応づけは文字数から機械的に推定したものです。ずれていたら元記事で確かめてください。`,',
         'foot: (links) => `韓国語・英語: み言選集の資料「평화를 사랑하는 세계인으로 (한.日.Eng.)」。日本語: 日本語版（み旨の裏庭の${links}）。`\n'
         '        + `日本語版・英語版で省かれている所は、韓国語から訳した AI 参考訳で補っています（公式訳ではありません。「AI訳」ボタンで消せます）。`\n'
         '        + `訳書が中身を書き換えている所と、訳書にしか無い文には「※」の注を付けました。`,'),
        ('foot: (links) => `출처: 다음 카페 「천일국 경전방」의 각 글 (${links}). `\n'
         '        + `문단 짝짓기는 글자 수를 바탕으로 기계가 추정한 것입니다. 어긋나 보이면 원글에서 확인해 주십시오.`,',
         'foot: (links) => `한국어·영어: 말씀선집 자료 「평화를 사랑하는 세계인으로 (한.日.Eng.)」. 일본어: 일본어판 (${links}). `\n'
         '        + `일본어판·영어판에서 생략된 부분은 한국어에서 옮긴 AI 참고 번역으로 채웠습니다 (공식 번역이 아닙니다. 「AI 번역」 버튼으로 숨길 수 있습니다). `\n'
         '        + `번역판이 내용을 바꾼 곳과 번역판에만 있는 문장에는 「※」 주를 달았습니다.`,'),
        ('foot: (links) => `Source: the posts in the Daum cafe "천일국 경전방" (${links}). `\n'
         '        + `The paragraph pairing is estimated mechanically from text length; if it looks off, check the original post.`,',
         'foot: (links) => `Korean and English: the source text "평화를 사랑하는 세계인으로 (한.日.Eng.)". Japanese: the Japanese edition (${links}). `\n'
         '        + `Passages left out of the Japanese or English edition are filled with AI reference translations from the Korean (not the official text; hide them with the AI button). `\n'
         '        + `Notes marked ※ point out where a translation changes the content, and sentences found only in a translation.`,'),
        ('wMoved: "⇄印の英語は、対訳のため翻訳版の掲載順から移動してあります",',
         'wMoved: "⇄印の訳文は、韓国語の順に合わせるため、訳書（日本語版・英語版）の順番から移動してあります",'),
        ('mvTitle: "対訳のため、翻訳版に掲載されていた順番から移動してあります",',
         'mvTitle: "韓国語の順に合わせるため、訳書の順番から移動してあります",\n'
         '      joTag: "日本語版のみの文（点線）", joT: "点線の文は、その欄の訳書（日本語版・英語版）にだけあり、韓国語の原文にはありません",\n'
         '      aiSegTag: "色付きの所は AI訳", aiSegT: "色付きの所は訳書で省かれていた語句を、韓国語から AI が訳したものです（公式訳ではありません。「AI訳」ボタンで消せます）",'),
        ('wMoved: "⇄ 표시가 붙은 영어는 대역을 맞추기 위해 번역판의 실린 순서에서 옮긴 것입니다",',
         'wMoved: "⇄ 표시가 붙은 번역문은 한국어 순서에 맞추기 위해 번역판(일본어판·영어판)의 순서에서 옮긴 것입니다",'),
        ('mvTitle: "대역을 맞추기 위해, 번역판에 실려 있던 순서에서 옮겼습니다",',
         'mvTitle: "한국어 순서에 맞추기 위해 번역판의 순서에서 옮겼습니다",\n'
         '      joTag: "일본어판에만 있는 문장 (점선)", joT: "점선 문장은 그 칸의 번역판(일본어판·영어판)에만 있고 한국어 원문에는 없습니다",\n'
         '      aiSegTag: "색 바탕은 AI 번역", aiSegT: "색 바탕 부분은 번역판에서 생략된 어구를 한국어에서 AI가 옮긴 것입니다 (공식 번역이 아닙니다. 「AI 번역」 버튼으로 숨길 수 있습니다)",'),
        ('wMoved: "English cells marked ⇄ were moved out of the order of the translated post so that they line up",',
         'wMoved: "Translation cells marked ⇄ were moved out of the order of the Japanese or English edition to follow the Korean",'),
        ('mvTitle: "Moved out of the order in which it appeared in the translated post, so that it lines up",',
         'mvTitle: "Moved out of the order of the translated edition to follow the Korean",\n'
         '      joTag: "Japanese edition only (dotted)", joT: "Dotted sentences appear only in the translated edition of that column (Japanese or English), not in the Korean original",\n'
         '      aiSegTag: "Shaded: AI translation", aiSegT: "Shaded words were left out of the translated edition and are an AI translation from the Korean (not the official text; hide them with the AI button)",'),
        ('if ((s.cells.en || []).some((c) => c.mv)) warn.push(t.wMoved);',
         'if ([...(s.cells.ja || []), ...(s.cells.en || [])].some((c) => c.mv)) warn.push(t.wMoved);\n'
         '    if (s.warn) warn.push(s.warn[ui] || s.warn.ja);'),
        # 韓国語のセルがまたぐ行は、日本語の公式の訳と AI 訳の切れ目。「N段落ぶん」とは言わない
        ('spanTag: (n) => `・ ${n}段落ぶん`,', 'spanTag: () => "",'),
        ('spanTag: (n) => `・ ${n}문단 분량`,', 'spanTag: () => "",'),
        ('spanTag: (n) => `· ${n} paragraphs`,', 'spanTag: () => "",'),
        # 序文の英語は元データに無い（「投稿されていない」は Daum の掲示板から作った祝福家庭と理想天国の言い方）
        ('wAisec: (l) => `${l}版はこの節が投稿されていません。${l}の欄は全文が韓国語からの AI 参考訳です（公式訳ではありません。「AI訳」ボタンで消せます）`,',
         'wAisec: (l) => `${l}版のこの節は元データにありません。${l}の欄は全文が韓国語からの AI 参考訳です（公式訳ではありません。「AI訳」ボタンで消せます）`,'),
        ('wAisec: (l) => `${l}판에는 이 절이 올라와 있지 않습니다. ${l} 칸은 전문이 한국어에서 옮긴 AI 참고 번역입니다 (공식 번역이 아닙니다. 「AI 번역」 단추로 숨길 수 있습니다)`,',
         'wAisec: (l) => `${l}판의 이 절은 원본 데이터에 없습니다. ${l} 칸은 전문이 한국어에서 옮긴 AI 참고 번역입니다 (공식 번역이 아닙니다. 「AI 번역」 단추로 숨길 수 있습니다)`,'),
        ('wAisec: (l) => `This section was never posted in ${l}. The whole ${l} column is an AI reference translation from the Korean (not the official text; hide it with the "AI" button)`,',
         'wAisec: (l) => `This section of the ${l} edition is missing from the source data. The whole ${l} column is an AI reference translation from the Korean (not the official text; hide it with the "AI" button)`,'),
        # 日本語版にしか無い文（seg の jo）に点線と札、セルの下に ※ の注（notes）
        ('        + (c.mv ? `<span class="mvtag" title="${esc(t.mvTitle)}">${t.mvTag}</span>` : "")\n',
         '        + (c.mv ? `<span class="mvtag" title="${esc(t.mvTitle)}">${t.mvTag}</span>` : "")\n'
         '        + ((c.seg || []).some((g) => g.jo) ? `<span class="mvtag" title="${esc(t.joT)}">${esc(c.jot || t.joTag)}</span>` : "")\n'
         '        + ((c.seg || []).some((g) => g.ai) ? `<span class="mvtag aisegtag" title="${esc(t.aiSegT)}">${esc(c.ait || t.aiSegTag)}</span>` : "")\n'),
        ('      + (c.t ? `<span class="body">${esc(c.t)}</span>`',
         '      + (c.t ? `<span class="body">${c.seg ? c.seg.map((g) => g.jo ? g.t.replace(/^(\\s*)([\\s\\S]*)$/, (m, sp, x) =>\n'
         '              `${esc(sp)}<span class="jaonly"><span class="jobadge" title="${esc(t.joT)}">${esc(c.jol || t.joTag)}</span>${esc(x)}</span>`)\n'
         '          : g.ai ? `<span class="aiseg" title="${esc(t.aiSegT)}">${esc(g.t)}</span>` : esc(g.t)).join("") : esc(c.t)}</span>`'),
        # コピーする本文: セルの中の AI 訳は、隠しているときは入れず、出しているときは〔AI: …〕で囲む
        ('        out.push((c.ai && !ai ? `〔${AITAG[L.id]}〕\\n` : "") + c.t.trim());',
         '        const body = c.seg ? c.seg.filter((g) => showAI || !g.ai)\n'
         '          .map((g) => g.ai ? g.t.replace(/^(\\s*)([\\s\\S]*)$/, "$1〔AI: $2〕") : g.t).join("") : c.t;\n'
         '        out.push((c.ai && !ai ? `〔${AITAG[L.id]}〕\\n` : "") + body.trim());'),
        ('      + (c.w ? briefBox(c.w) : "");',
         '      + (c.w ? briefBox(c.w) : "")\n'
         '      + (c.notes || []).map((n) => `<span class="cnote">${esc(n)}</span>`).join("");'),
    ]
    if not with_en:   # 英語の対応表がまだ無いときは、韓・日の2列
        reps.append(('    { id: "en", label: "English", tag: "EN" },\n', ''))
    for a, b in reps:
        n = s.count(a)
        assert n == 1, f'{n} 回: {a[:60]}'
        s = s.replace(a, b)
    # description と og:description の2つ
    desc = 'content="韓国語・日本語・英語を段落ごとに並べて読める対訳です。"'
    assert s.count(desc) == 2, s.count(desc)
    s = s.replace(desc, 'content="文鮮明先生の自叙伝『平和を愛する世界人として』の韓国語原文と日本語訳を、段落ごとに並べて読める対訳です。"')
    n = s.count('taiyaku/syuku_risoutengoku/index.html')
    assert n == 2, n
    s = s.replace('taiyaku/syuku_risoutengoku/index.html', 'taiyaku/heiwa_sekaijin/index.html')
    n = s.count('hoondok.')
    assert n >= 3, n
    s = s.replace('hoondok.', 'heiwa.')
    # 区切り（小見出しと出典の切れ目に太線）はこの本には無いので、ボタンを出さない
    s = s.replace('</style>', '  #brk{display:none}\n'
                  '  .cell .cnote{display:block;margin-top:.6em;font-size:.82em;line-height:1.65;color:var(--muted)}\n'
                  '  .cell .jaonly{text-decoration:underline dotted var(--markline);text-decoration-thickness:2px;text-underline-offset:.3em}\n'
                  '  .cell .jobadge{display:inline-block;font-size:.66em;line-height:1.55;padding:0 .55em;margin-right:.4em;\n'
                  '    border:1px solid var(--markline);border-radius:999px;color:var(--markline);vertical-align:.15em;white-space:nowrap}\n'
                  '  .cell .aiseg{color:var(--muted);background:color-mix(in srgb,var(--mark) 45%,transparent);\n'
                  '    border-radius:3px;padding:0 .15em;-webkit-box-decoration-break:clone;box-decoration-break:clone}\n'
                  '  .cell .aisegtag{color:var(--markline)}\n'
                  '  body.hideai .cell .aiseg,body.hideai .cell .aisegtag{display:none}\n'
                  '</style>', 1)
    return s


def en_chapter_titles():
    """{章: 英語の章の題}。元のファイルの英語の塊の頭の「CHAPTER ONE - Food is Love」から"""
    lines = (HERE / 'src' / 'ko-ja-en.txt').read_text(encoding='utf-8').replace('\xa0', ' ').splitlines()
    out, words = {}, ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN']
    for l in lines:
        m = re.match(r'^CHAPTER\s+(\w+)\s*[-–—]\s*(.+)$', l.strip(), re.I)
        if m and m.group(1).upper() in words:
            out.setdefault(words.index(m.group(1).upper()) + 1, l.strip())
    return out


# 英語の元ファイルの乱れ。画面に出さない文（E の番号）と、本文に紛れていた節の題
DROP_EN = {
    15: {40, 41},                  # 2-8 の E44・E45 と同じ2文が紛れ込んでいる（本物は 16 の方）
    28: {1, 2, 3},                 # 章の題・節の番号・節の題が本文の頭に入っていた
    32: {1, 2, 58, 59, 60, 61},    # 節の番号と題／E54〜E57 と同じ4文がもう一度
    67: set(range(56, 91)),        # 5-3（思春期の話）の英語 35文がそのまま紛れ込んでいる
    42: {1}, 43: {1},              # 節の題の2行目が本文の頭に入っていた
}
EN_TITLE_FIX = {28: '1. Paying the Ultimate Price to Follow God’s Path', 32: '5. Our Future Lies with the Ocean',
                42: '5. The Peaceful Family Is the Building Block of Heaven',
                43: '6. Ten Years of Tears Melt a Father-in-Law’s Heart'}


def drop_en(sec, al):
    """DROP_EN の文を対応表から外す。英語の文が無くなった、韓国語の無い組は消す"""
    drop = DROP_EN.get(sec['no'], set())
    if sec['no'] in EN_TITLE_FIX:
        sec['title']['en'] = EN_TITLE_FIX[sec['no']]
    if not drop:
        return al
    groups = []
    for g in al['groups']:
        g = dict(g, en=[x for x in g['en'] if not (isinstance(x, int) and x in drop)])
        if g['ko'] or g['en']:
            groups.append(g)
    return dict(al, groups=groups)


def main():
    trans = {L: frags.done(L) for L in ('ja', 'en')}
    chap = chapter_titles()
    chap_en = en_chapter_titles()
    toc_ko = ko_toc_titles()
    secs = []
    (OUT / 'data').mkdir(parents=True, exist_ok=True)
    with_en = any((HERE / 'work' / 'align-en').glob('*.json'))
    for f in sorted(SEC.glob('*.json')):
        sec = json.loads(f.read_text(encoding='utf-8'))
        als = {'ja': json.loads((ALIGN / f.name).read_text(encoding='utf-8'))}
        en_path = HERE / 'work' / 'align-en' / f.name
        if with_en and en_path.exists():
            als['en'] = drop_en(sec, json.loads(en_path.read_text(encoding='utf-8')))
        cells, n = rows_of(sec, als, trans)
        key = section_key(sec)
        no, ch = sec['no'], sec['ch']
        if sec['ko'] and not sec['title']['ko']:
            sec['title']['ko'] = toc_ko.get((ch, sec['sec']), '')
        if no == 0:
            label = '序文'
            titles = {'ko': f'{BOOK["ko"]} - 서문', 'ja': f'{BOOK["ja"]} - 序文', 'en': f'{BOOK["en"]} - Preface'}
            header = {'ko': [BOOK['ko'], '서문'], 'ja': [BOOK['ja'], '序文'], 'en': [BOOK['en'], 'Preface']}
            url = '../../heiwa_sekaijin/preface.html'
        else:
            label = f'第{NUM[ch]}章 {ch}-{sec["sec"]}'
            t_en = sec['title'].get('en', '')
            titles = {'ko': f'{BOOK["ko"]} - {chap[ch]["ko"]} - {sec["title"]["ko"]}' if sec['title']['ko'] else '',
                      'ja': f'{BOOK["ja"]} - {chap[ch]["ja"]} - {sec["title"]["ja"]}',
                      'en': f'{BOOK["en"]} - {chap_en.get(ch, "")} - {t_en}' if t_en else ''}
            header = {'ko': [BOOK['ko'], chap[ch]['ko'], sec['title']['ko']] if sec['title']['ko'] else [],
                      'ja': [BOOK['ja'], chap[ch]['ja'], sec['title']['ja']],
                      'en': [BOOK['en'], chap_en.get(ch, ''), t_en] if t_en else []}
            url = f'../../heiwa_sekaijin/chapter-{ch:02d}.html#section-{sec["sec"]:02d}'
        langs = [L for L in ('en', 'ja', 'ko') if cells.get(L)]
        entry = {'key': key, 'label': label, 'titles': titles, 'urls': {'ja': url}, 'header': header, 'n': n,
                 'counts': {L: len(sec.get(L, [])) for L in ('ko', 'ja', 'en')}, 'langs': langs}
        if sec['ko_missing']:
            entry['warn'] = MISSING_WARN
        elif 'en' in als and sec.get('en_missing') and cells.get('en'):
            entry['aisec'] = ['en']          # 英語版の序文は元データに無い。英語の欄はまるごと AI 訳
        secs.append(entry)
        body = json.dumps({'cells': cells}, ensure_ascii=False, separators=(',', ':'))
        (OUT / 'data' / f'{key}.js').write_text(f'window.HD.put("{key}", {body});\n', encoding='utf-8', newline='\n')
    v = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    book = json.dumps({'sections': secs, 'v': v}, ensure_ascii=False, separators=(',', ':'))
    (OUT / 'book.js').write_text(f'window.HOONDOK = {book};\n', encoding='utf-8', newline='\n')
    page = patch_viewer(VIEWER.read_text(encoding='utf-8'), with_en)
    (OUT / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    wait = sum(f.read_text(encoding='utf-8').count('〔訳待ち〕') for f in (OUT / 'data').glob('*.js'))
    print(f'{len(secs)} 節を書き出した → {OUT}（英語 {"あり" if with_en else "なし"}、訳待ち {wait} か所）')


if __name__ == '__main__':
    main()

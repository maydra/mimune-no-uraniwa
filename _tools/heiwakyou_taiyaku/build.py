# -*- coding: utf-8 -*-
"""天一国経典『平和経』の対訳を taiyaku/heiwakyou/ に書き出す。

_tools/heiwa_sekaijin/build.py（自叙伝の対訳）を写して、この本向けに直したもの。
ビューアは祝福家庭と理想天国の三か国語対訳（taiyaku/syuku_risoutengoku/index.html）を写し、
本の名前・出典・設定の保存先（localStorage の heiwakyou.〜）などを差し替える（patch_viewer）。
節の一覧は篇ごとにまとめる（optgroup）。いまは韓・日の2列。英語は次の段で足す。

行の作り方: 対応表（work/align/HHNN.json）の1組が1つの塊。日本語の欄は、公式の訳の文の続きと、
日本語に無い韓国語の AI 訳（work/trans/ja/*.json）を、それぞれ別の行（セル）にする。韓国語のセルは
その塊の行をまたぐ（span）。AI 訳のセルには ai 印（画面で札と「AI訳」ボタン）、韓国語の順に合わせて
動かした公式の訳のセルには mv 印（⇄ 順番移動）が付く。小見出しの行には h 印（太字・節の中の目次）、
日付・場所・行事の行には m 印（小さく）。

    python -I -X utf8 _tools/heiwakyou_taiyaku/build.py
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
OUT = ROOT / 'taiyaku' / 'heiwakyou'
VIEWER = ROOT / 'taiyaku' / 'syuku_risoutengoku' / 'index.html'
SITE = ROOT / 'heiwakyou'
KO_SRC = HERE / 'src' / 'UYjn.jsonl'     # _tools/cafe_books/raw/UYjn.jsonl の写し（掲示板の記事が変わっても対応表がずれないように固定）
CAFE = 'https://m.cafe.daum.net/ckatkfkdrhdqn/UYjn/'
BOOK = {'ko': '평화경', 'ja': '平和経', 'en': 'Pyeong Hwa Gyeong'}
KANJI = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
# 韓国語の掲示板には第六篇の篇の名前の行が無い。日本語版の篇の名前「理想世界の主役となる女性」は
# 同じ題の講演（0604〜0605・0607）の韓国語「이상세계의 주역이 될 여성」と同じなので、それを使う
KO_HEN_FALLBACK = {6: '이상세계의 주역이 될 여성'}


def hen_titles():
    """{篇: {ko, ja}}。日本語はサイトの目次（heiwakyou/index.html）、韓国語は記事の頭の「제1편 - 참평화의 근본원리」"""
    ja = {}
    soup = BeautifulSoup((SITE / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    for s in soup.select('summary'):
        m = re.match(r'^第(\S+?)篇\s*(.+)$', s.get_text(strip=True))
        if m and m.group(1) in KANJI:
            ja[KANJI.index(m.group(1))] = m.group(2).strip()
    ko = dict(KO_HEN_FALLBACK)
    for line in KO_SRC.read_text(encoding='utf-8').splitlines():
        r = json.loads(line)
        for p in r['paras'][:4]:
            for t in p['text'].split('\n'):
                m = re.search(r'제\s*(\d+)\s*편\s*-?\s*(.+)', t)
                if m and len(t) < 60:
                    ko.setdefault(int(m.group(1)), m.group(2).strip())
    assert sorted(ja) == sorted(ko) == list(range(1, 11)), (sorted(ja), sorted(ko))
    return {h: {'ko': ko[h], 'ja': ja[h]} for h in range(1, 11)}


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
            if cur and cur[-1]['kind'] == kind == 'off':
                cur[-1]['items'].append(x)
            else:
                cur.append({'kind': kind, 'items': [x], 'g': g})
        runs += cur or [{'kind': 'off', 'items': [], 'g': g}]
    return runs


def rows_of(sec, als, trans):
    """1講演ぶんの cells（ko・ja・en）と行の数。heiwa_sekaijin/build.py と同じ組み方。
    韓国語は、日本語と英語の両方の AI 訳の切れ目で行に切る。塊（block）は、日本語の組と英語の組の切れ目がそろう所まで"""
    langs = [L for L in ('ja', 'en') if als.get(L) and sec.get(L) is not None]
    ko = {x['n']: x['t'] for x in sec['ko']}
    kind = {x['n']: x['kind'] for x in sec['ko']}
    cells = {'ko': [], 'ja': [], 'en': []}
    seen_max = {L: 0 for L in langs}
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
    # 組を塊に割り振る。韓国語の無い組（訳だけの組）は、次の組と同じ塊に入れる（0414 の前書きは第1章の前）
    block_of = {n: i for i, nums in enumerate(blocks) for n in nums}
    owned = {L: [[] for _ in blocks] for L in langs}
    for L in langs:
        pending = []
        for g in als[L]['groups']:
            if not g['ko']:
                pending.append(g)
                continue
            b = block_of[g['ko'][0]]
            owned[L][b] += pending + [g]
            pending = []
        if pending:
            owned[L][-1] += pending
    r0 = 0
    for bi, nums in enumerate(blocks):
        whole = '\n'.join(ko[n] for n in nums)
        pos = [i for i, ch in enumerate(whole) if not SKIP.match(ch)]
        F = len(pos)
        flat_blk = ''.join(whole[i] for i in pos)
        lruns = {}
        for L in langs:
            runs_all, off = [], 0
            for g in owned[L][bi]:
                gflat = ''.join(SKIP.sub('', ko[n]) for n in g['ko'])
                runs = lang_runs([g], L)
                sp = ko_spans(gflat, runs) if g['ko'] else None
                if sp is None:
                    sp = [(0, len(gflat))] + [(len(gflat), len(gflat))] * (len(runs) - 1)
                for run, (a, b) in zip(runs, sp):
                    run['a'], run['b'] = off + a, off + b
                runs_all += runs
                off += len(gflat)
            # 文の途中の切れ目（訳書が語句だけを省いた所）では韓国語の文を切らない
            merged = []
            for run in runs_all:
                prev = merged[-1] if merged else None
                if (prev and prev['g'] is run['g'] and 0 < run['a'] < F
                        and not SENT_END.match(flat_blk[run['a'] - 1])):
                    if not prev['kind'] == run['kind'] == 'ai':
                        prev['kind'] = 'mix'
                    prev['items'] = prev['items'] + run['items']
                    prev['b'] = run['b']
                else:
                    merged.append(run)
            lruns[L] = merged
        rows = []
        span_of = {}
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
        texts = [whole[pos[a]:pos[b - 1] + 1].strip() if b > a else '' for a, b in rows]
        filled = [i for i, t in enumerate(texts) if t]
        # 小見出し・頭書きの行（[見出し]・[頭] の韓国語は1つで1組にしてある）
        mark = {}
        if len(nums) == 1 and kind[nums[0]] == 'head':
            mark = {'k': 1, 'h': 1}
        elif len(nums) == 1 and kind[nums[0]] == 'meta':
            mark = {'m': 1}
        ko_cells = []
        # 塊の頭が韓国語の無い行（日本語版にしか無い文の組。0414 の前書き）なら、そこは韓国語の欄を空ける
        # （次の韓国語のセルに受け持たせると、前書きの横に第1章の見出しが並んでしまう）
        lead = filled[0] if filled else 0
        if lead > 0 and any(not g['ko'] for L in langs for g in owned[L][bi]):
            ko_cells.append({'r': r0, 'span': lead, 't': ''})
        for k, i in enumerate(filled):
            start = 0 if k == 0 and not ko_cells else i
            end = filled[k + 1] if k + 1 < len(filled) else len(rows)
            ko_cells.append({'r': r0 + start, 'span': end - start, 't': texts[i], **mark})
        cells['ko'] += ko_cells
        for L in langs:
            lastrow = -1
            for run in lruns[L]:
                a, b = span_of.get(id(run), [lastrow + 1, lastrow + 1])
                c = cell_of(sec, L, run, r0 + a, b - a + 1, trans, seen_max)
                g = run['g']
                if len(g['ko']) == 1 and kind[g['ko'][0]] in ('head', 'meta'):
                    c.update({'h': 1} if kind[g['ko'][0]] == 'head' else {'m': 1})
                cells[L].append(c)
                lastrow = b
            notes_of(L, lruns[L], cells[L], cells['ko'])
        r0 += len(rows)
    return cells, r0


ONLY_TAG = {'ja': '点線の文は日本語版のみ（原文に無い）', 'en': 'Dotted: English edition only (not in the Korean)'}
ONLY_BADGE = {'ja': '日本語版のみ', 'en': 'English edition only'}
ONLY_KO = {'ja': '※ 일본어판에만 있는 문장 (일본어에서 AI 번역): ', 'en': '※ 영어판에만 있는 문장 (영어에서 AI 번역): '}
AISEG_TAG = {'ja': '色付きの所は韓国語からの AI訳', 'en': 'Shaded: AI translation from Korean'}


def cell_of(sec, L, run, r, span, trans, seen_max):
    """訳の続き1つのセル。heiwa_sekaijin/build.py と同じ"""
    sep = '' if L == 'ja' else ' '
    if run['kind'] == 'ai':
        parts = [trans[L].get(frags.key(sec['key'], x['ko'])) for x in run['items']]
        c = {'r': r, 'span': span, 't': sep.join(p if p else '〔訳待ち〕' for p in parts), 'ai': 1}
        run['cell'] = c
        return c
    sents = {x['s']: x for x in sec[L]}
    only = set(run['g'].get(f'{L}_only', []))
    seg, prev_p, moved = [], None, False
    for x in run['items']:
        if isinstance(x, dict):
            t = trans[L].get(frags.key(sec['key'], x['ko'])) or '〔訳待ち〕'
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
    その言語版にしか無い文の韓国語訳は、その文のある行の韓国語のセルの下に（韓国語の無い組は、次の韓国語のセルの下）"""
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
        if g.get(f'{L}_only_ko'):
            row = next((c['r'] for c in cs if any(x.get('jo') for x in c.get('seg', []))), cs[-1]['r'])
            home = (next((c for c in kocells if c['r'] <= row < c['r'] + c['span']), None)
                    or next((c for c in kocells if c['r'] >= row), None))
            if home:
                home.setdefault('notes', []).append(ONLY_KO[L] + g[f'{L}_only_ko'])


def patch_viewer(src, with_en=False):
    """祝福家庭と理想天国のビューアを、この本向けに書き換える。どの差し替えも当たらなければ止まる"""
    s = src
    T_JA, T_KO, T_EN = (('韓日英 三か国語対訳', '한일영 3개국어 대역', 'Korean–Japanese–English Parallel') if with_en
                        else ('韓日対訳', '한일 대역', 'Korean–Japanese Parallel'))
    reps = [
        ('<title>祝福家庭と理想天国 三か国語対訳</title>', f'<title>平和経 {T_JA}</title>'),
        ('<meta property="og:title" content="祝福家庭と理想天国 三か国語対訳">',
         f'<meta property="og:title" content="平和経 {T_JA}">'),
        ('title: "祝福家庭と理想天国 三か国語対訳", brand: "訓読 対訳",',
         f'title: "平和経 {T_JA}", brand: "天一国経典 対訳",'),
        ('title: "축복가정과 이상천국 3개국어 대역", brand: "훈독 대역",',
         f'title: "평화경 {T_KO}", brand: "천일국 경전 대역",'),
        ('title: "Blessing and Ideal Family — Three-Language Parallel", brand: "Hoondok Parallel",',
         f'title: "Pyeong Hwa Gyeong — {T_EN}", brand: "Cheon Il Guk Scripture Parallel",'),
        ('foot: (links) => `出典: Daum カフェ「천일국 경전방」の各記事（${links}）。`\n'
         '        + `段落の対応づけは文字数から機械的に推定したものです。ずれていたら元記事で確かめてください。`,',
         'foot: (links) => `出典（${links}）: 韓国語は Daum カフェ「천일국 경전방」の掲示板「2. 평화경」、日本語はみ旨の裏庭の『平和経』（同じカフェの「2. 平和経」から組んだもの）。`\n'
         '        + `日本語版で省かれている所は、韓国語から訳した AI 参考訳で補っています（公式訳ではありません。「AI訳」ボタンで消せます）。`\n'
         '        + `日本語版が中身を書き換えている所と、日本語版にしか無い文には「※」の注を付けました。`,'),
        ('foot: (links) => `출처: 다음 카페 「천일국 경전방」의 각 글 (${links}). `\n'
         '        + `문단 짝짓기는 글자 수를 바탕으로 기계가 추정한 것입니다. 어긋나 보이면 원글에서 확인해 주십시오.`,',
         'foot: (links) => `출처 (${links}): 한국어는 다음 카페 「천일국 경전방」의 게시판 「2. 평화경」, 일본어는 미무네노 우라니와의 『平和経』 (같은 카페의 「2. 平和経」에서 엮은 것). `\n'
         '        + `일본어판에서 생략된 부분은 한국어에서 옮긴 AI 참고 번역으로 채웠습니다 (공식 번역이 아닙니다. 「AI 번역」 버튼으로 숨길 수 있습니다). `\n'
         '        + `일본어판이 내용을 바꾼 곳과 일본어판에만 있는 문장에는 「※」 주를 달았습니다.`,'),
        ('foot: (links) => `Source: the posts in the Daum cafe "천일국 경전방" (${links}). `\n'
         '        + `The paragraph pairing is estimated mechanically from text length; if it looks off, check the original post.`,',
         'foot: (links) => `Sources (${links}): the Korean is from the board "2. 평화경" in the Daum cafe "천일국 경전방"; the Japanese is the 平和経 on this site (built from the board "2. 平和経" in the same cafe). `\n'
         '        + `Passages left out of the Japanese edition are filled with AI reference translations from the Korean (not the official text; hide them with the AI button). `\n'
         '        + `Notes marked ※ point out where the Japanese edition changes the content, and sentences found only in the Japanese edition.`,'),
        ('wMoved: "⇄印の英語は、対訳のため翻訳版の掲載順から移動してあります",',
         'wMoved: "⇄印の訳文は、韓国語の順に合わせるため、訳書（日本語版）の順番から移動してあります",'),
        ('mvTitle: "対訳のため、翻訳版に掲載されていた順番から移動してあります",',
         'mvTitle: "韓国語の順に合わせるため、訳書の順番から移動してあります",\n'
         '      joTag: "日本語版のみの文（点線）", joT: "点線の文は、その欄の訳書（日本語版）にだけあり、韓国語の原文にはありません",\n'
         '      aiSegTag: "色付きの所は AI訳", aiSegT: "色付きの所は訳書で省かれていた語句を、韓国語から AI が訳したものです（公式訳ではありません。「AI訳」ボタンで消せます）",'),
        ('wMoved: "⇄ 표시가 붙은 영어는 대역을 맞추기 위해 번역판의 실린 순서에서 옮긴 것입니다",',
         'wMoved: "⇄ 표시가 붙은 번역문은 한국어 순서에 맞추기 위해 번역판(일본어판)의 순서에서 옮긴 것입니다",'),
        ('mvTitle: "대역을 맞추기 위해, 번역판에 실려 있던 순서에서 옮겼습니다",',
         'mvTitle: "한국어 순서에 맞추기 위해 번역판의 순서에서 옮겼습니다",\n'
         '      joTag: "일본어판에만 있는 문장 (점선)", joT: "점선 문장은 그 칸의 번역판(일본어판)에만 있고 한국어 원문에는 없습니다",\n'
         '      aiSegTag: "색 바탕은 AI 번역", aiSegT: "색 바탕 부분은 번역판에서 생략된 어구를 한국어에서 AI가 옮긴 것입니다 (공식 번역이 아닙니다. 「AI 번역」 버튼으로 숨길 수 있습니다)",'),
        ('wMoved: "English cells marked ⇄ were moved out of the order of the translated post so that they line up",',
         'wMoved: "Translation cells marked ⇄ were moved out of the order of the Japanese edition to follow the Korean",'),
        ('mvTitle: "Moved out of the order in which it appeared in the translated post, so that it lines up",',
         'mvTitle: "Moved out of the order of the translated edition to follow the Korean",\n'
         '      joTag: "Japanese edition only (dotted)", joT: "Dotted sentences appear only in the translated edition of that column (Japanese), not in the Korean original",\n'
         '      aiSegTag: "Shaded: AI translation", aiSegT: "Shaded words were left out of the translated edition and are an AI translation from the Korean (not the official text; hide them with the AI button)",'),
        ('if ((s.cells.en || []).some((c) => c.mv)) warn.push(t.wMoved);',
         'if ([...(s.cells.ja || []), ...(s.cells.en || [])].some((c) => c.mv)) warn.push(t.wMoved);'),
        ('spanTag: (n) => `・ ${n}段落ぶん`,', 'spanTag: () => "",'),
        ('spanTag: (n) => `・ ${n}문단 분량`,', 'spanTag: () => "",'),
        ('spanTag: (n) => `· ${n} paragraphs`,', 'spanTag: () => "",'),
        # 日本語版にしか無い文（seg の jo）に点線と札、セルの下に ※ の注（notes）
        ('        + (c.mv ? `<span class="mvtag" title="${esc(t.mvTitle)}">${t.mvTag}</span>` : "")\n',
         '        + (c.mv ? `<span class="mvtag" title="${esc(t.mvTitle)}">${t.mvTag}</span>` : "")\n'
         '        + ((c.seg || []).some((g) => g.jo) ? `<span class="mvtag" title="${esc(t.joT)}">${esc(c.jot || t.joTag)}</span>` : "")\n'
         '        + ((c.seg || []).some((g) => g.ai) ? `<span class="mvtag aisegtag" title="${esc(t.aiSegT)}">${esc(c.ait || t.aiSegTag)}</span>` : "")\n'),
        ('      + (c.t ? `<span class="body">${esc(c.t)}</span>`',
         '      + (c.t ? `<span class="body">${c.seg ? c.seg.map((g) => g.jo ? g.t.replace(/^(\\s*)([\\s\\S]*)$/, (m, sp, x) =>\n'
         '              `${esc(sp)}<span class="jaonly"><span class="jobadge" title="${esc(t.joT)}">${esc(c.jol || t.joTag)}</span>${esc(x)}</span>`)\n'
         '          : g.ai ? `<span class="aiseg" title="${esc(t.aiSegT)}">${esc(g.t)}</span>` : esc(g.t)).join("") : esc(c.t)}</span>`'),
        ('        out.push((c.ai && !ai ? `〔${AITAG[L.id]}〕\\n` : "") + c.t.trim());',
         '        const body = c.seg ? c.seg.filter((g) => showAI || !g.ai)\n'
         '          .map((g) => g.ai ? g.t.replace(/^(\\s*)([\\s\\S]*)$/, "$1〔AI: $2〕") : g.t).join("") : c.t;\n'
         '        out.push((c.ai && !ai ? `〔${AITAG[L.id]}〕\\n` : "") + body.trim());'),
        ('      + (c.w ? briefBox(c.w) : "");',
         '      + (c.w ? briefBox(c.w) : "")\n'
         '      + (c.notes || []).map((n) => `<span class="cnote">${esc(n)}</span>`).join("");'),
        # 小見出しの行（h）は太字、日付・場所・行事の行（m）は小さく
        ('      + (c.ai ? " ai" : "");\n', '      + (c.ai ? " ai" : "") + (c.h ? " hd" : "") + (c.m ? " meta" : "");\n'),
        # 節（講演）の名前は篇ごとの番号（labels）。一覧は篇ごとにまとめる（optgroup）
        ('    return m ? `${T().chapter(+m[1])} ${s.key}` : s.label;',
         '    return m ? `${T().chapter(+m[1])} ${s.key}` : (s.labels ? s.labels[ui] || s.labels.ja : s.label);'),
        ('    data.forEach((s, i) => {\n'
         '      const o = document.createElement("option");\n'
         '      o.value = i;\n'
         '      o.textContent = `${secLabel(s)}　${secTitle(s)}`;\n'
         '      sel.appendChild(o);\n'
         '    });',
         '    let grp = null, box = sel;\n'
         '    data.forEach((s, i) => {\n'
         '      const g = s.grp ? s.grp[ui] || s.grp.ja : "";\n'
         '      if (g && g !== grp) {\n'
         '        box = document.createElement("optgroup");\n'
         '        box.label = g;\n'
         '        sel.appendChild(box);\n'
         '        grp = g;\n'
         '      }\n'
         '      const o = document.createElement("option");\n'
         '      o.value = i;\n'
         '      o.textContent = `${secLabel(s)}　${secTitle(s)}`;\n'
         '      box.appendChild(o);\n'
         '    });'),
    ]
    if not with_en:   # 英語の対応表がまだ無いときは、韓・日の2列
        reps.append(('    { id: "en", label: "English", tag: "EN" },\n', ''))
    for a, b in reps:
        n = s.count(a)
        assert n == 1, f'{n} 回: {a[:60]}'
        s = s.replace(a, b)
    desc = 'content="韓国語・日本語・英語を段落ごとに並べて読める対訳です。"'
    assert s.count(desc) == 2, s.count(desc)
    s = s.replace(desc, 'content="天一国経典『平和経』の韓国語原文と日本語訳を、段落ごとに並べて読める対訳です。"')
    n = s.count('taiyaku/syuku_risoutengoku/index.html')
    assert n == 2, n
    s = s.replace('taiyaku/syuku_risoutengoku/index.html', 'taiyaku/heiwakyou/index.html')
    n = s.count('hoondok.')
    assert n >= 3, n
    s = s.replace('hoondok.', 'heiwakyou.')
    s = s.replace('</style>', '  #brk{display:none}\n'
                  '  .cell .cnote{display:block;margin-top:.6em;font-size:.82em;line-height:1.65;color:var(--muted)}\n'
                  '  .cell .jaonly{text-decoration:underline dotted var(--markline);text-decoration-thickness:2px;text-underline-offset:.3em}\n'
                  '  .cell .jobadge{display:inline-block;font-size:.66em;line-height:1.55;padding:0 .55em;margin-right:.4em;\n'
                  '    border:1px solid var(--markline);border-radius:999px;color:var(--markline);vertical-align:.15em;white-space:nowrap}\n'
                  '  .cell .aiseg{color:var(--muted);background:color-mix(in srgb,var(--mark) 45%,transparent);\n'
                  '    border-radius:3px;padding:0 .15em;-webkit-box-decoration-break:clone;box-decoration-break:clone}\n'
                  '  .cell .aisegtag{color:var(--markline)}\n'
                  '  body.hideai .cell .aiseg,body.hideai .cell .aisegtag{display:none}\n'
                  '  .cell.hd .body{font-weight:700}\n'
                  '  .cell.meta .body{font-size:.86em;color:var(--muted)}\n'
                  '</style>', 1)
    return s


def main():
    trans = {L: frags.done(L) for L in ('ja', 'en')}
    hen = hen_titles()
    secs = []
    (OUT / 'data').mkdir(parents=True, exist_ok=True)
    with_en = any((HERE / 'work' / 'align-en').glob('*.json'))
    for f in sorted(SEC.glob('*.json')):
        sec = json.loads(f.read_text(encoding='utf-8'))
        als = {'ja': json.loads((ALIGN / f.name).read_text(encoding='utf-8'))}
        en_path = HERE / 'work' / 'align-en' / f.name
        if with_en and en_path.exists():
            als['en'] = json.loads(en_path.read_text(encoding='utf-8'))
        cells, n = rows_of(sec, als, trans)
        key, h, num = sec['key'], sec['hen'], sec['num']
        hj, hk = f'第{KANJI[h]}篇 {hen[h]["ja"]}', f'제{h}편 {hen[h]["ko"]}'
        titles = {'ja': sec['title']['ja'], 'ko': sec['title']['ko'], 'en': ''}
        header = {'ja': [BOOK['ja'], hj, sec['title']['ja']], 'ko': [BOOK['ko'], hk, sec['title']['ko']], 'en': []}
        langs = [L for L in ('en', 'ja', 'ko') if cells.get(L)]
        entry = {'key': key, 'label': f'第{KANJI[h]}篇 {num}',
                 'labels': {'ja': f'第{KANJI[h]}篇 {num}', 'ko': f'제{h}편 {num}', 'en': f'Book {h}-{num}'},
                 'grp': {'ja': hj, 'ko': hk, 'en': f'Book {h}'},
                 'titles': titles,
                 'urls': {'ko': CAFE + str(sec['posts'][0]), 'ja': f'../../heiwakyou/{key}.html'},
                 'header': header, 'n': n,
                 'counts': {L: len(sec.get(L, [])) for L in ('ko', 'ja', 'en')}, 'langs': langs}
        secs.append(entry)
        body = json.dumps({'cells': cells}, ensure_ascii=False, separators=(',', ':'))
        (OUT / 'data' / f'{key}.js').write_text(f'window.HD.put("{key}", {body});\n', encoding='utf-8', newline='\n')
    v = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    book = json.dumps({'sections': secs, 'v': v}, ensure_ascii=False, separators=(',', ':'))
    (OUT / 'book.js').write_text(f'window.HOONDOK = {book};\n', encoding='utf-8', newline='\n')
    page = patch_viewer(VIEWER.read_text(encoding='utf-8'), with_en)
    (OUT / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    wait = sum(f.read_text(encoding='utf-8').count('〔訳待ち〕') for f in (OUT / 'data').glob('*.js'))
    print(f'{len(secs)} 講演を書き出した → {OUT}（英語 {"あり" if with_en else "なし"}、訳待ち {wait} か所）')


if __name__ == '__main__':
    main()

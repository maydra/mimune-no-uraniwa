# Daum カフェ「천일국 경전방」の3つの掲示板から、み旨の裏庭の本のフォルダを作る
#   python -X utf8 _tools/cafe_books/build_books.py            # 3冊とも
#   python -X utf8 _tools/cafe_books/build_books.py sekai      # 1冊だけ（tengoku / heiwa / sekai）
# 先に crawl.py → parse.py。ページの形は touitusisou/（統一思想要綱）を写す
import json, os, re, sys, html, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from classify import RE_BOOK, RE_PART, RE_CHAP, RE_SEC, RE_SUB, kind

RAW = pathlib.Path(__file__).resolve().parent / 'raw'
# 書き出す先はこのリポジトリの根。別の作業フォルダ（git worktree）で組むときは SITE_ROOT で指す
SITE = pathlib.Path(os.environ.get('SITE_ROOT') or pathlib.Path(__file__).resolve().parents[2])
TMPL = (SITE / 'touitusisou' / '01.html').read_text(encoding='utf-8')
TMPL_INDEX = (SITE / 'touitusisou' / 'index.html').read_text(encoding='utf-8')
KANJI = '〇一二三四五六七八九'

def kanji_num(n):
    if n <= 10:
        return '十' if n == 10 else KANJI[n]
    t, o = divmod(n, 10)
    return ('' if t == 1 else KANJI[t]) + '十' + (KANJI[o] if o else '')

def rows(fld):
    return {r['n']: r for r in map(json.loads, open(RAW / f'{fld}.jsonl', encoding='utf-8'))}

def lines_of(r):
    return [l.strip() for p in r['paras'] for l in p['text'].split('\n') if l.strip()]

def esc(s):
    return html.escape(s, quote=False)

# ---- 雛形（touitusisou の 01.html / index.html から切り出す） ----
HEAD_PRE = TMPL[:TMPL.index('<title>')]                       # gtag・viewport・favicon・charset
HEAD_CSS = re.search(r'<link href="\.\./theme/style\.css[^>]*>\s*<link rel="stylesheet" href="\.\./theme/pages/[^"]+">', TMPL).group(0)
BOOT = re.search(r'<script id="theme-boot">.*?</script>', TMPL, re.S).group(0)
TYPO = re.search(r'<details class="typo-box.*?</details>', TMPL, re.S).group(0)
TYPO_JS = re.search(r'<script>\s*\(\(\) => \{\s*const root = document\.getElementById\("typo-report"\).*?</script>', TMPL, re.S).group(0)
TAIL = re.search(r'<script src="\.\./theme/script\.js[^"]*"></script>\s*</body>', TMPL).group(0)
IDX_CSS = re.search(r'<link href="\.\./theme/style\.css[^>]*>\s*<link rel="stylesheet" href="\.\./theme/pages/[^"]+">', TMPL_INDEX).group(0)
IDX_TAIL = re.search(r'<script src="\.\./theme/script\.js[^"]*"></script>\s*<script src="\.\./offline\.js[^"]*" defer></script>\s*</body>', TMPL_INDEX).group(0)
RANDOM = (SITE / 'touitusisou' / 'random.html').read_text(encoding='utf-8')

# 出典の行・部の題（世界経典）。2ページ以上で同じなので、extract_inline_css.py が共有ファイルに出す
EXTRA_CSS = '''<style>
.content-card p.cite { text-indent: 0; text-align: right; font-size: 0.9rem; opacity: 0.75; margin-top: -0.9rem; }
.content-card p.subhead.label { border-left: none; padding-left: 0; text-align: center; font-size: 1rem; letter-spacing: 0.2em; opacity: 0.85; }
.part-title { margin: 2.2rem 0 0.8rem; font-weight: 700; font-size: 1.15rem; letter-spacing: 0.06em; }
</style>'''

def page_nav(prev, nxt):
    a = (f'<a class="nav-btn" href="{prev[0]}"><span>←</span> {esc(prev[1])}</a>' if prev
         else '<span class="nav-btn" style="visibility:hidden"></span>')
    c = (f'<a class="nav-btn" href="{nxt[0]}">{esc(nxt[1])} <span>→</span></a>' if nxt
         else '<span class="nav-btn" style="visibility:hidden"></span>')
    return f'<nav class="page-nav">\n{a}\n<a class="nav-btn" href="index.html">目次</a>\n{c}\n</nav>'

def chapter_html(book, ch, prev, nxt):
    toc, body = [], []
    for b in ch['blocks']:
        t = b[0]
        if t == 'h3':
            toc.append(f'<li class="t1"><a href="#{b[1]}">{esc(b[2])}</a></li>')
            body.append(f'<h3 class="lv1" id="{b[1]}"><a href="#{b[1]}">{esc(b[2])}</a></h3>')
        elif t == 'h4':
            toc.append(f'<li class="t2"><a href="#{b[1]}">{esc(b[2])}</a></li>')
            body.append(f'<h4 class="lv2" id="{b[1]}"><a href="#{b[1]}">{esc(b[2])}</a></h4>')
        elif t == 'subhead':
            body.append(f'<p class="subhead">{esc(b[1])}</p>')
        elif t == 'label':
            body.append(f'<p class="subhead label">{esc(b[1])}</p>')
        elif t == 'cite':
            body.append(f'<p class="cite">{esc(b[1])}</p>')
        else:
            body.append(f'<p>{esc(b[1])}</p>')
    head_label = f'<span class="label">{esc(ch["label"])}</span>' if ch['label'] else ''
    toc_html = (f'<div class="toc" id="toc"><h3>この章の目次</h3><ul>\n' + '\n'.join(toc) + '\n</ul></div>\n') if len(toc) > 1 else ''
    title = f'{ch["label"]}　{ch["title"]}'.strip('　') + f' - {book["title"]}'
    return (HEAD_PRE + f'<title>{esc(title)}</title>\n' + HEAD_CSS + '\n' + EXTRA_CSS + '\n</head>\n\n'
            '<body class="dark-mode">\n' + BOOT + '\n<div class="container">\n'
            f'<h1><a href="index.html">{esc(book["title"])}</a></h1>\n'
            f'<div class="chapter-head">{head_label}<h2>{esc(ch["title"])}</h2></div>\n'
            + page_nav(prev, nxt) + '\n' + toc_html +
            '<div class="content-card">\n' + '\n'.join(body) + '\n</div>\n'
            + TYPO + '\n' + page_nav(prev, nxt) + '\n</div>\n'
            + TYPO_JS + '\n' + TAIL + '\n</html>\n')

def index_html(book):
    items = []
    flat = not any(b[0] in ('h3', 'h4') for ch in book['chapters'] for b in ch['blocks'])
    for ch in book['chapters']:
        if flat:
            items.append(f'<div class="chapter-item"><a class="chapter-link" href="{ch["file"]}">{esc(ch["label"])}. {esc(ch["title"])}</a></div>')
            continue
        if ch.get('part'):
            items.append(f'<p class="part-title">{esc(ch["part"])}</p>')
        secs = []
        for b in ch['blocks']:
            if b[0] == 'h3':
                secs.append(f'<li class="section-item"><a class="section-link" href="{ch["file"]}#{b[1]}">{esc(b[2])}</a></li>')
            elif b[0] == 'h4':
                secs.append(f'<li class="section-item indent-1"><a class="section-link" href="{ch["file"]}#{b[1]}">{esc(b[2])}</a></li>')
        summary = f'{ch["label"]}　{ch["title"]}'.strip('　')
        items.append('<div class="chapter-item">\n<details' + (' open' if len(book['chapters']) == 1 else '') + '>\n'
                     f'<summary>{esc(summary)}</summary>\n<div class="details-content">\n'
                     f'<div class="read-chapter"><a class="chapter-link" href="{ch["file"]}">➡ この章の本文を読む</a></div>\n'
                     '<ul class="section-list">\n' + '\n'.join(secs) + '\n</ul>\n</div>\n</details>\n</div>')
    slug = book['slug']
    return (TMPL_INDEX[:TMPL_INDEX.index('<title>')] + f'<title>{esc(book["title"])} | 目次 | み旨の裏庭</title>\n'
            + IDX_CSS + '\n' + EXTRA_CSS + '\n</head>\n<body class="dark-mode" data-pagefind-ignore>\n' + BOOT +
            f'\n<div class="container">\n<h1>{esc(book["title"])}</h1>\n<p class="lead">{esc(book["lead"])}</p>\n'
            f'<div class="book-search"><a class="book-search-btn" href="../search-all.html?book={slug}">この書籍の中で検索</a>'
            f'<button class="book-search-btn" id="offline-save-btn" data-book="{slug}" hidden>📥 この本をオフライン保存</button></div>\n'
            '<div class="index-list">\n' + '\n'.join(items) + '\n</div>\n' +
            '<div class="nav-links">\n<a href="../index.html">トップページへ戻る</a>\n'
            f'<a href="{book["chapters"][0]["file"]}">最初から読む</a>\n</div>\n</div>\n\n' + IDX_TAIL + '\n</html>\n')

def write(book):
    out = SITE / book['slug']
    out.mkdir(exist_ok=True)
    chs = book['chapters']
    for i, ch in enumerate(chs):
        nav = lambda c: (c['file'], (c['label'] or c['title'])) if c else None
        prev = nav(chs[i - 1]) if i else None
        nxt = nav(chs[i + 1]) if i + 1 < len(chs) else None
        (out / ch['file']).write_text(chapter_html(book, ch, prev, nxt), encoding='utf-8', newline='\n')
    (out / 'index.html').write_text(index_html(book), encoding='utf-8', newline='\n')
    if not (out / 'random.html').exists():
        (out / 'random.html').write_text(RANDOM, encoding='utf-8', newline='\n')
    chars = sum(len(b[-1]) for c in chs for b in c['blocks'])
    print(book['slug'], len(chs), 'pages', chars, 'chars')

# ---- 6. 天国を開く門 · 真の家庭（VS04。節ごとの記事 2〜38 を使う。44 の全文は見出しが本文とくっついている所がある） ----
def tengoku():
    R = rows('VS04')
    toc = lines_of(R[1])
    chap_titles = {}
    for l in toc:
        m = re.match(r'^第([一二三四五六七八九十]+)章\s*(.+)$', l)
        if m:
            chap_titles[KANJI.index(m.group(1)) if len(m.group(1)) == 1 else 10] = m.group(2).strip()
    chapters = {}
    for n in sorted(R):
        L = lines_of(R[n])
        if len(L) < 3 or not RE_CHAP.match(L[1].replace('　', ' ')):
            continue
        c = int(RE_CHAP.match(L[1]).group(1))
        ms = re.match(r'^第\s*([0-9一二三四五六七八九十]+)\s*節\s*(.+)$', L[2].replace('　', ' '))
        s = int(ms.group(1)) if ms.group(1).isdigit() else KANJI.index(ms.group(1))  # 第四節・第六節は漢数字で書いてある
        stitle = ms.group(2).strip()
        ch = chapters.setdefault(c, {'file': f'{c:02d}.html', 'label': f'第{kanji_num(c)}章',
                                     'title': chap_titles.get(c, RE_CHAP.match(L[1]).group(2).strip()), 'blocks': []})
        body = L[3:]
        # 第四章第八節は ① ② の小見出しが題の後ろに付いている
        m8 = re.match(r'^(.*?)(①.+)$', stitle)
        if m8:
            stitle, body = m8.group(1).strip(), [m8.group(2)] + body
        ch['blocks'].append(('h3', str(s), f'第{kanji_num(s)}節　{stitle}'))
        for l in body:
            if re.match(r'^[①②③④⑤⑥⑦⑧⑨]\s*[^。]{1,30}$', l):
                ch['blocks'].append(('subhead', l))
            else:
                ch['blocks'].append(('p', l))
    return {'slug': 'tengoku_mon', 'title': '天国を開く門 真の家庭',
            'lead': '『天国を開く門 真の家庭』の全文です。章の名前を押すと節の一覧が開きます。',
            'chapters': [chapters[k] for k in sorted(chapters)]}

# ---- 7. 平和の主人 · 血統の主人（VWMp） ----
# 全文の記事 36 を使う（ユーザーが選んだ。節ごとの記事 2〜34 と同じ訳の手直し版で、誤字が直っている）。
# 36 の見出しは 1〜24 に「N. 」が付き、25〜33 は番号なしの行。節ごとの記事の題と照らして見出しの行を見つける
HEIWA_FIX = {'最初に灰る': '最初に戻る', 'となリ得る': 'となり得る', 'りーダー': 'リーダー'}

def heiwa():
    import difflib
    R = rows('VWMp')
    W = lines_of(R[36])[1:]                      # 頭の行は本の題
    titles = [re.sub(r'\s*[（(]完[)）]\s*$', '', lines_of(R[n])[0]).strip() for n in range(2, 35)]
    chapters, k = [], 0
    for l in W:
        for a, b in HEIWA_FIX.items():
            l = l.replace(a, b)
        m = re.match(r'^(\d+)\.\s*(.+)$', l)
        nxt = titles[k] if k < len(titles) else None
        if len(l) < 50 and ((m and int(m.group(1)) == k + 1) or
                            (nxt and difflib.SequenceMatcher(None, l, nxt).ratio() > 0.8)):
            k += 1
            # 見出しごとに1ページ（ユーザー「それぞれの項目でページ分割したほうがよさそう」）
            chapters.append({'file': f'{k:02d}.html', 'label': str(k),
                             'title': m.group(2).strip() if m else l, 'blocks': []})
        else:
            chapters[-1]['blocks'].append(('p', l))
    assert k == 33, f'見出しが {k} 個しか見つからない'
    return {'slug': 'heiwa_syujin', 'title': '平和の主人 血統の主人',
            'lead': '『平和の主人、血統の主人』（2009年7月7日、米国イーストガーデン）の全文です。',
            'chapters': chapters}

# ---- 8. 世界経典 Ⅱ（VyWS。1記事＝1小節） ----
# 節と小節は記事の題（[226] 世界経典 - イエス - 1. 罪悪の… / [228] 世界経典 - イエス 3 - 真の人…）で決める。
# 本文の頭の行（第1部… / 第9章… / 11) イエス / 2. イエス : 神様の息子…）は見出しの文言に使う。
# 頭の行には小節の行が無い記事（226・373・386）、番号の誤り（241 の「11) ムハンマド」は 12）、
# 小節を「6) 巡礼と聖地」と書いた記事（398）がある
FIXES = []

def title_parts(t):
    """題から（節の名前, 小節の番号, 小節の名前）。小節の無い記事は (名前, None, None)"""
    t = re.sub(r'^\[\d+\]\s*世界経典\s*-\s*', '', t).strip()
    for pat in (r'^(.*?)\s*-\s*(\d+)\s*[.．)）]\s*(.+)$',   # イエス - 1. 罪悪の…
                r'^(.*?)\s+(\d+)\s*-\s*(.+)$',             # イエス 3 - 真の人…
                r'^(.*?)\s+(\d+)\s*[.．]\s*(.+)$'):         # 主権と全能 2. 人間社会の…
        m = re.match(pat, t)
        if m:
            return m.group(1).strip(), int(m.group(2)), m.group(3).strip()
    m = re.match(r'^(.*?)\s*-\s*(.+)$', t)
    if m:
        return m.group(1).strip(), 1, m.group(2).strip()
    return t, None, None

def sekai():
    R = rows('VyWS')
    chapters, part, cur = [], None, None
    sec_no, sec_name, sub_no = 0, None, 0
    for n in sorted(R):
        L = lines_of(R[n])
        t_sec, t_sub_no, t_sub = title_parts(R[n]['title'])
        i, b_sec, b_sub = 0, None, None
        while i < len(L) and len(L[i]) < 60:
            l = L[i].replace('　', ' ')
            if RE_BOOK.match(l):
                pass
            elif RE_PART.match(l):
                m = RE_PART.match(l); part = f'第{m.group(1)}部　{m.group(2).strip()}'
            elif RE_CHAP.match(l):
                m = RE_CHAP.match(l); c = int(m.group(1))
                if not cur or cur['num'] != c:
                    cur = {'num': c, 'file': f'{c:02d}.html', 'label': f'第{c}章', 'title': m.group(2).strip(),
                           'part': part if not chapters or chapters[-1]['part_raw'] != part else None,
                           'part_raw': part, 'blocks': []}
                    chapters.append(cur); sec_no, sec_name = 0, None
            elif RE_SEC.match(l) and b_sec is None:
                m = RE_SEC.match(l); b_sec = (int(m.group(1)), m.group(2).strip())
            elif RE_SUB.match(l) or RE_SEC.match(l):
                m = RE_SUB.match(l) or RE_SEC.match(l); b_sub = (int(m.group(1)), m.group(2).strip())
            else:
                break
            i += 1
        # 節は本文の頭の行（5) 主権と全能）の名前で決める。番号が前の節と同じか戻っていたら振り直す（241・242 の「11) ムハンマド」）
        name = b_sec[1] if b_sec else t_sec
        no = b_sec[0] if b_sec else sec_no
        if name != sec_name:
            if no <= sec_no:
                FIXES.append(f'[{n}] 節の番号 {no}) を {sec_no + 1}) に（{name}）')
                no = sec_no + 1
            sec_no, sec_name, sub_no = no, name, 0
            cur['blocks'].append(('h3', str(sec_no), f'{sec_no}) {name}'))
        # 節の最初の記事は、節の前置きの文のあとに小節の行（1. 被造物に…）が来る。その行があればそこに見出しを置く
        body = L[i:]
        at = 0
        if not b_sub and t_sub:
            for j, l in enumerate(body):
                m = RE_SUB.match(l)
                if m and len(l) < 60 and int(m.group(1)) == t_sub_no:
                    b_sub, at = (t_sub_no, m.group(2).strip()), j
                    del body[j]
                    break
        for j, l in enumerate(body):
            if j == at and (b_sub or t_sub):
                no, text = b_sub if b_sub else (t_sub_no, t_sub)
                if no != sub_no:
                    sub_no = no
                    cur['blocks'].append(('h4', f'{sec_no}-{sub_no}', f'{sub_no}. {text}'))
            k = kind(l)
            if k == 'label':
                name = re.sub(r'[^宗教経典み言選集文鮮明先生のみ御]', '', l)
                cur['blocks'].append(('label', f'― {name} ―'))
            else:
                cur['blocks'].append((k, l))
        if not body and (b_sub or t_sub):
            no, text = b_sub if b_sub else (t_sub_no, t_sub)
            if no != sub_no:
                sub_no = no
                cur['blocks'].append(('h4', f'{sec_no}-{sub_no}', f'{sub_no}. {text}'))
    for f in FIXES:
        print('  ', f)
    return {'slug': 'sekai_kyouten2', 'title': '世界経典 Ⅱ',
            'lead': '『世界経典 Ⅱ』の全文です。各節に世界の宗教の経典と、文鮮明先生のみ言（み言選集）を並べています。章の名前を押すと節の一覧が開きます。',
            'chapters': chapters}

BOOKS = {'tengoku': tengoku, 'heiwa': heiwa, 'sekai': sekai}
if __name__ == '__main__':
    for key in (sys.argv[1:] or BOOKS):
        write(BOOKS[key]())

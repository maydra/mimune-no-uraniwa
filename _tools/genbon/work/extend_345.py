# 3巻の残り（448〜457）・4巻・5巻を足す: 巻ごとの掲示板の記事 → 段落（units.json の続き）
#   python -I -X utf8 _tools/genbon/work/extend_345.py <落とした記事のフォルダ> <作業フォルダ>
# 落とした記事: cafe_books/crawl.py W8k2 W4A3 W4A4 で落としたもの（E:\mimune-no-uraniwa\cafe-raw\）
# 作業フォルダに units345.json（訳す前の段落）と、訳す束 wbN.json を書く（E:\mimune-no-uraniwa\genbon-work\）
#
# 巻の掲示板の記事は原稿1ページ＝1記事で、写真のあとに同じページの文が3つ並ぶ:
#   書いたままの文 → 字を直した漢字まじり文 → ハングル文。いまの対訳（WD3Y から 1〜447）の原文は2つめと同じ形
# 3つの区切りの行は「453」「[561]」「561쪽」「X - 011」「원리원본 (原理原本) - 453쪽」などまちまち。
# 区切りの行の後ろに文が続いている記事もある（「[674] 할 수 있는 …」）
import json, os, re, sys, html
from collections import Counter

RAW, WORK = sys.argv[1], sys.argv[2]
os.makedirs(WORK, exist_ok=True)
FLD = {'W8k2': 3, 'W4A3': 4, 'W4A4': 5}

def title_of(t):
    m = re.search(r'<h3 class="tit_subject">(.*?)</h3>', t, re.S)
    return html.unescape(re.sub(r'<[^>]+>|\s+', ' ', m.group(1))).strip() if m else ''

def lines_of(t):
    m = re.search(r'tx-content-container">(.*?)<script', t, re.S)
    b = re.sub(r'<br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>', '\n', m.group(1))
    b = re.sub(r'<img[^>]*>', '\n', b)
    return [re.sub(r'[ \t\u3000]+', ' ', l).strip() for l in html.unescape(re.sub(r'<[^>]+>', '', b)).replace('\xa0', ' ').split('\n') if l.strip()]

# 記事の題 → ページの印（448 / 497-2 / 661-1 / X-010）
def page_key(title):
    m = re.search(r'X\s*-\s*(\d+)\s*쪽', title)
    if m:
        return f'X-{int(m.group(1)):03d}'
    m = re.search(r'-\s*(\d{3})쪽(?:\s*(\d))?', title)
    if m:
        return m.group(1) + (f'-{m.group(2)}' if m.group(2) else '')
    return None

def order(k):
    if k.startswith('X-'):
        return (1000 + int(k[2:]), 0)
    a, _, b = k.partition('-')
    return (int(a), int(b or 0))

SEP_BODY = r'(?:원리원본\s*(?:\(原理原本\))?\s*[-：:]?\s*)?\[?(?:X\s*-?\s*)?\d{3}(?:\s*-\s*\d)?\]?\s*(?:쪽|장)?'

def split_versions(L, key):
    """区切りの行で3つに分け、2つめ（字を直した文）を返す"""
    blocks, cur = [], None
    for l in L[1:]:                                   # L[0] は記事の題の行
        m = re.fullmatch(SEP_BODY, l)
        m2 = re.match(r'^\[((?:X\s*-\s*)?\d{3}(?:-\d)?)\]\s+(.+)$', l)
        if m:
            cur = []; blocks.append(cur)
        elif m2:
            cur = [m2.group(2)]; blocks.append(cur)
        else:
            if cur is None:
                cur = []; blocks.append(cur)
            cur.append(l)
    blocks = [b for b in blocks if b]
    return blocks

pages, report = {}, []
for fld, vol in FLD.items():
    d = os.path.join(RAW, fld)
    for f in os.listdir(d):
        if not f.endswith('.html'):
            continue
        t = open(os.path.join(d, f), encoding='utf-8').read()
        ti = title_of(t)
        # 巻の全文を1記事にしたもの（「原理原本 記錄第五券 (561~675, X-028쪽)」）は使わない
        k = None if '記錄' in ti else page_key(ti)
        if k is None:
            report.append(f'{fld}/{f} 題にページが無い（{ti}）')
            continue
        if vol == 3 and order(k) < (448, 0):
            continue
        L = lines_of(t)
        blocks = split_versions(L, k)
        if len(blocks) != 3:
            report.append(f'{fld}/{f} {k}: 文のかたまりが {len(blocks)} 個')
        if not blocks:
            continue
        # 2つめが字を直した文。かたまりが3つでないときは、漢字の多さで「直した文」らしいものを選ぶ（下の report を見て確かめる）
        mix = blocks[1] if len(blocks) >= 2 else blocks[0]
        pages[k] = {'vol': vol, 'key': k, 'title': ti, 'lines': mix, 'n_blocks': len(blocks), 'src': f'{fld}/{f}'}

# 3巻の 448〜457 は W8k2、4巻 459〜、5巻 561〜（X は5巻の後ろ）
keys = sorted(pages, key=order)
json.dump([pages[k] for k in keys], open(os.path.join(WORK, 'pages345.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

# 段落にする: 原稿のページの切れ目で文が途中なら、次のページの頭の行とつなぐ（units2.py と同じ考え）
END = re.compile(r'(다|요|라|까|랴|냐|오|자|지|네|노라|도다|니라|리라|로다|함|음|임)[.!?。」』\)）”]*\s*$|[.!?。」』”]\s*$')

def next_page(a, b):
    """b が a の次のページか（497 → 497-2、661-1 → 661-2 も次）"""
    oa, ob = order(a), order(b)
    return ob[0] == oa[0] and ob[1] == oa[1] + 1 or (ob[0] == oa[0] + 1 and ob[1] == 0) or (ob[0] == oa[0] + 1 and oa[1] and ob[1] == 0)

units = []
prev_key = None
for k in keys:
    p = pages[k]
    for i, line in enumerate(p['lines']):
        prev = units[-1] if units else None
        if (i == 0 and prev and prev_key and next_page(prev_key, k)
                and not END.search(prev['parts'][-1][1]) and len(prev['parts'][-1][1]) > 40):
            prev['parts'].append([k, line])
            continue
        units.append({'vol': p['vol'], 'parts': [[k, line]]})
    prev_key = k
for i, u in enumerate(units, 1):
    u['id'] = 805 + i
    ko = u['parts'][0][1]
    u['head_guess'] = len(u['parts']) == 1 and len(ko) <= 60 and not END.search(ko)
json.dump(units, open(os.path.join(WORK, 'units345.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

print('pages', len(pages), 'units', len(units), 'joined', sum(1 for u in units if len(u['parts']) > 1),
      'head_guess', sum(u['head_guess'] for u in units), 'ko chars', sum(len(t) for u in units for _, t in u['parts']))
print('vol', Counter(u['vol'] for u in units))
for r in report:
    print('  ', r)

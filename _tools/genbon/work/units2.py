# pages.jsonl → units.json: 原稿のページの切れ目で途中になった文を次のページの頭とつなぎ、訳す単位（段落）にする。
# 単位の中のページの区切りは parts に残す（[ページ, 韓国語, 掲示板の日本語]）。見出しらしい単位には heading の候補印
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = [json.loads(l) for l in open(os.path.join(HERE, 'pages2.jsonl'), encoding='utf-8')]

def page_of(p):
    m = re.search(r'\(?(\d+)\)?\s*ページ', p['title'])
    return int(m.group(1)) if m else None

def blocks(p):
    out, cur = [], None
    for k, line in p['lines']:
        if k == 'ja':
            if cur is None or cur['mix']:
                cur = {'ja': [], 'mix': []}; out.append(cur)
            cur['ja'].append(line)
        elif k == 'mix':
            if cur is None:
                cur = {'ja': [], 'mix': []}; out.append(cur)
            cur['mix'].append(line)
    return out

# 文の終わり（韓国語の終止形か句点で終わっている）
END = re.compile(r'(다|요|라|까|랴|냐|오|자|지|네|노라|도다|니라|리라|로다)[.!?。」』\)）]*\s*$|[.!?。」』]\s*$')
VOL = lambda pg: 1 if pg <= 176 else (2 if pg <= 328 else 3)

seen = set(); pages = []
for p in P:
    pg = page_of(p)
    if pg is None or pg in seen:
        continue
    seen.add(pg); pages.append((pg, p))
pages.sort()

units = []
for pg, p in pages:
    bs = [b for b in blocks(p) if b['mix']]
    for i, b in enumerate(bs):
        ko, ja = ' '.join(b['mix']), ' '.join(b['ja'])
        prev = units[-1] if units else None
        # ページの頭の段落で、前のページの最後の段落が文の途中で終わっていたら、つなぐ
        if i == 0 and prev and not END.search(prev['parts'][-1][1]) and prev['parts'][-1][0] == pg - 1:
            prev['parts'].append([pg, ko, ja])
            continue
        units.append({'id': len(units) + 1, 'vol': VOL(pg), 'parts': [[pg, ko, ja]]})
for u in units:
    ko = u['parts'][0][1]
    u['head_guess'] = len(u['parts']) == 1 and len(ko) <= 60 and not END.search(ko)
json.dump(units, open(os.path.join(HERE, 'units2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
n_join = sum(1 for u in units if len(u['parts']) > 1)
print('pages', len(pages), 'units', len(units), 'joined', n_join, 'head_guess', sum(u['head_guess'] for u in units),
      'ko chars', sum(len(x[1]) for u in units for x in u['parts']))

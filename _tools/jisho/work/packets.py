# 残した候補に、文脈（韓・日・英の段落の抜き出し）と英語の候補を付けて、作業用の束に分ける
import json, re, sys, html, glob, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from en_align import best  # noqa: E402  （en_align は読み込み時に全段落を数える）

REPO = sys.argv[1]
cands = {c['id']: c for c in json.load(open('cands.json', encoding='utf-8'))}
rows = json.load(open('rows.json', encoding='utf-8'))

ruby = json.load(open('ruby.json', encoding='utf-8'))

def around(text, key, width=90):
    i = text.find(key)
    if i < 0:
        return text[:width * 2] + ('…' if len(text) > width * 2 else '')
    a, b = max(0, i - width), min(len(text), i + len(key) + width)
    return ('…' if a else '') + text[a:b] + ('…' if b < len(text) else '')

out = []
for line in open('keep.txt', encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    cat, *ids = line.split()
    for i in ids:
        c = cands[int(i)]
        n, en = best(c['ja_guess'], c['ko'])
        ctx = []
        for o in c['occ'][:2]:
            ko, ja, enr = rows[o]
            ctx.append({'ref': o, 'ko': around(ko, '(' + c['hanja'] + ')'), 'ja': around(ja, c['ja_guess']),
                        'en': enr if len(enr) < 900 else enr[:900] + '…'})
        out.append({'id': c['id'], 'cat': cat, 'ko': c['ko'], 'hanja': c['hanja'], 'ja_guess': c['ja_guess'],
                    'ja_hit': c['hit'] or 'none', 'count': c['n'], 'occ': c['occ'],
                    'en_candidates': [g for s, g, a, b in en], 'ruby': ruby.get(c['ja_guess'], ''),
                    'context': ctx})
k = int(sys.argv[2])
for j in range(k):
    part = out[j::k]
    json.dump(part, open('batch%d.json' % (j + 1), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('batch%d' % (j + 1), len(part))

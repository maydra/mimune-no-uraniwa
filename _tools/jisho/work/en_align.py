# 日本語の語が出る段落と出ない段落で、英語の n-gram の出方を比べて、英語の訳語の候補を挙げる
import json, re, html, glob, os, sys, collections, math
D = sys.argv[1] if not os.path.isdir(os.path.join(sys.argv[1], 'dp')) else os.path.join(sys.argv[1], 'taiyaku', 'genri_kouron')
def load(f):
    t = open(f, encoding='utf-8').read()
    return json.loads(t[t.index('{'):t.rstrip().rstrip(';').rindex('}') + 1])
TAG = re.compile(r'<rt>.*?</rt>|<rp>.*?</rp>|<[^>]+>')
rows = []   # (key, r, ko, ja, en)
for f in sorted(glob.glob(os.path.join(D, 'data', '*.js'))):
    key = os.path.basename(f)[:-3]
    c = load(f)['cells']
    m = {L: {x['r']: html.unescape(TAG.sub('', x['h'])) for x in c[L]} for L in ('ko', 'ja', 'en')}
    for r in sorted(set(m['ko']) | set(m['ja']) | set(m['en'])):
        rows.append((key, r, m['ko'].get(r, ''), m['ja'].get(r, ''), m['en'].get(r, '')))
STOP = set('the of and a an to in is that it as by for with this be are was which on from at or his he not have has their its were they them we our but so all one also through can into who been had will would must when what there these those only may than then'.split())
def toks(s):
    return re.findall(r"[a-z][a-z'\-]*", s.lower())
grams_by_row = []
df = collections.Counter()
for row in rows:
    t = toks(row[4]); g = set()
    for n in (1, 2, 3, 4, 5):
        for i in range(len(t) - n + 1):
            w = t[i:i + n]
            if w[0] in STOP or w[-1] in STOP:
                continue
            g.add(' '.join(w))
    grams_by_row.append(g)
    df.update(g)
N = len(rows)
def best(ja, ko, k=4):
    hit = [i for i, r in enumerate(rows) if ja in r[3] and (not ko or ko.replace(' ', '') in r[2].replace(' ', ''))]
    if not hit:
        hit = [i for i, r in enumerate(rows) if ja in r[3]]
    if not hit:
        return 0, []
    c = collections.Counter()
    for i in hit:
        c.update(grams_by_row[i])
    out = []
    for g, a in c.items():
        if a < max(1, len(hit) * 0.3):
            continue
        b = df[g]
        dice = 2 * a / (len(hit) + b)
        out.append((dice * (1 + 0.15 * (len(g.split()) - 1)), g, a, b))
    out.sort(reverse=True)
    return len(hit), out[:k]
if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2].isdigit() and not os.path.exists(sys.argv[1] + "/dp"):
    pairs = json.load(open('pairs2.json', encoding='utf-8'))
    for p in pairs[:int(sys.argv[2])]:
        if not p['hit']:
            continue
        n, cands = best(p['ja_guess'], p['ko'])
        print(p['ja_guess'], p['ko'], n, ' | '.join(f'{g}({a}/{b})' for s, g, a, b in cands))

# 「한글(漢字)」の組を集め直す（数字の続きは1つと数える・互換漢字は NFC）。
# 番号つきの一覧 list.txt と、文脈つきの cands.json を出す
import json, re, glob, collections, sys, html, os, unicodedata
from shinjitai import to_ja
D = sys.argv[1]
def load(f):
    t = open(f, encoding='utf-8').read()
    return json.loads(t[t.index('{'):t.rstrip().rstrip(';').rindex('}') + 1])
TAG = re.compile(r'<rt>.*?</rt>|<rp>.*?</rp>|<[^>]+>')
HAN = re.compile(r'[㐀-鿿豈-﫿]')
PAREN = re.compile(r'\(([㐀-鿿豈-﫿·・,、 ]+)\)')
rows = {}
order = []
for f in sorted(glob.glob(os.path.join(D, 'data', '*.js'))):
    key = os.path.basename(f)[:-3]
    c = load(f)['cells']
    m = {L: {x['r']: unicodedata.normalize('NFC', html.unescape(TAG.sub('', x['h']))) for x in c[L]} for L in ('ko', 'ja', 'en')}
    for r in sorted(set(m['ko']) | set(m['ja']) | set(m['en'])):
        rows[(key, r)] = (m['ko'].get(r, ''), m['ja'].get(r, ''), m['en'].get(r, ''))
        order.append((key, r))
cnt = collections.Counter(); occ = collections.defaultdict(list)
for k in order:
    t = rows[k][0]
    for m in PAREN.finditer(t):
        hz = re.sub(r'\s+', ' ', m.group(1).strip())
        need = len(HAN.findall(hz))
        i = m.start(); got = 0; j = i
        while j > 0 and got < need:
            ch = t[j - 1]
            if '가' <= ch <= '힣':
                got += 1; j -= 1
            elif ch.isdigit():
                while j > 0 and t[j - 1].isdigit():
                    j -= 1
                got += 1
            elif ch == ' ' and got > 0 and j > 1 and ('가' <= t[j - 2] <= '힣' or t[j - 2].isdigit()):
                j -= 1
            else:
                break
        ko = t[j:i].strip()
        key = (ko, hz)
        cnt[key] += 1
        occ[key].append(k)
ja_all = '\n'.join(v[1] for v in rows.values())
out = []
for i, ((ko, hz), n) in enumerate(cnt.most_common()):
    jp = to_ja(hz).replace(' ', '')
    first = occ[(ko, hz)][0]
    hit = 'row' if jp in rows[first][1] else ('all' if jp in ja_all else '')
    out.append({'id': i + 1, 'ko': ko, 'hanja': hz, 'ja_guess': jp, 'hit': hit, 'n': n, 'occ': ['%s:%d' % o for o in occ[(ko, hz)][:6]]})
json.dump(out, open('cands.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
with open('list.txt', 'w', encoding='utf-8') as f:
    for o in out:
        f.write('%d %s %s%s %d\n' % (o['id'], o['ja_guess'], o['ko'], '' if o['hit'] else ' *', o['n']))
json.dump({'%s:%d' % k: v for k, v in rows.items()}, open('rows.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(out), collections.Counter(o['hit'] for o in out))

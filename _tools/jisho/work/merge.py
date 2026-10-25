# out*.jsonl（用語）と names.jsonl（人名・地名）を1つにまとめて terms.json にする。
# fixes.json があれば、id ごとの手直し（上書き・{"drop": true}）を最後に当てる
#   python -X utf8 merge.py <出力先 terms.json>
import json, sys, os, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
cands = {c['id']: c for c in json.load(open(os.path.join(HERE, 'cands.json'), encoding='utf-8'))}
fixes = json.load(open(os.path.join(HERE, 'fixes.json'), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'fixes.json')) else {}
FIELDS = ('id', 'cat', 'ja', 'yomi', 'ko', 'hanja', 'en', 'en_alt', 'ja_alt', 'ko_alt', 'ref', 'n')
out, dropped = [], []
def take(e, n):
    t = {k: e[k] for k in FIELDS if e.get(k) not in (None, '', [])}
    t['n'] = n
    return t
for f in sorted(glob.glob(os.path.join(HERE, 'out*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get('drop'):
            dropped.append(e); continue
        out.append(take(e, cands[e['id']]['n']))
if os.path.exists(os.path.join(HERE, 'names.jsonl')):
    for k, line in enumerate(l for l in open(os.path.join(HERE, 'names.jsonl'), encoding='utf-8') if l.strip()):
        e = json.loads(line)
        if e.get('drop'):
            continue
        e['id'] = 2001 + k
        pat = re.compile(r'\b' + re.escape(e['en']) + r'\b')
        n = sum(1 for v in rows.values() if pat.search(v[2]))
        out.append(take(e, n))
byid = {t['id']: t for t in out}
for k, v in fixes.items():
    i = int(k)
    if v.get('drop'):
        byid.pop(i, None)
    elif i in byid:
        byid[i].update({a: b for a, b in v.items() if a != 'note'})
    else:
        byid[i] = v
out = sorted(byid.values(), key=lambda t: t['id'])
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('terms', len(out), 'dropped', len(dropped))

# まとめた terms.json を見直す材料を出す
#   ../venv/Scripts/python -X utf8 review.py terms.json
# 1) 同じ ja・同じ ko・同じ en が2件以上  2) Sudachi のよみと違う  3) ja が漢字の直しと違う（hanja があるのに）
import json, sys, collections, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shinjitai import to_ja
from sudachipy import Dictionary, SplitMode
tok = Dictionary(dict='core').create()
def sudachi(s):
    k = ''.join(m.reading_form() for m in tok.tokenize(s, SplitMode.C))
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in k)
T = json.load(open(sys.argv[1], encoding='utf-8'))
for key in ('ja', 'ko', 'en'):
    c = collections.defaultdict(list)
    for t in T:
        c[t[key].lower().replace(' ', '')].append(t['id'])
    d = {k: v for k, v in c.items() if len(v) > 1}
    print('== 同じ', key, len(d))
    for k, v in d.items():
        print('  ', k, v, ' / '.join(next(f"{x['ja']}|{x['ko']}|{x['en']}" for x in T if x['id'] == i) for i in v))
print('== よみが Sudachi と違う')
for t in T:
    if t.get('yomi') and re.search(r'[一-龥]', t['ja']):
        s = sudachi(t['ja'])
        if s != t['yomi']:
            print('  ', t['id'], t['ja'], t['yomi'], '／ sudachi', s)
print('== 漢字の直しと ja が違う')
for t in T:
    if t.get('hanja'):
        g = to_ja(t['hanja']).replace(' ', '')
        if g != t['ja']:
            print('  ', t['id'], t['hanja'], '→', g, '／ ja', t['ja'], '|', t['ko'], '|', t['en'])

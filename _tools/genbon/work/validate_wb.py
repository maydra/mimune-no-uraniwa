# outN.jsonl を確かめる:  python -X utf8 validate_wb.py outN.jsonl wbN.json
import json, re, sys
want = {x['id']: x for x in json.load(open(sys.argv[2], encoding='utf-8'))}
MARK = re.compile(r'〔\d+〕')
HANGUL = re.compile(r'[가-힣]')
err = warn = 0; seen = set()
for ln, line in enumerate(open(sys.argv[1], encoding='utf-8'), 1):
    if not line.strip():
        continue
    try:
        e = json.loads(line)
    except Exception as ex:
        print(ln, 'JSON が読めない', ex); err += 1; continue
    i = e.get('id')
    if i not in want:
        print(ln, i, 'この束に無い id'); err += 1; continue
    if i in seen:
        print(ln, i, '同じ id が2回'); err += 1
    seen.add(i)
    ja = e.get('ja', '')
    ko = want[i]['ko']
    if not ja.strip():
        print(ln, i, 'ja が空'); err += 1; continue
    if MARK.findall(ja) != MARK.findall(ko):
        print(ln, i, '〔ページ〕の印が原文と違う', MARK.findall(ko), '→', MARK.findall(ja)); err += 1
    h = HANGUL.findall(ja)
    if h:
        print(ln, i, 'ハングルが残っている:', ''.join(h)[:20]); err += 1
    r = len(MARK.sub('', ja)) / max(1, len(MARK.sub('', ko)))
    if not e.get('heading') and len(ko) > 40 and not (0.75 <= r <= 2.0):
        print(ln, i, f'注意: 長さの比 {r:.2f}（訳し落とし・付け足しが無いか）'); warn += 1
miss = sorted(set(want) - seen)
if miss:
    print('出力の無い id:', miss[:30], '…' if len(miss) > 30 else ''); err += 1
print('lines', len(seen), 'errors', err, 'warnings', warn)

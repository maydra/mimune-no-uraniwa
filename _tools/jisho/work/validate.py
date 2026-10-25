# out*.jsonl を確かめる。ref の段落に ja・ko・en がそのまま出ているか、en_alt が英語のどこかに出るか
#   python -X utf8 validate.py out1.jsonl [batch1.json]
import json, sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, 'rows.json'), encoding='utf-8'))
en_all = '\n'.join(v[2] for v in rows.values()).lower()
KANA = re.compile(r'^[ぁ-ゖー・ 　]+$')
errs = 0; seen = set(); n = 0
for ln, line in enumerate(open(sys.argv[1], encoding='utf-8'), 1):
    line = line.strip()
    if not line:
        continue
    try:
        e = json.loads(line)
    except Exception as ex:
        print(ln, 'JSON が読めない', ex); errs += 1; continue
    n += 1
    seen.add(e.get('id'))
    if e.get('drop'):
        if not e.get('reason'):
            print(ln, e.get('id'), 'drop には reason を付ける'); errs += 1
        continue
    bad = []
    for k in ('id', 'cat', 'ja', 'ko', 'en', 'ref'):
        if not e.get(k):
            bad.append('%s が空' % k)
    if e.get('cat') not in ('P', 'F', 'H', 'L', 'N'):
        bad.append('cat は P/F/H/L/N')
    ref = e.get('ref', '')
    if ref not in rows:
        bad.append('ref %r が無い（"1-1-1:3" の形）' % ref)
    else:
        ko, ja, en = rows[ref]
        if e.get('ja') and e['ja'] not in ja:
            bad.append('ja %r が ref の日本語に無い' % e['ja'])
        if e.get('ko') and e['ko'].replace(' ', '') not in ko.replace(' ', ''):
            bad.append('ko %r が ref の韓国語に無い' % e['ko'])
        if e.get('en') and e['en'].lower() not in en.lower():
            bad.append('en %r が ref の英語に無い' % e['en'])
    for a in e.get('en_alt') or []:
        if a.lower() not in en_all:
            bad.append('en_alt %r が英語のどこにも無い' % a)
    y = e.get('yomi', '')
    if re.search(r'[一-鿿]', e.get('ja', '')):
        if not y or not KANA.match(y):
            bad.append('漢字を含む ja には yomi（ひらがな）が要る')
    if bad:
        errs += 1
        print(ln, e.get('id'), e.get('ja'), '／'.join(bad))
if len(sys.argv) > 2:
    want = {c['id'] for c in json.load(open(sys.argv[2], encoding='utf-8'))}
    miss = sorted(want - seen)
    if miss:
        print('出力の無い id:', miss); errs += 1
print('lines', n, 'errors', errs)

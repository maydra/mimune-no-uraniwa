# raw/<番号>.html → pages.jsonl（記事ごとの題・巻・ページ・行の並び）。行は ja / mix（漢字まじりの韓国語）/ ko（ハングルだけ）
import os, re, json, html, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
KANA = re.compile(r'[ぁ-ゖァ-ヺ]')
HANGUL = re.compile(r'[가-힣]')
HAN = re.compile(r'[一-鿿]')

def kind(s):
    k, h, z = len(KANA.findall(s)), len(HANGUL.findall(s)), len(HAN.findall(s))
    if k >= 2 and k >= h:
        return 'ja'
    if h == 0:
        return 'other'
    return 'mix' if z >= max(2, h * 0.08) else 'ko'

out = []
for f in sorted(glob.glob(os.path.join(HERE, 'raw', '*.html')), key=lambda p: int(re.sub(r'\D', '', os.path.basename(p)) or 0)):
    n = int(os.path.basename(f)[:-5])
    t = open(f, encoding='utf-8').read()
    title = re.search(r'dataname: "([^"]*)",\s*parid', t)
    title = title.group(1) if title else ''
    m = re.search(r'tx-content-container">(.*?)<script', t, re.S)
    body = m.group(1) if m else ''
    body = re.sub(r'<br\s*/?>|</p>|</div>|<p[^>]*>|<div[^>]*>', '\n', body)
    imgs = len(re.findall(r'<img', body))
    text = html.unescape(re.sub(r'<[^>]+>', '', body)).replace('\xa0', ' ')
    lines = [re.sub(r'[ \t　]+', ' ', l).strip() for l in text.split('\n')]
    lines = [l for l in lines if l]
    vm = re.search(r'(\d)\s*巻\s*\(?\s*(\d+)\s*ページ', title)
    out.append({'n': n, 'title': title, 'vol': int(vm.group(1)) if vm else None, 'page': int(vm.group(2)) if vm else None,
                'imgs': imgs, 'lines': [[kind(l), l] for l in lines]})
with open(os.path.join(HERE, 'pages.jsonl'), 'w', encoding='utf-8') as w:
    for p in out:
        w.write(json.dumps(p, ensure_ascii=False) + '\n')
# まとめ
c = collections.Counter()
by_vol = collections.defaultdict(list)
for p in out:
    by_vol[p['vol']].append(p['page'])
    kinds = collections.Counter(k for k, _ in p['lines'])
    c['ja'] += kinds['ja']; c['mix'] += kinds['mix']; c['ko'] += kinds['ko']; c['other'] += kinds['other']
    c['has_ko_hangul_page'] += 1 if kinds['ko'] else 0
    c['imgs'] += p['imgs']
print(len(out), dict(c))
for v, ps in sorted(by_vol.items(), key=lambda x: (x[0] is None, x[0])):
    ps2 = sorted(x for x in ps if x is not None)
    print('vol', v, len(ps), ps2[:3], ps2[-3:], 'gaps', [x for x in range(ps2[0], ps2[-1] + 1) if x not in ps2][:20] if ps2 else '')
print([p['title'] for p in out if p['vol'] is None][:10])

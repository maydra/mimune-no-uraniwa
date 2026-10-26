# Daum カフェ「천일국 경전방」の掲示板 WD3Y（原理原本 (김현주)）の記事を全部落として raw/ に貯める
#   python -X utf8 crawl.py
# 一度落とした記事は取り直さない。無い番号は raw/missing.txt に書く（gyeong-parallel/scripts/crawl.py と同じやり方）
import os, re, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
CAFE, FLD = 'ckatkfkdrhdqn', 'WD3Y'
UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ko,ja;q=0.8'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')

os.makedirs(RAW, exist_ok=True)
top = max(int(x) for x in re.findall(r'dataid: (\d+),', fetch(f'https://m.cafe.daum.net/{CAFE}/{FLD}?boardType=')))
miss_path = os.path.join(RAW, 'missing.txt')
missing = set(open(miss_path).read().split()) if os.path.exists(miss_path) else set()
got = 0
for i in range(1, top + 1):
    path = os.path.join(RAW, f'{i}.html')
    if os.path.exists(path) or str(i) in missing:
        continue
    body = None
    for attempt in range(3):
        try:
            body = fetch(f'https://m.cafe.daum.net/{CAFE}/{FLD}/{i}')
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                break
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    if body is None or 'tx-content-container' not in body:
        missing.add(str(i))
        open(miss_path, 'a').write(f'{i}\n')
    else:
        open(path, 'w', encoding='utf-8').write(body)
        got += 1
    time.sleep(0.7)
print('top', top, 'got', got, 'missing', len(missing))

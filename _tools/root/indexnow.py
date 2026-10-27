# -*- coding: utf-8 -*-
"""変わったページの URL を IndexNow で Bing などに知らせる（Google は IndexNow を使っていない）。

GitHub Actions（.github/workflows/sitemap.yml）が、build_sitemap.py --stamp --changed FILE の
あとに回す。ふだんは手で回さなくていい。
    python _tools/root/indexnow.py changed.txt      # 1行1URL

鍵はリポジトリの根の <鍵>.txt（中身も同じ鍵）。サイトに置いた鍵のファイルで持ち主を確かめる仕組みなので、
鍵は秘密ではない。鍵のファイルがサイトのフォルダ（/mimune-no-uraniwa/）にあるので、
知らせられるのはこのフォルダの下の URL だけ（それで足りる）。
鍵を変えるときは、新しい .txt を置いて古いのを消すだけでいい。
"""
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://maydra.github.io/mimune-no-uraniwa/'
ENDPOINT = 'https://api.indexnow.org/indexnow'
BATCH = 10000  # 1回に送れる上限


def find_key():
    for p in ROOT.glob('*.txt'):
        if re.fullmatch(r'[0-9a-f]{32}', p.stem) and p.read_text(encoding='utf-8').strip() == p.stem:
            return p.stem
    sys.exit('鍵のファイル（<32桁の16進>.txt）がリポジトリの根に無い')


def wait_until_live(location, key, minutes=10):
    """鍵のファイルを足した push では、GitHub Pages に出るまで数分かかる。出る前に送ると断られる。"""
    for _ in range(minutes * 4):
        try:
            with urllib.request.urlopen(f'{location}?t={time.time():.0f}', timeout=20) as r:
                if r.read().decode('utf-8', 'replace').strip() == key:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(15)
    return False


def main(path):
    urls = [u.strip() for u in open(path, encoding='utf-8') if u.strip().startswith(BASE)]
    if not urls:
        print('知らせるページなし')
        return
    key = find_key()
    location = f'{BASE}{key}.txt'
    if not wait_until_live(location, key):
        sys.exit(f'{location} がサイトに出ていない')
    for i in range(0, len(urls), BATCH):
        part = urls[i:i + BATCH]
        body = json.dumps({'host': 'maydra.github.io', 'key': key, 'keyLocation': location,
                           'urlList': part}).encode('utf-8')
        req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                print(f'{len(part)} URLs → {r.status}')  # 200 か 202 なら受け付けられた
        except urllib.error.HTTPError as e:
            # 403: 鍵が合わない、422: URL が鍵の場所の外、429: 送りすぎ
            sys.exit(f'{len(part)} URLs → {e.code} {e.read()[:300]!r}')


if __name__ == '__main__':
    main(sys.argv[1])

# -*- coding: utf-8 -*-
"""Search Console の API で、サイトマップを送り、各ページが Google に載っているかを調べる。

    python _tools/root/search_console.py submit             # sitemap-index.xml を送る（送り直す）
    python _tools/root/search_console.py inspect --limit 1800 --max-age 6
        # 調べてから6日以上たったページに、古い順に URL 検査をかけ、
        # _tools/seo/index-status.json と index-status.md を書き直す

GitHub Actions が回す（submit は .github/workflows/sitemap.yml でページが変わったとき、
inspect は .github/workflows/index-status.yml で毎日）。手元で回すときは、鍵の JSON の場所を
環境変数 GSC_KEY_FILE に入れる。Actions では secret の GSC_KEY に鍵の JSON の中身を入れてある。

鍵はサービスアカウント online-count@mimune-online.iam.gserviceaccount.com のもの（ホームの「いま○人」と同じ）。
Search Console の「ユーザーと権限」に「フル」で足してある（submit に要る）。

URL 検査は1日 2,000 件・1分 600 件まで（上限は太平洋時間の0時に戻る）。ページは 3,600 余りなので、
毎日、調べてから6日以上たったページを調べると、1日 500 件ほどで1週間に一回りする。
Google の「インデックス登録をリクエスト」は API では送れない（Indexing API は求人とライブ配信専用）。
"""
import collections
import concurrent.futures
import datetime
import html
import json
import os
import pathlib
import re
import sys
import threading
import time
from urllib.parse import quote, unquote

import requests
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = 'https://maydra.github.io/mimune-no-uraniwa/'
SAFE = "/!$&'()*+,;=:@~"  # build_sitemap.py と同じ（& は %26 にしない）
API = 'https://searchconsole.googleapis.com'
SITE = quote(BASE, safe='')
PAGES = ROOT / '_tools' / 'root' / 'sitemap-lastmod.json'
STATUS = ROOT / '_tools' / 'seo' / 'index-status.json'
REPORT = ROOT / '_tools' / 'seo' / 'index-status.md'
JST = datetime.timezone(datetime.timedelta(hours=9))


def session():
    info = os.environ.get('GSC_KEY')
    scopes = ['https://www.googleapis.com/auth/webmasters']
    if info:
        creds = service_account.Credentials.from_service_account_info(json.loads(info), scopes=scopes)
    else:
        creds = service_account.Credentials.from_service_account_file(os.environ['GSC_KEY_FILE'], scopes=scopes)
    s = AuthorizedSession(creds)
    # 鍵が違う・Search Console から外されたときは、ここで止める（あとの URL 検査は失敗を数えるだけなので気づけない）
    r = s.get(f'{API}/webmasters/v3/sites', timeout=60)
    if not r.ok or BASE not in r.text:
        sys.exit(f'Search Console に入れない: {r.status_code} {r.text[:300]}')
    return s


def url(rel):
    return BASE if rel == 'index.html' else BASE + quote(rel, safe=SAFE)


def submit(s):
    feed = quote(BASE + 'sitemap-index.xml', safe='')
    r = s.put(f'{API}/webmasters/v3/sites/{SITE}/sitemaps/{feed}', timeout=60)
    print('submit sitemap-index.xml →', r.status_code)
    r.raise_for_status()


STOP = threading.Event()


def inspect_one(s, rel):
    for wait in (0, 5, 65):
        if STOP.is_set():
            return rel, None, 'stopped'
        time.sleep(wait)
        # timeout が無いと、返事の来ない接続を待ち続けて止まる（2026-10-28、手元で30分止まった）
        try:
            r = s.post(f'{API}/v1/urlInspection/index:inspect', timeout=60,
                       json={'inspectionUrl': url(rel), 'siteUrl': BASE, 'languageCode': 'ja'})
        except requests.RequestException as e:
            last = repr(e)[:200]
            continue
        if r.status_code == 429 or r.status_code >= 500:
            last = f'{r.status_code} {r.text[:200]}'
            continue
        if r.status_code != 200:
            return rel, None, f'{r.status_code} {r.text[:200]}'
        x = r.json()['inspectionResult']['indexStatusResult']
        return rel, {'verdict': x.get('verdict'), 'state': x.get('coverageState'),
                     'crawled': x.get('lastCrawlTime', '')[:10],
                     # Google が選んだ正規の URL がこのページと違うとき（重複とみなされた）だけ残す
                     'canonical': x.get('googleCanonical') if x.get('googleCanonical') not in (None, url(rel)) else None,
                     'checked': datetime.datetime.now(JST).date().isoformat()}, None
    # 1分あたりの上限なら待てば通る。1分待っても通らないのは1日の上限か Google の不調なので、全部やめる
    # （ここまでの分は書く）
    STOP.set()
    return rel, None, last


def save(status):
    STATUS.parent.mkdir(exist_ok=True)
    lines = ',\n'.join(f'{json.dumps(k, ensure_ascii=False)}: {json.dumps(status[k], ensure_ascii=False)}'
                       for k in sorted(status))
    STATUS.write_text('{\n' + lines + '\n}\n', encoding='utf-8', newline='\n')


def inspect(s, limit, max_age):
    pages = sorted(json.loads(PAGES.read_text(encoding='utf-8')))
    listed = set(pages)
    status = json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.exists() else {}
    # サイトマップから消えたページは忘れる
    status = {k: v for k, v in status.items() if k in listed}
    # 調べてから max_age 日たっていないページは飛ばす
    since = (datetime.datetime.now(JST).date() - datetime.timedelta(days=max_age)).isoformat()
    due = [rel for rel in pages if status.get(rel, {}).get('checked', '') <= since]
    # まだ調べていないページ → 調べたのが古いページ、の順。同じなら聖書（ほかのサイトにも同じ本文がある）は後
    todo = sorted(due, key=lambda rel: (rel in status, status.get(rel, {}).get('checked', ''),
                                        rel.startswith('Bible_out/'), rel))[:limit]
    errors = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, (rel, result, err) in enumerate(pool.map(lambda rel: inspect_one(s, rel), todo), 1):
            if result:
                status[rel] = result
            else:
                errors += 1
                if err != 'stopped':
                    print('  ', rel, err, flush=True)
            # 途中で落ちても、ここまでの分は残す
            if i % 100 == 0:
                save(status)
                print(f'{i}/{len(todo)}', flush=True)
    save(status)
    print(f'inspected {len(todo) - errors}, errors {errors}, known {len(status)}/{len(pages)}')
    report(s, pages, status)


def book_title(folder):
    p = ROOT / folder / 'index.html'
    if not p.exists():
        return folder
    m = re.search(r'(?is)<title[^>]*>(.*?)</title>', p.read_text(encoding='utf-8', errors='replace'))
    # 「目次/文鮮明先生の平和思想」「◆目次・伝道ハンドブック◆」「原理講論 | 目次」から本の名前だけを残す
    parts = re.split(r'\s*[|｜/／]\s*', html.unescape(m.group(1)).strip('◆ ') if m else '')
    keep = [re.sub(r'(?:総合|全章詳細リンク)?(?:目次|もくじ)[・\s-]*|\s*-\s*$', '', p).strip(' -◆・　_')
            for p in parts]
    return '／'.join(k for k in keep if k and k != 'み旨の裏庭') or folder


def report(s, pages, status):
    today = datetime.datetime.now(JST).date()
    states = collections.Counter(v['state'] for v in status.values())
    books = collections.defaultdict(collections.Counter)
    for rel in pages:
        folder = rel.split('/')[0] if '/' in rel else '(トップ)'
        v = status.get(rel)
        books[folder]['pages'] += 1
        if v and v['verdict'] == 'PASS':
            books[folder]['indexed'] += 1
        else:
            books[folder][v['state'] if v else 'まだ調べていない'] += 1
    out = [f'# Google のインデックス状況（{today.isoformat()} 更新）', '',
           '`_tools/root/search_console.py inspect` が毎日（Actions の index-status）書き直す。手で直さない。', '',
           f'サイトマップのページ {len(pages)}、調べたページ {len(status)}。', '', '## 状態ごと', '']
    out += [f'- {state}: {n}' for state, n in states.most_common()]
    out += ['', '## 本ごと（載っている / ページ数）', '', '| 本 | 載っている | ページ | 載っていない理由 |', '|---|---:|---:|---|']
    for folder in sorted(books, key=lambda f: (-books[f]['indexed'], f)):
        c = books[folder]
        why = '、'.join(f'{k} {n}' for k, n in c.most_common() if k not in ('pages', 'indexed'))
        name = '(トップ)' if folder == '(トップ)' else book_title(folder)
        out.append(f'| {name} | {c["indexed"]} | {c["pages"]} | {why} |')
    dup = [(rel, v['canonical']) for rel, v in sorted(status.items()) if v.get('canonical')]
    if dup:
        out += ['', '## Google が別の URL を正規に選んだページ', '']
        out += [f'- {rel} → {canon}' for rel, canon in dup[:100]]
    # 検索での表示とクリック（直近28日。Search Console の数字は2〜3日遅れる）
    end = today - datetime.timedelta(days=3)
    r = s.post(f'{API}/webmasters/v3/sites/{SITE}/searchAnalytics/query', timeout=60,
               json={'startDate': (end - datetime.timedelta(days=27)).isoformat(), 'endDate': end.isoformat(),
                     'dimensions': ['page'], 'rowLimit': 1000})
    rows = r.json().get('rows', []) if r.ok else []
    out += ['', f'## 検索での表示（{end - datetime.timedelta(days=27)}〜{end}）', '',
            f'表示されたページ {len(rows)}、表示 {sum(int(x["impressions"]) for x in rows)} 回、'
            f'クリック {sum(int(x["clicks"]) for x in rows)} 回', '', '| ページ | 表示 | クリック |', '|---|---:|---:|']
    for x in sorted(rows, key=lambda x: -x['impressions'])[:30]:
        out.append(f'| {unquote(x["keys"][0]).replace(BASE, "/")} | {int(x["impressions"])} | {int(x["clicks"])} |')
    REPORT.write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    args = sys.argv[1:]
    s = session()
    if args[:1] == ['submit']:
        submit(s)
    elif args[:1] == ['inspect']:
        inspect(s, int(args[args.index('--limit') + 1]) if '--limit' in args else 1800,
                int(args[args.index('--max-age') + 1]) if '--max-age' in args else 6)
    else:
        sys.exit(__doc__)

"""目次ページを検索の対象外にする。

サイト内検索（pagefind）は目次ページも普通のページとして索引に入れる。
目次には収録されている全部の題が並んでいるので、何を検索しても目次ばかりが
先に出てきてしまう。目次の <body> に data-pagefind-ignore を付けておくと、
pagefind はそのページを索引に入れない。

対象:
  - ファイル名が index*.html / Index*.html / mokuji*.html / *_mokuji.html
  - <title> に「目次」か「もくじ」が入っているページ

使い方:
  python tools/mark_search_ignore.py          # 付ける
  python tools/mark_search_ignore.py --check  # 付ける対象を数えるだけ

付けたあとは索引の作り直しが必要:
  npx pagefind@1.3.0 --site .
"""

import os
import re
import sys

SKIP_DIRS = {'.git', 'pagefind', 'node_modules', '__pycache__', 'theme'}
NAME_RE = re.compile(r'^(?:index.*|mokuji.*|.*_mokuji)\.html?$', re.IGNORECASE)
TITLE_RE = re.compile(r'<title>([^<]*)</title>', re.IGNORECASE)
BODY_RE = re.compile(r'<body\b', re.IGNORECASE)
ATTR = 'data-pagefind-ignore'


def is_toc(path, text):
    if NAME_RE.match(os.path.basename(path)):
        return True
    m = TITLE_RE.search(text)
    return bool(m) and ('目次' in m.group(1) or 'もくじ' in m.group(1))


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(('.html', '.htm')):
                yield os.path.join(dirpath, name)


def main():
    check_only = '--check' in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    marked = already = no_body = 0
    for path in walk(root):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue

        if not is_toc(path, text):
            continue
        if ATTR in text:
            already += 1
            continue

        m = BODY_RE.search(text)
        if not m:
            no_body += 1
            print(f'  <body> が無い: {os.path.relpath(path, root)}')
            continue

        marked += 1
        if check_only:
            continue
        end = m.end()
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text[:end] + f' {ATTR}' + text[end:])

    verb = '付ける対象' if check_only else '付けた'
    print(f'{verb}: {marked}件 / すでに付いている: {already}件 / <body>無し: {no_body}件')


if __name__ == '__main__':
    main()

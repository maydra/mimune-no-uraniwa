# -*- coding: utf-8 -*-
"""各ページに埋め込まれた <style> を、共有の CSS ファイルへ出す（何度回してもよい）。

4,000ページの <style> は中身が60通りしかなく、同じ CSS（1ページ約10KB、合計28MB）を
ページを移るたびに読み直していた。2ページ以上で使われている <style> は
theme/pages/<中身のハッシュ>.css に書き出し、元の場所を <link> に置き換える
（同じ位置に置くので、CSS の効く順番は変わらない）。

ついでに、スマホで重いものを落とす（2026-10-11、iPhone SE で dp のスクロールが引っかかった）:
  ・backdrop-filter（本文を包む .container や .content-card にまで掛かっていた）
  ・開いたときにふわっと出す animation: fadeInDown / fadeInUp
  ・Google Fonts は Noto Serif JP の 400 と 700 だけ（500/900 と Crimson Pro をやめる）
1ページだけの <style> は外に出さず、その場で同じ削り方をする。

属性つきの <style id="…">（スクリプトが探すもの）と、download/ の1ファイル版・
offline.html（それだけで表示できないといけない）は触らない。

リポジトリの根から:
    python _tools/root/extract_inline_css.py          # 書き換える
    python _tools/root/extract_inline_css.py --dry    # 数えるだけ
"""
import hashlib
import os
import re
import subprocess
import sys
import time
from collections import Counter

DRY = '--dry' in sys.argv
OUT_DIR = 'theme/pages'
VERSION = time.strftime('%Y%m%d%H%M')
MIN_USES = 2
MIN_BYTES = 300
SKIP = re.compile(r'^(download/|_tools/|offline\.html$)')

STYLE_RE = re.compile(r'<style>(.*?)</style>', re.S)
FONT_RE = re.compile(r'https://fonts\.googleapis\.com/css2\?family=Noto\+Serif\+JP[^"\']*')


def lighten(css):
    css = re.sub(r'[ \t]*(?:-webkit-)?backdrop-filter\s*:[^;{}]*;[ \t]*\r?\n?', '', css)
    css = re.sub(r'[ \t]*animation\s*:\s*fadeIn(?:Down|Up)\b[^;{}]*;[ \t]*\r?\n?', '', css)
    return css


def font_href(m):
    amp = '&amp;' if '&amp;' in m.group(0) else '&'
    return 'https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700' + amp + 'display=swap'


def key(block):
    return hashlib.sha1(block.encode('utf-8')).hexdigest()[:10]


def main():
    files = [f for f in subprocess.run(['git', 'ls-files', '*.html'], capture_output=True,
                                       text=True, encoding='utf-8').stdout.split('\n')
             if f and not SKIP.match(f)]
    texts = {}
    uses = Counter()
    for f in files:
        try:
            with open(f, encoding='utf-8', newline='') as fh:
                s = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        texts[f] = s
        for b in STYLE_RE.findall(s):
            uses[key(b)] += 1

    shared = {}
    changed = 0
    for f, s in texts.items():
        rel = os.path.relpath(OUT_DIR, os.path.dirname(f) or '.').replace('\\', '/')

        def repl(m):
            b = m.group(1)
            k = key(b)
            if uses[k] >= MIN_USES and len(b.encode('utf-8')) >= MIN_BYTES:
                shared[k] = lighten(b)
                return '<link rel="stylesheet" href="%s/%s.css?v=%s">' % (rel, k, VERSION)
            return '<style>' + lighten(b) + '</style>'

        t = STYLE_RE.sub(repl, s)
        t = FONT_RE.sub(font_href, t)
        if t != s:
            changed += 1
            if not DRY:
                with open(f, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(t)

    if not DRY:
        os.makedirs(OUT_DIR, exist_ok=True)
        for k, css in shared.items():
            with open(os.path.join(OUT_DIR, k + '.css'), 'w', encoding='utf-8', newline='') as fh:
                fh.write('/* _tools/root/extract_inline_css.py が書き出した。直すときは、これを直接直してよい */\n')
                fh.write(css.strip('\r\n') + '\n')
    print('pages changed:', changed, '/ shared css files:', len(shared), '(dry run)' if DRY else '')


if __name__ == '__main__':
    main()

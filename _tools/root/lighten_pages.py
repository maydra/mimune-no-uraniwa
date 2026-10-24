"""lighten_pages.py — 2026-10-24 の軽量化で、全ページを一括で書き換える。

使い方（リポジトリの根から。何度回しても同じ結果になる）:
    python _tools/root/lighten_pages.py webfont     # Google Fonts の <link> を外し、端末の明朝にする
    python _tools/root/lighten_pages.py theme-boot  # <body> の直後で配色を決める（明るい設定の人の「暗→白」のちらつき防止）
    python _tools/root/lighten_pages.py marquee     # 旧サイトの <marquee> の帯と「INDEXへ」を消す
    python _tools/root/lighten_pages.py og-image    # og:image を og-image.png（1.4MB）から og-image.jpg へ

- `_` で始まるフォルダと .git は触らない
- webfont は、韓国語のフォント（Noto Serif KR）を読んでいるページ（seika/）は触らない
- theme-boot は theme/style.css か theme/script.js を読んでいるページだけ（古い黒地のページには要らない）
- 回したあとは python _tools/root/cache_bust.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 端末に入っている明朝。iPhone/Mac はヒラギノ、Windows は BIZ UDP明朝（10 以降。游明朝より
# 画面で読みやすい）→ 游明朝、Linux は Noto Serif CJK。Android には明朝が無いので、
# theme/script.js が Android のときだけ Google Fonts の Noto Serif JP を読む。
FONT_STACK = '"Hiragino Mincho ProN", "BIZ UDPMincho", "Yu Mincho", YuMincho, "Noto Serif CJK JP", "Noto Serif JP", serif'

FONT_LINK_RE = re.compile(
    r'[ \t]*<link\s[^>]*fonts\.googleapis\.com/css2\?family=Noto\+Serif\+JP:wght@400;700&(?:amp;)?display=swap[^>]*>[ \t]*\r?\n?')
PRECONNECT_RE = re.compile(
    r'[ \t]*<link\s+rel="preconnect"\s+href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>[ \t]*\r?\n?')
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*[^;}]*Noto Serif JP[^;}]*")

# <body> の直後に置く。localStorage の theme（system/light/dark）と、reader.js の文字の大きさ。
# theme/script.js の applyTheme と同じ決め方（端末の設定に合わせる → 明るい → 暗い）。
BOOT = ('<script id="theme-boot">(function(){try{var c=document.body.classList,'
        "t=localStorage.getItem('theme');"
        "if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
        "c.remove('light-mode','dark-mode');c.add(t+'-mode');"
        "var f=localStorage.getItem('reader.font');if(f)document.documentElement.style.fontSize=f}"
        'catch(e){}})()</script>')
BODY_RE = re.compile(r'<body\b[^>]*>', re.I)

MARQUEE_RES = [
    re.compile(r'[ \t]*<b><marquee behavior="slide"[^>]*>.*?</marquee></b>[ \t]*\r?\n?', re.S),
    re.compile(r'[ \t]*<marquee behavior="slide"[^>]*>.*?</marquee>[ \t]*\r?\n?', re.S),
    re.compile(r'[ \t　]*<marquee behavior="alternate"[^>]*>.*?</marquee>', re.S),
    re.compile(r'[ \t　]*<a href="[^"]*index\.html" style="color : red;" target="_top">INDEXへ</a>[ \t]*\r?\n?'),
]


def pages():
    for p in ROOT.rglob('*.html'):
        rel = p.relative_to(ROOT)
        if any(part.startswith(('_', '.')) or part == 'node_modules' for part in rel.parts[:-1]):
            continue
        yield p


def read(p):
    with open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def do_webfont(s):
    if 'Noto+Serif+KR' in s:
        return s
    s = FONT_LINK_RE.sub('', s)
    s = PRECONNECT_RE.sub('', s)
    s = FONT_FAMILY_RE.sub('font-family: ' + FONT_STACK, s)
    return s


def do_theme_boot(s):
    if 'id="theme-boot"' in s:
        return s
    if 'theme/style.css' not in s and 'theme/script.js' not in s:
        return s
    m = BODY_RE.search(s)
    if not m:
        return s
    return s[:m.end()] + '\n' + BOOT + s[m.end():]


def do_marquee(s):
    for r in MARQUEE_RES:
        s = r.sub('', s)
    return s


def do_og_image(s):
    return s.replace('og-image.png', 'og-image.jpg')


STEPS = {'webfont': do_webfont, 'theme-boot': do_theme_boot, 'marquee': do_marquee, 'og-image': do_og_image}


def main():
    names = sys.argv[1:] or []
    if not names or any(n not in STEPS for n in names):
        print(__doc__)
        sys.exit(1)
    for name in names:
        fn = STEPS[name]
        changed = 0
        seen = 0
        for p in pages():
            seen += 1
            before = read(p)
            after = fn(before)
            if after != before:
                write(p, after)
                changed += 1
        print(f'{name}: {changed} / {seen} ページを書き換えた')


if __name__ == '__main__':
    main()

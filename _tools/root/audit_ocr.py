# -*- coding: utf-8 -*-
"""OCR 由来の誤字を洗い出す。

本文は OCR 起こしなので、字形の近い別字に化けている箇所が残っている。
目で読んで見つけるのは無理なので、3つの当て方で候補を出す。

  1. 頻度の外れ値 … 1文字だけ違う語のペアで、片方が何十回も出るのに
                     もう片方が1〜2回しか出ないもの（享進/亨進、統一数会 など）
  2. 年号の形     … 「一九XX年」から外れた漢数字（二九八四年、一九八八四年 など）
  3. 化けた文字   … □ ■ � が本文に紛れているもの（□ は「口」のことが多い）

使い方:
    python audit_ocr.py                  # サイト全体
    python audit_ocr.py syougairotei_10  # フォルダを指定

出た候補は「怪しい」止まりで、誤字と決まったわけではない。原理用語
（共生主義・共栄主義・共義主義 など）や、ご兄弟のお名前どうし（文興進様と
文國進様は1文字違い）は正しくても引っかかる。必ず前後の文を読んで決めること。
"""
import re, html, glob, os, sys
from collections import defaultdict, Counter

TAG = re.compile(r'(?s)<(script|style)[^>]*>.*?</\1>')
ANYTAG = re.compile(r'<[^>]+>')
KANJI = re.compile(r'[一-鿿]+')
KATA = re.compile(r'[ァ-ヶ][ァ-ヶー・]+')
NUM = set('〇一二三四五六七八九十百千万億零壱弐参')

# 旧字と新字など、正しい揺れ
VARIANT = """顯顕 惠恵 譽誉 國国 權権 榮栄 眞真 會会 學学 體体 點点 氣気 實実 變変
禮礼 屬属 歸帰 斷断 聲声 壽寿 龍竜 藝芸 廣広 據拠 餘余 圓円 獨独 觀観 關関 經経
齊斉 澤沢 邊辺 灣湾 舊旧 雜雑 數数 戰戦 發発 營営 傳伝 當当 總総 黨党 豐豊 鐵鉄""".split()
VARSET = set()
for pair in VARIANT:
    VARSET.add((pair[0], pair[1])); VARSET.add((pair[1], pair[0]))

MIN_COMMON, MAX_RARE, RATIO = 10, 2, 20


def visible_text(path):
    s = open(path, encoding='utf-8').read()
    return re.sub(r'[ \t　]+', ' ', html.unescape(ANYTAG.sub(' ', TAG.sub(' ', s))))


def main(scope):
    paths = sorted(glob.glob(os.path.join(scope, '**', '*.html'), recursive=True))
    counts, sample = Counter(), {}
    years, boxes = [], []

    for p in paths:
        try:
            t = visible_text(p)
        except Exception:
            continue
        rel = p.replace('\\', '/')

        def ctx(m, w=70):
            return re.sub(r'\s+', ' ', t[max(0, m.start() - w):m.end() + w]).strip()

        for rx in (KANJI, KATA):
            for m in rx.finditer(t):
                tok = m.group()
                if not (3 <= len(tok) <= 12):
                    continue
                counts[tok] += 1
                sample.setdefault(tok, (rel, ctx(m)))

        for m in re.finditer(r'[〇一二三四五六七八九]{4,7}年', t):
            g = m.group()
            if re.match(r'^(一九|二〇)[〇一二三四五六七八九]{2}年$', g):
                continue
            years.append((rel, g, ctx(m)))
        for m in re.finditer(r'[□■�]', t):
            boxes.append((rel, m.group(), ctx(m, 45)))

    bucket = defaultdict(list)
    for tok in counts:
        for i in range(len(tok)):
            bucket[(i, tok[:i] + '\0' + tok[i+1:])].append(tok)

    pairs = {}
    for toks in bucket.values():
        for i in range(len(toks)):
            for j in range(i + 1, len(toks)):
                a, b = toks[i], toks[j]
                ca, cb = counts[a], counts[b]
                if ca < cb:
                    a, b, ca, cb = b, a, cb, ca
                if ca < MIN_COMMON or cb > MAX_RARE or ca < cb * RATIO:
                    continue
                d = [(x, y) for x, y in zip(a, b) if x != y][0]
                if d in VARSET or d[0] in NUM or d[1] in NUM:
                    continue
                pairs.setdefault((a, b), (ca, cb) + sample.get(b, ('?', '?')))

    print('## 年号の形がおかしい (%d件) — 檀紀・皇紀・実在の西暦も混ざる' % len(years))
    for rel, g, c in years:
        print('  [%s] %s :: %s' % (g, rel, c))

    print('\n## 化けた文字 (%d件) — □ はたいてい「口」' % len(boxes))
    for rel, g, c in boxes[:120]:
        print('  [%s] %s :: %s' % (g, rel, c))

    rows = sorted(pairs.items(), key=lambda kv: -kv[1][0])
    print('\n## 頻度の外れ値 (%d件) — 左が頻出、右が誤字候補' % len(rows))
    for (a, b), (ca, cb, rel, c) in rows:
        print('  %s -> %s (%d:%d) %s\n      %s' % (a, b, ca, cb, rel, c))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')

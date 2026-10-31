# -*- coding: utf-8 -*-
"""『平和経』の英語を、韓日英の連載（Daum の掲示板 VfHJ「평화경 - 韓/日/英」）から抜き出して src/VfHJ-en.jsonl に書く。

連載は記事 1492〜2010 で、1記事＝講演の中の小見出し1つ。1記事の中に 韓 → 日 → 英 の順で同じ所が入っている。
全178講演のうち73講演しか無い（2026-10-31。掲示板の新しい記事は 2010 まで）。
記事を落として言語に分けるのは、前の試み（`E:\\auto-videos-creation\\gyeong-parallel\\`）の道具を使う。
一度だけ回して、できた src/VfHJ-en.jsonl をリポジトリに置く（prepare.py はそれを読む）。

    python -I -X utf8 _tools/heiwakyou_taiyaku/extract_en.py E:\\auto-videos-creation\\gyeong-parallel

1行1記事: {"id": 記事の番号, "key": "0101", "lines": [英語の行]}。頭の「Pyeong Hwa Gyeong - (001)」「Book 1. …」
「CHAPTER 1. …」の行は外す（講演の振り分けにだけ使う）。小見出しの行（「1. Where does …」）は残す。
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
GP = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(GP / 'scripts'))
from align import split_langs  # noqa: E402

BOOK = re.compile(r'^Book\s*(\d+)', re.I)
CHAP = re.compile(r'^CHAPTER\s*(\d+)', re.I)
HEAD = re.compile(r'^Pyeong\s*Hwa', re.I)


def main():
    rows = [json.loads(l) for l in (GP / 'data' / 'pyeonghwa.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    rows = sorted((r for r in rows if 1492 <= r['id'] <= 2010), key=lambda r: r['id'])
    out, cur, keys = [], None, set()
    for r in rows:
        langs = split_langs(r['paras'])
        assert langs, r['id']
        en = langs['en']
        b = next((BOOK.match(t) for t in en[:4] if BOOK.match(t)), None)
        c = next((CHAP.match(t) for t in en[:4] if CHAP.match(t)), None)
        if b and c:
            cur = f'{int(b.group(1)):02d}{int(c.group(1)):02d}'
        assert cur, r['id']
        lines = [t.strip() for t in en if t.strip() and not (HEAD.match(t) or BOOK.match(t) or CHAP.match(t))]
        out.append({'id': r['id'], 'key': cur, 'lines': lines})
        keys.add(cur)
    path = HERE / 'src' / 'VfHJ-en.jsonl'
    path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in out), encoding='utf-8', newline='\n')
    print(f'{len(out)} 記事・{len(keys)} 講演 → {path}')


if __name__ == '__main__':
    main()

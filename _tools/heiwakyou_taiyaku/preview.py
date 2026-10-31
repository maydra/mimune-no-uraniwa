# -*- coding: utf-8 -*-
"""対応表を、韓国語と日本語を組ごとに並べた文字の一覧にして見る。

    python _tools/heiwakyou_taiyaku/preview.py 0101          # work/preview/0101.txt に書く
    python _tools/heiwakyou_taiyaku/preview.py 0101 5 9      # 組5〜9 だけ
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main():
    no = sys.argv[1]
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    b = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 6
    sec = json.loads((HERE / 'work' / 'sections' / f'{no}.json').read_text(encoding='utf-8'))
    al = json.loads((HERE / 'work' / 'align' / f'{no}.json').read_text(encoding='utf-8'))
    ko = {x['n']: x['t'] for x in sec['ko']}
    ja = {x['s']: x['t'] for x in sec['ja']}
    out = [f'# {no} {sec["title"]["ko"]} / {sec["title"]["ja"]}']
    for gi, g in enumerate(al['groups'], 1):
        if not a <= gi <= b:
            continue
        out.append(f'\n=== 組{gi}  K{g["ko"]}' + (f'  ※{g["note"]}' if g.get('note') else ''))
        for d in g.get('diff', []):
            out.append(f'  【注】{d}')
        if g.get('ja_only'):
            out.append(f'  【日本語だけ】J{g["ja_only"]} → {g.get("ja_only_ko", "")}')
        for n in g['ko']:
            out.append(f'  K{n}: {ko[n]}')
        for x in g['ja']:
            out.append(f'  J{x}: {ja[x]}' if isinstance(x, int) else f'  【日本語に無い】{x["ko"]}')
    path = HERE / 'work' / 'preview' / f'{no}.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()

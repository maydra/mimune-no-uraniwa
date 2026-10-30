# -*- coding: utf-8 -*-
"""日本語に無い韓国語（対応表の {"ko": "…"}）を、AI 訳のために抜き出す・訳がそろったか確かめる。

    python _tools/heiwa_sekaijin/frags.py list              # work/trans/todo/NN.txt に訳す材料を書く
    python _tools/heiwa_sekaijin/frags.py check             # work/trans/ja/*.json の訳が全部そろったか
    python _tools/heiwa_sekaijin/frags.py list --lang en    # 英語版で省かれた所（work/trans/todo-en/、訳は work/trans/en/）

訳は、韓国語の文字列の印（節の番号＋韓国語を空白抜きで縮めた sha1 の頭10字）で持つ。
対応表を直して組の番号がずれても、同じ韓国語には同じ訳が付く（祝福家庭と理想天国の fill-ja と同じ考え）。

    work/trans/ja/<名前>.json  … {"07:3fa2c9d1e0": "日本語の訳", …}（何ファイルに分けてもよい）
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SEC = HERE / 'work' / 'sections'
TRANS = HERE / 'work' / 'trans'


def flat(s):
    return re.sub(r'\s', '', s)


def key(no, ko):
    return f'{no:02d}:' + hashlib.sha1(flat(ko).encode('utf-8')).hexdigest()[:10]


SIDE = {'ja': '日本語（公式の訳）', 'en': '英語（英語版の訳）'}


def align_dir(lang):
    return HERE / 'work' / ('align' if lang == 'ja' else f'align-{lang}')


def items(lang='ja'):
    """[(no, 組の番号, key, 韓国語, その組の韓国語の全文, 前の日本語, 後ろの日本語, note)]"""
    out = []
    for path in sorted(align_dir(lang).glob('*.json')):
        no = int(path.stem)
        sec = json.loads((SEC / path.name).read_text(encoding='utf-8'))
        ja = {x['s']: x['t'] for x in sec[lang]}
        ko = {x['n']: x['t'] for x in sec['ko']}
        groups = json.loads(path.read_text(encoding='utf-8'))['groups']
        # 前後の日本語を引くため、全部の組の ja を一続きに並べる
        seq = [(gi, x) for gi, g in enumerate(groups, 1) for x in g[lang]]
        for i, (gi, x) in enumerate(seq):
            if not isinstance(x, dict):
                continue
            prev = next((ja[y] for _, y in reversed(seq[:i]) if isinstance(y, int)), '')
            nxt = next((ja[y] for _, y in seq[i + 1:] if isinstance(y, int)), '')
            g = groups[gi - 1]
            out.append((no, gi, key(no, x['ko']), x['ko'], '\n'.join(ko[n] for n in g['ko']), prev, nxt, g.get('note', '')))
    return out


def done(lang='ja'):
    have = {}
    for f in sorted((TRANS / lang).glob('*.json')):
        have.update(json.loads(f.read_text(encoding='utf-8')))
    return have


def cmd_list(lang):
    have = done(lang)
    todo = TRANS / ('todo' if lang == 'ja' else f'todo-{lang}')
    todo.mkdir(parents=True, exist_ok=True)
    for f in todo.glob('*.txt'):
        f.unlink()
    by = {}
    for it in items(lang):
        if it[2] not in have:
            by.setdefault(it[0], []).append(it)
    total = 0
    for no, its in by.items():
        sec = json.loads((SEC / f'{no:02d}.json').read_text(encoding='utf-8'))
        lines = [f'# {no:02d}  {sec["title"]["ko"]} / {sec["title"]["ja"]}', '']
        for no_, gi, k, ko, whole, prev, nxt, note in its:
            lines += [f'## {k}  （組{gi}）',
                      f'訳す韓国語: {ko}',
                      f'その組の韓国語の全文: {whole}',
                      f'直前の{SIDE[lang]}: {prev}',
                      f'直後の{SIDE[lang]}: {nxt}']
            if note:
                lines.append(f'対応付けのメモ: {note}')
            lines.append('')
            total += len(flat(ko))
        (todo / f'{no:02d}.txt').write_text('\n'.join(lines), encoding='utf-8')
    print(f'訳が要る所 {sum(len(v) for v in by.values())} か所・{total} 字（{len(by)} 節）→ {todo}')


def cmd_check(lang):
    have = done(lang)
    keys = {it[2] for it in items(lang)}
    miss = sorted(keys - set(have))
    extra = sorted(set(have) - keys)
    empty = sorted(k for k in keys & set(have) if not have[k].strip())
    hangul = sorted(k for k in keys & set(have) if re.search(r'[가-힣]', have[k]))
    print(f'訳 {len(keys) - len(miss)}/{len(keys)}')
    for name, ks in (('訳が無い', miss), ('空の訳', empty), ('ハングルが残っている', hangul), ('対応表に無い印（直した後の古い訳）', extra)):
        if ks:
            print(f'{name}: {len(ks)} 件  ' + ', '.join(ks[:12]))
    sys.exit(1 if miss or empty or hangul else 0)


if __name__ == '__main__':
    lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'ja'
    {'list': cmd_list, 'check': cmd_check}[sys.argv[1] if len(sys.argv) > 1 else 'list'](lang)

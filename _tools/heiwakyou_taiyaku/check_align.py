# -*- coding: utf-8 -*-
"""『平和経』の韓日・韓英の対応表を確かめる（_tools/heiwa_sekaijin/check_align.py を写して、節の名前を HHNN にしたもの）。

    python -I -X utf8 _tools/heiwakyou_taiyaku/check_align.py 0101            # 韓日（work/align/0101.json）
    python -I -X utf8 _tools/heiwakyou_taiyaku/check_align.py all             # 韓日の全部（まとめを出す）
    python -I -X utf8 _tools/heiwakyou_taiyaku/check_align.py 0101 --lang en  # 韓英（work/align-en/0101.json）
    python -I -X utf8 _tools/heiwakyou_taiyaku/check_align.py 0414 --part 1   # 分けて組んだ一部（work/align-parts/0414-1.json の k_range・j_range の中）

対応表の形（くわしくは TASK-align.md・TASK-align-en.md）。L は ja か en:
    {"key": "0101", "groups": [
        {"ko": [1], "L": [1, 2, 3]},
        {"ko": [2, 3], "L": [4, {"ko": "訳に無い韓国語の文"}, 5], "note": "…"},
        …]}
読む人向けの書き足し: "diff"、"L_only"・"L_only_ko"（TASK-align.md）

誤り（直すまで OK にならない）:
    韓国語のかたまり・訳の文の、抜け・重なり。韓国語の番号が飛ぶ・逆に並ぶ
    [見出し]・[頭] の韓国語が、ほかの韓国語と同じ組に入っている（画面の行の形が崩れる）
    {"ko": "…"} の韓国語が、その組の韓国語の中に見つからない
    diff に作業の番号が入っている、L_only がその組の文でない、L_only_ko が韓国語でない
知らせ（誤りではない）:
    順番の入れ替え、訳に無い韓国語、大きすぎる組、韓国語の無い組
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SEC = HERE / 'work' / 'sections'
NAME = {'ja': '日本語', 'en': '英語'}
MARK = {'ja': 'J', 'en': 'E'}


def align_dir(lang):
    return HERE / 'work' / ('align' if lang == 'ja' else f'align-{lang}')


def flat(s):
    return re.sub(r'[\s"“”\'‘’]', '', s)


def check(no, lang='ja', part=None):
    """no は節の名前（"0101"）"""
    L, N, M = lang, NAME[lang], MARK[lang]
    sec = json.loads((SEC / f'{no}.json').read_text(encoding='utf-8'))
    path = align_dir(L) / f'{no}.json'
    if part:   # 長い講演を分けて組むとき: work/align-parts/HHNN-P.json。k_range・j_range の中だけを調べる
        path = HERE / 'work' / 'align-parts' / f'{no}-{part}.json'
    if not path.exists():
        return [f'{path.name} が無い'], [], {}
    try:
        al = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [f'JSON が読めない: {e}'], [], {}
    errs, info = [], []
    if al.get('key') != no:
        errs.append(f'"key" が {al.get("key")}（"{no}" のはず）')
    ko_text = {x['n']: x['t'] for x in sec['ko']}
    ko_kind = {x['n']: x['kind'] for x in sec['ko']}
    t_kind = {x['s']: x['kind'] for x in sec.get(L, [])}
    nko, nt = len(sec['ko']), len(sec.get(L, []))
    seen_ko, seen_t = [], []
    kr = al.get('k_range') if part else None
    jr = al.get('j_range') if part else None
    last_ko = kr[0] - 1 if kr else 0
    max_t = 0
    frag_chars = 0
    omitted = []
    for gi, g in enumerate(al.get('groups', []), 1):
        ko = g.get('ko', [])
        tr = g.get(L, [])
        if not isinstance(ko, list) or not isinstance(tr, list):
            errs.append(f'組{gi}: ko / {L} は配列で')
            continue
        if ko:
            if ko != list(range(ko[0], ko[0] + len(ko))):
                errs.append(f'組{gi}: ko {ko} が連続していない')
            if ko[0] != last_ko + 1:
                errs.append(f'組{gi}: ko {ko} の前の K{last_ko + 1}〜K{ko[0] - 1} が無いか、順が逆')
            last_ko = max(last_ko, ko[-1])
            seen_ko += ko
        elif not sec.get('ko_missing'):
            info.append(f'組{gi}: 韓国語の無い組（{N}だけ）: {M}{[x for x in tr if isinstance(x, int)]}')
        special = [n for n in ko if ko_kind.get(n) in ('head', 'meta')]
        if special and len(ko) > 1:
            errs.append(f'組{gi}: [見出し]・[頭] の K{special} は1つで1組に（ko {ko}）')
        group_ko = flat(''.join(ko_text.get(n, '') for n in ko))
        ints = []
        for x in tr:
            if isinstance(x, int):
                ints.append(x)
                if x < max_t:
                    info.append(f'組{gi}: {M}{x} が前の {M}{max_t} より前（順番の入れ替え）')
                max_t = max(max_t, x)
                seen_t.append(x)
            elif isinstance(x, dict) and isinstance(x.get('ko'), str):
                f = flat(x['ko'])
                if not f:
                    errs.append(f'組{gi}: 空の {{"ko"}}')
                elif f not in group_ko:
                    errs.append(f'組{gi}: {{"ko": "{x["ko"][:30]}…"}} が K{ko} の中に無い（字を写し間違えていないか）')
                frag_chars += len(f)
            else:
                errs.append(f'組{gi}: {L} の中身は {N}の文の番号 か {{"ko": "…"}} だけ: {x!r}'[:120])
        if ko and ints and all(ko_kind.get(n) == 'p' for n in ko) and any(t_kind.get(x) == 'head' for x in ints):
            info.append(f'組{gi}: {N}の見出しが本文の韓国語 K{ko} と組になっている')
        if ko and not ints:
            omitted.append(f'K{ko[0]}' + (f'〜K{ko[-1]}' if len(ko) > 1 else ''))
        # 読む人向けの書き足し。あれば形を確かめる
        for d in g.get('diff', []):
            if not isinstance(d, str) or not d.strip():
                errs.append(f'組{gi}: diff は空でない文字列の配列で')
            elif re.search(r'(?<![A-Za-z])[JKE]\d+', d) or re.search(r'組\d', d):
                errs.append(f'組{gi}: diff に番号（J12・E3・K3・組）が入っている。読む人には通じない: {d[:40]}')
        only = g.get(f'{L}_only', [])
        if only:
            if not all(isinstance(x, int) and x in ints for x in only):
                errs.append(f'組{gi}: {L}_only {only} は、この組の {L} にある{N}の文の番号だけ')
            if not re.search(r'[가-힣]', g.get(f'{L}_only_ko', '')):
                errs.append(f'組{gi}: {L}_only があるのに {L}_only_ko（韓国語訳）が無い')
        elif g.get(f'{L}_only_ko'):
            errs.append(f'組{gi}: {L}_only_ko があるのに {L}_only が無い')
        if len(ko) > 3 or len(ints) > 14:
            info.append(f'組{gi}: 大きい組（K{len(ko)}個・{M}{len(ints)}文）。細かく分けられないか')
    k_all = range(kr[0], kr[1] + 1) if kr else range(1, nko + 1)
    t_all = range(jr[0], jr[1] + 1) if jr else range(1, nt + 1)
    miss_ko = sorted(set(k_all) - set(seen_ko))
    dup_ko = sorted({n for n in seen_ko if seen_ko.count(n) > 1})
    miss_t = sorted(set(t_all) - set(seen_t))
    dup_t = sorted({n for n in seen_t if seen_t.count(n) > 1})
    bad_t = sorted(n for n in set(seen_t) if n not in t_all)
    if miss_ko:
        errs.append(f'韓国語の抜け: K{miss_ko}')
    if dup_ko:
        errs.append(f'韓国語の重なり: K{dup_ko}')
    if miss_t:
        errs.append(f'{N}の抜け: {M}{miss_t}')
    if dup_t:
        errs.append(f'{N}の重なり: {M}{dup_t}')
    if bad_t:
        errs.append(f'無い{N}の番号: {M}{bad_t}')
    if omitted:
        info.append(f'{N}がまったく無い韓国語: ' + ', '.join(omitted))
    stats = {'groups': len(al.get('groups', [])), 'ko': nko, 'tr': nt, 'frag_chars': frag_chars,
             'ko_chars': sum(len(flat(x['t'])) for x in sec['ko']), 'omitted': len(omitted),
             'reorder': sum('入れ替え' in i for i in info)}
    return errs, info, stats


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'ja'
    args = [a for a in args if a != lang or '--lang' not in sys.argv]
    arg = args[0] if args else 'all'
    part = sys.argv[sys.argv.index('--part') + 1] if '--part' in sys.argv else None
    args = [a for a in args if a != part]
    arg = args[0] if args else 'all'
    N = NAME[lang]
    nos = sorted(p.stem for p in SEC.glob('*.json')) if arg == 'all' else [arg]
    bad = 0
    rows = []
    for no in nos:
        errs, info, st = check(no, lang, part)
        if arg != 'all':
            for e in errs:
                print('誤り:', e)
            for i in info:
                print('知らせ:', i)
            if st:
                print(f'組 {st["groups"]}、韓国語 {st["ko"]}、{N} {st["tr"]} 文、'
                      f'{N}に無い韓国語 {st["frag_chars"]} 字（全 {st["ko_chars"]} 字）')
        if errs:
            bad += 1
        rows.append((no, 'NG' if errs else 'OK', st))
    if arg == 'all':
        for no, ok, st in rows:
            if st:
                print(f'{no} {ok} 組{st["groups"]:4d} {N}に無い韓国語 {st["frag_chars"]:5d}字/{st["ko_chars"]:5d}字 '
                      f'まったく無い {st["omitted"]:2d} 入れ替え {st["reorder"]:2d}')
            else:
                print(f'{no} {ok} （対応表が無い）')
    print('OK' if not bad else f'NG {bad} 節')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()

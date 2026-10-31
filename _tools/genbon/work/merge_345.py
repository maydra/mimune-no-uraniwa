# 3巻の残り・4巻・5巻の訳（outN.jsonl）を units.json の後ろに足す
#   python -I -X utf8 _tools/genbon/work/merge_345.py <作業フォルダ>
# 作業フォルダ（E:\mimune-no-uraniwa\genbon-work\）には extend_345.py が書いた units345.json と、訳した out1〜5.jsonl。
# 訳の決まりは作業フォルダの TASK.md（1〜447ページのときの work/TASK.md と同じ決まり）。何度回してもよい（806番から先を置き換える）
import json, re, sys
from pathlib import Path

WORK = Path(sys.argv[1])
UNITS = Path(__file__).resolve().parents[1] / 'units.json'
FIRST_NEW = 806

units = [u for u in json.loads(UNITS.read_text(encoding='utf-8')) if u['id'] < FIRST_NEW]
new = json.loads((WORK / 'units345.json').read_text(encoding='utf-8'))
tr = {}
for f in sorted(WORK.glob('out*.jsonl')):
    for line in f.read_text(encoding='utf-8').splitlines():
        if line.strip():
            e = json.loads(line)
            tr[e['id']] = e
missing = [u['id'] for u in new if u['id'] not in tr]
assert not missing, f'訳の無い段落: {missing}'

# compose.py と同じ語のそろえ。対像は 1〜447ページの訳と同じく対象に（40段落すべてそうした）
# 「相対像」は原文の字のまま（相対象という語は無い。なじみの薄い語は原文のまま、の決まり）
NORM = [('百姓', '民'), ('祖上', '先祖'), ('相対像', '相対'), ('対像', '対象'), ('相対', '相対像')]
JA_FIX = {815: [('相対象', '相対像')]}           # 訳した人が対像→対象の指示で直してしまった所
TAIZOU_NOTE = '原文「対像」は対象の意として訳した（原稿はほぼいつもこう書く。以下の段落も同じ）'
MARK = re.compile(r'〔[^〕]+〕')
page = lambda k: int(k) if re.fullmatch(r'\d+', str(k)) else k   # 448 は数、497-2・X-010 は文字のまま
# 日付の行（「51. 12/28」）で終わるページの次のページの頭が節の題だったのに、extend_345.py が文の途中とみてつないだ段落。
# 最後のページ（題の行）を切り離して見出しにする（段落の id → 切り離した後の断り書きの直し）
SPLIT_LAST = {837, 865, 866, 881}
NOTE_FIX = {
    837: [('。〔531〕の後の「原力으로 본 三位格 一体」は次の節の題とみられるが、原文でこの段落の中にあるので段落の中のまま訳した', '')],
    865: [('、〔575〕の後の「原理復帰世界とは基本自我完成世界」は次の節の題（写しのとおりこの段落に残した）', '')],
    866: [('、〔587〕の後の「創造世界が進化的論理に適用される根本意義」は次の節の題（写しのとおりこの段落に残した）', '')],
    881: [('段落の終わりの「하나님 아바지만으로 모시는 灵人은 未完全生」は645ページから始まる次の節の題（561ページの目次では「하나님을 아버지만으로 모시는 灵人은 未完全 生」）で、この段落の中にそのまま訳した。「아바지」は아버지（父）として訳した', '')],
}
# 見出しの付け直し。898「なぜ堕落させたのか？」は X-010 の3行目で、ここで節を切ると 898〜900 の3行だけの節になるので小見出しに
OVERRIDE = {898: {'heading': False, 'sub': True},
            # 5巻の頭の 561ページは5巻の目次（◎の行が、あとの節の題と同じ順に並ぶ）。前の節の続きにせず、節の名前を付ける
            857: {'sec_title': {'ja': '5巻の目次', 'ko': '5권 목차'}}}

out = []
for u in new:
    e = tr[u['id']]
    ja = e['ja']
    for a, b in NORM:
        ja = ja.replace(a, b)
    for a, b in JA_FIX.get(u['id'], []):
        assert a in ja, (u['id'], a)
        ja = ja.replace(a, b)
    ko_marks = [f'〔{p}〕' for p, _ in u['parts'][1:]]
    assert MARK.findall(ja) == ko_marks, (u['id'], MARK.findall(ja), ko_marks)
    rec = {'vol': u['vol'], 'parts': [[page(p), t] for p, t in u['parts']], 'ja': ja}
    for f in ('heading', 'sub', 'note', 'board'):
        if e.get(f):
            rec[f] = e[f]
    for f, v in OVERRIDE.get(u['id'], {}).items():
        if v:
            rec[f] = v
        else:
            rec.pop(f, None)
    if rec.get('heading') and rec.get('sub'):
        rec.pop('sub')
    for a, b in NOTE_FIX.get(u['id'], []):
        assert a in rec['note'], (u['id'], a)
        rec['note'] = rec['note'].replace(a, b).strip()
    if 'note' in rec and not rec['note']:
        rec.pop('note')
    if u['id'] in SPLIT_LAST:
        cut = ja.rfind('〔')
        head_ja = ja[ja.index('〕', cut) + 1:].strip()
        assert 0 < len(head_ja) <= 40, (u['id'], head_ja)
        rec['ja'] = ja[:cut].rstrip()
        head = {'vol': u['vol'], 'parts': [rec['parts'].pop()], 'ja': head_ja, 'heading': True}
        out += [rec, head]
    else:
        out.append(rec)
# 対像の断り書きは、原文に対像が最初に出る段落にだけ付ける
for rec in out:
    if any('対像' in t or '對像' in t for _, t in rec['parts']):
        rec['note'] = TAIZOU_NOTE + ('。' + rec['note'] if rec.get('note') else '')
        break
for i, rec in enumerate(out):
    if rec.get('note'):
        assert '誤り' not in rec['note'] and '誤記' not in rec['note'], (i, rec['note'])
    units.append({'id': FIRST_NEW + i, **rec})

UNITS.write_text(json.dumps(units, ensure_ascii=False, indent=0), encoding='utf-8', newline='\n')
print('段落', len(units), '（足した', len(new), '）見出し', sum(1 for u in units[FIRST_NEW - 1:] if u.get('heading')),
      '小見出し', sum(1 for u in units[FIRST_NEW - 1:] if u.get('sub')), '断り', sum(1 for u in units[FIRST_NEW - 1:] if u.get('note')))

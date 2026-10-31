# 記事の行を種類に分ける（build_books.py から使う）
import re
DASH = r'[―ー一\-－‐—–~～\s]*'
RE_BOOK = re.compile(r'^世界経典\s*[ⅡII2]+$')
RE_PART = re.compile(r'^第\s*(\d+)\s*部\s*(.*)$')
RE_CHAP = re.compile(r'^第\s*(\d+)\s*章\s*(.*)$')
RE_SEC = re.compile(r'^(\d+)\s*[)）]\s*(.+)$')
RE_SUB = re.compile(r'^(\d+)\s*[.．]\s*(.+)$')
RE_LABEL = re.compile(r'^' + DASH + r'(宗教経典|み言選集|文鮮明先生(?:の)?(?:み言|御言)?)' + DASH + r'$')
# (58-291、1972.6.25) / （21-44 ～ 45、1968.9.1） など
RE_SJ_CITE = re.compile(r'^[（(]\s*\d+\s*[-－‐ー−]\s*\d+[^()（）]{0,40}[)）]$')
# 道徳経1(道教) / ローマの信徒への手紙1.19 ～ 20（キリスト教）
RE_SCR_CITE = re.compile(r'^[^。！？]{1,70}[（(][^（()）。]{1,24}[)）]$')

# 原理講論、総序 / 御旨の道、人格 / 興進様の霊界メッセージ、2002.1.1
RE_BOOK_CITE = re.compile(r'^[（(]?(原理講論|御旨の道|み旨の道|興進様の霊界メッセージ|天聖経|平和神経)[、・,，]')
HIRA = re.compile(r'[ぁ-ゖ]')

def kind(line):
    if RE_LABEL.match(line):
        return 'label'
    if RE_SJ_CITE.match(line) or RE_BOOK_CITE.match(line):
        return 'cite'
    if RE_SCR_CITE.match(line) and not line.endswith(('」)', '」）')):
        return 'cite'
    # 人名・書名だけの短い行（トーマス・ジェファーソン / 董仲舒　春秋繁露）。詩の行はひらがなが多いので外れる
    if len(line) <= 40 and len(HIRA.findall(line)) <= 2 and not line.endswith(('。', '！', '？', '」', '』', '、')):
        return 'cite'
    return 'p'

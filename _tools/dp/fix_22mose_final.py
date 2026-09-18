import re

path = 'c:/malsum/mimune-no-uraniwa/dp/22mose.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix zero-padding in chapter filenames
# Matches /01.html, /001.html, etc.
text = re.sub(r'\/0+([0-9]+\.html)', r'/\1', text)

# 2. Fix the specific unlinked bible references
reps = {
    '（出エ二五～三一）': '（<a href="../Bible_out/01_Old Testament/02_exodus/25.html#v1" class="verse-link">出エ二五～三一</a>）',
    '（出エ三五～四〇）': '（<a href="../Bible_out/01_Old Testament/02_exodus/35.html#v1" class="verse-link">出エ三五～四〇</a>）',
    '（出エ三二・19）': '（<a href="../Bible_out/01_Old Testament/02_exodus/32.html#v19" class="verse-link">出エ三二・19</a>）',
    '（民数一三・１、２）': '（<a href="../Bible_out/01_Old Testament/04_numbers/13.html#v1" class="verse-link">民数一三・１、２</a>）',
    '（民数二〇・１～13）': '（<a href="../Bible_out/01_Old Testament/04_numbers/20.html#v1" class="verse-link">民数二〇・１～13</a>）',
    '（民数三二・11、12）': '（<a href="../Bible_out/01_Old Testament/04_numbers/32.html#v11" class="verse-link">民数三二・11、12</a>）',
    '（ヨシュア）': '（<a href="../Bible_out/01_Old Testament/06_joshua/1.html" class="verse-link">ヨシュア</a>）',
    '（ヨシュア六）': '（<a href="../Bible_out/01_Old Testament/06_joshua/6.html#v1" class="verse-link">ヨシュア六</a>）'
}

for k, v in reps.items():
    text = text.replace(k, v)

# 3. Fix duplication at 1273
# The broken line is:
# "                style=\"background-color:#CCFFFF\">神はモーセに、彼はカナンの地に入ることができないと言われ、「神の霊のやどっているヌンの子ヨシュアを選び、あなたの手をその上におき、彼を祭司エレアザルと全会衆の前に立たせて、彼らの前で職に任じなさい。そして彼にあなたの権威を分け与え、イスラエルの人々の全会衆を彼に従わせなさい」（民数二七・"
# It is followed by line 1274 which starts with 20 spaces and then the same text but starting the anchor.
# Actually, the repetition is almost identical.
pattern_dup = re.compile(r'                style=\"background-color:#CCFFFF\">神はモーセに、彼はカナンの地に入ることができないと言われ、「神の霊のやどっているヌンの子ヨシュアを選び、あなたの手をその上におき、彼を祭司エレアザルと全会衆の前に立たせて、彼らの前で職に任じなさい。そして彼にあなたの権威を分け与え、イスラエルの人々の全会衆を彼に従わせなさい」（民数二七・\r?\n')
text = pattern_dup.sub('', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

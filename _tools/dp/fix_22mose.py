import re

path = 'c:/malsum/mimune-no-uraniwa/dp/22mose.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Global Zero padding removal for chapters
# Matches /01.html, /001.html etc.
# We want to catch things like ../01.html#v1 -> ../1.html#v1
text = re.sub(r'/(?:0+)([0-9]+)\.html', r'/\1.html', text)

# 2. Fix the specific duplication mistake at line 1273 approx
# We'll search for the specific broken line.
broken_part = 'イスラエルの人々の全会衆を彼に従わせなさい」（民数二七・\n'
# Note: Line endings might be \r\n on Windows.
text = text.replace('イスラエルの人々の全会衆を彼に従わせなさい」（民数二七・\n', '')
text = text.replace('イスラエルの人々の全会衆を彼に従わせなさい」（民数二七・\r\n', '')

# 3. Specific Bible reference links (unlinked -> linked)
reps = {
    '（出エ二五～三一）': '（<a href="../Bible_out/01_Old Testament/02_exodus/25.html#v1" class="verse-link">出エ二五～三一</a>）',
    '（出エ三五～四〇）': '（<a href="../Bible_out/01_Old Testament/02_exodus/35.html#v1" class="verse-link">出エ三五～四〇</a>）',
    '壊してしまった（出エ三二・19）。ため': '壊してしまった（<a href="../Bible_out/01_Old Testament/02_exodus/32.html#v19" class="verse-link">出エ三二・19</a>）。ため',
    '命じられた（民数一三・１、２）。': '命じられた（<a href="../Bible_out/01_Old Testament/04_numbers/13.html#v1" class="verse-link">民数一三・１、２</a>）。',
    '打つことによって（民数二〇・１～13）、': '打つことによって（<a href="../Bible_out/01_Old Testament/04_numbers/20.html#v1" class="verse-link">民数二〇・１～13</a>）、',
    '入ったという事実である（民数三二・11、12）。そして': '入ったという事実である（<a href="../Bible_out/01_Old Testament/04_numbers/32.html#v11" class="verse-link">民数三二・11、12</a>）。そして',
    '事実である（ヨシュア）。': '事実である（<a href="../Bible_out/01_Old Testament/06_joshua/1.html" class="verse-link">ヨシュア</a>）。',
    '崩れてしまった（ヨシュア六）。しかるのち': '崩れてしまった（<a href="../Bible_out/01_Old Testament/06_joshua/6.html#v1" class="verse-link">ヨシュア六</a>）。しかるのち'
}

for k, v in reps.items():
    if k in text:
        text = text.replace(k, v)
    else:
        # Try without the context if it failed (but context is safer)
        # For simplicity, I'll just check if it was missing.
        print(f"Warning: Could not find target '{k}'")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Finished fixing 22mose.html")

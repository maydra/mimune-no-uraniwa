import re

with open('c:/malsum/mimune-no-uraniwa/dp/22mose.html', 'r', encoding='utf-8') as f:
    text = f.read()

books = ['出エ', '創', 'レビ', '民数', '申命', 'ヨシュア', 'マタイ', 'マルコ', 'ルカ', 'ヨハネ', '使徒', '黙', 'コリント', 'ユダ', 'アモス', 'ヘブル', '詩']
pattern = '|'.join(books)
# Search for Book KanjiNum ・ Digits
regex = re.compile(rf'({pattern})[〇-九一二三四五六七八九十]+・[0-9]+')

unlinked = []
lines = text.split('\n')

for i, line in enumerate(lines):
    for m in regex.finditer(line):
        # A simple proximity check for <a> on the same line
        # Check if the match is preceded by '<a ' and followed by '</a>'
        # or if there is any <a> on the line that looks like it belongs to it.
        start = m.start()
        post_text = line[m.end():]
        pre_text = line[:m.start()]
        
        # In this file, bible links are typically:
        # <a href="..." class="verse-link">Ref</a>
        # If the ref text itself is not inside tags, it's unlinked.
        
        # Let's find all <a> tags on this line and see if they contain the match position
        tags = list(re.finditer(r'<a [^>]+>.*?</a>', line))
        is_linked = False
        for tag in tags:
            if tag.start() <= m.start() and tag.end() >= m.end():
                is_linked = True
                break
        
        if not is_linked:
            unlinked.append((i + 1, m.group(0), line.strip()))

with open('c:/malsum/mimune-no-uraniwa/dp/unlinked_report.txt', 'w', encoding='utf-8') as cout:
    for line_num, ref, full_line in unlinked:
        cout.write(f'Line {line_num}: {ref} -- {full_line}\n')

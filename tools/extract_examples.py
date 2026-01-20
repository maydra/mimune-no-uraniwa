import re

with open("test_output.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find specific examples
ex1 = re.search(r'（ロマ一・[^）]+）', content)
ex2 = re.search(r'（[前後]編[^）]+参照）', content)
ex3 = re.search(r'（ロマ三・[^）]+）', content) # if exists
ex4 = re.search(r'（ロマ八・[^）]+）', content) # for range testing

with open("examples.txt", "w", encoding="utf-8") as f:
    if ex1: f.write(f"Example Bible: {ex1.group(0)}\n")
    if ex2: f.write(f"Example DP: {ex2.group(0)}\n")
    if ex3: f.write(f"Example Bible 2: {ex3.group(0)}\n")
    if ex4: f.write(f"Example Bible Range: {ex4.group(0)}\n")

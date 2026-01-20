import re

with open("dp/10sojo.html", "r", encoding="utf-8") as f:
    content = f.read()

refs = re.findall(r'（[^）]*href=[^）]*）', content)
with open("results.txt", "w", encoding="utf-8") as f:
    for r in refs:
        f.write(r + "\n")

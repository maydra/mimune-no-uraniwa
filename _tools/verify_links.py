import re

with open("test_output.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find Bible refs
bible_refs = re.findall(r'（[^）]*href="[^"]*Bible_out[^"]*"[^）]*）', content)
print("Bible Refs Sample:")
for r in bible_refs[:5]:
    print(r)

# Find DP refs
dp_refs = re.findall(r'（[^）]*href="[^"]*dp/[^"]*"[^）]*）', content)
print("\nDP Refs Sample:")
for r in dp_refs[:5]:
    print(r)

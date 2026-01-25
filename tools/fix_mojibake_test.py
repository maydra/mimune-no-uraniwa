
import os

# The garbled text sample from Line 118
# сЂЋсЂдсЂѓсЂфсЂЪ...
# Let's try to reverse it.

def try_fix(text):
    try:
        # Hypothesis: It was UTF-8 bytes interpreted as CP1251 (Cyrillic) and saved as UTF-8
        # So we take the string, encode it to CP1251 to get the 'original' bytes
        b = text.encode('cp1251')
        # Then decode those bytes as UTF-8 (most likely for modern web)
        return b.decode('utf-8')
    except Exception as e:
        return f"Error UTF-8: {e}"

def try_fix_sjis(text):
    try:
        b = text.encode('cp1251')
        return b.decode('shift_jis')
    except Exception as e:
        return f"Error SJIS: {e}"

target_file = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\Bible_out\02_New Testament\10_ephesians\002.html"

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's extract a snippet from the paragraph id="v1"
import re
match = re.search(r'<p id="v1"><sup>.*?</sup>(.*?)</p>', content)
if match:
    garbled = match.group(1)
    print(f"Garbled snippet: {garbled[:20]}")
    
    fixed_utf8 = try_fix(garbled)
    print(f"Fixed (UTF-8 attempt): {fixed_utf8[:50]}")
    
    fixed_sjis = try_fix_sjis(garbled)
    print(f"Fixed (SJIS attempt): {fixed_sjis[:50]}")
else:
    print("Could not find v1 paragraph")


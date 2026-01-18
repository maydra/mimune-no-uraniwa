
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def scan_files():
    if not os.path.exists(TARGET_DIR):
        print(f"Directory not found: {TARGET_DIR}")
        return

    giant_header_files = []

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
            
        filepath = os.path.join(TARGET_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='cp932') as f:
                    content = f.read()
            except:
                continue

        # Look for h2 tags
        # We want to match h2 tags that are suspiciously long
        # Regex to capture h2 content
        
        # This regex matches <h2>...</h2> but is non-greedy. 
        # If the file has a giant h2, it might span the whole file.
        # re.DOTALL is needed.
        
        matches = re.finditer(r'<(h[1-6])([^>]*)>(.*?)</\1>', content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            tag = match.group(1)
            inner = match.group(3)
            
            # Criteria: 
            # 1. Inner text length > 300
            # 2. Contains multiple <br> tags?
            
            if len(inner) > 1000: # 1000 is a safe bet for "way too long for a title"
                print(f"Found giant <{tag}> in {filename}: {len(inner)} chars")
                giant_header_files.append(filename)
                break # Only report once per file
            elif inner.count('<br') > 5:
                print(f"Found multiple <br> in <{tag}> in {filename}")
                giant_header_files.append(filename)
                break

if __name__ == "__main__":
    scan_files()

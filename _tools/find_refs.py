import os
import re

def find_refs(directory):
    # Match strings inside parentheses, filtering out those with HTML tags for now or including them if they are small
    pattern = re.compile(r'（([^）]{2,20})）')
    found = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for m in matches:
                            if '・' in m or '参照' in m:
                                found.add(m)
                except:
                    continue
    return sorted(list(found))

if __name__ == "__main__":
    dp_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp"
    refs = find_refs(dp_dir)
    # Output to a file to avoid console encoding issues
    with open('refs_list.txt', 'w', encoding='utf-8') as f:
        for r in refs:
            f.write(r + '\n')
    print(f"Found {len(refs)} unique references. Check refs_list.txt")

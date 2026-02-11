import os
import re

def fix_mangled_links():
    base_path = r'C:\malsum\mimune-no-uraniwa'
    # Focused on bokkaisyanomiti as we saw damage there
    mangled_dir = os.path.join(base_path, 'bokkaisyanomiti')
    index_path = os.path.join(mangled_dir, 'index.html')
    
    if not os.path.exists(index_path):
        return
        
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Pattern: href=C... -> href="03...
    # C is octal 103 (\1 + 03)
    # B is octal 102 (\1 + 02)
    # A is octal 101 (\1 + 01)
    # D is octal 104 (\1 + 04)
    # E is octal 105 (\1 + 05)
    
    replacements = {
        'href=A': 'href="01',
        'href=B': 'href="02',
        'href=C': 'href="03',
        'href=D': 'href="04',
        'href=E': 'href="05',
    }
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed mangled links in {index_path}")
    else:
        print(f"No mangled links found in {index_path}")

if __name__ == "__main__":
    fix_mangled_links()

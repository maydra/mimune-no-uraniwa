#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os
import sys

# Force UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_bible_links(filepath):
    """
    Fix Bible references to include book name and chapter inside the link tag.
    
    Current formats to fix:
    1. マタイ一六・<a href="..." class="verse-link">27</a>
    2. 出エジプト記三章<a href="..." class="verse-link">６</a>節
    
    Desired format: <a href="..." class="verse-link">マタイ一六・27</a>
    """
    print(f"\nProcessing: {filepath}")
    
    # Read the file with UTF-8 encoding
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Pattern 1: (BookName)(Chapter)・<a href="..." class="verse-link">(Verse)</a>
    pattern1 = r'([ぁ-んァ-ヶー一-龯]+)([一二三四五六七八九十百千]+)・<a\s+href="([^"]+)"\s+class="verse-link">([^<]+)</a>'
    
    def replacement1(match):
        book = match.group(1)
        chapter = match.group(2)
        url = match.group(3)
        verse = match.group(4)
        return f'<a href="{url}" class="verse-link">{book}{chapter}・{verse}</a>'
    
    content, count1 = re.subn(pattern1, replacement1, content)
    changes_made += count1
    
    # Pattern 2: (BookName)(Chapter)章<a href="..." class="verse-link">(Verse)</a>節
    pattern2 = r'([ぁ-んァ-ヶー一-龯]+)([一二三四五六七八九十百千]+)章<a\s+href="([^"]+)"\s+class="verse-link">([^<]+)</a>節'
    
    def replacement2(match):
        book = match.group(1)
        chapter = match.group(2)
        url = match.group(3)
        verse = match.group(4)
        return f'<a href="{url}" class="verse-link">{book}{chapter}章{verse}節</a>'
    
    content, count2 = re.subn(pattern2, replacement2, content)
    changes_made += count2
    
    if changes_made > 0:
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Updated {changes_made} Bible references (Pattern1: {count1}, Pattern2: {count2})")
        return True
    else:
        print("[SKIP] No changes needed")
        return False

if __name__ == "__main__":
    base_dir = r"c:\malsum\mimune-no-uraniwa\dp"
    files = ['26sairi.html', '23kaku.html', '24douji.html', '25saiko.html']
    
    total_updated = 0
    for filename in files:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if fix_bible_links(filepath):
                total_updated += 1
        else:
            print(f"[ERROR] File not found: {filepath}")
    
    print(f"\n{'='*60}")
    print(f"Summary: Updated {total_updated} out of {len(files)} files")
    print(f"{'='*60}")

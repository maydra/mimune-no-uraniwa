#!/usr/bin/env python3
"""
DPページの全HTMLファイルに color_filter.js のスクリプトタグを追加
"""

import os
import re
from pathlib import Path

# DPディレクトリのパス
DP_DIR = Path(r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp")

# 対象HTMLファイル
HTML_FILES = [
    "10sojo.html",
    "11sozo.html", 
    "12daraku.html",
    "13shuma.html",
    "14meshia.html",
    "15fukka.html",
    "16yotei.html",
    "17kirisu.html",
    "20sho.html",
    "21kidai.html",
    "22mose.html",
    "23kaku.html",
    "24douji.html",
    "25saiko.html",
    "26sairi.html"
]

# 追加するスクリプトタグ
SCRIPT_TAG = '<script src="color_filter.js"></script>'

def add_script_tag_to_file(filepath):
    """HTMLファイルにスクリプトタグを追加"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既にスクリプトタグがあるかチェック
    if 'color_filter.js' in content:
        print(f"  [OK] Already has script tag: {filepath.name}")
        return False
    
    # </body>タグの直前に挿入
    if '</body>' in content:
        content = content.replace('</body>', f'{SCRIPT_TAG}\n</body>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  [OK] Added script tag: {filepath.name}")
        return True
    else:
        print(f"  [ERROR] No </body> tag found: {filepath.name}")
        return False

def main():
    print("Adding color_filter.js script tag to DP HTML files...\n")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for filename in HTML_FILES:
        filepath = DP_DIR / filename
        
        if not filepath.exists():
            print(f"  [ERROR] File not found: {filename}")
            error_count += 1
            continue
        
        try:
            if add_script_tag_to_file(filepath):
                updated_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  [ERROR] Error processing {filename}: {e}")
            error_count += 1
    
    print(f"\n" + "="*50)
    print(f"Summary:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(HTML_FILES)}")
    print("="*50)

if __name__ == "__main__":
    main()

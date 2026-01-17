#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聖書の各章のHTMLファイルの節番号をリンク化するスクリプト
各節の小さな数字をクリック可能なリンクにして、共有できるようにします。
"""

import os
import re
from pathlib import Path

def process_html_file(file_path):
    """HTMLファイルを処理して節番号をリンク化する"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 既にリンク化されている場合はスキップ
        if 'verse-link' in content:
            return False
        
        # <p><sup>数字</sup>のパターンを検索して置換
        # 各行を処理
        lines = content.split('\n')
        modified_lines = []
        
        for line in lines:
            # <p><sup>数字</sup>のパターンがあるかチェック
            if re.search(r'<p[^>]*><sup>\d+</sup>', line):
                new_line = line
                
                # <p>タグにidがない場合に、<sup>数字</sup>の数字を使ってidを追加
                # パターン: <p><sup>数字</sup> または <p id="..."><sup>数字</sup>
                
                # まず、<p><sup>数字</sup>のパターンをすべて見つける
                verse_pattern = r'<p([^>]*)><sup>(\d+)</sup>'
                
                def add_id_and_link(match):
                    p_attrs = match.group(1)
                    verse_num = match.group(2)
                    
                    # 既にidがあるかチェック
                    if 'id=' in p_attrs:
                        # idがある場合、supのみをリンク化
                        return f'<p{p_attrs}><sup><a href="#v{verse_num}" class="verse-link">{verse_num}</a></sup>'
                    else:
                        # idがない場合、idを追加してsupもリンク化
                        return f'<p{p_attrs} id="v{verse_num}"><sup><a href="#v{verse_num}" class="verse-link">{verse_num}</a></sup>'
                
                new_line = re.sub(verse_pattern, add_id_and_link, new_line)
                modified_lines.append(new_line)
            else:
                modified_lines.append(line)
        
        new_content = '\n'.join(modified_lines)
        
        # CSSスタイルにverse-link用のスタイルを追加（まだない場合）
        if '</style>' in new_content and 'verse-link' not in new_content[:new_content.find('</style>')]:
            verse_link_css = '''

a.verse-link {
  color: #e74c3c;
  text-decoration: none;
  font-weight: bold;
}

a.verse-link:hover {
  text-decoration: underline;
  color: #c0392b;
}

[id^="v"]:target {
  background-color: #fff3cd;
  padding: 0.1em 0.2em;
  border-radius: 3px;
  scroll-margin-top: 1em;
}
'''
            new_content = new_content.replace('</style>', verse_link_css + '</style>')
        
        # 変更があった場合のみファイルを更新
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """メイン処理"""
    bible_dir = Path('Bible_out')
    
    if not bible_dir.exists():
        print(f"Error: {bible_dir} directory not found!")
        return
    
    # すべてのHTMLファイルを取得
    html_files = list(bible_dir.rglob('*.html'))
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    processed = 0
    modified = 0
    
    for html_file in html_files:
        if html_file.name == 'index.html':
            continue  # index.htmlはスキップ
        
        processed += 1
        if process_html_file(html_file):
            modified += 1
            print(f"Modified: {html_file}")
        
        if processed % 100 == 0:
            print(f"Processed {processed}/{len(html_files)} files...")
    
    print(f"\nCompleted!")
    print(f"Total files processed: {processed}")
    print(f"Files modified: {modified}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DPページの目次を折りたたみ可能にするスクリプト
"""

import re
import sys
from pathlib import Path

# Windows環境でのUnicode出力を有効にする
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# DPディレクトリのパス
DP_DIR = Path(r"C:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp")

# 追加するCSSスタイル
TOC_CSS = """
        /* 折りたたみ可能な目次のスタイル */
        .toc-collapsible {
            margin: 2.5rem 0;
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            background: #fbfbfb;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        }

        .toc-header {
            font-size: 1.8rem;
            font-weight: 700;
            cursor: pointer;
            list-style: none;
            user-select: none;
            color: #111;
            margin: 0;
            padding: 0.5rem 0;
        }

        .toc-header::-webkit-details-marker {
            display: none;
        }

        .toc-header::before {
            content: '▶ ';
            transition: transform 0.3s ease;
            display: inline-block;
            color: #667eea;
            margin-right: 0.5rem;
        }

        details[open].toc-collapsible .toc-header::before {
            transform: rotate(90deg);
        }

        .toc-nav {
            margin-top: 1.25rem;
        }

        .toc-nav ul {
            margin: 0;
            padding-left: 0;
            list-style: none;
        }

        .toc-nav li {
            margin: 0.2rem 0;
            padding-left: 0;
            position: relative;
        }

        .toc-nav ul ul {
            padding-left: 1.5rem;
            margin-top: 0.2rem;
            margin-bottom: 0.5rem;
            border-left: 1px solid rgba(0, 0, 0, 0.05);
        }

        .toc-nav a {
            color: #444;
            text-decoration: none;
            transition: all 0.2s ease;
            display: block;
            padding: 0.6rem 0.8rem;
            border-radius: 8px;
            font-size: 1.15rem;
            line-height: 1.4;
        }

        .toc-nav a:hover {
            color: #667eea;
            background: rgba(102, 126, 234, 0.08);
            transform: translateX(4px);
        }
"""


def add_collapsible_toc(html_content: str) -> str:
    """
    HTMLコンテンツに折りたたみ可能な目次を追加または更新する
    """
    import re
    
    # 1. CSSスタイルの更新または追加
    style_marker = "/* 折りたたみ可能な目次のスタイル */"
    if style_marker in html_content:
        # 既存のスタイルブロックを置換（柔軟なマッチング）
        pattern = r'/\* 折りたたみ可能な目次のスタイル \*/.*?\.toc-nav a:hover \{.*?\}'
        if re.search(pattern, html_content, flags=re.DOTALL):
            html_content = re.sub(pattern, TOC_CSS.strip(), html_content, flags=re.DOTALL)
    else:
        # 新规追加
        if "    </style>" in html_content:
            html_content = html_content.replace("    </style>", f"{TOC_CSS}    </style>")
        elif "</style>" in html_content:
            html_content = html_content.replace("</style>", f"{TOC_CSS}</style>")
    
    # 2. 目次構造の変換
    if '<details class="toc-collapsible"' in html_content:
        return html_content
        
    # パターン1: <nav id="toc"> を探す
    nav_pattern = r'<nav\s+[^>]*id="toc"[^>]*>'
    match = re.search(nav_pattern, html_content)
    
    if match:
        nav_start_pos = match.start()
        nav_end_pos = html_content.find('</nav>', nav_start_pos)
        if nav_end_pos != -1:
            nav_end_pos += len('</nav>')
            original_nav = html_content[nav_start_pos:nav_end_pos]
            
            h2_match = re.search(r'<h2[^>]*>目次</h2>', original_nav)
            if h2_match:
                nav_content = re.sub(r'<nav[^>]*>', '', original_nav, count=1)
                nav_content = re.sub(r'<h2[^>]*>目次</h2>', '', nav_content)
                nav_content = nav_content.replace('</nav>', '')
            else:
                nav_content = re.sub(r'<nav[^>]*>', '', original_nav, count=1)
                nav_content = nav_content.replace('</nav>', '')
            
            new_toc = f'''<details class="toc-collapsible" id="toc">
<summary class="toc-header">目次</summary>
<nav aria-label="目次" class="toc-nav">{nav_content.strip()}</nav>
</details>'''
            return html_content[:nav_start_pos] + new_toc + html_content[nav_end_pos:]

    # パターン2: 裸の <ul> 目次を探す (21kidai.html 等)
    # <h2> または <h3> の後にある <ul> で、中身が内部リンク (#数字) を含んでいるものを探す
    
    # 21kidai.html 等、階層化された（入れ子の）<ul> に対応するため、
    # 次のセクション見出し (<h2, <h3, <h4) が現れる直前の </ul> までをマッチさせる
    loose_ul_start_pattern = r'<ul>\s*<li><a\s+href="#1">'
    start_match = re.search(loose_ul_start_pattern, html_content)
    
    if start_match:
        start_pos = start_match.start()
        
        # 次の見出しを探す
        next_header = re.search(r'<h[234]', html_content[start_pos + 1:])
        if next_header:
            search_end = start_pos + 1 + next_header.start()
        else:
            search_end = len(html_content)
            
        # start_pos から search_end までの間で、一番最後にある </ul> を探す
        toc_area = html_content[start_pos:search_end]
        last_ul_close = toc_area.rfind('</ul>')
        
        if last_ul_close != -1:
            ul_end = start_pos + last_ul_close + len('</ul>')
            ul_content = html_content[start_pos:ul_end]
            
            # 前後の装飾の取り込み（既存ロジック踏襲）
            prefix_pattern = r'<p>\s*<div class="no1"><hr/><br/></div>\s*</p>\s*'
            suffix_pattern = r'\s*<p>\s*<div class="no1"><hr/><br/></div>\s*</p>'
            
            full_pattern = prefix_pattern + re.escape(ul_content) + suffix_pattern
            # re.escapeは改行の扱いに注意が必要なため、前後を個別にチェック
            
            actual_start = start_pos
            actual_end = ul_end
            
            # 前方のチェック
            pre_area = html_content[max(0, start_pos-100):start_pos]
            pre_match = re.search(prefix_pattern + r'$', pre_area, flags=re.DOTALL)
            if pre_match:
                actual_start = start_pos - (len(pre_match.group(0)))
                
            # 後方のチェック
            post_area = html_content[ul_end:ul_end+100]
            post_match = re.match(suffix_pattern, post_area, flags=re.DOTALL)
            if post_match:
                actual_end = ul_end + len(post_match.group(0))
            
            new_toc = f'''<details class="toc-collapsible" id="toc">
<summary class="toc-header">目次</summary>
<nav aria-label="目次" class="toc-nav">{ul_content}</nav>
</details>'''
            
            return html_content[:actual_start] + new_toc + html_content[actual_end:]

    return html_content


def process_dp_files():
    """
    DPディレクトリ内のすべてのHTMLファイルを処理する
    """
    html_files = list(DP_DIR.glob("[0-9]*.html"))
    
    processed_count = 0
    skipped_count = 0
    
    for html_file in html_files:
        print(f"処理中: {html_file.name}")
        
        try:
            content = html_file.read_text(encoding='utf-8')
            
            # 変換基準を緩和
            has_nav = re.search(r'<nav\s+[^>]*id="toc"[^>]*>', content)
            has_loose_ul = re.search(r'<ul>\s*<li><a\s+href="#1">', content)
            is_already_converted = "toc-collapsible" in content
            
            if has_nav or has_loose_ul or is_already_converted:
                new_content = add_collapsible_toc(content)
                
                if new_content != content:
                    html_file.write_text(new_content, encoding='utf-8')
                    processed_count += 1
                    print(f"  ✓ 更新完了")
                else:
                    skipped_count += 1
                    print(f"  - 変更なし（スキップ）")
            else:
                skipped_count += 1
                print(f"  - 目次なし（スキップ）")
                
        except Exception as e:
            print(f"  ✗ エラー: {e}")
    
    print(f"\n完了: {processed_count}ファイル処理, {skipped_count}ファイルスキップ")



if __name__ == "__main__":
    print("DPページの目次を折りたたみ可能に変換します...\n")
    process_dp_files()
    print("\n処理が完了しました。")

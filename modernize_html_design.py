#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
すべてのHTMLファイルにindex.htmlと同じモダンなデザインを適用するスクリプト
"""

import os
import re
from pathlib import Path

def get_modern_style():
    """モダンなデザインのCSSスタイルを返す"""
    return '''
    <link
        href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700;900&family=Crimson+Pro:wght@400;600;700&display=swap"
        rel="stylesheet" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Serif JP', 'Crimson Pro', serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 2rem 1rem;
            position: relative;
            overflow-x: hidden;
            font-size: 1.25rem;
            line-height: 1.9;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 107, 107, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        header {
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.8s ease-out;
        }

        h1 {
            font-size: clamp(2.5rem, 6vw, 4.5rem);
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1.5rem;
            letter-spacing: 0.05em;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
        }

        h1 a {
            text-decoration: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        h2 {
            font-size: 2.2rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 1.75rem;
            margin-top: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.7rem;
            letter-spacing: 0.05em;
        }

        h2::before {
            content: '◆';
            color: #667eea;
            font-size: 0.8em;
        }

        p {
            margin: 1em 0;
            line-height: 1.9;
            color: #e0e0e0;
        }
        
        /* すべてのテキストを白文字に */
        body, body * {
            color: #e0e0e0 !important;
        }
        
        /* 例外: リンクと強調はそのまま */
        a {
            color: #667eea !important;
        }
        
        a:hover {
            color: #f093fb !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #fff !important;
        }
        
        b, strong {
            color: #fff !important;
        }

        a {
            color: #667eea;
            text-decoration: none;
            transition: all 0.3s ease;
            border-bottom: 1px solid transparent;
        }

        a:hover {
            color: #f093fb;
            border-bottom-color: #f093fb;
        }

        hr {
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            margin: 2em 0;
        }

        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }

        li {
            margin: 0.5em 0;
            line-height: 1.9;
        }

        b, strong {
            font-weight: 700;
            color: #fff;
        }

        .content-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2rem 0;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s ease-out 0.2s both;
        }

        .content-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.4s ease;
        }

        .content-card:hover::before {
            transform: scaleX(1);
        }

        .links-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding-left: 0;
        }

        .links-list li {
            position: relative;
            padding-left: 1.6rem;
        }

        .links-list li::before {
            content: '▸';
            position: absolute;
            left: 0;
            color: #667eea;
            transition: transform 0.3s ease;
        }

        .links-list li:hover::before {
            transform: translateX(3px);
        }

        .links-list a {
            color: #e0e0e0;
            text-decoration: none;
            font-size: 1.25rem;
            line-height: 1.9;
            transition: all 0.3s ease;
            display: inline-block;
            position: relative;
            border-bottom: none;
        }

        .links-list a::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }

        .links-list a:hover {
            color: #fff;
            transform: translateX(3px);
        }

        .links-list a:hover::after {
            width: 100%;
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 768px) {
            body {
                padding: 1rem 0.75rem;
                font-size: 1.1rem;
            }

            .content-card {
                padding: 2rem;
            }

            h1 {
                font-size: clamp(2rem, 6vw, 3.5rem);
            }

            h2 {
                font-size: 1.8rem;
            }

            .links-list a {
                font-size: 1.15rem;
            }
        }

        @media (max-width: 480px) {
            body {
                font-size: 1rem;
            }

            h2 {
                font-size: 1.6rem;
            }

            .links-list a {
                font-size: 1.05rem;
            }
        }

        /* 特殊クラスのスタイル調整 */
        .section, .jpblock, .jpitem, .line, .note {
            color: #e0e0e0 !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }
        
        .note {
            color: #d0d0d0 !important;
        }
        
        ruby, ruby rt {
            color: #e0e0e0 !important;
        }
        
        /* 聖書の節リンク用スタイル（既存のものを保持） */
        a.verse-link {
            color: #e74c3c !important;
            text-decoration: none;
            font-weight: bold;
            border-bottom: none;
        }

        a.verse-link:hover {
            text-decoration: underline;
            color: #c0392b !important;
            border-bottom-color: transparent;
        }

        [id^="v"]:target {
            background-color: #fff3cd;
            padding: 0.1em 0.2em;
            border-radius: 3px;
            scroll-margin-top: 1em;
        }
    </style>
'''

def is_modernized(content):
    """既にモダン化されているかチェック"""
    # 古いスタイルが残っている場合は、モダン化されていないと判断
    old_style_indicators = [
        "font-family: sans-serif;",
        "font-family: 'Noto Sans JP'",
        "background-color: #fafafa",
        "color: #333",
        "max-width: 1250px",
    ]
    
    # 古いスタイルが存在する場合は未モダン化
    has_old_style = any(indicator in content for indicator in old_style_indicators)
    if has_old_style:
        return False
    
    # モダンなスタイルが存在する場合はモダン化済み
    modern_indicators = [
        "linear-gradient(135deg, #0f0c29",
        "Noto Serif JP",
        "fadeInDown",
        "backdrop-filter: blur"
    ]
    return any(indicator in content for indicator in modern_indicators)

def process_html_file(file_path):
    """HTMLファイルを処理してモダンなデザインを適用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 既にモダン化されている場合はスキップ
        if is_modernized(content):
            return False
        
        # headタグ内の処理
        # 既存のstyleタグを削除
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # 既存のGoogle Fontsリンクを削除
        content = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>', '', content, flags=re.IGNORECASE)
        
        # headタグを見つけて、モダンなスタイルを追加
        head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
        if head_match:
            head_end = head_match.end()
            # </head>の位置を見つける
            head_close_match = re.search(r'</head>', content[head_end:], re.IGNORECASE)
            if head_close_match:
                insert_pos = head_end + head_close_match.start()
                # モダンなスタイルを挿入
                content = content[:insert_pos] + get_modern_style() + content[insert_pos:]
        else:
            # headタグがない場合は追加
            html_match = re.search(r'<html[^>]*>', content, re.IGNORECASE)
            if html_match:
                insert_pos = html_match.end()
                head_tag = '<head>\n' + get_modern_style() + '</head>'
                content = content[:insert_pos] + head_tag + content[insert_pos:]
        
        # meta charsetを追加（まだない場合）
        if not re.search(r'<meta[^>]*charset', content, re.IGNORECASE):
            head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
            if head_match:
                insert_pos = head_match.end()
                charset_meta = '<meta charset="utf-8"/>'
                content = content[:insert_pos] + charset_meta + content[insert_pos:]
        
        # meta viewportを追加（まだない場合）
        if not re.search(r'<meta[^>]*name=["\']viewport["\']', content, re.IGNORECASE):
            head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
            if head_match:
                head_end = head_match.end()
                viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>'
                content = content[:head_end] + viewport_meta + content[head_end:]
        
        # faviconを追加（まだない場合）
        if not re.search(r'<link[^>]*rel=["\']icon["\']', content, re.IGNORECASE):
            head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
            if head_match:
                head_end = head_match.end()
                favicon_link = '<link rel="icon" href="/mimune-no-uraniwa/favicon.png" type="image/png"/>'
                content = content[:head_end] + favicon_link + content[head_end:]
        
        # og:imageを追加（まだない場合）
        if not re.search(r'<meta[^>]*property=["\']og:image["\']', content, re.IGNORECASE):
            head_match = re.search(r'</head>', content, re.IGNORECASE)
            if head_match:
                insert_pos = head_match.start()
                og_image = '<meta property="og:image" content="https://maydra.github.io/mimune-no-uraniwa/og-image.png"/>'
                content = content[:insert_pos] + og_image + content[insert_pos:]
        
        # bodyタグの属性をクリーンアップ
        body_match = re.search(r'<body[^>]*>', content, re.IGNORECASE)
        if body_match:
            body_tag = body_match.group(0)
            # background, bgcolor, alink, link, vlink, text属性を削除
            cleaned_body = re.sub(r'\s+(?:background|bgcolor|alink|link|vlink|text)=["\'][^"\']*["\']', '', body_tag, flags=re.IGNORECASE)
            content = content[:body_match.start()] + cleaned_body + content[body_match.end():]
        
        # body内のコンテンツを.containerでラップ（まだラップされていない場合）
        if not re.search(r'<div[^>]*class=["\'][^"\']*container[^"\']*["\']', content, re.IGNORECASE):
            body_match = re.search(r'<body[^>]*>', content, re.IGNORECASE)
            if body_match:
                body_start = body_match.end()
                # </body>を見つける（scriptタグより前）
                body_end_match = re.search(r'(</body>|</html>)', content[body_start:], re.IGNORECASE)
                if body_end_match:
                    body_end = body_start + body_end_match.start()
                    body_content = content[body_start:body_end].strip()
                    
                    # scriptタグを分離
                    scripts = []
                    body_without_scripts = body_content
                    script_matches = list(re.finditer(r'<script[^>]*>.*?</script>', body_content, re.DOTALL | re.IGNORECASE))
                    for match in reversed(script_matches):
                        scripts.insert(0, match.group(0))
                        body_without_scripts = body_without_scripts[:match.start()] + body_without_scripts[match.end():]
                    
                    # containerでラップ
                    if body_without_scripts.strip():
                        wrapped_content = f'<div class="container">\n{body_without_scripts}\n</div>'
                        # scriptを追加
                        if scripts:
                            wrapped_content += '\n' + '\n'.join(scripts)
                        
                        content = content[:body_start] + wrapped_content + content[body_end:]
        
        # 変更があった場合のみファイルを更新
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    root_dir = Path('.')
    
    # 除外するディレクトリ
    exclude_dirs = {
        'Bible_out',  # 聖書ファイルは既に特別なスタイルがある
        'pagefind',  # Pagefindのファイル
        'node_modules',  # もしあれば
        '.git',  # Gitディレクトリ
    }
    
    # 除外するファイル（ルートディレクトリのみ）
    exclude_root_files = {
        'index.html',  # ルートのindex.htmlは既にモダン
        'search.html',
        'search-all.html',
        'gacha.html',
        'google4950bff256850b5a.html',
    }
    
    # すべてのHTMLファイルを取得
    html_files = []
    for html_file in root_dir.rglob('*.html'):
        # 除外チェック
        if any(exclude_dir in html_file.parts for exclude_dir in exclude_dirs):
            continue
        # ルートディレクトリの特定のファイルのみ除外
        if html_file.name in exclude_root_files and html_file.parent == root_dir:
            continue
        html_files.append(html_file)
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    processed = 0
    modified = 0
    
    for html_file in html_files:
        processed += 1
        if process_html_file(html_file):
            modified += 1
            # ファイルパスの出力をスキップ（エンコーディング問題を回避）
        
        if processed % 50 == 0:
            print(f"Processed {processed}/{len(html_files)} files... (Modified: {modified})")
    
    print(f"\nCompleted!")
    print(f"Total files processed: {processed}")
    print(f"Files modified: {modified}")

if __name__ == '__main__':
    main()

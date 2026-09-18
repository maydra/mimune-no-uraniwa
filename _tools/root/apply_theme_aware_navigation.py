import os
import re
import json
from pathlib import Path

# ルートディレクトリ設定
ROOT_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa")

NAV_STYLE_LIGHT = """
/* モダンなナビゲーションボタン用スタイル (Light Theme) */
.page-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0;
    padding: 1rem 0;
}

.nav-btn {
    flex: 1;
    text-align: center;
    padding: 0.8rem 1rem;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 50px;
    color: #333;
    text-decoration: none;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.nav-btn:hover {
    background: #f0f0f0;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    border-color: rgba(102, 126, 234, 0.3);
    color: #000;
}

.nav-btn span {
    font-size: 1.2rem;
    line-height: 1;
}

@media (max-width: 600px) {
    .page-nav {
        flex-direction: column;
        gap: 0.75rem;
    }
    .nav-btn {
        width: 100%;
        padding: 0.7rem 1rem;
    }
}
"""

NAV_STYLE_DARK = """
/* モダンなナビゲーションボタン用スタイル (Dark Theme) */
.page-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0;
    padding: 1rem 0;
}

.nav-btn {
    flex: 1;
    text-align: center;
    padding: 0.8rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50px;
    color: #e0e0e0;
    text-decoration: none;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.nav-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    border-color: rgba(102, 126, 234, 0.5);
    color: #fff;
}

.nav-btn span {
    font-size: 1.2rem;
    line-height: 1;
}

@media (max-width: 600px) {
    .page-nav {
        flex-direction: column;
        gap: 0.75rem;
    }
    .nav-btn {
        width: 100%;
        padding: 0.7rem 1rem;
    }
}
"""

def extract_links(content):
    """既存のナビゲーションからリンクを抽出する"""
    links = {"prev": None, "index": None, "next": None}
    
    # 前のページ、目次、次のページ のリンクを探す
    prev_match = re.search(r'<a href="([^"]+)">前のページ(?:に戻る)?</a>', content)
    index_match = re.search(r'<a href="([^"]+)">目次(?:に戻る)?</a>', content)
    next_match = re.search(r'<a href="([^"]+)">次のページ(?:に進む)?</a>', content)
    
    # 既に新しい形式（nav-btn）になっている場合も考慮
    if not prev_match:
        prev_match = re.search(r'<a href="([^"]+)" class="nav-btn"><span>←</span> 前へ</a>', content)
    if not index_match:
        index_match = re.search(r'<a href="([^"]+)" class="nav-btn">目次</a>', content)
    if not next_match:
        next_match = re.search(r'<a href="([^"]+)" class="nav-btn">次へ <span>→</span></a>', content)

    if prev_match: links["prev"] = prev_match.group(1)
    if index_match: links["index"] = index_match.group(1)
    if next_match: links["next"] = next_match.group(1)
    
    return links

def build_nav_html(links):
    """新しいナビゲーションHTMLを構築する"""
    nav_html = '<nav class="page-nav">\n'
    
    if links["prev"]:
        nav_html += f'  <a href="{links["prev"]}" class="nav-btn"><span>←</span> 前へ</a>\n'
    else:
        nav_html += '  <div style="flex:1"></div>\n'
        
    if links["index"]:
        nav_html += f'  <a href="{links["index"]}" class="nav-btn">目次</a>\n'
    else:
        nav_html += '  <div style="flex:1"></div>\n'
        
    if links["next"]:
        nav_html += f'  <a href="{links["next"]}" class="nav-btn">次へ <span>→</span></a>\n'
    else:
        nav_html += '  <div style="flex:1"></div>\n'
        
    nav_html += '</nav>'
    return nav_html

def clean_html_structure(content):
    """HTMLタグの重複などをクリーンアップする"""
    if content.lower().count('</body>') > 1:
        parts = re.split(r'</body>', content, flags=re.IGNORECASE)
        content = "".join(parts[:-1]) + "</body>" + parts[-1]
    
    if content.lower().count('</html>') > 1:
        parts = re.split(r'</html>', content, flags=re.IGNORECASE)
        content = "".join(parts[:-1]) + "</html>" + parts[-1]
        
    return content

def is_dark_theme(content, file_path):
    """ページがダークテーマかどうかを判定する"""
    # 1. ディレクトリによる判定 (dp はライトテーマ)
    if "dp/" in str(file_path).replace("\\", "/"):
        return False
    
    # 2. typo-report のクラスによる判定
    if 'id="typo-report" class="typo-box dark-theme"' in content:
        return True
    
    # 3. 背景色の指定による判定 (例: linear-gradient の色)
    if '#0f0c29' in content or 'background: #000' in content or 'background: black' in content:
        return True
    
    return True # デフォルトはダークテーマ（dp以外）

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        links = extract_links(content)
        if not any(links.values()):
            return False

        nav_html = build_nav_html(links)
        
        # 1. 既存の全てのナビゲーションを除去
        content = re.sub(r'<div style="margin-top: 2em;">\s*<hr\s*/?>.*?</div>', '', content, flags=re.DOTALL)
        content = re.sub(r'<p><a href="[^"]+">目次に戻る</a></p>\s*<p><a href="[^"]+">前のページに戻る</a></p>\s*<p><a href="[^"]+">次のページに進む</a></p>', '', content, flags=re.DOTALL)
        content = re.sub(r'<nav class="page-nav">.*?</nav>', '', content, flags=re.DOTALL)

        # 2. クリーンアップ
        content = clean_html_structure(content)

        # 3. 再挿入
        if '</h1>' in content:
            content = content.replace('</h1>', f'</h1>\n{nav_html}')
        elif '<div class="container">' in content:
            content = content.replace('<div class="container">', f'<div class="container">\n{nav_html}')
        else:
            if '<body>' in content:
                content = content.replace('<body>', f'<body>\n{nav_html}')

        content = content.replace('</body>', f'{nav_html}\n</body>')

        # 4. CSSの追加/更新 (テーマ別)
        dark = is_dark_theme(content, file_path)
        style_to_use = NAV_STYLE_DARK if dark else NAV_STYLE_LIGHT
        
        # 既存のナビゲーションスタイルを除去（念のため）
        content = re.sub(r'/\* モダンなナビゲーションボタン用スタイル.*?\.nav-btn\s*\{.*?\}', '', content, flags=re.DOTALL)
        
        if '</style>' in content:
            content = content.replace('</style>', f'{style_to_use}\n</style>')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    pages_json_path = ROOT_DIR / "pages.json"
    if not pages_json_path.exists():
        print("pages.json not found.")
        return

    with open(pages_json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    excluded_keywords = ["index", "Index", "hajimeni", "jyobunn", "mokuji", "search", "gacha", "preview/", "library/"]
    
    files_to_process = []
    for page in pages:
        if not any(kw in page for kw in excluded_keywords):
            full_path = ROOT_DIR / page
            if full_path.exists():
                files_to_process.append(full_path)

    print(f"Found {len(files_to_process)} content files to apply theme-aware navigation update...")
    
    count = 0
    modified = 0
    for file_path in files_to_process:
        count += 1
        if process_file(file_path):
            modified += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(files_to_process)} files... (Modified: {modified})")

    print(f"Finished! Processed {count} files, Modified {modified} files.")

if __name__ == "__main__":
    main()

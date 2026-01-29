import os
import re
from pathlib import Path

# 対象となるディレクトリ
TARGET_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/dp")

NAV_STYLE = """
/* モダンなナビゲーションボタン用スタイル */
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

def extract_links(content):
    """既存のナビゲーションからリンクを抽出する"""
    links = {"prev": None, "index": None, "next": None}
    
    # 前のページ、目次、次のページ のリンクを探す（正規表現を強化）
    prev_match = re.search(r'<a href="([^"]+)">前のページ(?:に戻る)?</a>', content)
    index_match = re.search(r'<a href="([^"]+)">目次(?:に戻る)?</a>', content)
    next_match = re.search(r'<a href="([^"]+)">次のページ(?:に進む)?</a>', content)
    
    # 既に新しい形式（nav-btn）になっている場合も考慮して抽出
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
    # </body> が複数ある場合、最後の一つ以外を削除
    if content.lower().count('</body>') > 1:
        parts = re.split(r'</body>', content, flags=re.IGNORECASE)
        # 最後の </body> 以前のものを結合し、最後に一つだけ </body> を付ける
        content = "".join(parts[:-1]) + "</body>" + parts[-1]
    
    # </html> も同様
    if content.lower().count('</html>') > 1:
        parts = re.split(r'</html>', content, flags=re.IGNORECASE)
        content = "".join(parts[:-1]) + "</html>" + parts[-1]
        
    return content

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.name == "index.html":
            return False

        links = extract_links(content)
        if not any(links.values()):
            return False

        nav_html = build_nav_html(links)
        
        # 1. 既存の全てのナビゲーション（旧形式・新しい形式両方）を除去
        # 旧形式
        content = re.sub(r'<div style="margin-top: 2em;">\s*<hr\s*/?>.*?</div>', '', content, flags=re.DOTALL)
        # 既に挿入済みの新形式 nav
        content = re.sub(r'<nav class="page-nav">.*?</nav>', '', content, flags=re.DOTALL)

        # 2. クリーンアップ（重複 </body> 等の除去）
        content = clean_html_structure(content)

        # 3. 再挿入
        # 上部：<h1> の直後
        if '</h1>' in content:
            content = content.replace('</h1>', f'</h1>\n{nav_html}')
        elif '<div class="container">' in content:
            content = content.replace('<div class="container">', f'<div class="container">\n{nav_html}')

        # 下部：</body> の直前
        content = content.replace('</body>', f'{nav_html}\n</body>')

        # 4. CSSの追加/更新
        if '</style>' in content:
            if '.page-nav' not in content:
                content = content.replace('</style>', f'{NAV_STYLE}\n</style>')
            else:
                # 既にスタイルがある場合は、最新のものに置き換え
                content = re.sub(r'/\* モダンなナビゲーションボタン用スタイル \*/.*?@media.*?\.nav-btn\s*\{.*?\}', NAV_STYLE, content, flags=re.DOTALL)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    if not TARGET_DIR.exists():
        print(f"Directory not found: {TARGET_DIR}")
        return

    html_files = list(TARGET_DIR.glob("*.html"))
    print(f"Found {len(html_files)} files in DP directory...")
    
    count = 0
    for file_path in html_files:
        if process_file(file_path):
            count += 1
            
    print(f"Finished! Processed {count} files.")

if __name__ == "__main__":
    main()

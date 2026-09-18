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
    width: 100%;
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
    width: 100%;
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
    links = {"prev": None, "index": None, "next": None}
    
    # 既存のレガシーなリンク
    prev_m = re.search(r'<a href="([^"]+)">前のページ(?:に戻る)?</a>', content)
    index_m = re.search(r'<a href="([^"]+)">目次(?:に戻る)?</a>', content)
    next_m = re.search(r'<a href="([^"]+)">次のページ(?:に進む)?</a>', content)
    
    # 新しいUI形式のリンク（もし存在すれば）
    if not prev_m: prev_m = re.search(r'<a href="([^"]+)" class="nav-btn"><span>←</span> 前へ</a>', content)
    if not index_m: index_m = re.search(r'<a href="([^"]+)" class="nav-btn">目次</a>', content)
    if not next_m: next_m = re.search(r'<a href="([^"]+)" class="nav-btn">次へ <span>→</span></a>', content)

    if prev_m: links["prev"] = prev_m.group(1)
    if index_m: links["index"] = index_m.group(1)
    if next_m: links["next"] = next_m.group(1)
    
    return links

def build_nav_html(links):
    nav_html = '<nav class="page-nav">\n'
    if links["prev"]: nav_html += f'  <a href="{links["prev"]}" class="nav-btn"><span>←</span> 前へ</a>\n'
    else: nav_html += '  <div style="flex:1"></div>\n'
    
    if links["index"]: nav_html += f'  <a href="{links["index"]}" class="nav-btn">目次</a>\n'
    else: nav_html += '  <div style="flex:1"></div>\n'
    
    if links["next"]: nav_html += f'  <a href="{links["next"]}" class="nav-btn">次へ <span>→</span></a>\n'
    else: nav_html += '  <div style="flex:1"></div>\n'
    
    nav_html += '</nav>'
    return nav_html

def is_dark_theme(content, file_path):
    if "dp/" in str(file_path).replace("\\", "/"): return False
    if 'dark-theme' in content: return True
    if '#0f0c29' in content: return True
    return True

def apply_safely(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        links = extract_links(content)
        if not any(links.values()):
            return False

        nav_html = build_nav_html(links)
        
        # 1. 既存のナビゲーションを非常に慎重に除去（文字列一致ベース）
        # レガシーな目次ブロック
        content = re.sub(r'<p><a href="[^"]+">目次に戻る</a></p>\s*<p><a href="[^"]+">前のページに戻る</a></p>\s*<p><a href="[^"]+">次のページに進む</a></p>', '', content, flags=re.DOTALL)
        content = re.sub(r'<div style="margin-top: 2em;">\s*<hr\s*/?>.*?</div>', '', content, flags=re.DOTALL)
        # 以前適用した nav クラス
        content = re.sub(r'<nav class="page-nav">.*?</nav>', '', content, flags=re.DOTALL)

        # 2. 本文の上（h1の直下）と下（</body>の直前）に挿入
        if '</h1>' in content:
            content = content.replace('</h1>', f'</h1>\n{nav_html}', 1)
        
        # </body> の直前に挿入（最後の一つに限定）
        if '</body>' in content:
            parts = content.rsplit('</body>', 1)
            content = parts[0] + nav_html + '\n</body>' + parts[1]

        # 3. CSSの適用（テーマ別）
        dark = is_dark_theme(content, file_path)
        style_to_use = NAV_STYLE_DARK if dark else NAV_STYLE_LIGHT
        
        # 既存の「モダンなナビゲーション...」スタイルを確実に消去（コメントベース）
        content = re.sub(r'/\* モダンなナビゲーションボタン用スタイル.*?\*/', '', content, flags=re.DOTALL)
        # 本来あるはずのない余分な閉じカッコなどの混入を避けるため、正規表現ではなく文字列置換を優先
        # ただし、今回は git restore 直後なので比較的きれいはず

        if '</style>' in content:
            parts = content.rsplit('</style>', 1)
            content = parts[0] + style_to_use + '\n</style>' + parts[1]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    pages_json_path = ROOT_DIR / "pages.json"
    with open(pages_json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    excluded = ["index", "Index", "hajimeni", "jyobunn", "mokuji", "search", "gacha", "preview/", "library/"]
    
    modified = 0
    for page in pages:
        if not any(kw in page for kw in excluded):
            full_path = ROOT_DIR / page
            if full_path.exists():
                if apply_safely(full_path):
                    modified += 1

    print(f"Applied safely to {modified} files.")

if __name__ == "__main__":
    main()

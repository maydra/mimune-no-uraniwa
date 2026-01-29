import os
import re
from pathlib import Path

# 対象となるルートディレクトリ
ROOT_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa")

# ランダムスクロール用スクリプトの定義
RANDOM_SCROLL_SCRIPT = """
<script>
  const params = new URLSearchParams(window.location.search);
  if (params.get("randomScroll") === "true") {
    window.onload = () => {
      const y = Math.floor(Math.random() * document.body.scrollHeight);
      window.scrollTo({ top: y, behavior: "smooth" });
    };
  }
</script>"""

def clean_html_tags(content):
    """二重のbodyタグや不正なタグをクリーンアップする"""
    # 重複するbodyタグの整理
    # すでに <div class="container"> がある場合を考慮しつつ、
    # 余分な <body ...> タグが本文中にある場合は除去する
    
    # 本文（最初の<body>の後）にある <body ...> を除去
    content = re.sub(r'(<body[^>]*>.*?)(<body[^>]*>)', r'\1', content, flags=re.DOTALL | re.IGNORECASE)
    
    # 重複する </body> も除去（最後のものだけ残す）
    if content.lower().count('</body>') > 1:
        parts = re.split(r'</body>', content, flags=re.IGNORECASE)
        # 最後の空要素以外のパーツを結合し、最後に一つだけ </body> を付ける
        content = "</body>".join(parts[:-1]) + "</body>" + parts[-1]
        
    return content

def fix_random_scroll_script(file_path):
    """HTMLファイル内のrandomScrollスクリプトを一つに正規化する"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 既存のランダムスクロールスクリプトをすべて削除
        # <script>...</script> の中で randomScroll を含んでいるものを根こそぎ消す
        content = re.sub(r'<script[^>]*>(?:(?!<\/script>).)*?randomScroll.*?<\/script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # HTMLタグのクリーンアップ
        content = clean_html_tags(content)
        
        # </body> の直前にスクリプトを一つだけ挿入
        if '</body>' in content:
            # 最後の </body> の直前に挿入
            parts = content.rsplit('</body>', 1)
            content = parts[0] + f'\n{RANDOM_SCROLL_SCRIPT}\n</body>' + parts[1]
        elif '</html>' in content:
            content = content.replace('</html>', f'<body>{RANDOM_SCROLL_SCRIPT}</body></html>')
        else:
            content += f'\n{RANDOM_SCROLL_SCRIPT}'
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # pages.json から対象ファイルリストを取得
    import json
    pages_json_path = ROOT_DIR / "pages.json"
    
    if not pages_json_path.exists():
        print("pages.json not found.")
        return

    with open(pages_json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    # 除外フィルター（gacha.htmlの実装に合わせる）
    excluded_keywords = ["index", "Index", "hajimeni", "jyobunn", "mokuji", "search", "gacha", "preview/", "library/"]
    
    files_to_fix = []
    for page in pages:
        if not any(kw in page for kw in excluded_keywords):
            full_path = ROOT_DIR / page
            if full_path.exists():
                files_to_fix.append(full_path)

    print(f"Found {len(files_to_fix)} content files to process...")
    
    count = 0
    for file_path in files_to_fix:
        if fix_random_scroll_script(file_path):
            count += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(files_to_fix)} files...")

    print(f"Finished! Processed {count} files.")

if __name__ == "__main__":
    main()

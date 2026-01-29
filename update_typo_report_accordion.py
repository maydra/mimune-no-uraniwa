import os
import re
from pathlib import Path

# 対象となるルートディレクトリ
ROOT_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa")

def update_typo_report_to_accordion(file_path):
    """HTMLファイル内の誤植報告セクションをアコーディオン形式に変換する"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 旧形式のセクション全体を抽出
        # <section id="typo-report" ...> ... </section>
        section_pattern = re.compile(r'<section id="typo-report"[^>]*>.*?</section>', re.DOTALL | re.IGNORECASE)
        match = section_pattern.search(content)
        
        if not match:
            return False
            
        old_section = match.group(0)
        
        # すでに details タグが含まれている場合はスキップ
        if '<details' in old_section.lower():
            return False

        # タイトル部分（h3）と説明部分（p）を抽出
        title_match = re.search(r'<h3[^>]*>(.*?)</h3>', old_section, re.IGNORECASE)
        desc_match = re.search(r'<p[^>]*class="typo-desc"[^>]*>(.*?)</p>', old_section, re.IGNORECASE)
        form_match = re.search(r'<form[^>]*>.*?</form>', old_section, re.DOTALL | re.IGNORECASE)
        iframe_match = re.search(r'<iframe[^>]*>.*?</iframe>', old_section, re.DOTALL | re.IGNORECASE)

        if not (title_match and form_match):
            return False

        title = title_match.group(1).strip()
        desc = desc_match.group(1).strip() if desc_match else ""
        form_html = form_match.group(0)
        iframe_html = iframe_match.group(0) if iframe_match else ""

        # 新しいアコーディオン形式の構造を作成
        # details/summary を使用
        # summary のデザインを調整するためのスタイルも含む
        new_section = f'''<details id="typo-report" class="typo-box dark-theme">
  <summary class="typo-title">{title}</summary>
  <p class="typo-desc">{desc}</p>
  {form_html}
  {iframe_html}
</details>'''

        # コンテンツの置換
        content = content.replace(old_section, new_section)
        
        # CSSの修正（summaryタグへの対応など）
        # .typo-box が details になるため、スタイルを微調整
        content = content.replace('.dark-theme .typo-title{', '.dark-theme .typo-title{ cursor: pointer; ')
        
        # summary のデフォルトの矢印を制御したり、余白を調整するスタイルを追加
        if '<style>' in content and '.typo-title' in content:
            new_styles = '''
  .typo-box summary { cursor: pointer; list-style: none; outline: none; }
  .typo-box summary::-webkit-details-marker { display: none; }
  .typo-box summary::before { content: '▶'; display: inline-block; margin-right: 0.5rem; transition: transform 0.2s; font-size: 0.8em; }
  .typo-box[open] summary::before { transform: rotate(90deg); }
  .typo-box[open] { padding-bottom: 1.5rem; }'''
            # スタイルブロックの終わりに挿入
            content = content.replace('</style>', f'{new_styles}\n</style>')

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

    # 除外フィルター（前回と同様）
    excluded_keywords = ["index", "Index", "hajimeni", "jyobunn", "mokuji", "search", "gacha", "preview/", "library/"]
    
    files_to_process = []
    for page in pages:
        if not any(kw in page for kw in excluded_keywords):
            full_path = ROOT_DIR / page
            if full_path.exists():
                files_to_process.append(full_path)

    print(f"Found {len(files_to_process)} content files to update Typo Report UI...")
    
    count = 0
    modified = 0
    for file_path in files_to_process:
        count += 1
        if update_typo_report_to_accordion(file_path):
            modified += 1
        if count % 100 == 0:
            print(f"Processed {count}/{len(files_to_process)} files... (Modified: {modified})")

    print(f"Finished! Processed {count} files, Modified {modified} files.")

if __name__ == "__main__":
    main()

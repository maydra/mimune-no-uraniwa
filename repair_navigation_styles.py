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

def is_dark_theme(content, file_path):
    if "dp/" in str(file_path).replace("\\", "/"):
        return False
    if 'id="typo-report" class="typo-box dark-theme"' in content:
        return True
    if '#0f0c29' in content or 'background: #000' in content:
        return True
    return True

def repair_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 旧スタイルを徹底的に削除
        # 1. コメント付きのブロック (DP pilot, Global v1, Global v2)
        content = re.sub(r'/\* モダンなナビゲーションボタン用スタイル.*?\n\}\s*\}', '', content, flags=re.DOTALL)
        content = re.sub(r'/\* モダンなナビゲーションボタン用スタイル.*?\.nav-btn\s*\{.*?\}', '', content, flags=re.DOTALL)
        
        # 2. 残骸 (タグの整合性が崩れている場合など)
        content = re.sub(r'\.page-nav\s*\{[^\}]+\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\.nav-btn\s*\{[^\}]+\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\.nav-btn\s+span\s*\{[^\}]+\}', '', content, flags=re.DOTALL)
        content = re.sub(r'@media\s+\(max-width:\s+600px\)\s*\{\s*\.page-nav\s*\{[^\}]+\}\s*\.nav-btn\s*\{[^\}]+\}\s*\}', '', content, flags=re.DOTALL)

        # 3. 余分な閉じカッコなどのクリーンアップ（正規表現で完全にマッチしなかった場合のため）
        # 特に DP 10sojo.html で見られたような余計な `}` を掃除する
        # ただし、他のスタイルの閉じカッコを消さないよう注意が必要

        # テーマ判定と新しいスタイルの挿入
        dark = is_dark_theme(content, file_path)
        style_to_use = NAV_STYLE_DARK if dark else NAV_STYLE_LIGHT
        
        if '</style>' in content:
            # 最後の </style> の直前に挿入
            parts = content.rsplit('</style>', 1)
            content = parts[0] + style_to_use + '\n</style>' + parts[1]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error repairing {file_path}: {e}")
        return False

def main():
    pages_json_path = ROOT_DIR / "pages.json"
    if not pages_json_path.exists():
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

    print(f"Repairing navigation styles in {len(files_to_process)} files...")
    
    modified = 0
    for file_path in files_to_process:
        if repair_file(file_path):
            modified += 1
            
    print(f"Finished! Repaired {modified} files.")

if __name__ == "__main__":
    main()

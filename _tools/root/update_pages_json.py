import json
import os
from pathlib import Path

ROOT_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa")
PAGES_JSON = ROOT_DIR / "pages.json"
TARGET_DIR = ROOT_DIR / "syougairotei_11"

def update_pages_json():
    if not PAGES_JSON.exists():
        print("pages.json not found")
        return

    with open(PAGES_JSON, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    # Remove incorrect syougairotei_11 entries
    new_pages = [p for p in pages if not p.startswith("syougairotei_11/")]

    # Get actual files
    if not TARGET_DIR.exists():
        print("Target directory not found")
        return

    actual_files = []
    for f in TARGET_DIR.glob("*.html"):
        if f.name.startswith("chapter") and not f.name.endswith(".bak"):
            actual_files.append(f"syougairotei_11/{f.name}")
    
    # Add actual files
    new_pages.extend(actual_files)
    
    # Sort
    new_pages.sort()

    with open(PAGES_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_pages, f, indent=2, ensure_ascii=False)
    
    print(f"Updated pages.json. Removed old entries, added {len(actual_files)} new entries.")

if __name__ == "__main__":
    update_pages_json()

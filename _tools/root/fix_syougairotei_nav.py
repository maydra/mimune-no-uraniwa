import os
import re
from pathlib import Path

ROOT_DIR = Path("C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa")

def get_sorted_files(dir_path):
    files = []
    if not dir_path.exists():
        return []
    for f in dir_path.glob("*.html"):
        if f.name.startswith("0") and f.name != "index.html":
            files.append(f)
    return sorted(files, key=lambda x: x.name)

def fix_syougairotei_nav():
    # Identify volumes 1 to 11
    volumes = []
    for i in range(1, 12): # 1 to 11 likely, check directories
        dir_name = f"syougairotei_{i}"
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            volumes.append((i, dir_path))
    
    volumes.sort(key=lambda x: x[0])
    
    print(f"Found volumes: {[v[1].name for v in volumes]}")
    
    for i in range(len(volumes) - 1):
        curr_vol_num, curr_dir = volumes[i]
        next_vol_num, next_dir = volumes[i+1]
        
        curr_files = get_sorted_files(curr_dir)
        next_files = get_sorted_files(next_dir)
        
        if not curr_files or not next_files:
            continue
            
        last_file_curr = curr_files[-1]
        first_file_next = next_files[0] # Usually 001.html
        
        print(f"Linking {next_dir.name}/{first_file_next.name} Prev -> {curr_dir.name}/{last_file_curr.name}")
        
        # Determine relative path for link
        # From next_dir/001.html to curr_dir/last.html
        # ../syougairotei_X/last.html
        rel_link = f"../{curr_dir.name}/{last_file_curr.name}"
        
        # Modify first_file_next
        update_nav(first_file_next, rel_link)

def update_nav(file_path, prev_link):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if Prev button is missing or needs update
    # Regex for top nav
    # <nav class="page-nav">\s*<div style="flex:1"></div>
    pattern_top = r'(<nav class="page-nav">\s*)<div style="flex:1"></div>(\s*<a href="index.html" class="nav-btn">目次</a>)'
    
    replacement = f'\\1<a href="{prev_link}" class="nav-btn"><span>←</span> 前へ</a>\\2'
    
    new_content = re.sub(pattern_top, replacement, content)
    
    # Also remove redundant INDEX link if present
    # <a href=".*" style="color : red;" target="_top">INDEXへ</a>
    # Note: Regex needs to be careful
    new_content = re.sub(r'\s*<a href="[^"]*index\.html" style="color : red;" target="_top">INDEXへ</a>', '', new_content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path.name}")
    else:
        print(f"No changes for {file_path.name} (maybe already updated)")

if __name__ == "__main__":
    fix_syougairotei_nav()

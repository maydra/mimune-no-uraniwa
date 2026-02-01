import os
import re

root_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa"
root_index = os.path.join(root_dir, "index.html")

def process_file(file_path):
    if os.path.normpath(file_path) == os.path.normpath(root_index):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determine relative path to root index.html
    rel_path = os.path.relpath(root_dir, os.path.dirname(file_path))
    root_link = os.path.join(rel_path, "index.html").replace("\\", "/")
    
    # Check if a link to root index.html already exists
    # Patterns to look for:
    # 1. Relative links: index.html, ../index.html, etc.
    # 2. Absolute URL: https://maydra.github.io/mimune-no-uraniwa/index.html
    # 3. Text: トップページ, トップに戻る, み旨の裏庭トップ
    
    has_link = False
    
    # Check for root URL
    if "maydra.github.io/mimune-no-uraniwa/index.html" in content:
        has_link = True
    elif f'href="{root_link}"' in content or f"href='{root_link}'" in content:
        has_link = True
    elif 'href="/mimune-no-uraniwa/index.html"' in content:
        has_link = True
    
    if not has_link:
        print(f"Adding link to: {file_path}")
        
        # Determine if it's a dark or light theme
        is_dark = "background: linear-gradient" in content or "background-color: #2" in content or "background: #0" in content
        if "#fafafa" in content or "background-color: #fff" in content or 'bgcolor="#ffffcc"' in content:
            is_dark = False
        
        if is_dark:
            link_style = 'color: #fff; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2);'
            container_style = 'border-top: 1px solid rgba(255, 255, 255, 0.1);'
        else:
            link_style = 'color: #333; background: rgba(0, 0, 0, 0.05); border: 1px solid rgba(0, 0, 0, 0.1);'
            container_style = 'border-top: 1px solid rgba(0, 0, 0, 0.1);'

        link_html = f'''
    <div class="nav-links" style="margin-top: 4rem; text-align: center; padding-top: 2rem; {container_style}">
        <a href="{root_link}" style="display: inline-block; text-decoration: none; padding: 1rem 3rem; border-radius: 50px; transition: all 0.3s; font-weight: 700; letter-spacing: 0.05em; {link_style}">トップページへ戻る</a>
    </div>
'''
        
        if "</body>" in content:
            new_content = content.replace("</body>", f"{link_html}</body>")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(link_html)


def main():
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower() == "index.html":
                file_path = os.path.join(root, file)
                process_file(file_path)

if __name__ == "__main__":
    main()

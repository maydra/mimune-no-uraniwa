
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def cleanup_file(filepath, filename):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='cp932') as f:
                content = f.read()
        except:
            print(f"Failed to read {filename}")
            return
            
    original_content = content
    
    # 1. Remove double headers introduced by repair script
    # Pattern: <h2><h2 id="..."> -> <h2 id="...">
    # Regex: <(h[1-6])>\s*<\1([^>]*)>
    # Replace with <\1\2>
    
    content = re.sub(r'<(h[1-6])>\s*<\1([^>]*)>', r'<\1\2>', content, flags=re.IGNORECASE)
    
    # 2. Unwrap remaining header self-links (including H1)
    # Pattern: <hX attributes...><a href="#...">Text</a></hX>
    # We want to keep <hX attributes...>Text</hX>
    
    def unwrap_header(match):
        tag = match.group(1)
        attrs = match.group(2)
        inner_text = match.group(3)
        return f'<{tag}{attrs}>{inner_text}</{tag}>'
        
    # Regex:
    # <(h[1-6])       -> Group 1: tag
    # ([^>]*)>        -> Group 2: attributes (e.g. ' id="foo"')
    # \s*<a[^>]*href=["\']#[^"\']*["\'][^>]*>
    # ((?:(?!</a>).)*?) -> Group 3: inner text
    # </a>\s*</\1>
    
    content = re.sub(r'<(h[1-6])([^>]*)>\s*<a[^>]*href=["\']#[^"\']*["\'][^>]*>((?:(?!</a>).)*?)</a>\s*</\1>', unwrap_header, content, flags=re.DOTALL | re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned content: {filename}")

def main():
    if not os.path.exists(TARGET_DIR):
        return

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join(TARGET_DIR, filename)
        cleanup_file(filepath, filename)

if __name__ == "__main__":
    main()

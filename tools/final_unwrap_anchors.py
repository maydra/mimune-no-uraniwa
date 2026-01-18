
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def unwrap_anchors(filepath, filename):
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
    
    # Pattern: <a href="FILENAME" ... target="right"> ... </a>
    # Or just any anchor that wraps a huge block.
    
    # We really just want to unwrap anchors that point to the file itself OR are > 200 chars long.
    # filename variable contains the current filename.
    
    def unwrap_match(match):
        full_tag = match.group(0)
        href = match.group(1)
        inner_content = match.group(2)
        
        # Check if self-link (simple check)
        # href might be "fp10_01.html" or "#top"
        
        is_self_link = False
        if filename in href:
            is_self_link = True
        elif href.startswith("#"):
            is_self_link = True
            
        if is_self_link and len(inner_content) > 50:
             return inner_content
             
        if len(inner_content) > 200:
             return inner_content

        return full_tag
        
    # Regex: <a [^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>
    # Dotall is crucial.
    
    content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>((?:(?!</a>).)*?)</a>', unwrap_match, content, flags=re.DOTALL | re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Unwrapped anchors in: {filename}")

def main():
    if not os.path.exists(TARGET_DIR):
        print("Target dir not found")
        return

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join(TARGET_DIR, filename)
        unwrap_anchors(filepath, filename)

if __name__ == "__main__":
    main()

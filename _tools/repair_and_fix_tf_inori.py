
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def repair_file(filepath, filename):
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
    
    # 1. Repair broken headers from previous run
    # Pattern: <h2<a  -> <h2><a
    # Pattern: <h2Text -> <h2>Text
    # We look for <h[1-6] followed immediately by something that is NOT a space or >.
    # Actually, the previous script replaced <h2 id="..."> with <h2
    # So if there was a space after id removal (likely not, regex was specific), checks are needed.
    
    # Fix <hX< -> <hX><
    content = re.sub(r'<(h[1-6])(<)', r'<\1>\2', content)
    
    # Fix <hXText -> <hX>Text (where Text is not space)
    # Be careful not to match <h2 class="..."> which is valid.
    # The broken ones have NO attributes because the ID was the only attribute and it was stripped.
    # So we look for <h[1-6] followed by non-space, non->
    
    def repair_tag(match):
        tag = match.group(1)
        following = match.group(2)
        return f'<{tag}>{following}'

    content = re.sub(r'<(h[1-6])([^>\s])', repair_tag, content)

    # 2. Correctly strip giant IDs (re-run logic with fix)
    # The previous run only stripped IDs > 50 chars.
    # We need to ensure we don't break tags again.
    
    def fix_header_id_correctly(match):
        tag_start = match.group(1) # h2
        id_val = match.group(2)
        remainder = match.group(3) # attributes
        
        if len(id_val) > 50:
            # Drop the ID, return tag with remainder AND closing bracket
            return f'<{tag_start}{remainder}>'
        return match.group(0)

    # Regex to find headers with IDs
    content = re.sub(r'<(h[1-6])[^>]*id=["\']([^"\']*)["\']([^>]*)>', fix_header_id_correctly, content, flags=re.IGNORECASE)

    # 3. Enhanced Unwrap Logic
    # Unwrap anchors that wrap headers or are huge.
    
    def unwrap_match(match):
        full_tag = match.group(0)
        href = match.group(1)
        inner_content = match.group(2)
        
        # Unwrap if:
        # - Contains block tag
        # - Is a header self-link (even if short)
        # - Content > 50 chars
        
        if re.search(r'<(h[1-6]|div|p|br|table|ul|li)', inner_content, re.IGNORECASE):
            return inner_content
        
        if len(inner_content) > 50:
            return inner_content
            
        # Check if parent is a header? The match is just the anchor.
        # But if the anchor contains a header (e.g. <a...><h1>...</h1></a>), caught above.
        # If the anchor IS inside a header (e.g. <h1><a...>Text</a></h1>), regex won't know context.
        # BUT, detecting if 'href' looks like a self-link fragment:
        if href.startswith('#'):
            # It's a fragment link.
            # If text matches fragment ID? hard to tell.
            # But generally, in this specific corpus, these self-links are redundant.
            # If it's inside a header, we want to unwrap it.
            # We can't easily check "inside header" with this regex.
            # However, we can perform a separate pass: 
            pass

        return full_tag

    content = re.sub(r'<a[^>]*href=["\'](#[^"\']*)["\'][^>]*>((?:(?!</a>).)*?)</a>', unwrap_match, content, flags=re.DOTALL | re.IGNORECASE)

    # 4. Explicit Header Unwrap
    # Find <hX><a href="#...">Text</a></hX> and replace with <hX>Text</hX>
    def unwrap_header_link(match):
        tag = match.group(1)
        inner = match.group(2)
        return f'<{tag}>{inner}</{tag}>'
        
    content = re.sub(r'<(h[1-6])>\s*<a[^>]*href=["\']#[^"\']*["\'][^>]*>((?:(?!</a>).)*?)</a>\s*</\1>', unwrap_header_link, content, flags=re.DOTALL | re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Repaired content: {filename}")

def main():
    if not os.path.exists(TARGET_DIR):
        return

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
        # We process ALL html files in tf_inori to ensure repairs happen everywhere
        filepath = os.path.join(TARGET_DIR, filename)
        repair_file(filepath, filename)

if __name__ == "__main__":
    main()

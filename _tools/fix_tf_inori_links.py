
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def fix_content_file(filepath, filename):
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
    
    # 1. Remove self-linking anchors (anchors wrapping block elements or large text)
    # Pattern: <a href="#ID_OR_SAME">...</a> where ... is large or match ID
    
    # Strategy: Find all anchors. If they seem to be "wrappers", unwrap them.
    # We look for <a href="#..."> which contains a heading or is very long.
    
    # Regex for start tag, content, end tag.
    # Note: Regex parsing HTML is fragile, but sufficient for this specific artifact.
    # Case: <h2 id="LONG"><a href="#LONG">TEXT</a></h2> -> <h2 id="LONG">TEXT</h2>
    # Case: <a href="#LONG">TEXT...</a> where text is long.
    
    # Let's target the specific pattern seen: <a href="#...">CONTENT</a> where CONTENT has <br/> or is long.
    
    def unwrap_match(match):
        full_tag = match.group(0)
        href = match.group(1)
        inner_content = match.group(2)
        
        # Condition to unwrap:
        # 1. inner_content contains block tags
        if re.search(r'<(h[1-6]|div|p|br|table|ul|li)', inner_content, re.IGNORECASE):
            return inner_content
        # 2. inner_content is > 50 chars
        if len(inner_content) > 50:
            return inner_content
        # 3. href looks like a "self link" to a giant ID? 
        # (This is hard to verify without parsing the parent ID, but the above rules catch 90%)
        
        return full_tag

    # Regex: <a href="([^"]*)">((?:(?!</a>).)*)</a>
    # We use DOTALL to match newlines.
    content = re.sub(r'<a[^>]*href=["\'](#[^"\']*)["\'][^>]*>((?:(?!</a>).)*?)</a>', unwrap_match, content, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Cleanup giant IDs on headers
    # <h[1-6] id="...">
    def fix_header_id(match):
        tag_start = match.group(1) # e.g. h2
        id_val = match.group(2)
        remainder = match.group(3) # e.g. >
        
        if len(id_val) > 50:
            # Drop the ID
            return f'<{tag_start}{remainder}'
        return match.group(0)

    content = re.sub(r'<(h[1-6])[^>]*id=["\']([^"\']*)["\']([^>]*)>', fix_header_id, content, flags=re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed content: {filename}")

def fix_toc_file(filepath, filename):
    # Logic: replace href="#001" with href="fp{vol}_01.html"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
             with open(filepath, 'r', encoding='cp932') as f:
                content = f.read()
        except:
             return

    # Extract volume number
    # filename formats: framepage1.html, fp1_mokuji.html
    vol_match_Frame = re.search(r'framepage(\d+)\.html', filename)
    vol_match_Mokuji = re.search(r'fp(\d+)_mokuji\.html', filename)
    
    vol = None
    if vol_match_Frame:
        vol = vol_match_Frame.group(1)
    elif vol_match_Mokuji:
        vol = vol_match_Mokuji.group(1)
        
    if not vol:
        return

    original_content = content
    
    # Target: <a href="#001" ... >01 ...</a>
    # We want to change href="#001" to href="fp{vol}_01.html"
    # Be careful not to change the link to TOP or something else if it accidentally uses #001 (unlikely).
    # The pattern in the file was: <a href="#001" style="text-decoration : none;" target="right">01
    
    target_link = f'fp{vol}_01.html'
    
    # Replace href="#001" with href="fp{vol}_01.html"
    content = content.replace('href="#001"', f'href="{target_link}"')
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed TOC: {filename}")

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Dir not found: {TARGET_DIR}")
        return

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
            
        filepath = os.path.join(TARGET_DIR, filename)
        
        # Decide type
        if "mokuji" in filename or "framepage" in filename:
            fix_toc_file(filepath, filename)
        elif re.match(r'fp\d+_\d+\.html', filename):
            fix_content_file(filepath, filename)

if __name__ == "__main__":
    main()

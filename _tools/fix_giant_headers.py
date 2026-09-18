
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa/tf_inori"

def fix_file(filepath, filename):
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
    
    # Logic:
    # Find h2 blocks that are suspiciously long (> 200 chars).
    # Inside them, find the "Title" part.
    # The Title part ends at the first <br>, <hr>, or maybe <p>.
    # We want to change:
    # <h2 attrs>Title<br>Body...</h2>
    # to:
    # <h2 attrs>Title</h2><br>Body...
    
    # Regex Explanation:
    # <(h[1-6])([^>]*)>           : Start tag (Group 1: tag name, Group 2: attributes)
    # (.*?)                       : Title content (Group 3) - Non-greedy, stops at first terminator
    # (<br|<hr|<p|<div>|\n)       : Terminator (Group 4) - What indicates end of title
    # ((?:(?!</\1>).)*)           : The Body content (Group 5) - Everything else until closing tag
    # </\1>                       : Closing tag
    
    # Note: re.DOTALL is critical.
    
    def replacer(match):
        tag = match.group(1)
        attrs = match.group(2)
        title = match.group(3)
        terminator = match.group(4)
        body = match.group(5)
        
        # Safety check: if body is too short, maybe it's just a complex title?
        # But here we are targeting giant headers.
        full_content_len = len(title) + len(terminator) + len(body)
        if full_content_len < 100:
            return match.group(0) # Skip short headers
            
        return f'<{tag}{attrs}>{title}</{tag}>{terminator}{body}'
        
    pattern = r'<(h[1-6])([^>]*)>(.*?)(<br|<hr|<p|<div>|\r?\n)((?:(?!</\1>).)*)</\1>'
    
    # We run this replacement.
    # Note: Regex might be tricky with nested tags, but these files generally have simple structure.
    # The 'body' part ((?:(?!</\1>).)*) ensures we stop at the matching closing tag.
    
    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL | re.IGNORECASE)

    if new_content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed giant header in: {filename}")

def main():
    if not os.path.exists(TARGET_DIR):
        return

    for filename in os.listdir(TARGET_DIR):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join(TARGET_DIR, filename)
        fix_file(filepath, filename)

if __name__ == "__main__":
    main()

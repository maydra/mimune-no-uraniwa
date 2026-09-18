
import os
import re

TARGET_DIR = "C:/Users/dream/OneDrive/デスクトップ/Meiryu/mimune-no-uraniwa"
EXCLUDE_DIRS = ["dp", "Bible", "Bible_out", "tools", ".git", ".gemini", "node_modules", ".agent"]

# Colors to replace with white
BLACK_PATTERNS = [
    r'color\s*:\s*#000000',
    r'color\s*:\s*black',
    r'color\s*:\s*purple',
    r'text\s*=\s*["\']#000000["\']',
    r'text\s*=\s*["\']black["\']'
]

def should_process(filepath):
    # Check exclusions
    rel_path = os.path.relpath(filepath, TARGET_DIR)
    parts = rel_path.split(os.sep)
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    
    # Check if file has already acted as "modern" (white background)
    # We'll peek at the file content for "background: #ffffff" or similar
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if "background: #ffffff" in content or "background: white" in content:
                # But wait, we might have inline styles overriding this.
                # Use caution. If it's a file we JUST updated (like family_pledge), skip.
                if "family_pledge.html" in filepath or "seikon_mondou.html" in filepath:
                    return False
    except:
        pass
        
    return True

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
             with open(filepath, 'r', encoding='cp932') as f:
                content = f.read()
        except:
            print(f"Failed to read {filepath}")
            return

    original_content = content
    
    # 1. Clean <body> attributes
    # Remove text, link, vlink, alink attributes which might force colors
    content = re.sub(r'(<body[^>]*?)\s+(text|link|vlink|alink)=["\'][^"\']*["\']', r'\1', content, flags=re.IGNORECASE)
    
    # 2. Fix <font color="...">
    # Replace black/purple with white
    content = re.sub(r'(<font[^>]*?)color=["\'](black|#000000|purple)["\']', r'\1color="white"', content, flags=re.IGNORECASE)
    
    # 3. Fix inline styles
    content = re.sub(r'color\s*:\s*(#000000|black|purple)', 'color: #ffffff', content, flags=re.IGNORECASE)
    
    # 4. Fix specific case seen in heiwa_miti: <a ... style="color : #000000; ...">
    # The regex above handles basic cases, but let's handle spaces/casing better
    # Also handle 'text-decoration' if needed, but color is the main one.
    
    # 5. Ensure body has white text color if it doesn't have a class or style
    # If standard legacy body tag, add/merge style
    if "<body" in content:
        if "style=" in content:
            # If body has style, append color: #e0e0e0 if not present (simple hack)
            pass 
        else:
            # Inject style
            content = content.replace("<body>", '<body style="color: #e0e0e0;">')

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"Directory not found: {TARGET_DIR}")
        return

    for root, dirs, files in os.walk(TARGET_DIR):
        # Filter directories in place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for filename in files:
            if filename.endswith(".html"):
                filepath = os.path.join(root, filename)
                if should_process(filepath):
                    fix_file(filepath)

if __name__ == "__main__":
    main()

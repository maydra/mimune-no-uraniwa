import os
import re

TAG = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXQ0QTBYTR"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXQ0QTBYTR');
</script>
"""

def add_tag_to_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping {file_path} (could not decode with utf-8)")
        return

    if 'G-XXQ0QTBYTR' in content:
        # print(f"Skipping {file_path} (tag already exists)")
        return

    # Find the <head> tag
    # Use regex to find <head> or <head ...>
    head_match = re.search(r'<head(\s.*?)?>', content, re.IGNORECASE)
    if head_match:
        insert_pos = head_match.end()
        # Ensure we don't insert it multiple times if for some reason the config ID wasn't found but the tag was
        if 'www.googletagmanager.com/gtag/js' in content:
             print(f"Skipping {file_path} (another gtag found or partial tag exists)")
             return
             
        new_content = content[:insert_pos] + TAG + content[insert_pos:]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Added tag to {file_path}")
    else:
        # print(f"Warning: No <head> tag found in {file_path}")
        pass

def main():
    # Use the root of the project
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f"Searching in: {root_dir}")
    count = 0
    for root, dirs, files in os.walk(root_dir):
        # Exclude directories
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if 'pagefind' in dirs:
            dirs.remove('pagefind')
        if '.github' in dirs:
            dirs.remove('.github')

        for file in files:
            if file.endswith('.html'):
                # Verification file
                if file.startswith('google') and file.endswith('.html') and len(file) > 15:
                    continue
                file_path = os.path.join(root, file)
                add_tag_to_file(file_path)
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} files...")

if __name__ == "__main__":
    main()

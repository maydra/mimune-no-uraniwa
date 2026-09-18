import json
import os
import re
import html

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = text.replace('\n', ' ').replace('\r', ' ').strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def apply_fixes():
    base_path = r'C:\malsum\mimune-no-uraniwa'
    with open('audit_results.json', 'r', encoding='utf-8') as f:
        all_results = json.load(f)
        
    total_replaced = 0
    dirs_affected = 0
    
    for subdir, updates in all_results.items():
        index_path = os.path.join(base_path, subdir, 'index.html')
        if not os.path.exists(index_path):
            continue
            
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            print(f"Error reading {index_path}")
            continue
            
        new_content = content
        replaced_count = 0
        
        # Sort updates to process longer texts first? 
        # Actually, we should replace each link individually.
        
        # We find all <a> tags
        a_tag_pattern = re.compile(r'(<a\s+[^>]*href=(["\'])([^"\'\s>]+)(["\'])[^>]*>(.*?)</a>)', re.DOTALL | re.IGNORECASE)
        
        def replace_link(match):
            nonlocal replaced_count
            full_tag = match.group(1)
            quote1 = match.group(2)
            href = match.group(3)
            quote2 = match.group(4)
            link_html = match.group(5)
            
            link_text = clean_text(link_html)
            
            # Find a matching update
            for up in updates:
                if up['old'] == href and up['text'] == link_text:
                    # Found match!
                    new_href = up['new']
                    if new_href == href: return full_tag
                    
                    # Reconstruct tag
                    # Replace href="old" with href="new"
                    old_href_attr = f'href={quote1}{href}{quote2}'
                    new_href_attr = f'href={quote1}{new_href}{quote2}'
                    new_tag = full_tag.replace(old_href_attr, new_href_attr)
                    replaced_count += 1
                    return new_tag
            
            return full_tag

        new_content = a_tag_pattern.sub(replace_link, content)
        
        if replaced_count > 0:
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                total_replaced += replaced_count
                dirs_affected += 1
                print(f"Updated {subdir}: {replaced_count} links fixed.")
            except Exception as e:
                print(f"Error writing to {index_path}: {e}")
                
    print(f"\nSummary: Fixed {total_replaced} links across {dirs_affected} directories.")

if __name__ == "__main__":
    apply_fixes()

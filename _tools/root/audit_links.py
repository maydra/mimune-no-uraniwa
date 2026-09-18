import os
import re
import json

def get_text_clean(text):
    # Remove HTML tags and normalize whitespace
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', '', text)

def audit_directory(base_path, subdir):
    index_path = os.path.join(base_path, subdir, 'index.html')
    if not os.path.exists(index_path):
        return []

    print(f"Auditing {subdir}...")
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
    except Exception as e:
        print(f"Error reading {index_path}: {e}")
        return []

    errors = []
    # Find all <a> tags with href
    links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', index_content, re.DOTALL)
    
    for href, link_html in links:
        if href.startswith('http') or href.startswith('/') or href.startswith('#'):
            continue
        
        parts = href.split('#')
        target_file = parts[0]
        anchor = parts[1] if len(parts) > 1 else None
        
        target_path = os.path.join(base_path, subdir, target_file)
        if not os.path.exists(target_path):
            continue
            
        link_text = get_text_clean(link_html)
        if not link_text:
            continue

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                target_content = f.read()
        except Exception as e:
            print(f"Error reading {target_path}: {e}")
            continue

        if anchor:
            # Look for id="anchor" or name="anchor"
            # Pattern: id=["']anchor["']
            id_pattern = rf'id=["\']{re.escape(anchor)}["\']'
            name_pattern = rf'name=["\']{re.escape(anchor)}["\']'
            
            if not re.search(id_pattern, target_content) and not re.search(name_pattern, target_content):
                errors.append({
                    "subdir": subdir,
                    "href": href,
                    "link_text": link_text,
                    "issue": "Anchor not found"
                })
            else:
                # Find the element with this ID and check text
                # This is hard with regex, but we can try to find the tag containing the ID
                # and check nearby text.
                # simpler: find all IDs in target file and their associated text
                pass
        else:
            # No anchor
            pass

    # Systematic check for syougairotei style mismatch (sequential IDs)
    if subdir.startswith('syougairotei_'):
        # For these, we expect the N-th link to target the N-th (or offset) ID
        # But specifically, let's just check if the text matches.
        pass

    return errors

def main():
    base_path = r'C:\malsum\mimune-no-uraniwa'
    # Use lowercase for consistency in exclusion check
    exclude_dirs = {
        'dp', 'bible_out', 'syuku_&_risoutengoku', '.git', '.audit', '__pycache__', 
        'theme', 'data', 'malsum', 'library', 'preview', 'tools', 'pagefind'
    }
    
    all_errors = []
    subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    
    for d in subdirs:
        if d.lower() in exclude_dirs:
            continue
        errors = audit_directory(base_path, d)
        all_errors.extend(errors)
            
    with open(os.path.join(base_path, 'audit_results.json'), 'w', encoding='utf-8') as f:
        json.dump(all_errors, f, ensure_ascii=False, indent=2)
    
    print(f"Audit complete. Found {len(all_errors)} issues.")

if __name__ == "__main__":
    main()

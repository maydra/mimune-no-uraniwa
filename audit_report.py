import os
import re
import html
import json
import sys

# Ensure stdout is utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text) # Remove HTML tags
    text = html.unescape(text) # Unescape entities
    text = text.replace('\u3000', ' ') # Replace ideographic space
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_for_match(text):
    # Remove all whitespace for robust comparison
    return re.sub(r'\s+', '', text)

def find_id_for_text(target_html, search_text, cache_ids):
    if not search_text: return None
    
    if target_html not in cache_ids:
        ids = {}
        # Tags with ID
        tag_pattern = re.compile(rf'<([a-z0-9]+)\s+[^>]*id=["\']([^"\'\s>]+)["\'][^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
        for tag, tag_id, tag_html in tag_pattern.findall(target_html):
            if tag_id.lower() == 'toc': continue
            txt = clean_text(tag_html)
            if txt and tag_id not in ids:
                ids[tag_id] = txt
        
        # <a> tags with name
        a_name_pattern = re.compile(rf'<a\s+[^>]*name=["\']([^"\'\s>]+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        for tag_id, tag_html in a_name_pattern.findall(target_html):
            txt = clean_text(tag_html)
            if txt and tag_id not in ids:
                ids[tag_id] = txt
                
        cache_ids[target_html] = ids
    
    ids = cache_ids[target_html]
    search_norm = normalize_for_match(search_text)
    
    # 1. Exact Normal Match (ignoring spaces)
    for tag_id, txt in ids.items():
        if search_norm == normalize_for_match(txt):
            return tag_id
            
    # 2. Case-Insensitive Normal Match
    search_lower = search_norm.lower()
    for tag_id, txt in ids.items():
        if search_lower == normalize_for_match(txt).lower():
            return tag_id
            
    # 3. Partial Match
    best_partial = None
    min_len_diff = 999999
    for tag_id, txt in ids.items():
        txt_norm = normalize_for_match(txt)
        if search_norm in txt_norm or txt_norm in search_norm:
            diff = abs(len(txt_norm) - len(search_norm))
            if diff < min_len_diff:
                min_len_diff = diff
                best_partial = tag_id
                
    if min_len_diff < 30:
        return best_partial
        
    return None

FILE_CACHE = {}

def process_directory(base_path, subdir):
    index_path = os.path.join(base_path, subdir, 'index.html')
    if not os.path.exists(index_path):
        return []

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return []

    links = re.findall(r'(<a\s+[^>]*href=["\']([^"\'\s>]+)["\'][^>]*>(.*?)</a>)', content, re.DOTALL | re.IGNORECASE)
    
    updates = []
    id_cache = {}
    
    for full_tag, href, link_html in links:
        if href.startswith('http') or href.startswith('/') or href.startswith('javascript') or href.startswith('mailto:'):
            continue
            
        parts = href.split('#')
        target_file = parts[0]
        old_anchor = parts[1] if len(parts) > 1 else None
        
        if not target_file: target_file = 'index.html'
        if not target_file.endswith('.html'): continue
            
        target_path = os.path.join(base_path, subdir, target_file)
        if not os.path.exists(target_path): continue
            
        link_text = clean_text(link_html)
        if not link_text: continue
        
        if target_path not in FILE_CACHE:
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    FILE_CACHE[target_path] = f.read()
            except: continue
        
        target_html = FILE_CACHE[target_path]
        found_id = find_id_for_text(target_html, link_text, id_cache)
        
        if found_id:
            new_href = f"{target_file}#{found_id}"
            if new_href != href:
                updates.append({
                    "old": href,
                    "new": new_href,
                    "text": link_text
                })
            
    return updates

def main():
    base_path = r'C:\malsum\mimune-no-uraniwa'
    exclude_dirs = ['Dp', 'Bible', 'theme', '.git', '.github', '.agent']
    all_results = {}
    dirs = sorted([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and d not in exclude_dirs])
    
    for subdir in dirs:
        results = process_directory(base_path, subdir)
        if results:
            all_results[subdir] = results
            
    with open('audit_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Audit complete. Found potential updates in {len(all_results)} directories.")

if __name__ == "__main__":
    main()

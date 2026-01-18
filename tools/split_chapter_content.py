import os
from bs4 import BeautifulSoup
import re
import shutil
import copy

# Configuration
BASE_DIR = r"C:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\syougairotei_11"
TARGET_FILES = ["chapter001.html", "chapter002.html", "chapter003.html"]

def normalize_soup(content_div):
    """
    Normalizes HTML structure to ensure H2 tags are top-level children of content_div.
    """
    # 1. Unwrap nested H2 tags
    dirty = True
    while dirty:
        dirty = False
        for h2 in content_div.find_all('h2'):
            if h2.parent and h2.parent.name == 'h2':
                h2.parent.unwrap()
                dirty = True
                break

    # 2. Move H2 tags out of P tags
    for h2 in content_div.find_all('h2'):
        if h2.parent and h2.parent.name == 'p':
            p_tag = h2.parent
            h2.extract()
            p_tag.insert_after(h2)

    # 3. Handle H2 nested in 'a' tags
    for h2 in content_div.find_all('h2'):
        if h2.parent and h2.parent.name == 'a':
            a_tag = h2.parent
            h2.extract()
            a_tag.insert_after(h2)

def process_chapter(filename):
    filepath = os.path.join(BASE_DIR, filename)
    backup_path = filepath + ".bak"
    
    # Ensure backup exists and use it as source
    if not os.path.exists(backup_path):
        if os.path.exists(filepath):
            shutil.copy2(filepath, backup_path)
            source_file = backup_path
        else:
            print(f"File not found: {filepath}")
            return None
    else:
        source_file = backup_path

    print(f"Processing {filename} (source: {os.path.basename(source_file)})...")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Extract common parts
    head_content = soup.head
    body_attrs = soup.body.attrs if soup.body else {}
    
    # Extract Chapter Title (H1)
    chapter_title = "Unknown Chapter"
    h1 = soup.find('h1')
    if h1:
        chapter_title = h1.get_text(strip=True)
    elif soup.title:
        chapter_title = soup.title.get_text(strip=True)
    
    # Determine content container
    content_div = soup.find('div', class_='content')
    if not content_div:
         content_div = soup.find('div', class_='container')

    if not content_div:
        if soup.body:
            content_div = soup.body
        else:
            print("  Error: No body tag found.")
            return None

    # Normalize
    normalize_soup(content_div)

    # Try to extract section order from TOC if it exists
    toc_div = soup.find('div', class_='toc') or soup.find('div', id='toc')
    section_titles_ordered = []
    
    if toc_div:
        # Extract section titles from TOC links
        toc_links = toc_div.find_all('a')
        seen_toc_titles = set()
        for link in toc_links:
            title = link.get_text(strip=True)
            if title and title != "目次" and title not in seen_toc_titles:
                section_titles_ordered.append(title)
                seen_toc_titles.add(title)
        print(f"  Found {len(section_titles_ordered)} unique sections in TOC.")
    
    # Find all H2 tags
    h2_tags = content_div.find_all('h2', recursive=False)
    if len(h2_tags) < 3:
        h2_tags = content_div.find_all('h2')
    
    # Remove TOC heading from h2_tags
    h2_tags = [h2 for h2 in h2_tags if h2.get_text(strip=True) != "目次"]
    
    print(f"  Found {len(h2_tags)} content H2 tags.")

    # Build a map of title -> h2 tag
    h2_map = {}
    for h2 in h2_tags:
        title = h2.get_text(strip=True)
        if title not in h2_map:  # Only keep first occurrence
            h2_map[title] = h2
    
    # If we have a TOC, use its order; otherwise use h2_tags order
    if section_titles_ordered:
        ordered_h2s = []
        for title in section_titles_ordered:
            if title in h2_map:
                ordered_h2s.append(h2_map[title])
            else:
                print(f"  Warning: TOC section '{title}' not found in content")
        h2_tags_to_process = ordered_h2s
    else:
        h2_tags_to_process = list(h2_map.values())

    sections = []
    for i, h2 in enumerate(h2_tags_to_process):
        section_title = h2.get_text(strip=True)
        section_id = h2.get('id')
        if not section_id:
            prev = h2.previous_sibling
            if prev and prev.name == 'a' and prev.get('id'):
                section_id = prev.get('id')
            else:
                section_id = f"section{i+1}"
            h2['id'] = section_id
        
        content_nodes = []
        curr = h2.next_sibling
        while curr:
            if curr in h2_tags:
                break
            content_nodes.append(curr)
            curr = curr.next_sibling
            
        sections.append({
            'id': section_id,
            'title': section_title,
            'h2_tag': h2,
            'content': content_nodes
        })

    # Generate Sub-pages
    base_name = os.path.splitext(filename)[0]
    generated_links = []

    for i, section in enumerate(sections):
        file_suffix = f"section{i+1}"
        sub_filename = f"{base_name}_{file_suffix}.html"
        sub_filepath = os.path.join(BASE_DIR, sub_filename)
        
        new_soup = BeautifulSoup("<!DOCTYPE html><html lang='ja'></html>", 'html.parser')
        if head_content:
            new_soup.html.append(copy.copy(head_content))
        
        new_body = new_soup.new_tag('body', **body_attrs)
        new_soup.html.append(new_body)
        
        new_container = new_soup.new_tag('div', attrs={'class': 'container'})
        new_body.append(new_container)

        # Nav Back (to index.html)
        nav_div = new_soup.new_tag('div', style="margin-bottom: 20px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px;")
        back_link = new_soup.new_tag('a', href="index.html")
        back_link.string = "← 目次に戻る"
        nav_div.append(back_link)
        
        # Prev
        if i > 0:
            prev_suffix = f"section{i}"
            prev_filename = f"{base_name}_{prev_suffix}.html"
            prev_link = new_soup.new_tag('a', href=prev_filename, style="margin-left: 20px;")
            prev_link.string = "前へ"
            nav_div.append(prev_link)
        
        # Next
        if i < len(sections) - 1:
            next_suffix = f"section{i+2}"
            next_filename = f"{base_name}_{next_suffix}.html"
            next_link = new_soup.new_tag('a', href=next_filename, style="margin-left: 20px;")
            next_link.string = "次へ"
            nav_div.append(next_link)
            
        new_container.append(nav_div)
        
        new_content_div = new_soup.new_tag('div', attrs={'class': 'content'})
        new_container.append(new_content_div)
        
        new_content_div.append(copy.copy(section['h2_tag']))
        for node in section['content']:
            new_content_div.append(copy.copy(node))
            
        new_container.append(copy.copy(nav_div))
            
        with open(sub_filepath, 'w', encoding='utf-8') as f_out:
            f_out.write(str(new_soup))
            
        generated_links.append({
            'href': sub_filename,
            'title': section['title']
        })
        try:
            print(f"Created {sub_filename}")
        except:
            pass

    return {
        'title': chapter_title,
        'links': generated_links,
        'head': head_content, # Return head to use for master index
        'body_attrs': body_attrs
    }

def main():
    master_toc_data = []
    sample_head = None
    sample_body_attrs = {}

    for fname in TARGET_FILES:
        try:
            data = process_chapter(fname)
            if data:
                master_toc_data.append(data)
                if not sample_head:
                    sample_head = data['head']
                    sample_body_attrs = data['body_attrs']
                
                # Delete original file (since it's replaced by index and subpages, and we have backup)
                # But wait, we should only delete if we successfully processed.
                # And we rely on backup.
                full_path = os.path.join(BASE_DIR, fname)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Removed {fname}")

        except Exception as e:
            print(f"Failed to process {fname}: {e}")

    # Generate Unified Index
    if master_toc_data:
        index_filepath = os.path.join(BASE_DIR, "index.html")
        index_soup = BeautifulSoup("<!DOCTYPE html><html lang='ja'></html>", 'html.parser')
        
        if sample_head:
            index_soup.html.append(copy.copy(sample_head))
        
        index_body = index_soup.new_tag('body', **sample_body_attrs)
        index_soup.html.append(index_body)
        
        index_container = index_soup.new_tag('div', attrs={'class': 'container'})
        index_body.append(index_container)

        # Main Title
        h1 = index_soup.new_tag('h1')
        h1.string = "御父母様の生涯路程 (11)"
        index_container.append(h1)

        toc_div = index_soup.new_tag('div', attrs={'class': 'toc', 'id': 'toc'})
        # toc_h2 = index_soup.new_tag('h2')
        # toc_h2.string = "目次"
        # toc_div.append(toc_h2)
        
        for chapter in master_toc_data:
            # Chapter Section
            chap_h2 = index_soup.new_tag('h2')
            chap_h2.string = chapter['title']
            toc_div.append(chap_h2)
            
            ul = index_soup.new_tag('ul', attrs={'class': 'links-list'})
            for link_info in chapter['links']:
                li = index_soup.new_tag('li')
                a = index_soup.new_tag('a', href=link_info['href'])
                a.string = link_info['title']
                li.append(a)
                ul.append(li)
            toc_div.append(ul)
            
        index_container.append(toc_div)
        
        with open(index_filepath, 'w', encoding='utf-8') as f:
            f.write(str(index_soup))
        print(f"Created Master Index: index.html")

if __name__ == "__main__":
    main()

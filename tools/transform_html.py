import argparse
import os
import re
from bs4 import BeautifulSoup
import sys

def slugify(text):
    # Retrieve non-ASCII characters and replace spaces with hyphens
    # Simple slugify for Japanese/English
    text = text.strip()
    text = re.sub(r'\s+', '-', text)
    # Remove some special chars if needed, but keep Japanese
    return text

def transform_file(filepath, dry_run=False, output_dir=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    modified = False

    # 1. Remove Existing TOCs (Cleanup Phase)
    # Heuristic: Find existing "toc" container by class or ID
    old_tocs = soup.find_all(class_=re.compile(r'\btoc\b', re.IGNORECASE))
    for old_toc in old_tocs:
        old_toc.decompose()
        modified = True
    
    old_toc_id = soup.find(id="toc")
    if old_toc_id:
        old_toc_id.decompose()
        modified = True

    # Heuristic: Remove TOC based on "目次" or "Table of Contents" heading
    # We look for such headings and remove their container if it looks like a TOC
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = h.get_text().strip()
        if text == "目次" or text.lower() == "table of contents":
            # Check if parent is a container (nav, div, section)
            parent = h.find_parent(['nav', 'div', 'section'])
            if parent and parent.name != 'body':
                parent.decompose()
                modified = True
            else:
                # If no clear wrapper, remove the heading and any immediately following list
                curr = h
                next_sib = h.find_next_sibling()
                h.decompose()
                if next_sib and next_sib.name in ['ul', 'ol']:
                    next_sib.decompose()
                modified = True

    # 2. Process Headings & Generate IDs
    # Find all potential headings including "legacy" bold tags
    all_candidates = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b'])
    
    # Collect all currently used IDs to avoid collisions
    existing_ids = set(tag['id'] for tag in soup.find_all(id=True))
    
    toc_items = []
    id_counter = 1
    
    for element in all_candidates:
        # Filter logic
        is_heading_tag = element.name.startswith('h')
        is_legacy = False
        
        if element.name == 'b':
            # 1. Must not be inside a heading or link (navigation)
            if element.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']):
                continue
                
            # 2. Heuristic: Check surroundings for <br>
            # We check previous/next siblings, skipping empty strings
            
            # Scan backwards
            prev_node = element.previous_sibling
            while isinstance(prev_node, str) and not prev_node.strip():
                prev_node = prev_node.previous_sibling
            
            # Scan forwards
            next_node = element.next_sibling
            while isinstance(next_node, str) and not next_node.strip():
                next_node = next_node.next_sibling
                
            has_prev_br = (prev_node is None or prev_node.name == 'br')
            has_next_br = (next_node is None or next_node.name == 'br')
            
            # Only treat as heading if text is not empty
            text_content = element.get_text().strip()
            if not text_content:
                continue

            # User said: "preceded AND/OR followed by <br>"
            if has_prev_br or has_next_br:
                is_legacy = True
            else:
                continue

        # Processing ID
        if element.has_attr('id'):
            h_id = element['id']
        else:
            # Generate Sequential ID: 001, 002...
            while True:
                candidate = f"{id_counter:03d}"
                if candidate not in existing_ids:
                    h_id = candidate
                    existing_ids.add(h_id)
                    id_counter += 1
                    break
                id_counter += 1
        
        if element.get('id') != h_id:
            element['id'] = h_id
            modified = True

        # Self-Link Logic
        if not element.find('a', recursive=False):
            new_a = soup.new_tag('a', href=f"#{h_id}")
            # Move children
            contents = list(element.contents)
            element.clear()
            for child in contents:
                new_a.append(child)
            element.append(new_a)
            modified = True
        else:
            a_tag = element.find('a', recursive=False)
            if a_tag and a_tag.get('href') != f"#{h_id}":
                a_tag['href'] = f"#{h_id}"
                modified = True

        # Add to TOC
        text_clean = element.get_text().strip()
        if text_clean == "目次" or text_clean.lower() == "table of contents":
            continue
            
        if is_heading_tag:
            if element.name == 'h1': continue
            level = element.name # h2, h3...
            toc_class = f"toc-level-{level[1]}"
        else:
            level = 'b'
            toc_class = "toc-b"
            
        toc_items.append({'id': h_id, 'text': text_clean, 'class': toc_class})

    # 3. Insert New TOC
    if toc_items:
        # Check exclusion logic
        filename = os.path.basename(filepath).lower()
        h1_text = ""
        first_h1 = soup.find('h1')
        if first_h1:
            h1_text = first_h1.get_text().lower()
        
        is_family_pledge = (
            "familypledge" in filename 
            or "family_pledge" in filename 
            or "family pledge" in h1_text
        )
        
        path_parts = os.path.normpath(filepath).split(os.sep)
        is_excluded_folder = 'dp' in path_parts or 'tf_inori' in path_parts

        if not is_family_pledge and not is_excluded_folder:
            # Create TOC structure
            toc_div = soup.new_tag('div', id="toc", **{'class': 'toc'})
            toc_div.append(soup.new_tag('h2'))
            toc_div.h2.string = "目次"
            ul = soup.new_tag('ul')
            for item in toc_items:
                li = soup.new_tag('li')
                li['class'] = item['class']
                a = soup.new_tag('a', href=f"#{item['id']}")
                a.string = item['text']
                li.append(a)
                ul.append(li)
            toc_div.append(ul)

            # Insert: After H1, or at top of body
            if first_h1:
                first_h1.insert_after(toc_div)
            else:
                if soup.body:
                    soup.body.insert(0, toc_div)
            modified = True

    if modified:
        if dry_run:
            # print(f"[Dry-Run] Would modify: {filepath}")
            return 
        
        output_path = filepath
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(output_dir, os.path.basename(filepath))
            print(f"[Preview] Writing to: {output_path}")
        else:
            print(f"[Apply] Updating: {filepath}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

def main():
    parser = argparse.ArgumentParser(description="Transform HTML files: enhance headings and TOC.")
    parser.add_argument('files', nargs='*', help='Specific files to process (overrides scanning)')
    parser.add_argument('--root', default='.', help='Root directory to scan if no files provided')
    parser.add_argument('--dry-run', action='store_true', help='Do not write changes')
    parser.add_argument('--apply', action='store_true', help='Write changes to files')
    parser.add_argument('--only', help='Process only this single file path')
    parser.add_argument('--output-dir', help='Write output files to this directory instead of overwriting')
    parser.add_argument('--limit', type=int, help='Limit the number of files processed (for scanning)')

    args = parser.parse_args()

    targets = []
    if args.only:
        targets.append(args.only)
    elif args.files:
        targets = args.files
    else:
        # Scan dir
        count = 0
        for root, dirs, files in os.walk(args.root):
            for file in files:
                if file.endswith(".html"):
                    targets.append(os.path.join(root, file))
                    count += 1
                    if args.limit and count >= args.limit:
                        break
            if args.limit and count >= args.limit:
                break

    print(f"Found {len(targets)} targets.")

    for target in targets:
        try:
            transform_file(target, dry_run=args.dry_run, output_dir=args.output_dir)
        except Exception as e:
            print(f"Error processing {target}: {e}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))

if __name__ == "__main__":
    main()

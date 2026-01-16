import os
import json
import re
import hashlib
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://maydra.github.io/mimune-no-uraniwa/"
ROOT_DIR = "."
DATA_DIR = "data"
PARAGRAPHS_FILE = "paragraphs.json"
PAGE_MAP_FILE = "page-paragraphs.json"

# Files/Dirs to ignore
IGNORE_DIRS = {
    ".git", ".github", ".vscode", "data", "images", "css", "js", "pdf", "zip", 
    "pagefind", "brain"
}
IGNORE_EXTENSIONS = {
    ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", 
    ".xml", ".txt", ".py", ".md"
}
IGNORE_FILES = {
    "search.html", "google4950bff256850b5a.html"
}

def clean_text(text):
    """Normalize whitespace and remove zero-width characters."""
    return re.sub(r'\s+', ' ', text).strip()

def get_paragraphs(soup):
    """
    Extract paragraphs/blocks from content.
    Returns a list of strings.
    """
    # Remove unwanted elements
    for selector in ["nav", "header", "footer", "aside", ".toc", ".sidebar", "script", "style", "noscript", "iframe"]:
        for tag in soup.select(selector):
            tag.decompose()

    content_root = None
    
    # Priority list
    if soup.find("main"):
        content_root = soup.find("main")
    elif soup.find("article"):
        content_root = soup.find("article")
    elif soup.select_one("#content"):
        content_root = soup.select_one("#content")
    elif soup.select_one(".content"):
        content_root = soup.select_one(".content")
    else:
        content_root = soup.body

    if not content_root:
        return []

    # Strategy: Find all meaningful block tags and extract their text.
    # We want to merge inline tags (span, a, b) into the text, 
    # but keep separate blocks separate.
    
    target_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre', 'dt', 'dd', 'div']
    
    # Pruning strategy:
    # If we select 'div', we might get nested 'p'.
    # We should iterate and pick the "most specific" blocks?
    # Or just iterate all descendants and if it's a target tag AND doesn't contain other target tags?
    
    blocks = []
    
    # Simple pass: find all 'p', 'h1-6', 'li', 'blockquote', 'pre', 'dt', 'dd'.
    # These are usually leaf-ish blocks.
    # 'div' is risky.
    
    primary_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre', 'dt', 'dd']
    
    found_blocks = content_root.find_all(primary_tags)
    
    # If we found almost nothing, maybe the site uses divs for text?
    if len(found_blocks) < 3: 
        # Fallback: Treat divs as paragraphs if they contain text directly?
        # Or just use the get_text() method on the root but with better separator?
        pass # Stick to primary for now, if empty, we might miss content but cleaner.
        
    if not found_blocks:
        # Fallback to simple line split if no structure
        raw_text = content_root.get_text(separator='\n')
        return [clean_text(line) for line in raw_text.split('\n') if len(clean_text(line)) > 1]
        
    for tag in found_blocks:
        # Check if this block is inside another block we already processed?
        # find_all returns in document order.
        # It yields parents then children? No.
        # BS4 find_all: "depth-first"?
        # Actually, if we have <ul><li>...</li></ul>, find_all(['ul', 'li']) returns both.
        # We only included 'li', not 'ul', so that avoids duplication there.
        # Nested lists? <li>text <ul><li>sub</li></ul></li>
        # The parent <li> text will include the child <li> text? Yes: tag.get_text() includes children.
        
        # To avoid duplication in nested structures (like lists inside lists):
        # We can strip the children text that are also blocks?
        # Or just accept it.
        # For simplicity and robustness, getting the text of the leaf blocks is best.
        
        # Check if tag has block children
        has_block_children = tag.find(primary_tags)
        if has_block_children:
            # Skip this tag, let the children be picked up
            # Exception: if it has direct text nodes?
            # "Text <div>child</div>"
            # This is hard.
            # Let's assume most text is in the leaves.
            continue
            
        text = clean_text(tag.get_text(separator=' ', strip=True))
        if len(text) > 1:
            blocks.append(text)
            
    return blocks

def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16] # 16 chars is enough entropy

def build_index():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    paragraph_registry = {} # hash -> text
    page_registry = [] # List of page objects
    
    # Since we want deterministic IDs for paragraphs to save space (p0, p1...),
    # we can map hash -> ID.
    # However, user asked for "data/paragraphs.json" = { "id": "text" }
    
    unique_paragraphs = {} # hash -> id
    next_pid = 0
    
    results_paragraphs = {} # id -> text

    print(f"Scanning directory: {os.path.abspath(ROOT_DIR)}")

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            _, ext = os.path.splitext(file)
            if ext.lower() not in [".html", ".htm"]:
                continue
            
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            soup = BeautifulSoup(content, "html.parser")
            
            # Metadata
            title = soup.title.string if soup.title else file
            title = clean_text(str(title))
            
            # Extract content blocks
            paragraphs = get_paragraphs(soup)
            
            if not paragraphs:
                continue

            page_pids = []
            
            for p_text in paragraphs:
                p_hash = hash_text(p_text)
                
                if p_hash not in unique_paragraphs:
                    # New paragraph
                    pid = f"p{next_pid:x}" # Hex ID
                    next_pid += 1
                    
                    unique_paragraphs[p_hash] = pid
                    results_paragraphs[pid] = p_text
                
                page_pids.append(unique_paragraphs[p_hash])

            # URL
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            url_path = rel_path.replace(os.sep, "/")
            full_url = BASE_URL + url_path

            page_registry.append({
                "url": full_url,
                "title": title,
                "pids": page_pids
            })

    # Write Paragraphs Registry
    p_path = os.path.join(DATA_DIR, PARAGRAPHS_FILE)
    with open(p_path, "w", encoding="utf-8") as f:
        json.dump(results_paragraphs, f, ensure_ascii=False, separators=(',', ':'))
        
    # Write Page Map
    pm_path = os.path.join(DATA_DIR, PAGE_MAP_FILE)
    with open(pm_path, "w", encoding="utf-8") as f:
        json.dump(page_registry, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Index generated.")
    print(f"Total Unique Paragraphs: {len(results_paragraphs)}")
    print(f"Total Pages: {len(page_registry)}")
    print(f"Paragraphs DB: {p_path}")
    print(f"Page Map DB: {pm_path}")

if __name__ == "__main__":
    build_index()

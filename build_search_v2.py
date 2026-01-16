import os
import json
import re
import hashlib
from bs4 import BeautifulSoup
import collections

# Configuration
BASE_URL = "https://maydra.github.io/mimune-no-uraniwa/"
ROOT_DIR = "."
DATA_DIR = "data"
BOOKS_FILE = "books.json"
BOOK_TERMS_DIR = os.path.join(DATA_DIR, "book-terms")
BOOKS_DATA_DIR = os.path.join(DATA_DIR, "books")

# Files/Dirs to ignore
IGNORE_DIRS = {
    ".git", ".github", ".vscode", "data", "images", "css", "js", "pdf", "zip", 
    "pagefind", "brain", "_includes", "_layouts", "_site"
}
IGNORE_EXTENSIONS = {
    ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", 
    ".xml", ".txt", ".py", ".md"
}
IGNORE_FILES = {
    "search.html", "google4950bff256850b5a.html", "404.html"
}

def clean_text(text):
    """Normalize whitespace and remove zero-width characters."""
    return re.sub(r'\s+', ' ', text).strip()

def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

def extract_terms(text):
    """
    Extract meaningful terms for global search.
    Rules:
    - Kanji: 2-8 chars
    - Katakana: 3-12 chars
    - Alnum: 3-20 chars
    """
    terms = set()
    
    # Text is already Ruby-stripped and normalized
    
    # Kanji sequences (Unicode range 4E00-9FAF)
    kanji_matches = re.findall(r'[\u4e00-\u9faf]{2,8}', text)
    terms.update(kanji_matches)
    
    # Katakana sequences (Unicode range 30A0-30FF)
    katakana_matches = re.findall(r'[\u30a0-\u30ff]{3,12}', text)
    terms.update(katakana_matches)
    
    # Alphanumeric (Word boundaries?)
    # Simple regex for now
    alnum_matches = re.findall(r'[a-zA-Z0-9]{3,20}', text)
    # Filter out common short nonsense if needed, but 3 chars is safe-ish
    terms.update([t.lower() for t in alnum_matches])
    
    return terms
    
def get_paragraphs_and_terms(soup):
    """
    Extract paragraphs/blocks from content AND terms.
    Returns (list_of_block_text, set_of_terms)
    """
    # 1. Ruby Handling: Remove <rt> tags, unwrap <ruby>
    for rt in soup.find_all("rt"):
        rt.decompose() # Remove furigana
    for rp in soup.find_all("rp"):
        rp.decompose() # Remove parens if present

    # Unwrap ruby tags (optional, but get_text does it implicitly if tags are gone)
    
    # 2. Remove unwanted elements
    for selector in ["nav", "header", "footer", "aside", ".toc", ".sidebar", "script", "style", "noscript", "iframe"]:
        for tag in soup.select(selector):
            tag.decompose()

    content_root = None
    if soup.find("main"): content_root = soup.find("main")
    elif soup.find("article"): content_root = soup.find("article")
    elif soup.select_one("#content"): content_root = soup.select_one("#content")
    elif soup.select_one(".content"): content_root = soup.select_one(".content")
    else: content_root = soup.body

    if not content_root:
        return [], set()

    blocks = []
    all_text_content = ""
    
    # 3. Extract Block Text
    # Use the same logic as before: grouping by block tags
    primary_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre', 'dt', 'dd']
    found_blocks = content_root.find_all(primary_tags)
    
    if not found_blocks:
        # Fallback
        raw_text = content_root.get_text(separator='\n')
        lines = [clean_text(line) for line in raw_text.split('\n') if len(clean_text(line)) > 1]
        blocks = lines
        all_text_content = " ".join(lines)
    else:
        for tag in found_blocks:
            # Skip if inside another block (simple check)
            if tag.parent.name in primary_tags:
                continue
                
            text = clean_text(tag.get_text(separator=' ', strip=True))
            if len(text) > 1:
                blocks.append(text)
                all_text_content += " " + text
                
    # 4. Extract Terms from all content
    terms = extract_terms(all_text_content)
    
    return blocks, terms

def build_index():
    # Setup directories
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BOOK_TERMS_DIR, exist_ok=True)
    os.makedirs(BOOKS_DATA_DIR, exist_ok=True)
    
    books_registry = [] # List of books
    
    # Identify "Books" = Direct subdirectories of ROOT that contain HTML files
    # We will traverse specific depth? No, just os.walk but treat top-level dirs as books.
    
    print(f"Scanning root: {os.path.abspath(ROOT_DIR)}")
    
    # First, list top-level directories to define "Books"
    root_items = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d)) and d not in IGNORE_DIRS and not d.startswith('.')]
    
    # Also handle root files as a "General" book? 
    # Or just treat everything under root as part of "Home"?
    # For this site, it seems folders are books.
    
    for book_dir_name in root_items:
        book_path = os.path.join(ROOT_DIR, book_dir_name)
        
        # Check if it has HTML files (recursive)
        has_html = False
        for r, _, fs in os.walk(book_path):
            if any(f.endswith('.html') or f.endswith('.htm') for f in fs):
                has_html = True
                break
        
        if not has_html:
            continue
            
        print(f"Processing Book: {book_dir_name}")
        
        book_id = book_dir_name
        book_title = book_dir_name # Could try to find index.html title
        
        # Try to find title from index.html in that dir
        index_geo = os.path.join(book_path, "index.html")
        if os.path.exists(index_geo):
            try:
                with open(index_geo, 'r', encoding='utf-8') as f:
                    bs = BeautifulSoup(f.read(), 'html.parser')
                    if bs.title:
                        book_title = clean_text(bs.title.string)
            except: pass
            
        books_registry.append({
            "id": book_id,
            "title": book_title,
            "path": book_dir_name
        })
        
        # BOOK PROCESSING
        book_terms = set()
        book_paragraphs_unique = {} # hash -> text (pid)
        book_paragraphs_map = {} # hash -> pid
        book_pages = []
        next_pid = 0
        
        for r, dirs, files in os.walk(book_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                _, ext = os.path.splitext(file)
                if ext.lower() not in ['.html', '.htm']: continue
                
                fpath = os.path.join(r, file)
                
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Skipping {fpath}: {e}")
                    continue
                    
                soup = BeautifulSoup(content, "html.parser")
                
                # Title
                page_title = soup.title.string if soup.title else file
                page_title = clean_text(str(page_title))
                
                blocks, terms = get_paragraphs_and_terms(soup)
                
                # Accumulate Book Terms
                book_terms.update(terms)
                
                # Process Paragraphs
                page_pids = []
                for blk in blocks:
                    h = hash_text(blk)
                    if h not in book_paragraphs_map:
                        pid = f"p{next_pid:x}"
                        next_pid += 1
                        book_paragraphs_map[h] = pid
                        book_paragraphs_unique[pid] = blk
                    
                    page_pids.append(book_paragraphs_map[h])
                
                # URL
                rel_path = os.path.relpath(fpath, ROOT_DIR)
                url_path = rel_path.replace(os.sep, "/")
                full_url = BASE_URL + url_path
                
                book_pages.append({
                    "url": full_url,
                    "title": page_title,
                    "pids": page_pids
                })
        
        # OUTPUT BOOK DATA
        
        # 1. Book Terms
        with open(os.path.join(BOOK_TERMS_DIR, f"{book_id}.json"), "w", encoding="utf-8") as f:
            json.dump(list(book_terms), f, ensure_ascii=False)
            
        # 2. Book Paragraphs & Pages
        book_out_dir = os.path.join(BOOKS_DATA_DIR, book_id)
        os.makedirs(book_out_dir, exist_ok=True)
        
        with open(os.path.join(book_out_dir, "paragraphs.json"), "w", encoding="utf-8") as f:
            json.dump(book_paragraphs_unique, f, ensure_ascii=False)
            
        with open(os.path.join(book_out_dir, "page-paragraphs.json"), "w", encoding="utf-8") as f:
            json.dump(book_pages, f, ensure_ascii=False)
            
    # OUTPUT GLOBAL BOOKS LIST
    with open(os.path.join(DATA_DIR, BOOKS_FILE), "w", encoding="utf-8") as f:
        json.dump(books_registry, f, ensure_ascii=False, indent=2)
        
    print("Build Complete.")

if __name__ == "__main__":
    build_index()

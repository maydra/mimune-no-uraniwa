import os
import json
import re
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://maydra.github.io/mimune-no-uraniwa/"
ROOT_DIR = "."
OUTPUT_DIR = "data"
OUTPUT_FILE = "search-index.json"

# Files/Dirs to ignore
IGNORE_DIRS = {
    ".git", ".github", ".vscode", "data", "images", "css", "js", "pdf", "zip", 
    "pagefind", "brain" # Exclude artifacts if any
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

def extract_content(soup):
    """
    Extract main content from soup. 
    Priority: <main> -> <article> -> #content -> .content -> body
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
        return ""

    return clean_text(content_root.get_text())

def build_index():
    index_data = []
    
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Scanning directory: {os.path.abspath(ROOT_DIR)}")

    for root, dirs, files in os.walk(ROOT_DIR):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            _, ext = os.path.splitext(file)
            if ext.lower() not in [".html", ".htm"]:
                continue
            
            file_path = os.path.join(root, file)
            
            # Read file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            soup = BeautifulSoup(content, "html.parser")
            
            # Extract Title
            title = soup.title.string if soup.title else file
            title = clean_text(str(title))
            
            # Extract Text
            text = extract_content(soup)
            
            if not text:
                continue

            # Generate URL
            # Rel path from root
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            # Convert backslashes to slashes for URL
            url_path = rel_path.replace(os.sep, "/")
            full_url = BASE_URL + url_path

            index_data.append({
                "url": full_url,
                "title": title,
                "text": text
            })
            
    # Write JSON
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, separators=(',', ':')) # Minified
        
    print(f"Index generated: {output_path}")
    print(f"Total pages: {len(index_data)}")

if __name__ == "__main__":
    build_index()

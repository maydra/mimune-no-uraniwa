import os
import re
import shutil
from bs4 import BeautifulSoup

ROOT_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa"
EXCLUDE_DIRS = ['Bible_out', 'peacemessage', '.git', '.agent', 'tmp', 'scripts', 'tools']

MODERN_HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>{title} | み旨の裏庭</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700;900&family=Crimson+Pro:wght@400;600;700&display=swap" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Serif JP', 'Crimson Pro', serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 2rem 1rem;
            line-height: 1.9;
        }}
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(255, 107, 107, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            padding: 3rem;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }}
        h1 {{
            font-size: clamp(2rem, 5vw, 3.5rem);
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2.5rem;
            letter-spacing: 0.05em;
        }}
        details {{
            margin-bottom: 1.2rem;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        details:hover {{
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(102, 126, 234, 0.3);
        }}
        summary {{
            padding: 1.2rem 1.8rem;
            font-size: 1.25rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        summary::-webkit-details-marker {{ display: none; }}
        .summary-title {{ flex-grow: 1; color: #fff; text-decoration: none; }}
        .summary-title:hover {{ text-decoration: underline; }}
        .summary-hint {{ font-size: 0.85rem; opacity: 0.5; font-weight: normal; margin-left: 1rem; }}

        .details-content {{
            padding: 0 1.8rem 1.8rem 3rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 0.5rem;
            padding-top: 1.2rem;
        }}
        .details-content ul {{ list-style: none; }}
        .details-content li {{ margin-bottom: 0.6rem; position: relative; }}
        .details-content li::before {{ content: '▸'; position: absolute; left: -1.2rem; color: #667eea; }}
        .details-content a {{ color: #a5b4fc; text-decoration: none; transition: 0.3s; font-size: 1rem; }}
        .details-content a:hover {{ color: #fff; }}

        .nav-links {{ margin-top: 5rem; text-align: center; }}
        .nav-links a {{
            color: #fff; text-decoration: none; padding: 0.8rem 2rem;
            background: rgba(255, 255, 255, 0.1); border-radius: 50px;
            transition: 0.3s; border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 600; font-size: 1rem;
        }}
        .nav-links a:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-3px); }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 1.5rem; }}
            h1 {{ font-size: 1.8rem; }}
            summary {{ font-size: 1.1rem; padding: 1rem; }}
        }}
    </style>
</head>
<body>
<div class="container">
"""

COMMON_FOOT = """
    <div class="nav-links">
        <a href="../index.html">目次に戻る</a>
    </div>
</div>
</body>
</html>
"""

def extract_subheadings(file_path):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except: return []

    soup = BeautifulSoup(html, 'html.parser')
    sections = []
    
    # Heuristic for subheadings: <p>&nbsp;</p><p>TITLE</p><p>&nbsp;</p>
    ps = soup.find_all('p')
    for i in range(1, len(ps) - 1):
        prev = ps[i-1].get_text(strip=True).replace('\xa0', '')
        curr = ps[i].get_text(strip=True).replace('\xa0', '')
        nxt = ps[i+1].get_text(strip=True).replace('\xa0', '')
        
        if len(prev) == 0 and len(curr) > 0 and len(nxt) == 0:
            if 2 <= len(curr) <= 50 and not ps[i].find('a'):
                # Check for ID or create one if we were modifying content, 
                # but here we just need to know if sections exist.
                sections.append(curr)
    
    # Limit number of subheadings to keep index from being too huge
    return sections[:15]

def get_links_from_mokuji(mokuji_path, base_dir):
    if not os.path.exists(mokuji_path): return []
    try:
        with open(mokuji_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return []

    links = []
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href or 'index.html' in href: continue
        
        full_path = os.path.join(base_dir, href)
        if os.path.exists(full_path):
            if 'mokuji' in href:
                # Recursive call for nested mokuji
                links.extend(get_links_from_mokuji(full_path, base_dir))
            else:
                subheadings = extract_subheadings(full_path)
                links.append({'href': href, 'text': text, 'subsections': subheadings})
    return links

def process_book(book_dir):
    index_path = os.path.join(book_dir, "index.html")
    if not os.path.exists(index_path): return

    print(f"Processing book: {os.path.basename(book_dir)}")
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return

    title = soup.title.get_text().replace('目次', '').strip() if soup.title else os.path.basename(book_dir)
    
    # Extract structural links
    structure = []
    # Find all links in the index
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href or 'index.html' == href: continue
        
        full_path = os.path.join(book_dir, href)
        if os.path.exists(full_path):
            if 'mokuji' in href:
                # It's a volume or section mokuji
                chapters = get_links_from_mokuji(full_path, book_dir)
                structure.append({'type': 'volume', 'title': text, 'href': href, 'chapters': chapters})
            else:
                # It's a direct chapter link
                subheadings = extract_subheadings(full_path)
                structure.append({'type': 'chapter', 'title': text, 'href': href, 'subsections': subheadings})

    # Generate new HTML
    new_html = MODERN_HEAD.format(title=title)
    new_html += f"<h1>{title}</h1>"
    
    if not structure:
        new_html += '<p style="text-align:center; opacity:0.5;">目次データが見つかりませんでした。</p>'
    
    for item in structure:
        if item['type'] == 'volume':
            new_html += f'<details>'
            new_html += f'  <summary><a href="{item["href"]}" class="summary-title">{item["title"]}</a><span class="summary-hint">▼ 収録内容</span></summary>'
            new_html += f'  <div class="details-content"><ul>'
            for ch in item['chapters']:
                new_html += f'<li><a href="{ch["href"]}">{ch["text"]}</a>'
                if ch['subsections']:
                    new_html += '<ul style="margin-left: 1.5rem; opacity: 0.7; font-size: 0.85em; list-style: circle;">'
                    for sub in ch['subsections']:
                        new_html += f'<li>{sub}</li>'
                    new_html += '</ul>'
                new_html += '</li>'
            new_html += f'</ul></div></details>'
        else:
            new_html += f'<details>'
            new_html += f'  <summary><a href="{item["href"]}" class="summary-title">{item["title"]}</a><span class="summary-hint">▼ 小見出し</span></summary>'
            new_html += f'  <div class="details-content"><ul>'
            if item['subsections']:
                for sub in item['subsections']:
                    new_html += f'<li>{sub}</li>'
            else:
                new_html += '<li style="opacity:0.5;">（小見出しなし）</li>'
            new_html += f'</ul></div></details>'
            
    new_html += COMMON_FOOT
    
    # Save index.html
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    # Copy to mokuji.html
    shutil.copy2(index_path, os.path.join(book_dir, "mokuji.html"))

def main():
    # Scan root for directories
    dirs = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d)) and d not in EXCLUDE_DIRS]
    
    for d in dirs:
        process_book(os.path.join(ROOT_DIR, d))

if __name__ == "__main__":
    main()

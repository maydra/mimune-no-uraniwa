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
    <title>{title} | 目次 | み旨の裏庭</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700;900&family=Crimson+Pro:wght@400;600;700&display=swap" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Noto Serif JP', 'Crimson Pro', serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 3rem 1rem;
            line-height: 1.8;
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
            max-width: 900px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(25px);
            padding: 3rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
        }}
        h1 {{
            font-size: clamp(1.8rem, 5vw, 2.5rem);
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 3rem;
            letter-spacing: 0.05em;
        }}
        
        .index-list {{
            list-style: none;
            padding: 0;
        }}
        .volume-item {{
            margin-top: 2.5rem;
            margin-bottom: 1.5rem;
        }}
        .volume-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #fff;
            border-bottom: 2px solid rgba(102, 126, 234, 0.4);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}
        .volume-title a {{ color: #fff; text-decoration: none; }}
        .volume-title a:hover {{ text-decoration: underline; }}

        .chapter-list {{
            list-style: none;
            padding-left: 0.5rem;
        }}
        .chapter-item {{
            margin-bottom: 0.6rem;
            padding: 0.4rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .chapter-link {{
            color: #e0e0e0;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-block;
        }}
        .chapter-link:hover {{ color: #a5b4fc; transform: translateX(5px); }}

        .section-list {{
            list-style: none;
            padding-left: 1.5rem;
            margin-top: 0.4rem;
        }}
        .section-item {{
            margin-bottom: 0.3rem;
        }}
        .section-link {{
            font-size: 0.9rem;
            color: #b0c4de;
            opacity: 0.8;
            text-decoration: none;
            transition: opacity 0.2s;
        }}
        .section-link:hover {{ opacity: 1; color: #fff; }}
        .section-link::before {{ content: '・'; margin-right: 0.3rem; }}

        .nav-links {{
            margin-top: 4rem;
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .nav-links a {{
            color: #fff;
            text-decoration: none;
            padding: 1rem 3rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        .nav-links a:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}

        /* Collapsible Details Styles */
        details {{
            margin-bottom: 1.2rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s;
        }}
        details[open] {{
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(102, 126, 234, 0.3);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        summary {{
            padding: 1.2rem 1.8rem;
            font-size: 1.25rem;
            font-weight: 700;
            cursor: pointer;
            list-style: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #fff;
            transition: background 0.2s;
        }}
        summary:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        summary::-webkit-details-marker {{ display: none; }}
        summary::after {{
            content: '＋';
            font-size: 1.1rem;
            color: #667eea;
            transition: transform 0.3s;
        }}
        details[open] summary::after {{
            content: '－';
            transform: rotate(180deg);
        }}
        .details-content {{
            padding: 0 1.8rem 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 0;
        }}
        .details-content .chapter-item {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }}
        .details-content .chapter-item:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
<div class="container">
"""

COMMON_FOOT = """
    <div class="nav-links">
        <a href="../index.html">トップページへ戻る</a>
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
    
    # Method 1: Look for <b> tags with numeric IDs (Legacy/Transformed headings)
    for b in soup.find_all('b'):
        if b.get('id') and re.match(r'^\d{3,4}$', b.get('id')):
            text = b.get_text(strip=True)
            if text and 2 <= len(text) <= 120:
                sections.append({'text': text, 'id': b.get('id')})
    
    # Method 2: Standard <h1>-<h3>
    if not sections:
        for h in soup.find_all(['h1', 'h2', 'h3']):
            text = h.get_text(strip=True)
            if text and 2 <= len(text) <= 100:
                sections.append({'text': text, 'id': h.get('id')})

    # Method 3: <p>&nbsp;</p><p>TITLE</p><p>&nbsp;</p>
    if not sections:
        ps = soup.find_all('p')
        for i in range(1, len(ps) - 1):
            prev = ps[i-1].get_text(strip=True).replace('\xa0', '')
            curr = ps[i].get_text(strip=True).replace('\xa0', '')
            nxt = ps[i+1].get_text(strip=True).replace('\xa0', '')
            
            if len(prev) == 0 and len(curr) > 0 and len(nxt) == 0:
                if 2 <= len(curr) <= 60 and not ps[i].find('a'):
                    sections.append({'text': curr, 'id': ps[i].get('id')})
    
    # Dedup and limit
    seen_texts = set()
    unique_sections = []
    for s in sections:
        txt = s['text'] if isinstance(s, dict) else s
        if txt not in seen_texts:
            unique_sections.append(s)
            seen_texts.add(txt)
            
    return unique_sections[:15]

def get_links_from_mokuji(mokuji_path, base_dir):
    if not os.path.exists(mokuji_path): return []
    try:
        with open(mokuji_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return []

    links = []
    # If mokuji has nested frames or recursive links, handle carefully
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href or 'index.html' == href: continue
        
        full_path = os.path.join(base_dir, href)
        if os.path.exists(full_path):
            if 'mokuji' in href:
                # Don't recurse too deep, just flatten if possible
                continue
            else:
                subheadings = extract_subheadings(full_path)
                links.append({'href': href, 'text': text, 'subsections': subheadings})
    return links

def process_book(book_dir):
    index_path = os.path.join(book_dir, "index.html")
    if not os.path.exists(index_path): return

    print(f"Processing book: {os.path.basename(book_dir)}")
    
    # Re-parse index.html to get title
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return

    title = soup.title.get_text()
    title = re.sub(r'目次|み旨の裏庭|\|', '', title).strip()
    title = title.lstrip('/')
    if not title: title = os.path.basename(book_dir)

    # Simple extraction logic: Get all unique content links
    # We want to identify "Chapter" links and their "Subheadings"
    content_links = []
    seen_hrefs = set()
    
    # Source of truth: Original mokuji or standard links
    all_as = soup.find_all('a')
    
    # Deduplicate and filter links
    raw_links = []
    for a in all_as:
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href: continue
        if href.startswith('..') or 'index.html' in href or 'mokuji.html' in href: continue
        if any(x in text for x in ['目次', 'トップ', '戻る', '進む', 'ランダム']): continue
        
        # Normalize href
        href = href.replace('./', '')
        if href not in seen_hrefs:
            raw_links.append({'href': href, 'text': text})
            seen_hrefs.add(href)

    # For each unique link, get its subheadings
    for item in raw_links:
        full_path = os.path.join(book_dir, item['href'])
        if not os.path.exists(full_path): continue
        
        subs = []
        if 'mokuji' in item['href'].lower():
            # If it's a mokuji file (like fp1_mokuji.html), get its internal links
            inner_links = get_links_from_mokuji(full_path, book_dir)
            for il in inner_links:
                if il['href'] not in seen_hrefs:
                    content_links.append(il)
                    seen_hrefs.add(il['href'])
        else:
            item['subsections'] = extract_subheadings(full_path)
            content_links.append(item)

    # Generate new Simple Modern HTML
    new_html = MODERN_HEAD.format(title=title)
    new_html += f"<h1>{title}</h1>"
    new_html += '<div class="index-list">'
    
    # Check if this is tf_inori for special collapsible grouping
    if os.path.basename(book_dir) == 'tf_inori':
        # Flattened grouped structure
        for i in range(1, 13):
            fp_filename = f"framepage{i}.html"
            fp_path = os.path.join(book_dir, fp_filename)
            if not os.path.exists(fp_path): continue
            
            try:
                with open(fp_path, 'r', encoding='utf-8') as ffp:
                    fsoup = BeautifulSoup(ffp.read(), 'html.parser')
                
                vol_title = fsoup.title.get_text().replace('目次', '').strip()
                if not vol_title: vol_title = f"父の祈り　第{i}巻"
                
                # Get chapters
                vol_chaps = []
                for la in fsoup.find_all('a'):
                    lhref = la.get('href', '')
                    ltext = la.get_text(strip=True)
                    if lhref.startswith(f"fp{i}_") and 'mokuji' not in lhref:
                        vol_chaps.append({'href': lhref, 'text': ltext})
                
                if vol_chaps:
                    new_html += f'<details>'
                    new_html += f'<summary>{vol_title}</summary>'
                    new_html += '<div class="details-content">'
                    for ch in vol_chaps:
                        new_html += '<div class="chapter-item">'
                        new_html += f'<a href="{ch["href"]}" class="chapter-link">{ch["text"]}</a>'
                        new_html += '</div>'
                    new_html += '</div></details>'
            except:
                continue
    else:
        # Standard list for other books
        for ch in content_links:
            new_html += '<div class="chapter-item">'
            new_html += f'<a href="{ch["href"]}" class="chapter-link">{ch["text"]}</a>'
            if ch.get('subsections'):
                new_html += '<ul class="section-list">'
                for sub in ch['subsections']:
                    if isinstance(sub, dict) and 'id' in sub and sub['id']:
                        new_html += f'<li class="section-item"><a href="{ch["href"]}#{sub["id"]}" class="section-link">{sub["text"]}</a></li>'
                    else:
                        txt = sub['text'] if isinstance(sub, dict) else sub
                        new_html += f'<li class="section-item"><span class="section-link">{txt}</span></li>'
                new_html += '</ul>'
            new_html += '</div>'
        
    new_html += '</div>'
    new_html += COMMON_FOOT
    
    # Save
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    shutil.copy2(index_path, os.path.join(book_dir, "mokuji.html"))

def main():
    dirs = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d)) and d not in EXCLUDE_DIRS]
    for d in dirs:
        process_book(os.path.join(ROOT_DIR, d))

if __name__ == "__main__":
    main()

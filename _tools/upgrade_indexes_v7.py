import os
import re
import sys
from bs4 import BeautifulSoup, NavigableString

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa"

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
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(25px);
            padding: 3rem;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
        }}
        h1 {{
            font-size: clamp(2rem, 6vw, 3rem);
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4rem;
            letter-spacing: 0.1em;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
        }}
        
        .index-list {{
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }}

        .index-entry {{
            transition: all 0.2s ease;
            position: relative;
            display: block;
            text-decoration: none;
            color: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            padding: 0.3rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
        }}

        .index-entry:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(8px);
            color: #fff;
        }}

        /* Level Styles - Indentation */
        .level-0 {{ /* Chapter */
            font-size: 1.35rem;
            font-weight: 700;
            color: #fff;
            margin-top: 1.8rem;
            border-bottom: 2px solid rgba(102, 126, 234, 0.4);
            padding-bottom: 0.4rem;
            margin-bottom: 0.4rem;
            background: rgba(255, 255, 255, 0.03);
        }}
        .level-1 {{ /* Section */
            font-size: 1.2rem;
            font-weight: 600;
            color: #a5b4fc;
            margin-top: 0.8rem;
            margin-left: 0rem;
            padding-left: 1rem;
            border-left: 5px solid #667eea;
            background: rgba(102, 126, 234, 0.05);
        }}
        .level-2 {{ /* Subsection 一、二... */
            font-size: 1.1rem;
            font-weight: 500;
            color: #e0e0e0;
            margin-left: 2rem;
            padding-left: 1rem;
            border-left: 2px solid rgba(255, 255, 255, 0.15);
        }}
        .level-3 {{ /* Minor ｸ、ｹ... */
            font-size: 1rem;
            color: #b0c4de;
            margin-left: 4rem;
            padding-left: 1rem;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .level-4 {{ /* Small ①、②... */
            font-size: 0.95rem;
            color: #8fa1b3;
            margin-left: 6rem;
            padding-left: 1rem;
            border-left: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .nav-links {{
            margin-top: 5rem;
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        .nav-links a {{
            color: #fff;
            text-decoration: none;
            padding: 0.8rem 2.5rem;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
            border-radius: 50px;
            transition: all 0.3s;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        .nav-links a:hover {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.4), rgba(118, 75, 162, 0.4));
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            border-color: #a5b4fc;
        }}

        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            h1 {{ font-size: 1.8rem; }}
            .level-2 {{ margin-left: 1rem; }}
            .level-3 {{ margin-left: 2rem; }}
            .level-4 {{ margin-left: 3rem; }}
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

BLACKLIST = ["礼節と儀式", "サイト目次", "トップページ", "目次に戻る", "HOME", "トップ"]

def get_level(text):
    orig_text = text
    # Clean text: remove "P.41", leading dots/spaces
    text = re.sub(r'^[Pp][\s\.]*\d+[\s\.]*', '', text.strip())
    text = text.lstrip(' 　.・-')
    
    # Chapter level: 第X章
    if re.match(r'^第[一二三四五六七八九十百千万]+章', text):
        return 0
    # Section level: 第X節
    if re.match(r'^第[一二三四五六七八九十百千万]+節', text):
        return 1
    # Subsection level: 一　, 二　 or (一), (二)
    if re.match(r'^[一二三四五六七八九十百]+[\s　、]|^[（\(][一二三四五六七八九十百]+[）\)]', text):
        return 2
    # Minor level: ｸ　, ｹ　 or (1), (2) or １
    if re.match(r'^[ｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ][\s　]|^\d+[\s　、]|^[（\(]\d+[）\)]|^[０-９]+[\s　、]|^[（\(][０-９]+[）\)]|^[0-9]+[\s　、]', text):
        return 3
    # Small level: ①, ②...
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', text):
        return 4
    
    # Keywords
    if "章" in text and len(text) < 15: return 0
    if "節" in text and len(text) < 15: return 1
    
    return -1

def clean_text(t):
    if not t: return None
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) > 70 or len(t) < 2: return None
    if any(b in t for b in BLACKLIST): return None
    return t

def extract_headings_v7(file_path):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_html = f.read()
            soup = BeautifulSoup(content_html, 'html.parser')
    except: return []

    results = []
    seen_texts = set()
    last_id = None

    # We iterate through all elements and text in the body to maintain order
    body = soup.find('blockquote') or soup.find('body')
    if not body: return []

    # Better extraction: iterate through all elements and text nodes
    for element in body.descendants:
        # Update last known ID
        if hasattr(element, 'get') and element.get('id'):
            last_id = element.get('id')
        
        # If it's a tag like <b> it might have an ID itself
        # But we mostly care about the text content matching patterns
        if isinstance(element, NavigableString):
            parent = element.parent
            # Skip script/style content
            if parent.name in ['script', 'style', 'title', 'meta', 'link']: continue
            
            # Text fragments separated by <br> or block boundaries
            # Note: bs4 descendants includes full text nodes. 
            # If the HTML has <p>P.41<br>Heading</p>, we get segments.
            
            text_val = element.strip()
            if not text_val: continue
            
            # Split by common delimiters in case text nodes are combined
            for line in text_val.split('\n'):
                txt = clean_text(line)
                if not txt: continue
                if txt in seen_texts: continue
                
                lv = get_level(txt)
                if lv != -1:
                    # Found a heading!
                    # Try to find an accurate ID
                    best_id = last_id
                    # If the parent has an id (e.g. <b id="001">Chapter</b>), use it
                    if parent.get('id'): best_id = parent.get('id')
                    
                    results.append({'text': txt, 'id': best_id, 'level': lv})
                    seen_texts.add(txt)

    return results

def process_book_v7(book_dir):
    book_id = os.path.basename(book_dir)
    print(f"Processing {book_id}...")
    
    index_path = os.path.join(book_dir, "index.html")

    source_files = []
    mokuji_path = os.path.join(book_dir, "mokuji.html")
    if os.path.exists(mokuji_path):
        try:
            with open(mokuji_path, 'r', encoding='utf-8') as f:
                msoup = BeautifulSoup(f.read(), 'html.parser')
            for a in msoup.find_all('a'):
                href = a.get('href', '').split('#')[0]
                if href.endswith('.html') and '../' not in href:
                    if href not in ['index.html', 'Index.html', 'mokuji.html', 'random.html']:
                        if href not in source_files:
                            source_files.append(href)
        except: pass
        
    if not source_files:
        for f in os.listdir(book_dir):
            if f.endswith('.html') and f.lower() not in ['index.html', 'Index.html', 'mokuji.html', 'random.html', 'divine.html']:
                if re.match(r'^\d', f):
                    source_files.append(f)
        source_files.sort()
    
    all_index_items = []
    
    for fname in source_files:
        path = os.path.join(book_dir, fname)
        headings = extract_headings_v7(path)
        
        if not headings:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                rt = soup.title.get_text() if soup.title else ""
                title = re.sub(r'^[\d\w]+_', '', rt).strip().split('|')[0].strip()
                if not title and soup.h1: title = soup.h1.get_text().strip()
                
                if title and not any(b in title for b in BLACKLIST):
                    lv = get_level(title)
                    if lv == -1: lv = 2
                    headings = [{'text': title, 'id': None, 'level': lv}]
            except: pass
            
        for h in headings:
            all_index_items.append({
                'text': h['text'],
                'href': f"{fname}#{h['id']}" if h.get('id') else fname,
                'level': h['level']
            })

    unique_items = []
    seen = set()
    for item in all_index_items:
        key = (item['text'], item['level'])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    final_title = book_id
    for search_file in ['mokuji.html', 'Index.html', 'Index03.html', 'index.html']:
        sp = os.path.join(book_dir, search_file)
        if os.path.exists(sp):
            try:
                with open(sp, 'r', encoding='utf-8') as f:
                    isoup = BeautifulSoup(f.read(), 'html.parser')
                    t_cand = ""
                    if isoup.title:
                        t_cand = isoup.title.get_text().split('|')[0].strip()
                    elif isoup.h1:
                        t_cand = isoup.h1.get_text().strip()
                    
                    if t_cand and t_cand.lower() != book_id.lower() and t_cand != "目次":
                        final_title = t_cand.replace('目次', '').strip().rstrip('/')
                        if final_title: break
            except: pass

    new_html = MODERN_HEAD.format(title=final_title)
    new_html += f"<h1>{final_title}</h1>"
    new_html += '<div class="index-list">'
    
    for item in unique_items:
        lv = item['level']
        level_class = f"level-{lv}"
        new_html += f'<a href="{item["href"]}" class="index-entry {level_class}">{item["text"]}</a>\n'
    
    new_html += '</div>'
    new_html += COMMON_FOOT
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f"  Finalized: {index_path} ({len(unique_items)} items) Title: {final_title}")

def main():
    targets = ['makotonarusijyonomiti', 'bokkaisyanomiti', 'kitou']
    for t in targets:
        path = os.path.join(ROOT_DIR, t)
        if os.path.isdir(path):
            process_book_v7(path)

if __name__ == "__main__":
    main()

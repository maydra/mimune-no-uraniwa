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

        .section-item {{ margin-bottom: 0.2rem; }}
        .section-item.indent-1 {{ margin-left: 1.5rem; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 0.8rem; margin-top: 0.3rem; }}
        .section-item.indent-2 {{ margin-left: 3.0rem; border-left: 1px solid rgba(255,255,255,0.04); padding-left: 0.8rem; margin-top: 0.2rem; }}
        .section-item.indent-3 {{ margin-left: 4.5rem; border-left: 1px solid rgba(255,255,255,0.02); padding-left: 0.8rem; margin-top: 0.1rem; }}
        .section-item.indent-4 {{ margin-left: 6.0rem; border-left: 1px solid rgba(255,255,255,0.01); padding-left: 0.8rem; margin-top: 0.1rem; }}

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

def extract_subheadings(file_path, exclude_title=None):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except: return []

    soup = BeautifulSoup(html, 'html.parser')
    sections = []
    
    # Method 0: Look for structured TOC in <nav id="toc">
    toc_nav = soup.find('nav', id='toc')
    if toc_nav:
        def parse_toc_ul(ul, level=0):
            res = []
            for li in ul.find_all('li', recursive=False):
                a = li.find('a', recursive=False)
                if a:
                    t = a.get_text(strip=True)
                    h = a.get('href', '').replace('#', '')
                    if t and h:
                        res.append({'text': t, 'id': h, 'level': level})
                nested = li.find('ul', recursive=False)
                if nested:
                    res.extend(parse_toc_ul(nested, level + 1))
            return res
        
        main_ul = toc_nav.find('ul')
        if main_ul:
            sections = parse_toc_ul(main_ul)

    if not sections:
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
    
    # Deduplicate while prioritizing items with IDs and maintaining order
    unique_sections = []
    seen = {}  # text_normalized -> index
    
    def normalize(t):
        if not t: return ""
        # Remove spaces, numbers, and common markers for comparison
        t = re.sub(r'[\s　0-9一二三四五六七八九十]', '', t)
        for junk in ['原理講論', '第', '章', '節', '序', '論']:
            t = t.replace(junk, '')
        return t

    norm_exclude = normalize(exclude_title) if exclude_title else ""

    for s in sections:
        txt = s['text']
        sid = s.get('id')
        
        # Global filter: remove typo reports and index links
        if any(x in txt for x in ['誤植', '修正提案', '目次', 'トップ', '戻る']):
            continue
            
        # Similarity filter to remove redundancy with chapter title
        # For structured TOCs (Method 0), we are more lenient
        norm_txt = normalize(txt)
        if norm_exclude and len(norm_txt) > 0:
            # Only apply strict filtering for non-TOC items or exact matches
            is_toc_item = toc_nav is not None
            if norm_txt == norm_exclude:
                continue
            if not is_toc_item:
                if norm_txt in norm_exclude or (len(norm_txt) > 2 and norm_exclude in norm_txt):
                    continue

        # Level detection for hierarchical display (if not already set by TOC)
        level = s.get('level', 0)
        if level == 0:
            if re.match(r'^[（\(][一二三四五六七八九十百]+[）\)]', txt): level = 1
            elif re.match(r'^\(\d+\)', txt): level = 2
        s['level'] = level

        if norm_txt in seen:
            idx = seen[norm_txt]
            if not unique_sections[idx].get('id') and sid:
                unique_sections[idx]['id'] = sid
        else:
            seen[norm_txt] = len(unique_sections)
            unique_sections.append(s)
            
    return unique_sections[:50]  # Allow more for deep hierarchies like DP

def get_links_from_mokuji(mokuji_path, base_dir):
    if not os.path.exists(mokuji_path): return []
    try:
        with open(mokuji_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return []

    links = []
    # If mokuji has nested frames or recursive links, handle carefully
    seen_hrefs = set()
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href or 'index.html' == href: continue
        
        # Avoid duplicate links to same chapter
        clean_href = href.split('?')[0].split('#')[0]
        if clean_href in seen_hrefs: continue
        seen_hrefs.add(clean_href)
        
        full_path = os.path.join(base_dir, href)
        if os.path.exists(full_path):
            if 'mokuji' in href:
                # Don't recurse too deep, just flatten if possible
                continue
            
            # If text is too short or generic, try to get from title or h1/h2
            is_generic = len(text) < 2 or any(x in text for x in ['本文を読む', '次へ', '前へ', '戻る', 'トップ'])
            if is_generic:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        tsoup = BeautifulSoup(f.read(), 'html.parser')
                    # Fallback sequence: title -> h1 -> h2
                    candidate = None
                    if tsoup.title:
                        candidate = tsoup.title.get_text(strip=True).replace('原理講論', '').replace('|', '').replace(':', '').strip()
                    if not candidate or len(candidate) < 2:
                        h1 = tsoup.find('h1')
                        if h1: candidate = h1.get_text(strip=True)
                    if not candidate or len(candidate) < 2:
                        h2 = tsoup.find('h2')
                        if h2: candidate = h2.get_text(strip=True)
                    
                    if candidate and len(candidate) >= 2:
                        print(f"  [DEBUG] Fixed generic title for {href}: '{text}' -> '{candidate}'")
                        text = candidate
                    else:
                        print(f"  [DEBUG] Failed to find candidate for {href}")
                except Exception as e:
                    print(f"  [DEBUG] Error reading {href}: {e}")

            # Final filter to avoid navigation-only links if we couldn't find a better name
            if any(x in text for x in ['本文を読む', '次へ', '前へ', '戻る', 'トップ']):
                continue

            subheadings = extract_subheadings(full_path, exclude_title=text)
            links.append({'href': href, 'text': text, 'subsections': subheadings})
    return links

def process_book(book_dir):
    # Try to find the best source for links (prioritize divine.html or mokuji.html over index.html)
    candidates = ["divine.html", "mokuji.html", "index.html"]
    index_path = None
    for c in candidates:
        p = os.path.join(book_dir, c)
        if os.path.exists(p):
            # If it's index.html or a generated mokuji, we might need a fallback for titles
            index_path = p
            break
            
    if not index_path: return

    print(f"Processing book: {os.path.basename(book_dir)} (source: {os.path.basename(index_path)})")
    
    # Re-parse index source to get metadata
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return

    title = soup.title.get_text()
    title = re.sub(r'目次|み旨の裏庭|\|', '', title).strip()
    title = title.lstrip('/')
    
    book_id = os.path.basename(book_dir)
    if book_id == 'syougairotei_11':
        title = "御父母様の生涯路程⑪"
        
    if not title: title = book_id

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

    # For each unique link, get its subheadings and fix generic titles
    for item in raw_links:
        full_path = os.path.join(book_dir, item['href'])
        if not os.path.exists(full_path): continue
        
        # If title is generic (e.g. from a previous run index.html), fix it
        is_generic = len(item['text']) < 2 or any(x in item['text'] for x in ['本文を読む', '次へ', '前へ', '戻る', 'トップ', '➡'])
        if is_generic:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    tsoup = BeautifulSoup(f.read(), 'html.parser')
                candidate = None
                if tsoup.title:
                    candidate = tsoup.title.get_text(strip=True).replace('原理講論', '').replace('|', '').replace(':', '').strip()
                if not candidate or len(candidate) < 2:
                    h1 = tsoup.find('h1')
                    if h1: candidate = h1.get_text(strip=True)
                if not candidate or len(candidate) < 2:
                    h2 = tsoup.find('h2')
                    if h2: candidate = h2.get_text(strip=True)
                if candidate and len(candidate) >= 2:
                    print(f"  [FIX] Title for {item['href']}: '{item['text']}' -> '{candidate}'")
                    item['text'] = candidate
            except: pass

        if 'mokuji' in item['href'].lower() and os.path.exists(full_path):
            inner_links = get_links_from_mokuji(full_path, book_dir)
            for il in inner_links:
                if il['href'] not in seen_hrefs:
                    content_links.append(il)
                    seen_hrefs.add(il['href'])
        else:
            item['subsections'] = extract_subheadings(full_path, exclude_title=item['text'])
            content_links.append(item)

    # Generate new Simple Modern HTML
    new_html = MODERN_HEAD.format(title=title)
    new_html += f"<h1>{title}</h1>"
    new_html += '<div class="index-list">'
    
    # Check if this is tf_inori for special collapsible grouping
    book_id = os.path.basename(book_dir)
    if book_id == 'tf_inori':
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
    elif book_id == 'syougairotei_11':
        # Special layout for Lifetime Course 11
        sections_config = [
            ("第一節　一九九三年　新しい家庭と統一祖国", 1, 1, 10),
            ("第二節 一九九四年 真の父母と成約時代定着", 2, 1, 8),
            ("第三節 一九九五年 真の御父母様の勝利圏を相続しよう", 3, 1, 10)
        ]
        
        for sec_name, ch_num, start_s, end_s in sections_config:
            new_html += f'<div class="volume-item">'
            new_html += f'<h2 class="volume-title">{sec_name}</h2>'
            new_html += '<div class="chapter-list">'
            for s in range(start_s, end_s + 1):
                href = f"chapter00{ch_num}_section{s}.html"
                full_p = os.path.join(book_dir, href)
                if os.path.exists(full_p):
                    try:
                        with open(full_p, 'r', encoding='utf-8') as f:
                            csoup = BeautifulSoup(f.read(), 'html.parser')
                        chap_title = csoup.find('h2').get_text(strip=True) if csoup.find('h2') else href
                        
                        new_html += '<div class="chapter-item">'
                        new_html += f'<a href="{href}" class="chapter-link">{chap_title}</a>'
                        
                        # Subheadings
                        subs = extract_subheadings(full_p, exclude_title=chap_title)
                        if subs:
                            new_html += '<ul class="section-list">'
                            for sub in subs:
                                l_cls = f"section-item indent-{sub['level']}" if sub.get('level') else "section-item"
                                if isinstance(sub, dict) and 'id' in sub and sub['id']:
                                    new_html += f'<li class="{l_cls}"><a href="{href}#{sub["id"]}" class="section-link">{sub["text"]}</a></li>'
                            new_html += '</ul>'
                        new_html += '</div>'
                    except: continue
            new_html += '</div></div>'
            
    elif book_id == 'dp':
        # Custom precise mapping and grouped structure for Divine Principle
        dp_groups = [
            ("", [("総序", "10sojo.html")]),
            ("【前編】", [
                ("第1章　創造原理", "11sozo.html"),
                ("第2章　堕落論", "12daraku.html"),
                ("第3章　人類歴史の終末論", "13shuma.html"),
                ("第4章　メシヤの降臨とその再臨の目的", "14meshia.html"),
                ("第5章　復活論", "15fukka.html"),
                ("第6章　予定論", "16yotei.html"),
                ("第7章　キリスト論", "17kirisu.html")
            ]),
            ("【後編】", [
                ("緒論", "20sho.html"),
                ("第1章　復帰基台摂理時代", "21kidai.html"),
                ("第2章　モーセとイエスを中心とする復帰摂理", "22mose.html"),
                ("第3章　摂理歴史の各時代とその年数の形成", "23kaku.html"),
                ("第4章　摂理的同時性から見た復帰摂理時代と復帰摂理延長時代", "24douji.html"),
                ("第5章　メシヤ再降臨準備時代", "25saiko.html"),
                ("第6章　再臨論", "26sairi.html")
            ])
        ]
        
        # Build a lookup for subheadings
        link_map = {ch['href']: ch for ch in content_links}
        
        for sec_title, entries in dp_groups:
            if sec_title:
                new_html += f'<h2 class="volume-title" style="margin-top: 2.5rem; border-bottom: 2px solid rgba(102,126,234,0.4); padding-bottom:0.5rem; color:#fff;">{sec_title}</h2>'
            
            for label, fname in entries:
                # Find the existing entry to get subheadings
                ch = link_map.get(fname, {"href": fname, "text": label})
                
                new_html += '<div class="chapter-item">'
                new_html += f'<details>'
                new_html += f'<summary>{label}</summary>'
                new_html += '<div class="details-content">'
                new_html += f'<div style="margin: 1rem 0 1.5rem 0;"><a href="{fname}" class="chapter-link" style="font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.2);">➡ この章の本文を読む</a></div>'
                
                # Use subheadings from extraction if available
                subsections = ch.get('subsections')
                if subsections:
                    new_html += '<ul class="section-list">'
                    for sub in subsections:
                        l_cls = f"section-item indent-{sub.get('level', 0)}" if sub.get('level') else "section-item"
                        if isinstance(sub, dict) and 'id' in sub and sub['id']:
                            new_html += f'<li class="{l_cls}"><a href="{fname}#{sub["id"]}" class="section-link">{sub["text"]}</a></li>'
                    new_html += '</ul>'
                new_html += '</div></details></div>'
    else:
        # Standard list for other books
        for ch in content_links:
            new_html += '<div class="chapter-item">'
            new_html += f'<a href="{ch["href"]}" class="chapter-link">{ch["text"]}</a>'
            if ch.get('subsections'):
                new_html += '<ul class="section-list">'
                for sub in ch['subsections']:
                    l_cls = f"section-item indent-{sub.get('level', 0)}" if sub.get('level') else "section-item"
                    if isinstance(sub, dict) and 'id' in sub and sub['id']:
                        new_html += f'<li class="{l_cls}"><a href="{ch["href"]}#{sub["id"]}" class="section-link">{sub["text"]}</a></li>'
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

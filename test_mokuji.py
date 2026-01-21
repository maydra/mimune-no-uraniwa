import os
from bs4 import BeautifulSoup

def get_links_from_mokuji(mokuji_path, base_dir):
    if not os.path.exists(mokuji_path): return []
    try:
        with open(mokuji_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except: return []

    links = []
    seen_hrefs = set()
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if not href or href.startswith('http') or '#' in href or 'index.html' == href: continue
        
        clean_href = href.split('?')[0]
        if clean_href in seen_hrefs: continue
        if any(x in text for x in ['本文を読む', '次へ', '前へ', '戻る', 'トップ']):
            print(f"Skipping navigation link: {text}")
            continue
            
        seen_hrefs.add(clean_href)
        print(f"Found link: {text} -> {href}")
        links.append({'href': href, 'text': text})
    return links

res = get_links_from_mokuji('dp/mokuji.html', 'dp')
print(res)

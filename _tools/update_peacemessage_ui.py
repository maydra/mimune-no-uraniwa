import os
import re
from bs4 import BeautifulSoup

# Define directories
TARGET_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\peacemessage"
INDEX_FILE = os.path.join(TARGET_DIR, "index.html")

# Modified Header with the same modern style as the main index
MODERN_HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>{title} | 平和メッセージ</title>
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
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2.5rem;
            letter-spacing: 0.05em;
        }}
        .toc {{
            background: rgba(0, 0, 0, 0.3);
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 3rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .toc-title {{
            font-weight: 700;
            font-size: 1.2rem;
            margin-bottom: 1.5rem;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .toc-title::before {{ content: '◆'; color: #667eea; font-size: 0.8em; }}
        .toc ul {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.8rem; }}
        .toc li {{ position: relative; padding-left: 1.5rem; }}
        .toc li::before {{ content: '▸'; position: absolute; left: 0; color: #667eea; }}
        .toc a {{ color: #b8c1ec; text-decoration: none; transition: all 0.3s; }}
        .toc a:hover {{ color: #fff; text-decoration: underline; }}
        
        .subheading {{
            font-weight: 700;
            font-size: 1.8rem;
            color: #fff;
            margin: 5rem 0 2rem 0;
            display: block;
            border-left: 6px solid #667eea;
            padding: 0.5rem 0 0.5rem 1.5rem;
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.1) 0%, transparent 100%);
        }}
        .subheading a {{ color: inherit; text-decoration: none; }}
        
        /* Details style for Index */
        details {{
            margin-bottom: 1.5rem;
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
            padding: 1.5rem 2rem;
            font-size: 1.4rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        summary::-webkit-details-marker {{ display: none; }}
        .summary-title {{ flex-grow: 1; color: #fff; text-decoration: none; }}
        .summary-title:hover {{ text-decoration: underline; }}
        .summary-hint {{ font-size: 0.9rem; opacity: 0.5; font-weight: normal; }}

        .details-content {{
            padding: 0 2rem 2rem 3.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 0.5rem;
            padding-top: 1.5rem;
        }}
        .details-content ul {{ list-style: none; }}
        .details-content li {{ margin-bottom: 0.8rem; position: relative; }}
        .details-content li::before {{ content: '▸'; position: absolute; left: -1.5rem; color: #667eea; }}
        .details-content a {{ color: #a5b4fc; text-decoration: none; transition: 0.3s; font-size: 1.1rem; }}
        .details-content a:hover {{ color: #fff; }}

        .nav-links {{ margin-top: 5rem; text-align: center; }}
        .nav-links a {{
            color: #fff; text-decoration: none; padding: 1rem 2.5rem;
            background: rgba(255, 255, 255, 0.1); border-radius: 50px;
            transition: 0.3s; border: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: 600;
        }}
        .nav-links a:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-3px); }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 1.5rem; }}
            h1 {{ font-size: 2.2rem; }}
            .subheading {{ font-size: 1.5rem; }}
            .toc ul {{ grid-template-columns: 1fr; }}
            summary {{ font-size: 1.2rem; padding: 1.2rem; }}
        }}
    </style>
</head>
<body>
<div class="container">
"""

COMMON_FOOT = """
    <div class="nav-links">
        <a href="index.html">目次に戻る</a>
    </div>
</div>
</body>
</html>
"""

def fix_index():
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # Reconstruct the index body with fixed links and styling
    new_body = MODERN_HEAD.format(title="平和神経／平和メッセージ")
    new_body += "<h1>平和神経／平和メッセージ</h1>"
    new_body += '<p style="text-align:center; opacity:0.8; margin-bottom: 3rem;">世界平和統一家庭連合の創始者、文鮮明・韓鶴子ご夫妻による講演文集です。</p>'

    details_list = soup.find_all('details')
    for det in details_list:
        summary = det.find('summary')
        content_a = summary.find('a')
        href = content_a['href']
        title_text = content_a.get_text()
        
        sections_ul = det.find('ul')
        
        new_body += f'<details>'
        new_body += f'  <summary>'
        new_body += f'    <a href="{href}" class="summary-title">{title_text}</a>'
        new_body += f'    <span class="summary-hint">▼ 章一覧</span>'
        new_body += f'  </summary>'
        new_body += f'  <div class="details-content">'
        if sections_ul:
            # Rebuild clean UL
            new_body += '<ul>'
            for li in sections_ul.find_all('li'):
                a = li.find('a')
                new_body += f'<li><a href="{a["href"]}">{a.get_text()}</a></li>'
            new_body += '</ul>'
        else:
            new_body += '<p style="opacity: 0.5;">（目次構成なし）</p>'
        new_body += '  </div>'
        new_body += '</details>'

    # Top level nav link
    new_body += """
    <div class="nav-links">
        <a href="../index.html">トップページへ戻る</a>
    </div>
</div>
</body>
</html>
"""
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(new_body)

def update_all_pages():
    for i in range(1, 18):
        file_path = os.path.join(TARGET_DIR, f"{i}.html")
        if not os.path.exists(file_path): continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        title = soup.title.get_text().replace(' | 平和メッセージ', '')
        h1_text = soup.h1.get_text()
        toc = soup.find('div', class_='toc')
        
        # The content is everything between toc (or h1) and nav-links
        # Let's find common wrapper elements
        content = ""
        # Find everything after TOC
        start_node = toc if toc else soup.h1
        for sibling in start_node.find_next_siblings():
            if 'nav-links' in sibling.get('class', []):
                break
            content += str(sibling)
            
        new_html = MODERN_HEAD.format(title=title)
        new_html += f"<h1>{h1_text}</h1>"
        if toc: new_html += str(toc)
        new_html += content
        new_html += COMMON_FOOT
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_html)

if __name__ == "__main__":
    fix_index()
    update_all_pages()
    print("UI update completed.")

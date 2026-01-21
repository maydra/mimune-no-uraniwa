import os
import re
from bs4 import BeautifulSoup

# Define directories
SOURCE_ROOT = r"C:\Users\dream\OneDrive\デスクトップ\output_html_peacemessages\peacemessages"
TARGET_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\peacemessage"

# Common Header/Footer for the new site
COMMON_HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>{{title}} | 平和メッセージ</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet" />
    <style>
        body {{
            font-family: 'Noto Serif JP', serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: #e0e0e0;
            line-height: 1.8;
            padding: 2rem 1rem;
            margin: 0;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 2.5rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            font-size: 2.2rem;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            font-weight: 700;
        }}
        .toc {{
            background: rgba(0, 0, 0, 0.2);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }}
        .toc-title {{
            font-weight: 700;
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        .toc ul {{
            list-style: none;
            padding: 0;
        }}
        .toc li {{
            margin-bottom: 0.5rem;
        }}
        .toc a {{
            color: #a5b4fc;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        p {{
            margin: 1.5rem 0;
        }}
        .subheading {{
            font-weight: 700;
            font-size: 1.4rem;
            color: #fff;
            margin: 3.5rem 0 1.5rem 0;
            display: block;
            border-left: 5px solid #667eea;
            padding-left: 1rem;
            background: rgba(255,255,255,0.03);
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
        }}
        .subheading a {{
            color: inherit;
            text-decoration: none;
        }}
        .nav-links {{
            margin-top: 4rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 2rem;
            text-align: center;
        }}
        .nav-links a {{
            color: #fff;
            text-decoration: none;
            margin: 0 1rem;
            padding: 0.5rem 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }}
        summary {{
            list-style: none;
            outline: none;
        }}
        summary::-webkit-details-marker {{
            display: none;
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

def process_peacemessage(num):
    src_file = os.path.join(SOURCE_ROOT, f"peacemessages{num}", "index.html")
    if not os.path.exists(src_file):
        print(f"File not found: {src_file}")
        return None

    with open(src_file, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract Title
    title_tag = soup.find('h2', class_='title')
    title = title_tag.get_text() if title_tag else f"平和メッセージ{num}"

    # Find the main body content
    content_div = soup.find('div', class_='content')
    if not content_div:
        content_div = soup.find('div', class_='post-content')
    
    if not content_div:
        print(f"Content div not found for PM{num}")
        return None

    # Clean up the content
    # Find the white background div usually inside content
    inner_block = content_div.find('div', style=lambda s: s and 'background:#fff' in s.replace(' ', ''))
    if inner_block:
        work_soup = inner_block
    else:
        work_soup = content_div

    # Identify subheadings and build sections
    sections = []
    
    # We'll go through all p tags and look for the pattern
    # <p>&nbsp;</p> <p>TEXT</p> <p>&nbsp;</p>
    all_p = work_soup.find_all('p')
    for i in range(1, len(all_p) - 1):
        prev_p = all_p[i-1]
        curr_p = all_p[i]
        next_p = all_p[i+1]
        
        # Check if prev and next are effectively empty (just nbsp or whitespace)
        def is_empty(p):
            text = p.get_text(strip=True).replace('\xa0', '')
            return len(text) == 0

        if is_empty(prev_p) and is_empty(next_p) and not is_empty(curr_p):
            text = curr_p.get_text(strip=True)
            # Rough filter for subheadings
            if 2 <= len(text) <= 50 and not curr_p.find('a'):
                anchor = f"sec-{len(sections) + 1}"
                sections.append({'text': text, 'anchor': anchor})
                
                # Replace the p tag with a proper heading structure
                new_tag = soup.new_tag("span", id=anchor)
                new_tag['class'] = "subheading"
                a_tag = soup.new_tag("a", href=f"#{anchor}")
                a_tag.string = text
                new_tag.append(a_tag)
                curr_p.replace_with(new_tag)

    content_html = ""
    for child in work_soup.children:
        # Skip top level script/style if any
        if child.name in ['script', 'style']:
            continue
        content_html += str(child)

    # Build TOC for the page
    toc_html = ""
    if sections:
        toc_html = '<div class="toc"><div class="toc-title">目次</div><ul>'
        for sec in sections:
            toc_html += f'<li><a href="#{sec["anchor"]}">{sec["text"]}</a></li>'
        toc_html += '</ul></div>'

    final_html = COMMON_HEAD.replace('{{title}}', title) + f"<h1>{title}</h1>" + toc_html + content_html + COMMON_FOOT
    
    target_file = os.path.join(TARGET_DIR, f"{num}.html")
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    return {'num': num, 'title': title, 'sections': sections}

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        
    results = []
    for i in range(1, 18):
        print(f"Processing PM{i}...")
        res = process_peacemessage(i)
        if res:
            results.append(res)

    # Generate index.html
    index_title = "平和神経／平和メッセージ"
    index_body = f"<h1>{index_title}</h1>"
    index_body += '<p style="text-align:center; opacity:0.8;">世界平和統一家庭連合の創始者、文鮮明・韓鶴子ご夫妻による講演文集です。</p><br>'
    
    for res in results:
        num = res['num']
        title = res['title']
        sections = res['sections']
        
        index_body += f'<details style="margin-bottom: 1.2rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; transition: all 0.3s ease;">'
        index_body += f'<summary style="padding: 1.2rem; font-size: 1.3rem; font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">'
        index_body += f'<a href="{num}.html" style="color: #fff; text-decoration: none; flex-grow: 1;">{title}</a>'
        index_body += f'<span style="opacity: 0.5; font-size: 0.9rem;">▼ 章一覧</span>'
        index_body += f'</summary>'
        if sections:
            index_body += '<ul style="margin: 0 1.2rem 1.2rem 2.5rem; list-style: circle; padding-left: 1rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1rem;">'
            for sec in sections:
                index_body += f'<li style="margin-bottom: 0.6rem;"><a href="{num}.html#{sec["anchor"]}" style="color: #a5b4fc; text-decoration: none;">{sec["text"]}</a></li>'
            index_body += '</ul>'
        else:
            index_body += '<p style="padding: 0 1.2rem 1.2rem; opacity: 0.5;">（目次構成なし）</p>'
        index_body += '</details>'

    final_index = COMMON_HEAD.replace('{{title}}', index_title) + index_body + COMMON_FOOT
    final_index = final_index.replace('<a href="index.html">目次に戻る</a>', '<a href="../index.html">トップページへ戻る</a>')
    
    with open(os.path.join(TARGET_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(final_index)
    print("Migration completed successfully.")

if __name__ == "__main__":
    main()

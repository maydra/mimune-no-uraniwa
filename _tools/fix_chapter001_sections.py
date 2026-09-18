import requests
from bs4 import BeautifulSoup
import os
import copy
import sys

# Configure stdout for UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BASE_DIR = r"C:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\syougairotei_11"
LIVE_URL = "https://maydra.github.io/mimune-no-uraniwa/syougairotei_11/chapter001.html"

print(f"Downloading content from {LIVE_URL}...")
response = requests.get(LIVE_URL)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

# Extract the head and body attrs
head_content = soup.head
body_attrs = soup.body.attrs if soup.body else {}

# Find all H2 sections
h2_tags = soup.find_all('h2')
print(f"Found {len(h2_tags)} H2 tags")

# Filter to get sections 4-10
section_map = {
    '四　アメリカでの活動方向と事業推進': 4,
    '五　世界平和具現のための摂理': 5,
    '六　真の御父母様のアメリカ巡回講演と主要行事': 6,
    '七　真のお母様の日本巡回講演と日本の使命': 7,
    '八　真のお母様の韓国巡回講演': 8,
    '九　日本の女性幹部の特別修練': 9,
    '十　真のお母様の世界巡回講演と真の御子女様のアメリカ講演': 10
}

sections_to_extract = []
for h2 in h2_tags:
    title = h2.get_text(strip=True)
    if title in section_map:
        sections_to_extract.append((section_map[title], title, h2))

sections_to_extract.sort(key=lambda x: x[0])
print(f"Found {len(sections_to_extract)} sections to extract (4-10)")

# Extract content for each section
for i, (section_num, title, h2) in enumerate(sections_to_extract):
    print(f"\nProcessing section {section_num}: {title}")
    
    # Collect content until next H2
    content_nodes = []
    current = h2.next_sibling
    
    # Find the next section's H2 (if any)
    next_h2 = sections_to_extract[i+1][2] if i < len(sections_to_extract) - 1 else None
    
    while current:
        if current == next_h2:
            break
        if current.name == 'h2' and current != h2:
            # Stop at any H2 that's not our starting one
            break
        content_nodes.append(current)
        current = current.next_sibling
    
    # Create new HTML file
    new_soup = BeautifulSoup("<!DOCTYPE html><html lang='ja'></html>", 'html.parser')
    if head_content:
        new_soup.html.append(copy.copy(head_content))
    
    new_body = new_soup.new_tag('body', **body_attrs)
    new_soup.html.append(new_body)
    
    new_container = new_soup.new_tag('div', attrs={'class': 'container'})
    new_body.append(new_container)
    
    # Navigation
    nav_div = new_soup.new_tag('div', style="margin-bottom: 20px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px;")
    back_link = new_soup.new_tag('a', href="index.html")
    back_link.string = "← 目次に戻る"
    nav_div.append(back_link)
    
    if section_num > 1:
        prev_link = new_soup.new_tag('a', href=f"chapter001_section{section_num-1}.html", style="margin-left: 20px;")
        prev_link.string = "前へ"
        nav_div.append(prev_link)
    
    if section_num < 10:
        next_link = new_soup.new_tag('a', href=f"chapter001_section{section_num+1}.html", style="margin-left: 20px;")
        next_link.string = "次へ"
        nav_div.append(next_link)
    
    new_container.append(nav_div)
    
    # Content
    new_content_div = new_soup.new_tag('div', attrs={'class': 'content'})
    new_container.append(new_content_div)
    
    # Add H2 and content
    new_content_div.append(copy.copy(h2))
    for node in content_nodes:
        new_content_div.append(copy.copy(node))
    
    # Bottom navigation
    new_container.append(copy.copy(nav_div))
    
    # Write file
    filename = f"chapter001_section{section_num}.html"
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(new_soup))
    
    print(f"  Created {filename} ({len(str(new_soup))} bytes)")

print("\nDone!")

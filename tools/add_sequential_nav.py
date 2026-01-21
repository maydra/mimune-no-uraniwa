import os
from bs4 import BeautifulSoup

TARGET_DIR = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\peacemessage"

def update_nav_links():
    for i in range(1, 18):
        file_path = os.path.join(TARGET_DIR, f"{i}.html")
        if not os.path.exists(file_path):
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        nav_div = soup.find('div', class_='nav-links')
        if not nav_div:
            continue
            
        # Clear existing links
        nav_div.clear()
        
        # Build new navigation
        links = []
        
        # Back to Index (Always present)
        links.append(('<a href="index.html">目次に戻る</a>'))
        
        # Previous Page
        if i > 1:
            links.insert(0, f'<a href="{i-1}.html">前のページに戻る</a>')
            
        # Next Page
        if i < 17:
            links.append(f'<a href="{i+1}.html">次のページに進む</a>')
            
        # Join links with proper HTML structure
        # Since we use clear() above, we can just inject the HTML
        nav_div.append(BeautifulSoup(" ".join(links), 'html.parser'))
        
        # Update CSS to handle spacing between buttons if needed, 
        # but the current CSS uses margin on links which might be enough.
        # Let's ensure the style handles multiple links nicely.
        style_tag = soup.find('style')
        if style_tag and ".nav-links a" in style_tag.string:
            if "display: inline-block" not in style_tag.string:
                 style_tag.string = style_tag.string.replace(".nav-links a {", ".nav-links a { display: inline-block; margin: 0.5rem; ")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

if __name__ == "__main__":
    update_nav_links()
    print("Sequential navigation implemented.")

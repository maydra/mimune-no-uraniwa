import os
import re

def inject_theme(root_dir):
    # Absolute path of the root directory to calculate relative paths
    root_abs = os.path.abspath(root_dir)
    
    html_pattern = re.compile(r'\.html$', re.IGNORECASE)
    
    for root, dirs, files in os.walk(root_dir):
        # Skip some directories
        if '.git' in root or 'pagefind' in root:
            continue
            
        for file in files:
            if html_pattern.search(file):
                filepath = os.path.join(root, file)
                file_abs = os.path.abspath(filepath)
                file_dir = os.path.dirname(file_abs)
                
                # Calculate relative path to root_dir
                rel_to_root = os.path.relpath(root_abs, file_dir).replace('\\', '/')
                if rel_to_root == '.':
                    rel_prefix = ''
                else:
                    rel_prefix = rel_to_root + '/'
                
                theme_css = f'<link rel="stylesheet" href="{rel_prefix}theme/style.css">'
                theme_js = f'<script src="{rel_prefix}theme/script.js"></script>'
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Remove old absolute-ish injections if they exist
                    content = re.sub(r'<link rel="stylesheet" href="/mimune-no-uraniwa/theme/style\.css">', '', content)
                    content = re.sub(r'<script src="/mimune-no-uraniwa/theme/script\.js"></script>', '', content)
                    
                    # Check if already injected (avoid double injection if script is rerun)
                    if 'theme/style.css' in content:
                        # Re-inject with correct relative path if it changed
                        content = re.sub(r'<link rel="stylesheet" href=".*?theme/style\.css">', theme_css, content)
                        content = re.sub(r'<script src=".*?theme/script\.js">', f'<script src="{rel_prefix}theme/script.js">', content)
                    else:
                        # Inject CSS in <head>
                        if '</head>' in content:
                            content = content.replace('</head>', f'    {theme_css}\n</head>')
                        
                        # Inject JS before </body>
                        if '</body>' in content:
                            content = content.replace('</body>', f'{theme_js}\n</body>')
                        else:
                            content += f'\n{theme_js}'
                        
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    inject_theme(r'c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa')

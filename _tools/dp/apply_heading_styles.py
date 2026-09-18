import os
import re

HEADING_CSS = """
        h3 {
            font-size: 1.8rem;
            font-weight: 700;
            color: #111;
            margin-top: 1.5rem;
            margin-bottom: 1.25rem;
        }

        h4 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #111;
            margin-top: 1.25rem;
            margin-bottom: 1rem;
        }

        h5,
        h6 {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111;
            margin-top: 1rem;
            margin-bottom: 0.75rem;
        }
"""

TARGET_FILES = [
    '10sojo.html', '11sozo.html', '12daraku.html', '13shuma.html', '14meshia.html',
    '15fukka.html', '16yotei.html', '17kirisu.html', '20sho.html', '21kidai.html',
    '22mose.html', '23kaku.html', '24douji.html', '25saiko.html', '26sairi.html'
]

DP_DIR = 'c:/malsum/mimune-no-uraniwa/dp'

def apply_heading_styles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if the specific color is applied to h3
    # Use regex to find h3 block and check for color
    h3_match = re.search(r'h3\s*\{([^}]*)\}', content)
    if h3_match and 'color: #111;' in h3_match.group(1):
        print(f"Skipping {os.path.basename(file_path)} (h3 already has color)")
        return

    # Clean up any existing h3, h4, h5, h6 definitions to avoid duplicates
    content = re.sub(r'h3\s*\{[^}]*\}', '', content)
    content = re.sub(r'h4\s*\{[^}]*\}', '', content)
    content = re.sub(r'h5,\s*h6\s*\{[^}]*\}', '', content)
    # Also handle individual h5/h6 if they exist
    content = re.sub(r'h5\s*\{[^}]*\}', '', content)
    content = re.sub(r'h6\s*\{[^}]*\}', '', content)

    # Insert after h2 block or before p block
    if 'h2 {' in content:
        # Find the end of h2 block
        parts = re.split(r'(h2\s*\{[^}]*\})', content)
        if len(parts) > 1:
            content = parts[0] + parts[1] + '\n' + HEADING_CSS + "".join(parts[2:])
    elif 'p {' in content:
        content = content.replace('p {', HEADING_CSS + '\n        p {')
    else:
        content = content.replace('</style>', HEADING_CSS + '</style>')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated heading styles in {os.path.basename(file_path)}")

for filename in TARGET_FILES:
    full_path = os.path.join(DP_DIR, filename)
    if os.path.exists(full_path):
        apply_heading_styles(full_path)

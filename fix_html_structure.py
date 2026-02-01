import os

root_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa"

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check if there is content after </html>
    html_close_idx = -1
    for i, line in enumerate(lines):
        if "</html>" in line:
            html_close_idx = i
            break
    
    if html_close_idx != -1 and html_close_idx < len(lines) - 1:
        # There is content after </html>
        extra_content = lines[html_close_idx + 1:]
        # Remove empty lines from extra content
        extra_content = [l for l in extra_content if l.strip()]
        
        if extra_content:
            print(f"Fixing extra content in: {file_path}")
            
            # Find </body>
            body_close_idx = -1
            for i, line in enumerate(lines):
                if "</body>" in line:
                    body_close_idx = i
                    break
            
            if body_close_idx != -1:
                # Move extra content before </body>
                new_lines = lines[:body_close_idx] + extra_content + lines[body_close_idx:html_close_idx + 1]
                
                # Check for "トップページへ戻る" link and make sure it's at the very bottom
                top_link_start = -1
                top_link_end = -1
                for i, line in enumerate(new_lines):
                    if 'class="nav-links"' in line and 'トップページへ戻る' in "".join(new_lines[i:i+5]):
                        top_link_start = i
                        # Find end of this div
                        for j in range(i, min(i+10, len(new_lines))):
                            if '</div>' in new_lines[j]:
                                top_link_end = j
                                break
                        break
                
                if top_link_start != -1 and top_link_end != -1:
                    # Move it to just before </body>
                    link_lines = new_lines[top_link_start:top_link_end+1]
                    remaining_lines = new_lines[:top_link_start] + new_lines[top_link_end+1:]
                    
                    # Find new </body> position
                    new_body_close_idx = -1
                    for i, line in enumerate(remaining_lines):
                        if "</body>" in line:
                            new_body_close_idx = i
                            break
                    
                    if new_body_close_idx != -1:
                        final_lines = remaining_lines[:new_body_close_idx] + link_lines + remaining_lines[new_body_close_idx:]
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(final_lines)

def main():
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower() == "index.html":
                fix_file(os.path.join(root, file))

if __name__ == "__main__":
    main()

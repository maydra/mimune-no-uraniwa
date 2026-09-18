import os

root_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa"
search_terms = ["トップページ", "トップに戻る", "み旨の裏庭トップ"]

missing_files = []

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.lower() == "index.html":
            file_path = os.path.join(root, file)
            # Skip the root index.html
            if os.path.normpath(file_path) == os.path.normpath(os.path.join(root_dir, "index.html")):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not any(term in content for term in search_terms):
                    missing_files.append(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

print("Files missing the top link:")
for f in missing_files:
    print(f)

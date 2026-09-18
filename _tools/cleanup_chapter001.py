import os
import re

directory = r"C:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\syougairotei_11"

# Pattern to KEEP: chapterXXX_sectionN.html
keep_pattern = re.compile(r"^chapter\d{3}_section\d+\.html$")

# Also keep backups
keep_backups = re.compile(r"^chapter\d{3}\.html\.bak$")

print(f"Cleaning up directory: {directory}")

for filename in os.listdir(directory):
    # Only target chapter related html files
    if filename.startswith("chapter") and filename.endswith(".html"):
        if filename in ["chapter001.html", "chapter002.html", "chapter003.html"]:
             # These should have been deleted by split script, but if they exist, correct to delete them as user requested?
             # User said "chapter001.html is no longer needed".
             # The split script deleted them. If they are there, delete them.
             print(f"Deleting legacy index: {filename}")
             os.remove(os.path.join(directory, filename))
             continue
             
        if not keep_pattern.match(filename):
            print(f"Deleting: {filename}")
            try:
                os.remove(os.path.join(directory, filename))
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

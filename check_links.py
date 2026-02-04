import os
import re

dp_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp"
patterns = [
    r"コリント・[一二三四五六七八九十\d]+章[一二三四五六七八九十\d]+節",
    r"コリント・[一二三四五六七八九十\d]+・[一二三四五六七八九十\d]+"
]

def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all occurrences of the patterns
    all_o = []
    for p in patterns:
        for match in re.finditer(p, content):
            # Check if this match is inside an <a> tag
            # Simple check: see if there's a <a ...> before it without a </a>
            # Better check: check if it's already linked in the style of existing links
            # Actually, the user says "not yet hyperlinked".
            # Usually, the link is on the verse number part.
            # Example: コリント・一〇章<a ...>４</a>節
            # So if the match is "コリント・一〇章４節", and it's NOT linked, it would look like just that.
            
            # Let's see if the match itself or its immediate context contains <a
            start, end = match.span()
            snippet = content[max(0, start-50):min(len(content), end+50)]
            
            # Search for typical link structure: コリント・...<a ...>...</a>
            # If the "コリント" part is there but no <a> for the verse number, it's a hit.
            
            # Let's regex for the whole linked thing and see if this match is part of it.
            # Existing linked style: コリント・[Chapter][章・]<a ...>[Verse]</a>[節]?
            
            is_linked = False
            # Check if there's <a ... class="verse-link" inside or immediately after the chapter part.
            # A common one is: コリント・三・<a ...>16</a>
            # Match would be "コリント・三・16" (if verse is numeric) or "コリント・三・一六"
            
            # Let's just look if <a href=... class="verse-link" is present in the match or within 20 chars after "コリント・".
            if "class=\"verse-link\"" in snippet:
                # Need to be more precise.
                # If the <a> tag is BETWEEN the chapter/dot and the verse number.
                pass
            
            # Let's just find matches that DON'T have <a nearby.
            # Or better, let's find matches and print them with context.
            all_o.append((match.group(), start, end, snippet))

    return all_o

for filename in os.listdir(dp_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(dp_dir, filename)
        matches = check_file(filepath)
        if matches:
            print(f"--- {filename} ---")
            for m, start, end, snippet in matches:
                # Check link presence in snippet
                if "verse-link" not in snippet:
                    print(f"POSSIBLY UNLINKED: {m}")
                    print(f"Context: {snippet.strip()}")
                    print("-" * 20)

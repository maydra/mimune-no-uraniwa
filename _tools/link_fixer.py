
import os
import re
import sys

# Ensure UTF-8 Output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

KANJI_NUMS = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '〇': 0
}

def normalize_width(s):
    """Converts full-width digits/alpha to half-width."""
    return s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))

def kanji_to_int(text):
    if not text:
        return None
    
    # Normalize full-width digits first
    text = normalize_width(text)
    
    if text.isdigit():
        return int(text)
    
    value_chars = ['十', '百']
    is_value_based = any(c in text for c in value_chars)
    
    if is_value_based:
        total = 0
        current = 0
        for char in text:
            if char.isdigit():
                current = current * 10 + int(char)
            elif char in KANJI_NUMS:
                val = KANJI_NUMS[char]
                if val >= 10:
                    if current == 0: current = 1
                    total += current * val
                    current = 0
                else:
                    current = current * 10 + val
        return total + current
    else:
        s = ''
        for char in text:
            if char in KANJI_NUMS: s += str(KANJI_NUMS[char])
            elif char.isdigit(): s += char
        if s: return int(s)
        return 0

DP_MAP = {
    '1': '11sozo.html',
    '2': '12daraku.html',
    '3': '13shuma.html',
    '4': '14meshia.html',
    '5': '15fukka.html',
    '6': '16yotei.html',
    '7': '17kirisu.html',
    'PART2_1': '21kidai.html',
    'PART2_2': '22mose.html',
    'PART2_3': '23kaku.html',
    'PART2_4': '24douji.html',
    'PART2_5': '25saiko.html',
    'PART2_6': '26sairi.html',
    '総序': '10sojo.html',
    '緒論': '20sho.html'
}

SPECIAL_FIX_MAP = {
    '重生論': '17kirisu.html#4-1',
    '三位一体論': '17kirisu.html#4-2',
}

BIBLE_BOOKS = {
    '創世記': ('01_Old Testament', '01_genesis'),
    '創': ('01_Old Testament', '01_genesis'),
    '出エジプト記': ('01_Old Testament', '02_exodus'),
    '出エジプト': ('01_Old Testament', '02_exodus'),
    '出': ('01_Old Testament', '02_exodus'),
    'レビ記': ('01_Old Testament', '03_leviticus'),
    'レビ': ('01_Old Testament', '03_leviticus'),
    '民数記': ('01_Old Testament', '04_numbers'),
    '民': ('01_Old Testament', '04_numbers'),
    '申命記': ('01_Old Testament', '05_deuteronomy'),
    '申': ('01_Old Testament', '05_deuteronomy'),
    'ヨシュア記': ('01_Old Testament', '06_joshua'),
    'ヨシュア': ('01_Old Testament', '06_joshua'),
    '士師記': ('01_Old Testament', '07_judges'),
    '士': ('01_Old Testament', '07_judges'),
    'ルツ記': ('01_Old Testament', '08_ruth'),
    'ルツ': ('01_Old Testament', '08_ruth'),
    'サムエル記上': ('01_Old Testament', '09_1-samuel'),
    'サムエル上': ('01_Old Testament', '09_1-samuel'),
    'サム上': ('01_Old Testament', '09_1-samuel'),
    'サムエル記下': ('01_Old Testament', '10_2-samuel'),
    'サムエル下': ('01_Old Testament', '10_2-samuel'),
    'サム下': ('01_Old Testament', '10_2-samuel'),
    '列王記上': ('01_Old Testament', '11_1-kings'),
    '列王上': ('01_Old Testament', '11_1-kings'),
    '列王記下': ('01_Old Testament', '12_2-kings'),
    '列王下': ('01_Old Testament', '12_2-kings'),
    '歴代誌上': ('01_Old Testament', '13_1-chronicles'),
    '代上': ('01_Old Testament', '13_1-chronicles'),
    '歴代誌下': ('01_Old Testament', '14_2-chronicles'),
    '代下': ('01_Old Testament', '14_2-chronicles'),
    'エズラ記': ('01_Old Testament', '15_ezra'),
    'エズラ': ('01_Old Testament', '15_ezra'),
    'ネヘミヤ記': ('01_Old Testament', '16_nehemiah'),
    'ネヘミヤ': ('01_Old Testament', '16_nehemiah'),
    'エステル記': ('01_Old Testament', '17_esther'),
    'エステル': ('01_Old Testament', '17_esther'),
    'ヨブ記': ('01_Old Testament', '18_job'),
    'ヨブ': ('01_Old Testament', '18_job'),
    '詩篇': ('01_Old Testament', '19_psalms'),
    '詩': ('01_Old Testament', '19_psalms'),
    '箴言': ('01_Old Testament', '20_proverbs'),
    '箴': ('01_Old Testament', '20_proverbs'),
    '伝道の書': ('01_Old Testament', '21_ecclesiastes'),
    '伝道': ('01_Old Testament', '21_ecclesiastes'),
    '伝': ('01_Old Testament', '21_ecclesiastes'),
    '雅歌': ('01_Old Testament', '22_song-of-songs'),
    'イザヤ書': ('01_Old Testament', '23_isaiah'),
    'イザヤ': ('01_Old Testament', '23_isaiah'),
    'エレミヤ書': ('01_Old Testament', '24_jeremiah'),
    'エレミヤ': ('01_Old Testament', '24_jeremiah'),
    '哀歌': ('01_Old Testament', '25_lamentations'),
    'エゼキエル書': ('01_Old Testament', '26_ezekiel'),
    'エゼキエル': ('01_Old Testament', '26_ezekiel'),
    'ダニエル書': ('01_Old Testament', '27_daniel'),
    'ダニエル': ('01_Old Testament', '27_daniel'),
    'ホセア書': ('01_Old Testament', '28_hosea'),
    'ホセア': ('01_Old Testament', '28_hosea'),
    'ヨエル書': ('01_Old Testament', '29_joel'),
    'ヨエル': ('01_Old Testament', '29_joel'),
    'アモス書': ('01_Old Testament', '30_amos'),
    'アモス': ('01_Old Testament', '30_amos'),
    'オバデヤ書': ('01_Old Testament', '31_obadiah'),
    'オバデヤ': ('01_Old Testament', '31_obadiah'),
    'ヨナ書': ('01_Old Testament', '32_jonah'),
    'ヨナ': ('01_Old Testament', '32_jonah'),
    'ミカ書': ('01_Old Testament', '33_micah'),
    'ミカ': ('01_Old Testament', '33_micah'),
    'ナホム書': ('01_Old Testament', '34_nahum'),
    'ナホム': ('01_Old Testament', '34_nahum'),
    'ハバクク書': ('01_Old Testament', '35_habakkuk'),
    'ハバクク': ('01_Old Testament', '35_habakkuk'),
    'ゼパニヤ書': ('01_Old Testament', '36_zephaniah'),
    'ゼパニヤ': ('01_Old Testament', '36_zephaniah'),
    'ハガイ書': ('01_Old Testament', '37_haggai'),
    'ハガイ': ('01_Old Testament', '37_haggai'),
    'ゼカリヤ書': ('01_Old Testament', '38_zechariah'),
    'ゼカリヤ': ('01_Old Testament', '38_zechariah'),
    'マラキ書': ('01_Old Testament', '39_malachi'),
    'マラキ': ('01_Old Testament', '39_malachi'),
    
    'マタイによる福音書': ('02_New Testament', '01_matthew'),
    'マタイ福音書': ('02_New Testament', '01_matthew'),
    'マタイ': ('02_New Testament', '01_matthew'),
    'マルコによる福音書': ('02_New Testament', '02_mark'),
    'マルコ福音書': ('02_New Testament', '02_mark'),
    'マルコ': ('02_New Testament', '02_mark'),
    'ルカによる福音書': ('02_New Testament', '03_luke'),
    'ルカ福音書': ('02_New Testament', '03_luke'),
    'ルカ': ('02_New Testament', '03_luke'),
    'ヨハネによる福音書': ('02_New Testament', '04_john'),
    'ヨハネ福音書': ('02_New Testament', '04_john'),
    'ヨハネ': ('02_New Testament', '04_john'),
    '使徒行伝': ('02_New Testament', '05_acts'),
    '使徒': ('02_New Testament', '05_acts'),
    'ローマ人への手紙': ('02_New Testament', '06_romans'),
    'ロマ書': ('02_New Testament', '06_romans'),
    'ロマ': ('02_New Testament', '06_romans'),
    'コリント人への手紙第一': ('02_New Testament', '07_1-corinthians'),
    'コリント前書': ('02_New Testament', '07_1-corinthians'),
    'コリント前': ('02_New Testament', '07_1-corinthians'),
    'コリント・前': ('02_New Testament', '07_1-corinthians'),
    'コリント・一': ('02_New Testament', '07_1-corinthians'),
    'コリント人への手紙第二': ('02_New Testament', '08_2-corinthians'),
    'コリント後書': ('02_New Testament', '08_2-corinthians'),
    'コリント後': ('02_New Testament', '08_2-corinthians'),
    'コリント・後': ('02_New Testament', '08_2-corinthians'),
    'コリント・二': ('02_New Testament', '08_2-corinthians'),
    'コリント': ('02_New Testament', '07_1-corinthians'), 
    'ガラテヤ人への手紙': ('02_New Testament', '09_galatians'),
    'ガラテヤ書': ('02_New Testament', '09_galatians'),
    'ガラテヤ': ('02_New Testament', '09_galatians'),
    'エペソ人への手紙': ('02_New Testament', '10_ephesians'),
    'エペソ書': ('02_New Testament', '10_ephesians'),
    'エペソ': ('02_New Testament', '10_ephesians'),
    'ピリピ人への手紙': ('02_New Testament', '11_philippians'),
    'ピリピ書': ('02_New Testament', '11_philippians'),
    'ピリピ': ('02_New Testament', '11_philippians'),
    'コロサイ人への手紙': ('02_New Testament', '12_colossians'),
    'コロサイ書': ('02_New Testament', '12_colossians'),
    'コロサイ': ('02_New Testament', '12_colossians'),
    'テサロニケ人への手紙第一': ('02_New Testament', '13_1-thessalonians'),
    'テサロニケ前書': ('02_New Testament', '13_1-thessalonians'),
    'テサロニケ前': ('02_New Testament', '13_1-thessalonians'),
    'テサロニケ人への手紙第二': ('02_New Testament', '14_2-thessalonians'),
    'テサロニケ後書': ('02_New Testament', '14_2-thessalonians'),
    'テサロニケ後': ('02_New Testament', '14_2-thessalonians'),
    'テサロニケ・': ('02_New Testament', '13_1-thessalonians'),
    'テサロニケ': ('02_New Testament', '13_1-thessalonians'),
    'テモテへの手紙第一': ('02_New Testament', '15_1-timothy'),
    'テモテ前書': ('02_New Testament', '15_1-timothy'),
    'テモテ前': ('02_New Testament', '15_1-timothy'),
    'テモテ沒': ('02_New Testament', '15_1-timothy'), 
    'テモテへの手紙第二': ('02_New Testament', '16_2-timothy'),
    'テモテ後書': ('02_New Testament', '16_2-timothy'),
    'テモテ後': ('02_New Testament', '16_2-timothy'),
    'テトスへの手紙': ('02_New Testament', '17_titus'),
    'テトス書': ('02_New Testament', '17_titus'),
    'テトス': ('02_New Testament', '17_titus'),
    'ピレモンへの手紙': ('02_New Testament', '18_philemon'),
    'ピレモン書': ('02_New Testament', '18_philemon'),
    'ピレモン': ('02_New Testament', '18_philemon'),
    'ヘブル人への手紙': ('02_New Testament', '19_hebrews'),
    'ヘブル書': ('02_New Testament', '19_hebrews'),
    'ヘブル': ('02_New Testament', '19_hebrews'),
    'ヤコブの手紙': ('02_New Testament', '20_james'),
    'ヤコブ書': ('02_New Testament', '20_james'),
    'ヤコブ': ('02_New Testament', '20_james'),
    'ペテロの手紙第一': ('02_New Testament', '21_1-peter'),
    'ペテロ前書': ('02_New Testament', '21_1-peter'),
    'ペテロ前': ('02_New Testament', '21_1-peter'),
    'ペテロ': ('02_New Testament', '21_1-peter'),
    'ペテロの手紙第二': ('02_New Testament', '22_2-peter'),
    'ペテロ後書': ('02_New Testament', '22_2-peter'),
    'ペテロ後': ('02_New Testament', '22_2-peter'),
    'ペテロ・': ('02_New Testament', '22_2-peter'), 
    'ヨハネの手紙第一': ('02_New Testament', '23_1-john'),
    'ヨハネ一書': ('02_New Testament', '23_1-john'),
    'ヨハネの手紙第二': ('02_New Testament', '24_2-john'),
    'ヨハネ二書': ('02_New Testament', '24_2-john'),
    'ヨハネの手紙第三': ('02_New Testament', '25_3-john'),
    'ヨハネ三書': ('02_New Testament', '25_3-john'),
    'ユダの手紙': ('02_New Testament', '26_jude'),
    'ユダ書': ('02_New Testament', '26_jude'),
    'ユダ': ('02_New Testament', '26_jude'),
    'ヨハネの黙示録': ('02_New Testament', '27_revelation'),
    'ヨハネ黙示録': ('02_New Testament', '27_revelation'),
    '黙示録': ('02_New Testament', '27_revelation'),
    '黙': ('02_New Testament', '27_revelation'),
}

def scan_headers(dp_dir):
    map_dict = {}
    pattern = re.compile(r'<h[1-6][^>]*id="([^"]+)"[^>]*>(.*?)</h[1-6]>', re.DOTALL | re.IGNORECASE)
    
    for filename in os.listdir(dp_dir):
        if not filename.endswith('.html'): continue
        path = os.path.join(dp_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        matches = pattern.findall(content)
        for mid, mtext in matches:
            clean_text = re.sub(r'<[^>]+>', '', mtext).strip()
            clean_text_ns = clean_text.translate(str.maketrans('', '', ' \t\n\u3000'))
            
            map_dict[clean_text] = f"{filename}#{mid}"
            map_dict[clean_text_ns] = f"{filename}#{mid}"

            sub_match = re.search(r'^[（(][一二三四五六七八九十百0-9]+[）)](.+)$', clean_text_ns)
            if sub_match:
                sub_text = sub_match.group(1)
                map_dict[sub_text] = f"{filename}#{mid}"
    
    for k, v in SPECIAL_FIX_MAP.items():
        map_dict[k] = v
        
    return map_dict

def find_bible_file(base_dir, testament, book_dir, chapter_num):
    dir_path = os.path.join(base_dir, testament, book_dir)
    f3 = f"{chapter_num:03d}.html"
    if os.path.exists(os.path.join(dir_path, f3)): return f3
    f1 = f"{chapter_num}.html"
    if os.path.exists(os.path.join(dir_path, f1)): return f1
    f2 = f"{chapter_num:02d}.html"
    if os.path.exists(os.path.join(dir_path, f2)): return f2
    return f"{chapter_num:03d}.html"

def remove_existing_links(content):
    # Aggressively remove textually formatted links like <a href="...">text</a>
    
    # Standard cleanup for verse links
    pattern = re.compile(r'<a [^>]*href="[^"]*(?:Bible_out|bible_out|BIBLE_OUT)[^"]*"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    old_content = content
    while True:
        new_content = pattern.sub(r'\1', old_content)
        if new_content == old_content:
            break
        old_content = new_content
        
    # Also clean up links that look like Verse Links but might be malformed or old
    # e.g. class="verse-link" or class="toc-bible-link"
    pattern2 = re.compile(r'<a [^>]*class="(?:verse-link|toc-bible-link)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    while True:
        new_content = pattern2.sub(r'\1', old_content)
        if new_content == old_content:
            break
        old_content = new_content
        
    return old_content

def process_dp_files(dp_dir, bible_base_dir, header_map):
    sorted_keys = sorted(BIBLE_BOOKS.keys(), key=lambda x: len(x), reverse=True)
    book_pattern_str = '|'.join(map(re.escape, sorted_keys))
    
    # FULL WIDTH SUPPORT ADDED to Chapter and Verse Capture
    # ADDED '〇' (Zero) to character class for correct parsing of '一〇' (10)
    regex_bible = re.compile(
        f'(?P<bookname>{book_pattern_str}|同)'
        r'(?:[\s\u30fb\uff65\u2022\.]|第)?'
        r'(?P<chapter>[0-9０-９一二三四五六七八九十百〇]+)'
        r'(?:章|篇|[\u30fb\uff65\u2022\.:\s]|第)'
        r'(?:第)?'
        r'(?P<verse>[0-9０-９一二三四五六七八九十百〇]+)節?'
    )
    
    regex_dp = re.compile(r'（(?P<part>前編|後編|本章)?(?:第)?(?P<chap>[一二三四五六七八九十百〇]+)章(?:第)?(?P<sect>[一二三四五六七八九十百〇]+)?節?(?:(?:（|\()(?P<subsect>[一二三四五六七八九十百0-9]+)(?:）|\)))?(?:(?:（|\()(?P<subsub>[0-9]+)(?:）|\)))?）?')
    regex_parens = re.compile(r'（([^）<>]+)）')

    modifications = []

    for filename in os.listdir(dp_dir):
        if not filename.endswith('.html'): continue
        path = os.path.join(dp_dir, filename)
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        clean_content = remove_existing_links(content)
        
        chunks = re.split(r'(<[^>]+>)', clean_content)
        new_chunks = []
        inside_a = False
        last_book_bible = None
        
        for chunk in chunks:
            if not chunk: 
                new_chunks.append(chunk)
                continue
                
            if chunk.startswith('<'):
                tag_lower = chunk.lower()
                if tag_lower.startswith('<a ') or tag_lower.startswith('<a\n'):
                    inside_a = True
                elif tag_lower.startswith('</a>'):
                    inside_a = False
                new_chunks.append(chunk)
                continue
            
            if inside_a:
                new_chunks.append(chunk)
                continue
            
            # TEXT PROCESSING
            processed_chunk = chunk
            
            # 1. BIBLE PROCESSING
            def replace_bible(match):
                nonlocal last_book_bible
                book_str = match.group('bookname')
                chapter_str = match.group('chapter')
                verse_str = match.group('verse')
                
                book_key = None
                
                if book_str == '同':
                    if last_book_bible:
                        book_key = last_book_bible
                    else:
                        return match.group(0)
                else:
                    book_key = book_str
                
                if not book_key or book_key not in BIBLE_BOOKS:
                    return match.group(0)
                
                last_book_bible = book_key
                
                testament, book_dir = BIBLE_BOOKS[book_key]
                chapter_num = kanji_to_int(chapter_str)
                verse_num = kanji_to_int(verse_str)
                
                if not chapter_num or not verse_num:
                    return match.group(0)

                # Special Override for Thessalonians II 2:8
                if book_dir == '13_1-thessalonians' and chapter_num == 2 and verse_num == 8:
                    book_dir = '14_2-thessalonians'

                bible_filename = find_bible_file(bible_base_dir, testament, book_dir, chapter_num)
                url = f"../Bible_out/{testament}/{book_dir}/{bible_filename}#v{verse_num}"
                
                full_match_text = match.group(0)
                v_start = match.start('verse') - match.start(0)
                v_end = match.end('verse') - match.start(0)
                
                prefix = full_match_text[:v_start]
                verse_text = full_match_text[v_start:v_end]
                suffix = full_match_text[v_end:]
                
                # Force RED link
                link = f'<a href="{url}" class="verse-link">{verse_text}</a>'
                result = f"{prefix}{link}{suffix}"
                
                modifications.append(f"Fixed Bible Link: {filename} -> {full_match_text} -> {result} (Url: {url})")
                return result

            processed_chunk = regex_bible.sub(replace_bible, processed_chunk)
            
            # 2. DP REFERENCE PROCESSING
            def replace_dp(match):
                text = match.group(0)
                part = match.group('part')
                chap = match.group('chap')
                sect = match.group('sect')
                subsect = match.group('subsect')
                subsub = match.group('subsub')
                
                file_key = None
                
                if part == '前編':
                    file_key = str(kanji_to_int(chap))
                elif part == '後編':
                    file_key = 'PART2_' + str(kanji_to_int(chap))
                elif part == '本章':
                    target_file = filename
                    anchor = ""
                    if sect:
                        anchor += f"#{kanji_to_int(sect)}"
                        if subsect:
                            anchor += f"-{kanji_to_int(subsect)}"
                            if subsub:
                                anchor += f"-{subsub}"
                    
                    url = f"{target_file}{anchor}"
                    modifications.append(f"Fixed DP Self Link: {filename} -> {text} -> {url}")
                    return f'<a href="{url}">{text}</a>'
                else:
                    return match.group(0)
                
                if file_key and file_key in DP_MAP:
                    target_file = DP_MAP[file_key]
                    anchor = ""
                    if sect:
                        anchor += f"#{kanji_to_int(sect)}"
                        if subsect:
                            anchor += f"-{kanji_to_int(subsect)}"
                            if subsub:
                                anchor += f"-{subsub}"
                    
                    url = f"{target_file}{anchor}"
                    modifications.append(f"Fixed DP Link: {filename} -> {text} -> {url}")
                    return f'<a href="{url}">{text}</a>'
                
                return match.group(0)

            processed_chunk = regex_dp.sub(replace_dp, processed_chunk)
            
            # 3. NAMED REFERENCES
            def replace_named(match):
                full_text = match.group(0)
                inner = match.group(1)
                
                if inner in header_map:
                    url = header_map[inner]
                    modifications.append(f"Fixed Named Link: {filename} -> {full_text} -> {url}")
                    return f'（<a href="{url}">{inner}</a>）'

                key = inner.replace('参照', '').strip()
                if key in header_map:
                    url = header_map[key]
                    modifications.append(f"Fixed Named Link: {filename} -> {full_text} -> {url}")
                    return f'（<a href="{url}">{inner}</a>）'
                
                return full_text
            
            processed_chunk = regex_parens.sub(replace_named, processed_chunk)

            new_chunks.append(processed_chunk)
            
        new_content = ''.join(new_chunks)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

    return modifications

def main():
    dp_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\dp"
    bible_base_dir = r"c:\Users\dream\OneDrive\デスクトップ\Meiryu\mimune-no-uraniwa\Bible_out"
    
    print("Processing files...")
    mods = process_dp_files(dp_dir, bible_base_dir, scan_headers(dp_dir))
    
    print("Done.")
    print("--- REPORT ---")
    print(f"Total modifications: {len(mods)}")
    # Print distinct 50 modifications
    for m in mods[:50]:
        try:
            print(m)
        except Exception:
            pass

if __name__ == "__main__":
    main()

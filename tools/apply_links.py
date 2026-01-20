import re
import os
import urllib.parse
import sys

# more robust way to find the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# tools folder is in the root, so parent of SCRIPT_DIR is the root
BASE_DIR = os.path.dirname(SCRIPT_DIR)

def normalize_digits(s):
    return s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))

def kanji_to_int(s):
    kanji_map = {'〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100}
    if not s: return 0
    if s == '緒': return 0
    
    if '十' not in s and '百' not in s and len(s) > 1:
        res = 0
        for char in s:
            if char in kanji_map:
                res = res * 10 + kanji_map[char]
            else:
                return 0
        return res
        
    res = 0
    temp = 0
    for char in s:
        if char == '十':
            res += (temp if temp > 0 else 1) * 10
            temp = 0
        elif char == '百':
            res += (temp if temp > 0 else 1) * 100
            temp = 0
        else:
            temp = kanji_map.get(char, 0)
    res += temp
    return res

BIBLE_BOOKS = {
    '創': '01_Old Testament/01_genesis', '出': '01_Old Testament/02_exodus', '利': '01_Old Testament/03_leviticus',
    '民': '01_Old Testament/04_numbers', '申': '01_Old Testament/05_deuteronomy', 'ヨシュア': '01_Old Testament/06_joshua',
    '士': '01_Old Testament/07_judges', 'ルツ': '01_Old Testament/08_ruth', 'サ上': '01_Old Testament/09_1-samuel',
    'サ下': '01_Old Testament/10_2-samuel', '列上': '01_Old Testament/11_1-kings', '列下': '01_Old Testament/12_2-kings',
    '代上': '01_Old Testament/13_1-chronicles', '代下': '01_Old Testament/14_2-chronicles', 'エズラ': '01_Old Testament/15_ezra',
    'ネヘミヤ': '01_Old Testament/16_nehemiah', 'エス': '01_Old Testament/17_esther', 'ヨブ': '01_Old Testament/18_job',
    '詩': '01_Old Testament/19_psalms', '箴': '01_Old Testament/20_proverbs', '伝': '01_Old Testament/21_ecclesiastes',
    '雅': '01_Old Testament/22_song-of-songs', 'イザ': '01_Old Testament/23_isaiah', 'エレ': '01_Old Testament/24_jeremiah',
    '哀': '01_Old Testament/25_lamentations', 'エゼ': '01_Old Testament/26_ezekiel', 'ダニ': '01_Old Testament/27_daniel',
    'ホセ': '01_Old Testament/28_hosea', 'ヨエル': '01_Old Testament/29_joel', 'アモ': '01_Old Testament/30_amos',
    'オバ': '01_Old Testament/31_obadiah', 'ヨナ': '01_Old Testament/32_jonah', 'ミカ': '01_Old Testament/33_micah',
    'ナホ': '01_Old Testament/34_nahum', 'ハバ': '01_Old Testament/35_habakkuk', 'ゼパ': '01_Old Testament/36_zephaniah',
    'ハガ': '01_Old Testament/37_haggai', 'ゼカ': '01_Old Testament/38_zechariah', 'マラ': '01_Old Testament/39_malachi',
    'マタイ': '02_New Testament/01_matthew', 'マルコ': '02_New Testament/02_mark', 'ルカ': '02_New Testament/03_luke',
    'ヨハネ': '02_New Testament/04_john', '使徒': '02_New Testament/05_acts', 'ロマ': '02_New Testament/06_romans',
    'コリ前': '02_New Testament/07_1-corinthians', 'コリ後': '02_New Testament/08_2-corinthians', 'ガラ': '02_New Testament/09_galatians',
    'エペソ': '02_New Testament/10_ephesians', 'エペ': '02_New Testament/10_ephesians', 'ピリ': '02_New Testament/11_philippians',
    'コロ': '02_New Testament/12_colossians', 'テサ前': '02_New Testament/13_1-thessalonians', 'テサ後': '02_New Testament/14_2-thessalonians',
    'テモ前': '02_New Testament/15_1-timothy', 'テモ後': '02_New Testament/16_2-timothy', 'テト': '02_New Testament/17_titus',
    'ピレ': '02_New Testament/18_philemon', 'ヘブル': '02_New Testament/19_hebrews', 'ヤコ': '02_New Testament/20_james',
    'ペテ前': '02_New Testament/21_1-peter', 'ペテ後': '02_New Testament/22_2-peter', '一ヨハ': '02_New Testament/23_1-john',
    '二ヨハ': '02_New Testament/24_2-john', '三ヨハ': '02_New Testament/25_3-john', 'ユダ': '02_New Testament/26_jude',
    '黙': '02_New Testament/27_revelation',
}

DP_CHAPTERS = {
    '前編第一章': '11sozo.html', '前編第二章': '12daraku.html', '前編第三章': '13shuma.html',
    '前編第四章': '14meshia.html', '前編第五章': '15fukka.html', '前編第六章': '16yotei.html',
    '前編第七章': '17kirisu.html', '後編緒論': '20sho.html', '後編第一章': '21kidai.html',
    '後編第二章': '22mose.html', '後編第三章': '23kaku.html', '後編第四章': '24douji.html',
    '後編第五章': '25saiko.html', '後編第六章': '26sairi.html', '総序': '10sojo.html',
}

BOOKS_SORTED = sorted(BIBLE_BOOKS.keys(), key=len, reverse=True)
BIBLE_REF_PATTERN = r'(' + '|'.join(re.escape(k) for k in BOOKS_SORTED) + r')([一二三四五六七八九十百〇]+)・([0-9０-９]+(?:[、〜,][0-9０-９]+)*)'
DP_REF_PATTERN = r'(前編|後編|本章|総序)([第一二三四五六七章節緒]+)([^）]*)参照'

def get_bible_filename(path_root, chapter_num):
    # Normalize path_root to use system slashes
    rel_path_to_book = os.path.join(*path_root.split('/'))
    base_path = os.path.join(BASE_DIR, "Bible_out", rel_path_to_book)
    
    file1 = f"{chapter_num}.html"
    file3 = f"{str(chapter_num).zfill(3)}.html"
    
    if os.path.exists(os.path.join(base_path, file3)):
        return file3
    return file1

def linkify_bible_ref(match):
    book_jp = match.group(1)
    chapter_jp = match.group(2)
    verses_str = match.group(3).strip()
    
    path_root = BIBLE_BOOKS.get(book_jp)
    if not path_root: return match.group(0)
    
    chapter_num = kanji_to_int(chapter_jp)
    filename = get_bible_filename(path_root, chapter_num)
    
    # For URL construction, always use /
    path_encoded = '/'.join(urllib.parse.quote(p) for p in path_root.split('/'))
    
    comma_parts = re.split(r'([、,])', verses_str)
    final_parts = []
    for cp in comma_parts:
        if cp in ['、', ',']:
            final_parts.append(cp)
            continue
        
        cp_normalized = normalize_digits(cp)
        if '〜' in cp:
            m = re.match(r'^([0-9]+)(〜[0-9]+)(.*)', cp_normalized)
            if m:
                v_start = m.group(1)
                final_parts.append(f'<a href="../Bible_out/{path_encoded}/{filename}#v{v_start}">{cp}</a>')
            else:
                final_parts.append(cp)
        else:
            m = re.match(r'^([0-9]+)(.*)', cp_normalized)
            if m:
                v_num = m.group(1)
                final_parts.append(f'<a href="../Bible_out/{path_encoded}/{filename}#v{v_num}">{cp}</a>')
            else:
                final_parts.append(cp)
                
    return f'{book_jp}{chapter_jp}・{"".join(final_parts)}'

def linkify_dp_ref(match, current_file):
    prefix = match.group(1)
    detail = match.group(2)
    suffix = match.group(3)
    
    chapter_m = re.search(r'第([一二三四五六七])章', detail)
    section_m = re.search(r'第([一二三四五六七])節', detail)
    
    target_file = None
    if prefix == '本章' or (prefix == '総序' and '章' not in detail):
        if prefix == '本章': target_file = current_file
        else: target_file = '10sojo.html'
    elif prefix in ['前編', '後編']:
        if chapter_m:
            ch_kanji = chapter_m.group(1)
            key = f'{prefix}第{ch_kanji}章'
            target_file = DP_CHAPTERS.get(key)
        elif '緒論' in detail or '緒' in detail:
             target_file = '20sho.html'

    if not target_file: return match.group(0)
    fragment = f"#{kanji_to_int(section_m.group(1))}" if section_m else ""
    return f'<a href="./{target_file}{fragment}">{prefix}{detail}{suffix}参照</a>'

def fix_existing_links(content):
    # Fix existing DP links like #第X節 or #第五節 to #5
    def fix_dp_anchor(m):
        full_match = m.group(0)
        prefix = m.group(1)
        kanji_num = m.group(2)
        suffix = m.group(3)
        num = kanji_to_int(kanji_num)
        return f'{prefix}{num}{suffix}'
    
    pattern = re.compile(r'(href="[^"]*#)第([一二三四五六七])節(")')
    content = pattern.sub(fix_dp_anchor, content)
    
    # Also fix any Bible links that might have been incorrectly created as [1-9].html when they should be [0-9][0-9][0-9].html
    # This is trickier because we need to know the book. 
    # But if we just rerun the process for everything, it might be easier.
    return content

def process_content(content, filename):
    # Fix existing anchors in content
    content = fix_existing_links(content)
    
    def replace_func(m):
        inner = m.group(1)
        
        # If the inner content already contains links, we want to skip or FIX them.
        # However, to avoid complexity, let's first strip existing links for Bible/DP refs 
        # that we recognize, OR just let the script overwrite if the user wants.
        # For now, let's try to detect if it's our link and fix the filename if needed.
        
        # If it's already linked, let's try to fix the anchor or filename inside it.
        if '<a ' in inner:
            # Fix DP anchors inside existing links
            inner = fix_existing_links(inner)
            # Fix Bible filenames inside existing links
            def fix_bible_filename(m_link):
                prefix = m_link.group(1) # <a href="../Bible_out/.../
                path_root_enc = m_link.group(2) # 02_New%20Testament/06_romans
                old_file = m_link.group(3) # 3.html
                suffix = m_link.group(4) # #v10">...
                
                path_root = urllib.parse.unquote(path_root_enc)
                # find chapter num from old_file or suffix? 
                # old_file is like '3.html'
                ch_m = re.match(r'^([0-9]+)\.html$', old_file)
                if ch_m:
                    ch_num = int(ch_m.group(1))
                    new_file = get_bible_filename(path_root, ch_num)
                    return f'{prefix}{path_root_enc}/{new_file}{suffix}'
                return m_link.group(0)

            # Regex for Bible links: href="../Bible_out/(path_root_enc)/(chapter).html(#v123)"
            inner = re.sub(r'(href="\.\./Bible_out/)([^/]+/[^/]+)/([0-9]+\.html)(#[^"]*")', fix_bible_filename, inner)
            return '（' + inner + '）'
        
        new_inner = re.sub(BIBLE_REF_PATTERN, lambda bm: linkify_bible_ref(bm), inner)
        new_inner = re.sub(DP_REF_PATTERN, lambda dm: linkify_dp_ref(dm, filename), new_inner)
        return '（' + new_inner + '）'
    
    return re.sub(r'（([^）]+)）', replace_func, content)

def apply_to_file(file_path):
    print(f"Processing {file_path}...")
    filename = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = process_content(content, filename)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path}")
    else:
        print(f"No changes for {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target):
            apply_to_file(target)
        elif os.path.isdir(target):
            # Sort files to process in consistent order
            for root, dirs, files in os.walk(target):
                for file in sorted(files):
                    if file.endswith('.html'):
                        apply_to_file(os.path.join(root, file))
        else:
            print(f"Error: {target} is not a file or directory.")
    else:
        print("Usage: python apply_links.py <file_path or directory>")

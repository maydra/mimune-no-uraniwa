import os
import json
import re
from bs4 import BeautifulSoup

# 設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "search-index.json")
BASE_URL = "https://maydra.github.io/mimune-no-uraniwa/"

# スキャン対象ディレクトリのリスト
TARGET_DIRS = [
    "peacemessage", "Bible_out", "seikonmondou", "kansha_suru_faith", "tijyouseikatu_reikai",
    "tumito_tougennfukki", "utyu", "utyuuno_konnpon", "tenitikoku", "tensoukan", "tf_inori",
    "syougairotei_1", "syougairotei_2", "syougairotei_3", "syougairotei_4", "syougairotei_5",
    "syougairotei_6", "syougairotei_7", "syougairotei_8", "syougairotei_9", "syougairotei_10",
    "syougairotei_11", "syuku_&_risoutengoku", "syukufuku_katei", "syukufukuto_nyuuseki",
    "syukuga_sennpu", "sokoku_koufuku", "sokokukoufuku_nyuuseki", "souzokutekimesiya",
    "reikon", "reisetutogisiki", "seinenno_kibou", "seiyakujinno_miti", "sekaiheiwa",
    "sensyuu55", "sijyosidou", "sikkutati", "nippon", "niseinomiti", "ouza", "msge",
    "nanboku_heiwa", "nanbokutouitu", "makotonokatei", "makotonokatei-kateimeisei", "malsum",
    "mimuneto_umi", "mimunetosekai", "library", "makotonarusijyonomiti", "makotono_ai",
    "makotono_kami", "makotonofubo", "kann_taiheiyou", "kitou", "kounoseikatu", "kunkyou",
    "kunkyou2", "kyouiku_tetugaku", "heiwa_miti", "heiwasisou", "hitonosyougai", "honkyou",
    "houkansyuu_dansei", "houkansyuu_jyosei", "kamisamaoukensokuisiki", "dendou_hand", "dp",
    "bokkaisyanomiti", "heiwa_sekaijin"
]

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_content(soup):
    # 不要な要素を削除
    for selector in ["nav", "header", "footer", "aside", ".toc", ".sidebar", ".typo-box", "script", "style", "noscript", "iframe"]:
        for tag in soup.select(selector):
            tag.decompose()
    return clean_text(soup.get_text())

index_data = []

# 各ディレクトリをスキャン
for target in TARGET_DIRS:
    target_path = os.path.join(BASE_DIR, target)
    if os.path.exists(target_path):
        print(f"スキャン中: {target}")
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(".html"):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                            soup = BeautifulSoup(f.read(), "html.parser")
                        
                        # タイトル抽出（欠落時はファイル名）
                        if soup.title and soup.title.string:
                            title = soup.title.string.strip()
                        else:
                            title = file
                            
                        text = extract_content(soup)
                        
                        if text:
                            # 相対パスからURLを作成
                            rel_path = os.path.relpath(file_path, BASE_DIR).replace("\\", "/")
                            index_data.append({
                                "url": BASE_URL + rel_path,
                                "title": title,
                                "text": text
                            })
                    except Exception as e:
                        print(f"エラー発生 ({file}): {e}")

# JSON書き出し
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(index_data, f, ensure_ascii=False)

print(f"更新完了！ {len(index_data)} ページを {OUTPUT_FILE} に保存しました。")
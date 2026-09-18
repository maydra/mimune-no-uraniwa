import os
import re
from bs4 import BeautifulSoup

# The goal TOC structure provided by the user
GOAL_STRUCTURE = """序　文

成約のみ言
・救援摂理史の原理観
・宇宙の根本を探して
・真の愛を中心とした真の家庭と真の宇宙
・真の家庭と私

----

『み旨の道』
●一　み旨について
　み旨
　　一　み旨
　　二　善と悪
　復帰・復帰の心情
　指導者
　実践
　　一　伝統
　　二　公義
　　三　責任感
　苦労・祭物・従順
　　一　苦労
　　二　祭物
　　三　従順
　審判
　天国
二　み言・人格・心情について
　み言
　　一　み言
　　二　法度（法律と制度）
　人格
　心情
三　信仰について
　教会・教会生活
　　一　教会・聖地
　　二　生活指導
　　三　カイン・アベル
　信仰生活
　伝　道
　　一　伝道
　　二　信仰の子女
　試験・試練
　説教
　祈祷
　義務守則
四　祝福について
　祝福
　理想相対
　家庭・家庭生活

----

『祝福家庭と理想天国』
第一章　創造理想と男女の愛
第一節　創造理想と人間の堕落
　１.神のみ旨と四位基台完成
　２.愛を通した創造理想実現
　３.アダムとエバを創造された目的
　４.アダムとエバの成長期間
　５.個人完成 and 愛の出発点
　６.アダムとエバを通した創造理想世界
　７.アダムとエバの堕落
　８.堕落の結果
　９.アダムとエバが堕落しなかったならば
第二節　真の男女の愛
　１.創造本然の男女の愛
　２.男性と女性が生まれた理由
　３.互日は絶対的に必要な存在
　４.愛は相対から来る
　５.真の異性観
　６.男性は志操、女性は貞節
　７.愛には発展も革命もない
　８.愛は極めて自然なもの
第三節　真なる結婚と真の愛
　１.結婚の意義
　２.結婚はなぜするのか
　３.真の結婚観
　４、思春期の変化と結婚の適期
　５.勉強と結婚
　６.思春期と初恋
　７.心と体が一致しなければならない
　８.真の愛の完成
　９.真の愛の特権
第四節　愛を中心とした終末の現象
　１.終末とはどのような時か
　２.終末の現象―青少年の堕落
　３.終末におけるサタンの正体
　４.世界的な分裂現象と統一運動
　５.青少年問題と統一教会
　６.真の愛の運動と統一教会
　７.終末における望みの中心

第二章　真の父母と神の家庭
第一節　イエスと祝福
　１.メシヤは誰か
　２.イエス様と祝福
　３.本来のイエス様
　４.イエス様の恨み
　５.イエス様の祝福とキリスト教思想
第二節　小羊の婚宴と最初の復活
　１.小羊の婚宴を通した神様の理想実現
　２.小羊の婚宴の意義
　３.小羊の婚宴は地上で成される
　４.宗教はなぜ、独身生活を強調してきたか
　５.最初の復活にあずかる者
第三節　真の父母と真の子女
　１.真の父母とはどんな方か
　２.真の父母は全体の希望
　３.真의父母は歴史的希望の中心点
　４.人類歴史とは真の父母を迎えるためのもの
　５.偽りの父母と真の父母
　６.統一教会が主張すること
　７.真の父母の息子・娘になろうとすれば
　８.失われた心情を復帰すべき私たち
　９.歴史的な希望の日
第四節　家庭を中心とした復帰摂理
　１.堕落人間の願い
　２.復帰摂理ের 最終目標
　３.家庭を中心とした復帰摂理
　４.復帰の家庭
　５.復帰の家庭になるには
　６.真の家庭主義と真の父母の宗教

第三章　祝福の意義と価値
第一節　新生の根本原理
　１.メシヤが必要な理由
　２.再び生まれることの真の意味
　３.血統転換の意味
　４.重生（新生）しようとすれば
第二節　新生と祝福の起源
　１.イスラエル民族を通した血統転換
　２.イエスと聖霊を通した重生の役事
　３.真の父母と真の子女を通した重生の役事
　４.歴史的犠牲の土台の上に成された祝福
　５.祝福の日は歴史的所願成就の日
第三節　祝福の意義と価値
　１.祝福の意義
　２.祝福の価値
　３.祝福を受けるべき理由
　４.祝福は誰がしてくれるのか
　５.祝福は宇宙全体のためのものである
　６.合同結婚式を挙行する理由
第四節　祝福を受けるための蕩減条件
　１.復活と蕩減条件
　２.蕩減条件は自分自身が立てなければならない
　３.サタン圏（堕落圏）を脱するには
　４.祝福を受けるための基台
　５.祝福を受けるための蕩減条件
　６.祝福を受けるための蕩減期間
　７.修練の過程と七日断食
　８.信仰の三子女
　９.祝福の本来の基準
　10.祝福を受けられる資格基準
　11.祝福を受けられるただ一つの資格
　12.私たちがもつべき信念と姿勢

第四章　祝福の過程
第一節　祝福の相対の決定
　１.祝福の相対は誰が決めるか
　２.自分自身で相対を決定してはいけない
　３.どうすれば理想相対に結ばれるか
　４.相手はどこかにいるものである
　５.相対的に創造された男性と女性
　６.女性の美しさと男性の魅力
　７.女性と化粧
　８.恋愛は絶対許されない
第二節　相対を結ぶ基準と私たちの姿勢
　１.組み合わせてくださるお父様の眼識
　２.極と極の調和を成さなければならない
　３.人間の四つの型と理想 specimen
　４.「目の峠」を越えられなければならない
　５.低くなろうとする者が高くなる
　６.学歴よりもっと重要な条件
　７.結婚は後孫のためにしなければならない
　８.約婚のための真の父母の苦労
第三節　約婚事例
　事例１：自分のために祈祷する者
　事例２：写真結婚
　事例３：ある夫婦の話
　事例４：不具の一人の女性
　事例５：アメリカの精鋭の三人
　事例６：あるオランダ宣教師の信仰
　事例７：蕩減復帰のための祝福
　事例８：六〇〇〇双の約婚時にあったこと
第四節　祝福の過程とその意義
　１.約婚式の意義
　２.聖酒式の成立過程と意義
　３.聖酒伝授の意義
　４.男性と女性の立場と復帰
　５.祝福式の意義
　６.四十日蕩減期間
　７.蕩減棒行事と三日行事
　８.祝福後の三年動員路程
　９.祝福は最後の道である

第五章　完成のための公式路程
第一節　完成期七年公式路程
　１.三時代を一時に蕩減する七年路程
　２.七年大患難と七年路程
　３.祝福を受ける位置は完成した位置ではない
　４.父母の位置を復帰するための七年路程
　５.霊界と肉界を蕩減復帰のための七年期間
　６.ご父母様の七年路程と子女たちの七年路程
　７.個人的七年路程と家庭的七年路程
　８.家庭完成を要する時代
　９.摂理의 先頭에 立べき女性
第二節　再創造のための子女たちの責任分担
　１.再創造時に必要な条件
　２.再創造のための私たちの活動
　３.真の父母の愛の圏を相続するための訓練
　４.万物復帰
　５.神様を痛哭させうる内容
　６.月一人伝道の意義
　７.霊界生活のための地上訓練
第三節　信仰の三子女を通した家庭復帰
　１.信仰の三子女
　２.八人の家族がいなければ復帰できない
　３.信仰の三子女を通した家庭編成
　４.家庭復帰のための公式路程
　５.信仰の子女と直系子女の関係
　６.復帰された父母の立場に立とうとすれば
　７.信仰の父母の使命と愛の公式

第六章　ご父母様の聖婚と祝福家庭
第一節　ご父母様の聖婚と七年路程
　１.患難と迫害の最高峰になった聖婚式
　２.三弟子を先に探し立てたご父母様の聖婚式
　３.父母が責任をもち開拓する時代
　４.ご父母様の家庭的十字架路程
　５.お母様を通した七年路程
　６.一九六〇年代の摂理的標語
　７.三六、七二、一二四家庭の祝福
　８.失った日々を探し立てた期間
第二節　祝福家庭に対する摂理的意義
　１.第三イスラエルの意義
　２.祝福家庭を通した第三イスラエル圏の編成
　３.三六家庭祝福の摂理的意義
　４.七二家庭祝福の摂理的意義
　５.一二四家庭祝福の摂理적 意義
　６.四三〇家庭祝福の摂理的意義
　７.七七七家庭祝福の摂理的意義
　８.一八〇〇家庭祝福の意義
　９.六〇〇〇家庭祝福の意義
第三節　祝福家庭の価値と使命
　１.祝福家庭の価値
　２.祝福家庭은 ご父母様의 指導를 受けなければならない
　３.祝福をしてくださった理由
　４.祝福家庭의 使命과 責任
　５.祭司長の使命を果たすべき祝福家庭
　６.三時代の使命に責任を負うべき祝福家庭
　７.氏族的メシヤとなれ
　８.既成祝福家庭의 使命
　９.祝福家庭が行くべき必然的運命の道
　10.祝福を受けた夫婦が行くべき道
　11.世界的な家庭的カナン復帰
　12.新しい時代の主人になる者
第四節　国際祝福家庭の使命
　１.神様を中心とした一つの世界主義
　２.すべての人類は一つの兄弟、一つの家族
　３.国際合同結婚式의 意義
　４.東西文明の差異と国際結婚
　５.国際結婚時代의 開幕
　６.国際祝福家庭の使命

第七章　真の夫婦と理想家庭
第一節　真の夫婦
　１.創造本然의 夫婦関係
　２.復帰されるべき真の夫婦の理想
　３.祝福を受けた夫婦の立場
　４.理想的夫婦
　５.夫婦の愛
　６.夫婦の運命の道
　７.愛する人が死ねばなぜ悲しいか
　８.真の夫婦の協助
第二節　理想家庭
　１.理想家庭
　２.三時代が連結されている家庭
　３.家庭은 真의 愛의 訓練道場
　４.家庭は天宙主義を完成する最終基準
　５.息子・娘をなぜひねばならないか
　６.祝福子女의 価値
　７.家庭天国
　８.天国に入る秘訣
第三節　祝福家庭의 生活
　１.手本のとなるべき祝福家庭
　２.祝福家庭의 家庭生活
　３.祝福家庭의 夫婦生活
　４.祝福家庭의 み旨에 かなう 生活
　５.祝福家庭의 信仰生活
　６.祝福家庭의 侍る 生活
　７.三位基台を中心とした生活
　８.祝福家庭의 共同生活
　９.後孫が福を受ける道
　10.死ぬときも四位基台をえなければならない
第四節　真なる父母と子女
　１.真なる父母と子女
　２.真なる子女의 道理
　３.伝統を相続してあげる父母となろう
　４.子女に対する父母の愛
　５.子供は父母의 愛를 受けなければならない
　６.愛のむち
　７.後孫のために精誠を尽くそう
第五節　子女教育
　１.家庭教育
　２.真なる子女教育
　３.真なる愛国教育
　４.世界と共に生きることのできる教育
　５.信仰と勉強
　６.愛は学んで分かるものではない
　７.愛を中心とした人生行路"""

def normalize(text):
    """Normalize text for cross-referencing."""
    text = text.replace('・', '').replace('　', '').replace(' ', '')
    text = text.replace('(', '（').replace(')', '）')
    # Use only alphanumeric and Japanese/Korean chars
    text = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]', '', text)
    # Remove honorifics and common glue words for flexibility
    text = text.replace('様', '').replace('and', '').replace('と', '').replace('the', '')
    return text

def build_lookup():
    """Scan all HTML files to build a mapping of normalized text -> (file, anchor)."""
    base_dir = r'c:\malsum\mimune-no-uraniwa\syuku_&_risoutengoku'
    lookup = {}
    
    html_files = [f for f in sorted(os.listdir(base_dir)) if f.endswith('.html') and f != 'index.html']
    
    for filename in html_files:
        path = os.path.join(base_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # 1. Search in TOC
            toc = soup.find('div', id='toc') or soup.find('div', class_='toc')
            if toc:
                for a in toc.find_all('a'):
                    href = a.get('href')
                    if href and href.startswith('#'):
                        norm = normalize(a.get_text())
                        if norm and norm not in lookup:
                            lookup[norm] = (filename, href[1:])
            
            # 2. Search all elements with IDs
            for el in soup.find_all(id=True):
                text = el.get_text().strip()
                if not text:
                    text = el.find_next_sibling(string=True)
                    if not text: continue
                norm = normalize(text)
                if norm and norm not in lookup:
                    lookup[norm] = (filename, el['id'])
                    
    return lookup

def parse_input_structure():
    lines = GOAL_STRUCTURE.split('\n')
    parsed = []
    
    for line in lines:
        if line.strip() == '----':
            parsed.append({'type': 'sep'})
            continue
        if line.strip().startswith('＊＊＊') or line.strip() == '':
            continue
            
        match = re.match(r'^([ 　\t]*)', line)
        indent_str = match.group(1) if match else ""
        indent_val = indent_str.count('\u3000') + (indent_str.count(' ') // 2) + indent_str.count('\t')
        
        text = line.strip()
        is_segment = text.startswith('『') and text.endswith('』')
        
        # Determine if it's a Section Title pattern
        # Handles: 第一節, 第一章, ●一, 二, 三, 四
        is_section_title = bool(re.match(r'^[●○・]?[第一二三四五六七八九十0-9]+[章節　]', text))
        
        parsed.append({
            'type': 'entry',
            'text': text,
            'level': indent_val,
            'is_segment': is_segment,
            'is_section_title': is_section_title
        })
    return parsed

def main():
    lookup = build_lookup()
    structure = parse_input_structure()
    
    final_items = []
    
    # Second pass for anchor synchronization (minus 1 logic)
    for i in range(len(structure)):
        item = structure[i]
        if item['type'] == 'sep':
            final_items.append('<hr class="toc-sep">')
            continue
            
        text = item['text']
        level = item['level']
        is_segment = item['is_segment']
        
        norm = normalize(text)
        link_dest = lookup.get(norm)
        
        # Dead Header Link Fix: 
        if (item.get('is_section_title') or is_segment) and i + 1 < len(structure):
            next_item = structure[i+1]
            next_norm = normalize(next_item['text'])
            next_dest = lookup.get(next_norm)
            
            if next_dest:
                fname, anchor = next_dest
                if anchor and anchor.isdigit():
                    new_anchor = str(int(anchor) - 1).zfill(len(anchor))
                    link_dest = (fname, new_anchor)

        # Special Case Manual Fixes
        if text == "４、思春期の変化と結婚の適期":
            link_dest = ("011.html", "006")
        elif text == "序　文":
            link_dest = ("hajimeni.html", None)
        elif text == "成約のみ言":
            link_dest = ("001.html", "001")
        elif text == "●一　み旨について":
            link_dest = ("002.html", "002")
            
        href = ""
        if link_dest:
            filename, anchor = link_dest
            href = f'{filename}' + (f'#{anchor}' if anchor else '')
            
        classes = [f'level-{level}']
        if is_segment: classes.append('segment-title')
            
        class_attr = ' '.join(classes)
        
        content = text
        if href:
            content = f'<a href="{href}">{text}</a>'
            
        final_items.append(f'<div class="{class_attr}">{content}</div>')

    toc_body = "\n".join(final_items)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>祝福家庭と理想天国 - 全目次</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700;900&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="../theme/style.css">
    <style>
        /* Specific TOC Layout Overrides */
        body {{
            padding: 4rem 1.5rem;
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4rem;
            border-bottom: 2px solid var(--link-color);
            padding-bottom: 1rem;
        }}
        h1 {{ font-size: 1.8rem; font-weight: 900; letter-spacing: 0.1em; }}
        h1 a {{ color: inherit !important; text-decoration: none !important; }}
        
        .toc-body {{ margin-bottom: 5rem; }}
        
        .level-0 {{ font-size: 1.25rem; font-weight: 700; margin-top: 1.8rem; position: relative; }}
        .level-1 {{ padding-left: 2rem; font-size: 1.1rem; font-weight: 500; margin-top: 0.8rem; }}
        .level-2 {{ padding-left: 4.5rem; font-size: 1rem; opacity: 0.9; margin-top: 0.4rem; }}
        .level-3 {{ padding-left: 7rem; font-size: 0.95rem; opacity: 0.8; margin-top: 0.3rem; }}
        
        .segment-title {{
            font-size: 1.6rem;
            text-align: center;
            margin: 5rem 0 3rem;
            letter-spacing: 0.15em;
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--card-border);
        }}
        .segment-title a {{ border-bottom: none !important; }}
        
        .toc-sep {{ border: none; border-top: 1px solid var(--card-border); margin: 6rem 0; opacity: 0.5; }}
        
        /* Level Symbols */
        .level-0 > a::before {{ content: '●'; font-size: 0.8em; margin-right: 0.6rem; color: var(--link-color); }}
        .level-0:not(.segment-title) > a::before {{ content: '●'; }}
        .level-1 > a::before {{ content: '○'; font-size: 0.8em; margin-right: 0.6rem; vertical-align: middle; }}
        .level-2 > a::before {{ content: '・'; font-size: 1.0em; margin-right: 0.4rem; vertical-align: middle; }}

        .footer {{ text-align: center; border-top: 1px solid var(--card-border); padding-top: 3rem; margin-top: 5rem; }}
        .footer-link {{ 
            display: inline-block; 
            margin: 0.5rem; 
            font-size: 0.95rem; 
            border: 1px solid var(--card-border); 
            padding: 0.8rem 1.8rem; 
            border-radius: 50px; 
            transition: 0.3s;
            text-decoration: none !important;
            background: var(--card-bg);
        }}
        .footer-link:hover {{ border-color: var(--link-color); transform: translateY(-2px); }}
        
        a {{ transition: 0.2s; }}
        a:hover {{ transform: translateX(4px); }}

        @media (max-width: 600px) {{
            body {{ padding: 2rem 1rem; }}
            .level-1 {{ padding-left: 1rem; }}
            .level-2 {{ padding-left: 2rem; }}
            .level-3 {{ padding-left: 3rem; }}
            h1 {{ font-size: 1.4rem; }}
        }}
    </style>
</head>
<body class="dark-mode">
<div class="container">
    <header>
        <h1><a href="index.html">祝福家庭と理想天国</a></h1>
    </header>

    <div class="toc-body">
        {toc_body}
    </div>

    <div class="footer">
        <a href="https://maydra.github.io/mimune-no-uraniwa/index.html" class="footer-link">み旨の裏庭トップ</a>
        <a href="random.html" class="footer-link">📖 今日の御言をランダム表示</a>
    </div>
</div>

<script src="../theme/script.js"></script>
</body>
</html>
"""
    
    output_path = r'c:\malsum\mimune-no-uraniwa\syuku_&_risoutengoku\index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Successfully updated {output_path}")

if __name__ == "__main__":
    main()

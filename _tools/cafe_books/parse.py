# raw/<FLD>/*.html から記事の題と段落を取り出して raw/<FLD>.jsonl に書く
#   python -X utf8 _tools/cafe_books/parse.py VWMp VS04 VyWS
# 段落ごとに text・太字か・色（見出しの見分けに使う）を残す
import os, re, sys, json, html as H
from html.parser import HTMLParser
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw')

class Article(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0          # div#article の中の div の深さ（0 は外）
        self.paras = []
        self.cur = None
        self.bold = 0
        self.colors = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth == 0:
            if tag == 'div' and a.get('id') == 'article':
                self.depth = 1
            return
        if tag == 'div':
            self.depth += 1
        elif tag == 'p':
            self.cur = {'text': '', 'bold': False, 'colors': set()}
        elif tag == 'br' and self.cur is not None:
            self.cur['text'] += '\n'
        elif tag in ('b', 'strong'):
            self.bold += 1
        elif tag == 'span':
            m = re.search(r'color:\s*(#[0-9a-fA-F]{6})', a.get('style') or '')
            self.colors.append(m.group(1).lower() if m else None)
    def handle_endtag(self, tag):
        if self.depth == 0:
            return
        if tag == 'div':
            self.depth -= 1
        elif tag == 'p' and self.cur is not None:
            t = self.cur['text'].replace('\u00a0', ' ').replace('\u200b', '')
            t = '\n'.join(s.strip() for s in t.split('\n')).strip()
            if t:
                self.paras.append({'text': t, 'bold': self.cur['bold'],
                                   'colors': sorted(self.cur['colors'])})
            self.cur = None
        elif tag in ('b', 'strong'):
            self.bold = max(0, self.bold - 1)
        elif tag == 'span' and self.colors:
            self.colors.pop()
    def handle_data(self, data):
        if self.depth and self.cur is not None and data.strip():
            self.cur['text'] += data
            if self.bold:
                self.cur['bold'] = True
            c = next((c for c in reversed(self.colors) if c), None)
            if c:
                self.cur['colors'].add(c)

for fld in sys.argv[1:]:
    raw = os.path.join(ROOT, fld)
    nums = sorted(int(f[:-5]) for f in os.listdir(raw) if f.endswith('.html'))
    out = open(os.path.join(ROOT, f'{fld}.jsonl'), 'w', encoding='utf-8')
    for n in nums:
        h = open(os.path.join(raw, f'{n}.html'), encoding='utf-8').read()
        m = re.search(r'<h3 class="tit_subject">(.*?)</h3>', h, re.S) or re.search(r'property="og:title" content="(.*?)"', h)
        title = H.unescape(re.sub(r'<[^>]+>|\s+', ' ', m.group(1))).strip() if m else ''
        p = Article(); p.feed(h)
        paras = p.paras
        # 平和経の第五篇 22〜28 は PDF を HTML にしたものを貼ってあり、<p> が無い。<div class="t …"> 1つが1段落
        if sum(len(x['text']) for x in paras) < 200 and '<div class="t ' in h:
            body = re.search(r'tx-content-container">(.*?)<script', h, re.S).group(1)
            paras = []
            # div の外にも題・日付の行がある（28）。外の部分は <br>・<p>・<div> で行に分ける
            for i, d in enumerate(re.split(r'<div class="t [^"]*">(.*?)</div>', body, flags=re.S)):
                if i % 2 == 0:
                    d = re.sub(r'<br\s*/?>|</?p[^>]*>|</?div[^>]*>', '\n', d)
                for t in (d.split('\n') if i % 2 == 0 else [re.sub(r'<br\s*/?>', '', d)]):
                    t = H.unescape(re.sub(r'<[^>]+>', '', t)).replace(' ', ' ').strip()
                    if t:
                        paras.append({'text': t, 'bold': False, 'colors': [], 'pdf': True})
        # 平和経の第五篇 21 は1つの <p> に、行の幅で折り返した行が空行1つ置きに並ぶ（段落の切れ目は空行3つ）
        fixed = []
        for x in paras:
            if x['text'].count('\n\n') > 20:
                for t in re.split(r'\n{4,}', x['text']):
                    fixed.append(dict(x, text=re.sub(r'\n+', '', t).strip(), pdf=True))
            else:
                fixed.append(x)
        paras = [x for x in fixed if x['text']]
        out.write(json.dumps({'n': n, 'title': title, 'paras': paras}, ensure_ascii=False) + '\n')
    out.close()
    print(fld, len(nums), 'articles')

# 英語の固有名詞が出る段落で、日本語のカタカナ語・韓国語の語頭がどれだけそろって出るかを数える（人名・地名の対応探し）
#   python -X utf8 cooc.py "Abraham"
import json, sys, os, re, collections
rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rows.json'), encoding='utf-8'))
q = sys.argv[1]
pat = re.compile(r'\b' + re.escape(q) + r'\b')
hit = [v for v in rows.values() if pat.search(v[2])]
print(len(hit), 'rows contain', q)
ja = collections.Counter(); ko = collections.Counter()
ja_df = collections.Counter(); ko_df = collections.Counter()
def ja_words(s):
    return set(re.findall(r'[ァ-ヴー・]{2,}|[一-龥]{1,4}[ァ-ヴー]{2,}|[ァ-ヴー]{2,}[一-龥]{1,3}', s))
def ko_words(s):
    out = set()
    for w in re.findall(r'[가-힣]+', s):
        for L in range(2, min(len(w), 7) + 1):
            out.add(w[:L])
    return out
for v in rows.values():
    ja_df.update(ja_words(v[1])); ko_df.update(ko_words(v[0]))
for v in hit:
    ja.update(ja_words(v[1])); ko.update(ko_words(v[0]))
def top(c, df):
    sc = [(2 * a / (len(hit) + df[w]), w, a, df[w]) for w, a in c.items() if a >= max(1, len(hit) * 0.3)]
    sc.sort(reverse=True)
    return ' | '.join('%s(%d/%d)' % (w, a, b) for s, w, a, b in sc[:6])
print('JA', top(ja, ja_df))
print('KO', top(ko, ko_df))

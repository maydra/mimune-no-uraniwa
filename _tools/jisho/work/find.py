# 原理講論の三か国語の段落を引く道具
#   python -X utf8 find.py row 1-1-1:3          … その段落の韓・日・英を全部出す
#   python -X utf8 find.py ja 復帰摂理 [件数]    … 日本語にその字句がある段落（英語の頭も出す）
#   python -X utf8 find.py ko 복귀섭리 [件数]
#   python -X utf8 find.py en "providence of restoration" [件数]   （英語は大文字小文字を区別しない）
#   python -X utf8 find.py count ja|ko|en 字句  … 何段落に出るか
import json, sys, os
rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rows.json'), encoding='utf-8'))
L = {'ko': 0, 'ja': 1, 'en': 2}
cmd = sys.argv[1]
if cmd == 'row':
    ko, ja, en = rows[sys.argv[2]]
    print('[KO]', ko, '\n[JA]', ja, '\n[EN]', en)
elif cmd == 'count':
    lang, q = sys.argv[2], sys.argv[3]
    n = sum(1 for v in rows.values() if (q.lower() in v[2].lower() if lang == 'en' else q in v[L[lang]]))
    print(n)
else:
    lang, q = cmd, sys.argv[2]
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    hits = [(k, v) for k, v in rows.items() if (q.lower() in v[2].lower() if lang == 'en' else q in v[L[lang]])]
    print(len(hits), 'rows')
    for k, v in hits[:lim]:
        t = v[L[lang]]
        i = t.lower().find(q.lower()) if lang == 'en' else t.find(q)
        print('---', k)
        for name, j in (('KO', 0), ('JA', 1), ('EN', 2)):
            s = v[j]
            if j == L[lang]:
                print('[%s] …%s…' % (name, s[max(0, i - 80): i + len(q) + 80]))
            else:
                print('[%s] %s' % (name, s[:400] + ('…' if len(s) > 400 else '')))

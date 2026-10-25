# 原理講論の日本語（対訳のデータ）に付いているルビを集める
import json, re, glob, os, sys, collections
D = sys.argv[1]
ruby = collections.defaultdict(collections.Counter)
for f in glob.glob(os.path.join(D, 'data', '*.js')):
    t = open(f, encoding='utf-8').read().replace('\\"', '"')
    for m in re.finditer(r'<ruby>((?:(?!</?ruby>).)*?)<rt>([^<]+)</rt>', t):
        base = re.sub(r'<[^>]+>', '', m.group(1))
        ruby[base][m.group(2)] += 1
json.dump({k: v.most_common(1)[0][0] for k, v in ruby.items()}, open('ruby.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(ruby))

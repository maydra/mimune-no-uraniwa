import json
import os

with open('audit_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

s5 = results.get('syougairotei_5', [])
matches = [x for x in s5 if '0286' in x['old']]
print(json.dumps(matches, indent=2, ensure_ascii=False))

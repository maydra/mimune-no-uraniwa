"""seika/hangul-yomi.js（読みを付ける道具の変換）が、hangul_kana.py と同じ読みを出すか確かめる

    python -I -X utf8 _tools/seika/check_yomi_js.py

全曲の歌のファイルに出てくる語と、規則ごとの例の語を両方で変換して比べる。node が要る。
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hangul_kana import to_kana, to_roman  # noqa: E402

EXAMPLES = ("받들어 빛나네 찬란히 약속함의 같이 좋아 많다 싫어 읽어 없어 앉아 국립 신라 설날 합니다 굳이 "
            "놓는 학교 젊은 닮고 맑게 밟히다 넓게 의사 회의 계시다 차례 쉬어 뒤에 영광을 꽃동산을 뚫는 앉히다").split()

words = set(EXAMPLES)
for f in (HERE / "songs").glob("*.txt"):
    for w in re.findall(r"[가-힣]+", f.read_text(encoding="utf-8")):
        words.add(w)
words = sorted(words)
expect = {w: [to_kana(w), to_roman(w)] for w in words}

js = (HERE.parents[1] / "seika" / "hangul-yomi.js").as_posix()
script = (
    "const y = require(" + json.dumps(js) + ");"
    "let s = '';process.stdin.on('data', d => s += d).on('end', () => {"
    "const out = {}; for (const w of JSON.parse(s)) out[w] = [y.toKana(w), y.toRoman(w)];"
    "process.stdout.write(JSON.stringify(out)); });"
)
res = subprocess.run(["node", "-e", script], input=json.dumps(words), capture_output=True, text=True, encoding="utf-8")
if res.returncode:
    sys.exit(res.stderr)
got = json.loads(res.stdout)
bad = [(w, expect[w], got[w]) for w in words if expect[w] != got[w]]
print(f"{len(words)} words, {len(bad)} differ")
for w, e, g in bad[:30]:
    print(w, "python", e, "js", g)
sys.exit(1 if bad else 0)

"""割り振り表を更新する。 nextgroups.py done=G1,G2 start=N
done の組を「済」にし、「未」の組を上から N 個「描いている」にして、その担当の文字列を出す"""
import json, re, sys
args = dict(a.split("=", 1) for a in sys.argv[1:])
done = [x for x in args.get("done", "").split(",") if x]
n = int(args.get("start", "0"))
p = "assign.md"; s = open(p, encoding="utf-8").read()
for g in done:
    s = re.sub(rf"(\| {g} \|[^\n]*\| )\S+( \|)", r"\1済\2", s)
groups = json.load(open("groups_kou.json", encoding="utf-8"))
started = []
for m in re.finditer(r"\| (\S+) \| (\S+) \| [^|]+ \| 未 \|", s):
    if len(started) >= n: break
    started.append(m.group(1))
for g in started:
    s = re.sub(rf"(\| {g} \|[^\n]*\| )未( \|)", r"\1描いている\2", s)
open(p, "w", encoding="utf-8").write(s)
for g in started:
    v = groups[g]
    print(g, v["page"], " ".join(f"{i}={img}" + ("" if sz == [822, 435] else f"({sz[0]}x{sz[1]})") for i, img, sz in v["charts"]))
print("未:", len(re.findall(r"\| 未 \|", s)), "描いている:", len(re.findall(r"\| 描いている \|", s)), "済:", len(re.findall(r"\| 済 \|", s)))

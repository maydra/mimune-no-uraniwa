"""聖歌集（ハングル）の曲と、YouTube の動画を突き合わせる → videos.tsv

    python -I -X utf8 _tools/seika/match_videos.py

元のデータ（yt-dlp --flat-playlist で取った題の一覧）:
  youtube/playlist_ja.tsv   日本語歌詞の聖歌の再生リスト（題が「聖歌5番：勝利者の新歌」）
  youtube/channel_ruby.tsv  @kyungboonpark9875 のルビ入りの歌（題が「勝利者の新歌 ルビ入り (승리자의 새 노래)」）

日本の聖歌は番号の付け方が違う（ハングルの1番「승리자의 새 노래」が日本の5番）。
番号ではなく題で、ハングルの題 → チャンネルの動画（日本語の題も入っている）→ 日本の聖歌の番号、とたどる。
題が揺れていて機械で当たらないものは、下の MANUAL に書く。
"""

import csv
import difflib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANGUL_RUN = re.compile(r"[가-힣][가-힣 ]*[가-힣]|[가-힣]")

# ハングルの曲番号 → 日本の聖歌の番号（題の訳が違って機械で当たらないもの）
MANUAL_JA = {
    # 次の2曲は、日本の聖歌の歌詞（ja_official.json）と1節目を読み比べて同じ歌と確かめた
    "16": "2部2",   # 한숨을 걷어차라（チャンネルは「ため息を蹴飛ばそう」、日本の聖歌は「嘆きを吹きとばせ」。冬の木枯らし→春風）
    "45": "2部4",   # 동산의 봄노래（チャンネルに日本語の題が無い。오너라 동무야 동산의 봄은＝来たれ友よ園の春は）
    "44": "38",     # 생명시냇가에 살겠네（チャンネルの題が「生命と泉の磅」と誤字。日本の聖歌「生命の泉のほとり」）
}
# ハングルの曲番号 → チャンネルの動画（ハングルの題が聖歌集と違うもの）
MANUAL_RUBY = {
    "51": ["0qBakgvI5L4"],  # 통일 노래 = 「統一の歌 ルビ入り (우리의 소원)」
}


def norm_ko(s):
    return re.sub(r"\s+", "", s)


def norm_ja(s):
    s = re.sub(r"ルビ入り|※広告なし|[\s　・]", "", s)
    return s


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n").split("\t") for line in f if line.strip()]


def parse_channel(rows):
    out = []
    for _idx, vid, title in rows:
        accomp = "반주" in title or "伴奏" in title
        t = re.sub(r"-?\s*반주\s*\(伴奏\)", "", title)
        kos = HANGUL_RUN.findall(t)
        ko = max(kos, key=len) if kos else ""
        ja = t
        for k in kos:
            ja = ja.replace(k, " ")
        ja = re.sub(r"ルビ入り|[()（）\[\]\-–]|韓\.日|歌詞|日本語|韓国語", " ", ja)
        ja = re.sub(r"\s+", " ", ja).strip()
        out.append({"id": vid, "title": title, "ko": ko, "ja": ja, "accomp": accomp})
    return out


def parse_playlist(rows):
    out = []
    for _idx, vid, title in rows:
        m = re.match(r"聖歌((?:2部)?\d+)番：(.+?)(?:（([AB])）)?(?:\s*※広告なし)?$", title)
        if m:
            out.append({"id": vid, "no": m.group(1), "ja": m.group(2).strip(), "ab": m.group(3) or ""})
    return out


def main():
    songs = list(csv.DictReader(open(HERE / "songs_index.tsv", encoding="utf-8"), delimiter="\t"))
    chan = parse_channel(read_tsv(HERE / "youtube" / "channel_ruby.tsv"))
    plist = parse_playlist(read_tsv(HERE / "youtube" / "playlist_ja.tsv"))
    by_ja = {}
    for p in plist:
        by_ja.setdefault(norm_ja(p["ja"]), []).append(p)

    rows = []
    for s in songs:
        key = norm_ko(s["ko"])
        hits = [c for c in chan if norm_ko(c["ko"]) == key]
        if s["no"] in MANUAL_RUBY:
            hits = [c for c in chan if c["id"] in MANUAL_RUBY[s["no"]]]
        elif not hits:  # 題の綴りの揺れ（띄어쓰기・括弧の中だけ違う など）
            cand = {norm_ko(c["ko"]): c for c in chan if c["ko"]}
            close = difflib.get_close_matches(key, list(cand), n=1, cutoff=0.8)
            if close:
                hits = [c for c in chan if norm_ko(c["ko"]) == close[0]]
        sing = [c for c in hits if not c["accomp"]]
        acc = [c for c in hits if c["accomp"]]
        ja_titles = [c["ja"] for c in hits if c["ja"]]

        ja = []
        how = ""
        if s["no"] in MANUAL_JA:
            ja = [p for p in plist if p["no"] == MANUAL_JA[s["no"]]]
            how = "手で"
        else:
            for t in ja_titles:
                k = norm_ja(t)
                # 日本語の題は完全に一致したときだけ。近い題で当てると
                # 「農園の歌」が「園の歌」に当たってしまう
                if k in by_ja:
                    ja = by_ja[k]
                    how = "題"
                    break
        rows.append({
            "no": s["no"], "ko": s["ko"],
            "ja_no": ja[0]["no"] if ja else "",
            "ja_title": ja[0]["ja"] if ja else (ja_titles[0] if ja_titles else ""),
            "ja_video": " ".join(p["id"] + (f"({p['ab']})" if p["ab"] else "") for p in ja),
            "ruby_video": " ".join(c["id"] for c in sing),
            "ruby_accomp": " ".join(c["id"] for c in acc),
            "how": how,
        })

    cols = ["no", "ko", "ja_no", "ja_title", "ja_video", "ruby_video", "ruby_accomp", "how"]
    with open(HERE / "videos.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(r[c] for c in cols) + "\n")
    for r in rows:
        print("\t".join(r[c] for c in cols))


if __name__ == "__main__":
    main()

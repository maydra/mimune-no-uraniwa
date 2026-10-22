"""ハングルの語（分かち書きの1区切り）を、発音どおりのカタカナにする。

聖歌のルビ用。綴りではなく実際の音（標準発音）を写す:
  連音化（받들어 → 받드러）、鼻音化（빛나 → 빈나）、流音化（찬란 → 찰란）、
  激音化（약속함 → 약소캄）、濃音化（받들 → 받뜰）、口蓋音化（같이 → 가치）、
  ㅎ の脱落（좋아 → 조아）、助詞の 의 は 에、語中の 의 は 이。

パッチムは家庭盟誓のページと同じく小さいカナで書く: ㄱ→ㇰ ㄴ→ン ㄷ→ッ ㄹ→ㇽ
ㅁ→ㇺ ㅂ→ㇷ゚ ㅇ→ン。濃音（ㄲ ㄸ ㅃ ㅆ ㅉ）は前にパッチムが無いとき「ッ」を付ける。

漢字語の ㄹ の後の濃音化（절대 → 절때）、合成語の濁らない音（꽃동산）、
ㄴ の添加（솜이불 → 솜니불）は綴りからは分からないので、歌のファイルで
語{カナ} と書いて直す。
"""

import re

CHO = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONG = [""] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")

# 母音 → 表の列
VOWEL = {
    "ㅏ": "a", "ㅐ": "e", "ㅑ": "ya", "ㅒ": "ye", "ㅓ": "o", "ㅔ": "e",
    "ㅕ": "yo", "ㅖ": "ye", "ㅗ": "o", "ㅘ": "wa", "ㅙ": "we", "ㅚ": "we",
    "ㅛ": "yo", "ㅜ": "u", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅠ": "yu",
    "ㅡ": "u", "ㅢ": "ui", "ㅣ": "i",
}
COLS = ["a", "e", "ya", "ye", "o", "wa", "we", "yo", "u", "wo", "wi", "yu", "ui", "i"]
ROWS = {
    "":   "ア エ ヤ イェ オ ワ ウェ ヨ ウ ウォ ウィ ユ ウィ イ",
    "k":  "カ ケ キャ キェ コ クァ クェ キョ ク クォ クィ キュ クィ キ",
    "g":  "ガ ゲ ギャ ギェ ゴ グァ グェ ギョ グ グォ グィ ギュ グィ ギ",
    "n":  "ナ ネ ニャ ニェ ノ ヌァ ヌェ ニョ ヌ ヌォ ヌィ ニュ ヌィ ニ",
    "t":  "タ テ テャ テェ ト トァ トェ ティョ トゥ トゥォ トゥィ テュ トゥィ ティ",
    "d":  "ダ デ デャ デェ ド ドァ ドェ ディョ ドゥ ドゥォ ドゥィ デュ ドゥィ ディ",
    "r":  "ラ レ リャ リェ ロ ルァ ルェ リョ ル ルォ ルィ リュ ルィ リ",
    "m":  "マ メ ミャ ミェ モ ムァ ムェ ミョ ム ムォ ムィ ミュ ムィ ミ",
    "p":  "パ ペ ピャ ピェ ポ プァ プェ ピョ プ プォ プィ ピュ プィ ピ",
    "b":  "バ ベ ビャ ビェ ボ ブァ ブェ ビョ ブ ブォ ブィ ビュ ブィ ビ",
    "s":  "サ セ シャ シェ ソ スァ スェ ショ ス スォ シュィ シュ スィ シ",
    "ch": "チャ チェ チャ チェ チョ チュァ チュェ チョ チュ チュォ チュィ チュ チュィ チ",
    "j":  "ジャ ジェ ジャ ジェ ジョ ジュァ ジュェ ジョ ジュ ジュォ ジュィ ジュ ジュィ ジ",
    "h":  "ハ ヘ ヒャ ヒェ ホ ファ フェ ヒョ フ フォ フィ ヒュ フィ ヒ",
}
TABLE = {row: dict(zip(COLS, kana.split())) for row, kana in ROWS.items()}

FINAL_KANA = {"": "", "ㄱ": "ㇰ", "ㄴ": "ン", "ㄷ": "ッ", "ㄹ": "ㇽ", "ㅁ": "ㇺ", "ㅂ": "ㇷ゚", "ㅇ": "ン"}

# 初声 → (無声の行, 有声の行)。濁るのは平音だけ
ROW_OF = {
    "ㄱ": ("k", "g"), "ㄷ": ("t", "d"), "ㅂ": ("p", "b"), "ㅈ": ("ch", "j"),
    "ㄲ": ("k", None), "ㄸ": ("t", None), "ㅃ": ("p", None), "ㅉ": ("ch", None), "ㅆ": ("s", None),
    "ㅋ": ("k", None), "ㅌ": ("t", None), "ㅍ": ("p", None), "ㅊ": ("ch", None),
    "ㄴ": ("n", None), "ㄹ": ("r", None), "ㅁ": ("m", None), "ㅅ": ("s", None),
    "ㅎ": ("h", None), "ㅇ": ("", None),
}
TENSE = {"ㄱ": "ㄲ", "ㄷ": "ㄸ", "ㅂ": "ㅃ", "ㅅ": "ㅆ", "ㅈ": "ㅉ"}
ASPIRATE = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}
NASAL = {"ㄱ": "ㅇ", "ㄷ": "ㄴ", "ㅂ": "ㅁ"}

# 母音の前で、パッチムがどう割れるか（残る音, 次の初声）
LIAISON = {
    "ㄳ": ("ㄱ", "ㅆ"), "ㄵ": ("ㄴ", "ㅈ"), "ㄺ": ("ㄹ", "ㄱ"), "ㄻ": ("ㄹ", "ㅁ"),
    "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅆ"), "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"),
    "ㅄ": ("ㅂ", "ㅆ"), "ㄶ": ("", "ㄴ"), "ㅀ": ("", "ㄹ"), "ㅎ": ("", "ㅇ"),
}


def rep(jong, nxt=None):
    """子音の前・語末で実際に鳴るパッチム（7つ）"""
    if jong in ("ㄱ", "ㄲ", "ㅋ", "ㄳ"):
        return "ㄱ"
    if jong == "ㄺ":
        return "ㄹ" if nxt == "ㄱ" else "ㄱ"
    if jong in ("ㄴ", "ㄵ", "ㄶ"):
        return "ㄴ"
    if jong in ("ㄷ", "ㅅ", "ㅆ", "ㅈ", "ㅊ", "ㅌ", "ㅎ"):
        return "ㄷ"
    if jong in ("ㄹ", "ㄼ", "ㄽ", "ㄾ", "ㅀ"):
        return "ㄹ"
    if jong in ("ㅁ", "ㄻ"):
        return "ㅁ"
    if jong in ("ㅂ", "ㅍ", "ㅄ", "ㄿ"):
        return "ㅂ"
    return jong  # "" か ㅇ


def decompose(word):
    out = []
    for ch in word:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append({"cho": CHO[code // 588], "jung": JUNG[(code % 588) // 28],
                        "jong": JONG[code % 28], "orig_cho": CHO[code // 588]})
    return out


def apply_rules(syl):
    for i in range(len(syl) - 1):
        a, b = syl[i], syl[i + 1]
        j, c = a["jong"], b["cho"]
        if not j:
            continue
        if c == "ㅇ":
            if j == "ㅇ":
                continue
            if j in LIAISON:
                a["jong"], b["cho"] = LIAISON[j]
            else:
                a["jong"], b["cho"] = "", j
                if b["jung"] == "ㅣ" and j in ("ㄷ", "ㅌ"):
                    b["cho"] = "ㅈ" if j == "ㄷ" else "ㅊ"
            continue
        if c == "ㅎ" and j not in ("ㄴ", "ㄹ", "ㅁ", "ㅇ", "ㄶ", "ㅀ", "ㅎ"):
            r = {"ㄺ": "ㄱ", "ㄼ": "ㅂ"}.get(j) or rep(j)
            a["jong"] = "ㄹ" if j in ("ㄺ", "ㄼ") else ""
            if r == "ㄱ":
                b["cho"] = "ㅋ"
            elif r == "ㅂ":
                b["cho"] = "ㅍ"
            elif j in ("ㅈ", "ㅊ") or (j in ("ㄷ", "ㅌ") and b["jung"] == "ㅣ"):
                b["cho"] = "ㅊ"
            else:
                b["cho"] = "ㅌ"
            continue
        if j in ("ㅎ", "ㄶ", "ㅀ"):
            keep = {"ㅎ": "", "ㄶ": "ㄴ", "ㅀ": "ㄹ"}[j]
            if c in ASPIRATE:
                a["jong"], b["cho"] = keep, ASPIRATE[c]
                continue
            if c == "ㅅ":
                a["jong"], b["cho"] = keep, "ㅆ"
                continue
            if c == "ㄴ":
                a["jong"] = "ㄹ" if j == "ㅀ" else "ㄴ"
                if j == "ㅀ":
                    b["cho"] = "ㄹ"
                continue
        r = rep(j, c)
        if r in NASAL and c in ("ㄴ", "ㅁ"):
            r = NASAL[r]
        elif c == "ㄹ":
            if r == "ㄴ":
                r = "ㄹ"
            elif r in ("ㅁ", "ㅇ"):
                b["cho"] = "ㄴ"
            elif r in NASAL:
                r, b["cho"] = NASAL[r], "ㄴ"
        elif c == "ㄴ" and r == "ㄹ":
            b["cho"] = "ㄹ"
        if c in TENSE and (r in NASAL or j in ("ㄵ", "ㄻ", "ㄺ", "ㄼ", "ㄾ")):
            b["cho"] = TENSE[c]
        a["jong"] = r
    if syl:
        syl[-1]["jong"] = rep(syl[-1]["jong"])
    # 의・ㅖ の読み
    for i, s in enumerate(syl):
        if s["jung"] == "ㅢ":
            if s["orig_cho"] != "ㅇ":
                s["jung"] = "ㅣ"
            elif i == 0:
                pass
            elif i == len(syl) - 1:
                s["jung"] = "ㅔ"  # 助詞の 의
            else:
                s["jung"] = "ㅣ"
        elif s["jung"] == "ㅖ" and s["cho"] != "ㅇ":
            s["jung"] = "ㅔ"
    return syl


def to_kana(word):
    syl = apply_rules(decompose(word))
    out = []
    prev_final = None  # None = 語頭
    for s in syl:
        voiceless, voiced = ROW_OF[s["cho"]]
        row = voiceless
        if voiced and prev_final is not None and prev_final in ("", "ㄴ", "ㄹ", "ㅁ", "ㅇ"):
            row = voiced
        kana = TABLE[row][VOWEL[s["jung"]]]
        if s["cho"] in ("ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ") and not prev_final:
            kana = "ッ" + kana
        out.append(kana + FINAL_KANA[s["jong"]])
        prev_final = s["jong"]
    return "".join(out)


# ローマ字（英語圏の人向け）。国の方式（Revised Romanization）の字を、綴りではなく
# 上と同じ「実際の音」に当てる: 받들어 → batteureo、빛나네 → binnane、호산나의 → hosannae
R_CHO = {"ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r", "ㅁ": "m", "ㅂ": "b",
         "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅇ": "", "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k",
         "ㅌ": "t", "ㅍ": "p", "ㅎ": "h"}
R_JUNG = {"ㅏ": "a", "ㅐ": "ae", "ㅑ": "ya", "ㅒ": "yae", "ㅓ": "eo", "ㅔ": "e", "ㅕ": "yeo",
          "ㅖ": "ye", "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wae", "ㅚ": "oe", "ㅛ": "yo", "ㅜ": "u",
          "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅠ": "yu", "ㅡ": "eu", "ㅢ": "ui", "ㅣ": "i"}
R_JONG = {"": "", "ㄱ": "k", "ㄴ": "n", "ㄷ": "t", "ㄹ": "l", "ㅁ": "m", "ㅂ": "p", "ㅇ": "ng"}
# 詰まる音（ㄱ ㄷ ㅂ）の後の濃音は、前の字と重ねない（학교 → hakkyo、받들어 → batteureo）
R_AFTER_STOP = {"ㄲ": "k", "ㄸ": "t", "ㅃ": "p", "ㅆ": "s", "ㅉ": "j"}


def to_roman(word):
    syl = apply_rules(decompose(word))
    out = []
    prev_final = None
    for s in syl:
        c = s["cho"]
        if c == "ㄹ" and prev_final == "ㄹ":
            head = "l"
        elif c in R_AFTER_STOP and prev_final in ("ㄱ", "ㄷ", "ㅂ"):
            head = R_AFTER_STOP[c]
        else:
            head = R_CHO[c]
        # ng の後に母音が来ると n＋g と読めてしまうので区切る（영광을 → yeonggwang-eul）
        if not head and prev_final == "ㅇ":
            head = "-"
        out.append(head + R_JUNG[s["jung"]] + R_JONG[s["jong"]])
        prev_final = s["jong"]
    return "".join(out)


HANGUL_RUN = re.compile(r"[가-힣]+")


if __name__ == "__main__":
    import sys
    for w in sys.argv[1:]:
        print(w, to_kana(w), to_roman(w))

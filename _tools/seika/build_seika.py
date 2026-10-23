"""聖歌のページを作る: _tools/seika/songs/NNN.txt → seika/NNN.html と一覧 seika/index.html

    python -I -X utf8 _tools/seika/build_seika.py            # 全曲＋一覧
    python -I -X utf8 _tools/seika/build_seika.py 001 002    # 指定した曲＋一覧

NNN はハングルの聖歌集『성가』の番号。日本の聖歌は番号の付け方が違うので
（ハングル1番＝日本の5番）、ページと一覧には両方を出す（videos.tsv で対応を持つ）。

歌のファイルの書き方（songs/001.txt が見本）:
    no: / ko: / ja: / page:   曲番号・ハングルの題・日本語の題・聖歌集のページ
    [1] [2] …                 節の始まり。[*] は折り返し（＊）
    ハングル | 日本語の意味     1行ずつ。日本の聖歌の歌詞（公式の訳詞）が1行ずつ当たる曲では
                              意味は出さない（日本の聖歌が無い曲・当たらない曲だけに出す）
    (*)                       「＊くり返し」の印
    語{=발음}                 読みを手で直す。実際の音をハングルで書く（절대{=절때}）。カナもローマ字もここから作る
    ## 語句                   以下「語 | 説明」を欄外の語句に出す
"""

import csv
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hangul_kana import to_kana, to_roman  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SONGS = HERE / "songs"
OUT = ROOT / "seika"
VERSION = "202610240200"
SITE = "https://maydra.github.io/mimune-no-uraniwa/seika/"

WORD = re.compile(r"([^\s{]+)(?:\{([^}]*)\})?")
HANGUL = re.compile(r"[가-힣]+")
JA_RUBY = re.compile(r"([一-鿿々〆ヶ]+)[(（]([ぁ-ゖー]+)[)）]")

# 動画の持ち主
JA_OWNER = ("太陽と月", "https://www.youtube.com/playlist?list=PLA7Q9J0AlZLNDZTBfDVKIJOP5dPYcA0uh")
RUBY_OWNER = ("KYUNGBOON PARK", "https://www.youtube.com/@kyungboonpark9875")


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


SONG_INDEX = read_tsv(HERE / "songs_index.tsv")                     # ハングルの聖歌集の目次
VIDEOS = {r["no"]: r for r in read_tsv(HERE / "videos.tsv")}         # match_videos.py が作る
JA_OFFICIAL = json.loads((HERE / "ja_official.json").read_text(encoding="utf-8"))  # parse_ja_official.py が作る


def ja_label(ja_no):
    """「5」→「5番」、「2部2」→「第2部 2番」"""
    m = re.match(r"^2部(\d+)$", ja_no)
    return f"第2部 {m.group(1)}番" if m else f"{ja_no}番"


def official_for(ja_no):
    return JA_OFFICIAL.get(ja_no) or JA_OFFICIAL.get(ja_no + "(A)")


def official_title(ja_no):
    """公式の題（読みの括弧と（Ａ）は外す）。歌詞の無い曲は再生リストの題"""
    off = official_for(ja_no)
    t = off["title"] if off else ""
    t = re.sub(r"[(（][ぁ-ゖー]+[)）]", "", t)
    return re.sub(r"（[ＡＢ]）$", "", t)


def ja_order(ja_no):
    m = re.match(r"^(?:2部)?(\d+)$", ja_no)
    return (1 if ja_no.startswith("2部") else 0, int(m.group(1)))


def load_ja_rows():
    """日本の聖歌の番号 → 題、→ 動画。公式の歌詞（第一部1〜70・第二部2〜9）と、
    再生リスト（第二部1・10〜17 もある）の両方から集める"""
    rows, vids = {}, {}
    for key in JA_OFFICIAL:
        k = re.sub(r"\([AB]\)$", "", key)
        rows.setdefault(k, official_title(k))
    with open(HERE / "youtube" / "playlist_ja.tsv", encoding="utf-8") as f:
        for r in csv.reader(f, delimiter="\t"):
            m = re.match(r"聖歌((?:2部)?\d+)番：(.+?)(?:（([AB])）)?(?:\s*※広告なし)?$", r[2])
            if m:
                rows.setdefault(m.group(1), m.group(2).strip())
                vids.setdefault(m.group(1), []).append(r[1] + (f"({m.group(3)})" if m.group(3) else ""))
    return rows, vids


JA_ROWS, JA_VIDS = load_ja_rows()
# ハングル版の無い日本の聖歌（41〜70番の讃美歌など）。日本語の歌詞と動画だけのページを作る
JA_OFFICIAL_ONLY = [k for k in sorted(JA_ROWS, key=ja_order)
                    if k not in {v["ja_no"] for v in VIDEOS.values() if v.get("ja_no")}]


def ja_page_name(ja_no):
    """ja-45.html、第2部は ja-2-10.html"""
    return "ja-" + ja_no.replace("2部", "2-") + ".html"


# ---------------------------------------------------------------- 歌のファイル

def parse(path):
    song = {"verses": [], "glossary": []}
    verse = None
    in_glossary = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## 語句"):
            in_glossary = True
            continue
        if in_glossary:
            term, _, desc = line.partition("|")
            song["glossary"].append((term.strip(), desc.strip()))
            continue
        m = re.match(r"^(no|ko|ja|page|all):\s*(.*)$", line)
        if m and verse is None:
            song[m.group(1)] = m.group(2).strip()
            continue
        m = re.match(r"^\[(\d+[ab]?|\*)\]$", line)
        if m:
            verse = {"no": m.group(1), "lines": []}
            song["verses"].append(verse)
            continue
        if line == "(*)":
            verse["lines"].append(None)
            continue
        if line.startswith("#"):  # 覚え書き（誤植を直した所など）。ページには出さない
            continue
        if "||" in line:  # 日本の聖歌の歌詞を手で当てた行
            ko, _, off = line.partition("||")
            song.setdefault("manual", {})[(len(song["verses"]) - 1, len(verse["lines"]))] = off.strip()
            verse["lines"].append((ko.strip(), ""))
            continue
        ko, _, ja = line.partition("|")
        verse["lines"].append((ko.strip(), ja.strip()))
    return song


def ruby(text):
    """ハングルを語ごとに <ruby> にする。読みはカナ（.rk）とローマ字（.rr）の両方を入れ、
    どちらを見せるかはページのボタンで切り替える。語の前後の記号はルビの外に出す"""
    parts = []
    for m in WORD.finditer(text):
        word, fix = m.group(1), m.group(2)
        core = HANGUL.findall(word)
        if not core:
            parts.append(html.escape(word))
            continue
        # 語の中のハングルの塊ごとにルビを付け、間の記号（合いの手の括弧など）はルビの外に出す。
        # 読みの手直し {=발음} は、語がひと塊のときだけ効く
        pieces, pos = [], 0
        for hm in HANGUL.finditer(word):
            pieces.append(html.escape(word[pos:hm.start()]))
            base = hm.group(0)
            sound = fix[1:] if fix and fix.startswith("=") and len(core) == 1 else base
            kana = "".join(to_kana(h) for h in HANGUL.findall(sound))
            roman = "".join(to_roman(h) for h in HANGUL.findall(sound))
            rt = f'<span class="rk">{html.escape(kana)}</span><span class="rr" lang="ko-Latn">{html.escape(roman)}</span>'
            pieces.append(f"<ruby>{html.escape(base)}<rt>{rt}</rt></ruby>")
            pos = hm.end()
        pieces.append(html.escape(word[pos:]))
        # 1語を箱に入れる。箱が無いと、字より長い読みが隣の語との空きにはみ出す
        parts.append('<span class="w">' + "".join(pieces) + "</span>")
    return " ".join(parts)


def plain(text):
    """読みの手直し {…} を取った、元のハングル"""
    return re.sub(r"\{[^}]*\}", "", text)


def kana_ruby(text):
    """公式の訳詞の「生命(いのち)」を <ruby> にする（読みの前の漢字の並びに付ける）"""
    out, pos = [], 0
    for m in JA_RUBY.finditer(text):
        out.append(html.escape(text[pos:m.start()]))
        out.append(f"<ruby>{html.escape(m.group(1))}<rt>{html.escape(m.group(2))}</rt></ruby>")
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def align_official(song, off):
    """公式の訳詞を、ハングルの行に1行ずつ当てる。{(節の位置, 行の位置): 訳詞の行}

    公式の訳詞は各節に折り返し（＊）まで書いてあり、ハングルの歌のファイルは
    折り返しを [*] に1回だけ書く。節の行数＋折り返しの行数が合わない曲は
    当てずに None を返す（ページの下に訳詞をまとめて出す）。"""
    if not off:
        return None
    verses = song["verses"]
    numbered = [i for i, v in enumerate(verses) if v["no"] != "*"]
    if len(numbered) != len(off["verses"]):
        return None
    refrain_at = next((i for i, v in enumerate(verses) if v["no"] == "*"), None)
    refrain_n = len(verses[refrain_at]["lines"]) if refrain_at is not None else 0

    # 節ごとに、ハングルの行（＝訳詞の各行を当てる先）を並べる。訳詞は折り返しまで
    # 毎節書いてあるので、ハングルの節の行＋折り返しの行（最初の節だけ実際の行、
    # あとの節は (*) で省いてあるので当てる先が無い）
    pairs = {}
    for k, vi in enumerate(numbered):
        ja_lines = off["verses"][k]
        own = [(vi, j) for j, ln in enumerate(verses[vi]["lines"]) if ln is not None]
        candidates = [own]
        if refrain_n and (vi + 1 == refrain_at or verses[vi]["lines"][-1:] == [None]):
            ref = [(refrain_at, j) for j in range(refrain_n)] if vi + 1 == refrain_at else [None] * refrain_n
            candidates.insert(0, own + ref)  # 訳詞が折り返しまで書いてある形を先に試す
        for slots in candidates:
            if len(ja_lines) == len(slots):
                step = 1
            elif len(ja_lines) * 2 == len(slots):
                step = 2  # 訳詞の1行がハングルの2行（半行ずつ書いてある曲）
            else:
                continue
            for n, ja in enumerate(ja_lines):
                slot = slots[n * step]
                if slot is not None:
                    pairs[slot] = ja
            break
        else:
            return None
    return pairs


# ---------------------------------------------------------------- 曲のページ

def video_card(vid, label, owner):
    """サムネだけ出し、押したら埋め込みの再生に替える（最初から iframe を並べると重い）"""
    m = re.match(r"^([\w-]+)(?:\((\w)\))?$", vid)
    vid, ab = m.group(1), m.group(2)
    if ab:
        label += f"（{ab}）"
    name, url = owner
    return f"""          <figure class="yt">
            <button type="button" class="yt-play" data-id="{vid}" aria-label="{html.escape(label)}を再生">
              <img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">
              <span class="yt-icon" aria-hidden="true">▶</span>
            </button>
            <figcaption>{html.escape(label)}<br><a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">YouTube で開く</a>（<a href="{url}" target="_blank" rel="noopener">{html.escape(name)}</a>）</figcaption>
          </figure>"""


def videos_block(v):
    if not v:
        return ""
    cards = []
    for vid in v.get("ja_video", "").split():
        cards.append(video_card(vid, f"日本語の歌詞（日本の聖歌 {ja_label(v['ja_no'])}）", JA_OWNER))
    for vid in v.get("ruby_video", "").split():
        cards.append(video_card(vid, "ハングル・ルビ入り（歌）", RUBY_OWNER))
    for vid in v.get("ruby_accomp", "").split():
        cards.append(video_card(vid, "ハングル・ルビ入り（伴奏）", RUBY_OWNER))
    if not cards:
        return ""
    return ('\n      <section class="videos">\n        <h2>動画で聴く</h2>\n        <div class="vgrid">\n'
            + "\n".join(cards) + "\n        </div>\n      </section>\n")


HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXQ0QTBYTR"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());

    gtag('config', 'G-XXQ0QTBYTR');
  </script>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="https://maydra.github.io/mimune-no-uraniwa/og-image.png" />
  <link rel="icon" href="/mimune-no-uraniwa/favicon.png?v=202609192031" type="image/png" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700&family=Noto+Serif+KR:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../theme/style.css?v=202609192031">
  <link rel="stylesheet" href="../theme/pages/e631ced897.css?v=202610110220">
  <link rel="stylesheet" href="seika.css?v={version}">
</head>
"""

# 試験中（2026-10-23 にホームの主要文献へ「聖歌（試験中）」として出した）。誤りの知らせは、
# 本のページと同じ「誤植・修正提案」のフォーム（Google Apps Script。ページの URL が自動で付く）
BETA_NOTE = '      <p class="beta">聖歌のコーナーは試験中です。読み・訳・誤字など、気づいたことは下の「誤植・修正提案」から送ってください。</p>\n'
TYPO_BOX = """
    <details id="typo-report" class="typo-box dark-theme">
      <summary class="typo-title">誤植・修正提案</summary>
      <p class="typo-desc">読みの誤り・訳の違い・誤字など、コメント感覚で送れます（匿名OK）。ページURLは自動で添付されます。</p>
      <form id="typoForm"
            action="https://script.google.com/macros/s/AKfycbzKaBDjVMe5wZgmZ1yQ5We6u3W3E3PGVLthOniv3TQvuopr2bWU_yrYQ1oQucz5NdwH8w/exec"
            method="POST"
            target="typoSink">
        <label class="typo-label" for="typoText">内容（必須）</label>
        <textarea id="typoText" name="typoText" class="typo-textarea" rows="4" required
          placeholder="例：〇番の2行目の読みが違う、訳の行がずれている…"></textarea>
        <label class="typo-label" for="typoQuote">該当箇所（任意）</label>
        <textarea id="typoQuote" name="typoQuote" class="typo-textarea" rows="2"
          placeholder="該当の行をコピペ（任意）"></textarea>
        <input type="hidden" id="pageUrl" name="pageUrl">
        <input type="hidden" id="whenIso" name="whenIso">
        <input type="hidden" id="userAgent" name="userAgent">
        <label class="typo-label" for="replyEmail">返信が欲しい方は、メールアドレスを入力ください（任意）</label>
        <input type="email" id="replyEmail" name="replyEmail" class="typo-input" placeholder="例：name@example.com">
        <div class="typo-row">
          <button type="submit" id="typoSubmit" class="typo-btn">送信</button>
          <span id="typoStatus" class="typo-status" aria-live="polite"></span>
        </div>
      </form>
      <iframe name="typoSink" id="typoSink" style="display:none;"></iframe>
    </details>
    <script>
      (function () {
        var form = document.getElementById('typoForm'), sink = document.getElementById('typoSink');
        var statusEl = document.getElementById('typoStatus'), btn = document.getElementById('typoSubmit');
        function fill() {
          document.getElementById('pageUrl').value = location.href;
          document.getElementById('whenIso').value = new Date().toISOString();
          document.getElementById('userAgent').value = navigator.userAgent;
        }
        fill();
        form.addEventListener('submit', function () { fill(); btn.disabled = true; statusEl.textContent = '送信中…'; });
        sink.addEventListener('load', function () {
          btn.disabled = false;
          statusEl.textContent = '送信しました。ありがとうございます！';
          setTimeout(function () { form.reset(); }, 200);
        });
      })();
    </script>
"""

# 日本の聖歌の訳詞のうち、ほかの教団の讃美歌集の訳とほぼ同じで、権利を確かめるまで歌詞を出さない曲
# 42「神ともに居まして」＝日本基督教団『讃美歌』405番「神ともにいまして　ゆく道をまもり」とほぼ同じ
JA_HOLD = {"42"}

# 共有: スマホは端末の共有画面（LINE など）、パソコンはリンクをコピー
SHARE_JS = """
      function share(btn, title, url) {
        if (navigator.share) {
          navigator.share({ title: title, url: url }).catch(function () {});
          return;
        }
        function done() {
          var old = btn.textContent;
          btn.textContent = 'リンクをコピーしました';
          setTimeout(function () { btn.textContent = old; }, 1800);
        }
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(done, function () { prompt('リンク', url); });
        } else {
          prompt('リンク', url);
        }
      }"""


def render(song):
    no = int(song["no"])
    title_ko = song["ko"]
    v = VIDEOS.get(str(no)) or {}
    ja_no = v.get("ja_no", "")
    off = official_for(ja_no) if ja_no else None
    # 手で当てた行（ハングル || 訳詞）があればそれを使い、無ければ行数で当てる
    pairs = song.get("manual") or align_official(song, off)
    title_ja = official_title(ja_no) if off else (v.get("ja_title") or song["ja"])

    out = []
    for vi, verse in enumerate(song["verses"]):
        refrain = verse["no"] == "*"
        mark = "＊" if refrain else verse["no"]
        cls = "verse refrain" if refrain else "verse"
        label = "折り返し" if refrain else verse["no"] + "番"
        out.append(f'      <section class="{cls}">\n        <p class="vno" aria-label="{label}">{mark}</p>\n        <div class="lines">')
        # ハングルの行を、日本語の1行が当たるまとまりにする（訳詞の1行がハングルの2行に
        # 当たる曲もある）。日本語はまとまりの最初の行に当ててあるので、日本語の無い行は前に足す
        groups = []
        for j, ln in enumerate(verse["lines"]):
            if ln is None:
                groups.append(None)
                continue
            ko, ja = ln
            if pairs:
                side = f'<p class="ja-off">{kana_ruby(pairs[(vi, j)])}</p>' if (vi, j) in pairs else ""
            else:
                side = f'<p class="ja">{html.escape(ja)}</p>' if ja else ""
            if side or not groups or groups[-1] is None or not groups[-1][1]:
                groups.append([[ko], side])
            else:
                groups[-1][0].append(ko)
        for g in groups:
            if g is None:
                out.append('          <p class="again">＊ くり返し</p>')
                continue
            kos, side = g
            kos = "\n".join(f'              <p class="ko" lang="ko">{ruby(k)}</p>' for k in kos)
            out.append('          <div class="line">\n'
                       f'            <div class="kos">\n{kos}\n            </div>\n'
                       f'            <div class="side">{side}</div>\n'
                       '          </div>')
        out.append("        </div>\n      </section>")
    verses = "\n".join(out)

    # 「日本語」の表示: 公式の訳詞を節ごとに全部（行に当てられなかった曲も、訳詞のほうに
    # 節が多い曲も、ここで全節読める）。13番のように（Ａ）（Ｂ）があれば両方
    off_block = ""
    has_meaning = any(ln and ln[1] for vs in song["verses"] for ln in vs["lines"])
    if off:
        versions = [JA_OFFICIAL[k] for k in (ja_no, ja_no + "(A)", ja_no + "(B)") if k in JA_OFFICIAL]
        body = []
        for ver in versions:
            ab = re.search(r"（([ＡＢ])）$", ver["title"])
            if ab:
                body.append(f'          <h3 class="off-ab">（{ab.group(1)}）</h3>')
            body += [f'          <p class="off-verse"><span>{k}.</span> ' + "<br>".join(kana_ruby(x) for x in vs) + "</p>"
                     for k, vs in enumerate(ver["verses"], 1)]
        off_block = ('\n      <section class="official">\n        <h2>日本の聖歌の歌詞</h2>\n'
                     + "\n".join(body) + "\n      </section>\n")
    elif has_meaning:
        # 日本の聖歌に無い曲は、このサイトで付けた意味を節ごとに
        body = []
        for verse in song["verses"]:
            mark = "＊" if verse["no"] == "*" else verse["no"] + "."
            lines = [html.escape(ln[1]) for ln in verse["lines"] if ln and ln[1]]
            if None in verse["lines"]:
                lines.append("（＊ くり返し）")
            if lines:
                body.append(f'          <p class="off-verse"><span>{mark}</span> ' + "<br>".join(lines) + "</p>")
        off_block = ('\n      <section class="official">\n        <h2>意味（このサイトの訳）</h2>\n'
                     + "\n".join(body) + "\n      </section>\n")

    gloss = "\n".join(
        f'          <div><dt lang="ko">{html.escape(t)}</dt><dd>{html.escape(d)}</dd></div>'
        for t, d in song["glossary"])
    gloss_block = (f'\n      <aside class="gloss">\n        <h2>語句</h2>\n        <dl>\n{gloss}\n        </dl>\n      </aside>\n'
                   if gloss else "")

    badges = f'<span class="badge badge-ja">日本の聖歌 {ja_label(ja_no)}</span>' if ja_no else ""
    badges += f'<span class="badge badge-ko">성가 {no}</span>'
    # 表示はハングルと日本語のどちらか（並べるとスマホで読みにくい）。パソコンは幅があるので、
    # ハングルの表示でも欄外に日本語を出す
    view_tabs = ""
    if off_block:
        view_tabs = ('\n      <div class="view-tabs" role="group" aria-label="表示">\n'
                     '        <button type="button" data-view="ko">ハングル</button><button type="button" data-view="ja">日本語</button>\n'
                     '      </div>\n')
    off_source = ""
    if off:
        part = "第二部" if ja_no.startswith("2部") else "第一部"
        off_source = (f'日本の聖歌の歌詞: 静岡家庭教会「<a href="{off["source"]}" target="_blank" rel="noopener">'
                      f'日本統一教会　聖歌　{part}</a>」（閉鎖、Internet Archive の保存から）。')
    made = "読み" if pairs else "読みと意味"
    page_title = (f"日本の聖歌{ja_label(ja_no)}" if ja_no else f"성가{no}") + f"「{title_ja}」{plain(title_ko)} | み旨の裏庭"
    desc = f"{plain(title_ko)}（{title_ja}）のハングルの歌詞。カタカナ・ローマ字の読みと日本語の歌詞つき。"

    return HEAD.format(title=html.escape(page_title), desc=html.escape(desc), version=VERSION) + f"""<body>
  <div class="container">
    <article class="song lyrics read-kana view-ko" id="song">
      <header class="song-head">
        <p class="badges">{badges}</p>
        <h1 lang="ko">{ruby(title_ko)}</h1>
        <p class="title-ja">{html.escape(title_ja)}</p>
        <button type="button" class="share-btn" id="share">🔗 この歌を共有</button>
      </header>
{view_tabs}
      <div class="song-tools">
        <div class="opt" role="group" aria-label="読み">
          <span class="opt-label">読み</span>
          <div class="seg"><button type="button" data-read="kana">カナ</button><button type="button" data-read="roman">ABC</button></div>
        </div>
      </div>

{verses}
{off_block}{videos_block(v)}{gloss_block}
      <details class="howto">
        <summary>読みについて</summary>
        <ul>
          <li>読みは綴りではなく、実際に聞こえる音で付けています（받들어 → パットゥロ／batteureo、빛나네 → ピンナネ／binnane）</li>
          <li>小さいカナは音節の終わりの子音（パッチム）です: ㇰ＝k、ン＝n／ng、ッ＝t、ㇽ＝l、ㇺ＝m、ㇷ゚＝p。母音を付けずに口を閉じるだけにします</li>
          <li>「〜의」（〜の）は歌でも話し言葉でも「エ」と読みます（호산나의 → ホサンナエ／hosannae）</li>
          <li>ABC は韓国の公式のローマ字（Revised Romanization）の綴り方で、音を写しています</li>
        </ul>
      </details>

      <p class="source">ハングルの歌詞: 聖歌集『성가』（2018年）{html.escape(song.get("page", ""))}ページ。{off_source}{made}はこのサイトで付けたものです。</p>
{BETA_NOTE}    </article>
{TYPO_BOX}
    <nav class="nav-links"><a href="index.html">聖歌の一覧</a> <a href="../index.html">トップページ</a></nav>
  </div>

  <script>
    (function () {{
      var song = document.getElementById('song');
{SHARE_JS}
      document.getElementById('share').addEventListener('click', function () {{
        share(this, document.title, location.href.split('#')[0]);
      }});

      // 読み: カナ／ABC／なし。日本語でない端末では最初から ABC
      var readBtns = song.querySelectorAll('[data-read]');
      function setRead(mode) {{
        song.classList.remove('read-kana', 'read-roman');
        song.classList.add('read-' + mode);
        readBtns.forEach(function (b) {{ b.setAttribute('aria-pressed', b.dataset.read === mode ? 'true' : 'false'); }});
      }}
      var mode = (navigator.language || 'ja').slice(0, 2) === 'ja' ? 'kana' : 'roman';
      try {{ var saved = localStorage.getItem('seika-read'); if (saved === 'kana' || saved === 'roman') mode = saved; }} catch (e) {{}}
      setRead(mode);
      readBtns.forEach(function (b) {{
        b.addEventListener('click', function () {{
          setRead(b.dataset.read);
          try {{ localStorage.setItem('seika-read', b.dataset.read); }} catch (e) {{}}
        }});
      }});

      // 表示: ハングル／日本語。選んだほうを覚える
      var viewBtns = song.querySelectorAll('button[data-view]');
      function setView(v) {{
        song.classList.remove('view-ko', 'view-ja');
        song.classList.add('view-' + v);
        viewBtns.forEach(function (b) {{ b.setAttribute('aria-pressed', b.dataset.view === v ? 'true' : 'false'); }});
      }}
      if (viewBtns.length) {{
        var view = 'ko';
        try {{ if (localStorage.getItem('seika-view') === 'ja') view = 'ja'; }} catch (e) {{}}
        setView(view);
        viewBtns.forEach(function (b) {{
          b.addEventListener('click', function () {{
            setView(b.dataset.view);
            try {{ localStorage.setItem('seika-view', b.dataset.view); }} catch (e) {{}}
          }});
        }});
      }}

      document.querySelectorAll('.yt-play').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          var f = document.createElement('iframe');
          f.src = 'https://www.youtube-nocookie.com/embed/' + btn.dataset.id + '?autoplay=1&rel=0';
          f.title = btn.getAttribute('aria-label');
          f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
          f.allowFullscreen = true;
          btn.replaceWith(f);
        }});
      }});
    }})();
  </script>
  <script src="../theme/script.js?v=202609192031"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- 流行歌の紹介のページ

def parse_intro(path):
    """流行歌（作詞・作曲者のいる韓国の歌）は歌詞を全部は載せない。紹介・1〜2行の引用・
    主な語句・正規の配信への参照だけのページにする（引用の範囲。訳も引用の中だけ）

        type: intro / no: / ko: / ja: / page: / credit:（作詞作曲・歌）
        ## 紹介      段落（1行1段落）
        ## 引用      ハングル | 意味
        ## 語句      語 | 説明
        ## 参照      表示 | URL
    """
    song = {"about": [], "quote": [], "glossary": [], "links": [], "videos": []}
    section = None
    keys = {"紹介": "about", "引用": "quote", "語句": "glossary", "参照": "links", "動画": "videos"}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("# "):
            continue
        m = re.match(r"^## (.+)$", line)
        if m:
            section = keys[m.group(1).strip()]
            continue
        if section is None:
            k, _, val = line.partition(":")
            song[k.strip()] = val.strip()
        elif section == "about":
            song["about"].append(line)
        elif section == "videos":  # 動画のID | チャンネル | チャンネルのURL | 説明
            song["videos"].append([x.strip() for x in line.split("|")])
        else:
            a, _, b = line.partition("|")
            song[section].append((a.strip(), b.strip()))
    return song


def render_intro(song):
    no = int(song["no"])
    title_ko, title_ja = song["ko"], song["ja"]
    about = "\n".join(f"        <p>{html.escape(p)}</p>" for p in song["about"])
    quote = "\n".join(
        '          <div class="line">\n'
        f'            <p class="ko" lang="ko">{ruby(ko)}</p>\n'
        f'            <div class="side"><p class="ja">{html.escape(ja)}</p></div>\n'
        '          </div>' for ko, ja in song["quote"])
    gloss = "\n".join(
        f'          <div><dt lang="ko">{ruby(t)}</dt><dd>{html.escape(d)}</dd></div>' for t, d in song["glossary"])
    links = "\n".join(
        f'          <li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a></li>'
        for t, u in song["links"])
    cards = [video_card(vid, label, (ch, url)) for vid, ch, url, label in song["videos"]]
    videos = ('\n      <section class="videos">\n        <h2>動画で聴く</h2>\n        <div class="vgrid">\n'
              + "\n".join(cards) + "\n        </div>\n      </section>\n") if cards else ""
    page_title = f"성가{no}「{plain(title_ko)}」（{title_ja}） | み旨の裏庭"
    desc = f"韓国の歌「{plain(title_ko)}」の紹介と主な語句。"
    return HEAD.format(title=html.escape(page_title), desc=html.escape(desc), version=VERSION) + f"""<body>
  <div class="container">
    <article class="song read-kana" id="song">
      <header class="song-head">
        <p class="badges"><span class="badge badge-ko">성가 {no}</span></p>
        <h1 lang="ko">{ruby(title_ko)}</h1>
        <p class="title-ja">{html.escape(title_ja)}</p>
        <button type="button" class="share-btn" id="share">🔗 この歌を共有</button>
      </header>

      <div class="song-tools">
        <div class="opt" role="group" aria-label="読み">
          <span class="opt-label">読み</span>
          <div class="seg"><button type="button" data-read="kana">カナ</button><button type="button" data-read="roman">ABC</button></div>
        </div>
      </div>

      <section class="intro">
{about}
        <p class="credit">{html.escape(song.get("credit", ""))}</p>
      </section>

      <section class="quote">
        <h2>歌詞から（一部）</h2>
        <blockquote class="lines">
{quote}
        </blockquote>
        <p class="note">この歌は作詞・作曲者のいる韓国の歌なので、歌詞の全文はここには載せません。全文は下の正規の配信で見られます。</p>
      </section>

      <aside class="gloss">
        <h2>歌に出てくる主な語句</h2>
        <dl>
{gloss}
        </dl>
      </aside>

      <section class="refs">
        <h2>歌詞の全文と歌を聴く</h2>
        <ul>
{links}
        </ul>
        <p class="note">歌詞を写して <a href="yomi.html">読みを付ける道具</a> に貼ると、カナ・ローマ字の読みと日本語・英語の意味が見られます（貼った歌詞はこのサイトには残りません）。</p>
      </section>
{videos}

      <p class="source">聖歌集『성가』（2018年）{html.escape(song.get("page", ""))}ページに入っている歌です。紹介・読み・意味はこのサイトで付けたものです。</p>
{BETA_NOTE}    </article>
{TYPO_BOX}
    <nav class="nav-links"><a href="index.html">聖歌の一覧</a> <a href="../index.html">トップページ</a></nav>
  </div>

  <script>
    (function () {{
      var song = document.getElementById('song');
{SHARE_JS}
      document.getElementById('share').addEventListener('click', function () {{
        share(this, document.title, location.href.split('#')[0]);
      }});
      var readBtns = song.querySelectorAll('[data-read]');
      function setRead(mode) {{
        song.classList.remove('read-kana', 'read-roman');
        song.classList.add('read-' + mode);
        readBtns.forEach(function (b) {{ b.setAttribute('aria-pressed', b.dataset.read === mode ? 'true' : 'false'); }});
      }}
      var mode = (navigator.language || 'ja').slice(0, 2) === 'ja' ? 'kana' : 'roman';
      try {{ var saved = localStorage.getItem('seika-read'); if (saved === 'kana' || saved === 'roman') mode = saved; }} catch (e) {{}}
      setRead(mode);
      readBtns.forEach(function (b) {{
        b.addEventListener('click', function () {{
          setRead(b.dataset.read);
          try {{ localStorage.setItem('seika-read', b.dataset.read); }} catch (e) {{}}
        }});
      }});
      document.querySelectorAll('.yt-play').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          var f = document.createElement('iframe');
          f.src = 'https://www.youtube-nocookie.com/embed/' + btn.dataset.id + '?autoplay=1&rel=0';
          f.title = btn.getAttribute('aria-label');
          f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
          f.allowFullscreen = true;
          btn.replaceWith(f);
        }});
      }});
    }})();
  </script>
  <script src="../theme/script.js?v=202609192031"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- ハングル版の無い日本の聖歌

def render_ja_only(ja_no):
    title = JA_ROWS[ja_no]
    off = official_for(ja_no)
    if ja_no in JA_HOLD:
        lyrics = '\n      <p class="none">歌詞は、権利を確かめるまで載せていません。下の動画に日本語の歌詞が出ます。</p>\n'
        source = ""
    elif off:
        credit = f'<p class="credit">{html.escape(off["credit"])}</p>' if off.get("credit") else ""
        body = "\n".join(
            f'          <p class="off-verse"><span>{k}.</span> ' + "<br>".join(kana_ruby(x) for x in vs) + "</p>"
            for k, vs in enumerate(off["verses"], 1))
        part = "第二部" if ja_no.startswith("2部") else "第一部"
        lyrics = f'\n      <section class="official ja-only">\n        {credit}\n{body}\n      </section>\n'
        source = (f'歌詞: 静岡家庭教会「<a href="{off["source"]}" target="_blank" rel="noopener">'
                  f'日本統一教会　聖歌　{part}</a>」（閉鎖、Internet Archive の保存から）。')
    else:
        lyrics = '\n      <p class="none">歌詞はまだありません。下の動画に日本語の歌詞が出ます。</p>\n'
        source = ""
    cards = [video_card(vid, f"日本語の歌詞（日本の聖歌 {ja_label(ja_no)}）", JA_OWNER) for vid in JA_VIDS.get(ja_no, [])]
    videos = ('\n      <section class="videos">\n        <h2>動画で聴く</h2>\n        <div class="vgrid">\n'
              + "\n".join(cards) + "\n        </div>\n      </section>\n") if cards else ""
    page_title = f"日本の聖歌{ja_label(ja_no)}「{title}」 | み旨の裏庭"
    desc = f"日本の聖歌{ja_label(ja_no)}「{title}」の歌詞と動画。"
    return HEAD.format(title=html.escape(page_title), desc=html.escape(desc), version=VERSION) + f"""<body>
  <div class="container">
    <article class="song" id="song">
      <header class="song-head">
        <p class="badges"><span class="badge badge-ja">日本の聖歌 {ja_label(ja_no)}</span></p>
        <h1>{html.escape(title)}</h1>
        <p class="title-ja">ハングルの聖歌集（성가）には無い曲です</p>
        <button type="button" class="share-btn" id="share">🔗 この歌を共有</button>
      </header>
{lyrics}{videos}
      <p class="source">{source}</p>
{BETA_NOTE}    </article>
{TYPO_BOX}
    <nav class="nav-links"><a href="index.html">聖歌の一覧</a> <a href="../index.html">トップページ</a></nav>
  </div>

  <script>
    (function () {{
{SHARE_JS}
      document.getElementById('share').addEventListener('click', function () {{
        share(this, document.title, location.href.split('#')[0]);
      }});
      document.querySelectorAll('.yt-play').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          var f = document.createElement('iframe');
          f.src = 'https://www.youtube-nocookie.com/embed/' + btn.dataset.id + '?autoplay=1&rel=0';
          f.title = btn.getAttribute('aria-label');
          f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
          f.allowFullscreen = true;
          btn.replaceWith(f);
        }});
      }});
    }})();
  </script>
  <script src="../theme/script.js?v=202609192031"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- 読みを付ける道具

def build_yomi():
    """歌詞を貼ると、読み（カナ・ABC）と意味（日本語・English）を出すページ。
    流行歌のように歌詞を載せられない歌でも、見る人が自分で写した歌詞に、その人の
    ブラウザの中で読みを付ける（サイトは歌詞を持たない・送らない）。
    読みは seika/hangul-yomi.js（hangul_kana.py を移したもの）。意味は、Chrome の端末内の
    翻訳（Translator API）が使えればそれで訳し、使えなければ行ごとに Papago・Google 翻訳を開くボタン"""
    page = HEAD.format(title="読みを付ける | 聖歌 | み旨の裏庭",
                       desc="ハングルの歌詞を貼ると、カタカナ・ローマ字の読みと、日本語・英語の意味が出ます。",
                       version=VERSION) + """<body>
  <div class="container">
    <article class="song read-kana yomi" id="song">
      <header class="song-head">
        <h1>読みを付ける</h1>
        <p class="title-ja">ハングルの歌詞を貼ると、読みと意味が出ます</p>
        <p class="title-en" lang="en">Paste Korean lyrics to see how to read them and what they mean</p>
      </header>

      <textarea id="src" rows="8" lang="ko" placeholder="ここにハングルの歌詞を貼り付け / Paste Korean lyrics here"></textarea>

      <div class="song-tools">
        <div class="opt" role="group" aria-label="読み Reading">
          <span class="opt-label">読み</span>
          <div class="seg"><button type="button" data-read="kana">カナ</button><button type="button" data-read="roman">ABC</button></div>
        </div>
        <div class="opt" role="group" aria-label="意味 Meaning">
          <span class="opt-label">意味</span>
          <div class="seg"><button type="button" data-mean="ja">日本語</button><button type="button" data-mean="en">English</button><button type="button" data-mean="both">両方</button><button type="button" data-mean="none">なし</button></div>
        </div>
      </div>
      <p class="go-row"><button type="button" class="go-btn" id="go">読みと意味を出す / Show</button></p>
      <p class="note" id="status" aria-live="polite"></p>

      <section id="out"></section>
      <p class="whole" id="whole" hidden></p>

      <details class="howto">
        <summary>使い方と注意 / Notes</summary>
        <ul>
          <li>読みは、綴りではなく実際に聞こえる音を自動で付けています。漢字語や合成語では、実際の発音と違うことがあります（聖歌のページの読みは、そうした所を手で直してあります）</li>
          <li>意味は機械翻訳です。パソコンの Chrome では、端末の中で訳すので歌詞はどこにも送りません。そのほかのブラウザでは、行ごとの「Papago」「Google」を押すと翻訳サイトが開きます（押した行だけがそのサイトに送られます）</li>
          <li>貼った歌詞はこのページの中だけで使い、保存もしません</li>
          <li lang="en">Readings are generated automatically from the actual pronunciation (ABC = Revised Romanization). Meanings are machine translations: Chrome on a computer translates on your device; elsewhere, tap Papago or Google to open a translator for that line. Nothing you paste is stored.</li>
        </ul>
      </details>
    </article>

    <nav class="nav-links"><a href="index.html">聖歌の一覧</a> <a href="../index.html">トップページ</a></nav>
  </div>

  <script src="hangul-yomi.js?v=""" + VERSION + """"></script>
  <script>
    (function () {
      var song = document.getElementById('song');
      var src = document.getElementById('src');
      var out = document.getElementById('out');
      var statusEl = document.getElementById('status');
      var HANGUL = /[\\uac00-\\ud7a3]+/g;

      function esc(s) {
        return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
      }
      // 語ごとに箱へ入れ、語の中のハングルの塊にルビ（カナと ABC の両方）を付ける
      function rubyLine(line) {
        return line.split(/(\\s+)/).map(function (tok) {
          if (!tok.trim()) return tok;
          var html = '', pos = 0, m;
          HANGUL.lastIndex = 0;
          while ((m = HANGUL.exec(tok))) {
            html += esc(tok.slice(pos, m.index));
            html += '<ruby>' + m[0] + '<rt><span class="rk">' + HangulYomi.toKana(m[0]) + '</span><span class="rr" lang="ko-Latn">'
              + HangulYomi.toRoman(m[0]) + '</span></rt></ruby>';
            pos = m.index + m[0].length;
          }
          return '<span class="w">' + html + esc(tok.slice(pos)) + '</span>';
        }).join('');
      }
      function papago(text, lang) { return 'https://papago.naver.com/?sk=ko&tk=' + lang + '&st=' + encodeURIComponent(text); }
      function google(text, lang) { return 'https://translate.google.com/?sl=ko&tl=' + lang + '&text=' + encodeURIComponent(text) + '&op=translate'; }
      var LANG_LABEL = { ja: '日本語', en: 'English' };

      // 端末の中の翻訳（Chrome の Translator API）。使えなければ null
      var translators = {};
      async function getTranslator(lang) {
        if (translators[lang] !== undefined) return translators[lang];
        translators[lang] = null;
        if (!('Translator' in self)) return null;
        try {
          var opts = { sourceLanguage: 'ko', targetLanguage: lang };
          if ((await Translator.availability(opts)) === 'unavailable') return null;
          opts.monitor = function (m) {
            m.addEventListener('downloadprogress', function (e) {
              statusEl.textContent = '翻訳の準備をしています（初回だけ） ' + Math.round(e.loaded * 100) + '%';
            });
          };
          translators[lang] = await Translator.create(opts);
        } catch (e) {
          translators[lang] = null;
        }
        return translators[lang];
      }

      function meanLangs() {
        var m = song.dataset.mean || 'ja';
        return m === 'both' ? ['ja', 'en'] : m === 'none' ? [] : [m];
      }

      async function show() {
        var lines = src.value.split(/\\r?\\n/);
        var langs = meanLangs();
        out.innerHTML = '';
        var jobs = [];
        lines.forEach(function (line) {
          var text = line.trim();
          if (!text) {
            if (out.lastChild && !out.lastChild.classList.contains('gap')) {
              var gap = document.createElement('div');
              gap.className = 'gap';
              out.appendChild(gap);
            }
            return;
          }
          var row = document.createElement('div');
          row.className = 'line';
          var side = langs.map(function (lang) {
            return '<p class="mt" data-lang="' + lang + '"><span class="mt-text"></span>'
              + '<span class="mt-links"><span class="mt-lang">' + LANG_LABEL[lang] + '</span>'
              + '<a href="' + papago(text, lang) + '" target="_blank" rel="noopener">Papago</a>'
              + '<a href="' + google(text, lang) + '" target="_blank" rel="noopener">Google</a></span></p>';
          }).join('');
          row.innerHTML = '<p class="ko" lang="ko">' + rubyLine(text) + '</p><div class="side">' + side + '</div>';
          out.appendChild(row);
          if (/[\\uac00-\\ud7a3]/.test(text)) jobs.push([row, text]);
        });

        var whole = document.getElementById('whole');
        var all = lines.join('\\n').trim();
        whole.hidden = !all || !langs.length;
        whole.innerHTML = '全体を翻訳サイトで開く: ' + langs.map(function (lang) {
          return LANG_LABEL[lang] + '（<a href="' + papago(all, lang) + '" target="_blank" rel="noopener">Papago</a>・'
            + '<a href="' + google(all, lang) + '" target="_blank" rel="noopener">Google</a>）';
        }).join(' ');

        // 端末の中で訳せる言葉は自動で訳し、訳せたら翻訳サイトのボタンは隠す
        for (var k = 0; k < langs.length; k++) {
          var t = await getTranslator(langs[k]);
          if (!t) continue;
          statusEl.textContent = LANG_LABEL[langs[k]] + 'の意味を、端末の中で訳しています…';
          for (var n = 0; n < jobs.length; n++) {
            var p = jobs[n][0].querySelector('.mt[data-lang="' + langs[k] + '"]');
            try {
              p.querySelector('.mt-text').textContent = await t.translate(jobs[n][1]);
              p.classList.add('done');
            } catch (e) { /* その行はボタンのまま */ }
          }
        }
        var auto = langs.some(function (l) { return translators[l]; });
        statusEl.textContent = !langs.length ? ''
          : auto ? '意味は端末の中の機械翻訳です（Chrome）。違和感のある行は Papago・Google でも確かめてください。'
          : '意味は、行ごとの「Papago」「Google」を押すと翻訳サイトで見られます。';
      }
      document.getElementById('go').addEventListener('click', show);

      // 読みと意味の選び方は覚えておく（歌詞は覚えない）
      function setChoice(kind, value) {
        song.querySelectorAll('[data-' + kind + ']').forEach(function (b) {
          b.setAttribute('aria-pressed', b.dataset[kind] === value ? 'true' : 'false');
        });
        if (kind === 'read') {
          song.classList.remove('read-kana', 'read-roman');
          song.classList.add('read-' + value);
        } else {
          song.dataset.mean = value;
        }
        try { localStorage.setItem('seika-' + kind, value); } catch (e) {}
      }
      var ja = (navigator.language || 'ja').slice(0, 2) === 'ja';
      var saved = {};
      try { saved.read = localStorage.getItem('seika-read'); saved.mean = localStorage.getItem('seika-mean'); } catch (e) {}
      setChoice('read', saved.read === 'kana' || saved.read === 'roman' ? saved.read : (ja ? 'kana' : 'roman'));
      setChoice('mean', saved.mean || (ja ? 'ja' : 'en'));
      ['read', 'mean'].forEach(function (kind) {
        song.querySelectorAll('[data-' + kind + ']').forEach(function (b) {
          b.addEventListener('click', function () {
            setChoice(kind, b.dataset[kind]);
            if (kind === 'mean' && out.children.length) show();
          });
        });
      });
    })();
  </script>
  <script src="../theme/script.js?v=202609192031"></script>
</body>
</html>
"""
    (OUT / "yomi.html").write_text(page, encoding="utf-8", newline="\n")
    print("wrote", (OUT / "yomi.html").relative_to(ROOT))


# ---------------------------------------------------------------- 一覧

def build_index():
    """礼拝で「聖歌○番」と言われたらすぐ開けて共有できるように、日本の聖歌の番号で並べる。
    ハングルの聖歌集の番号でも並べ替えられる。ハングルのページがまだ無い曲も行は出す"""
    ko_by_ja = {v["ja_no"]: v for v in VIDEOS.values() if v.get("ja_no")}
    ko_title = {s["no"]: s["ko"] for s in SONG_INDEX}
    has_page = {int(p.stem) for p in SONGS.glob("*.txt")}
    ja_pages = {k: ja_page_name(k) for k in JA_OFFICIAL_ONLY}  # ハングル版の無い日本の聖歌のページ

    ja_rows = JA_ROWS

    def row(ja_no, title_ja, ko_no, mode, with_id=True):
        """mode = 大きく出す番号。"ja" は日本の聖歌の番号（紫）、"ko" は성가の番号（青緑）。
        2行目には、もう一方の番号を出す"""
        if ko_no:
            ko_no = int(ko_no)
        if ko_no and ko_no in has_page:
            page = f"{ko_no:03d}.html"
        else:
            page = ja_pages.get(ja_no, "")
        anchor = f"j{ja_no}" if ja_no else f"k{ko_no}"
        if mode == "ja":
            num = ja_no.replace("2部", "2-")
            other = f"성가 {ko_no}" if ko_no else "ハングルの聖歌集には無い曲"
        else:
            num = str(ko_no)
            other = f"日本の聖歌 {ja_label(ja_no)}" if ja_no else "日本の聖歌には無い曲"
        sub = [f'<span lang="ko">{html.escape(ko_title.get(str(ko_no), ""))}</span>'] if ko_no else []
        has_other = ko_no if mode == "ja" else ja_no
        other_cls = ("other-ko" if mode == "ja" else "other-ja") if has_other else "other-none"
        sub.append(f'<span class="{other_cls}">{other}</span>')
        tag = '<span class="tag">準備中</span>' if not page else ""
        body = (f'<span class="num num-{mode}">{html.escape(num)}</span>'
                f'<span class="t"><span class="tt"><b>{html.escape(title_ja)}</b>{tag}</span><small>{" · ".join(sub)}</small></span>')
        link = f'<a class="go" href="{page}">{body}</a>' if page else f'<div class="go off">{body}</div>'
        share_url = SITE + (page or f"#{anchor}")
        search = " ".join(filter(None, [ja_no, str(ko_no or ""), title_ja, ko_title.get(str(ko_no), "") if ko_no else ""]))
        id_attr = f' id="{anchor}"' if with_id else ""  # 同じ曲が2つの並びに出るので、id は片方だけ
        return (f'        <li{id_attr} data-ja="{html.escape(ja_no)}" data-ko="{ko_no or ""}" data-search="{html.escape(search)}">'
                f'{link}<button type="button" class="share" data-url="{share_url}" data-title="{html.escape(title_ja)}" aria-label="{html.escape(title_ja)}を共有">🔗</button></li>')

    by_ja = [row(k, ja_rows[k], ko_by_ja.get(k, {}).get("no", ""), "ja") for k in sorted(ja_rows, key=ja_order)]
    by_ko, ko_only = [], []
    for s in SONG_INDEX:
        v = VIDEOS.get(s["no"], {})
        title = official_title(v["ja_no"]) if v.get("ja_no") and official_for(v["ja_no"]) else (v.get("ja_title") or "")
        by_ko.append(row(v.get("ja_no", ""), title or s["ko"], s["no"], "ko", with_id=False))
        if not v.get("ja_no"):
            ko_only.append(row("", title or s["ko"], s["no"], "ko"))

    page = HEAD.format(title="聖歌の一覧 | み旨の裏庭",
                       desc="日本の聖歌とハングルの聖歌（성가）の一覧。番号で探して、そのまま共有できます。",
                       version=VERSION) + f"""<body>
  <div class="container">
    <article class="song seika-index" id="idx" data-view="ja">
      <header class="song-head">
        <h1>聖歌 <span class="beta-tag">試験中</span></h1>
        <p class="title-ja">番号か題で探して、🔗 で共有できます</p>
        <p class="tool-link"><a href="yomi.html">ハングルの歌詞に読みと意味を付ける道具</a></p>
      </header>

      <div class="finder">
        <input type="search" id="q" placeholder="日本の聖歌の番号か題（例: 5、勝利、승리）" inputmode="search" autocomplete="off" aria-label="番号か題で探す">
        <div class="seg seg-order" role="group" aria-label="並び">
          <button type="button" data-order="ja" aria-pressed="true">日本の聖歌の番号</button><button type="button" data-order="ko" aria-pressed="false">성가の番号</button>
        </div>
      </div>

      <p class="list-cap" id="cap-ja">番号は <b class="c-ja">日本の聖歌</b> の番号です</p>
      <p class="list-cap" id="cap-ko" hidden>番号は <b class="c-ko">성가（ハングルの聖歌集）</b> の番号です</p>
      <ol class="songs" id="list-ja">
{chr(10).join(by_ja)}
      </ol>
      <h2 class="ko-only" id="ko-only-h">日本の聖歌に無い曲（番号は <span class="c-ko">성가</span> の番号）</h2>
      <ol class="songs" id="list-ko-only">
{chr(10).join(ko_only)}
      </ol>
      <ol class="songs" id="list-ko" hidden>
{chr(10).join(by_ko)}
      </ol>
      <p class="none" id="none" hidden>見つかりませんでした</p>

      <p class="source">「準備中」の曲は、ページをこれから作ります。日本の聖歌の番号と題は、静岡家庭教会の聖歌のページ（Internet Archive の保存）と YouTube の再生リスト（太陽と月）によります。</p>
    </article>

    <nav class="nav-links"><a href="../index.html">トップページ</a></nav>
  </div>

  <script>
    (function () {{
{SHARE_JS}
      document.querySelectorAll('.share').forEach(function (b) {{
        b.addEventListener('click', function () {{ share(b, b.dataset.title, b.dataset.url); }});
      }});

      var q = document.getElementById('q');
      var lists = {{ ja: [document.getElementById('cap-ja'), document.getElementById('list-ja'), document.getElementById('ko-only-h'), document.getElementById('list-ko-only')],
                    ko: [document.getElementById('cap-ko'), document.getElementById('list-ko')] }};
      var PLACEHOLDER = {{ ja: '日本の聖歌の番号か題（例: 5、勝利、승리）', ko: '성가の番号か題（例: 1、勝利、승리）' }};
      // 並びを替えたら、番号が裏返って入れ替わるように見せる（どちらの番号かを目で追えるように）
      function flip() {{
        var n = 0;
        lists[order].forEach(function (el) {{
          el.classList.remove('flip');
          void el.offsetWidth;
          el.classList.add('flip');
          if (el.tagName !== 'OL') return;
          [].forEach.call(el.children, function (li) {{
            if (!li.hidden) li.style.setProperty('--i', Math.min(n++, 14));
          }});
        }});
      }}
      var order = 'ja';
      function visibleItems() {{
        var out = [];
        lists[order].forEach(function (el) {{ if (el.tagName === 'OL') out = out.concat([].slice.call(el.children)); }});
        return out;
      }}
      // 数字だけなら、いまの並びの番号とぴったり同じ曲。それ以外は題に含まれる曲
      function filter() {{
        var s = q.value.trim().replace(/番$/, '');
        var digits = /^[0-9０-９]+$/.test(s) ? s.replace(/[０-９]/g, function (c) {{ return String.fromCharCode(c.charCodeAt(0) - 65248); }}) : '';
        var shown = 0;
        visibleItems().forEach(function (li) {{
          var hit = !s ? true : digits ? (li.dataset[order] === digits) : li.dataset.search.indexOf(s) >= 0;
          li.hidden = !hit;
          if (hit) shown++;
        }});
        document.getElementById('ko-only-h').hidden = order !== 'ja' || document.querySelectorAll('#list-ko-only > li:not([hidden])').length === 0;
        document.getElementById('none').hidden = shown > 0;
        return shown;
      }}
      q.addEventListener('input', filter);
      // Enter で、1曲だけ当たっていてページがあれば開く
      q.addEventListener('keydown', function (e) {{
        if (e.key !== 'Enter') return;
        var hits = visibleItems().filter(function (li) {{ return !li.hidden; }});
        var a = hits.length === 1 && hits[0].querySelector('a.go');
        if (a) location.href = a.href;
      }});
      document.querySelectorAll('button[data-order]').forEach(function (b) {{
        b.addEventListener('click', function () {{
          order = b.dataset.order;
          document.querySelectorAll('button[data-order]').forEach(function (x) {{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
          lists.ja.forEach(function (el) {{ el.hidden = order !== 'ja'; }});
          lists.ko.forEach(function (el) {{ el.hidden = order !== 'ko'; }});
          document.getElementById('idx').dataset.view = order;
          q.placeholder = PLACEHOLDER[order];
          filter();
          flip();
        }});
      }});
      // 共有されたリンク …/seika/#j5 で開いたら、その行を目立たせる
      if (location.hash) {{
        var li = document.getElementById(location.hash.slice(1));
        if (li) {{ li.classList.add('here'); li.scrollIntoView({{ block: 'center' }}); }}
      }}
    }})();
  </script>
  <script src="../theme/script.js?v=202609192031"></script>
</body>
</html>
"""
    (OUT / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print("wrote", (OUT / "index.html").relative_to(ROOT), f"({len(by_ja)} + {len(ko_only)} songs)")


def main(args):
    OUT.mkdir(exist_ok=True)
    files = [SONGS / f"{a}.txt" for a in args] if args else sorted(SONGS.glob("*.txt"))
    for f in files:
        if f.read_text(encoding="utf-8").startswith("type: intro"):
            song = parse_intro(f)
            page = render_intro(song)
        else:
            song = parse(f)
            page = render(song)
        dest = OUT / f"{int(song['no']):03d}.html"
        dest.write_text(page, encoding="utf-8", newline="\n")
        print("wrote", dest.relative_to(ROOT))
    if not args:
        for k in JA_OFFICIAL_ONLY:
            (OUT / ja_page_name(k)).write_text(render_ja_only(k), encoding="utf-8", newline="\n")
        print("wrote", len(JA_OFFICIAL_ONLY), "pages of Japanese-only songs (seika/ja-*.html)")
    build_yomi()
    build_index()
    build_sitemap()


def build_sitemap():
    """seika/sitemap.xml。サイト全体の sitemap-index.xml から読まれる（本のフォルダと同じ形）"""
    import datetime
    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p.name}</loc><lastmod>{today}</lastmod></url>"
                   for p in sorted(OUT.glob("*.html")))
    (OUT / "sitemap.xml").write_text(
        "<?xml version='1.0' encoding='utf-8'?>\n"
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8", newline="\n")
    print("wrote", (OUT / "sitemap.xml").relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])

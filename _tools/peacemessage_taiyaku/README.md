# 平和神経 韓日対訳（taiyaku/peacemessage）

『平和神経』（平和メッセージ 1〜17）の韓国語の原文と日本語版を、韓国語の段落ごとに並べる。韓国語を正とし、韓国語も日本語も1つ残らず組にする。日本語版に無い所は AI 訳で補い、日本語版が中身を書き換えた所には注を付ける。やり方と道具は『平和経』の対訳（`_tools/heiwakyou_taiyaku/`）を写したもの（2026-11-21）。

## 元にしたもの

- 韓国語: Daum カフェ「천일국 경전방」の掲示板 W7Yt「4. 평화신경」。記事 1〜17 が平和メッセージ 1〜17
  - `_tools/cafe_books/crawl.py W7Yt` と `parse.py W7Yt` で抜き出し、その写しを `src/W7Yt.jsonl` に置いた（2026-11-21）
  - 目次の記事は W8T0/88。記事 19〜24（目次では 18〜23 番のメッセージ: 天地父母天宙カイン・アベル平和安着大会、アベル国連定着と天一国完成は韓国、自叙伝5万冊、平和の主人 血統の主人、天地人真の父母定着実体み言宣布天宙大会 Ⅲ、後天時代の女性の役割）は、サイトの『平和神経』に日本語版が無いので扱っていない
  - 記事 1〜3 には本の頁の番号だけの行（「11」「12」…）が残っている。`prepare.py` で落とす。動画のリンクと「평화메시지 N」の行も落とす
- 日本語: このサイトの `peacemessage/N.html`（17編）

韓国語と日本語で、頭の行の日付・行事が違うメッセージがある（同じ題の講演を別の日・別の場所で語り直した版が元になっている）。違いは注（`diff`）に出る。

## 作り方

| 段 | するもの | 書くもの |
|---|---|---|
| 1 | `prepare.py` | `work/sections/NN.json`・`.txt`（NN はメッセージの番号2桁）。韓国語は段落（`K`）、日本語は文（`J`）。題・日付・行事の行は `[頭]`、小見出しは `[見出し]` |
| 2 | 対応表と注。`TASK-align.md` をサブエージェント（Sonnet）に渡して作った（1人あたり韓＋日で約3〜4万字、9組） | `work/align/NN.json` |
| 3 | 日本語版に無い所の AI 訳。`frags.py list` が `work/trans/todo/` に書き出し、`TASK-translate.md` で訳す | `work/trans/ja/*.json` |
| 4 | `build.py` | `taiyaku/peacemessage/`（index.html・book.js・data/*.js） |

```
python -I -X utf8 _tools/peacemessage_taiyaku/prepare.py
python -I -X utf8 _tools/peacemessage_taiyaku/check_align.py all     # 対応表（抜け・重なり・順・注の形・見出しの組）
python -I -X utf8 _tools/peacemessage_taiyaku/frags.py check        # AI 訳がそろっているか
python -I -X utf8 _tools/peacemessage_taiyaku/build.py
python -I -X utf8 _tools/peacemessage_taiyaku/preview.py 04         # 組ごとに韓国語と日本語を並べた一覧（work/preview/）
```

サイトの日本語（`peacemessage/N.html`）を直すときは、文の切れ目（。！？）を変えないこと。変えると文の番号がずれ、対応表が合わなくなる。直したら `prepare.py` → `check_align.py all` で確かめる。

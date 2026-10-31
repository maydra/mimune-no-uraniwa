# 平和経 韓日対訳（taiyaku/heiwakyou）

天一国経典『平和経』の韓国語の原文と日本語版を、韓国語の段落ごとに並べる（全178講演）。韓国語を正とし、韓国語も日本語も1つ残らず組にする。日本語版で省かれた所は AI 訳で補い、日本語版が中身を書き換えた所には注を付ける。やり方は『平和を愛する世界人として』の対訳（`_tools/heiwa_sekaijin/`）と同じ。英語は次の段で足す。

前の試み（2026-10、`E:\auto-videos-creation\gyeong-parallel\`）は、元にした韓日英の連載（Daum の掲示板 VfHJ）に77講演しか無かった。また、段落を文字数の比から推定で組んでいたので、保留にした。

## 元にしたもの

- 韓国語: Daum カフェ「천일국 경전방」の掲示板 UYjn「2. 평화경」。1記事＝1講演で182本ある
  - `_tools/cafe_books/crawl.py UYjn` と `parse.py UYjn` で抜き出し、その写しを `src/UYjn.jsonl` に置いた（2026-10-31）
  - 掲示板の記事があとで直されても、対応表がずれないようにするため
  - 3冊の韓国語の掲示板は、案内の記事 W8MH/24「천일국 3대 경전」に並んでいる（SxxP 천성경（증보판）・UYjn 평화경・W2OB 참부모경）
- 日本語: このサイトの `heiwakyou/HHNN.html`（掲示板 V1yi「2. 平和経」から組んだもの）
  - 突き合わせで見つけた組み方の誤りは、`_tools/cafe_books/build_books.py` で直した（英語の略称の所で切れた段落、第四篇14 の章の見出し）

### 講演の対応

- 記事の通し番号 [001]〜[182] は、日本語版の講演の順と同じ
- 例外1: [062]〜[066]「천국을 여는 문 참가정 1〜5」は、日本語版では第四篇14 の1講演（0414）なので、5本をつなぐ
- 例外2: 第六篇6〜10 は、日本語版は日付の順、掲示板は題の順に並んでいる。日付の行で組み直した（`prepare.py` の `ORDER_FIX`）
- 日付の行で全講演の対応を確かめた。1日ずれている講演（0905・1006・1013）は、注に書いた

## 作り方

| 段 | するもの | 書くもの |
|---|---|---|
| 1 | `prepare.py` | `work/sections/HHNN.json`・`.txt`（HHNN は篇2桁＋講演の番号2桁）。韓国語は段落（`K`）、日本語は文（`J`）。日付・場所・行事の行は `[頭]`、小見出しは `[見出し]` |
| 2 | 対応表と注。`TASK-align.md` をサブエージェントに渡して作った（1人あたり韓＋日で約5万字、68組。0414 は長いので章で2人に分け、`work/align-parts/` からつないだ） | `work/align/HHNN.json` |
| 3 | 日本語版で省かれた所の AI 訳。`frags.py list` が `work/trans/todo/` に書き出し、`TASK-translate.md` で訳す | `work/trans/ja/*.json` |
| 4 | `build.py` | `taiyaku/heiwakyou/`（index.html・book.js・data/*.js） |

```
python -I -X utf8 _tools/heiwakyou_taiyaku/prepare.py
python -I -X utf8 _tools/heiwakyou_taiyaku/check_align.py all        # 対応表（抜け・重なり・順・注の形・見出しの組）
python -I -X utf8 _tools/heiwakyou_taiyaku/frags.py check           # AI 訳がそろっているか
python -I -X utf8 _tools/heiwakyou_taiyaku/build.py
python -I -X utf8 _tools/heiwakyou_taiyaku/preview.py 0101          # 組ごとに韓国語と日本語を並べた一覧（work/preview/）
```

- 対応表の形と、注（`diff`・`ja_only`・`ja_only_ko`）の決まりは `TASK-align.md` にある
- 作業者向けの `note` には「原文の疑い:」（韓国語の掲示板の書き誤りらしい所）と「日本語の字:」（日本語版の字の誤りらしい所）が残っている。画面には出ない
- 2026-10-31 の時点で、それぞれ61件と430件ある。日本語版の字は、`build_books.py` で直す候補
  - サイトの日本語を直すときは、文の切れ目（。！？）を変えないこと。変えると文の番号がずれ、対応表が合わなくなる

## 表示

ビューアは `taiyaku/syuku_risoutengoku/index.html` を写して、`build.py` の `patch_viewer` で差し替える。どの差し替えも1回ずつ当たらなければ止まるので、あちらのビューアを直したら作り直して確かめる。

- 節の一覧は篇ごとにまとめる（optgroup）
- 小見出しの行は太字で、節の中の目次になる
- 日付・場所・行事の行は小さく出す
- 日本語版にしか無い前書き（0414 の頭）の行は、韓国語の欄を空ける
- 韓国語の第六篇の篇の名前は、掲示板に行が無い。日本語版の篇の名前と同じ題の講演から「이상세계의 주역이 될 여성」とした

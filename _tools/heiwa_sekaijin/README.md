# 平和を愛する世界人として 韓日英対訳（taiyaku/heiwa_sekaijin）

文鮮明先生の自叙伝『平和を愛する世界人として』の韓国語の原文・日本語版・英語版（As a Peace-Loving Global Citizen）を、韓国語の段落ごとに並べる。

## 元にしたもの

- 韓国語・英語: み言選集の Zip に入っていた「평화를 사랑하는 세계인으로 (한.日.Eng.).txt」（節ごとに 韓→日→英 の塊）。写しを `src/ko-ja-en.txt` に置いて使う。**リポジトリには入れていない**（`.gitignore`）
- 日本語: このサイトの `heiwa_sekaijin/*.html`（読み取りの誤りを直してある版）。元データの日本語は使わない

## 作り方

| 段 | するもの | 書くもの |
|---|---|---|
| 1 | `prepare.py` | `work/sections/NN.json`・`NN.txt`（韓日）、`work/sections-en/NN.txt`（韓英）。NN は 00 が序文、01〜67 が本文の節 |
| 2 | 対応表。`TASK-align.md`・`TASK-align-en.md` をサブエージェントに渡して作った | `work/align/NN.json`（韓日）・`work/align-en/NN.json`（韓英） |
| 3 | 訳書で省かれた所の AI 訳。`frags.py list [--lang en]` が `work/trans/todo*/` に書き出し、`TASK-translate*.md` で訳す | `work/trans/ja/*.json`・`work/trans/en/*.json` |
| 4 | 読む人向けの注。`TASK-notes.md`・`TASK-notes-en.md` | 対応表の `diff`・`ja_only`・`en_only` など |
| 5 | `build.py` | `taiyaku/heiwa_sekaijin/`（index.html・book.js・data/*.js） |

```
python -I _tools/heiwa_sekaijin/prepare.py
python -I _tools/heiwa_sekaijin/check_align.py all              # 韓日の対応表（抜け・重なり・順・注の形）
python -I _tools/heiwa_sekaijin/check_align.py all --lang en    # 韓英
python -I _tools/heiwa_sekaijin/frags.py check [--lang en]      # AI 訳がそろっているか
python -I _tools/heiwa_sekaijin/build.py
```

ビューアは `taiyaku/syuku_risoutengoku/index.html` を写して、`build.py` の `patch_viewer` で差し替える。どの差し替えも1回ずつ当たらなければ止まるので、あちらのビューアを直したら作り直して確かめる。

## 対応表（work/align*/NN.json）の1組

```json
{"ko": [3], "ja": [4, 5, 6, {"ko": "일본 선교활동 계획을 모두 준비한 뒤"}, 7],
 "note": "作業のメモ（画面に出ない）",
 "diff": ["原文では呼んだ年を書いていない（日本語版は「一九五八年」…）"],
 "ja_only": [5, 6], "ja_only_ko": "그래서 몇 차례 선교사 파견을 시도했지만 …"}
```

- `ko` は韓国語のかたまりの番号、`ja`・`en` は訳書の文の番号。訳書に無い所は `{"ko": "省かれた韓国語"}` で、その AI 訳を `work/trans/` に `節:sha1の頭10字` の鍵で置く（`frags.key`）
- `diff` は訳書が中身を書き換えている所の注（日本語の欄は日本語、英語の欄は英語）。`ja_only`・`en_only` は訳書にしか無い文で、点線と札が付き、`*_only_ko` の韓国語訳が韓国語の欄に注で出る

## 表示の決まり

- 韓国語は、日本語・英語の AI 訳の切れ目で行に切る。ただし文の途中の切れ目（訳書が語句だけ省いた所）では切らず、公式の訳のセルの中に AI 訳を色付きで差し込む
- 公式の訳の続き・AI 訳のセルは、もとの韓国語の行をまたぐ

## 英語の元データの乱れ（build.py）

- `DROP_EN`: 7章14節に紛れ込んだ5章3節の英語35文、2章7節・4章5節の重複、本文の頭に紛れた節の題を出さない
- `EN_TITLE_FIX`: 題が本文に紛れていた節の英語の題
- 英語版が段を隣の節へ移している所（1章7・8節、4章8・9節、7章5・6節）は、英語の欄を空にして両側に注
- 序文は英語が無いので全文 AI 訳。6章7節は韓国語・英語とも元データに無い（日本語だけ）

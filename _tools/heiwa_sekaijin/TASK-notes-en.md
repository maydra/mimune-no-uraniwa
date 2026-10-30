# 英語版について、読む人向けの注を書き足す（『平和を愛する世界人として』韓英対訳）

韓英の対応表（`work/align-en/NN.json`）はできている。各組の `note` は作業者向けのメモで、画面には出ない。
この作業では、画面に出す注を組に書き足す。韓日でやったこと（TASK-notes.md）と同じで、**注は英語で書く**
（英語の欄の下に出る。読むのは英語で読む人。韓日の注は日本語の欄の下に日本語で出ている）。

## 材料
- `work/align-en/NN.json` … 対応表。各組の `note` に「食い違い: …」や、省略・書き換え・移動のメモがある
- `work/sections-en/NN.txt` … 韓国語の原文（K）と英語版（E）の全文
- 手本: 韓日の注 `work/align/NN.json` の `diff`・`ja_only`・`ja_only_ko`（形は同じ。`ja` が `en` になる）

## 書き足すもの（組に足す。ほかのキーは変えない）

```json
{"ko": [19], "en": [25, 26, 27], "note": "（作業者向けのメモ。そのまま残す）",
 "diff": ["The Korean original says he settled in Japan in 1958 after three years of hardship (English edition: “a year and a half,” “October 1959”)."],
 "en_only": [26],
 "en_only_ko": "한국과 일본 사이에는 아직 국교가 없었습니다."}
```

### `diff`（英語の欄の下に「※」で出る）
英語版が**中身を書き換えている所**を、英語の読者向けに1つ1文で書く。
- 対象: 数・年・日付・期間・場所・人数・年齢・人名などが違う所／意味が逆・別になっている所／文の途中の語句が落ちて意味が変わる所／発言の中身が違う所
- 形: **“The Korean original says …. (English edition: “…”)”**。原文の中身は自分で英語に訳して書く。英語版の言い方は “ ” で引く。英語版に無いだけなら “(not in the English edition)”
- **英語版が他の節へ移した所**（1章8節の頭の農作業の段は1章7節の終わりへ、7章5節の終わりの段は7章6節の頭へ、など。`note` に書いてある）は、移された先と元の両方の組に、“The English edition places this passage at the end of the previous section (…).” のように1文で書く
- 書かないもの: 言い回し・意訳・まとめ方の違い／英語圏向けの説明の足し（それは `en_only` か書かない）／`{"ko"}` の AI 訳で補ってある所（AI 訳の行に出ているので繰り返さない。2026-10-30 に、段落ごと AI 訳の組の要約や「(not in the English edition)」の注を15、画面に出さない紛れ込みの2文にふれた注を2つ外した）
- 番号（E12・K3・組）や作業の言葉は入れない

### `en_only` と `en_only_ko`（英語版にしか無い文）
英語版にあって**原文の韓国語に無い文**を、その組の `en` にある文の番号で `en_only` に並べる。
- 文の中身がまるごと原文に無いものだけ（言い回しの足しは入れない）
- `en_only_ko` には、その文（複数なら全部）を韓国語に訳して書く。韓国語の欄に「영어판에만 있는 문장 · 영어에서 AI 번역」の札付きで出る。原文と同じく「-습니다」体で、人名・用語は原文の書き方に合わせる

## 確かめる
リポジトリの根（`E:\mimune-no-uraniwa\mimune-no-uraniwa`）で

    python -I _tools/heiwa_sekaijin/check_align.py NN --lang en

が OK になること。渡された節のファイルだけを書く。JSON を書き直すときは、`groups` の `ko`・`en`・`note` を変えない。

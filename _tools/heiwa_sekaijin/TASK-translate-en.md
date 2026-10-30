# 英語版で省かれた所の AI 訳（『平和を愛する世界人として』）

英語版（As a Peace-Loving Global Citizen）は、韓国語の原文を所々省いている。対訳では、その省かれた韓国語を英語に訳して、
英語版の文のあいだの元の位置に入れる。画面では “AI translation from Korean — not the official text” の札が付く。
日本語でやったこと（TASK-translate.md）の英語版。

## 材料（読むだけ）
- `work/trans/todo-en/NN.txt` … 訳す所の一覧。1か所ごとに印（`## 07:3fa2c9d1e0`）、訳す韓国語、その組の韓国語の全文、直前と直後の英語（英語版の訳）、対応付けのメモ
- `work/sections-en/NN.txt` … その節の韓国語と英語版の全文。人名・地名・用語の英語の書き方はここで確かめる
- 00（序文）は英語版の序文が元データに無いので、序文はまるごと訳す（前後の英語は無い）

## 書くもの: `work/trans/en/<担当の名前>.json`

```json
{"28:3fa2c9d1e0": "He was sent back to Korea. I sent him to Japan once more, but this time, too, he was caught by the Japanese police and returned.",
 "28:9b1e04c2aa": "…"}
```
印は todo の `## ` の行のものをそのまま使う。担当した印を1つ残らず訳す。

## 訳し方
- **英語版の文体に合わせる。** 一人称の語り（I）、過去の出来事は過去形、平明な英語。英語版の前後の文と自然につながる形にする（韓国語が文の途中から始まる・終わるときも、前後の英語版の文とつながる完結した文にする。ただし英語版に書いてある内容を繰り返さない）
- **人名・地名・用語は、同じ節（なければ前後の節）の英語版と同じ書き方にする**。英語版に出てこない語は、英語版の他の節の書き方、または家庭連合（統一教会）の英語の文書でふつうに使う書き方にする（하나님＝God、참사랑＝true love、참부모＝True Parents、통일교회＝Unification Church、식구＝members、정성＝devotion、탕감＝indemnity、섭리＝providence）。韓国の人名はローマ字で、英語版の綴りに合わせる
- **原文に忠実に。** 省かれた所を補うのが目的なので、要約しない・和らげない・足さない。拷問や暴力の場面もそのまま訳す
- 英語版の文は直さない。訳すのは渡された韓国語だけ

## 確かめる
リポジトリの根（`E:\mimune-no-uraniwa\mimune-no-uraniwa`）で

    python -I _tools/heiwa_sekaijin/frags.py check --lang en

を回し、自分の担当の印が「訳が無い」「ハングルが残っている」に出なくなればよい（ほかの担当の分は出ていてかまわない）。

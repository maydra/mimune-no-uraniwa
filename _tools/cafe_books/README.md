# cafe_books — Daum カフェの掲示板から本を組む

八大教材・教本のうち、このサイトに無かった3冊を、Daum カフェ「천일국 경전방」の掲示板にある日本語版から組んだ（2026-10-31）。

| 本 | 掲示板 | フォルダ | 組み方 |
|---|---|---|---|
| 天国を開く門 真の家庭 | VS04 | tengoku_mon/ | 節ごとの記事（2〜38）。章ごとに1ページ |
| 平和の主人 血統の主人 | VWMp | heiwa_syujin/ | 全文の記事 36（節ごとの記事 2〜34 と同じ訳の手直し版）。33の見出しごとに1ページ |
| 世界経典 Ⅱ | VyWS | sekai_kyouten2/ | 1記事＝1小節（514本）。部・章・節・小節は記事の頭の行と題から。章ごとに1ページ |

作り直すときはリポジトリの根から:

```
python -X utf8 _tools/cafe_books/crawl.py VS04 VWMp VyWS   # raw/ に記事を落とす（一度落としたものは取り直さない）
python -X utf8 _tools/cafe_books/parse.py VS04 VWMp VyWS   # raw/<掲示板>.jsonl
python -X utf8 _tools/cafe_books/build_books.py            # 3冊とも（1冊だけなら tengoku / heiwa / sekai）
```

そのあと、本を足したときの決まりの台本を回す（sitemap → seo_titles → extract_inline_css → build_fulltext → build_downloads → build_offline_manifest → build_gacha）。
ページの形は touitusisou/（統一思想要綱）を写している。

元の記事の誤りで直したもの:
- 世界経典 Ⅱ: 241番の節の番号「11) ムハンマド」（11 はイエス）を 12) に。398番の小節「6) 巡礼と聖地」を 6. に。小節の行が無い記事（226・373・386）は題から補う
- 平和の主人 血統の主人: 見出しの誤字「最初に灰る」「となリ得る」「りーダー」

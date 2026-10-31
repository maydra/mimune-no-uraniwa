# 原理講論の図（dp/charts）

原理講論のページ（dp/）の「表示：」に「図」を足し、『原理講論 要約訓読チャート（12時間用）』（世界平和統一堂）の図を、その図を映していたスライドの説明文が終わる文のあとに1枚ずつ出す（段落の途中にも入る）。図は元の画像を SVG に描き直したもの。2026-10-30〜31 に前編の8章（総序 28・創造原理 105・堕落論 69・終末論 54・メシヤ 43・復活論 42・予定論 22・キリスト論 31、合わせて 394枚）、続けて後編の7章（緒論 33・復帰基台摂理時代 82・モーセとイエス 128・各時代と年数 46・摂理的同時性 55・メシヤ再降臨準備時代 77・再臨論 65、合わせて 486枚）を作った。前後編で 880枚。

## 置き場所
| 物 | 場所 |
|---|---|
| ページで図を出す仕組み | `dp/charts.js`（「図」のボタン・文の終わりを探して差し込む・読んでいた所を動かさない） |
| ページごとの図（作った物） | `dp/charts/<page>.json`（`build_charts.py` が書く） |
| 図の一覧と、出す所の目印 | `_tools/dpcharts/charts.json` |
| 描き直した SVG | `_tools/dpcharts/svg/<id>.svg`（id は前編 z＋スライド番号、後編 k＋番号） |
| SVG の決まり | `_tools/dpcharts/STYLE.md` |
| 元の PPT・取り出した画像・OCR | `E:\mimune-no-uraniwa\dpcharts-work\`（著作物なのでリポジトリに入れない） |

元は Desktop の「DP 12h 前編.ppt」（642枚）・「DP 12h 後編.ppt」（896枚）。どのスライドも「上に図・下に説明文」で、両方とも画像（印刷用の CMYK の JPEG）。文字のデータは無い。前編の緑の下線・点は PowerPoint の図形で上に描いてあり、図の画像には入っていない。

## 作り方（章を足すとき）
取り出しと突き合わせのスクリプトは `_tools/dpcharts/extract/`。作業のフォルダ（dpcharts-work）を引数で渡す。

1. **取り出す**（dpcharts-work）: PowerPoint を COM で読み取り専用で開き（`analyze.ps1`）、.pptx に保存し直して `ppt/media` から図と説明文の画像を抜く（`slidemap.py`・`extract_media.py`）
2. **説明文を読む**: Windows の日本語 OCR（`ocr_batch.ps1`）。誤りは「メシヤ→メシャ」くらい
3. **段落と突き合わせる**: `map_paragraphs.py` が、説明文の3文字の組がいちばん多く重なる段落を探す。前編は642枚中568枚が一致度0.5以上
4. **描く図を選ぶ**: `chartsheet.py` で図の一覧を作って目で見る。章・節の扉と、題の下線の有無だけ違う重複は外す（創造原理は136枚 → 105枚）。`charts.json` に足す
5. **置く文を決める**: `python -I -X utf8 _tools/dpcharts/anchors.py <map_zen.json> --page <page>`。図を映していた最後のスライド（題の下線だけ違う重複の図のスライドも含める）の説明文の、最後の一文を本文の文と突き合わせ、いちばん重なる文の終わりに置く。講義が本文の2文を1文にまとめている所は、後ろの文の終わり（次の文の言い終わりがほぼそのまま重なるときだけ。本文の「のである」は除いて比べる）。目印は、その文の終わりで終わり、ページに1回しか出ない最も短い字の並び（8字以上、空白は数えない）。引用（「」『』）の中の「。」では文を切らない（堕落論で、図が引用の途中に入った）。計算で決まった所は全部、スライドの最後の一文と本文の文を並べて目で確かめる。合わない所は charts.json の "after" を手で書き、"fixed": true と "how"（理由）を付ける（anchors.py は fixed の図を計算し直さない）。説明文の無い字だけの図や、OCR が崩れた図もこれで置く。ユーザー「スライドは連続配置するのではなく、刻んで配置して欲しい」（2026-10-30）
6. **描く**: STYLE.md のとおり。見本は z095・z180。`render.py` で元の画像と重ねて見比べる（赤=元だけ、水色=SVG だけ）。後編は約50組（1組 9〜10枚）に分け、9人のサブエージェントに同時に描かせた。描き手への手順は dpcharts-work の `BRIEF_kou.md`、割り振りの表は `assign.md`（`nextgroups.py done=<組> start=<数>` で消し込み、次の組を出す）。描き手は頼まれた文の色に引っぱられて元の色を変えることがある（白い楕円を黄に、など）。**元の図の色を優先する**と手順に書き、終わった組の報告で「元と変えた所」を読んで直す
7. **フォント**: `python -X utf8 _tools/dpcharts/build_font.py`。図に出てくる字だけの BIZ UDPゴシック（OFL 版）を `dp/fonts/` に書く。元の ttf は dpcharts-work/fontsrc（リポジトリに入れない）。図の字を足したり直したりしたら回す。フォントに無い字があれば名前を出すので、図形で描くか別の字に替える（縦書きの括弧︵︶は（）を回した）
8. **まとめる**: `python -I -X utf8 _tools/dpcharts/build_charts.py`。SVG の決まり（id の頭・使わない要素・目印がページに1回だけか）を確かめ、Chrome で描いてある物の範囲を測って viewBox の余白を詰め、`dp/charts/<page>.json` を書き、ページの `<script src="charts.js" data-charts="…">` を足す・直す
9. `python _tools/root/build_offline_manifest.py`（図の JSON とフォントもオフライン保存に入る）
10. **確かめる**（`extract/` の道具。作業のフォルダは dpcharts-work）
   - 字: `python -I -X utf8 ocr_check.py prep <page>` → `ocr_batch.ps1` で `ocrcheck/<page>/orig` と `svg` を OCR → `ocr_check.py diff <page>`。元の画像と描き直しの両方を OCR にかけ、元にだけある字を出す（OCR の読み癖は両方に出るので打ち消し合う）。出た字は SVG の中身を直接見て確かめる（縦書きや丸の中の字は OCR が読み落とすだけのことが多い）。本当の誤りは「蕩減」を「蕩滅」と写したものばかり（前後編で10枚）。描き終えたら SVG を「蕩滅」で検索する
   - 置き場所: `node shot.mjs http://127.0.0.1:8766/dp/<page>.html out.png --eval "$(cat verify_after.js)"`。図が全部、決めた文の直後にあるか、蛍光ペンの中に入っていないか
   - 読んでいた所: `keep_test3.js`（「図」を出し入れしても、画面の上の字が同じ高さに残るか）
   - 字の形: `render.py --font web` で絞ったフォント、`--font other` で BIZ UDPゴシックの無い端末の代わり（游ゴシック）で描ける。web はこの PC の BIZ UDPゴシックと画素まで同じになるはず
11. **十字架**: 型を変えたときは `python -I -X utf8 _tools/dpcharts/fix_crosses.py` で、描いた図の十字架を元の画像の寸法に合わせ直せる

## ページでの動き（dp/charts.js）
- 既定は出さない。「図」を押すと JSON を読み、目印の字の並びで終わる文の直後に `<figure class="dpc-fig">` を差し込む。文のあとに字が続けば、字のノードを割って間に入れる（段落の途中）。段落の終わりなら次の `<br>` のあと。差し込んだら `dpchartsplaced` を出し、reader.js が字のノードを取り直す。状態は localStorage の `dp_charts`
- 置く所が蛍光ペンの span の中なら、span を二つに割って図を外に出す。中に置くと、暗い配色の蛍光ペンの字の色（theme/style.css の `[style*="FCD2E7"] *`）が図の字にかかる
- 図の幅は、図の 1 単位を 0.55px にした大きさ（34em と画面の幅が上限）。後編の図は元の画像が小さい（幅 822、前編は 1303）ので、JSON の "u"（0.55×1303÷822）で前編と同じ見た目の大きさにする。viewBox を描いてある物の範囲に詰めているので、そのままだと物の少ない図ほど字が大きくなる
- 出し入れの前後で読んでいた所を保つのは、画面の上の字を「本文の何字目か」で覚えて戻す方法（charts.js の keepPlace）。字のノードで覚えると、図が同じノードの途中に入ってノードが割れたときに戻し先がずれた（復活論で 38px。2026-10-31 に直した）
- 図の字は本文の字数に入れない（theme/reader.js の NOT_BODY、color_filter.js の保護）。出し入れの前後で、画面の上にあった字が同じ高さに来るようにスクロールを戻す
- 「図」は3か所にある: ページの頭の「表示：」の並び、上の帯（reader.js の `#reader-crumb`）の ☰ の手前、目次の引き出し。帯の「図」は押しても引き出しを開かない。どれも `window.dpCharts` を呼ぶ。帯に置いたのは、ユーザー「スライド表示ボタンがなかなか出ないぬ」（読んでいる途中からは、ページの頭まで戻らないと押せなかった）
- 図はまず縦横比（viewBox と同じ）の枠だけを置き、画面の上下 1500px に入った枠から SVG を入れる（IntersectionObserver）。枠の高さは SVG を入れても変わらないので、スクロールの位置は動かない
- 図の字のフォントは `'BIZ UDPGothic','DPC Gothic',…`（charts.js の CSS が SVG の font-family 属性に勝つ）。DPC Gothic は dp/fonts の絞ったフォントで、@font-face は JSON の fonts を読んだとき（「図」を出したとき）に足す。BIZ UDPゴシックの入っている Windows はダウンロードしない。ユーザーの iPhone で字が箱からはみ出していた（2026-10-31）
- 字を縦の真ん中にそろえる `dominant-baseline` は、`build_charts.py` が JSON に書くときに、`<g>` から中の `<text>`・`<tspan>` 1つずつへ書き写す（`pin_baselines`）。Safari（iPhone も）はこの指定を親から引き継がず（WebKit のバグ 139258）、`<g>` にまとめて付けた字が字の下の線にそろって、箱の上へはみ出していた（2026-10-31、ユーザーのスクショ。フォントを配っても直らなかった）。Chrome は引き継ぐので、Windows では気づけない。確かめるときは、Chrome に `text:not([dominant-baseline]),tspan:not([dominant-baseline]){dominant-baseline:auto}` を足すと Safari と同じずれ方になる
- JSON の URL には中身のハッシュを付ける。dp/ の JS・JSON は SW がキャッシュ優先で出すので、付けないと直した図が1回遅れて届く

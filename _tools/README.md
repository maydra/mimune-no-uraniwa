# _tools — サイトの保守スクリプト置き場

フォルダ名が `_` で始まるのは意図的。GitHub Pages（Jekyll ビルド）は
`_` 始まりのフォルダを公開しないので、**ここに置いたものはサイトに出ない**。
以前はリポジトリ直下と `tools/` に散らばって、全部そのまま公開されていた。

- `root/` … 以前リポジトリ直下にあった一括処理スクリプト（cache_bust.py など）
- `dp/` … 原理講論ページの生成・修理に使ったもの
- `CHANGELOG.md` … サイトの仕組み・見た目を変えたときの編集履歴
- 直下 … 以前の `tools/`（build_fulltext.py＝検索インデックスの作成、ほか）

実行は**リポジトリの根から**（例: `python _tools/root/cache_bust.py`）。
多くのスクリプトはカレントディレクトリ基準でファイルを歩くため、
_tools の中で実行すると何も見つからないか、間違った場所を書き換える。

HTML を書き換えるスクリプトを回したあとは `python _tools/root/cache_bust.py` で
`?v=` を打ち直すこと（これを忘れると、直しても利用者に届かない）。

## 1ファイル版（download/）

`python _tools/root/build_downloads.py` で、各本を1つの HTML にまとめて `download/` に書き出し、
各本の目次に「📄 1ファイルで保存」ボタンを置く（聖書は書ごと）。
「この本をオフライン保存」はブラウザの保存領域に頼るので、機内で開けないことがある。こちらは端末にファイルとして残る。
本文を直したら、その本だけ作り直す: `python _tools/root/build_downloads.py dp kitou`

## 検索エンジン向け（2026-10-27）

- サイトマップは GitHub Actions（`.github/workflows/sitemap.yml`）が push のたびに `_tools/root/build_sitemap.py` で作り直す。手で回さなくていい
- 同じ Actions が、title・description・本文の文字が変わったページだけ最終更新日（lastmod）を新しくし（記録は `_tools/root/sitemap-lastmod.json`、手で直さない）、その URL を IndexNow で Bing などに知らせる（`_tools/root/indexnow.py`。鍵は根の `e54f07b2…txt`、消さない）。`?v=` の打ち直しだけでは日付は変わらない。Google は IndexNow を使わないので、Google にはサイトマップの日付で知らせる
- **本やページを足したら `python _tools/root/seo_titles.py --all` を回す。** 見分けのつかない title に見出しを足し、
  description・canonical・og:〜（LINE や X で共有したときのカード）の無いページに足す。付いているものは触らないので、何度回してもいい
- サイトは maydra.github.io の下のフォルダにあるので、robots.txt は Google に読まれない。サイトマップは Search Console
  から `sitemap-index.xml` を送って知らせる。ページが変わった push のあとは、同じ Actions が Search Console の API で送り直す
- **Google に載っているかの一覧は `_tools/seo/index-status.md`**（本ごとに、載っているページ数と載っていない理由）。
  Actions の index-status が週2回（日本時間の月・火の朝）URL 検査をかけて書き直す。中身は `_tools/root/search_console.py`
- Search Console の API に使う鍵は、サービスアカウント `online-count@mimune-online.iam.gserviceaccount.com`（「いま○人」と同じ）のもの。
  Search Console の「ユーザーと権限」に「フル」で足してあり、GCP のプロジェクト mimune-online で Search Console API を有効にしてある。
  Actions では secret の `GSC_KEY` に鍵の JSON の中身を入れる。手元で回すときは `GSC_KEY_FILE` に鍵のファイルの場所を入れる
- URL の `&` は `%26` にしない（Google は `syuku_&_risoutengoku/` を `&` のまま登録している）。HTML とサイトマップの中では `&amp;` と書く
- 存在しない URL には `404.html` が出る（検索欄と目次へのリンク）。どの階層の URL にも同じものが出るので、リンクは `/mimune-no-uraniwa/` から書く

## ページの CSS は theme/pages/ に（2026-10-11）

各ページに同じ <style>（1ページ約10KB）が埋め込まれていたので、`theme/pages/<ハッシュ>.css` に出して
`<link>` で読むようにした。ページを移っても CSS はキャッシュから出る。

- 見た目を直すときは、`theme/pages/` の CSS を直せば、それを使う全ページに効く
- `<style>` をページに書き込むスクリプト（`_tools/upgrade_*.py` など）を回したら、最後に
  `python _tools/root/extract_inline_css.py` を回す。2ページ以上で同じ `<style>` は共有ファイルに出る
- 同じとき、`backdrop-filter`（ぼかし）と、開いたときの `fadeInDown` / `fadeInUp` も落とす。
  iPhone SE でスクロールが重くなる原因だった
- フォントは端末の明朝（2026-10-24 から。`_tools/root/lighten_pages.py` の FONT_STACK）。Google Fonts の `<link>` は
  ページに書かない（Android で端末に明朝が無いときだけ theme/script.js が読む。あるかどうかは canvas で描き比べて
  localStorage の `font.mincho` に覚える）。古い `_tools/upgrade_*.py` などの雛形にはまだ Noto Serif JP の
  `<link>` が残っているので、回したら `python _tools/root/lighten_pages.py webfont theme-boot` も回す
- 共有ファイルを足したら `python _tools/root/build_offline_manifest.py` も回す（オフライン保存が一緒に持っていく）
- `theme/` の CSS・JS は、Service Worker がネットワーク優先で取る。直せば次に開いたときに届く

## ホームの「いま○人が利用しています」（2026-10-18）

`_tools/online-count/` の Cloudflare Worker（https://mimune-online.dreamerhigh2015.workers.dev ）が、
Google アナリティクス（プロパティ 520812725）の直近5分の人数を `{"active":N,"minutes":5}` で返す。ホームの `#online-now` がそれを読む。

- アナリティクスを読むのは Google Cloud のプロジェクト mimune-online のサービスアカウント `online-count@mimune-online.iam.gserviceaccount.com`。プロパティには「閲覧者」で入っている
- その鍵は Cloudflare の secret `GA_KEY` にだけある。リポジトリには置かない。作り直したら `npx wrangler secret put GA_KEY < 鍵.json`
- Worker を直したら `_tools/online-count` で `npx wrangler deploy`（Cloudflare のアカウント dreamerhigh2015 にログインが要る: `npx wrangler login`）
- アナリティクスに聞くのは Worker 1つあたり1分に1回まで。取れないときは 503 を返し、ホームは行を見せない（場所は空けたまま。2026-10-24 から、後から出して一覧を押し下げないように）
- ホームが Worker に聞きに行くのは、最初の描画が画面に出てから（index.html の `afterPaint()`。gtag の本体も同じ）

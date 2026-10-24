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

## ページの CSS は theme/pages/ に（2026-10-11）

各ページに同じ <style>（1ページ約10KB）が埋め込まれていたので、`theme/pages/<ハッシュ>.css` に出して
`<link>` で読むようにした。ページを移っても CSS はキャッシュから出る。

- 見た目を直すときは、`theme/pages/` の CSS を直せば、それを使う全ページに効く
- `<style>` をページに書き込むスクリプト（`_tools/upgrade_*.py` など）を回したら、最後に
  `python _tools/root/extract_inline_css.py` を回す。2ページ以上で同じ `<style>` は共有ファイルに出る
- 同じとき、`backdrop-filter`（ぼかし）と、開いたときの `fadeInDown` / `fadeInUp` も落とす。
  iPhone SE でスクロールが重くなる原因だった
- フォントは端末の明朝（2026-10-24 から。`_tools/root/lighten_pages.py` の FONT_STACK）。Google Fonts の `<link>` は
  ページに書かない（Android だけ theme/script.js が読む）。古い `_tools/upgrade_*.py` などの雛形にはまだ Noto Serif JP の
  `<link>` が残っているので、回したら `python _tools/root/lighten_pages.py webfont theme-boot` も回す
- 共有ファイルを足したら `python _tools/root/build_offline_manifest.py` も回す（オフライン保存が一緒に持っていく）
- `theme/` の CSS・JS は、Service Worker がネットワーク優先で取る。直せば次に開いたときに届く

## ホームの「いま○人が利用しています」（2026-10-18）

`_tools/online-count/` の Cloudflare Worker（https://mimune-online.dreamerhigh2015.workers.dev ）が、
Google アナリティクス（プロパティ 520812725）の直近5分の人数を `{"active":N,"minutes":5}` で返す。ホームの `#online-now` がそれを読む。

- アナリティクスを読むのは Google Cloud のプロジェクト mimune-online のサービスアカウント `online-count@mimune-online.iam.gserviceaccount.com`。プロパティには「閲覧者」で入っている
- その鍵は Cloudflare の secret `GA_KEY` にだけある。リポジトリには置かない。作り直したら `npx wrangler secret put GA_KEY < 鍵.json`
- Worker を直したら `_tools/online-count` で `npx wrangler deploy`（Cloudflare のアカウント dreamerhigh2015 にログインが要る: `npx wrangler login`）
- アナリティクスに聞くのは Worker 1つあたり1分に1回まで。取れないときは 503 を返し、ホームは行ごと出さない

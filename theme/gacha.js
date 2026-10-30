/* theme/gacha.js — ガチャ（ランダムに一節を見る）の振り分け
 *
 * ホームの「🎲 み言をランダムに見る」(gacha.html) と、各本の目次の
 * 「📖 今日のみ言をこの本からランダムに探す」(<本>/random.html) が読む。
 * data/gacha.json（_tools/root/build_gacha.py が作る）の [ページ, 本文の字数] から、
 * 字数に比例して1ページを選んで飛ぶ。どの字も同じ確率で当たる。
 * 着いたページでは theme/reader.js が ?gacha を見て、本文から一節を選んで色を付ける。
 *
 *   gacha.html       … み言の本すべてから（solo の本は入れない）。?gacha=1
 *   <本>/random.html … その本から。?gacha=book（「もう一回」がその本の random.html に戻る）
 */
(function () {
    'use strict';

    var me = document.currentScript;
    var root = new URL('../', me.src);                 // サイトの根（自分は theme/ にいる）
    var here = new URL('.', location.href).pathname;   // このページのフォルダ
    var book = here.indexOf(root.pathname) === 0
        ? decodeURIComponent(here.slice(root.pathname.length)).replace(/\/$/, '')
        : '';

    function fail(err) {
        console.error('ページ取得失敗:', err);
        var p = document.createElement('p');
        p.textContent = 'ページ取得に失敗しました。';
        p.style.fontWeight = 'bold';
        var back = document.createElement('a');
        back.href = book ? 'index.html' : new URL('index.html', root).href;
        back.textContent = book ? 'この本の目次に戻る' : 'トップページに戻る';
        document.body.append(p, back);
    }

    fetch(new URL('data/gacha.json', root))
        .then(function (res) { return res.json(); })
        .then(function (d) {
            var pages = d.pages.filter(function (p) {
                var b = p[0].split('/')[0];
                return book ? b === book : d.solo.indexOf(b) < 0;
            });
            if (!pages.length) throw new Error('利用可能な本文ページが見つかりませんでした。');
            var r = Math.random() * pages.reduce(function (sum, p) { return sum + p[1]; }, 0);
            var hit = pages[pages.length - 1][0];
            for (var i = 0; i < pages.length; i++) {
                r -= pages[i][1];
                if (r < 0) { hit = pages[i][0]; break; }
            }
            // 本の名前は着いたページの札に出す（ページの題は本によって書き方がまちまち）
            try {
                sessionStorage.setItem('reader.gacha', JSON.stringify({ p: hit, b: d.books[hit.split('/')[0]] || '' }));
            } catch (e) { }
            // replace: 履歴にこのページを残さない。href だと着地先で「戻る」を押した
            // 瞬間ここへ戻って再抽選され、元のページに帰れなくなる
            location.replace(new URL(hit, root).href + '?gacha=' + (book ? 'book' : '1'));
        })
        .catch(fail);
})();

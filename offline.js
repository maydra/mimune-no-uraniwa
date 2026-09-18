/* 「📥 この本をオフライン保存」ボタン（各書籍の index.html が読み込む）。
 *
 * 押すと data/offline-manifest.json からその書籍の全ページ一覧を取り、
 * sw.js に CACHE_BOOK で渡してまとめて保存する。進捗はボタンの文字で見せる。
 * 保存済みの記録は localStorage（mimune.offline.books）。offline.html が
 * この記録を読んで「保存済みの本」一覧を出す。
 *
 * Service Worker が使えない環境ではボタンを出さない（hidden のまま）。
 */
(function () {
    var btn = document.getElementById('offline-save-btn');
    if (!btn) return;
    if (!('serviceWorker' in navigator) || !window.caches) return;

    var book = btn.dataset.book;
    var root = new URL('..', location.href);   // 書籍フォルダの1つ上 = サイトの根

    // ふだんは theme/script.js が登録するが、独自テーマの書籍
    // (heiwa_sekaijin など) に直接来たときのために、ここでも登録して
    // おく。register は同じ sw.js なら何度呼んでも安全。
    navigator.serviceWorker.register(new URL('sw.js', root)).catch(function () { });
    var KEY = 'mimune.offline.books';
    var state = 'idle';
    var urls = null;

    function readReg() {
        try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; }
    }
    function writeReg(r) {
        try { localStorage.setItem(KEY, JSON.stringify(r)); } catch (e) { }
    }
    function label() {
        if (state === 'saved') btn.textContent = '✓ オフラインで読めます（押すと解除）';
        else if (state === 'idle') btn.textContent = '📥 この本をオフライン保存';
    }

    async function buildUrls() {
        if (urls) return urls;
        var res = await fetch(new URL('data/offline-manifest.json', root));
        var man = await res.json();
        var files = (man.books && man.books[book]) || [];
        if (!files.length) throw new Error('book not in manifest');
        var list = files.map(function (p) { return new URL(p, root).href; });
        // 表示に要る共有ファイルを、いま実際に使っている ?v= つきで足す
        document.querySelectorAll(
            'link[rel="stylesheet"][href*="theme/style.css"], script[src*="theme/script.js"], link[rel="icon"]'
        ).forEach(function (el) {
            list.push(new URL(el.href || el.src, location.href).href);
        });
        list.push(new URL('offline.html', root).href);
        urls = Array.from(new Set(list));
        return urls;
    }

    navigator.serviceWorker.addEventListener('message', function (e) {
        var m = e.data || {};
        if (m.book !== book) return;
        if (m.type === 'BOOK_PROGRESS') {
            btn.textContent = '保存中… ' + m.done + ' / ' + m.total;
        } else if (m.type === 'BOOK_DONE') {
            state = 'saved';
            var r = readReg();
            r[book] = {
                pages: m.total,
                savedAt: Date.now(),
                title: (document.title || book).split(/[|｜/]/)[0].trim() || book
            };
            writeReg(r);
            btn.disabled = false;
            if (m.failed) {
                btn.textContent = '✓ 保存しました（' + m.failed + '件は取得できず）';
            } else {
                label();
            }
        } else if (m.type === 'BOOK_REMOVED') {
            state = 'idle';
            var r2 = readReg();
            delete r2[book];
            writeReg(r2);
            btn.disabled = false;
            label();
        }
    });

    btn.addEventListener('click', async function () {
        try {
            var ready = await navigator.serviceWorker.ready;
            var sw = ready.active;
            if (!sw) return;
            if (state === 'saved') {
                if (!confirm('この本のオフライン保存を解除しますか？')) return;
                btn.disabled = true;
                btn.textContent = '解除中…';
                sw.postMessage({ type: 'REMOVE_BOOK', book: book, urls: await buildUrls() });
                return;
            }
            if (state !== 'idle') return;
            state = 'working';
            btn.disabled = true;
            btn.textContent = '準備中…';
            var list = await buildUrls();
            btn.disabled = false;
            sw.postMessage({ type: 'CACHE_BOOK', book: book, urls: list });
        } catch (e) {
            state = 'idle';
            btn.disabled = false;
            btn.textContent = '保存できませんでした。もう一度押してください';
        }
    });

    state = readReg()[book] ? 'saved' : 'idle';
    label();

    // スマホ・タブレット（タッチ端末）だけに出す。PC で押しても
    // 「何が起きたか分からない」ので、マウス環境では隠しておく。
    // ただし PC で保存済みの記録があるときは、解除できるように出す。
    var coarse = false;
    try { coarse = matchMedia('(pointer: coarse)').matches; } catch (e) { }
    if (coarse || state === 'saved') btn.hidden = false;
})();

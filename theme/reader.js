/* theme/reader.js — 長い本文ページの読書支援
 *
 * 1ページが2万〜5万字ある本が52冊あり、見出しも1ページに40個入る。
 * そこで「いま本のどこを読んでいるか」を常に出し、迷子にならないようにする。
 *
 *   ・上端の進捗バー
 *   ・現在位置バー（見出しの道筋。押すと目次が開く）
 *   ・目次の引き出し（見出し一覧＋いま読んでいる所を光らせる）
 *   ・しおり（前回の続きへ。トップと本の目次に「続きから読む」）
 *   ・手で挟むしおり（目次の引き出しの「ここにしおり」か b。トップと本の目次に一覧）
 *   ・拡大縮小しても読んでいた場所を保つ
 *   ・キーボード（← → で前後のページ、j k で見出し送り、t で目次、b でしおり）
 *
 * **位置は「画面の一番上にある文字が、本文の何文字目か」で持つ。**
 * 本文が <br> 区切りで段落タグの無い本が多く（生涯路程7は <p> が0個で <br> が647個）、
 * 要素を目印にできない。文字数なら、拡大しても字を大きくしても同じ場所に戻れる。
 *
 * theme/script.js から読み込まれる。HTML には手を入れない。
 */
(function () {
    'use strict';

    // 読み物ではないページ。目次・検索・ランダムには要らない
    var SKIP = /(?:^|\/)(index|mokuji|random|gacha|search-all|404|offline|test_output|google[0-9a-f]+)\.html$/i;
    // 本文ではない所（ここの文字は数に入れない）
    var NOT_BODY = 'script,style,nav,rt,rp,.page-nav,.typo-box,#reader-ui,#stacked-header-container,.toc,.hits';
    var TOP = 96;              // 「画面の上」とみなす高さ
    var MIN_CHARS = 2500;      // これより短いページには出さない
    var STORE = 'reader.pos.';
    var MARKS = 'reader.marks';    // 手で挟むしおり。何か所でも。新しい順
    var RECENT = 'reader.recent';  // ページをまたいだ「最後に読んだ所」。本ごとに1件、新しい順
    // サイトの根（/mimune-no-uraniwa/）。自分が theme/ の下にいることから割り出す
    var ROOT = (function () {
        try {
            var me = document.currentScript;
            if (me && me.src) return new URL('../', me.src).pathname;
        } catch (e) { }
        return '/';
    })();

    if (window.__readerReady) return;
    window.__readerReady = true;

    var nodes = [];            // 本文のテキストノード
    var starts = [];           // 各ノードが本文の何文字目から始まるか
    var total = 0;             // 本文の総字数
    var heads = [];            // 見出し
    var cur = 0;               // いま画面の上にある文字の位置
    var ui = null, bar = null, crumb = null, drawer = null, items = [];
    var restoring = false;

    // ---- 本文の文字を数える ------------------------------------------------
    function collect() {
        nodes = []; starts = []; total = 0;
        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
            acceptNode: function (n) {
                if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                var p = n.parentElement;
                if (!p || p.closest(NOT_BODY)) return NodeFilter.FILTER_REJECT;
                return NodeFilter.FILTER_ACCEPT;
            }
        });
        var n;
        while ((n = walker.nextNode())) {
            nodes.push(n); starts.push(total); total += n.nodeValue.length;
        }
    }

    function nodeIndex(pos) {        // 文字位置 → ノード番号（二分探索）
        var lo = 0, hi = nodes.length - 1, best = 0;
        while (lo <= hi) {
            var mid = (lo + hi) >> 1;
            if (starts[mid] <= pos) { best = mid; lo = mid + 1; } else { hi = mid - 1; }
        }
        return best;
    }

    // 画面の上にある文字は何文字目か。キャレット API で本文の字を直に拾う
    function caretAt(x, y) {
        var r = null;
        if (document.caretRangeFromPoint) {
            r = document.caretRangeFromPoint(x, y);
        } else if (document.caretPositionFromPoint) {
            var p = document.caretPositionFromPoint(x, y);
            if (p) { r = document.createRange(); r.setStart(p.offsetNode, p.offset); r.collapse(true); }
        }
        return r;
    }

    function posOfNode(node, offset) {
        var i = nodes.indexOf(node);
        if (i < 0) return -1;
        return starts[i] + Math.min(offset, node.nodeValue.length);
    }

    function topPos() {
        var w = window.innerWidth;
        // 中央・左寄り・右寄りと、少し下へずらしながら当てる（余白に当たると取れない）
        var xs = [w * 0.5, w * 0.35, w * 0.65], ys = [TOP, TOP + 24, TOP + 60, TOP + 120];
        for (var yi = 0; yi < ys.length; yi++) {
            for (var xi = 0; xi < xs.length; xi++) {
                var r = caretAt(xs[xi], ys[yi]);
                if (!r) continue;
                var p = posOfNode(r.startContainer, r.startOffset);
                if (p >= 0) return p;
            }
        }
        // 取れなければ、画面の高さの割合から見当をつける
        var h = document.documentElement.scrollHeight - window.innerHeight;
        return h > 0 ? Math.round(total * (window.scrollY / h)) : 0;
    }

    function scrollToPos(pos, keep) {
        if (!nodes.length) return;
        var i = nodeIndex(pos);
        var r = document.createRange();
        r.setStart(nodes[i], Math.min(pos - starts[i], nodes[i].nodeValue.length));
        r.collapse(true);
        var rect = r.getBoundingClientRect();
        if (!rect || (!rect.top && !rect.height)) {            // 折り返しの境目は箱が取れない
            rect = nodes[i].parentElement.getBoundingClientRect();
        }
        restoring = true;
        window.scrollBy(0, rect.top - (keep == null ? TOP : keep));
        setTimeout(function () { restoring = false; }, 60);
    }

    // ---- 見出し ------------------------------------------------------------
    function clean(el) {
        var c = el.cloneNode(true);
        Array.prototype.forEach.call(c.querySelectorAll('rt,rp'), function (r) { r.remove(); });
        return (c.textContent || '').replace(/[◆▸▶･・]/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function collectHeads() {
        heads = [];
        // ページの題と同じ見出し（多くの本は <h1> が <title> の写し）は道筋に出さない。
        // 「第一節　…／真の御父母様の生涯路程 7」と毎回出ても場所の手がかりにならない
        // 題は「第一節　…　家庭教会は私の天国/真の御父母様の生涯路程 7」のように
        // 「節の名前／書名」で書かれている。書名の方は、どのページでも同じなので
        // 場所の手がかりにならない。書名だけの見出しは並べず、節の名前に
        // くっついている書名は切り落とす
        var parts = (document.title || '').split('/');
        var book = parts.length > 1 ? parts[parts.length - 1].trim() : '';
        var flatBook = book.replace(/[\s　]/g, '');
        var all = document.querySelectorAll('h1,h2,h3,h4,h5,h6');
        Array.prototype.forEach.call(all, function (h) {
            if (h.closest(NOT_BODY) || h.classList.contains('page-title')) return;
            var t = clean(h);
            if (!t) return;
            var flat = t.replace(/[\s　]/g, '');
            var isTitle = flatBook.length > 3 && flat === flatBook;
            if (!isTitle && flatBook.length > 3 && flat.length > flatBook.length &&
                flat.slice(-flatBook.length) === flatBook) {
                t = t.replace(/[\s　]*[\/／][\s　]*[^\/／]*$/, '').trim() || t;
            }
            heads.push({ el: h, level: +h.tagName.substring(1), text: t, isTitle: !!isTitle });
        });
        // ページの頭では、同じ節の名前が二度書いてあることがある（<h1> が <title> の
        // 写しで、少し下に同じ名前が <h2> で入る。題の方は切れていることもある）。
        // 書名だけの見出しを飛ばして並べ直し、隣り合う二つが同じ言い換えなら前を落とす
        var live = heads.filter(function (h) { return !h.isTitle; }).slice(0, 4);
        for (var i = 0; i < live.length - 1; i++) {
            var a = live[i].text.replace(/[\s　]/g, '');
            var b = live[i + 1].text.replace(/[\s　]/g, '');
            if (a.length < 6 || b.length < 6) continue;
            if (a.indexOf(b) === 0 || b.indexOf(a) === 0) live[i].isTitle = true;
        }
        depths();
    }

    // 見出しの深さは、そのページに出てくる段だけで数え直す。
    // 本によって始まりが <h2> だったり <h4> だったりするので、タグの数字を
    // そのまま使うと、一番浅い見出しが深い所から始まってしまう
    function depths() {
        var used = [];
        heads.forEach(function (h) {
            if (h.isTitle) return;
            if (used.indexOf(h.level) < 0) used.push(h.level);
        });
        used.sort(function (a, b) { return a - b; });
        heads.forEach(function (h) {
            var d = used.indexOf(h.level);
            h.depth = d < 0 ? 0 : Math.min(d, 4);
        });
    }

    function currentHead() {
        var found = -1;
        for (var i = heads.length - 1; i >= 0; i--) {
            if (heads[i].el.getBoundingClientRect().top <= TOP + 8) { found = i; break; }
        }
        return found;
    }

    function pathTo(i) {
        if (i < 0) return [];
        var out = [heads[i]], lv = heads[i].level;
        for (var k = i - 1; k >= 0; k--) {
            if (heads[k].level < lv) { out.unshift(heads[k]); lv = heads[k].level; }
        }
        return out;
    }

    // ---- 画面を作る --------------------------------------------------------
    function css() {
        var s = document.createElement('style');
        s.id = 'reader-style';
        s.textContent = [
            '#reader-ui{position:fixed;inset:0 0 auto 0;z-index:9000;pointer-events:none;font-family:inherit;padding-right:72px}',
            '#reader-progress{height:3px;width:0;background:linear-gradient(90deg,#6366f1,#ec4899);transition:width .12s linear}',
            '#reader-crumb{pointer-events:auto;display:none;align-items:center;gap:.4em;max-width:min(96vw,1000px);',
            'margin:.35rem auto 0;padding:.35em .9em;border-radius:999px;font-size:.78rem;line-height:1.4;',
            'background:rgba(255,255,255,.92);color:#333;border:1px solid rgba(0,0,0,.08);',
            'box-shadow:0 2px 10px rgba(0,0,0,.10);cursor:pointer;',
            'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
            '#reader-crumb.on{display:flex}',
            '#reader-crumb .sep{opacity:.45;margin:0 .15em;flex:0 0 auto}',
            '#reader-crumb .tail{font-weight:600}',
            '#reader-crumb>span:not(.sep):not(.menu){overflow:hidden;text-overflow:ellipsis}',
            '#reader-crumb>span:not(.sep):not(.menu):not(.tail){flex:0 1 auto;opacity:.72;max-width:12em}',
            '#reader-crumb .tail{flex:1 1 auto;min-width:4em}',
            '#reader-crumb .menu{flex:0 0 auto;margin-left:.5em;opacity:.55;font-size:.9em}',
            'body.dark-mode #reader-crumb{background:rgba(26,26,46,.92);color:#e6e6f0;border-color:rgba(255,255,255,.14)}',
            '#reader-drawer{position:fixed;inset:0;z-index:10000;display:none;pointer-events:auto}',
            '#reader-drawer.on{display:block}',
            '#reader-drawer .veil{position:absolute;inset:0;background:rgba(0,0,0,.35)}',
            '#reader-drawer .panel{position:absolute;top:0;right:0;height:100%;width:min(86vw,380px);',
            'background:#fff;color:#222;overflow:auto;-webkit-overflow-scrolling:touch;',
            'box-shadow:-8px 0 28px rgba(0,0,0,.18);padding:1rem .9rem 3rem}',
            'body.dark-mode #reader-drawer .panel{background:#1a1a2e;color:#e6e6f0}',
            '#reader-drawer h4{margin:.2rem 0 .7rem;font-size:.95rem;opacity:.75;font-weight:600}',
            '#reader-drawer a.item{display:block;position:relative;padding:.42em .5em;border-radius:7px;',
            'text-decoration:none;color:inherit !important;font-size:.88rem;line-height:1.45}',
            '#reader-drawer a.item:hover{background:rgba(127,127,127,.14)}',
            '#reader-drawer a.item.here{background:rgba(99,102,241,.16)}',
            '#reader-drawer a.item.here::after{content:"";position:absolute;left:-.55rem;top:.5em;bottom:.5em;',
            'width:3px;border-radius:2px;background:#6366f1}',
            // 段が深くなるほど左へ下げ、字を小さく薄くする。縦線で親子を見せる
            '#reader-drawer .d0{font-weight:700;margin-top:.55em}',
            '#reader-drawer .d0:first-child{margin-top:0}',
            '#reader-drawer .d1,#reader-drawer .d2,#reader-drawer .d3,#reader-drawer .d4{',
            'border-left:1px solid rgba(127,127,127,.3)}',
            '#reader-drawer .d1{margin-left:.55em;padding-left:.85em;font-size:.855rem}',
            '#reader-drawer .d2{margin-left:1.5em;padding-left:.85em;font-size:.83rem;opacity:.88}',
            '#reader-drawer .d3{margin-left:2.45em;padding-left:.85em;font-size:.81rem;opacity:.8}',
            '#reader-drawer .d4{margin-left:3.4em;padding-left:.85em;font-size:.79rem;opacity:.74}',
            '#reader-drawer a.item.here{opacity:1;font-weight:700}',
            '#reader-drawer .tools{margin:.2rem 0 1rem;display:flex;flex-wrap:wrap;gap:.4rem}',
            '#reader-drawer .tools a{flex:1 1 auto;text-align:center;padding:.5em .7em;border-radius:8px;',
            'font-size:.82rem;text-decoration:none;background:rgba(127,127,127,.14);color:inherit !important}',
            '#reader-drawer .side{margin-top:1.2rem;border-top:1px solid rgba(127,127,127,.25);padding-top:.7rem}',
            '#reader-drawer .side a{display:block;padding:.5em .5em;font-size:.82rem;line-height:1.5;','text-decoration:none;color:inherit !important;border-radius:7px}','#reader-drawer .side a:hover{background:rgba(127,127,127,.14)}','#reader-drawer .side a>span{display:block;opacity:.55;font-size:.74rem}','#reader-drawer .side a>em{display:block;opacity:.6;font-size:.74rem;font-style:normal}','#reader-drawer .side a>b{display:block;font-weight:600}',
            '#reader-drawer .side span{opacity:.6;font-size:.74rem}',
            '#reader-resume{pointer-events:auto;position:fixed;left:50%;transform:translateX(-50%);bottom:1.1rem;',
            'z-index:10001;display:none;align-items:center;gap:.6em;padding:.55em .8em .55em 1em;border-radius:999px;',
            'font-size:.83rem;background:rgba(30,30,40,.92);color:#fff;box-shadow:0 4px 18px rgba(0,0,0,.28)}',
            '#reader-resume.on{display:flex}',
            '#reader-resume button{font:inherit;color:#fff;background:rgba(255,255,255,.18);border:0;',
            'border-radius:999px;padding:.35em .9em;cursor:pointer}',
            '#reader-resume .x{background:none;padding:.2em .5em;opacity:.7}',
            '#reader-drawer .tools a.pin{flex:1 1 100%;font-weight:700;background:rgba(99,102,241,.18)}',
            '#reader-drawer .marks{margin:0 0 1rem}',
            '#reader-drawer .marks:empty{display:none}',
            '#reader-drawer .mark{display:flex;align-items:flex-start;gap:.3em;border-radius:7px}',
            '#reader-drawer .mark:hover{background:rgba(127,127,127,.14)}',
            '#reader-drawer .mark a{flex:1 1 auto;padding:.42em .5em;text-decoration:none;color:inherit !important;',
            'font-size:.84rem;line-height:1.45}',
            '#reader-drawer .mark a span{display:block;opacity:.55;font-size:.74rem}',
            '#reader-drawer .mark button{flex:0 0 auto;font:inherit;font-size:.9rem;background:none;border:0;',
            'color:inherit;opacity:.5;padding:.4em .6em;cursor:pointer}',
            '#reader-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:1.1rem;z-index:10002;display:none;',
            'padding:.55em 1.1em;border-radius:999px;font-size:.85rem;background:rgba(30,30,40,.92);color:#fff;',
            'box-shadow:0 4px 18px rgba(0,0,0,.28)}',
            '#reader-toast.on{display:block}',
            // 本文ページの題。各ページの <style> が clamp(2rem,6vw,3.5rem)・太さ900 で
            // 出していて、30字を超える節の名前には大きすぎる。読み物のページだけ抑える
            // （書籍の目次ページは今までどおり大きく出す）
            'body.reader-on h1{font-size:clamp(1.35rem,2.4vw,1.95rem) !important;line-height:1.4 !important;',
            'letter-spacing:.02em !important;margin-bottom:1rem !important;text-shadow:none !important}',
            // 題の後ろに付いている書名は、小さく下の行へ回す
            'body.reader-on h1 .reader-book{display:block;font-size:.58em;font-weight:600;opacity:.72;margin-top:.3em}',
            'body.reader-on h1 .reader-book .sep{display:none}',
            '@media print{#reader-ui,#reader-drawer,#reader-resume,#reader-toast{display:none !important}}'
        ].join('');
        document.head.appendChild(s);
    }

    function build() {
        ui = document.createElement('div');
        ui.id = 'reader-ui';
        ui.innerHTML = '<div id="reader-progress"></div><div id="reader-crumb" role="button" tabindex="0"></div>';
        document.body.appendChild(ui);
        bar = ui.querySelector('#reader-progress');
        crumb = ui.querySelector('#reader-crumb');

        drawer = document.createElement('div');
        drawer.id = 'reader-drawer';
        drawer.innerHTML = '<div class="veil"></div><div class="panel"><div class="tools"></div>'
            + '<div class="marks"></div>'
            + '<h4>このページの見出し</h4><div class="list"></div><div class="side"></div></div>';
        document.body.appendChild(drawer);

        crumb.addEventListener('click', openDrawer);
        crumb.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openDrawer(); }
        });
        drawer.querySelector('.veil').addEventListener('click', closeDrawer);

        fillDrawer();
    }

    // ページの題が「節の名前／書名」になっているとき、書名を小さい行へ回す。
    // 字は1文字も変えず、後ろ半分を <span> で包むだけ
    function splitTitle() {
        var h = document.querySelector('h1');
        if (!h || h.closest(NOT_BODY) || h.childNodes.length !== 1) return;
        var node = h.firstChild;
        if (!node || node.nodeType !== 3) return;
        var m = node.nodeValue.match(/^([\s\S]*\S)([\s　]*[\/／][\s　]*)(\S[\s\S]*)$/);
        if (!m || m[1].length < 4 || m[3].length < 4) return;
        var span = document.createElement('span');
        span.className = 'reader-book';
        // 区切りの「／」は行が分かれるので見せない。ただし字は残す
        // （h1 の textContent は今までどおり「節の名前／書名」のまま）
        var sep = document.createElement('i');
        sep.className = 'sep';
        sep.textContent = m[2];
        span.appendChild(sep);
        span.appendChild(document.createTextNode(m[3]));
        node.nodeValue = m[1];
        h.appendChild(span);
    }

    // そのページの「目次」ボタンが指している所。本によっては本の目次が
    // 篇ごとに分かれているので、index.html と決め打ちしない
    function tocHref() {
        var nav = document.querySelector('.page-nav');
        var hit = 'index.html';
        if (nav) {
            Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
                if ((a.textContent || '').replace(/[\s　]/g, '') === '目次') {
                    hit = a.getAttribute('href') || hit;
                }
            });
        }
        return hit;
    }

    function bookSlug() {
        var seg = location.pathname.split('/').filter(Boolean);
        return seg.length >= 2 ? seg[seg.length - 2] : '';
    }

    function fillDrawer() {
        var list = drawer.querySelector('.list');
        items = heads.map(function (h, i) {
            if (h.isTitle) return null;            // 題そのものの見出しは並べない
            var a = document.createElement('a');
            a.className = 'item d' + h.depth;
            a.href = '#';
            a.textContent = h.text;
            a.addEventListener('click', function (e) {
                e.preventDefault();
                closeDrawer();
                h.el.scrollIntoView({ block: 'start' });
                window.scrollBy(0, -TOP + 20);
            });
            list.appendChild(a);
            return a;
        });
        if (!heads.length) {
            drawer.querySelector('h4').style.display = 'none';
        }

        // 道具（この本の目次・この書籍の中で検索）
        var tools = drawer.querySelector('.tools');
        var pin = document.createElement('a');
        pin.href = '#';
        pin.className = 'pin';
        pin.textContent = '🔖 ここにしおり';
        pin.addEventListener('click', function (e) { e.preventDefault(); closeDrawer(); addMark(); });
        tools.appendChild(pin);
        var src = tocHref();
        var toc = document.createElement('a');
        toc.href = src;
        toc.textContent = 'この本の目次';
        tools.appendChild(toc);
        var slug = bookSlug();
        if (slug) {
            // 目次が篇ごとに分かれている本では、検索もその篇の中だけにして、
            // 戻り先もその篇の目次にする。篇の名前は題（「…／第一篇　神様／…」）から
            var part = (document.title || '').match(/第[〇一二三四五六七八九十]+篇/);
            var q = document.createElement('a');
            q.href = '../search-all.html?book=' + encodeURIComponent(slug)
                + (part && src !== 'index.html'
                    ? '&part=' + encodeURIComponent(part[0]) + '&back=' + encodeURIComponent(src)
                    : '');
            q.textContent = 'この書籍の中で検索';
            tools.appendChild(q);
        }

        // 前後のページ（既にある page-nav から拾う）
        var side = drawer.querySelector('.side');
        var nav = document.querySelector('.page-nav');
        if (nav) {
            Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
                var label = (a.textContent || '').replace(/[←→\s]/g, '');
                if (label !== '前へ' && label !== '次へ') return;
                var link = document.createElement('a');
                link.href = a.getAttribute('href');
                link.innerHTML = '<span>' + label + '</span><br>' + a.getAttribute('href');
                link.dataset.role = label;
                side.appendChild(link);
            });
            titles(side);
        }
    }

    // 前後のページの見出しは、本の目次ページを1回だけ読んで拾う（本ごとに覚える）。
    // 節の名前だけだと「第三節」がどの篇のどの章の話か分からないので、目次の中で
    // その行より上にある浅い段（篇・章）を親として一緒に出す。
    function titles(side) {
        var links = side.querySelectorAll('a[data-role]');
        if (!links.length) return;
        var src = tocHref();
        var key = 'reader.titles.' + bookSlug() + '.' + src;

        var apply = function (map) {
            Array.prototype.forEach.call(links, function (a) {
                var file = (a.getAttribute('href') || '').split('/').pop().split('#')[0];
                var it = map[file];
                if (!it) return;
                a.innerHTML = '<span>' + a.dataset.role + '</span>'
                    + (it.up ? '<em>' + esc(it.up) + '</em>' : '')
                    + '<b>' + esc(it.name) + '</b>';
                var real = document.querySelector('.page-nav a[href="' + a.getAttribute('href') + '"]');
                if (real) real.title = (it.up ? it.up + ' / ' : '') + it.name;
            });
        };

        try {
            var cached = sessionStorage.getItem(key);
            if (cached) { apply(JSON.parse(cached)); return; }
        } catch (e) { }

        fetch(src).then(function (r) { return r.ok ? r.text() : null; }).then(function (html) {
            if (!html) return;
            var doc = new DOMParser().parseFromString(html, 'text/html');
            var map = {};
            var stack = [];
            var clean = function (el) {
                var c = el.cloneNode(true);
                Array.prototype.forEach.call(c.querySelectorAll('rt,rp'), function (r) { r.remove(); });
                return (c.textContent || '').replace(/\s+/g, ' ').trim();
            };
            Array.prototype.forEach.call(doc.querySelectorAll('li'), function (li) {
                var m = (li.className || '').match(/lv(\d)/);
                var lv = m ? +m[1] : 9;
                var text = clean(li);
                if (!text) return;
                var a = li.querySelector('a[href]');
                if (!a) {                       // 見出しの行（篇・章）。親として覚える
                    stack = stack.filter(function (s) { return s.lv < lv; });
                    stack.push({ lv: lv, text: text });
                    return;
                }
                var f = (a.getAttribute('href') || '').split('/').pop().split('#')[0];
                if (!/\.html?$/i.test(f) || map[f]) return;
                var up = stack.filter(function (s) { return s.lv < lv; })
                    .map(function (s) { return s.text; }).join(' ／ ');
                map[f] = { up: up.slice(0, 80), name: text.slice(0, 60) };
            });
            try { sessionStorage.setItem(key, JSON.stringify(map)); } catch (e) { }
            apply(map);
        }).catch(function () { });
    }

    function openDrawer() { drawerMarks(); drawer.classList.add('on'); markHere(); }
    function closeDrawer() { drawer.classList.remove('on'); }

    var hereAt = -2;
    function markHere() {
        var i = currentHead();
        if (i !== hereAt) {
            hereAt = i;
            items.forEach(function (a, k) { if (a) a.classList.toggle('here', k === i); });
        }
        if (i >= 0 && drawer.classList.contains('on') && items[i]) {
            items[i].scrollIntoView({ block: 'nearest' });
        }
    }

    // ---- 更新 --------------------------------------------------------------
    var ticking = false;
    var settleT = null;
    function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
            ticking = false;
            var h = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.width = (h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0) + '%';
            var i = currentHead();
            if (window.scrollY < 180 || i < 0) {
                crumb.classList.remove('on');
            } else {
                crumb.classList.add('on');
                // ページの題は落とし、深い方から3段だけ出す。前を切ったときは … を付ける
                var path = pathTo(i).filter(function (h) { return !h.isTitle; });
                var cut = path.length > 3;
                if (cut) path = path.slice(-3);
                var html = (cut ? '<span class="sep">…</span>' : '') + path.map(function (h, k) {
                    return (k === path.length - 1 ? '<span class="tail">' : '<span>') + esc(h.text) + '</span>';
                }).join('<span class="sep">/</span>') + '<span class="menu" aria-hidden="true">☰</span>';
                if (crumb.innerHTML !== html) crumb.innerHTML = html;
            }
            markHere();
        });
        // 字を当てて探すのは重いので、スクロールの途中ではやらない（iPhone SE で引っかかる）
        clearTimeout(settleT);
        settleT = setTimeout(function () {
            if (!restoring) cur = topPos();
            save();
        }, 160);
    }

    function esc(s) {
        return s.replace(/[&<>"]/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
        });
    }

    // ---- 拡大縮小・画面の作り直しでも同じ所に戻す --------------------------
    // iPhone の Safari は、スクロールの向きを変えるたびにツールバーが出入りして
    // 高さだけが変わり resize が来る。そこで scrollBy すると慣性スクロールが止まる
    // （dp で「いきなり止まる」と言われた）。字の折り返しが変わるのは幅が変わったときだけ
    var resizeT = null;
    var lastW = window.innerWidth;
    function onResize() {
        if (window.innerWidth === lastW) return;
        lastW = window.innerWidth;
        var keep = cur;
        clearTimeout(resizeT);
        resizeT = setTimeout(function () {
            collect();                       // 文字数は変わらないが、ノードは取り直す
            scrollToPos(keep, TOP);
        }, 60);
    }

    // ---- しおり ------------------------------------------------------------
    var saveT = null;
    function save() {
        clearTimeout(saveT);
        saveT = setTimeout(function () {
            try {
                if (cur > total * 0.02) {
                    localStorage.setItem(STORE + location.pathname, String(cur));
                    remember();
                } else {
                    localStorage.removeItem(STORE + location.pathname);
                }
            } catch (e) { }
        }, 700);
    }

    // サイトを開き直すとトップか本の目次に戻るので、ページの中のしおりだけでは
    // 「どの章まで読んだか」が分からない。本ごとに最後のページを覚えておき、
    // 入口（トップ・本の目次）に「続きから読む」を出す
    function dirOf(p) { return p.replace(/[^\/]*$/, ''); }

    function readRecent() {
        try {
            var list = JSON.parse(localStorage.getItem(RECENT) || '[]');
            return Array.isArray(list) ? list : [];
        } catch (e) { return []; }
    }

    // いまの場所を、入口の一覧に出せる形で（本・ページの題・節・%）
    function place() {
        var t = (document.title || '').split('/');
        var book = t.length > 1 ? t[t.length - 1].trim() : '';
        var name = (t.length > 1 ? t.slice(0, -1).join('/') : t[0]).trim();
        var path = pathTo(currentHead()).filter(function (h) { return !h.isTitle; });
        var sec = path.length ? path[path.length - 1].text : '';
        if (sec.replace(/[\s　]/g, '') === name.replace(/[\s　]/g, '')) sec = '';
        return {
            p: location.pathname, d: dirOf(location.pathname), b: book, n: name, s: sec,
            pct: Math.min(100, Math.round((cur / total) * 100)), t: Date.now()
        };
    }

    function remember() {
        var it = place();
        var list = readRecent().filter(function (x) { return x && x.d !== it.d; });
        list.unshift(it);
        localStorage.setItem(RECENT, JSON.stringify(list.slice(0, 10)));
    }

    // ---- 手で挟むしおり ----------------------------------------------------
    function readMarks() {
        try {
            var list = JSON.parse(localStorage.getItem(MARKS) || '[]');
            return Array.isArray(list) ? list.filter(function (m) { return m && m.id && m.p; }) : [];
        } catch (e) { return []; }
    }

    function writeMarks(list) {
        try { localStorage.setItem(MARKS, JSON.stringify(list.slice(0, 100))); } catch (e) { }
    }

    // 挟んだ所の本文の頭。一覧で「どこだったか」を見分ける手がかり
    function snippet(pos) {
        if (!nodes.length) return '';
        var out = '', i = nodeIndex(pos), off = pos - starts[i];
        // 画面の上の字は行の途中のことが多いので、近くの文の頭（。の次）まで戻る
        var before = nodes[i].nodeValue.slice(Math.max(0, off - 80), off);
        var cut = before.lastIndexOf('。');
        off = cut >= 0 ? off - before.length + cut + 1 : (off <= 80 ? 0 : off);
        while (i < nodes.length && out.length < 40) {
            out += nodes[i].nodeValue.slice(Math.max(0, off));
            off = 0; i++;
        }
        out = out.replace(/\s+/g, ' ').trim();
        return out.length > 24 ? out.slice(0, 24) + '…' : out;
    }

    function toast(msg) {
        var el = document.getElementById('reader-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'reader-toast';
            el.setAttribute('role', 'status');
            document.body.appendChild(el);
        }
        el.textContent = msg;
        el.classList.add('on');
        clearTimeout(el._t);
        el._t = setTimeout(function () { el.classList.remove('on'); }, 2200);
    }

    function addMark() {
        var it = place();
        it.id = Date.now().toString(36);
        it.pos = cur;
        it.x = snippet(cur);
        // 同じページのすぐ近く（300字以内）にあるしおりは、挟み直しとみなして置き換える
        var list = readMarks().filter(function (m) {
            return !(m.p === it.p && Math.abs(m.pos - it.pos) < 300);
        });
        list.unshift(it);
        writeMarks(list);
        var r = document.getElementById('reader-resume');
        if (r) r.classList.remove('on');
        toast('🔖 しおりを挟みました（' + it.pct + '%）');
    }

    function removeMark(id) {
        writeMarks(readMarks().filter(function (m) { return m.id !== id; }));
    }

    // 目次の引き出しの中の「このページのしおり」
    function drawerMarks() {
        var box = drawer.querySelector('.marks');
        box.innerHTML = '';
        var list = readMarks().filter(function (m) { return m.p === location.pathname; })
            .sort(function (a, b) { return a.pos - b.pos; });
        if (!list.length) return;
        var h = document.createElement('h4');
        h.textContent = 'このページのしおり';
        box.appendChild(h);
        list.forEach(function (m) {
            var row = document.createElement('div');
            row.className = 'mark';
            row.innerHTML = '<a href="#"><span>' + m.pct + '%' + (m.s ? '・' + esc(m.s) : '') + '</span>'
                + esc(m.x || '') + '</a><button type="button" aria-label="しおりを外す">×</button>';
            row.querySelector('a').addEventListener('click', function (e) {
                e.preventDefault();
                closeDrawer();
                scrollToPos(m.pos, TOP);
            });
            row.querySelector('button').addEventListener('click', function () {
                removeMark(m.id);
                drawerMarks();
            });
            box.appendChild(row);
        });
    }

    function ago(t) {
        var m = Math.round((Date.now() - t) / 60000);
        if (!(m >= 0)) return '';
        if (m < 60) return m < 2 ? 'さっき' : m + '分前';
        var h = Math.round(m / 60);
        if (h < 24) return h + '時間前';
        var d = Math.round(h / 24);
        return d < 31 ? d + '日前' : new Date(t).toLocaleDateString('ja-JP');
    }

    function card(it, label) {
        var a = document.createElement('a');
        a.className = 'reader-continue';
        a.href = it.p + '#resume';
        a.innerHTML = (label ? '<span class="k">' + label + '</span>' : '')
            + (it.b ? '<b>' + esc(it.b) + '</b>' : '')
            + '<em>' + esc(it.n) + (it.s ? ' ／ ' + esc(it.s) : '') + '</em>'
            + '<span class="meta">' + it.pct + '%まで・' + ago(it.t) + '</span>'
            + '<i class="bar" style="width:' + it.pct + '%"></i>';
        return a;
    }

    function entranceCss() {
        var s = document.createElement('style');
        s.id = 'reader-entrance-style';
        s.textContent = [
            '.reader-recent{max-width:640px;margin:1.2rem auto 1.8rem;display:flex;flex-direction:column;gap:.6rem}',
            '.reader-continue{display:block;position:relative;overflow:hidden;padding:.8em 1.1em 1em;border-radius:14px;',
            'text-decoration:none !important;text-align:left;font-size:1rem;line-height:1.5;',
            'background:rgba(255,255,255,.94);color:#222 !important;box-shadow:0 4px 18px rgba(0,0,0,.18)}',
            '.reader-continue:hover{transform:translateY(-1px)}',
            '.reader-continue .k{display:block;font-size:.75rem;font-weight:700;color:#6366f1 !important;letter-spacing:.05em}',
            // サイト側のリンク色（明るい表示では青）に負けないよう、中の字はカードの色にそろえる
            '.reader-recent a.reader-continue,.reader-recent a.reader-continue b,.reader-recent a.reader-continue em,'
            + '.reader-recent a.reader-continue .meta{color:#222 !important}',
            'body.dark-mode .reader-recent a.reader-continue,body.dark-mode .reader-recent a.reader-continue b,'
            + 'body.dark-mode .reader-recent a.reader-continue em,body.dark-mode .reader-recent a.reader-continue .meta{color:#e6e6f0 !important}',
            '.reader-continue b{display:block;font-size:1.02rem}',
            '.reader-continue em{display:block;font-style:normal;font-size:.88rem;opacity:.8}',
            '.reader-continue .meta{display:block;font-size:.74rem;opacity:.55;margin-top:.15em}',
            '.reader-continue .bar{position:absolute;left:0;bottom:0;height:3px;background:linear-gradient(90deg,#6366f1,#ec4899)}',
            '.reader-recent.in-book{margin-left:0}',
            '.reader-recent .reader-continue+.reader-continue{font-size:.9rem;padding:.6em 1.1em .8em}',
            'body.dark-mode .reader-continue{background:rgba(26,26,46,.92);color:#e6e6f0 !important;',
            'border:1px solid rgba(255,255,255,.14)}',
            'body.dark-mode .reader-continue .k{color:#a5b4fc !important}',
            // 本の目次では、読みかけの行に印を付ける
            // 行末に札を付けると、狭い画面では札だけ次の行に落ちる（iPhone SE で崩れた）。
            // 行全体を薄い箱で囲み、札は箱の中の上に置く。箱は影で広げるので字の位置は動かない
            'li.reader-here{background:rgba(99,102,241,.14);border-radius:6px;',
            'box-shadow:0 0 0 .45em rgba(99,102,241,.14);margin-top:1em !important;margin-bottom:.9em !important}',
            'li.reader-here::before{content:"読みかけ" !important;display:block;width:max-content;margin:0 0 .2em;',
            'padding:.05em .6em;border-radius:999px;font-size:.68rem;font-weight:700;line-height:1.6;',
            'background:#6366f1;color:#fff}',
            '.reader-marks{padding:.7em .5em .5em;border-radius:14px;text-align:left;line-height:1.5;',
            'background:rgba(255,255,255,.94);box-shadow:0 4px 18px rgba(0,0,0,.18)}',
            '.reader-marks .row{display:flex;align-items:flex-start;border-radius:9px}',
            '.reader-marks .row:hover{background:rgba(127,127,127,.12)}',
            '.reader-marks .row a{flex:1 1 auto;display:block;padding:.45em .6em;text-decoration:none !important;font-size:.9rem}',
            '.reader-marks .row b{display:block;font-size:.95rem}',
            '.reader-marks .row em{display:block;font-style:normal;font-size:.84rem;opacity:.8}',
            '.reader-marks .row .x{display:block;font-size:.8rem;opacity:.7}',
            '.reader-marks .meta{display:block;font-size:.72rem;opacity:.55}',
            '.reader-marks .more{padding:.2em .6em .3em}',
            '.reader-marks .row button{flex:0 0 auto;font:inherit;font-size:1rem;background:none;border:0;',
            'opacity:.45;padding:.45em .7em;cursor:pointer}',
            '.reader-marks .row button:hover{opacity:.9}',
            // サイト側のリンク色に負けないよう、字の色はここで決める
            '.reader-marks,.reader-marks .row a,.reader-marks .row a *,.reader-marks .row button{color:#222 !important}',
            '.reader-marks .k{display:block;padding:0 .6em .2em;font-size:.75rem;font-weight:700;color:#6366f1 !important}',
            'body.dark-mode .reader-marks{background:rgba(26,26,46,.92);border:1px solid rgba(255,255,255,.14)}',
            'body.dark-mode .reader-marks,body.dark-mode .reader-marks .row a,',
            'body.dark-mode .reader-marks .row a *,body.dark-mode .reader-marks .row button{color:#e6e6f0 !important}',
            'body.dark-mode .reader-marks .k{color:#a5b4fc !important}',
            '@media print{.reader-recent{display:none !important}}'
        ].join('');
        document.head.appendChild(s);
    }

    // 入口に出す「しおり」の一覧。トップでは本の名前も出す
    function markList(marks, withBook) {
        var wrap = document.createElement('div');
        wrap.className = 'reader-marks';
        wrap.innerHTML = '<span class="k">🔖 しおり</span>';
        var shown = marks.slice(0, 8);
        shown.forEach(function (m) {
            var row = document.createElement('div');
            row.className = 'row';
            row.innerHTML = '<a href="' + esc(m.p) + '#mark-' + esc(m.id) + '">'
                + (withBook && m.b ? '<b>' + esc(m.b) + '</b>' : '')
                + '<em>' + esc(m.n) + (m.s ? ' ／ ' + esc(m.s) : '') + '</em>'
                + (m.x ? '<span class="x">' + esc(m.x) + '</span>' : '')
                + '<span class="meta">' + m.pct + '%・' + ago(m.t) + '</span></a>'
                + '<button type="button" aria-label="しおりを外す">×</button>';
            row.querySelector('button').addEventListener('click', function () {
                removeMark(m.id);
                row.remove();
                if (!wrap.querySelector('.row')) wrap.remove();
            });
            wrap.appendChild(row);
        });
        if (marks.length > shown.length) {
            var more = document.createElement('span');
            more.className = 'meta more';
            more.textContent = 'ほか ' + (marks.length - shown.length) + ' 件（本の目次ごとに見られます）';
            wrap.appendChild(more);
        }
        return wrap;
    }

    function entrance() {
        var here = location.pathname;
        var isTop = here === ROOT || here === ROOT + 'index.html';
        var isToc = /(?:^|\/)(index|mokuji)\.html$/i.test(here) || /\/$/.test(here);
        if (!isTop && !isToc) return;
        var list = readRecent().filter(function (x) { return x && x.p && x.d; });
        var marks = readMarks();
        if (!isTop) {
            list = list.filter(function (x) { return x.d === dirOf(here); });
            marks = marks.filter(function (m) { return m.d === dirOf(here); });
        }
        if (!list.length && !marks.length) return;
        entranceCss();

        var box = document.createElement('div');
        box.className = 'reader-recent';
        list.slice(0, isTop ? 3 : 1).forEach(function (it, i) {
            box.appendChild(card(it, i === 0 ? '続きから読む' : ''));
        });
        if (marks.length) box.appendChild(markList(marks, isTop));

        if (isTop) {
            var head = document.querySelector('.container > header') || document.querySelector('header');
            if (head) head.parentNode.insertBefore(box, head.nextSibling);
            else document.body.insertBefore(box, document.body.firstChild);
            return;
        }

        box.classList.add('in-book');
        var h1 = document.querySelector('h1');
        var after = (h1 && h1.nextElementSibling && h1.nextElementSibling.classList.contains('book-search'))
            ? h1.nextElementSibling : h1;
        if (after) after.parentNode.insertBefore(box, after.nextSibling);
        else document.body.insertBefore(box, document.body.firstChild);

        if (!list.length) return;
        // 目次の中の、読みかけの行に印。同じページへのリンクが節の数だけあるので、
        // 覚えた節の名前と同じ行を選び、無ければそのページの最初の行
        var it = list[0];
        var file = it.p.split('/').pop();
        var rows = Array.prototype.filter.call(document.querySelectorAll('li > a[href]'), function (a) {
            return (a.getAttribute('href') || '').split('#')[0].split('/').pop() === file;
        });
        if (!rows.length) return;
        var flat = function (s) { return (s || '').replace(/[\s　◆▸▶･・]/g, ''); };  // clean() と同じ字を落として比べる
        var hit = null;
        if (it.s) {
            rows.forEach(function (a) { if (!hit && flat(a.textContent) === flat(it.s)) hit = a; });
        }
        (hit || rows[0]).parentNode.classList.add('reader-here');
    }

    // 「続きから読む」から来たときは、確かめずにそのまま読んでいた所へ移る。
    // 字の表示（Web フォント）が後から入って行がずれるので、触られるまでは入れ直す
    // 手で挟んだしおり（#mark-<id>）から来たときも同じ
    function resumeNow(pos) {
        try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { }
        if (!(pos > 0)) return;
        var touched = false;
        var mark = function () { touched = true; };
        ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach(function (ev) {
            window.addEventListener(ev, mark, { once: true, passive: true });
        });
        var go = function () {
            if (touched) return;
            collect();
            scrollToPos(pos, TOP);
            cur = pos;
        };
        go();
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
        window.addEventListener('load', go);
    }

    function offerResume() {
        if (location.hash === '#resume') {
            var last = null;
            try { last = localStorage.getItem(STORE + location.pathname); } catch (e) { }
            resumeNow(last && +last > total * 0.02 ? +last : 0);
            return;
        }
        var mk = location.hash.match(/^#mark-([0-9a-z]+)$/);
        if (mk) {
            var hit = readMarks().filter(function (m) { return m.id === mk[1] && m.p === location.pathname; })[0];
            resumeNow(hit ? hit.pos : 0);
            return;
        }
        if (location.hash) return;
        var saved = null;
        try { saved = localStorage.getItem(STORE + location.pathname); } catch (e) { }
        if (!saved) return;
        var pos = +saved;
        if (!(pos > total * 0.02)) return;
        var pct = Math.round((pos / total) * 100);
        var box = document.createElement('div');
        box.id = 'reader-resume';
        box.innerHTML = '<span>前回の続き（' + pct + '%）</span>'
            + '<button type="button" class="go">そこへ</button>'
            + '<button type="button" class="x" aria-label="閉じる">×</button>';
        document.body.appendChild(box);
        box.classList.add('on');
        var hide = function () { box.classList.remove('on'); };
        box.querySelector('.go').addEventListener('click', function () { scrollToPos(pos, TOP); hide(); });
        box.querySelector('.x').addEventListener('click', hide);
        setTimeout(hide, 12000);
    }

    // ---- キーボード --------------------------------------------------------
    function navTo(which) {
        var nav = document.querySelector('.page-nav');
        if (!nav) return;
        var hit = null;
        Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
            var t = (a.textContent || '').replace(/[←→\s]/g, '');
            if (t === which) hit = a;
        });
        if (hit) location.href = hit.getAttribute('href');
    }

    function jumpHead(step) {
        if (!heads.length) return;
        var i = currentHead();
        var n = Math.max(0, Math.min(heads.length - 1, i + step));
        if (step > 0 && i < 0) n = 0;
        heads[n].el.scrollIntoView({ block: 'start' });
        window.scrollBy(0, -TOP + 20);
    }

    function onKey(e) {
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        var t = e.target;
        if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
        if (e.key === 'Escape') { closeDrawer(); return; }
        if (e.key === 'ArrowLeft') { navTo('前へ'); return; }
        if (e.key === 'ArrowRight') { navTo('次へ'); return; }
        if (e.key === 'j') { jumpHead(1); e.preventDefault(); return; }
        if (e.key === 'k') { jumpHead(-1); e.preventDefault(); return; }
        if (e.key === 'b') { addMark(); e.preventDefault(); return; }
        if (e.key === 't') { drawer.classList.contains('on') ? closeDrawer() : openDrawer(); e.preventDefault(); }
    }

    // ---- 始める ------------------------------------------------------------
    function start() {
        if (SKIP.test(location.pathname) || /\/$/.test(location.pathname)) { entrance(); return; }
        collect();
        if (total < MIN_CHARS) return;
        collectHeads();
        // dp の古い現在位置バーは、こちらと二重になるので引っ込める
        var old = document.getElementById('stacked-header-container');
        if (old) old.style.display = 'none';
        document.body.classList.add('reader-on');
        css();
        splitTitle();
        build();
        onScroll();
        offerResume();
        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', onResize);
        window.addEventListener('keydown', onKey);
        window.addEventListener('pagehide', function () { clearTimeout(saveT); save(); });
        document.addEventListener('visibilitychange', function () { if (document.hidden) save(); });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();

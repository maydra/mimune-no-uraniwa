/* theme/reader.js — 長い本文ページの読書支援
 *
 * 1ページが2万〜5万字ある本が52冊あり、見出しも1ページに40個入る。
 * そこで「いま本のどこを読んでいるか」を常に出し、迷子にならないようにする。
 *
 *   ・上端の進捗バー
 *   ・現在位置バー（見出しの道筋。押すと目次が開く）
 *   ・目次の引き出し（見出し一覧＋いま読んでいる所を光らせる）
 *   ・しおり（前回の続きへ）
 *   ・拡大縮小しても読んでいた場所を保つ
 *   ・キーボード（← → で前後のページ、j k で見出し送り、t で目次）
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
        var pageTitle = (document.title || '').replace(/[\s　]/g, '');
        var all = document.querySelectorAll('h1,h2,h3,h4,h5,h6');
        Array.prototype.forEach.call(all, function (h) {
            if (h.closest(NOT_BODY) || h.classList.contains('page-title')) return;
            var t = clean(h);
            if (!t) return;
            // ページの先頭にある「題そのもの」の見出しは道筋にも目次にも要らない。
            // 多くの本は <h1> が <title> の写し、その下に書名だけの <h2> が続く
            var flat = t.replace(/[\s　]/g, '');
            var isTitle = heads.length < 3 && pageTitle && flat.length > 3 &&
                (pageTitle.indexOf(flat) >= 0 || flat.indexOf(pageTitle) >= 0);
            heads.push({ el: h, level: +h.tagName.substring(1), text: t, isTitle: !!isTitle });
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
            'box-shadow:0 2px 10px rgba(0,0,0,.10);cursor:pointer;backdrop-filter:blur(8px);',
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
            '#reader-drawer a.item{display:block;padding:.42em .5em;border-radius:7px;text-decoration:none;',
            'color:inherit !important;font-size:.88rem;line-height:1.45}',
            '#reader-drawer a.item:hover{background:rgba(127,127,127,.14)}',
            '#reader-drawer a.item.here{background:rgba(99,102,241,.16);font-weight:700}',
            '#reader-drawer .lv2{padding-left:.9em}#reader-drawer .lv3{padding-left:2em}',
            '#reader-drawer .lv4{padding-left:3.1em}#reader-drawer .lv5,#reader-drawer .lv6{padding-left:4.2em}',
            '#reader-drawer .tools{margin:.2rem 0 1rem;display:flex;flex-wrap:wrap;gap:.4rem}',
            '#reader-drawer .tools a{flex:1 1 auto;text-align:center;padding:.5em .7em;border-radius:8px;',
            'font-size:.82rem;text-decoration:none;background:rgba(127,127,127,.14);color:inherit !important}',
            '#reader-drawer .side{margin-top:1.2rem;border-top:1px solid rgba(127,127,127,.25);padding-top:.7rem}',
            '#reader-drawer .side a{display:block;padding:.45em .5em;font-size:.82rem;text-decoration:none;color:inherit !important}',
            '#reader-drawer .side span{opacity:.6;font-size:.74rem}',
            '#reader-resume{pointer-events:auto;position:fixed;left:50%;transform:translateX(-50%);bottom:1.1rem;',
            'z-index:10001;display:none;align-items:center;gap:.6em;padding:.55em .8em .55em 1em;border-radius:999px;',
            'font-size:.83rem;background:rgba(30,30,40,.92);color:#fff;box-shadow:0 4px 18px rgba(0,0,0,.28)}',
            '#reader-resume.on{display:flex}',
            '#reader-resume button{font:inherit;color:#fff;background:rgba(255,255,255,.18);border:0;',
            'border-radius:999px;padding:.35em .9em;cursor:pointer}',
            '#reader-resume .x{background:none;padding:.2em .5em;opacity:.7}',
            '@media print{#reader-ui,#reader-drawer,#reader-resume{display:none !important}}'
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
            + '<h4>このページの見出し</h4><div class="list"></div><div class="side"></div></div>';
        document.body.appendChild(drawer);

        crumb.addEventListener('click', openDrawer);
        crumb.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openDrawer(); }
        });
        drawer.querySelector('.veil').addEventListener('click', closeDrawer);

        fillDrawer();
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
            a.className = 'item lv' + h.level;
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
        var toc = document.createElement('a');
        toc.href = 'index.html'; toc.textContent = 'この本の目次';
        tools.appendChild(toc);
        var slug = bookSlug();
        if (slug) {
            var q = document.createElement('a');
            q.href = '../search-all.html?book=' + encodeURIComponent(slug);
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

    // 前後のページの題は、本の目次ページを1回だけ読んで拾う（本ごとに覚える）
    function titles(side) {
        var links = side.querySelectorAll('a[data-role]');
        if (!links.length) return;
        var key = 'reader.titles.' + bookSlug();
        var apply = function (map) {
            Array.prototype.forEach.call(links, function (a) {
                var file = (a.getAttribute('href') || '').split('/').pop().split('#')[0];
                var name = map[file];
                if (!name) return;
                a.innerHTML = '<span>' + a.dataset.role + '</span><br>' + name;
                var real = document.querySelector('.page-nav a[href="' + a.getAttribute('href') + '"]');
                if (real) real.title = name;
            });
        };
        try {
            var cached = sessionStorage.getItem(key);
            if (cached) { apply(JSON.parse(cached)); return; }
        } catch (e) { }
        fetch('index.html').then(function (r) { return r.ok ? r.text() : null; }).then(function (html) {
            if (!html) return;
            var doc = new DOMParser().parseFromString(html, 'text/html');
            var map = {};
            Array.prototype.forEach.call(doc.querySelectorAll('a[href]'), function (a) {
                var f = a.getAttribute('href').split('/').pop().split('#')[0];
                if (!/\.html?$/i.test(f) || map[f]) return;
                var t = (a.textContent || '').replace(/\s+/g, ' ').trim();
                if (t) map[f] = t.slice(0, 60);
            });
            try { sessionStorage.setItem(key, JSON.stringify(map)); } catch (e) { }
            apply(map);
        }).catch(function () { });
    }

    function openDrawer() { drawer.classList.add('on'); markHere(); }
    function closeDrawer() { drawer.classList.remove('on'); }

    function markHere() {
        var i = currentHead();
        items.forEach(function (a, k) { if (a) a.classList.toggle('here', k === i); });
        if (i >= 0 && drawer.classList.contains('on') && items[i]) {
            items[i].scrollIntoView({ block: 'nearest' });
        }
    }

    // ---- 更新 --------------------------------------------------------------
    var ticking = false;
    function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
            ticking = false;
            if (!restoring) cur = topPos();
            if (total) bar.style.width = Math.min(100, (cur / total) * 100) + '%';
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
            save();
        });
    }

    function esc(s) {
        return s.replace(/[&<>"]/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
        });
    }

    // ---- 拡大縮小・画面の作り直しでも同じ所に戻す --------------------------
    var resizeT = null;
    function onResize() {
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
                if (cur > total * 0.02) localStorage.setItem(STORE + location.pathname, String(cur));
                else localStorage.removeItem(STORE + location.pathname);
            } catch (e) { }
        }, 700);
    }

    function offerResume() {
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
        if (e.key === 't') { drawer.classList.contains('on') ? closeDrawer() : openDrawer(); e.preventDefault(); }
    }

    // ---- 始める ------------------------------------------------------------
    function start() {
        if (SKIP.test(location.pathname)) return;
        collect();
        if (total < MIN_CHARS) return;
        collectHeads();
        // dp の古い現在位置バーは、こちらと二重になるので引っ込める
        var old = document.getElementById('stacked-header-container');
        if (old) old.style.display = 'none';
        css();
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

/**
 * 原理講論（dp/）のページに図を出す。図は『原理講論 要約訓読チャート（12時間用）』（世界平和統一堂）を
 * SVG に描き直したもの（作り方は _tools/dpcharts/README.md）。
 *
 * - ページの <script src="charts.js" data-charts="charts/11sozo.json?v=…"> で読む。JSON の中身は
 *   { fonts: {重さ: URL}, charts: [{ id, after, svg }] }。after は「この字の並びで終わる文のあとに出す」目印（空白を除いた本文の字）。
 *   図は、その図を映していたスライドの説明文が終わる文のあとに1枚ずつ入る（段落の途中にも入る）
 * - 「表示：」の並びの「図」で出す・隠すを切り替える（既定は隠す）。状態は localStorage の dp_charts
 * - 目次の引き出し（theme/reader.js）からも window.dpCharts で切り替える
 */
(function () {
    'use strict';

    var me = document.currentScript;
    var src = me && me.getAttribute('data-charts');
    if (!src || window.dpCharts) return;
    var DATA_URL = new URL(src, me.src).href;
    var KEY = 'dp_charts';
    var CREDIT = '図は『原理講論 要約訓読チャート（12時間用）』（世界平和統一堂）の図を描き直したものです。';
    var TOP = 96;   // 「画面の上」とみなす高さ（reader.js と同じ）

    var on = false;
    try { on = localStorage.getItem(KEY) === '1'; } catch (e) { }
    var loading = null;
    var placed = false;
    var buttons = [];
    var note = null;

    // ---- 本文の字 ------------------------------------------------------------
    // 図の目印は「空白を除いた本文の字」で探す。ルビの読み・目次・ボタンなどの字は数えない。
    // _tools/dpcharts/anchors.py の page_text() と同じ決まり
    var SKIP = 'rt,rp,script,style,nav,.toc-collapsible,#toc,.page-nav,#typo-report,#stacked-header-container,' +
        '.color-filter-container,.dpc-fig,.dpc-note,#reader-ui,#reader-drawer';

    function pageText() {
        var chars = [], nodes = [], offs = [];
        var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
            acceptNode: function (n) {
                var p = n.parentElement;
                return (!p || p.closest(SKIP)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
            }
        });
        var n;
        while ((n = w.nextNode())) {
            var v = n.nodeValue;
            for (var i = 0; i < v.length; i++) {
                if (/\s/.test(v.charAt(i))) continue;
                chars.push(v.charAt(i)); nodes.push(n); offs.push(i);
            }
        }
        return { text: chars.join(''), nodes: nodes, offs: offs };
    }

    // ---- 図を置く所 ----------------------------------------------------------
    var BLOCK = /^(DIV|P|H[1-6]|UL|OL|LI|TABLE|BLOCKQUOTE|HR|SECTION|ARTICLE|MAIN|BODY|FIGURE|DETAILS)$/;

    function blockOf(node) {
        var e = node.nodeType === 1 ? node : node.parentElement;
        while (e && !BLOCK.test(e.nodeName)) e = e.parentElement;
        return e || document.body;
    }

    // 文の終わり（node の off 字目の前）に図を置く所。
    // 文のあとに字が続くなら（段落の途中）、そこで字のノードを割って間に置く。
    // 段落の終わりなら、次の <br> のあと（<br> の前に置くと、図の下に空の行ができる）。
    // 見出しなどのブロックが先に来たら、その前。何も無ければ、文を含むブロックの終わり
    function placeAt(node, off) {
        if (off < node.nodeValue.length) node.splitText(off);
        var block = blockOf(node);
        var w = document.createTreeWalker(block, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
        w.currentNode = node;
        var n;
        while ((n = w.nextNode())) {
            if (n.nodeType === 3) {
                if (/\S/.test(n.nodeValue)) return splitAfter(node, block);   // 全角の空白（字下げ）は \s に入る
                continue;
            }
            if (n.nodeName === 'BR') return splitAfter(n, block);
            if (BLOCK.test(n.nodeName)) return { parent: n.parentNode, before: n };
        }
        return { parent: block, before: null };
    }

    // 置く所が蛍光ペンの span の中なら、span をそこで二つに割って、図を span の外に出す。
    // span の中に置くと、暗い配色の蛍光ペンの決まり（[style*="FCD2E7"] * の字の色）が図の字にもかかる。
    // 字のノードは動かすだけで作り直さない（割った字のノードだけは新しくなるので、reader.js に取り直してもらう）
    function splitAfter(br, block) {
        var node = br;
        while (node.parentNode && node.parentNode !== block) {
            var parent = node.parentNode;
            if (node.nextSibling) {
                var clone = parent.cloneNode(false);
                clone.removeAttribute('id');
                while (node.nextSibling) clone.appendChild(node.nextSibling);
                parent.parentNode.insertBefore(clone, parent.nextSibling);
            }
            node = parent;
        }
        return { parent: block, before: node.nextSibling };
    }

    function place(list) {
        var pt = pageText();
        var groups = [], byEnd = {};
        list.forEach(function (c) {
            var i = pt.text.indexOf(c.after);
            if (i < 0) { console.warn('[dpCharts] 目印が見つからない:', c.id, c.after); return; }
            var end = i + c.after.length - 1;      // 文の最後の字
            if (!byEnd[end]) { byEnd[end] = { end: end, charts: [] }; groups.push(byEnd[end]); }
            byEnd[end].charts.push(c);
        });
        // 後ろから置く。字のノードを割ると、割った所より後ろの字の位置（pt）が使えなくなるため
        groups.sort(function (a, b) { return b.end - a.end; });
        groups.forEach(function (g) {
            var spot = placeAt(pt.nodes[g.end], pt.offs[g.end] + 1);
            g.charts.forEach(function (c) {
                var f = document.createElement('figure');
                f.className = 'dpc-fig';
                f.setAttribute('data-id', c.id);
                // 105枚の SVG を一度に描くと、押してから出るまで約1秒かかった。先に図の大きさの枠だけを置き、
                // 画面に近づいた図から SVG を入れる（枠の縦横比は viewBox と同じなので、入れても高さは変わらない）
                var box = document.createElement('div');
                box.className = 'dpc-box';
                var vb = (c.svg.match(/viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"/) || []).slice(3).map(Number);
                if (vb.length === 2 && vb[0] && vb[1]) {
                    box.style.aspectRatio = vb[0] + ' / ' + vb[1];
                    // viewBox は描いてある物の範囲に詰めてあるので、そのまま幅いっぱいにすると、物の少ない図ほど
                    // 大きく出る。図の 1 単位を 0.55px にして、どの図も字の大きさをそろえる（34em と画面の幅が上限）。
                    // 後編の図は元の画像が小さいので、1 単位の大きさを JSON の u でもらう
                    f.style.maxWidth = 'min(34em, ' + Math.round(vb[0] * (c.u || 0.55) + 28) + 'px)';
                }
                f.appendChild(box);
                svgs.set(box, c.svg);
                spot.parent.insertBefore(f, spot.before);
                lazy().observe(box);
            });
        });
        placed = true;
        document.dispatchEvent(new CustomEvent('dpchartsplaced'));
    }

    // 画面の上下 1500px に入った枠へ SVG を入れる。隠しているあいだ（display:none）は入らない
    var svgs = new Map();
    var io = null;
    function lazy() {
        if (io) return io;
        if (!('IntersectionObserver' in window)) {
            io = { observe: fill };
            return io;
        }
        io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) { io.unobserve(e.target); fill(e.target); }
            });
        }, { rootMargin: '1500px 0px' });
        return io;
    }
    function fill(box) {
        var s = svgs.get(box);
        if (!s) return;
        box.innerHTML = s;
        svgs.delete(box);
    }

    // ---- 読んでいた所を動かさない --------------------------------------------
    function caretAt(x, y) {
        if (document.caretRangeFromPoint) return document.caretRangeFromPoint(x, y);
        if (document.caretPositionFromPoint) {
            var p = document.caretPositionFromPoint(x, y);
            if (!p) return null;
            var r = document.createRange();
            r.setStart(p.offsetNode, p.offset);
            return r;
        }
        return null;
    }

    function lineTop(node, off) {
        var r = document.createRange();
        var len = node.nodeValue.length;
        if (!len) return null;
        var o = Math.min(off, len - 1);
        r.setStart(node, o); r.setEnd(node, o + 1);
        var rs = r.getClientRects();
        return rs.length ? rs[0].top : null;
    }

    // 画面の上にある字を「本文の何字目か」（pageText の番号）で覚え、出し入れのあとその字の高さへ戻す。
    // 字のノードで覚えると、図を同じ字のノードの途中に差し込んだとき（ノードが二つに割れる）に、
    // 覚えた位置が割れた前半に残って戻し先がずれた（復活論で 38px）
    function charIndexAt(pt, node, off) {
        for (var i = 0; i < pt.nodes.length; i++) {
            if (pt.nodes[i] === node && pt.offs[i] >= off) return i;
        }
        // そのノードの残りが空白だけなら、次の字
        for (var j = pt.nodes.length - 1; j >= 0; j--) {
            if (pt.nodes[j] === node) return j + 1 < pt.nodes.length ? j + 1 : j;
        }
        return -1;
    }

    function keepPlace(fn) {
        var mark = null;
        if (window.scrollY > 0) {
            var xs = [0.5, 0.35, 0.65], ys = [TOP, TOP + 30, TOP + 70];
            var pt = null;
            for (var a = 0; a < ys.length && !mark; a++) {
                for (var b = 0; b < xs.length && !mark; b++) {
                    var r = caretAt(window.innerWidth * xs[b], ys[a]);
                    if (r && r.startContainer.nodeType === 3 && !r.startContainer.parentElement.closest(SKIP)) {
                        pt = pt || pageText();
                        var k = charIndexAt(pt, r.startContainer, r.startOffset);
                        var t = k >= 0 ? lineTop(pt.nodes[k], pt.offs[k]) : null;
                        if (t !== null) mark = { k: k, top: t };
                    }
                }
            }
        }
        fn();
        if (mark) {
            var pt2 = pageText();
            if (mark.k < pt2.nodes.length) {
                var now = lineTop(pt2.nodes[mark.k], pt2.offs[mark.k]);
                if (now !== null && Math.abs(now - mark.top) > 1) window.scrollBy(0, now - mark.top);
            }
        }
    }

    // ---- 出す・隠す ------------------------------------------------------------
    function load() {
        if (!loading) {
            loading = fetch(DATA_URL).then(function (r) {
                if (!r.ok) throw new Error(r.status);
                return r.json();
            });
        }
        return loading;
    }

    // 図の字のフォント。JSON の fonts（{"700": "fonts/dpc-gothic-700.woff2?v=…"}）を @font-face にする。
    // 「図」を出すまでは足さないので、図を出さない人はダウンロードしない。届くまでは端末のフォントで描く（swap）
    var fontsAdded = false;
    function useFonts(f) {
        if (fontsAdded || !f) return;
        fontsAdded = true;
        var css = Object.keys(f).map(function (w) {
            return "@font-face{font-family:'DPC Gothic';src:url('" + new URL(f[w], me.src).href +
                "') format('woff2');font-weight:" + w + ';font-display:swap}';
        }).join('\n');
        var s = document.createElement('style');
        s.id = 'dpc-fonts';
        s.textContent = css;
        document.head.appendChild(s);
    }

    function paint() {
        document.body.classList.toggle('dpc-on', on);
        buttons.forEach(function (b) {
            b.classList.toggle('active', on);
            b.setAttribute('aria-pressed', on ? 'true' : 'false');
            var s = b.querySelector('.toggle-status');
            if (s) s.textContent = on ? 'ON' : 'OFF';
        });
    }

    function set(v) {
        on = !!v;
        try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) { }
        document.dispatchEvent(new CustomEvent('dpcharts', { detail: { on: on } }));
        if (!on) {
            keepPlace(paint);
            return Promise.resolve();
        }
        return load().then(function (d) {
            if (!on) return;
            useFonts(d.fonts);
            keepPlace(function () {
                if (!placed) place(d.charts || []);
                paint();
            });
        }).catch(function (e) {
            console.warn('[dpCharts] 図を読めなかった:', e);
            on = false;
            paint();
        });
    }

    window.dpCharts = {
        isOn: function () { return on; },
        set: set,
        credit: CREDIT
    };

    // ---- ボタンと見た目 ------------------------------------------------------
    function injectStyles() {
        var css = [
            '.dpc-fig{display:none;clear:both;box-sizing:border-box;max-width:34em;margin:1em auto 1.4em;padding:12px 14px;',
            'background:#fff;border:1px solid rgba(0,0,0,.14);border-radius:10px;color:#111;line-height:1}',
            'body.dpc-on .dpc-fig{display:block}',
            // 端末のフォントが少し広くても字が切れないように（viewBox は描いてある物の範囲に詰めてある）
            '.dpc-box{width:100%}',
            '.dpc-box svg{display:block;width:100%;height:100%;overflow:visible}',
            // 図は BIZ UDPゴシックで寸法を合わせて描いた。入っていない端末（iPhone・Android・Mac）では、図の字だけに絞った
            // 同じフォント（DPC Gothic、dp/fonts）を使う。入っている Windows はダウンロードしない（useFonts）
            ".dpc-box svg{font-family:'BIZ UDPGothic','DPC Gothic','Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic',Meiryo,sans-serif}",
            'body.dark-mode .dpc-fig{background:#1f1d36;border-color:rgba(255,255,255,.16);color:#e6e6ef}',
            'body.dark-mode .dpc-fig .paper{fill:#2c2a48}',
            '.dpc-note{display:none;max-width:34em;margin:-.6rem auto 1.2rem;padding:0 .4rem;font-size:.8rem;opacity:.75;text-align:center}',
            'body.dpc-on .dpc-note{display:block}',
            '.dpc-btn .dpc-ico{width:12px;height:10px;flex-shrink:0;border:1.5px solid currentColor;border-radius:2px;box-sizing:border-box}',
            '@media (max-width:600px){.dpc-fig{padding:6px 4px;margin-left:-.4rem;margin-right:-.4rem}}'
        ].join('\n');
        var s = document.createElement('style');
        s.id = 'dpc-styles';
        s.textContent = css;
        document.head.appendChild(s);
    }

    function makeButton() {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'filter-btn dpc-btn';
        b.title = CREDIT;
        b.innerHTML = '<span class="dpc-ico" aria-hidden="true"></span><span class="color-label">図</span><span class="toggle-status"></span>';
        b.addEventListener('click', function () { set(!on); });
        buttons.push(b);
        return b;
    }

    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        injectStyles();
        // color_filter.js の「表示：」の並びに足す。無いページでは自分で並びを作る
        var box = document.querySelector('.color-filter-container');
        var row = box && box.querySelector('.filter-buttons');
        if (!row) {
            box = document.createElement('div');
            box.className = 'color-filter-container';
            box.innerHTML = '<span class="filter-label">表示：</span><div class="filter-buttons"></div>';
            row = box.querySelector('.filter-buttons');
            var nav = document.querySelector('.page-nav');
            if (nav) nav.parentNode.insertBefore(box, nav.nextSibling);
        }
        row.appendChild(makeButton());
        note = document.createElement('p');
        note.className = 'dpc-note';
        note.textContent = CREDIT;
        if (box.parentNode) box.parentNode.insertBefore(note, box.nextSibling);
        paint();
        if (on) set(true);
    }

    init();
})();

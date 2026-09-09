/* サイト内一括検索。

   打った文字列をそのまま探す（ブラウザの Ctrl+F と同じ）。そのために
   サイトの本文を data/fulltext/ から丸ごと持ってきて、ブラウザの中で探す。
   約15MB を1回落とすだけで、あとは Cache API に残るので通信は起きない。

   以前は pagefind（語に切った索引）を使っていたが、「み旨」のように索引の
   切り方と合わない言葉が取りこぼされ、抜粋を出すのにページごとの通信が
   必要だった。本文が手元にあれば、どちらもいらない。

   ?book=<フォルダ名> を付けると、その書籍の中だけを探す。本文は書籍ごとに
   分けてあるので、読み込むのもその1冊ぶんだけで済む（数百KB）。各書籍の
   目次にある「この書籍の中で検索」がここへ来る。

   本文の作り方は tools/build_fulltext.py。 */
(function () {
    const MANIFEST_URL = 'data/fulltext/manifest.json';
    const SHARD_DIR = 'data/fulltext/';
    const CACHE_NAME = 'mimune-fulltext-v1';

    // ?book=dp なら原理講論の中だけ。無ければサイト全体。
    let scopeBook = new URLSearchParams(location.search).get('book') || '';
    let scopeTitle = '';

    // 抜粋は当たった所の前後をこれだけ切り出す
    const EXCERPT_BEFORE = 110;
    const EXCERPT_AFTER = 220;

    // 聖書は 1,189 ページある。目当てでないのに結果を埋めるので、既定で外す。
    const BIBLE_PREFIX = 'Bible_out/';

    // 関連度（BM25）。同じ語が何度も出るほど強いが頭打ちにし、長いページは
    // 割り引き、どのページにもある語は弱く、見出しに入っていれば大きく足す。
    const K1 = 1.2;
    const B = 0.75;
    const TITLE_WEIGHT = 2.5;

    // --- 本文の読み込み ---------------------------------------------------
    // シャード1つ = { docs:[[URL, タイトル, 文字数], ...], body, starts }
    // body は各ページの本文を "\n" でつないだもの。本文に改行は無いので、
    // 探している文字列がページをまたいで当たることはない。
    const shards = [];
    let totalChars = 0;
    let totalPages = 0;
    let loadedBytes = 0;
    let totalBytes = 0;
    let loading = null;
    let ready = false;

    function openCache() {
        if (!('caches' in window)) return Promise.resolve(null);
        return caches.open(CACHE_NAME).catch(() => null);
    }

    async function fetchShard(cache, s) {
        const url = SHARD_DIR + s.file + '?v=' + s.hash;
        let res = null;
        if (cache) { try { res = await cache.match(url); } catch (e) { } }
        if (!res) {
            res = await fetch(url);
            if (!res.ok) throw new Error(s.file);
            if (cache) { try { await cache.put(url, res.clone()); } catch (e) { } }
        }
        const raw = await res.text();
        const nl = raw.indexOf('\n');
        const docs = JSON.parse(raw.slice(0, nl)).docs;
        const body = raw.slice(nl + 1);

        // ページごとの開始位置。当たった位置からページを引くのに使う。
        // 区切りは読み飛ばす。改行が CRLF に化けても位置がずれないように、
        // 文字数を足すのではなく、実際に改行を跨いで数える。
        const starts = new Int32Array(docs.length);
        let off = 0;
        for (let i = 0; i < docs.length; i++) {
            starts[i] = off;
            off += docs[i][2];
            while (off < body.length) {
                const c = body.charCodeAt(off);
                if (c !== 10 && c !== 13) break;
                off += 1;
            }
        }
        return { docs: docs, body: body, starts: starts, lower: null };
    }

    function loadCorpus(onProgress) {
        if (loading) return loading;
        loading = (async () => {
            const man = await (await fetch(MANIFEST_URL)).json();

            // 書籍を指定されていたら、その1冊ぶんのシャードだけを読む。
            // 知らない名前だったときはサイト全体に落とす。
            const book = (man.books || []).find(b => b.id === scopeBook);
            const wantedShards = book
                ? man.shards.filter(s => s.book === book.id)
                : man.shards;
            if (book) {
                scopeTitle = book.title || book.id;
                totalChars = book.chars;
                totalPages = book.pages;
            } else {
                totalChars = man.chars;
                totalPages = man.pages;
            }
            totalBytes = wantedShards.reduce((a, s) => a + s.bytes, 0);
            if (book) { showScope(); } else { scopeBook = ''; clearScope(); }

            const cache = await openCache();
            if (cache) {
                // 作り直しで消えたシャードを捨てる。1冊だけ読むときも、
                // 判断は manifest 全体で行う（他の書籍のぶんを消さない）。
                const wanted = new Set(man.shards.map(
                    s => SHARD_DIR + s.file + '?v=' + s.hash));
                try {
                    for (const req of await cache.keys()) {
                        const u = new URL(req.url);
                        const key = SHARD_DIR + u.pathname.split('/').pop() + u.search;
                        if (!wanted.has(key)) await cache.delete(req);
                    }
                } catch (e) { }
            }

            await Promise.all(wantedShards.map(async (s) => {
                const sh = await fetchShard(cache, s);
                shards.push(sh);
                loadedBytes += s.bytes;
                if (onProgress) onProgress();
            }));
            ready = true;
            if (onProgress) onProgress();
        })();
        return loading;
    }

    // --- 探す -------------------------------------------------------------
    function normalize(s) {
        return s.normalize ? s.normalize('NFKC') : s;
    }

    // 英字が入っているときだけ、大文字小文字を無視する（本文の小文字版を作る）
    function loweredBody(sh) {
        if (sh.lower === null) sh.lower = sh.body.toLowerCase();
        return sh.lower;
    }

    // 当たった位置がどのページか
    function docAt(sh, pos) {
        let lo = 0, hi = sh.starts.length - 1;
        while (lo < hi) {
            const mid = (lo + hi + 1) >> 1;
            if (sh.starts[mid] <= pos) lo = mid; else hi = mid - 1;
        }
        return lo;
    }

    // 1語ぶん。ページごとに「何回出たか」と「最初に出た位置」を返す。
    function findTerm(term) {
        const needle = normalize(term);
        const hits = new Map();
        if (!needle) return hits;
        const useLower = /[A-Za-z]/.test(needle);
        const q = useLower ? needle.toLowerCase() : needle;

        for (let si = 0; si < shards.length; si++) {
            const sh = shards[si];
            const hay = useLower ? loweredBody(sh) : sh.body;
            let i = hay.indexOf(q);
            while (i >= 0) {
                const di = docAt(sh, i);
                const key = si + ':' + di;
                const cur = hits.get(key);
                if (cur) {
                    cur.tf += 1;
                } else {
                    hits.set(key, {
                        sh: sh, di: di, tf: 1,
                        at: i - sh.starts[di], // ページの中での位置
                    });
                }
                i = hay.indexOf(q, i + q.length);
            }
        }
        return hits;
    }

    function idf(df) {
        const n = totalPages || 1;
        return Math.log(1 + (n - df + 0.5) / (df + 0.5));
    }

    function score(hit, term, df, avgLen) {
        const doc = hit.sh.docs[hit.di];
        const len = doc[2] || avgLen;
        const body = (hit.tf * (K1 + 1)) /
            (hit.tf + K1 * (1 - B + B * (len / (avgLen || len || 1))));
        const inTitle = doc[1] && doc[1].indexOf(term) >= 0;
        return idf(df) * (body + (inTitle ? TITLE_WEIGHT : 0));
    }

    // AND: 全部の語が載っているページ。OR: どれかが載っているページ。
    function runQuery(terms, mode) {
        const avgLen = totalPages ? totalChars / totalPages : 1;
        let merged = null;

        for (const term of terms) {
            const hits = findTerm(term);
            const df = hits.size;

            if (merged === null) {
                merged = new Map();
                for (const [key, h] of hits) {
                    const s = score(h, term, df, avgLen);
                    merged.set(key, { hit: h, score: s, best: s, hits: 1 });
                }
                continue;
            }

            if (mode === 'or') {
                for (const [key, h] of hits) {
                    const s = score(h, term, df, avgLen);
                    const cur = merged.get(key);
                    if (!cur) {
                        merged.set(key, { hit: h, score: s, best: s, hits: 1 });
                    } else {
                        cur.hits += 1;
                        cur.score += s;
                        if (s > cur.best) { cur.best = s; cur.hit = h; }
                    }
                }
            } else {
                for (const [key, cur] of merged) {
                    const h = hits.get(key);
                    if (!h) { merged.delete(key); continue; }
                    const s = score(h, term, df, avgLen);
                    cur.score += s;
                    if (s > cur.best) { cur.best = s; cur.hit = h; }
                }
                if (!merged.size) break;
            }
        }

        if (!merged) return [];
        return [...merged.values()]
            .sort((a, b) => b.hits - a.hits || b.score - a.score);
    }

    // --- AND / OR の書き方 -------------------------------------------------
    // 語の区切りは半角/全角スペース・読点・カンマ。
    // 「祝福 | 家庭」「祝福 OR 家庭」「祝福 または 家庭」は選択に関係なく OR。
    const TERM_SEP = /[\s、,，]+/;
    const OR_MARK = /^(?:\||｜|[Oo][Rr]|または)$/;

    function parseQuery(raw, mode) {
        const tokens = raw.replace(/[|｜]/g, ' | ').replace(/または/g, ' | ')
            .split(TERM_SEP).map(t => t.replace(/["'“”「」]/g, '')).filter(Boolean);
        const hasOrMark = tokens.some(t => OR_MARK.test(t));
        const terms = [...new Set(tokens.filter(t => !OR_MARK.test(t)))];

        // 「または」そのものを探しているときは、区切りではなく語として扱う
        if (!terms.length) return { mode: 'and', terms: [raw] };

        const or = terms.length > 1 && (hasOrMark || mode === 'or');
        return { mode: or ? 'or' : 'and', terms: terms };
    }

    // --- 画面 -------------------------------------------------------------
    const input = document.getElementById('search-input');
    const btn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    const statsContainer = document.getElementById('search-stats');
    const modeInputs = Array.from(document.querySelectorAll('input[name="search-mode"]'));
    const bibleInput = document.getElementById('exclude-bible');

    const MODE_KEY = 'mimune-search-mode';
    const BIBLE_KEY = 'mimune-search-exclude-bible';

    // ページの置き場所（GitHub Pages では /mimune-no-uraniwa/）
    const BASE = new URL('.', document.currentScript
        ? document.currentScript.src : location.href).pathname;

    function currentMode() {
        const checked = modeInputs.find(el => el.checked);
        return checked ? checked.value : 'and';
    }

    // 1冊の中を探しているときは、聖書を外すも何もない
    function excludingBible() {
        return !scopeBook && !!(bibleInput && bibleInput.checked);
    }

    // --- 「1冊の中だけ」の見せ方 -------------------------------------------
    const headingLink = document.querySelector('h1 a');
    const backLink = document.querySelector('a.nav-link');
    const bibleRow = bibleInput ? bibleInput.closest('.search-filter') : null;
    const scopeNote = document.getElementById('search-scope');

    function showScope() {
        if (!scopeBook) return;
        const name = scopeTitle ? `『${scopeTitle}』` : 'この書籍';
        if (headingLink) headingLink.textContent = name + 'の中から検索';
        document.title = `み旨の裏庭 | ${name}の中から検索`;
        if (backLink) {
            backLink.textContent = `← ${name}の目次に戻る`;
            backLink.setAttribute('href', encodeURI(scopeBook) + '/index.html');
        }
        if (bibleRow) bibleRow.hidden = true;
        if (scopeNote) {
            scopeNote.innerHTML = '';
            scopeNote.appendChild(document.createTextNode(
                name + 'の中だけを探しています。'));
            const all = document.createElement('a');
            all.href = 'search-all.html';
            all.textContent = 'サイト全体から探す';
            scopeNote.appendChild(all);
            scopeNote.hidden = false;
        }
    }

    // 知らない書籍名だったとき。サイト全体の見た目に戻す。
    function clearScope() {
        if (headingLink) headingLink.textContent = 'サイト内一括検索';
        document.title = 'み旨の裏庭 | サイト内一括検索';
        if (backLink) {
            backLink.textContent = '← トップページに戻る';
            backLink.setAttribute('href', 'index.html');
        }
        if (bibleRow) bibleRow.hidden = false;
        if (scopeNote) {
            scopeNote.hidden = true;
            scopeNote.innerHTML = '';
        }
    }

    // タイトルが分かるのは manifest が届いてからなので、まず入れ物だけ整える
    showScope();

    try {
        const saved = localStorage.getItem(MODE_KEY);
        const target = modeInputs.find(el => el.value === saved);
        if (target) target.checked = true;
        // 既定は「聖書を除く」。入れてほしいと言われたときだけ入れる。
        if (bibleInput) bibleInput.checked = localStorage.getItem(BIBLE_KEY) !== '0';
    } catch (e) { /* localStorage が使えない環境は既定のまま */ }

    function escapeHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function highlightRe(terms) {
        const esc = terms
            .map(t => normalize(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
            .filter(Boolean);
        return esc.length ? new RegExp('(' + esc.join('|') + ')', 'gi') : null;
    }

    // 当たった所の前後を切り出して、語に色を付ける
    function excerpt(hit, re) {
        const doc = hit.sh.docs[hit.di];
        const from = hit.sh.starts[hit.di];
        const start = Math.max(0, hit.at - EXCERPT_BEFORE);
        const end = Math.min(doc[2], hit.at + EXCERPT_AFTER);
        const text = hit.sh.body.slice(from + start, from + end);

        let html = '';
        if (re) {
            let last = 0;
            let m;
            re.lastIndex = 0;
            while ((m = re.exec(text)) !== null) {
                if (m[0].length === 0) { re.lastIndex += 1; continue; }
                html += escapeHtml(text.slice(last, m.index));
                html += '<mark>' + escapeHtml(m[0]) + '</mark>';
                last = m.index + m[0].length;
            }
            html += escapeHtml(text.slice(last));
        } else {
            html = escapeHtml(text);
        }
        return (start > 0 ? '…' : '') + html + (end < doc[2] ? '…' : '');
    }

    // 1件ぶんの HTML。要素を1つずつ作ると1,800件で4秒以上かかるので、
    // 文字列にまとめて一度だけ innerHTML に渡す。
    function itemHtml(entry, re) {
        const doc = entry.hit.sh.docs[entry.hit.di];
        const href = escapeHtml(encodeURI(BASE + doc[0]));
        return '<div class="result-item"><div class="result-title">' +
            '<a href="' + href + '">' + escapeHtml(doc[1] || doc[0]) + '</a>' +
            '</div><div class="result-snippet">' + excerpt(entry.hit, re) +
            '</div></div>';
    }

    let renderToken = 0;

    function pct() {
        return totalBytes ? Math.round(loadedBytes / totalBytes * 100) : 0;
    }

    function runSearch() {
        const query = input.value.trim();
        if (!query) return;
        const token = ++renderToken;

        // まだ1つも届いていないときは、届いてから
        if (!shards.length) {
            resultsContainer.innerHTML = '';
            statsContainer.textContent = '本文を読み込み中...';
            loadCorpus(progress)
                .then(() => { if (token === renderToken) runSearch(); })
                .catch(() => { statsContainer.textContent = '本文を読み込めませんでした。'; });
            return;
        }

        const parsed = parseQuery(query, currentMode());
        let results = runQuery(parsed.terms, parsed.mode);

        // 聖書を外す。全部が聖書だったときのために、外した件数を出す。
        let dropped = 0;
        if (excludingBible()) {
            const kept = results.filter(e =>
                e.hit.sh.docs[e.hit.di][0].indexOf(BIBLE_PREFIX) !== 0);
            dropped = results.length - kept.length;
            results = kept;
        }

        const label = parsed.mode === 'or'
            ? parsed.terms.map(t => `「${t}」`).join('と')
            : `「${parsed.terms.join(' ')}」`;
        const how = parsed.terms.length > 1
            ? (parsed.mode === 'or' ? '（どれかを含む）' : '（すべて含む）')
            : '';
        const minus = dropped ? `（聖書の${dropped}件を除く）` : '';
        const partial = ready ? '' : `　※本文を読み込み中（${pct()}%）。揃ったら出し直します`;

        resultsContainer.innerHTML = '';
        if (!results.length) {
            statsContainer.textContent = dropped
                ? `${label}に一致するのは聖書の${dropped}件だけでした。${partial}`
                : `${label}に一致するページはありませんでした。${how}${partial}`;
            return;
        }

        statsContainer.textContent =
            `${label}の検索結果: ${results.length}件${how}${minus}${partial}`;

        const re = highlightRe(parsed.terms);
        const html = new Array(results.length);
        for (let i = 0; i < results.length; i++) html[i] = itemHtml(results[i], re);
        resultsContainer.innerHTML = html.join('');
    }

    // 読み込みの途中経過。検索済みなら、揃った時点で出し直す。
    function progress() {
        if (resultsContainer.children.length || renderToken) {
            if (ready && input.value.trim()) runSearch();
            return;
        }
        statsContainer.textContent = ready ? '' : `本文を読み込み中... ${pct()}%`;
    }

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runSearch();
    });
    btn.addEventListener('click', runSearch);

    // AND / OR や聖書の有無を切り替えたら、いま出ている結果をその場で引き直す
    for (const el of modeInputs) {
        el.addEventListener('change', () => {
            try { localStorage.setItem(MODE_KEY, el.value); } catch (e) { }
            if (input.value.trim()) runSearch();
        });
    }
    if (bibleInput) {
        bibleInput.addEventListener('change', () => {
            try {
                localStorage.setItem(BIBLE_KEY, bibleInput.checked ? '1' : '0');
            } catch (e) { }
            if (input.value.trim()) runSearch();
        });
    }

    // ページを開いた時点で裏で読み始める。打ち終わる頃には揃っている。
    loadCorpus(progress).catch(() => { });
})();

/* サイト内一括検索 — pagefind (pagefind/) を使う。
   以前は data/search-index.json を丸ごと（約57MB）取りに行っていた。 */
(function () {
    // 結果は全部出す。ただし本文の抜粋は1件ずつ取りに行くので、
    // この数ずつ描いては画面に返し、待たされている感じを減らす。
    const CHUNK = 25;

    // 抜粋の長さ（語数）。pagefind の既定は 30 で、日本語だと40字ほどにしか
    // ならない。4〜5行ぶんの前後関係が見えるように広げる。
    const EXCERPT_LENGTH = 140;

    // 日本語の区切りが入っていないページでは、pagefind が本文をまるごと
    // 抜粋として返してくることがある（1万字を超えることもある）。
    // 見出しに当たった語の周りだけを残す。
    const MAX_EXCERPT_CHARS = 300;

    // 索引（pagefind）は日本語を単語に切って持っている（「み旨」→「み」「旨」）。
    // ところが検索側の wasm は日本語を切らないので、「み旨」と打つとその6文字が
    // 丸ごと1語として探され、どこにも無いので0件になる。ここで問い合わせ側も
    // 同じように切ってから渡す。
    const CJK = /[぀-ヿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ]/;

    function segment(query) {
        if (typeof Intl !== 'undefined' && Intl.Segmenter) {
            const seg = new Intl.Segmenter('ja', { granularity: 'word' });
            const words = Array.from(seg.segment(query))
                .filter(s => s.isWordLike)
                .map(s => s.segment);
            if (words.length) return words;
        }
        // Intl.Segmenter が無いブラウザ: 日本語は1文字ずつに割る
        return query.split(/\s+/)
            .flatMap(w => (CJK.test(w) ? Array.from(w) : [w]))
            .filter(Boolean);
    }

    // ブラウザの切り方（ICU）と索引の切り方（pagefind）は完全には一致しない。
    // 例えば「神様」は ICU では1語、索引では「神」＋「様」。0件だったときだけ、
    // 索引に無い語を探して1文字ずつに割り、もう一度引く。
    //
    // これは「切った語がページのどこかにあれば当たる」引き方なので、
    // 「愛はない」と打つと「愛」「は」「ない」がばらばらにあるページまで出る
    // （1375件）。並びのまま探す searchPhrase で駄目だったときの保険に使う。
    async function searchLoose(pf, query) {
        const words = segment(query);
        if (!words.length) return await pf.search(query);

        const result = await pf.search(words.join(' '));
        if (result.results.length) return result;

        const retry = [];
        let changed = false;
        for (const word of words) {
            if (word.length > 1 && CJK.test(word) &&
                (await pf.search(word)).results.length === 0) {
                retry.push(...Array.from(word));
                changed = true;
            } else {
                retry.push(word);
            }
        }
        if (!changed) return result;
        return await pf.search(retry.join(' '));
    }

    // 打った通りの並びで探す。pagefind は問い合わせ全体が " " で囲まれていると
    // 語の連続として扱う（「愛 は ない」がその順で並んでいるページだけ）。
    // 索引の切り方と合わなければ0件になるので、そのときは null を返す。
    async function searchPhrase(pf, term) {
        const words = segment(term);
        if (!words.length) return null;
        const result = await pf.search(`"${words.join(' ')}"`);
        return result.results.length ? result.results : null;
    }

    // 1語ぶんの検索。まず並びのまま、駄目なら語をばらして。
    async function searchTerm(pf, term) {
        return (await searchPhrase(pf, term)) || (await searchLoose(pf, term)).results;
    }

    // --- AND / OR ---------------------------------------------------------
    // 語の区切りは半角/全角スペース・読点・カンマ。
    // 「祝福 | 家庭」「祝福 OR 家庭」「祝福 または 家庭」と書いたときは、
    // ラジオボタンの選択に関係なく OR で引く。
    const TERM_SEP = /[\s、,，]+/;
    const OR_MARK = /^(?:\||｜|[Oo][Rr]|または)$/;

    function parseQuery(raw, mode) {
        // 「|」「または」は前後にスペースが無くても区切りとして扱う
        // 引用符は pagefind に渡す前に自分で付けるので、打たれていても取る
        const tokens = raw.replace(/[|｜]/g, ' | ').replace(/または/g, ' | ')
            .split(TERM_SEP).map(t => t.replace(/["'“”「」]/g, '')).filter(Boolean);
        const hasOrMark = tokens.some(t => OR_MARK.test(t));
        const terms = [...new Set(tokens.filter(t => !OR_MARK.test(t)))];

        // 「または」そのものを探しているときは、区切りではなく語として扱う
        if (!terms.length) return { mode: 'and', terms: [raw] };

        // 語がひとつだけなら AND も OR も同じ
        const or = terms.length > 1 && (hasOrMark || mode === 'or');
        return { mode: or ? 'or' : 'and', terms };
    }

    // AND: 語ごとに引いて、全部に出てきたページだけ残す。
    // 「男女 愛はない」なら、両方がその並びで載っているページ。
    async function searchEvery(pf, terms) {
        let kept = null;
        for (const term of terms) {
            const list = await searchTerm(pf, term);
            const byId = new Map(list.map(r => [r.id, r]));

            if (kept === null) {
                kept = new Map(list.map(r => [r.id, { result: r, score: r.score || 0 }]));
                continue;
            }
            for (const [id, cur] of kept) {
                const r = byId.get(id);
                if (!r) { kept.delete(id); continue; }
                cur.score += r.score || 0;
                // 抜粋はいちばん強く当たった語のものを出す
                if ((r.score || 0) > (cur.result.score || 0)) cur.result = r;
            }
            if (!kept.size) break;
        }
        return [...kept.values()]
            .sort((a, b) => b.score - a.score)
            .map(v => v.result);
    }

    // OR: 語ごとに引いて結果を混ぜる。
    // 多くの語に当たったページほど上、同数ならスコア順。
    async function searchAny(pf, terms) {
        const found = new Map();
        for (const term of terms) {
            const list = await searchTerm(pf, term);
            for (const r of list) {
                const cur = found.get(r.id);
                if (!cur) {
                    found.set(r.id, { result: r, score: r.score || 0, hits: 1 });
                } else {
                    cur.hits += 1;
                    if ((r.score || 0) > cur.score) {
                        cur.score = r.score || 0;
                        cur.result = r; // 抜粋はいちばん強く当たった語のものを出す
                    }
                }
            }
        }
        return [...found.values()]
            .sort((a, b) => b.hits - a.hits || b.score - a.score)
            .map(v => v.result);
    }

    const input = document.getElementById('search-input');
    const btn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    const statsContainer = document.getElementById('search-stats');
    const modeInputs = Array.from(document.querySelectorAll('input[name="search-mode"]'));

    const MODE_KEY = 'mimune-search-mode';

    function currentMode() {
        const checked = modeInputs.find(el => el.checked);
        return checked ? checked.value : 'and';
    }

    try {
        const saved = localStorage.getItem(MODE_KEY);
        const target = modeInputs.find(el => el.value === saved);
        if (target) target.checked = true;
    } catch (e) { /* localStorage が使えない環境は既定のまま */ }

    let pagefind = null;
    let loading = null;
    let renderToken = 0;

    // pagefind は pagefind.js の置き場所から baseUrl を割り出して
    // result.url に付けてくれる（/mimune-no-uraniwa/... になる）ので、そのまま使う

    function loadPagefind() {
        if (pagefind) return Promise.resolve(pagefind);
        if (!loading) {
            loading = import('./pagefind/pagefind.js').then(async (mod) => {
                await mod.options({ excerptLength: EXCERPT_LENGTH });
                await mod.init();
                pagefind = mod;
                return mod;
            });
        }
        return loading;
    }

    async function runSearch() {
        const query = input.value.trim();
        if (!query) return;

        const token = ++renderToken; // 前の検索の描画を止める
        resultsContainer.innerHTML = '';
        statsContainer.textContent = '検索中...';

        let pf;
        try {
            pf = await loadPagefind();
        } catch (e) {
            statsContainer.textContent = '検索データを読み込めませんでした。';
            return;
        }

        const parsed = parseQuery(query, currentMode());
        let results;
        let note = '';
        try {
            results = parsed.mode === 'or'
                ? await searchAny(pf, parsed.terms)
                : await searchEvery(pf, parsed.terms);

            // 全部の語が載っているページが無いときは、語をばらして探し直す。
            // 黙って広げると件数の意味が変わるので、そのことを画面に書く。
            if (!results.length && parsed.terms.length > 1) {
                const loose = await searchLoose(pf, parsed.terms.join(' '));
                if (loose.results.length) {
                    results = loose.results;
                    note = '（そのままの並びでは見つからないので、語をばらして探しました）';
                }
            }
        } catch (e) {
            statsContainer.textContent = '検索に失敗しました。';
            return;
        }

        const label = parsed.mode === 'or'
            ? parsed.terms.map(t => `「${t}」`).join('と')
            : `「${parsed.terms.join(' ')}」`;
        const how = parsed.terms.length > 1
            ? (parsed.mode === 'or' ? '（どれかを含む）' : '（すべて含む）')
            : '';
        if (results.length === 0) {
            statsContainer.textContent = `${label}に一致するページはありませんでした。${how}`;
            return;
        }
        const stats = `${label}の検索結果: ${results.length}件${note || how}`;
        statsContainer.textContent = stats;
        await renderAll(results, stats, token);
    }

    // 抜粋に入るタグは <mark> だけ。当たった語の手前から MAX_EXCERPT_CHARS 字を残す。
    function trimExcerpt(html) {
        const parts = html.split(/(<\/?mark>)/);
        let plainLen = 0;
        let markAt = -1;
        for (const p of parts) {
            if (p === '<mark>') { if (markAt < 0) markAt = plainLen; continue; }
            if (p === '</mark>') continue;
            plainLen += p.length;
        }
        if (plainLen <= MAX_EXCERPT_CHARS) return html;

        const start = Math.max(0, Math.max(markAt, 0) - Math.floor(MAX_EXCERPT_CHARS / 3));
        const end = start + MAX_EXCERPT_CHARS;

        let out = '';
        let pos = 0;
        for (const p of parts) {
            if (p === '<mark>' || p === '</mark>') {
                if (pos >= start && pos <= end) out += p;
                continue;
            }
            const from = Math.max(start, pos);
            const to = Math.min(end, pos + p.length);
            if (to > from) out += p.slice(from - pos, to - pos);
            pos += p.length;
        }

        // 切ったところで <mark> が開きっぱなし／閉じっぱなしになるのを直す
        const opens = (out.match(/<mark>/g) || []).length;
        const closes = (out.match(/<\/mark>/g) || []).length;
        if (opens > closes) out += '</mark>';
        if (closes > opens) out = '<mark>' + out;

        return (start > 0 ? '…' : '') + out + (end < plainLen ? '…' : '');
    }

    function buildItem(d) {
        const item = document.createElement('div');
        item.className = 'result-item';

        const title = document.createElement('div');
        title.className = 'result-title';
        const link = document.createElement('a');
        link.href = d.url;
        link.textContent = (d.meta && d.meta.title) ? d.meta.title : d.url;
        title.appendChild(link);

        const snippet = document.createElement('div');
        snippet.className = 'result-snippet';
        snippet.innerHTML = trimExcerpt(d.excerpt); // pagefind が <mark> を付けて返す

        item.appendChild(title);
        item.appendChild(snippet);
        return item;
    }

    // 全件出す。抜粋は1件ずつ取りに行くので、少しずつ描いて画面を返す。
    async function renderAll(results, stats, token) {
        let shown = 0;
        for (let i = 0; i < results.length; i += CHUNK) {
            if (token !== renderToken) return; // 新しい検索が始まった
            const batch = results.slice(i, i + CHUNK);
            const data = await Promise.all(batch.map(r => r.data().catch(() => null)));
            if (token !== renderToken) return;

            const frag = document.createDocumentFragment();
            for (const d of data) {
                if (d) frag.appendChild(buildItem(d));
            }
            resultsContainer.appendChild(frag);
            shown += batch.length;

            if (shown < results.length) {
                statsContainer.textContent = `${stats} — ${shown}件目まで表示中...`;
            } else {
                statsContainer.textContent = stats;
            }
        }
    }

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runSearch();
    });
    btn.addEventListener('click', runSearch);

    // AND / OR を切り替えたら、いま出ている結果をその場で引き直す
    for (const el of modeInputs) {
        el.addEventListener('change', () => {
            try { localStorage.setItem(MODE_KEY, el.value); } catch (e) { }
            if (input.value.trim()) runSearch();
        });
    }

    // 入力を始めた時点で裏読みしておくと、Enter を押した瞬間に結果が出る
    input.addEventListener('focus', () => { loadPagefind().catch(() => { }); }, { once: true });
})();

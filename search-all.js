/* サイト内一括検索 — pagefind (pagefind/) を使う。
   以前は data/search-index.json を丸ごと（約57MB）取りに行っていた。 */
(function () {
    const PAGE_SIZE = 20;

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
    async function searchJapanese(pf, query) {
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

    // --- AND / OR ---------------------------------------------------------
    // 語の区切りは半角/全角スペース・読点・カンマ。
    // 「祝福 | 家庭」「祝福 OR 家庭」「祝福 または 家庭」と書いたときは、
    // ラジオボタンの選択に関係なく OR で引く。
    const TERM_SEP = /[\s、,，]+/;
    const OR_MARK = /^(?:\||｜|[Oo][Rr]|または)$/;

    function parseQuery(raw, mode) {
        // 「|」「または」は前後にスペースが無くても区切りとして扱う
        const tokens = raw.replace(/[|｜]/g, ' | ').replace(/または/g, ' | ')
            .split(TERM_SEP).filter(Boolean);
        const hasOrMark = tokens.some(t => OR_MARK.test(t));
        const terms = [...new Set(tokens.filter(t => !OR_MARK.test(t)))];

        // 「または」そのものを探しているときは、区切りではなく語として扱う
        if (!terms.length) return { mode: 'and', terms: [raw] };

        // 語がひとつだけなら AND も OR も同じ
        const or = terms.length > 1 && (hasOrMark || mode === 'or');
        return { mode: or ? 'or' : 'and', terms };
    }

    // OR: 語ごとに引いて結果を混ぜる。
    // 多くの語に当たったページほど上、同数ならスコア順。
    async function searchAny(pf, terms) {
        const found = new Map();
        for (const term of terms) {
            const res = await searchJapanese(pf, term);
            for (const r of res.results) {
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
    let pending = [];
    let shown = 0;

    // pagefind は pagefind.js の置き場所から baseUrl を割り出して
    // result.url に付けてくれる（/mimune-no-uraniwa/... になる）ので、そのまま使う

    function loadPagefind() {
        if (pagefind) return Promise.resolve(pagefind);
        if (!loading) {
            loading = import('./pagefind/pagefind.js').then(async (mod) => {
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

        resultsContainer.innerHTML = '';
        shown = 0;
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
        try {
            results = parsed.mode === 'or'
                ? await searchAny(pf, parsed.terms)
                : (await searchJapanese(pf, parsed.terms.join(' '))).results;
        } catch (e) {
            statsContainer.textContent = '検索に失敗しました。';
            return;
        }

        pending = results;
        const label = parsed.mode === 'or'
            ? parsed.terms.map(t => `「${t}」`).join('と')
            : `「${parsed.terms.join(' ')}」`;
        const how = parsed.terms.length > 1
            ? (parsed.mode === 'or' ? '（どれかを含む）' : '（すべて含む）')
            : '';
        if (pending.length === 0) {
            statsContainer.textContent = `${label}に一致するページはありませんでした。${how}`;
            return;
        }
        statsContainer.textContent = `${label}の検索結果: ${pending.length}件${how}`;
        await showMore();
    }

    async function showMore() {
        const batch = pending.slice(shown, shown + PAGE_SIZE);
        shown += batch.length;

        const data = await Promise.all(batch.map(r => r.data()));
        for (const d of data) {
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
            snippet.innerHTML = d.excerpt; // pagefind が <mark> を付けて返す

            item.appendChild(title);
            item.appendChild(snippet);
            resultsContainer.appendChild(item);
        }

        const old = document.getElementById('search-more');
        if (old) old.remove();

        if (shown < pending.length) {
            const more = document.createElement('button');
            more.id = 'search-more';
            more.textContent = `さらに表示（残り ${pending.length - shown}件）`;
            more.addEventListener('click', () => {
                more.disabled = true;
                showMore();
            });
            resultsContainer.appendChild(more);
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

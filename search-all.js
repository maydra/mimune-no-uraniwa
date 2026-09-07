/* サイト内一括検索 — pagefind (pagefind/) を使う。
   以前は data/search-index.json を丸ごと（約57MB）取りに行っていた。 */
(function () {
    const PAGE_SIZE = 20;

    const input = document.getElementById('search-input');
    const btn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    const statsContainer = document.getElementById('search-stats');

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

        let search;
        try {
            search = await pf.search(query);
        } catch (e) {
            statsContainer.textContent = '検索に失敗しました。';
            return;
        }

        pending = search.results;
        if (pending.length === 0) {
            statsContainer.textContent = `「${query}」に一致するページはありませんでした。`;
            return;
        }
        statsContainer.textContent = `「${query}」の検索結果: ${pending.length}件`;
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

    // 入力を始めた時点で裏読みしておくと、Enter を押した瞬間に結果が出る
    input.addEventListener('focus', () => { loadPagefind().catch(() => { }); }, { once: true });
})();

(function () {
    const INDEX_URL = 'data/search-index.json';
    let searchIndex = null;
    let isLoading = false;

    const input = document.getElementById('search-input');
    const btn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('search-results');
    const statsContainer = document.getElementById('search-stats');

    // Trigger search on Enter
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadAndSearch();
        }
    });

    btn.addEventListener('click', () => {
        loadAndSearch();
    });

    function loadAndSearch() {
        const query = input.value.trim();
        if (!query) return;

        if (isLoading) return;

        if (!searchIndex) {
            isLoading = true;
            statsContainer.textContent = 'データ読み込み中 (約50MB)... しばらくお待ち下さい...';

            fetch(INDEX_URL)
                .then(response => {
                    if (!response.ok) throw new Error('Index not found');
                    return response.json();
                })
                .then(data => {
                    searchIndex = data;
                    isLoading = false;
                    performSearch(query);
                })
                .catch(err => {
                    console.error(err);
                    isLoading = false;
                    statsContainer.textContent = 'エラー: 検索データを読み込めませんでした。ローカルサーバー(http.server)等で実行してください。';
                });
        } else {
            performSearch(query);
        }
    }

    function performSearch(query) {
        const rawKeywords = query.trim().split(/\s+/).filter(k => k.length > 0);

        statsContainer.textContent = '検索中...';

        // Use timeout to allow UI to update "Searching..." text
        setTimeout(() => {
            const keywords = rawKeywords.map(k => k.normalize('NFKC').toLowerCase());
            const results = [];

            for (const item of searchIndex) {
                const title = (item.title || '').normalize('NFKC');
                const text = (item.text || '').normalize('NFKC');
                const titleLower = title.toLowerCase();
                const textLower = text.toLowerCase();

                let totalHits = 0;
                let allKeywordsFound = true;

                for (const kw of keywords) {
                    let hits = 0;
                    hits += (titleLower.split(kw).length - 1) * 2;
                    hits += (textLower.split(kw).length - 1);

                    if (hits === 0) {
                        allKeywordsFound = false;
                        break;
                    }
                    totalHits += hits;
                }

                if (allKeywordsFound) {
                    results.push({
                        item: item,
                        hits: totalHits,
                        originalTitle: item.title,
                        originalText: item.text
                    });
                }
            }

            results.sort((a, b) => b.hits - a.hits);
            renderResults(results, keywords);
        }, 10);
    }

    function renderResults(results, keywords) {
        statsContainer.textContent = `${results.length} 件見つかりました (描画中...)`;
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>該当するページが見つかりませんでした。</p>';
            statsContainer.textContent = '0 件見つかりました';
            return;
        }

        const CHUNK_SIZE = 50;
        let currentIndex = 0;

        function renderChunk() {
            const fragment = document.createDocumentFragment();
            const chunkEnd = Math.min(currentIndex + CHUNK_SIZE, results.length);

            for (let i = currentIndex; i < chunkEnd; i++) {
                const res = results[i];
                const div = document.createElement('div');
                div.className = 'result-item';

                const snippet = generateSnippet(res.originalText, keywords);
                const title = highlightText(res.originalTitle, keywords);

                div.innerHTML = `
                    <div class="result-title"><a href="${res.item.url}">${title}</a></div>
                    <div class="result-snippet">${snippet}</div>
                `;
                fragment.appendChild(div);
            }

            resultsContainer.appendChild(fragment);
            currentIndex += CHUNK_SIZE;

            if (currentIndex < results.length) {
                statsContainer.textContent = `${results.length} 件見つかりました (描画中... ${currentIndex}/${results.length})`;
                // Use setTimeout to yield logic to browser for render
                setTimeout(renderChunk, 0);
            } else {
                statsContainer.textContent = `${results.length} 件見つかりました`;
            }
        }

        renderChunk();
    }

    function generateSnippet(text, keywords) {
        if (!text) return '';
        const lowerText = text.normalize('NFKC').toLowerCase();

        let bestIndex = -1;
        const firstKw = keywords[0];
        bestIndex = lowerText.indexOf(firstKw);

        if (bestIndex === -1) bestIndex = 0;

        const start = Math.max(0, bestIndex - 60);
        const end = Math.min(text.length, bestIndex + 60 + firstKw.length);

        let snippet = text.substring(start, end);
        if (start > 0) snippet = '...' + snippet;
        if (end < text.length) snippet = snippet + '...';

        return highlightText(snippet, keywords);
    }

    function highlightText(text, keywords) {
        if (!text) return '';
        const escapeRegExp = (string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

        let html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        keywords.forEach(kw => {
            const pattern = new RegExp(`(${escapeRegExp(kw)})`, 'gi');
            html = html.replace(pattern, '<mark>$1</mark>');
        });

        return html;
    }

})();

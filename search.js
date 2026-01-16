(function () {
    const BOOKS_URL = 'data/books.json';
    const BOOK_TERMS_BASE = 'data/book-terms/';
    const BOOKS_DATA_BASE = 'data/books/';

    let booksRegistry = [];
    let currentBookId = null; // If null, in "Global Search" mode. If set, in "Book Search" mode.

    // In-Book Index
    let paragraphsDB = null;
    let pagesDB = null;

    // UI Elements
    const input = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    const statsContainer = document.getElementById('search-stats');

    // Check URL params for deep linking
    const urlParams = new URLSearchParams(window.location.search);
    const initialBook = urlParams.get('book');
    const initialQuery = urlParams.get('q');

    init();

    async function init() {
        statsContainer.textContent = '初期化中...';
        try {
            const resp = await fetch(BOOKS_URL);
            if (!resp.ok) throw new Error('Books not found');
            booksRegistry = await resp.json();

            if (initialBook) {
                // Determine if valid book
                const book = booksRegistry.find(b => b.id === initialBook);
                if (book) {
                    switchToBookMode(book, initialQuery);
                    return;
                }
            }

            // Default: Global Mode
            switchToGlobalMode(initialQuery);

        } catch (e) {
            console.error(e);
            statsContainer.textContent = 'データ読み込みに失敗しました。';
        }
    }

    // --- MODE SWITCHING ---

    function switchToGlobalMode(defaultQuery = '') {
        currentBookId = null;
        input.value = defaultQuery || '';
        input.placeholder = "全集から検索（言葉を入力してください）";
        statsContainer.textContent = "全集検索モード: 言葉を入力すると、その言葉が含まれる巻（フォルダ）を表示します。";
        resultsContainer.innerHTML = '';

        if (defaultQuery) {
            performGlobalSearch(defaultQuery);
        }
    }

    async function switchToBookMode(book, defaultQuery = '') {
        currentBookId = book.id;
        input.value = defaultQuery || '';
        input.placeholder = `${book.title} 内を検索`;
        statsContainer.textContent = `読み込み中... (${book.title})`;
        resultsContainer.innerHTML = '';

        // Load Book Index
        try {
            const [pData, pageData] = await Promise.all([
                fetch(`${BOOKS_DATA_BASE}${book.id}/paragraphs.json`).then(r => r.json()),
                fetch(`${BOOKS_DATA_BASE}${book.id}/page-paragraphs.json`).then(r => r.json())
            ]);

            paragraphsDB = pData;
            pagesDB = pageData;

            statsContainer.textContent = `${book.title} 内検索モード`;

            // Add "Back to Global" link
            const backBtn = document.createElement('button');
            backBtn.textContent = "← 全集検索に戻る";
            backBtn.onclick = () => {
                // Update URL
                const nextUrl = window.location.pathname;
                history.pushState({}, '', nextUrl);
                switchToGlobalMode('');
            };

            statsContainer.prepend(backBtn);
            statsContainer.prepend(document.createTextNode(" "));

            if (defaultQuery) {
                performBookSearch(defaultQuery);
            }

        } catch (e) {
            console.error(e);
            statsContainer.textContent = `インデックスの読み込みに失敗しました (${book.title})`;
        }
    }

    // --- EVENT LISTENERS ---

    let debounceTimer;
    input.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const val = e.target.value.trim();
            if (currentBookId) {
                performBookSearch(val);
            } else {
                performGlobalSearch(val);
            }
        }, 300);
    });

    // --- GLOBAL SEARCH (Stage 1) ---
    async function performGlobalSearch(query) {
        if (!query) {
            resultsContainer.innerHTML = '';
            statsContainer.textContent = "全集検索モード";
            return;
        }

        statsContainer.textContent = "検索中...";
        resultsContainer.innerHTML = '';

        const term = query.trim().split(/\s+/)[0];
        if (!term) return;

        const hits = [];

        const promises = booksRegistry.map(book => {
            return fetch(`${BOOK_TERMS_BASE}${book.id}.json`)
                .then(r => {
                    if (!r.ok) return [];
                    return r.json();
                })
                .then(terms => {
                    const q = term.normalize('NFKC').toLowerCase();
                    if (terms.some(t => t.includes(q))) {
                        hits.push(book);
                    }
                })
                .catch(e => { /* ignore missing */ });
        });

        await Promise.all(promises);

        statsContainer.textContent = `${hits.length} 巻に見つかりました`;
        renderGlobalResults(hits, term);
    }

    function renderGlobalResults(books, term) {
        const fragment = document.createDocumentFragment();
        if (books.length === 0) {
            resultsContainer.innerHTML = '<p>見つかりませんでした。</p>';
            return;
        }

        books.forEach(book => {
            const div = document.createElement('div');
            div.className = 'result-item';
            div.style.cursor = 'pointer';

            div.innerHTML = `
                <div class="result-title">📂 ${book.title}</div>
                <div class="result-snippet">この巻内を検索する &gt;</div>
            `;

            div.onclick = () => {
                const newUrl = `${window.location.pathname}?book=${book.id}&q=${encodeURIComponent(term)}`;
                history.pushState({ book: book.id, q: term }, '', newUrl);
                switchToBookMode(book, term);
            };

            fragment.appendChild(div);
        });

        resultsContainer.appendChild(fragment);
    }

    // --- BOOK SEARCH (Stage 2) ---
    function performBookSearch(query) {
        const rawKeywords = query.trim().split(/\s+/).filter(k => k.length > 0);

        if (rawKeywords.length === 0) {
            resultsContainer.innerHTML = '';
            statsContainer.textContent = `${currentBookId} 内検索モード`;
            // Re-render back button if needed, but handled by textContent being simplistic.
            if (!statsContainer.querySelector('button')) {
                const backBtn = document.createElement('button');
                backBtn.textContent = "← 全集検索に戻る";
                backBtn.onclick = () => {
                    const url = window.location.pathname;
                    history.pushState({}, '', url);
                    switchToGlobalMode('');
                };
                statsContainer.prepend(backBtn);
                statsContainer.prepend(document.createTextNode(" "));
            }
            return;
        }

        const keywords = rawKeywords.map(k => k.normalize('NFKC').toLowerCase());

        // Step 1: Find matching PIDs
        const matchingPids = new Set();

        for (const [pid, text] of Object.entries(paragraphsDB)) {
            const lowerText = text.normalize('NFKC').toLowerCase();
            let allFound = true;

            for (const kw of keywords) {
                if (!lowerText.includes(kw)) {
                    allFound = false;
                    break;
                }
            }

            if (allFound) {
                matchingPids.add(pid);
            }
        }

        // Step 2: Match Pages
        const results = [];

        for (const page of pagesDB) {
            let pageHits = 0;
            let bestPid = null;
            let maxPidHits = 0;

            const titleLower = (page.title || '').normalize('NFKC').toLowerCase();
            let titleMatch = true;

            for (const kw of keywords) {
                const count = titleLower.split(kw).length - 1;
                if (count <= 0) {
                    titleMatch = false;
                }
            }

            const pageKeywordsFound = new Set();
            if (titleMatch) {
                keywords.forEach(k => pageKeywordsFound.add(k));
            } else {
                keywords.forEach(k => {
                    if (titleLower.includes(k)) pageKeywordsFound.add(k);
                });
            }

            page.pids.forEach(pid => {
                const text = paragraphsDB[pid];
                if (!text) return;
                const lowerText = text.normalize('NFKC').toLowerCase();

                keywords.forEach(kw => {
                    if (lowerText.includes(kw)) {
                        pageKeywordsFound.add(kw);
                        pageHits++;

                        if (pageHits > maxPidHits) {
                            bestPid = pid;
                            maxPidHits = pageHits;
                        }
                        if (!bestPid) bestPid = pid;
                    }
                });
            });

            if (pageKeywordsFound.size === keywords.length) {
                results.push({
                    page: page,
                    hits: pageHits + (titleMatch ? 10 : 0),
                    snippetPid: bestPid
                });
            }
        }

        results.sort((a, b) => b.hits - a.hits);
        renderBookResults(results, keywords);
    }

    function renderBookResults(results, keywords) {
        if (!statsContainer.querySelector('button')) {
            const backBtn = document.createElement('button');
            backBtn.textContent = "← 全集検索に戻る";
            backBtn.onclick = () => {
                const url = window.location.pathname;
                history.pushState({}, '', url);
                switchToGlobalMode('');
            };
            statsContainer.innerHTML = '';
            statsContainer.appendChild(backBtn);
            statsContainer.appendChild(document.createTextNode(" "));
        }

        const span = document.createElement('span');
        span.textContent = `${results.length} 件見つかりました`;

        // Remove old span if exists (anything after button and space)
        while (statsContainer.childNodes.length > 2) {
            statsContainer.removeChild(statsContainer.lastChild);
        }
        statsContainer.appendChild(span);

        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>該当するページが見つかりませんでした。</p>';
            return;
        }

        const fragment = document.createDocumentFragment();

        results.slice(0, 50).forEach(res => {
            const div = document.createElement('div');
            div.className = 'result-item';

            const snippetText = res.snippetPid ? paragraphsDB[res.snippetPid] : res.page.title;
            const snippet = generateSnippet(snippetText, keywords);
            const title = highlightText(res.page.title, keywords);

            div.innerHTML = `
                <div class="result-title"><a href="${res.page.url}">${title}</a></div>
                <div class="result-snippet">${snippet}</div>
            `;
            fragment.appendChild(div);
        });

        resultsContainer.appendChild(fragment);
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

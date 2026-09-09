// バージョンを上げると、古いキャッシュは activate 時に全部消える
// v4: 全文検索の本文を書籍ごとに分け直してファイル名が総入れ替えになった。
// 古い manifest.json が残っていると、もう無いシャードを探しに行ってしまう。
const CACHE_NAME = 'mimune-cache-v4';
const STATIC_URLS = [
    './index.html',
    './theme/style.css',
    './theme/script.js',
    './favicon.png',
    './manifest.json',
    './pages.json',
    './search-all.html',
    './search-all.js',
    './gacha.html'
];

self.addEventListener('install', event => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// HTML かどうか（ページ本体か、ただの部品か）
function isPageRequest(request) {
    if (request.mode === 'navigate') return true;
    const accept = request.headers.get('accept') || '';
    if (accept.includes('text/html')) return true;
    const path = new URL(request.url).pathname;
    return path.endsWith('/') || path.endsWith('.html') || path.endsWith('.htm');
}

self.addEventListener('fetch', event => {
    const request = event.request;

    // GET 以外と外部ドメイン（Google Fonts / gtag など）には触らない
    if (request.method !== 'GET') return;
    if (new URL(request.url).origin !== self.location.origin) return;

    if (isPageRequest(request)) {
        // ページ本体はネットワーク優先。
        // これがないと、ページを直しても一度読んだ人には永久に古いままになる
        event.respondWith(
            fetch(request)
                .then(response => {
                    if (response && response.ok) {
                        const copy = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
                    }
                    return response;
                })
                .catch(() => caches.match(request).then(cached => cached || Promise.reject()))
        );
        return;
    }

    // CSS / JS / 画像などは、キャッシュを返しつつ裏で更新しておく
    event.respondWith(
        caches.match(request).then(cached => {
            const network = fetch(request).then(response => {
                if (response && response.ok) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
                }
                return response;
            }).catch(() => cached);
            return cached || network;
        })
    );
});

// Message handler to trigger caching
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'CACHE_ALL') {
        event.waitUntil(
            cacheAllFiles(event.source)
        );
    }
});

async function cacheAllFiles(client) {
    try {
        const cache = await caches.open(CACHE_NAME);

        // 1. Cache static files first
        await cache.addAll(STATIC_URLS);

        // 2. Fetch pages.json to get all content pages
        const response = await fetch('./pages.json');
        if (!response.ok) throw new Error('Failed to fetch pages.json');

        const pages = await response.json();

        // 3. Cache all pages from pages.json
        // We'll do this in chunks to avoid overwhelming the network/browser
        const total = pages.length;
        let count = 0;

        // Helper to post progress
        const postProgress = (current, total) => {
            if (client) {
                client.postMessage({
                    type: 'CACHE_PROGRESS',
                    current,
                    total
                });
            }
        };

        // Cache in batches
        const BATCH_SIZE = 20;
        for (let i = 0; i < pages.length; i += BATCH_SIZE) {
            const batch = pages.slice(i, i + BATCH_SIZE);
            const promises = batch.map(url => {
                // Normalize URL: remove leading slash if present, though pages.json seems to not have them
                // pages.json has "bokkaisyanomiti/0301010041.html" format
                const targetUrl = url.startsWith('/') ? url.substring(1) : url;
                // Ensure we encode it if needed, but fetch usually handles it.
                // However, some file names might have spaces or special chars.
                return cache.add(targetUrl).catch(err => {
                    console.warn(`Failed to cache ${targetUrl}:`, err);
                    // We continue even if one fails
                });
            });

            await Promise.all(promises);
            count += batch.length;
            postProgress(Math.min(count, total), total);
        }

        // 4. Notify completion
        if (client) {
            client.postMessage({ type: 'CACHE_COMPLETE' });
        }

    } catch (err) {
        console.error('Caching failed:', err);
        if (client) {
            client.postMessage({ type: 'CACHE_ERROR', error: err.toString() });
        }
    }
}

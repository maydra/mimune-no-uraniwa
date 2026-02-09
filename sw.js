const CACHE_NAME = 'mimune-cache-v1';
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
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
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

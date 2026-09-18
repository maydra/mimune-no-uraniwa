/* み旨の裏庭 service worker v5
 *
 * 方針: ふだんの閲覧は今までどおりネットワークから（SW が壊れても
 * サイトは壊れない）。開いたページは通りすがりに保存しておき、
 * オフラインのときだけキャッシュから出す。
 *
 * 「この本をオフライン保存」(offline.js) は CACHE_BOOK メッセージで
 * 書籍の全ページをまとめて取りに来る。進捗は postMessage で返す。
 *
 * 検索の本文 (data/fulltext/) は search-all.js が自前の Cache API
 * (mimune-fulltext-v1) で管理しているので、ここでは一切触らない。
 * 触ると「サイト更新のたびに検索が壊れる」事故になる（v4 の失敗）。
 */
const VERSION = 'v5';
const PAGES = 'mimune-pages-' + VERSION;   // HTML（見たページ＋保存した本）
const ASSETS = 'mimune-assets-' + VERSION; // CSS/JS/画像
const OFFLINE_URL = 'offline.html';

self.addEventListener('install', (event) => {
    event.waitUntil((async () => {
        const cache = await caches.open(ASSETS);
        await cache.put(OFFLINE_URL, await fetch(OFFLINE_URL, { cache: 'reload' }));
        await self.skipWaiting();
    })());
});

self.addEventListener('activate', (event) => {
    event.waitUntil((async () => {
        for (const key of await caches.keys()) {
            const stale =
                (key.startsWith('mimune-pages-') && key !== PAGES) ||
                (key.startsWith('mimune-assets-') && key !== ASSETS) ||
                key.startsWith('mimune-cache-'); // 旧世代（v4 以前）
            if (stale) await caches.delete(key);
        }
        await self.clients.claim();
    })());
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    if (url.origin !== location.origin) return;            // フォント等は素通し
    if (url.pathname.includes('/data/fulltext/')) return;  // 検索が自前管理

    // ページ: ネットワーク優先。届いたら保存、届かなければキャッシュ→案内ページ
    if (req.mode === 'navigate') {
        event.respondWith((async () => {
            try {
                const res = await fetch(req);
                if (res.ok) {
                    const copy = res.clone();
                    caches.open(PAGES).then((c) => c.put(req, copy)).catch(() => { });
                }
                return res;
            } catch (err) {
                const hit = await caches.match(req, { ignoreSearch: true });
                return hit || await caches.match(OFFLINE_URL);
            }
        })());
        return;
    }

    // CSS/JS/画像: キャッシュ優先（?v= が変われば URL ごと変わる）、裏で更新
    event.respondWith((async () => {
        const hit = await caches.match(req);
        const refresh = fetch(req).then((res) => {
            if (res && res.ok) {
                const copy = res.clone();
                caches.open(ASSETS).then((c) => c.put(req, copy)).catch(() => { });
            }
            return res;
        }).catch(() => null);
        if (hit) return hit;
        const res = await refresh;
        if (res) return res;
        return (await caches.match(req, { ignoreSearch: true })) || Response.error();
    })());
});

// --- 「この本をオフライン保存」 -------------------------------------------
self.addEventListener('message', (event) => {
    const msg = event.data || {};
    const reply = (m) => { if (event.source) event.source.postMessage(m); };

    if (msg.type === 'CACHE_BOOK') {
        event.waitUntil((async () => {
            const cache = await caches.open(PAGES);
            const urls = msg.urls || [];
            let done = 0;
            let failed = 0;
            const CHUNK = 8; // 一斉に投げると帯域を食い合うので少しずつ
            for (let i = 0; i < urls.length; i += CHUNK) {
                await Promise.all(urls.slice(i, i + CHUNK).map(async (u) => {
                    try {
                        const res = await fetch(u, { cache: 'no-cache' });
                        if (res.ok) await cache.put(u, res); else failed += 1;
                    } catch (err) { failed += 1; }
                    done += 1;
                }));
                reply({ type: 'BOOK_PROGRESS', book: msg.book, done: done, total: urls.length });
            }
            reply({ type: 'BOOK_DONE', book: msg.book, failed: failed, total: urls.length });
        })());
    } else if (msg.type === 'REMOVE_BOOK') {
        event.waitUntil((async () => {
            const cache = await caches.open(PAGES);
            for (const u of msg.urls || []) await cache.delete(u);
            reply({ type: 'BOOK_REMOVED', book: msg.book });
        })());
    }
});

/* theme/script.js */
(function () {
    // Smarter DP check: look for 'dp' as a directory segment
    const pathSegments = window.location.pathname.split(/[/\\]/);
    const isDP = pathSegments.includes('dp');

    // theme/style.css owns the look of #theme-toggle. A handful of old pages
    // (malsum/ など) never link it, so give those the same rules inline.
    function ensureToggleStyles() {
        if (document.querySelector('link[href*="theme/style.css"]')) return;
        if (document.getElementById('theme-toggle-style')) return;
        const style = document.createElement('style');
        style.id = 'theme-toggle-style';
        style.textContent = [
            '#theme-toggle{position:fixed;top:20px;right:20px;z-index:9999;',
            'width:44px;height:44px;border-radius:50%;',
            'background:rgba(255,255,255,0.2);backdrop-filter:blur(10px);',
            'border:1px solid rgba(255,255,255,0.3);',
            'display:flex;align-items:center;justify-content:center;',
            'cursor:pointer;font-size:20px;transition:all 0.3s ease;',
            'box-shadow:0 4px 15px rgba(0,0,0,0.2);}',
            'body.light-mode #theme-toggle{background:rgba(0,0,0,0.05);',
            'border-color:rgba(0,0,0,0.1);}',
            '#theme-toggle:hover{transform:scale(1.1);}',
            '@media (max-width:768px){#theme-toggle{top:auto;bottom:18px;right:14px;}}'
        ].join('');
        document.head.appendChild(style);
    }

    function applyTheme(theme) {
        if (isDP) {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            return;
        }

        document.body.classList.remove('light-mode', 'dark-mode');
        document.body.classList.add(theme + '-mode');

        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
        }
    }

    function init() {
        let savedTheme = null;

        try {
            savedTheme = localStorage.getItem('theme');
        } catch (e) {
            // private mode などで読めないときは既定値にフォールバックする
        }

        if (!savedTheme) {
            const path = window.location.pathname.toLowerCase();
            // Default logic
            if (path.includes('/bible_out/') ||
                path.includes('/seikonmondou/') ||
                path.includes('/dp/') ||
                path.includes('family_pledge.html')) {
                savedTheme = 'light';
            } else {
                savedTheme = 'dark';
            }
        }

        applyTheme(savedTheme);

        if (!isDP) {
            if (!document.getElementById('theme-toggle')) {
                ensureToggleStyles();

                const toggle = document.createElement('div');
                toggle.id = 'theme-toggle';
                toggle.setAttribute('aria-label', 'テーマ切り替え');
                toggle.setAttribute('role', 'button');
                toggle.setAttribute('tabindex', '0');
                toggle.innerHTML = savedTheme === 'light' ? '🌙' : '☀️';

                document.body.appendChild(toggle);

                const switchTheme = () => {
                    const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    try {
                        localStorage.setItem('theme', newTheme);
                    } catch (e) { }
                    applyTheme(newTheme);
                };

                toggle.addEventListener('click', switchTheme);
                toggle.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        switchTheme();
                    }
                });
            }
        }
    }

    // --- ルビ（<rt>）を含む本文のコピー対策 ---------------------------------
    // 各ページの CSS は rt に user-select:none を掛けているが、これはブラウザと
    // 貼り付け先によっては親文字（漢字）ごとコピーから落ちる。コピー内容を
    // こちらで組み立てて、親文字は必ず残し、ふりがなだけを外す。
    // ついでに <ruby> の中に入っている改行（"苦悶<rt>くもん</rt>\n" の \n）も
    // 取り除く。そのままだとルビ語のうしろに余計な空白が入ってコピーされる。
    function cleanRuby(root) {
        const rubies = root.querySelectorAll ? root.querySelectorAll('ruby') : [];

        for (const ruby of rubies) {
            for (const annotation of ruby.querySelectorAll('rt, rp')) {
                annotation.remove();
            }
            // 残った親文字から整形用の改行・インデントを落として、
            // <ruby> の入れ物ごとただの文字に置き換える
            const base = ruby.textContent.replace(/[\s　]+/g, '');
            ruby.replaceWith(document.createTextNode(base));
        }

        return root;
    }

    function handleCopy(e) {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;
        if (!e.clipboardData) return;

        // 入力欄の中のコピーには手を出さない
        const active = document.activeElement;
        if (active && /^(INPUT|TEXTAREA)$/.test(active.tagName)) return;

        const holder = document.createElement('div');
        let hasRuby = false;

        for (let i = 0; i < selection.rangeCount; i++) {
            const fragment = selection.getRangeAt(i).cloneContents();
            if (fragment.querySelector('ruby')) hasRuby = true;
            holder.appendChild(fragment);
        }

        // ルビが入っていない選択は既定の動作のままでよい
        if (!hasRuby) return;

        cleanRuby(holder);

        // innerText は画面に出ている要素でないと改行を拾わないので、
        // 見えない場所に一度置いてから読む
        holder.style.cssText = 'position:fixed;left:-9999px;top:0;';
        document.body.appendChild(holder);
        const plain = holder.innerText;
        const html = holder.innerHTML;
        document.body.removeChild(holder);

        e.clipboardData.setData('text/plain', plain);
        e.clipboardData.setData('text/html', html);
        e.preventDefault();
    }

    document.addEventListener('copy', handleCopy);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // --- PWA ---------------------------------------------------------------
    // この script.js はほぼ全ページが読んでいるので、ここで一度だけ
    // service worker を登録すればサイト全体がオフライン対応になる。
    // サイトの根は script.js 自身の URL（…/theme/script.js）から割り出す。
    try {
        if ('serviceWorker' in navigator && document.currentScript && document.currentScript.src) {
            const root = new URL('..', document.currentScript.src);
            navigator.serviceWorker.register(new URL('sw.js', root)).catch(function () { });
            if (!document.querySelector('link[rel="manifest"]')) {
                const m = document.createElement('link');
                m.rel = 'manifest';
                m.href = new URL('manifest.json', root).href;
                document.head.appendChild(m);
            }
            if (!document.querySelector('link[rel="apple-touch-icon"]')) {
                const a = document.createElement('link');
                a.rel = 'apple-touch-icon';
                a.href = new URL('icons/icon-192.png', root).href;
                document.head.appendChild(a);
            }
        }
    } catch (e) { }
})();

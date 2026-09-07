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
            '#theme-toggle:hover{transform:scale(1.1);}'
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

/* theme/script.js */
(function () {
    console.log('Theme script loading...');

    // Smarter DP check: look for 'dp' as a directory segment
    const pathSegments = window.location.pathname.split(/[/\\]/);
    const isDP = pathSegments.includes('dp');

    console.log('Is DP page:', isDP, 'Path:', window.location.pathname);

    function applyTheme(theme) {
        console.log('Applying theme:', theme);
        if (isDP) {
            console.log('Force Light Mode for DP');
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            return;
        }

        document.body.classList.remove('light-mode', 'dark-mode');
        document.body.classList.add(theme + '-mode');

        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.innerHTML = theme === 'light' ? '🌙' : '☀️';
            // Debug styling
            toggle.style.border = '2px solid red';
        }
    }

    function init() {
        console.log('Theme script init started');
        let savedTheme = null;

        try {
            savedTheme = localStorage.getItem('theme');
            console.log('LocalStorage theme:', savedTheme);
        } catch (e) {
            console.error('LocalStorage access failed:', e);
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
            console.log('Using default theme based on path:', savedTheme);
        }

        applyTheme(savedTheme);

        if (!isDP) {
            if (!document.getElementById('theme-toggle')) {
                console.log('Creating theme-toggle button');
                const toggle = document.createElement('div');
                toggle.id = 'theme-toggle';
                toggle.setAttribute('aria-label', 'テーマ切り替え');
                toggle.innerHTML = savedTheme === 'light' ? '🌙' : '☀️';
                // Inline styles for absolute certainty
                Object.assign(toggle.style, {
                    position: 'fixed',
                    top: '20px',
                    right: '20px',
                    zIndex: '10000',
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    fontSize: '24px',
                    border: '2px solid red', // DEBUG BORDER
                    background: 'white',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.5)'
                });

                document.body.appendChild(toggle);
                console.log('Button appended to body');

                toggle.addEventListener('click', () => {
                    const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    console.log('Switching to:', newTheme);
                    try {
                        localStorage.setItem('theme', newTheme);
                    } catch (e) { }
                    applyTheme(newTheme);
                });
            } else {
                console.log('Button already exists');
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

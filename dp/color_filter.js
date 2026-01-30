/**
 * DPページ用色別フィルター機能
 */
(function () {
    'use strict';

    // 色の定義
    const COLORS = {
        pink: { hex: '#FCD2E7', label: 'ピンク', bg: '#FCD2E7' },
        blue: { hex: '#CCFFFF', label: '青', bg: '#CCFFFF' },
        yellow: { hex: '#FFFF99', label: '黄色', bg: '#FFFF99' },
        white: { hex: 'none', label: '白', bg: '#FFFFFF' }
    };

    const STORAGE_KEY = 'dp_color_filter_state';

    let filterState = {
        pink: true,
        blue: true,
        yellow: true,
        white: true
    };

    /**
     * LocalStorageから状態を読み込み
     */
    function loadFilterState() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                filterState = { ...filterState, ...JSON.parse(saved) };
            }
        } catch (e) {
            console.warn('Failed to load filter state:', e);
        }
    }

    /**
     * LocalStorageに状態を保存
     */
    function saveFilterState() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(filterState));
        } catch (e) {
            console.warn('Failed to save filter state:', e);
        }
    }

    /**
     * 要素が保護対象（常に表示、改変禁止）かどうかを判定
     */
    function isProtected(element) {
        if (!element || !element.tagName) return false;

        // タグ名による保護（ナビゲーションに関わる構造タグ）
        const tag = element.tagName.toUpperCase();
        if (['NAV', 'HEADER', 'FOOTER', 'SCRIPT', 'STYLE', 'BUTTON'].includes(tag)) {
            return true;
        }

        // 重要：見出し（H1-H6）内にある要素（自己リンクなど）は常に保護
        if (element.closest('h1, h2, h3, h4, h5, h6')) {
            return true;
        }

        // ナビゲーションUI、目次、誤植フォーム等は保護
        // ただし .color-filter-text-unit は除外（自分自身を保護しないため）
        if (element.classList.contains('color-filter-text-unit')) {
            return false;
        }

        if (element.closest('.page-nav, .toc-collapsible, .color-filter-container, #typo-report, #toc, .nav-btn, .footer')) {
            return true;
        }

        return false;
    }

    /**
     * 見出し要素かどうか
     */
    function isHeading(element) {
        if (!element || !element.tagName) return false;
        if (/^H[1-6]$/i.test(element.tagName)) return true;
        // IDがある要素も見出しとするが、自ら作成したユニットは除く
        if (element.hasAttribute('id') && !element.classList.contains('color-filter-text-unit')) return true;
        return false;
    }

    /**
     * RGB文字列をHEXに変換
     */
    function rgbToHex(color) {
        const rgb = color.match(/\d+/g);
        if (rgb && rgb.length >= 3) {
            const hex = "#" + rgb.slice(0, 3).map(x => {
                const h = parseInt(x).toString(16);
                return h.length === 1 ? "0" + h : h;
            }).join("");
            return hex.toUpperCase();
        }
        return null;
    }

    /**
     * 要素の背景色を取得
     */
    function getBackgroundColor(element) {
        if (!element) return 'none';

        let color = '';

        // 【優先1】getAttribute('style')から直接解析
        if (element.getAttribute) {
            const styleAttr = element.getAttribute('style');
            if (styleAttr) {
                const bgColorMatch = styleAttr.match(/background-color\s*:\s*(#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3}|rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\))/i);
                if (bgColorMatch) {
                    color = bgColorMatch[1];
                } else {
                    const bgMatch = styleAttr.match(/background\s*:\s*(#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3})/i);
                    if (bgMatch) {
                        color = bgMatch[1];
                    }
                }
            }
        }

        // 【優先2】element.style.backgroundColor
        if (!color && element.style && element.style.backgroundColor) {
            color = element.style.backgroundColor;
        }

        // 【優先3】getComputedStyle
        if (!color && window.getComputedStyle) {
            try {
                const style = window.getComputedStyle(element);
                if (style && style.backgroundColor) {
                    color = style.backgroundColor;
                }
            } catch (e) {
                // エラーは無視
            }
        }

        // 透明・未設定の場合は 'none'
        if (!color || color === 'transparent' || color === 'rgba(0, 0, 0, 0)' || color === 'initial' || color === 'inherit') {
            return 'none';
        }

        // RGB形式をHEXに変換
        if (color.startsWith('rgb')) {
            const hex = rgbToHex(color);
            if (hex) return hex;
        }

        // HEX形式はそのまま大文字で返す
        if (color.startsWith('#')) return color.toUpperCase();

        return color;
    }

    /**
     * 要素がインラインで背景色を持っているかチェック（高速版）
     */
    function hasInlineBackgroundColor(element) {
        if (!element || !element.getAttribute) return false;
        const styleAttr = element.getAttribute('style');
        return styleAttr && /background(-color)?\s*:\s*#[A-Fa-f0-9]{3,6}/i.test(styleAttr);
    }

    /**
     * テキストノードをスパンで囲む（本文エリアのみを対象）
     */
    function wrapTextNodes(root) {
        if (!root || isProtected(root)) return;

        // 【重要】root自身が背景色付きSPANの場合は、即座にユニット化して終了
        // 12daraku.htmlなどで、コンテナの直下にSPANが来ている場合に対応
        if (root.tagName === 'SPAN' && !root.classList.contains('color-filter-text-unit') && hasInlineBackgroundColor(root)) {
            root.classList.add('color-filter-text-unit');
            return;
        }

        const nodes = Array.from(root.childNodes);
        nodes.forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent.trim();
                if (text) {
                    const span = document.createElement('span');
                    span.className = 'color-filter-text-unit';
                    span.textContent = node.textContent;
                    node.parentNode.replaceChild(span, node);
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toUpperCase();

                // 【重要】SPANで背景色がある場合は、即座にユニット化して再帰を停止
                if (tagName === 'SPAN' && !isProtected(node) && hasInlineBackgroundColor(node)) {
                    node.classList.add('color-filter-text-unit');
                    return; // 子要素を処理せずに終了（rubyタグなどが別ユニット化されるのを防ぐ）
                }

                // リンクや背景色なしスパンの処理
                if ((tagName === 'A' || tagName === 'SPAN') && !isProtected(node)) {
                    node.classList.add('color-filter-text-unit');
                    if (tagName === 'A') return; // リンクは子要素を処理しない
                    // 背景色なしスパンは再帰処理を続ける
                }

                // 更に深く探索
                if (!isProtected(node) && !isHeading(node)) {
                    wrapTextNodes(node);
                }
            }
        });
    }

    /**
     * 背景色からカラーキーを取得
     */
    function getColorKey(bgColor) {
        const hex = (bgColor || '').toUpperCase();

        // ピンク系
        if (hex === '#FCD2E7' || hex === '#D1AFBF') return 'pink';

        // 青系
        if (hex === '#CCFFFF' || hex === '#AACCFF' || hex === '#CFF' || hex === '#CCF') return 'blue';

        // 黄色系
        if (hex === '#FFFF99' || hex === '#E6E68A' || hex === '#FF9' || hex === '#FE9') return 'yellow';

        // 白・透明・未設定
        if (hex === '#FFFFFF' || hex === '#FFF' || hex === 'NONE' || hex === 'TRANSPARENT' ||
            hex === 'RGBA(0, 0, 0, 0)' || hex === '' || bgColor === 'none') {
            return 'white';
        }

        // 認識できない色の場合は警告を出す（デバッグ用）
        console.warn('[Color Filter Debug] Unknown color:', bgColor, '-> defaulting to white');
        return 'white';
    }

    /**
     * フィルタリングを適用
     */
    function applyFilter() {
        // 1. 各テキスト単位の表示/非表示を切り替え
        const textUnits = document.querySelectorAll('.color-filter-text-unit');
        let debugCount = 0;
        textUnits.forEach(el => {
            const bgColor = getBackgroundColor(el);
            const key = getColorKey(bgColor);
            el.style.display = filterState[key] ? '' : 'none';

            // デバッグ: 最初の10要素のみログ出力
            if (debugCount < 10 && bgColor && bgColor !== 'none') {
                console.log(`[Filter Debug ${debugCount}]`, {
                    element: el.tagName,
                    text: el.textContent.substring(0, 30) + '...',
                    bgColor: bgColor,
                    key: key,
                    display: el.style.display
                });
                debugCount++;
            }
        });

        // 2. 段落などのブロック要素の制御（空になったら隠す）
        const blocks = document.querySelectorAll('p, li, blockquote, div.no1');
        blocks.forEach(block => {
            if (isProtected(block) || isHeading(block)) {
                block.style.display = '';
                return;
            }

            if (block.querySelector('h1, h2, h3, h4, h5, h6')) {
                block.style.display = '';
                return;
            }

            const units = block.querySelectorAll('.color-filter-text-unit');
            if (units.length === 0) {
                if (block.classList.contains('color-filter-text-unit')) {
                    const key = getColorKey(getBackgroundColor(block));
                    block.style.display = filterState[key] ? '' : 'none';
                    return;
                }
                block.style.display = '';
                return;
            }

            const hasVisible = Array.from(units).some(u => u.style.display !== 'none');
            block.style.display = hasVisible ? '' : 'none';
        });

        // 3. コンテナやセクションカードなどの大きな要素の制御
        const containers = document.querySelectorAll('.content-card, .section-card, .content-section, article, main');
        containers.forEach(container => {
            if (container.querySelector('h1, h2, h3, h4, h5, h6, [id]:not(.color-filter-text-unit)')) {
                container.style.display = '';
                return;
            }

            const hasVisibleContent = Array.from(container.querySelectorAll('p, li, blockquote, div.no1')).some(b => b.style.display !== 'none');
            const hasDirectVisibleUnits = Array.from(container.children).some(c => c.classList.contains('color-filter-text-unit') && c.style.display !== 'none');

            if (container.querySelectorAll('p, li, div.no1').length > 0) {
                container.style.display = (hasVisibleContent || hasDirectVisibleUnits) ? '' : 'none';
            }
        });
    }

    /**
     * ボタンのUIを更新
     */
    function updateButtonUI(button, colorKey) {
        const span = button.querySelector('.toggle-status');
        if (filterState[colorKey]) {
            button.classList.add('active');
            button.setAttribute('aria-pressed', 'true');
            if (span) span.textContent = 'ON';
        } else {
            button.classList.remove('active');
            button.setAttribute('aria-pressed', 'false');
            if (span) span.textContent = 'OFF';
        }
    }

    /**
     * フィルターボタンを作成
     */
    function createFilterButtons() {
        if (document.querySelector('.color-filter-container')) return null;

        const container = document.createElement('div');
        container.className = 'color-filter-container';

        const label = document.createElement('span');
        label.className = 'filter-label';
        label.textContent = '表示：';
        container.appendChild(label);

        const buttonsWrapper = document.createElement('div');
        buttonsWrapper.className = 'filter-buttons';

        Object.entries(COLORS).forEach(([key, config]) => {
            const button = document.createElement('button');
            button.className = 'filter-btn';
            button.innerHTML = `
                <span class="color-swatch" style="background-color: ${config.bg}${key === 'white' ? '; border: 1px solid #ccc' : ''}"></span>
                <span class="color-label">${config.label}</span>
                <span class="toggle-status"></span>
            `;

            button.addEventListener('click', () => {
                filterState[key] = !filterState[key];
                updateButtonUI(button, key);
                saveFilterState();
                applyFilter();
            });

            updateButtonUI(button, key);
            buttonsWrapper.appendChild(button);
        });

        container.appendChild(buttonsWrapper);
        return container;
    }

    /**
     * スタイルを注入
     */
    function injectStyles() {
        if (document.getElementById('color-filter-styles')) return;
        const style = document.createElement('style');
        style.id = 'color-filter-styles';
        style.textContent = `
            .color-filter-container {
                margin: 1.5rem auto;
                padding: 0.8rem 1.2rem;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                display: flex;
                align-items: center;
                gap: 1rem;
                flex-wrap: wrap;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                max-width: fit-content;
                clear: both;
            }
            .filter-label { font-weight: bold; font-size: 0.95rem; color: #555; }
            .filter-buttons { display: flex; gap: 0.6rem; flex-wrap: wrap; }
            .filter-btn {
                display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.8rem;
                border: 1px solid #ddd; border-radius: 50px; background: #f5f5f5;
                cursor: pointer; transition: all 0.2s; font-family: inherit;
                font-size: 0.85rem; color: #666;
            }
            .filter-btn.active { background: #fff; border-color: #4a90e2; color: #333; }
            .color-swatch { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
            .toggle-status {
                background: #bbb; color: white; font-size: 0.65rem; font-weight: bold;
                padding: 1px 5px; border-radius: 8px; min-width: 22px; text-align: center;
            }
            .filter-btn.active .toggle-status { background: #4a90e2; }

            .color-filter-text-unit {
                display: initial;
                background-color: inherit;
            }

            @media (max-width: 600px) {
                .color-filter-container { padding: 0.6rem; gap: 0.5rem; justify-content: center; }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * 初期化
     */
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        injectStyles();
        loadFilterState();

        const toc = document.querySelector('.toc-collapsible, #toc');
        const typoReport = document.querySelector('#typo-report');

        console.log('[Color Filter] Initializing...', { toc: !!toc, typoReport: !!typoReport });

        if (toc && typoReport) {
            let current = toc.nextSibling;
            const nodesToProcess = [];

            while (current && current !== typoReport) {
                nodesToProcess.push(current);
                current = current.nextSibling;
            }

            console.log(`[Color Filter] Processing ${nodesToProcess.length} nodes between TOC and typo report`);
            nodesToProcess.forEach(node => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    wrapTextNodes(node);
                } else if (node.nodeType === Node.TEXT_NODE) {
                    const text = node.textContent.trim();
                    if (text) {
                        const span = document.createElement('span');
                        span.className = 'color-filter-text-unit';
                        span.textContent = node.textContent;
                        node.parentNode.replaceChild(span, node);
                    }
                }
            });
        } else {
            console.log('[Color Filter] Fallback: Processing content areas');
            const contentAreas = document.querySelectorAll('.content-card, .section-card, .content-section, article, main');
            console.log(`[Color Filter] Found ${contentAreas.length} content areas`);
            contentAreas.forEach(area => wrapTextNodes(area));
        }

        const totalUnits = document.querySelectorAll('.color-filter-text-unit').length;
        console.log(`[Color Filter] Total text units created: ${totalUnits}`);

        const nav = document.querySelector('.page-nav');
        if (nav) {
            const filterContainer = createFilterButtons();
            if (filterContainer) {
                nav.parentNode.insertBefore(filterContainer, nav.nextSibling);
            }
        }

        applyFilter();
    }

    init();
})();

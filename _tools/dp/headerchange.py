import os
import re
from bs4 import BeautifulSoup

def repair_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Processing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 異常な閉じタグの暴走をストップ (</a></a></a>... を 1つに整理)
    html = re.sub(r'(</a>\s*){2,}', '</a>\n', html)

    soup = BeautifulSoup(html, 'html.parser')

    # 2. <a>の中に<h>が入っている「逆転現象」を正常化
    # (例: <a href...><h3...>...</h3></a> を <h3...><a href...>...</a></h3> に直す)
    for a_tag in soup.find_all('a'):
        h_tag = a_tag.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if h_tag:
            new_h = soup.new_tag(h_tag.name, **h_tag.attrs)
            new_a = soup.new_tag('a', **a_tag.attrs)
            new_a.extend(h_tag.contents)
            new_h.append(new_a)
            a_tag.replace_with(new_h)

    # 3. 古いコンテナを一度削除し、クリーンなものをbody先頭に再配置
    for el in soup.find_all(id='stacked-header-container'):
        el.decompose()

    header_html = """
    <div id="stacked-header-container" class="stacked-header-container">
        <div id="breadcrumb-view" class="breadcrumb-view"></div>
        <div id="stacked-view" class="stacked-view"></div>
    </div>
    """
    if soup.body:
        soup.body.insert(0, BeautifulSoup(header_html, 'html.parser'))

    # 4. 古いヘッダー用JavaScriptを削除（重複防止）
    for script in soup.find_all('script'):
        if script.string and 'stacked-header-container' in script.string:
            script.decompose()

    # 5. 最新の安定版JS（クリック展開対応）をbody末尾に挿入
    js_code = r"""
    document.addEventListener('DOMContentLoaded', () => {
        const container = document.getElementById('stacked-header-container');
        const breadcrumb = document.getElementById('breadcrumb-view');
        const stackedView = document.getElementById('stacked-view');
        
        if (!container || !breadcrumb || !stackedView) return;

        const headings = Array.from(document.querySelectorAll('h1:not(.page-title), h2, h3, h4, h5, h6'));
        const bars = {};

        stackedView.innerHTML = ''; // 初期化

        for (let i = 1; i <= 6; i++) {
            const bar = document.createElement('div');
            bar.className = 'stack-bar';
            bar.dataset.level = i;
            bar.innerHTML = '<span></span>';
            stackedView.appendChild(bar);
            bars[i] = { el: bar, text: bar.querySelector('span'), activeHeading: null };

            // 展開されたバーをクリックしたときのスクロール処理
            bar.addEventListener('click', (e) => {
                e.stopPropagation();
                if (bars[i].activeHeading) {
                    const offset = 80;
                    const bodyRect = document.body.getBoundingClientRect().top;
                    const elementRect = bars[i].activeHeading.getBoundingClientRect().top;
                    const offsetPosition = (elementRect - bodyRect) - offset;
                    window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
                    container.classList.remove('is-expanded');
                }
            });
        }

        // パンくずリストをクリックしたときの展開処理
        breadcrumb.addEventListener('click', (e) => {
            e.stopPropagation();
            container.classList.toggle('is-expanded');
        });

        // 画面の他をクリックしたら閉じる
        document.addEventListener('click', () => {
            container.classList.remove('is-expanded');
        });

        const getCleanText = (el) => {
            const clone = el.cloneNode(true);
            clone.querySelectorAll('rt, rp').forEach(r => r.remove());
            return (clone.textContent || clone.innerText || '').replace(/[◆▸▶]/g, '').trim();
        };

        const updateHeader = () => {
            const threshold = 120;
            let current = null;
            for (let i = headings.length - 1; i >= 0; i--) {
                if (headings[i].getBoundingClientRect().top <= threshold) {
                    current = headings[i];
                    break;
                }
            }

            if (window.scrollY < 200 || !current) {
                breadcrumb.classList.remove('visible');
                container.classList.remove('is-expanded');
                return;
            }

            breadcrumb.classList.add('visible');
            const path = [];
            let temp = current;
            let tempLevel = parseInt(temp.tagName.substring(1));
            path.unshift({ heading: temp, level: tempLevel });

            let currentIndex = headings.indexOf(temp);
            for (let i = currentIndex - 1; i >= 0; i--) {
                let level = parseInt(headings[i].tagName.substring(1));
                if (level < tempLevel) {
                    path.unshift({ heading: headings[i], level: level });
                    tempLevel = level;
                }
            }

            const breadcrumbText = path.map(p => getCleanText(p.heading)).join('<span class="separator">/</span>');
            if (breadcrumb.innerHTML !== breadcrumbText) breadcrumb.innerHTML = breadcrumbText;

            for (let i = 1; i <= 6; i++) {
                const barData = bars[i];
                const pathItem = path.find(p => p.level === i);
                if (pathItem) {
                    barData.el.style.display = 'flex';
                    barData.activeHeading = pathItem.heading;
                    const cleanText = getCleanText(pathItem.heading);
                    if (barData.text.textContent !== cleanText) barData.text.textContent = cleanText;
                } else {
                    barData.el.style.display = 'none';
                    barData.activeHeading = null;
                }
            }
        };

        const observer = new IntersectionObserver(() => updateHeader(), { rootMargin: '-5% 0px -90% 0px' });
        headings.forEach(h => observer.observe(h));
        window.addEventListener('scroll', updateHeader, { passive: true });
        updateHeader();
    });
    """
    new_script = soup.new_tag('script')
    new_script.string = js_code
    if soup.body:
        soup.body.append(new_script)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"✅ 修復完了: {file_path}")

def main():
    target_dir = r"C:\malsum\mimune-no-uraniwa\dp"
    target_files = ['11sozo.html', '12daraku.html']
    
    for filename in target_files:
        file_path = os.path.join(target_dir, filename)
        repair_file(file_path)

if __name__ == '__main__':
    main()
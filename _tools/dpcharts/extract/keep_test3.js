// 「表示：」の図のボタン（charts.js の keepPlace）で出し入れしたとき、画面の上の字が同じ高さに残るか。
// 字は「本文の何字目か」で覚える（図の差し込みで字のノードが割れても追える）
(async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const SKIP = 'rt,rp,script,style,nav,.toc-collapsible,#toc,.page-nav,#typo-report,#stacked-header-container,.color-filter-container,.dpc-fig,.dpc-note,#reader-ui,#reader-drawer';
  const chars = () => {
    const out = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n => { const p = n.parentElement; return (!p || p.closest(SKIP)) ? 2 : 1; } });
    let n;
    while ((n = w.nextNode())) for (let i = 0; i < n.nodeValue.length; i++) if (!/\s/.test(n.nodeValue[i])) out.push([n, i]);
    return out;
  };
  const topOf = ([n, i]) => { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const rs = r.getClientRects(); return rs.length ? Math.round(rs[0].top) : null; };
  const btn = document.querySelector('.color-filter-container .dpc-btn');
  const out = [];
  for (const y of [5000, 9000, 14000, 20000, 30000]) {
    if (dpCharts.isOn()) { btn.click(); await sleep(400); }
    window.scrollTo(0, y); await sleep(300);
    const r = document.caretRangeFromPoint(innerWidth / 2, 100);
    if (!r || r.startContainer.nodeType !== 3) { out.push({ y, skip: true }); continue; }
    const cs = chars();
    let k = cs.findIndex(([n, i]) => n === r.startContainer && i >= r.startOffset);
    if (k < 0) { out.push({ y, skip: 'k' }); continue; }
    const t0 = topOf(cs[k]);
    btn.click(); await sleep(600);
    const t1 = topOf(chars()[k]);
    btn.click(); await sleep(400);
    const t2 = topOf(chars()[k]);
    out.push({ y, ch: cs[k][0].nodeValue.slice(cs[k][1], cs[k][1] + 6), t0, on: t1, off: t2 });
  }
  return out;
})()

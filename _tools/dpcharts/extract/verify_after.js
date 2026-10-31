(async () => {
  const d = await (await fetch(document.querySelector('script[data-charts]').getAttribute('data-charts').replace(/^/, '/dp/'))).json();
  const want = Object.fromEntries(d.charts.map(c => [c.id, c.after]));
  const SKIP = 'rt,rp,script,style,nav,.toc-collapsible,#toc,.page-nav,#typo-report,#stacked-header-container,.color-filter-container,.dpc-fig,.dpc-note,#reader-ui,#reader-drawer';
  // 図の直前の本文（空白を除く）を、文書の頭から図までの字で作る
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
    acceptNode: n => {
      if (n.nodeType === 1) return n.classList && n.classList.contains('dpc-fig') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      const p = n.parentElement; return (!p || p.closest(SKIP)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
    }
  });
  let buf = '', n, ok = 0, bad = [], mid = 0, order = [];
  while ((n = w.nextNode())) {
    if (n.nodeType === 1) {
      const id = n.dataset.id; order.push(id);
      if (buf.endsWith(want[id])) ok++; else bad.push(id + ':' + buf.slice(-12));
      // 図のすぐ後ろが段落の途中か（次の字のノードが同じブロックの中で続くか）
      let nx = n.nextSibling; while (nx && nx.nodeType === 3 && !nx.nodeValue.trim()) nx = nx.nextSibling;
      if (nx && !(nx.nodeName === 'BR' || (nx.classList && nx.classList.contains('dpc-fig')))) mid++;
      continue;
    }
    buf += n.nodeValue.replace(/\s/g, '');
  }
  const inHl = [...document.querySelectorAll('.dpc-fig')].filter(f => f.parentElement.closest('[style*=background-color]')).length;
  return { figures: order.length, endsRight: ok, bad, midParagraph: mid, insideHighlight: inHl, first6: order.slice(0, 6).join(' ') };
})()

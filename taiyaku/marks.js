// 対訳ビューアで、本文の字を選んで自分のマーカーを引く（2026-11-25）。
// 本文ページの reader.js の userMarks と同じ見た目・同じ動き。対訳は欄（言語 × 段落）ごとに
// 描き直されるので、位置は「節のキー・言語・段落・欄の中の何文字目か」で覚える。
// ビューアの paint() が描き終えたら "taiyaku:paint"（detail.key = 節のキー）を投げ、ここで塗る。
// 欄をまたいで選んだときは、欄ごとに1本ずつ引く。端末のブラウザにだけ残る。
(function () {
  "use strict";
  const COLORS = [["y", "黄"], ["g", "緑"], ["b", "青"], ["p", "桃"]];
  // 数えない字: 言語の札・空の印・注・英語版の書き換えの箱・ルビ・ボタン
  const SKIP = ".tag,.empty,.cnote,.wbox,.jobadge,.mvtag,rt,rp,button,script,style";
  const KEY = "taiyaku.hl." + location.pathname.replace(/[^/]*$/, "");
  let all = read();          // { 節のキー: [{ l, r, a, b, c, t, at }] }
  let key = null;            // いま出している節
  let bar, sel = null, edit = null, hold = false, timer = 0;

  function read() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY) || "{}");
      return v && typeof v === "object" && !Array.isArray(v) ? v : {};
    } catch { return {}; }
  }
  function write() {
    Object.keys(all).forEach((k) => { if (!all[k].length) delete all[k]; });
    try {
      if (Object.keys(all).length) localStorage.setItem(KEY, JSON.stringify(all));
      else localStorage.removeItem(KEY);
    } catch {}
  }
  const list = () => (key ? (all[key] = all[key] || []) : []);

  // 欄の中の数える字のノードと、それぞれの頭の位置
  function nodesOf(cell) {
    const out = [];
    let p = 0;
    const w = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    for (let n; (n = w.nextNode()); p += n.nodeValue.length) out.push({ n, p });
    return out;
  }
  const fullText = (ns) => ns.map((x) => x.n.nodeValue).join("");
  const cellOf = (l, r) => document.querySelector(`#body .cell[lang="${l}"][data-r="${r}"]`);

  function clear() {
    const ps = new Set();
    document.querySelectorAll("#body mark.tk-hl").forEach((mk) => {
      const p = mk.parentNode;
      while (mk.firstChild) p.insertBefore(mk.firstChild, mk);
      p.removeChild(mk);
      ps.add(p);
    });
    ps.forEach((p) => p.normalize());
  }

  // 覚えた字が位置からずれていたら（字の直しなど）、同じ欄でいちばん近い所を探し直す
  function relocate(m, text) {
    if (text.slice(m.a, m.b) === m.t) return true;
    let best = -1;
    for (let k = text.indexOf(m.t); k >= 0; k = text.indexOf(m.t, k + 1))
      if (best < 0 || Math.abs(k - m.a) < Math.abs(best - m.a)) best = k;
    if (best < 0) return false;            // 見つからないものは消さずに残す（塗らない）
    m.b = best + m.t.length; m.a = best;
    return true;
  }

  function paint() {
    clear();
    const ms = list();
    // 後ろから包むと、前のマーカーが使うノードの位置は変わらない
    const order = ms.map((m, i) => i).sort((x, y) => ms[y].a - ms[x].a);
    const cache = new Map();
    order.forEach((i) => {
      const m = ms[i];
      const cell = cellOf(m.l, m.r);
      if (!cell) return;                    // その言語を隠している
      if (!cache.has(cell)) cache.set(cell, fullText(nodesOf(cell)));
      if (!relocate(m, cache.get(cell))) return;
      nodesOf(cell).forEach(({ n, p }) => {
        const s = Math.max(0, m.a - p), e = Math.min(n.nodeValue.length, m.b - p);
        if (e <= s) return;
        if (e < n.nodeValue.length) n.splitText(e);
        const x = s > 0 ? n.splitText(s) : n;
        const mk = document.createElement("mark");
        mk.className = "tk-hl hl-" + m.c;
        mk.dataset.k = i;
        x.parentNode.insertBefore(mk, x);
        mk.appendChild(x);
      });
    });
  }

  // 選んだ範囲 → 欄ごとの [a, b)。前後の空白は外す
  function picked() {
    const s = window.getSelection();
    if (!s || s.isCollapsed || !s.rangeCount || !key) return null;
    const rg = s.getRangeAt(0);
    const body = document.getElementById("body");
    if (!body || !rg.intersectsNode(body)) return null;
    const out = [];
    body.querySelectorAll(".cell").forEach((cell) => {
      if (!rg.intersectsNode(cell)) return;
      const ns = nodesOf(cell);
      let a = -1, b = -1;
      ns.forEach(({ n, p }) => {
        if (!rg.intersectsNode(n)) return;
        const s0 = n === rg.startContainer ? rg.startOffset : 0;
        const e0 = n === rg.endContainer ? rg.endOffset : n.nodeValue.length;
        if (e0 <= s0) return;
        if (a < 0) a = p + s0;
        b = p + e0;
      });
      if (a < 0) return;
      const text = fullText(ns), t = text.slice(a, b);
      a += t.length - t.replace(/^\s+/, "").length;
      b -= t.length - t.replace(/\s+$/, "").length;
      if (b > a) out.push({ l: cell.lang, r: cell.dataset.r, a, b, text });
    });
    return out.length ? out : null;
  }

  const same = (m, x) => m.l === x.l && String(m.r) === String(x.r);
  function overlaps(xs) {
    return xs.some((x) => list().some((m) => same(m, x) && m.a < x.b && m.b > x.a));
  }
  // 欄 x の [a, b) に重なっている所を削る（はみ出した所は残す）
  function cut(x, text) {
    const ms = list(), out = [];
    ms.forEach((m) => {
      if (!same(m, x) || m.b <= x.a || m.a >= x.b) { out.push(m); return; }
      if (m.a < x.a) out.push({ ...m, b: x.a, t: text.slice(m.a, x.a) });
      if (m.b > x.b) out.push({ ...m, a: x.b, t: text.slice(x.b, m.b) });
    });
    all[key] = out.filter((m) => m.t.replace(/\s/g, ""));
  }
  function add(x, c, text) {
    let a = x.a, b = x.b;
    // 同じ色で重なる・接するマーカーは1本にまとめる
    list().forEach((m) => { if (same(m, x) && m.c === c && m.a <= b && m.b >= a) { a = Math.min(a, m.a); b = Math.max(b, m.b); } });
    cut({ ...x, a, b }, text);
    list().push({ l: x.l, r: x.r, a, b, c, t: text.slice(a, b), at: Date.now() });
    list().sort((p, q) => (p.l + p.r).localeCompare(q.l + q.r) || p.a - q.a);
  }

  function pick(c) {
    let xs = sel;
    if (edit) {
      const cell = cellOf(edit.l, edit.r);
      xs = cell ? [{ ...edit, text: fullText(nodesOf(cell)) }] : null;
    }
    if (!xs) return;
    xs.forEach((x) => (c ? add(x, c, x.text) : cut(x, x.text)));
    write();
    paint();
    try { window.getSelection().removeAllRanges(); } catch {}
    hide();
  }

  // 選んだ字がかかる段落の、ほかの言語の本文。対訳は段落（行）ごとに組なので、文ごとには取れない
  const TAGS = { ko: "韓", ja: "日", en: "英" };
  function otherText(l) {
    const rows = [...new Set(sel.map((x) => String(x.r)))];
    return rows.map((r) => { const c = cellOf(l, r); return c ? fullText(nodesOf(c)).trim() : ""; })
      .filter(Boolean).join("\n\n");
  }
  function copy(text) {
    const done = () => {
      // 帯のすぐ上に出す（帯が折り返して高くなっても重ならない）
      if (bar.classList.contains("on")) note.style.bottom = (innerHeight - bar.getBoundingClientRect().top + 8) + "px";
      else note.style.bottom = "";
      note.textContent = "コピーしました"; note.classList.add("on"); setTimeout(() => note.classList.remove("on"), 1400); };
    const byExec = () => {
      const ta = document.createElement("textarea");
      ta.value = text; ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch {}
      ta.remove();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, byExec);
    else byExec();
  }
  let note;

  function show(mode) {
    bar.dataset.mode = mode;
    const mine = new Set((mode === "sel" ? sel : []).map((x) => x.l));
    bar.querySelectorAll("button[data-copy]").forEach((o) => {
      const l = o.dataset.copy;
      o.style.display = mode === "sel" && !mine.has(l) && sel.some((x) => cellOf(l, x.r)) ? "" : "none";
    });
    const on = mode === "edit" ? edit.c : "";
    bar.querySelectorAll("button[data-c]").forEach((o) => o.setAttribute("aria-pressed", String(o.dataset.c === on)));
    bar.querySelector(".x").style.display = mode === "edit" || (sel && overlaps(sel)) ? "" : "none";
    bar.classList.add("on");
  }
  function hide() { bar.classList.remove("on"); sel = null; edit = null; }

  function css() {
    const s = document.createElement("style");
    s.textContent = [
      "mark.tk-hl{color:inherit;padding:0;border-radius:2px;background:linear-gradient(transparent 52%,var(--hl) 52%);",
      "-webkit-box-decoration-break:clone;box-decoration-break:clone;cursor:pointer}",
      ".hl-y{--hl:rgba(250,204,21,.6)}.hl-g{--hl:rgba(74,222,128,.55)}.hl-b{--hl:rgba(96,165,250,.55)}.hl-p{--hl:rgba(244,114,182,.55)}",
      'html[data-theme="dark"] .hl-y{--hl:rgba(250,204,21,.5)}html[data-theme="dark"] .hl-g{--hl:rgba(74,222,128,.45)}',
      'html[data-theme="dark"] .hl-b{--hl:rgba(96,165,250,.5)}html[data-theme="dark"] .hl-p{--hl:rgba(244,114,182,.5)}',
      "#tk-hl{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(1.4rem + env(safe-area-inset-bottom,0px));",
      "z-index:10003;display:none;align-items:center;justify-content:center;flex-wrap:wrap;gap:.4rem;padding:.4rem .55rem;border-radius:1.4rem;",
      "width:max-content;max-width:calc(100vw - 16px);box-sizing:border-box;",
      "background:rgba(30,30,40,.94);color:#fff;box-shadow:0 4px 18px rgba(0,0,0,.3);font-size:15px;",
      "-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}",
      "#tk-hl.on{display:flex}",
      "#tk-hl span{opacity:.75;padding:0 .2rem 0 .3rem;white-space:nowrap}",
      "#tk-hl button{font:inherit;border:0;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      "#tk-hl button[data-c]{width:2.1rem;height:2.1rem;border-radius:50%;border:2px solid rgba(255,255,255,.25);color:#222;font-weight:700;font-size:13px}",
      '#tk-hl button[data-c="y"]{background:#facc15}#tk-hl button[data-c="g"]{background:#4ade80}',
      '#tk-hl button[data-c="b"]{background:#60a5fa}#tk-hl button[data-c="p"]{background:#f472b6}',
      '#tk-hl button[aria-pressed="true"]{border-color:#fff;box-shadow:0 0 0 2px rgba(255,255,255,.5)}',
      "#tk-hl .cp{background:rgba(255,255,255,.1);color:#fff;border-radius:999px;padding:.45em .7em;white-space:nowrap;border-left:1px solid rgba(255,255,255,.2)}",
      "#tk-hl-note{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(5rem + env(safe-area-inset-bottom,0px));z-index:10004;",
      "background:rgba(30,30,40,.94);color:#fff;padding:.4em 1em;border-radius:999px;font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none}",
      "#tk-hl-note.on{opacity:1}",
      ".cell .tag .cp1{font:inherit;font-size:12px;letter-spacing:0;background:none;border:0;padding:2px 6px;margin-left:4px;",
      "opacity:.45;cursor:pointer;vertical-align:-1px;-webkit-tap-highlight-color:transparent}",
      ".cell .tag .cp1:hover,.cell .tag .cp1:focus-visible{opacity:1}",
      "@media print{.cell .tag .cp1{display:none}}",
      "#tk-hl .x{background:rgba(255,255,255,.16);color:#fff;border-radius:999px;padding:.45em .9em;white-space:nowrap}",
      // スマホは下の端に Safari の帯などが重なるので、少し上に出す
      "@media (pointer:coarse){#tk-hl{bottom:calc(4.6rem + env(safe-area-inset-bottom,0px))}}",
      "@media print{#tk-hl{display:none !important}mark.tk-hl{background:none}}",
    ].join("");
    document.head.appendChild(s);
  }

  function start() {
    css();
    bar = document.createElement("div");
    bar.id = "tk-hl";
    bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", "マーカー");
    bar.innerHTML = "<span>🖍</span>" + COLORS.map(([c, n]) =>
      `<button type="button" data-c="${c}" aria-label="${n}のマーカー">${n}</button>`).join("")
      + '<button type="button" class="x">消す</button>'
      + Object.entries(TAGS).map(([l, n]) =>
        `<button type="button" class="cp" data-copy="${l}" title="選んだ所の段落の${n}をコピー" aria-label="選んだ所の段落の${n}をコピー">📋${n}</button>`).join("");
    document.body.appendChild(bar);
    note = document.createElement("div");
    note.id = "tk-hl-note";
    document.body.appendChild(note);
    // 押した瞬間に選択が外れて帯が引っ込まないように、押している間は隠さない
    bar.addEventListener("pointerdown", (e) => { e.preventDefault(); hold = true; });
    bar.addEventListener("pointercancel", () => { hold = false; });
    bar.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      hold = false;
      if (b && b.dataset.copy) { if (sel) copy(otherText(b.dataset.copy)); return; }
      if (b) pick(b.classList.contains("x") ? "" : b.dataset.c);
    });

    document.addEventListener("selectionchange", () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (hold) return;
        const xs = picked();
        if (xs) { sel = xs; edit = null; show("sel"); }
        else if (bar.dataset.mode === "sel") hide();
      }, 220);
    });
    // 引いた所を押したら、色を替える・消す。段落に印が付く（欄の onclick）のは止める
    document.addEventListener("click", (e) => {
      if (bar.contains(e.target)) return;
      const s = window.getSelection();
      if (s && !s.isCollapsed) return;
      const mk = e.target.closest && e.target.closest("mark.tk-hl");
      const m = mk && list()[+mk.dataset.k];
      if (m) { e.stopPropagation(); edit = m; sel = null; show("edit"); }
      else if (bar.classList.contains("on")) hide();
    }, true);
    window.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  }

  // 欄ごとのコピー。行番号の横の 📋 は出している言語を全部まとめてコピーするので、
  // 言語の札（JA・KO・EN）の横に、その欄だけをコピーする 📋 を置く
  // （2026-11-25、ユーザー「各言語だけコピーするボタンが欲しい」）
  function cellCopies() {
    document.querySelectorAll("#body .cell").forEach((cell) => {
      const tag = cell.querySelector(".tag");
      if (!tag || tag.querySelector(".cp1") || !fullText(nodesOf(cell)).trim()) return;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "cp1";
      b.textContent = "📋";
      b.title = (TAGS[cell.lang] || "") + "だけをコピー";
      b.setAttribute("aria-label", b.title);
      b.addEventListener("click", (e) => { e.stopPropagation(); copy(fullText(nodesOf(cell)).trim()); });
      tag.appendChild(b);
    });
  }

  window.addEventListener("taiyaku:paint", (e) => {
    key = e.detail && e.detail.key;
    if (!bar) start();
    hide();
    paint();
    cellCopies();
  });
})();

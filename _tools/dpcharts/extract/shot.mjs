// ヘッドレス Chrome を CDP で動かし、図を出したページを撮る。
// node shot.mjs <url> <out.png> [--theme light|dark] [--width 1280] [--height 900] [--mobile] [--charts 1|0]
//   [--to <図の id>] [--eval <式>]
// 撮ったあと、図の数・コンソールの警告とエラーを出す
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const argv = process.argv.slice(2);
const url = argv[0], out = argv[1];
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i < 0 ? d : argv[i + 1]; };
const flag = (k) => argv.includes('--' + k);
const theme = opt('theme', 'light'), width = +opt('width', 1280), height = +opt('height', 900);
const mobile = flag('mobile'), charts = opt('charts', '1'), to = opt('to', ''), extra = opt('eval', '');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const prof = mkdtempSync(path.join(tmpdir(), 'dpc-cdp-'));
const port = 9300 + Math.floor(Math.random() * 600);
const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`,
    '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });

let ws;
for (let i = 0; i < 100 && !ws; i++) {
    try {
        const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
        const page = list.find((t) => t.type === 'page');
        if (page) ws = new WebSocket(page.webSocketDebuggerUrl);
    } catch (e) { }
    if (!ws) await sleep(150);
}
await new Promise((r) => { ws.onopen = r; });
let seq = 0;
const pending = new Map(), logs = [];
ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); return; }
    if (d.method === 'Runtime.consoleAPICalled' && ['warning', 'error'].includes(d.params.type))
        logs.push(d.params.type + ': ' + d.params.args.map((a) => a.value ?? a.description).join(' '));
    if (d.method === 'Runtime.exceptionThrown')
        logs.push('exception: ' + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text));
};
const send = (method, params = {}) => new Promise((res) => { const i = ++seq; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
const loaded = async () => { for (let i = 0; i < 100; i++) { if (await evaluate('document.readyState') === 'complete') return; await sleep(100); } };

await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile });
await send('Page.navigate', { url });
await loaded();
await evaluate(`localStorage.setItem('dp_charts', '${charts}'); localStorage.setItem('theme', '${theme}'); 1`);
logs.length = 0;
await send('Page.reload', { ignoreCache: true });
await loaded();
let n = 0;
for (let i = 0; i < 50; i++) {
    n = await evaluate("document.querySelectorAll('.dpc-fig').length");
    if (charts !== '1' || n > 0) break;
    await sleep(100);
}
await sleep(800);
if (to) {
    await evaluate(`(() => { const f = document.querySelector('.dpc-fig[data-id="${to}"]');
        if (f) window.scrollTo(0, f.getBoundingClientRect().top + window.scrollY - 140); })()`);
    await sleep(500);
}
let extraOut = '';
if (extra) extraOut = JSON.stringify(await evaluate(extra));
const shot = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
console.log(out, 'figures:', n, extraOut);
for (const l of logs) console.log('  ' + l);
ws.close();
proc.kill();
await sleep(300);
try { rmSync(prof, { recursive: true, force: true }); } catch (e) { }
process.exit(0);

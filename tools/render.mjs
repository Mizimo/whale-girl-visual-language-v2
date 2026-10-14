#!/usr/bin/env node
/**
 * 逐幀渲染：HTML → MP4。
 *
 * 原理和 HyperFrames 一樣——headless Chrome 跳到每一幀的時刻、截圖，再用 ffmpeg 編碼。
 * 差別是這裡沒有 npm 依賴：CDP 走 Node 內建的 WebSocket，截圖走 Chrome 自己的介面。
 *
 * 為什麼可以逐幀截：頁面必須提供 window.__seek(t)（見 examples/cover-anim.html 的 <script>），
 * 它把每一層動畫 pause 住再設 currentTime。所以任何一幀都能單獨重現，
 * 渲染順序不影響結果，也不會像螢幕錄影一樣掉幀。
 *
 * 音訊：頁面裡的 <audio src="…" data-start="1.2" data-duration="3" data-volume="0.6">
 * 會被讀出來，交給 ffmpeg 依同樣的秒數放進去。畫面用 seek、聲音用 adelay，
 * 兩邊都從同一條時間軸算，所以本來就是同步的。怎麼準備音樂見 docs/VIDEO.md。
 *
 * 用法（在 repo 根目錄跑）：
 *   node tools/render.mjs examples/cover-anim.html -o examples/cover-anim.mp4
 *   node tools/render.mjs examples/cover-anim.html -o /tmp/x.mp4 --scale 2 --fps 60
 *
 * 需要：Node 22+（內建 WebSocket）、Chrome、ffmpeg。不用 npm install。
 */

import { spawn } from 'node:child_process';
import { mkdtemp, writeFile, readFile, rm, mkdir, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

const CHROME_CANDIDATES = [
  process.env.CHROME,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].filter(Boolean);

/* ── 參數 ─────────────────────────────────────────────── */
function parseArgs(argv) {
  const o = { fps: 30, scale: 1, width: 1280, height: 720, duration: null, keep: false, quality: 18 };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '-o' || a === '--out') o.out = next();
    else if (a === '--fps') o.fps = Number(next());
    else if (a === '--scale') o.scale = Number(next());
    else if (a === '--width') o.width = Number(next());
    else if (a === '--height') o.height = Number(next());
    else if (a === '--duration') o.duration = Number(next());
    else if (a === '--crf') o.quality = Number(next());
    else if (a === '--keep') o.keep = true;
    else rest.push(a);
  }
  o.input = rest[0];
  return o;
}

const args = parseArgs(process.argv.slice(2));
if (!args.input) {
  console.error('用法：node tools/render.mjs <composition.html> [-o out.mp4] [--fps 30] [--scale 2] [--keep]');
  process.exit(2);
}
const INPUT = path.resolve(args.input);
if (!existsSync(INPUT)) { console.error(`找不到 ${INPUT}`); process.exit(2); }
// 沒給 -o 就放在 HTML 旁邊，不要丟到當下的工作目錄
const OUT = path.resolve(args.out
  || path.join(path.dirname(INPUT), path.basename(INPUT).replace(/\.html?$/, '') + '.mp4'));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── CDP 連線 ─────────────────────────────────────────── */
class CDP {
  constructor(ws) {
    this.ws = ws;
    this.seq = 0;
    this.pending = new Map();
    this.handlers = new Map();
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(`${msg.error.message} (${JSON.stringify(msg.error.data ?? '')})`)) : resolve(msg.result);
      } else if (msg.method) {
        for (const h of this.handlers.get(msg.method) ?? []) h(msg.params);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.seq;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  on(method, fn) {
    this.handlers.set(method, [...(this.handlers.get(method) ?? []), fn]);
  }
  once(method, timeoutMs = 30000) {
    return new Promise((resolve) => {
      const timer = setTimeout(() => resolve(null), timeoutMs);
      this.on(method, (p) => { clearTimeout(timer); resolve(p); });
    });
  }
  async eval(expression, awaitPromise = true) {
    const r = await this.send('Runtime.evaluate', { expression, awaitPromise, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result?.value;
  }
}

async function connect(port, attempts = 100) {
  for (let i = 0; i < attempts; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) {
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((resolve, reject) => {
          ws.addEventListener('open', resolve, { once: true });
          ws.addEventListener('error', () => reject(new Error('CDP WebSocket 連不上')), { once: true });
        });
        return new CDP(ws);
      }
    } catch { /* Chrome 還沒起來 */ }
    await sleep(100);
  }
  throw new Error('等不到 Chrome 的 debugging port');
}

/* ── 主流程 ───────────────────────────────────────────── */
const chromePath = CHROME_CANDIDATES.find((p) => existsSync(p));
if (!chromePath) { console.error('找不到 Chrome。用 CHROME=/path/to/chrome 指定。'); process.exit(2); }

const profile = await mkdtemp(path.join(tmpdir(), 'wg-render-'));
const framesDir = args.keep ? path.join(path.dirname(OUT), '.frames') : path.join(profile, 'frames');
await mkdir(framesDir, { recursive: true });

const chrome = spawn(chromePath, [
  '--headless=new',
  '--remote-debugging-port=0',
  `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-gpu', '--hide-scrollbars', '--mute-audio',
  '--force-device-scale-factor=1',
  '--allow-file-access-from-files',
  '--disable-lcd-text',                       // 和 PDF 管線一樣：不要次像素抗鋸齒
  '--font-render-hinting=none',               // 也不要 hinting，跨機器才長得一樣
  `--window-size=${args.width},${args.height}`,
  'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe'] });

let stderr = '';
chrome.stderr.on('data', (b) => { stderr += b.toString(); });

let exitCode = 0;
try {
  // Chrome 會把實際的 port 寫在 profile 裡
  let port = null;
  for (let i = 0; i < 100 && port === null; i++) {
    try {
      const txt = await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8');
      port = Number(txt.split('\n')[0]);
    } catch { await sleep(100); }
  }
  if (!port) throw new Error('Chrome 沒有寫出 DevToolsActivePort');

  const cdp = await connect(port);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: args.width, height: args.height, deviceScaleFactor: args.scale, mobile: false,
  });

  const loaded = cdp.once('Page.loadEventFired');
  await cdp.send('Page.navigate', { url: pathToFileURL(INPUT).href });
  await loaded;

  const seekable = await cdp.eval('typeof window.__seek === "function"');
  if (!seekable) throw new Error('這個 HTML 沒有 window.__seek(t)。逐幀渲染需要它——見 _video-lab/cover-anim.html 的做法。');

  // 時長：優先用 HTML 自己宣告的 data-duration，其次 --duration
  const declared = await cdp.eval('(document.querySelector("[data-duration]")||{}).dataset?.duration ?? null');
  const duration = args.duration ?? (declared ? Number(declared) : null);
  if (!duration) throw new Error('不知道要render多長：在 composition 的標籤上加 data-duration="6"（秒），或給 --duration。');

  const total = Math.round(duration * args.fps);
  const compId = await cdp.eval('(document.querySelector("[data-composition-id]")||{}).dataset?.compositionId ?? ""');

  // seek 真的生效了嗎？先驗一次。沒有這一步的話，seek 悄悄失效也只會產出
  // 一支時間軸亂掉、但看起來「有在動」的影片，很難發現。
  const probe = await cdp.eval(`window.__seek(1.234).then(() => {
    const a = document.getAnimations();
    return { n: a.length, paused: a.every(x => x.playState === 'paused'),
             times: [...new Set(a.map(x => Math.round(x.currentTime)))] };
  })`);
  if (!probe || probe.n === 0) throw new Error('這個頁面沒有任何動畫，seek 無從驗證');
  if (!probe.paused) throw new Error('seek 之後動畫沒有停住——每一幀都會不一樣');
  if (probe.times.length !== 1 || probe.times[0] !== 1234) {
    throw new Error(`seek 沒有對齊：${probe.n} 個動畫的 currentTime 是 ${JSON.stringify(probe.times)}，應該是 [1234]`);
  }

  // 音訊：頁面裡宣告的 <audio> 就是時間軸的一部分，data-start 跟視覺的同一套秒數。
  // 畫面是逐幀 seek 出來的，聲音不是——聲音在編碼階段由 ffmpeg 依同樣的時間放進去。
  // 兩邊各自從同一個時間軸算，所以不需要「對齊」，本來就是對齊的。
  const tracks = (await cdp.eval(`[...document.querySelectorAll('audio[src]')].map(a => ({
    src: a.getAttribute('src'),
    start: Number(a.dataset.start ?? 0),
    duration: a.dataset.duration ? Number(a.dataset.duration) : null,
    volume: Number(a.dataset.volume ?? 1),
  }))`)) ?? [];
  for (const tr of tracks) {
    tr.path = path.resolve(path.dirname(INPUT), decodeURIComponent(tr.src));
    if (!existsSync(tr.path)) throw new Error(`音訊檔不存在：${tr.src}（相對於 ${path.basename(INPUT)}）`);
    if (tr.start >= duration) throw new Error(`音訊 ${tr.src} 的 data-start=${tr.start} 已經超出影片長度 ${duration}s`);
  }

  console.log(`${path.basename(INPUT)}  ${args.width * args.scale}×${args.height * args.scale}  ${args.fps}fps  ${duration}s  ${total} 幀${compId ? `  id=${compId}` : ''}${tracks.length ? `  ${tracks.length} 軌音訊` : '  無聲'}`);

  const t0 = Date.now();
  for (let f = 0; f < total; f++) {
    const t = f / args.fps;
    // 直接呼叫，不要寫成 `() => window.__seek(t)`——那只是求值出一個函式，
    // 不會執行，而且 Runtime.evaluate 對它不會報錯，於是動畫照真實時間跑、
    // 每一幀被抓到的時刻都是隨機的，時間軸整個亂掉。
    await cdp.eval(`window.__seek(${t})`);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
    await writeFile(path.join(framesDir, `${String(f).padStart(5, '0')}.png`), Buffer.from(shot.data, 'base64'));
    if (f % 10 === 0 || f === total - 1) {
      const done = f + 1;
      const eta = ((Date.now() - t0) / done) * (total - done);
      process.stdout.write(`\r  截圖 ${String(done).padStart(4)}/${total}  ${(done / (Date.now() - t0) * 1000).toFixed(1)} fps  剩 ${(eta / 1000).toFixed(0)}s   `);
    }
  }
  process.stdout.write('\n');

  const files = (await readdir(framesDir)).filter((f) => f.endsWith('.png')).sort();
  if (files.length !== total) throw new Error(`截到 ${files.length} 幀，預期 ${total} 幀`);

  // ffmpeg：yuv420p + faststart，YouTube／SNS／QuickTime 都能直接播
  const ffArgs = [
    '-y', '-loglevel', 'error',
    '-framerate', String(args.fps),
    '-i', path.join(framesDir, '%05d.png'),
  ];

  if (tracks.length) {
    // 每一軌各自「切到自己的長度 → 延遲到自己的 data-start → 套自己的音量」，再全部混在一起。
    // normalize=0 是必要的：預設 amix 會把所有軌一起除以軌數，加了第二軌音樂反而變小聲。
    const filters = [];
    tracks.forEach((tr, i) => {
      ffArgs.push('-i', tr.path);
      filters.push(`[${i + 1}:a]${[
        `atrim=0:${tr.duration ?? duration}`,
        `adelay=${Math.round(tr.start * 1000)}:all=1`,
        `volume=${tr.volume}`,
      ].join(',')}[a${i}]`);
    });
    filters.push(tracks.length > 1
      ? `${tracks.map((_, i) => `[a${i}]`).join('')}amix=inputs=${tracks.length}:normalize=0[aout]`
      : '[a0]anull[aout]');
    ffArgs.push('-filter_complex', filters.join(';'), '-map', '0:v', '-map', '[aout]', '-c:a', 'aac', '-b:a', '192k');
  }

  ffArgs.push(
    '-c:v', 'libx264', '-preset', 'slow', '-crf', String(args.quality),
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-t', String(duration),          // 音訊比影片長的時候不要把影片拖長
    OUT,
  );

  const ff = spawn(process.env.FFMPEG || 'ffmpeg', ffArgs, { stdio: ['ignore', 'ignore', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', (b) => { ffErr += b.toString(); });
  const code = await new Promise((r) => ff.on('close', r));
  if (code !== 0) throw new Error(`ffmpeg 失敗：\n${ffErr}`);

  const kb = (await readFile(OUT)).length / 1024;
  console.log(`  ${OUT}  ${kb < 1024 ? kb.toFixed(0) + ' KB' : (kb / 1024).toFixed(1) + ' MB'}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  if (args.keep) console.log(`  幀留在 ${framesDir}`);
} catch (err) {
  exitCode = 1;
  console.error(`\n渲染失敗：${err.message}`);
  if (stderr.trim()) console.error(stderr.trim().split('\n').slice(-6).join('\n'));
} finally {
  // profile 一律刪——即使 --keep，要留的幀也在 OUT 旁邊，不在 profile 裡
  chrome.kill('SIGKILL');
  await rm(profile, { recursive: true, force: true });
}
process.exit(exitCode);

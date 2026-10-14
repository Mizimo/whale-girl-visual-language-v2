# 視頻

HTML 變成 MP4。跟 PDF 是同一套路——同一份 HTML、同一組 CSS、同一組元件，只是把「一頁」換成「一秒」。

```bash
node tools/render.mjs examples/cover-anim.html -o examples/cover-anim.mp4
```

需要 Node 22+、Chrome、ffmpeg。**不用 npm install**——CDP 走 Node 內建的 WebSocket，截圖走 Chrome 自己的介面。

## 跟簡報差在哪

同一個視覺語言，但視頻是**在手機上、隔著一點距離、只掃一眼**，簡報是投影在牆上、人坐在那裡看。所以 [`templates/video.css`](../templates/video.css) 做的事只有一件：把 [`tokens.css`](../templates/tokens.css) 的尺寸換成隔著看也清楚的數字。

- **字級放大約 1.6 倍**　封面標題 64pt（簡報 40pt）、正文 22pt（20pt）
- **線條加粗**　`--rule` 3px、`--deck-bar` 5px——縮圖上看不見的線就等於沒有
- **角色小臉放大**　`--av` 76px，不然在 720p 上只剩一顆頭
- **署名縮小**　11pt，小到不想看可以忽略

**不是越大越好。** 72pt 的標題會撞到主視覺的留白，副標會壓在角色的頭髮上。64pt 是配合現在那張 key visual 量出來的——**換圖要重新量**。

## 做一支的步驟

1. HTML 連 `../templates/video.css`（它會把 `deck.css` 拉進來，不要再另外連）
2. 在最外層的 `.slide` 上宣告時間：`data-composition-id`、`data-duration`、`data-width`、`data-height`
3. 用純 CSS animation 寫動畫，每一層一個 `@keyframes`，節奏靠 `animation-delay`
4. 頁面提供 `window.__seek(t)`（複製 `examples/cover-anim.html` 的那一段）
5. 渲染

## window.__seek(t) 是唯一的要求

逐幀渲染的前提是：**任何一幀都能單獨重現**。不能靠 wall clock，也不能靠播放——不然就是螢幕錄影，會掉幀、跑兩次結果不一樣。

```js
window.__seek = async (t) => {
  await document.fonts.ready;
  for (const a of document.getAnimations()) {
    a.pause();
    a.currentTime = t * 1000;   // CSS animation 的 currentTime 包含 delay
  }
  await new Promise(r => { requestAnimationFrame(() => requestAnimationFrame(r)); setTimeout(r, 80); });
};
```

`animation-fill-mode: both` 是必要的，少了它，seek 到動畫開始前會直接跳到結束狀態。

**踩過的坑。** 一開始寫成 `() => window.__seek(t)`——那只是「算出一個函式」，不會執行；而 CDP 的 `Runtime.evaluate` 對它**不會報錯**。結果動畫照真實時間跑、每一幀被抓到的時刻都是隨機的，影片看起來「有在動」，時間軸卻整個是亂的。所以 `render.mjs` 開工前會先驗一次：seek 到 1.234 秒，所有動畫的 `currentTime` 必須都是 1234、而且都停住，不是就拒絕渲染。

## 音訊

宣告在 HTML 裡，跟視覺同一條時間軸：

```html
<audio src="../assets/audio/bgm.m4a" data-start="0" data-duration="6" data-volume="0.5"></audio>
```

畫面用 seek、聲音用 ffmpeg 的 `adelay`——兩邊各自從同一個秒數算，所以**不需要對齊，本來就是對齊的**。多軌會自動 `amix` 混在一起。

- `data-start` 是這一軌從第幾秒開始播，不是相對時間
- `data-duration` 省略就播到影片結束；比影片長會被切掉
- `amix` 一定要 `normalize=0`。預設是全部除以軌數，加了第二軌音樂反而變小聲
- **淡出要自己處理**——音樂忽然斷掉很難聽，但那是編曲的事，渲染器不管
- 音樂自己做的話，Logic Pro 輸出 48kHz 立體聲就好；渲染器會編成 AAC 192k

## 踩過的坑

- **動畫不能超過 `data-duration`。** 曾經有一個泡泡是 3.7 秒開始、跑 2.6 秒，總共 6.5 秒，而影片只有 6 秒——最後 0.5 秒被硬切掉，看起來像畫面閃了一下。
- **渲染速度大約 5 fps。** 一支 30fps、6 秒的影片（180 幀）要 40 秒左右；1 分鐘的影片要 12 分鐘。`--scale 2` 是 supersampling，畫質更好但慢四倍。
- **幀不會自動清掉。** `--keep` 會把 PNG 留在輸出檔旁邊的 `.frames/`，除錯用；預設是渲完就刪。

## 什麼時候該換成 HyperFrames

原理是同一套——headless Chrome 逐幀 seek，再用 ffmpeg 編碼。這份實作是零依賴的小版本，`data-composition-id` / `data-start` / `data-duration` / `data-volume` 的屬性名刻意跟 [HyperFrames](https://github.com/heygen-com/hyperframes)（HeyGen，Apache 2.0）一樣，所以真要搬過去，頁面不用重寫。

會想搬過去的時候：

- 要 **shader 轉場、Lottie、Three.js、Anime.js**
- 要現成的 catalog 元件（圖表、地圖、字幕條、社群浮層）
- 要**雲端渲染**或 AWS Lambda 分散渲染
- 要做**人聲佔的頻段自動壓下音樂**、EQ／壓縮／reverb 這一類混音

**這份沒有的就是後面那一整組**——它是個渲染器，不是一套製作系統。音訊只有「放進去、延遲、音量、混音」四件事，剩下的在 ffmpeg 或編曲軟體裡做。

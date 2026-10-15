# 素材來源與授權

這個 repo 收了五組素材，**授權條件不一樣**，用之前先看這一頁。

## 一、original-design ｜ 鯨魚娘設計稿

- **上游**：[phoiex/AAAAGENT](https://github.com/phoiex/AAAAGENT) 的 `assets/original-design`
- **檔案**：`whale-avatar.png`（512×512 頭像）、`whale-design.png`（937×1678 白底全身）、`whale-transparent.png`（1117×1858 透明整稿）、`whale-layers.psd`（44 層）、`assets.json`（上游校驗清單）
- **製作方式**：AI 輔助繪製 ＋ 人工挑選與本地影像處理
- **授權**：CC BY-NC-SA 4.0（署名、非商業、相同方式分享）
- **上游署名鏈**：歷史參考為 [fornarwhal/deepseek-whale-girl-icon](https://github.com/fornarwhal/deepseek-whale-girl-icon)，該倉庫署名上善無形（OC「溟月」）、ZipZipPipe、QYQCAMIAO，並註明原圖作者未確認
- **怎麼用**：頭像最常用。圓形裁切 34px 放講解框、58mm 放封面

## 二、dsh-widget ｜ DSH 餘額小鯨魚掛件

- **上游**：[MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget)（`dsh-whale-widget` v0.4.2）
- **檔案**：`whale-chibi.png`（原 `DSniang1.png`，610×610）、`whale-chibi-hd.png`（原 `DSniang02.png`，1026×1026）、`plugin-icon.png`（原 `icon.png`，256×256）
- **製作方式**：AI 工具生成的圖，經人工挑選與裁切；**生成工具與原始出處已不可考**（檔案內的中介資料已被剝離）
- **授權**：⚠️ 這一組跟其他三組不一樣。插件的**程式碼**是 MIT，但上游 `PROVENANCE.md` 明確寫：`assets/**` 的插畫與音效**不在 MIT 覆蓋範圍內**，按 **as-is** 隨插件分發、**僅用於運行該插件、不授予再許可**。
  - 這個 repo 是 private，屬於個人保存與自用。
  - **不要把這三張圖再公開散布或再授權**。要在公開作品裡用，回去跟作者確認。
- **怎麼用**：Q 版表情，適合當貼圖、小圖示、狀態指示

## 三、maid-atelier ｜ 深海女僕工坊皮膚

- **上游**：[Small-tailqwq/dsh-deep-whale](https://github.com/Small-tailqwq/dsh-deep-whale/tree/main/maid-atelier) 的 `maid-atelier`（來源固定在提交 `62ec784`）
- **本機位置**：`~/.dsh/skins/maid-atelier`、壁紙 `~/Pictures/DSH/maid-atelier-background/`
- **檔案**：`maid-left.webp`（1122×2019 透明）、`maid-right.webp`（1394×2649 透明）、`palace-night.webp`（1586×992 夜景背景），外加原樣的 `NOTICE` 與 `LICENSE-ARTWORK`
- **授權**：CC BY-NC-SA 4.0（署名、非商業、相同方式分享）
- **署名鏈（完整保留，不能省）**：
  1. 一創 **上善** —— 鯨魚娘角色形象原設計，[pixiv](https://www.pixiv.net/users/62155430)
  2. 二創 **zipzip / ZipZipPipe** —— 加入 DeepSeek 元素的女僕鯨魚娘二次設計（GPT Image 2），[pixiv](https://www.pixiv.net/users/18604994)
  3. 三創 **Small-tailqwq** —— 皮膚用的 DeepSeek 元素再設計與整理
- **怎麼用**：兩張立繪是全身透明稿，適合當封面主視覺、簡報人物、海報；夜景圖當背景

## 四、gal-view ｜ GAL 視窗插件

- **上游**：`gal-view` v0.3.3（作者 Yunicon），DSH 的 Galgame 風格對話視圖插件
- **檔案**：`whale-girl-tachie.png`（原 `DeepSeek娘_立绘.png`，1024×1536 透明立繪）、`bedroom-bg.png`（原 `DeepSeek娘_背景_卧室.png`，1672×941）、`dialogue-box.png`（原 `对话框.png`，1672×941 透明蕾絲框）
- **取出方式**：這三張內嵌在插件的 `gal-scene.json` 裡（`assets[].dataUrl` 的 base64）。解析 JSON、把 base64 還原成 PNG，**像素未做任何修改**。
- **授權**：插件的 `LICENSE` 是 MIT（Copyright 2026 Yunicon），`gal-scene.json` 列在 `package.json` 的 `files` 裡隨包分發。但**內嵌圖片的個別作者與來源，插件文件沒有另外說明，這點未經確認**。
- **怎麼用**：立繪是目前手上最完整的一張全身圖，細節最多，適合當主要視覺；對話框可以直接當 UI 素材

## 五、generated-2026-10-14 ｜ 本次補圖

- **位置**：[`assets/generated-2026-10-14/`](../assets/generated-2026-10-14/README.md)
- **內容**：6 張表情、1 張 Q 版站姿、5 張橫式主視覺、3 張教學動作、4 張小圖案與 1 張單色線稿，共 20 張 PNG。主視覺分原版、cinematic、editorial、ink-print、casual；editorial 與 ink-print 已選定保留。
- **製作日期與工具**：2026-10-14，Codex 內建 `image_gen`；本次生成，未指定或推測底層模型版本。
- **角色來源**：15 張角色相關圖片以本 repo 的 `assets/original-design/whale-design.png` 為角色參考；表情差分直接編輯同批的 `expressions/whale-happy.png`，部分圖片也引用這張基準臉。4 張小圖案為文字提示生成，沒有輸入第三方圖片。
- **Q 版來源**：以 [Neko3000 的 chibi 主參考 0067](https://github.com/Neko3000/deepseek-whalechan/blob/main/skills/whalechan-image-character/assets/reference-images/chibi/0067_angry_you_are_silly_reply_rendered_isolated.webp) 為主要依據，[TreapGoGo 的 Q 版三視圖](https://github.com/TreapGoGo/deepseek-whale-girl/blob/main/characters/dafeiyu/reference-sheets/dafeiyu-chibi-character-sheet.png) 補充造型與站姿。只使用這兩張圖作為本次交付 Q 版的圖像參考；淘汰版本保留於提示詞歷史，參考原圖未加入本庫。
- **人設研究**：[Neko3000/deepseek-whalechan](https://github.com/Neko3000/deepseek-whalechan) 的 [character-spec.md](https://github.com/Neko3000/deepseek-whalechan/blob/main/skills/whalechan-image-character/references/character-spec.md) 與 [form-profiles.md](https://github.com/Neko3000/deepseek-whalechan/blob/main/skills/whalechan-image-character/references/form-profiles.md)，以及 [TreapGoGo/deepseek-whale-girl](https://github.com/TreapGoGo/deepseek-whale-girl) 的[人設與提示詞](https://treapgogo.github.io/deepseek-whale-girl/)。Neko 規格文件標示 CC BY-NC-SA 4.0，Treap 原創說明與提示詞標示 CC BY-SA 4.0；本批提示詞另行撰寫，沒有搬入兩站的原始圖片。上述文件授權不自動涵蓋 Q 版使用的參考圖片。
- **主視覺研究**：[VISIONS 2026 官方樣張頁](https://visions.pr-pixiv.net/2026/en/sample/) 與 [01.webp](https://visions.pr-pixiv.net/2026/assets/img/sample/01.webp)（光影與空間）、[04.webp](https://visions.pr-pixiv.net/2026/assets/img/sample/04.webp)（限色、排線與紙感）、[06.webp](https://visions.pr-pixiv.net/2026/assets/img/sample/06.webp)（低彩度時裝插畫）、[05.webp](https://visions.pr-pixiv.net/2026/assets/img/sample/05.webp)（城市敘事與色塊層次）。研究的是一般繪畫與構圖手法，參考作品原圖未加入本庫，也不納入本庫的授權。最初由 2027 路徑取得的樣張經核對與 2026 版本位元相同，來源統一引用 VISIONS 2026。
- **主視覺方向**：cinematic 著重窗邊光影；editorial 採低彩度與細線；ink-print 採限色排線；casual 為雨後高架車站街角，角色穿奶油色短夾克、海軍藍白條紋 T 與藍灰寬褲，背帆布包跨步回望，以平塗拼貼和粉筆紙紋呈現，右側保留淡奶油／鼠尾草色標題空間。
- **處理紀錄**：保留生成 PNG，未裁切、縮放、去背或修改像素；Q 版為原生 1254×1254 不透明淺米白背景，小圖案的透明背景由生成工具直接產生。五張主視覺保留原生橫式畫幅與標題留白，逐檔尺寸見素材目錄及 `manifest.json`。
- **授權與署名**：15 張 `original-design` 衍生角色圖沿用其 CC BY-NC-SA 4.0 與署名鏈；4 張新增小圖案也按本庫 CC BY-NC-SA 4.0 整理，共 19 張。Q 版所參照的 Neko3000／TreapGoGo 圖片授權另計，目前未確認其個別許可；本圖保留於 private repo 自用、待 DSH 審核，不另授 CC。保留 AI 輔助製作揭露，不代表官方角色素材。
- **可追溯資料**：資料夾中的 `prompts-*.json` 保存實際使用的完整提示詞、引用圖與生成紀錄；`manifest.json` 保存每張圖片的尺寸、透明資訊、位元組數及 SHA-256。全庫校驗清單也已更新。

使用這批圖片中適用 CC BY-NC-SA 4.0 的 19 張時可附：

```text
大肥魚（@Kujira-rice）／ Mizimo
大肥魚補充插圖：Mizimo 專案，Codex image_gen AI 輔助製作（2026-10-14）
角色視覺參考：phoiex/AAAAGENT original-design；歷史設計參考 fornarwhal/deepseek-whale-girl-icon
人設規格參考：Neko3000/deepseek-whalechan、TreapGoGo/deepseek-whale-girl
CC BY-NC-SA 4.0，僅供非商業使用；完整來源與原署名鏈見 docs/SOURCES.md
```

Q 版另記錄為「視覺參考：Neko3000/deepseek-whalechan chibi 0067、TreapGoGo/deepseek-whale-girl Q 版三視圖」，不套用上面的 CC 授權文字。

## 六、deepseek-icon ｜ 圓角圖標

- **位置**：`assets/deepseek-icon/whale-icon.png`
- **內容**：1254 × 1254 圓角方形圖標，透明背景。
- **來源**：Mizimo 用 ChatGPT 內建 `image_gen` 生成，2026-09-30 下載（生成日期不晚於此），原檔名 `DeepSeek.png`。
- **紀錄完整度**：這一張**沒有**提示詞與參考圖紀錄，跟第五組不同，只能記下已知的部分。
- **處理紀錄**：原檔複製，**像素未做任何修改**。四角本來就是圓的，不需要再裁。
- **授權與署名**：AI 生成素材，比照第五組處理。角色如果算 `original-design` 的衍生，沿用它的 CC BY-NC-SA 4.0 與署名鏈；但因為沒有參考圖紀錄，無法確認實際從哪張圖衍生，所以不另外宣告獨立的 CC。用到公開產出物上時附上「AI 輔助製作」揭露。
- **怎麼用**：README 主視覺、頭像。

## 檔名對照

- `DSniang1.png` → `assets/dsh-widget/whale-chibi.png`
- `DSniang02.png` → `assets/dsh-widget/whale-chibi-hd.png`
- `icon.png` → `assets/dsh-widget/plugin-icon.png`
- `maid-atelier-maid-left-v5.webp` → `assets/maid-atelier/maid-left.webp`
- `maid-atelier-maid-right-v6.webp` → `assets/maid-atelier/maid-right.webp`
- `maid-atelier-palace-night-v4.webp` → `assets/maid-atelier/palace-night.webp`
- `DeepSeek娘_立绘.png` → `assets/gal-view/whale-girl-tachie.png`
- `DeepSeek娘_背景_卧室.png` → `assets/gal-view/bedroom-bg.png`
- `对话框.png` → `assets/gal-view/dialogue-box.png`

## 用素材時要附的署名

`original-design`、`maid-atelier` 與本次 15 張 `original-design` 衍生圖按 CC BY-NC-SA 4.0 使用，產出物上要附署名；`dsh-widget`、Q 版與 `gal-view` 的限制見各自段落。把用到的來源各列一行：

```text
大肥魚（@Kujira-rice）／ Mizimo
角色素材：phoiex/AAAAGENT original-design（CC BY-NC-SA 4.0）
深海女僕工坊：上善（原案）／ zipzip（二創）／ Small-tailqwq（皮膚素材），CC BY-NC-SA 4.0
```

**第一行一定先寫自己**（`大肥魚（@Kujira-rice）／ Mizimo`），再列素材來源。素材授權要求的是後面那幾行，
但產出物上只出現別人的名字會看不出是誰做的。

`assets/original-design/assets.json` 有上游檔案大小與 SHA-256，可以核對手上這份是不是原樣。

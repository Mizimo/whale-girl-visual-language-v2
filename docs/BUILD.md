# 建置與輸出

HTML 要變成 PDF、截圖、預覽圖，靠的是 `tools/` 和 `templates/build_pdf.py`。這一頁記流程和踩過的坑。

## 一次重建全部

```bash
pip install fonttools pillow pypdfium2
python3 tools/fetch_fonts.py     # 第一次，或 fonts/ 空的時候
python3 tools/build.py
```

`build.py` 依序做五件事，任何一步失敗就停下來：

1. `tools/tokens.py --check`　色表、字級表、對比檢查
2. `templates/build_pdf.py`　把 `examples/` 的每份 HTML 輸出成 PDF
3. `tools/previews.py`　更新 README 的預覽圖
4. `tools/shots.py`　重截 COMPONENTS.md 的元件截圖
5. `tools/checksums.py --check`　核對校驗清單

## 只輸出一個檔案

```bash
python3 templates/build_pdf.py 你的檔案.html 輸出.pdf
```

需要 Chrome 131 以後的版本，Chromium、Edge 也可以。macOS、Linux、Windows 都會自動找，找不到就用 `--chrome 路徑` 指定。

輸出後會檢查兩件事：

- **PDF 頁數比 section 多** → 有一頁塞不下，直接失敗。拆頁或刪內容，不要縮字。
- **有 Type 3 字型** → 提醒你先抓字體。系統的 PingFang、可變字型、CFF 外框的 OpenType，Chrome 都會嵌成 Type 3，有些閱讀器和印刷流程會處理不好。

## 元件截圖

```bash
python3 tools/shots.py             # 全部重截，順便刪掉沒有對應元件的舊圖
python3 tools/shots.py whale ex    # 只截這幾個
```

每次只留下一個元件和包著它的那幾層、把周圍的空白裁掉。A4 的元件照 A4 內容寬排、兩倍解析度；簡報的整張投影片照原尺寸截。截完會順手把 [COMPONENTS.md](COMPONENTS.md) 裡 A4 元件圖的 width 改成實際寬度的一半。

## 改配色、字級

只動 [`templates/tokens.css`](../templates/tokens.css)，然後：

```bash
python3 tools/tokens.py
```

色表、字級表、`docs/palette.svg`、講義範例裡的色塊都會跟著更新。

## 每台機器輸出的要一樣

這幾件事是踩過才穩下來的，換機器或接到 CI 之前先確認：

- **先跑一次 `python3 tools/fetch_fonts.py`。** `fonts/` 不進 git；沒跑的話不只用不到 Noto 的靜態字重，還少了 `WGAccidentals`——升降記號會掉到系統的 Apple Symbols 或 DejaVu，字寬和字重都不對。
- **抗鋸齒要固定。** macOS 的 Chrome 預設用 sub-pixel（LCD）抗鋸齒，Linux／headless 用 grayscale，同一份字型看起來會粗一級。`components.css` 的 `html` 已經關掉 sub-pixel、改用 geometricPrecision；這幾行不要拿掉。
- **等寬字型現在還是靠系統。** `--font-mono` 排到 `"DejaVu Sans Mono"`：Linux 有，macOS 會落到 Andale Mono，字重差一點。要完全一致得再從 Noto 系列抽一組等寬字型進來（還沒做，記在這裡）。
- **截圖很吃 Chrome。** `tools/shots.py` 一次要開六十幾次 headless，偶爾會卡住；逾時已經放寬到 300 秒並重試三次，還是卡就先把殘留的 `--headless` 程序清掉再跑。
- **`fonts/` 別進 git。** 四個字型加起來二十幾 MB，用 `fetch_fonts.py` 生就好。

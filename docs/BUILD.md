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

## 改紙張、配色、字級

**紙張**　`templates/doc.css` 開頭的 `--paper` 和 `--page-h`：`A4` / `297mm` 是預設，
`A4 landscape` / `210mm` 是橫向，`A5` / `210mm`、`Letter` / `279mm` 也吃。整份一起換。

**配色、字級**　只動 [`templates/tokens.css`](../templates/tokens.css)，然後：

```bash
python3 tools/tokens.py
```

色表、字級表、`docs/palette.svg`、講義範例裡的色塊都會跟著更新。

## 重建之後 PDF 的位元組會不一樣

Chrome 每次產 PDF 都會寫新的 `/CreationDate` 和 `/ID`，所以就算內容一個字都沒改，`git status` 還是會顯示四份 PDF 變了。要比對有沒有真的動到內容，看頁數和文字：

```bash
python3 -c "
import pathlib, pypdfium2 as pdfium
for p in sorted(pathlib.Path('examples').glob('*.pdf')):
    d = pdfium.PdfDocument(p); w, h = d[0].get_size()
    print(p.name, len(d), '頁', f'{w/72*25.4:.0f} x {h/72*25.4:.0f} mm')
"
```

內容沒變就 `git checkout -- examples/` 退掉，別讓它混進 diff。

## 每台機器輸出的要一樣

這幾件事是踩過才穩下來的，換機器或接到 CI 之前先確認：

- **先跑一次 `python3 tools/fetch_fonts.py`。** `fonts/` 不進 git；沒跑的話不只用不到 Noto 的靜態字重，還少了 `WGAccidentals`——升降記號會掉到系統的 Apple Symbols 或 DejaVu，字寬和字重都不對。
- **抗鋸齒要固定。** macOS 的 Chrome 預設用 sub-pixel（LCD）抗鋸齒，Linux／headless 用 grayscale，同一份字型看起來會粗一級。`components.css` 的 `html` 已經關掉 sub-pixel、改用 geometricPrecision；這幾行不要拿掉。
- **等寬字型現在還是靠系統。** `--font-mono` 排到 `"DejaVu Sans Mono"`：Linux 有，macOS 會落到 Andale Mono，字重差一點。要完全一致得再從 Noto 系列抽一組等寬字型進來（還沒做，記在這裡）。
- **截圖很吃 Chrome。** `tools/shots.py` 一次要開六十幾次 headless，偶爾會卡住；逾時已經放寬到 300 秒並重試三次，還是卡就先把殘留的 `--headless` 程序清掉再跑。
- **`fonts/` 別進 git。** 四個字型加起來二十幾 MB，用 `fetch_fonts.py` 生就好。

## 柔邊不要用半透明的 `box-shadow`

Chrome 印 PDF 的時候，**半透明的 `box-shadow`**（有模糊，或只有擴散的那種）會被寫成帶
Luminosity 軟遮罩的 `ExtGState`。macOS 的「預覽程式」和 PDFKit **不套用那個遮罩**，
陰影就整塊糊成一個實心正方形——圓形頭像背後忽然多一塊方形底色，就是這個原因。
在 Chrome 裡看、用 Chrome 重新截圖都正常，只有拿去 Preview 開才會看到，所以很容易漏掉。

柔邊一律改用 `filter: drop-shadow()`，它不會走軟遮罩：

```css
/* ✗ 在 Preview 裡是一塊方塊 */
box-shadow: 0 2px 10px rgba(90, 100, 163, .16);
/* ✓ */
filter: drop-shadow(0 2px 10px rgba(90, 100, 163, .16));
```

判斷方法：

- **模糊或擴散其中一個不是 0，而且顏色是半透明的** → 走軟遮罩，Preview 會壞。
- **模糊 0、擴散 0、顏色不透明**（`.sticker` 的紙邊、`.bubbles` 的泡泡、`.level` 的點、
  `.beats` 的亮拍）→ Chrome 直接畫成向量，沒問題，那些留著。
- 要一圈外框就用 `outline`：跟著 `border-radius` 走，又不影響排版。
- `text-shadow` 沒這個問題。

改完重新輸出，然後確認 PDF 裡沒有 Luminosity 軟遮罩（全部 0 就對了）：

```bash
python3 - <<'PY'
import glob, pypdf
for f in sorted(glob.glob('examples/*.pdf')):
    n = sum(1 for p in pypdf.PdfReader(f).pages
              for v in ((p.get('/Resources') or {}).get('/ExtGState') or {}).values()
              if v.get_object().get('/SMask') and v.get_object().get('/SMask') != '/None')
    print(f, n)
PY
```

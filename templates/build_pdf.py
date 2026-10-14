#!/usr/bin/env python3
"""HTML → PDF（給大肥魚視覺語言庫的文件模板用）

用法：
    python3 build_pdf.py 輸入.html [輸出.pdf] [--chrome 路徑] [--no-check]

沒給輸出路徑就放在 HTML 旁邊、同檔名 .pdf。
用 Chrome 的 headless 列印，所以 @page 頁首頁碼、section 分頁、A4／16:9 尺寸
這些 CSS 設定都會照做，也不會多出瀏覽器預設的頁首頁尾。需要 Chrome 131 以後。

找 Chrome 的順序：--chrome 參數 → 環境變數 CHROME → 各平台的常見安裝位置。

輸出後會檢查兩件事：
  1. 溢頁：PDF 頁數要等於 section.page／section.slide 的數量。多出來代表有一頁塞不下，
     照「塞不下就拆頁」的原則，這種情況直接失敗。
  2. Type 3 字型：通常是系統的可變字型（例如 PingFang）。只提醒、不失敗；
     執行 python3 tools/fetch_fonts.py 之後重新輸出就會改用 Noto Sans TC。
"""
from __future__ import annotations

import html.parser
import os
import pathlib
import re
import shutil
import subprocess
import sys

CANDIDATES = {
    "darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ],
    "linux": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"],
    "win32": [
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    ],
}


def find_chrome(explicit: str | None = None) -> str:
    for c in (explicit, os.environ.get("CHROME")):
        if c:
            return c
    for c in CANDIDATES.get(sys.platform, CANDIDATES["linux"]):
        c = os.path.expandvars(c)
        found = c if os.path.isabs(c) and pathlib.Path(c).exists() else shutil.which(c)
        if found:
            return found
    raise RuntimeError("找不到 Chrome。用 --chrome 指定路徑，或設定環境變數 CHROME。")


class _Sections(html.parser.HTMLParser):
    """數 section.page／section.slide，一個 section 應該剛好印成一頁。"""

    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "section":
            classes = (dict(attrs).get("class") or "").split()
            if "page" in classes or "slide" in classes:
                self.count += 1


def count_sections(src: pathlib.Path) -> int:
    p = _Sections()
    p.feed(src.read_text(encoding="utf-8"))
    return p.count


def html_to_pdf(src: pathlib.Path, dst: pathlib.Path | None = None, chrome: str | None = None,
                timeout: int = 180) -> pathlib.Path:
    src = src.resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    dst = (dst or src.with_suffix(".pdf")).resolve()

    cmd = [
        find_chrome(chrome),
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={dst}",
        src.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not dst.exists():
        raise RuntimeError(f"Chrome 轉檔失敗（{r.returncode}）：{r.stderr[-1500:]}")
    return dst


def check(src: pathlib.Path, pdf: pathlib.Path) -> bool:
    data = pdf.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page\b", data))
    sections = count_sections(src)
    ok = True
    if sections and pages != sections:
        print(f"✗ 溢頁：HTML 有 {sections} 個 section，PDF 卻印成 {pages} 頁。"
              f"有一頁塞不下，拆頁或刪內容，不要縮字。", file=sys.stderr)
        ok = False
    if b"/Type3" in data:
        print("! PDF 裡有 Type 3 字型，有些閱讀器和印刷流程會處理不好。"
              "執行 python3 tools/fetch_fonts.py 後重新輸出。", file=sys.stderr)
    return ok


def main(argv: list[str]) -> int:
    args = argv[1:]
    chrome = None
    if "--chrome" in args:
        i = args.index("--chrome")
        chrome = args[i + 1]
        del args[i:i + 2]
    no_check = "--no-check" in args
    args = [a for a in args if a != "--no-check"]
    if not args:
        print(__doc__.strip())
        return 2
    src = pathlib.Path(args[0])
    dst = pathlib.Path(args[1]) if len(args) > 1 else None
    out = html_to_pdf(src, dst, chrome)
    print(f"PDF → {out}  ({out.stat().st_size / 1024:.0f} KB)", flush=True)
    if no_check:
        return 0
    return 0 if check(src.resolve(), out) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

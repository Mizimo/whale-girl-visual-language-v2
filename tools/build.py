#!/usr/bin/env python3
"""一次重建：token 檢查 → 輸出 examples/ 的每份 PDF → 更新預覽圖和元件截圖 → 核對校驗清單。

影片 composition（HTML 裡有 data-composition-id 的那種）不輸出 PDF——它是動畫，
靜止的 PDF 只會是一頁空白。影片另外渲染，見 docs/VIDEO.md 和 tools/render.mjs。

用法：
    python3 tools/build.py

任何一步失敗就停下來並回傳 1。輸出 PDF 和元件截圖需要 Chrome（見 templates/build_pdf.py），
預覽圖需要 Pillow 和 pypdfium2（pip install pillow pypdfium2）。
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(*args: str) -> None:
    print(f"\n▸ {' '.join(args)}", flush=True)
    if subprocess.run([sys.executable, *args], cwd=ROOT).returncode != 0:
        raise SystemExit(1)


def is_video(html: pathlib.Path) -> bool:
    """這個 HTML 是不是影片 composition。看契約標記，不看檔名。"""
    return "data-composition-id" in html.read_text(encoding="utf-8")


def main() -> int:
    run("tools/tokens.py", "--check")
    for html in sorted((ROOT / "examples").glob("*.html")):
        if is_video(html):
            print(f"\n▸ 略過 {html.relative_to(ROOT)}（影片 composition，不輸出 PDF）", flush=True)
            continue
        run("templates/build_pdf.py", str(html.relative_to(ROOT)))
    run("tools/previews.py")
    run("tools/shots.py")
    run("tools/checksums.py", "--check")
    print("\n全部完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

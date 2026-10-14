#!/usr/bin/env python3
"""一次重建：token 檢查 → 輸出 examples/ 的每份 PDF → 更新預覽圖 → 核對校驗清單。

用法：
    python3 tools/build.py

任何一步失敗就停下來並回傳 1。輸出 PDF 需要 Chrome（見 templates/build_pdf.py），
預覽圖需要 Pillow 和 poppler 的 pdftoppm。
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


def main() -> int:
    run("tools/tokens.py", "--check")
    for html in sorted((ROOT / "examples").glob("*.html")):
        run("templates/build_pdf.py", str(html.relative_to(ROOT)))
    run("tools/previews.py")
    run("tools/checksums.py", "--check")
    print("\n全部完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

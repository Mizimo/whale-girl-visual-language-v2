#!/usr/bin/env python3
"""把 examples/ 的 PDF 排成 README 用的預覽圖：docs/preview/ 底下的 handout、deck、components、components-deck。

用法：
    python3 tools/previews.py

需要 Pillow 和 pypdfium2（pip install pillow pypdfium2），兩者都是純 Python，不用另外裝系統工具。
先用 templates/build_pdf.py 重新輸出範例 PDF，再跑這支。
"""
from __future__ import annotations

import pathlib
import re
import tempfile

import pypdfium2 as pdfium
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAP = 12
A4, SLIDE = (396, 560), (640, 360)
A4_SMALL, SLIDE_SMALL = (330, 467), (480, 270)  # 元件總覽頁數多，格子小一點
CELL = {"handout": A4, "deck": SLIDE, "components": A4_SMALL, "components-deck": SLIDE_SMALL}
COLS = {"handout": 3, "deck": 3, "components": 5, "components-deck": 4}


def background() -> str:
    css = (ROOT / "templates" / "tokens.css").read_text(encoding="utf-8")
    return re.search(r"--c-code-bg:\s*(#[0-9a-fA-F]{6})", css).group(1)


def sheet(name: str, bg: str) -> pathlib.Path:
    w, h = CELL[name]
    with tempfile.TemporaryDirectory() as tmp:
        pdf = pdfium.PdfDocument(ROOT / "examples" / f"{name}.pdf")
        paths = []
        for i in range(len(pdf)):
            p = pathlib.Path(tmp) / f"p-{i + 1:02d}.png"
            pdf[i].render(scale=150 / 72).to_pil().convert("RGB").save(p)
            paths.append(p)
        pages = [Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS) for p in sorted(paths)]
    cols = COLS[name]
    rows = (len(pages) + cols - 1) // cols
    out = Image.new("RGB", (cols * w + (cols + 1) * GAP, rows * h + (rows + 1) * GAP), bg)
    for i, page in enumerate(pages):
        out.paste(page, (GAP + (i % cols) * (w + GAP), GAP + (i // cols) * (h + GAP)))
    dst = ROOT / "docs" / "preview" / f"{name}.png"
    out.save(dst, optimize=True)
    return dst


def main() -> int:
    bg = background()
    for name in CELL:
        p = sheet(name, bg)
        print(f"更新　{p.relative_to(ROOT)}　{p.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

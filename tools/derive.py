#!/usr/bin/env python3
"""從原圖產生衍生圖：README 預覽縮圖、講解框頭像、深底用的反白小圖示、給模板用的輕量版。

用法：
    python3 tools/derive.py

需要 Pillow（pip install pillow）。原圖永遠不動，衍生圖都可以用這支腳本重新產生；
改完記得跑 python3 tools/checksums.py 更新校驗清單。
"""
from __future__ import annotations

import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
GEN = ASSETS / "generated-2026-10-14"

# README 預覽用的縮圖：跟 generated-2026-10-14/thumbnails 同規格（長邊 720px、WebP q85），只縮不放大
THUMBS = [
    "original-design/whale-avatar.png",
    "original-design/whale-design.png",
    "deepseek-icon/whale-icon.png",
    "dsh-widget/whale-chibi.png",
    "dsh-widget/plugin-icon.png",
    "maid-atelier/maid-left.webp",
    "maid-atelier/palace-night.webp",
    "gal-view/whale-girl-tachie.png",
    "gal-view/bedroom-bg.png",
]

# 六張表情共用同一張基準臉，裁成跟 original-design/whale-avatar.png 一樣的取景：
# 雙眼在畫面約 48% 高度、兩眼間距約佔寬度 20%
AVATAR_BOX = (87, 0, 1153, 1066)
AVATAR_SIZE = 256

# 輕量版（各資料夾底下的 lite/）：CSS 預設和範例 PDF 用這一組。
# 不透明的圖轉 JPEG，Chrome 會原樣嵌進 PDF；PNG 會被無損重壓，一張插圖就要 2–3 MB。
# 透明的小圖示縮到用得到的大小。要最好的畫質，在 HTML 裡直接指原圖就好。
LITE_JPEG = [
    "gal-view/bedroom-bg.png",
    "generated-2026-10-14/teaching/whale-teaching-blank-sign.png",
    "generated-2026-10-14/teaching/whale-teaching-notebook.png",
    "generated-2026-10-14/teaching/whale-teaching-pointer.png",
    "generated-2026-10-14/key-visual/whale-key-visual-editorial.png",
]
LITE_PNG = {  # 檔名樣式：長邊
    "generated-2026-10-14/icons/*.png": 256,
    "generated-2026-10-14/icons/on-dark/*.png": 256,
    "generated-2026-10-14/line-art/whale-line-art-transparent.png": 640,
}
JPEG_QUALITY = 88


def thumb(rel: str) -> pathlib.Path:
    src = ASSETS / rel
    out = src.parent / "thumbnails" / (src.stem + ".webp")
    out.parent.mkdir(exist_ok=True)
    im = Image.open(src)
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    im.thumbnail((720, 720), Image.LANCZOS)
    im.save(out, "WEBP", quality=85, method=6)
    return out


def avatars() -> list[pathlib.Path]:
    outs = []
    dst = GEN / "avatars"
    dst.mkdir(exist_ok=True)
    for src in sorted((GEN / "expressions").glob("*.png")):
        im = Image.open(src).convert("RGB").crop(AVATAR_BOX).resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
        out = dst / src.name
        im.save(out, "PNG", optimize=True)
        outs.append(out)
    return outs


def _lightness(r: int, g: int, b: int) -> float:
    # 近似感知明度，只用來分出深色描邊
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def icons_on_dark() -> list[pathlib.Path]:
    """深藍描邊在深底上會消失，改成白色描邊；藍色填色和亮面保留。"""
    outs = []
    dst = GEN / "icons" / "on-dark"
    dst.mkdir(exist_ok=True)
    for src in sorted((GEN / "icons").glob("*.png")):
        im = Image.open(src).convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                t = min(1.0, max(0.0, (_lightness(r, g, b) - 0.22) / 0.16))  # 0＝描邊（明度約 .20），1＝填色（.38 以上）
                px[x, y] = (round(255 + (r - 255) * t), round(255 + (g - 255) * t), round(255 + (b - 255) * t), a)
        out = dst / src.name
        im.save(out, "PNG", optimize=True)
        outs.append(out)
    return outs


def lite() -> list[pathlib.Path]:
    outs = []
    for rel in LITE_JPEG:
        src = ASSETS / rel
        out = src.parent / "lite" / (src.stem + ".jpg")
        out.parent.mkdir(exist_ok=True)
        Image.open(src).convert("RGB").save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
        outs.append(out)
    for pattern, size in LITE_PNG.items():
        for src in sorted(ASSETS.glob(pattern)):
            out = src.parent / "lite" / src.name
            out.parent.mkdir(exist_ok=True)
            im = Image.open(src).convert("RGBA")
            im.thumbnail((size, size), Image.LANCZOS)
            im.save(out, "PNG", optimize=True)
            outs.append(out)
    return outs


def main() -> int:
    made = [thumb(rel) for rel in THUMBS] + avatars() + icons_on_dark() + lite()
    for p in made:
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

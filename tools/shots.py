#!/usr/bin/env python3
"""把元件總覽裡每個標了 data-shot 的元件各截一張圖，放到 docs/preview/c/，給 docs/COMPONENTS.md 用。

用法：
    python3 tools/shots.py              全部重截（順便刪掉已經沒有對應元件的舊圖）
    python3 tools/shots.py chat vs      只截這幾個

做法：用 Chrome 的螢幕截圖（不經過 PDF）。每次只留下一個元件和包著它的那幾層，其他全部藏起來，
再把四周的空白裁掉。A4 的元件照 A4 內容寬（182mm）排、兩倍解析度，無損和高品質有損哪個小就存哪個；
簡報的元件整張投影片照原尺寸截，存有損 WebP（照片多，無損太大）。
A4 章節頁這種整頁的（名字以 chapter 開頭）照整張 A4 截、不裁白。
截完會順手把 docs/COMPONENTS.md 裡 A4 元件圖的 width 改成實際寬度的一半（兩倍圖照原大小顯示）；
簡報和整頁的圖是縮圖，寬度在文件裡自己定，不會動。
需要 Chrome（找法跟 templates/build_pdf.py 一樣）和 Pillow。
"""
from __future__ import annotations

import io
import pathlib
import re
import subprocess
import sys
import time
import tempfile

from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "templates"))
from build_pdf import find_chrome  # noqa: E402

OUT = ROOT / "docs" / "preview" / "c"
DOC = ROOT / "docs" / "COMPONENTS.md"
SOURCES = {"components.html": "doc", "components-deck.html": "deck"}
A4_WIDTH = 688   # A4 扣掉左右邊界剩 182mm，96dpi 下約 688px
PAD = 16         # 裁切時四周留的白（CSS px）
SCALE = {"doc": 2, "deck": 1}
WINDOW = {"doc": (A4_WIDTH + 2 * PAD, 1400), "deck": (1280, 720), "page": (794, 1123)}
FULL_PAGE = ("chapter",)  # 名字這樣開頭的是 A4 整頁（章節頁）：照整張 A4 截、不裁白


def isolate(html: str, name: str, base: str, medium: str) -> str:
    """只留下 data-shot=name 的元件、它裡面的東西和包著它的那幾層。"""
    sel = f'[data-shot="{name}"]'
    css = f"body :not({sel}, {sel} *, :has({sel})) {{ display: none !important; }}\n"
    if medium == "doc":
        css += f"html {{ background: #fff; }}\nbody {{ margin: 0; padding: {PAD}px; width: {A4_WIDTH}px; }}\n"
    elif medium == "page":
        css += "body { margin: 0; width: 210mm; }\n"
    else:
        css += "body { margin: 0; }\n"
    return html.replace("<head>", f'<head>\n<base href="{base}">\n<style>\n{css}</style>', 1)


def trim(im: Image.Image, pad: int) -> Image.Image:
    """裁掉四周的白，再留 pad 的邊。"""
    diff = ImageChops.difference(im, Image.new("RGB", im.size, "white")).convert("L")
    box = diff.point(lambda v: 255 if v > 6 else 0).getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def shoot(chrome: str, src: pathlib.Path, name: str, medium: str, tmp: pathlib.Path) -> pathlib.Path:
    page = tmp / f"{name}.html"
    page.write_text(isolate(src.read_text(encoding="utf-8"), name, src.parent.as_uri() + "/", medium),
                    encoding="utf-8")
    png = tmp / f"{name}.png"
    w, h = WINDOW[medium]
    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--run-all-compositor-stages-before-draw", "--virtual-time-budget=5000",
           f"--force-device-scale-factor={SCALE.get(medium, 1)}", f"--window-size={w},{h}",
           f"--screenshot={png}", page.as_uri()]
    # 偶爾會卡住（Chrome 開太多次之後），放寬逾時並重試幾次
    for attempt in range(3):
        png.unlink(missing_ok=True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            err = r.stderr
        except subprocess.TimeoutExpired:
            r, err = None, "逾時"
        if r is not None and r.returncode == 0 and png.exists():
            break
        print(f"  重試 {name}（{attempt + 1}/3）：{err[-200:]}", flush=True)
        time.sleep(3)
    else:
        raise RuntimeError(f"截圖失敗：{name}\n{err[-800:]}")
    im = Image.open(png).convert("RGB")
    out = OUT / f"{name}.webp"
    if medium == "doc":
        im = trim(im, PAD * SCALE[medium])
        encoded = []
        for opts in ({"lossless": True}, {"quality": 92}):
            buf = io.BytesIO()
            im.save(buf, "WEBP", method=6, **opts)
            encoded.append(buf.getvalue())
        out.write_bytes(min(encoded, key=len))
    else:
        im.save(out, "WEBP", quality=86, method=6)
    return out


def sync_widths() -> None:
    """COMPONENTS.md 裡 A4 元件圖的 width＝實際寬度／2，兩倍圖才會照原大小顯示。"""
    if not DOC.exists():
        return
    text = DOC.read_text(encoding="utf-8")

    def fix(m: re.Match) -> str:
        name, img = m.group(2), OUT / f"{m.group(2)}.webp"
        if name.startswith(("deck-",) + FULL_PAGE) or not img.exists():
            return m.group(0)
        return f"{m.group(1)}{Image.open(img).width // SCALE['doc']}{m.group(3)}"

    new = re.sub(r'(<img src="preview/c/([\w-]+)\.webp" width=")\d+(")', fix, text)
    if new != text:
        DOC.write_text(new, encoding="utf-8")
        print(f"更新　{DOC.relative_to(ROOT)} 的圖寬")


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    jobs = []
    for file, medium in SOURCES.items():
        src = ROOT / "examples" / file
        for name in re.findall(r'data-shot="([^"]+)"', src.read_text(encoding="utf-8")):
            jobs.append((src, name, "page" if name.startswith(FULL_PAGE) else medium))
    names = [n for _, n, _ in jobs]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        print(f"data-shot 重複：{', '.join(sorted(dupes))}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        for src, name, medium in jobs:
            if wanted and name not in wanted:
                continue
            out = shoot(chrome, src, name, medium, pathlib.Path(tmp))
            print(f"更新　{out.relative_to(ROOT)}　{out.stat().st_size / 1024:.0f} KB", flush=True)
    sync_widths()
    if not wanted:
        for old in OUT.glob("*.webp"):
            if old.stem not in names:
                old.unlink()
                print(f"刪除　{old.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

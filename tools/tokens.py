#!/usr/bin/env python3
"""設計 token 工具：templates/tokens.css 是唯一來源，色表和字級表都從它產生。

用法：
    python3 tools/tokens.py            更新 docs/palette.svg，以及 README.md、examples/handout.html 裡的色表與字級表
    python3 tools/tokens.py --check    只檢查不改檔：表是不是最新、對比有沒有達標；有問題就回傳 1
    python3 tools/tokens.py sample     重新量基準設定圖的「明度 → 色相」曲線（需要 Pillow）

對比門檻（WCAG）：種類 text 的顏色對白底至少 4.5:1，line 至少 3:1，
另外檢查幾組實際會疊在一起的組合，例如講解框底上的標籤字。
"""
from __future__ import annotations

import html
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "templates" / "tokens.css"
VIDEO = ROOT / "templates" / "video.css"
SVG = ROOT / "docs" / "palette.svg"
README = ROOT / "README.md"
HANDOUT = ROOT / "examples" / "handout.html"
CANON = ROOT / "assets" / "original-design" / "whale-transparent.png"

# 實際會疊在一起的組合：（字或線, 底, 門檻, 說明）
PAIRS = [
    ("primary", "tint", 4.5, "講解框標籤"),
    ("ink", "tint", 4.5, "講解框內文"),
    ("ink", "tint-2", 4.5, "例子框內文"),
    ("title", "code-bg", 4.5, "程式碼字"),
    ("accent", "tint", 3.0, "講解框左線"),
    ("line-strong", "tint-2", 3.0, "例子框左線"),
]
SWATCHES = ["title", "primary", "accent", "accent-soft", "tint", "tint-2", "line-strong", "ink", "ink-2", "ink-3"]
SANS = "PingFang TC, Noto Sans TC, Noto Sans CJK TC, Microsoft JhengHei, sans-serif"
MONO = "SF Mono, Menlo, Consolas, DejaVu Sans Mono, monospace"


# ── 讀 token ──────────────────────────────
def read_tokens():
    css = TOKENS.read_text(encoding="utf-8")
    colors = {}
    for name, value, note in re.findall(r"--c-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6});\s*/\*\s*(.+?)\s*\*/", css):
        label, use, kind = [s.strip() for s in note.split("｜")]
        kind, _, bg = kind.partition("@")
        colors[name] = {"hex": value.lower(), "label": label, "use": use, "kind": kind, "bg": bg or "paper"}
    sizes = {"doc": [], "deck": []}
    for medium, step, value, note in re.findall(r"--(doc|deck)-([a-z]+):\s*([\d.]+pt);\s*/\*\s*(.+?)\s*\*/", css):
        sizes[medium].append((step, value, note))
    leading = dict(re.findall(r"--(doc|deck)-leading:\s*([\d.]+);", css))
    # 視頻不是新的一組變數，是「覆寫簡報」——同一個名字、不同的數字，放在 video.css。
    # 另外讀一份併進 sizes，字級表就還是由這裡產生，不用手寫、也不會走鐘。
    sizes["video"] = [(step, value, note) for step, value, note in re.findall(
        r"--deck-([a-z]+):\s*([\d.]+pt);\s*/\*\s*(.+?)\s*\*/", VIDEO.read_text(encoding="utf-8"))]
    leading["video"] = leading["deck"]
    return colors, sizes, leading


# ── 對比 ─────────────────────────────────
def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_: str) -> float:
    r, g, b = (_lin(int(hex_[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def audit(colors) -> list[str]:
    bad = []
    for name, c in colors.items():
        need = {"text": 4.5, "line": 3.0}.get(c["kind"])
        bg = colors[c["bg"]]["hex"]
        if need and contrast(c["hex"], bg) < need:
            bad.append(f"--c-{name} {c['hex']} 對 --c-{c['bg']} 只有 {contrast(c['hex'], bg):.2f}:1（{c['kind']} 至少 {need}:1）")
    for fg, bg, need, why in PAIRS:
        ratio = contrast(colors[fg]["hex"], colors[bg]["hex"])
        if ratio < need:
            bad.append(f"{why}：--c-{fg} 疊在 --c-{bg} 上只有 {ratio:.2f}:1（至少 {need}:1）")
    return bad


# ── 產生 ─────────────────────────────────
def ratio_note(c, colors) -> str:
    return f"　{contrast(c['hex'], colors[c['bg']]['hex']):.1f}:1" if c["kind"] in ("text", "line") else ""


def is_deep(name: str) -> bool:
    return name.startswith("deep") or "on-deep" in name


def render_svg(colors) -> str:
    light = [(n, c) for n, c in colors.items() if n != "paper" and not is_deep(n)]
    deep = [(n, c) for n, c in colors.items() if is_deep(n)]

    def block(items, top, title_fill, sub_fill, body_fill, panel, edge):
        half = (len(items) + 1) // 2
        out = []
        for i, (name, c) in enumerate(items):
            x = 34 if i < half else 467
            y = top + (i if i < half else i - half) * 74
            stroke = edge if abs(luminance(c["hex"]) - luminance(panel)) < 0.25 else "none"
            out.append(f'<rect x="{x}" y="{y}" width="54" height="54" rx="10" fill="{c["hex"]}" stroke="{stroke}"/>')
            out.append(f'<text x="{x + 68}" y="{y + 22}" font-family="{MONO}" font-size="14.5" font-weight="600" '
                       f'fill="{title_fill}">{c["hex"]}<tspan font-size="12" font-weight="400" '
                       f'fill="{sub_fill}">　--c-{name}</tspan></text>')
            out.append(f'<text x="{x + 68}" y="{y + 42}" font-family="{SANS}" font-size="13" fill="{body_fill}">'
                       f'{html.escape(c["label"])}　·　{html.escape(c["use"])}{ratio_note(c, colors)}</text>')
        return out, top + max(half, len(items) - half) * 74

    hexes = {n: c["hex"] for n, c in colors.items()}
    rows_light, y = block(light, 92, hexes["title"], hexes["ink-3"], hexes["ink-2"], hexes["tint-2"], hexes["line"])
    band = y + 8
    rows_deep, y2 = block(deep, band + 66, hexes["on-deep"], hexes["on-deep-3"], hexes["on-deep-2"], hexes["deep"],
                          hexes["line-on-deep"])
    h = y2 + 16
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{h}" viewBox="0 0 900 {h}">',
           f'<rect width="100%" height="100%" rx="14" fill="{hexes["tint-2"]}"/>',
           f'<path d="M0 {band}H900V{h - 14}a14 14 0 0 1-14 14H14a14 14 0 0 1-14-14Z" fill="{hexes["deep"]}"/>',
           f'<text x="34" y="52" font-family="{SANS}" font-size="23" font-weight="700" fill="{hexes["title"]}">配色</text>',
           f'<text x="106" y="52" font-family="{SANS}" font-size="14" fill="{hexes["ink-3"]}">'
           f'從角色身上取色：深色跟洋裝與髮根，淺色跟髮尾與眼睛</text>',
           *rows_light,
           f'<text x="34" y="{band + 44}" font-family="{SANS}" font-size="23" font-weight="700" fill="{hexes["on-deep"]}">深海</text>',
           f'<text x="106" y="{band + 44}" font-family="{SANS}" font-size="14" fill="{hexes["on-deep-3"]}">'
           f'深色頁用的一組：章節頁、深色簡報、VS Code 深色預覽</text>',
           *rows_deep, "</svg>"]
    return "\n".join(out) + "\n"


def size_line(sizes, leading, medium: str) -> str:
    parts = []
    for step, value, note in sorted(sizes[medium], key=lambda s: -float(s[1][:-2])):
        lead = f"（行距 {leading[medium]}）" if step == "body" else ""
        parts.append(f"{value.replace('pt', '')}pt {note}{lead}")
    return "／".join(parts)


def palette_md(colors) -> str:
    def line(n, c):
        return f"- `{c['hex']}`　**{c['label']}**　`--c-{n}`　{c['use']}{ratio_note(c, colors)}"
    light = [line(n, c) for n, c in colors.items() if n != "paper" and not is_deep(n)]
    deep = [line(n, c) for n, c in colors.items() if is_deep(n)]
    return "\n".join(light) + "\n\n深海（深色頁用，比例是對 `--c-deep` 算的）：\n\n" + "\n".join(deep)


def type_md(sizes, leading) -> str:
    return (f"- **A4 文件**　{size_line(sizes, leading, 'doc')}\n"
            f"- **16:9 簡報**　{size_line(sizes, leading, 'deck')}\n"
            f"- **視頻**　{size_line(sizes, leading, 'video')}")


def palette_html(colors) -> str:
    chips = []
    for n in SWATCHES:
        c = colors[n]
        chips.append(f'    <div><div class="chip" style="background:var(--c-{n})"></div>'
                     f'<div class="name">{c["hex"]}<br>{html.escape(c["label"])}</div></div>')
    return '  <div class="swatches">\n' + "\n".join(chips) + "\n  </div>"


def type_html(sizes, leading) -> str:
    return (f'  <ul class="scale">\n    <li>A4　{html.escape(size_line(sizes, leading, "doc"))}</li>\n'
            f'    <li>簡報　{html.escape(size_line(sizes, leading, "deck"))}</li>\n'
            f'    <li>視頻　{html.escape(size_line(sizes, leading, "video"))}</li>\n  </ul>')


def splice(text: str, key: str, body: str) -> str:
    pat = re.compile(rf"(<!-- tokens:{key} -->)(.*?)([ \t]*<!-- /tokens:{key} -->)", re.S)
    if not pat.search(text):
        raise SystemExit(f"找不到標記 <!-- tokens:{key} -->")
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(3), text)


def targets(colors, sizes, leading) -> dict[pathlib.Path, str]:
    readme = README.read_text(encoding="utf-8")
    readme = splice(readme, "palette-md", palette_md(colors))
    readme = splice(readme, "type-md", type_md(sizes, leading))
    handout = HANDOUT.read_text(encoding="utf-8")
    handout = splice(handout, "palette-html", palette_html(colors))
    handout = splice(handout, "type-html", type_html(sizes, leading))
    return {SVG: render_svg(colors), README: readme, HANDOUT: handout}


# ── 取色 ─────────────────────────────────
def sample() -> int:
    from PIL import Image  # 只有這個子命令需要

    def oklch(r, g, b):
        r, g, b = (_lin(v / 255) for v in (r, g, b))
        l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
        m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
        s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
        L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
        A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
        B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
        return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360

    im = Image.open(CANON).convert("RGBA")
    im.thumbnail((360, 360))
    bins = {}
    for r, g, b, a in im.getdata():
        if a < 230:
            continue
        L, C, H = oklch(r, g, b)
        if C < 0.035 or not 200 <= H <= 320:  # 只看藍色系，略過膚色、白色、灰色
            continue
        d = bins.setdefault(round(L * 20) / 20, [0.0, 0.0, []])
        d[0] += math.sin(math.radians(H))
        d[1] += math.cos(math.radians(H))
        d[2].append(C)
    print(f"{CANON.relative_to(ROOT)}：藍色系像素的 OKLCH 明度 → 色相、彩度")
    for L, (s, c, cs) in sorted(bins.items()):
        if len(cs) < 40:
            continue
        cs.sort()
        print(f"  L {L:.2f}　色相 {math.degrees(math.atan2(s, c)) % 360:5.1f}°　彩度 {cs[len(cs) // 2]:.3f}　（{len(cs)} px）")
    return 0


def main(argv: list[str]) -> int:
    if "sample" in argv[1:]:
        return sample()
    colors, sizes, leading = read_tokens()
    bad = audit(colors)
    for b in bad:
        print(f"✗ {b}", file=sys.stderr)
    stale = []
    for path, want in targets(colors, sizes, leading).items():
        have = path.read_text(encoding="utf-8") if path.exists() else ""
        if have != want:
            if "--check" in argv[1:]:
                stale.append(path)
            else:
                path.write_text(want, encoding="utf-8")
                print(f"更新　{path.relative_to(ROOT)}")
    for p in stale:
        print(f"✗ {p.relative_to(ROOT)} 跟 tokens.css 不同步，執行 python3 tools/tokens.py", file=sys.stderr)
    if not bad and not stale:
        print("token 檢查通過")
    return 1 if bad or stale else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

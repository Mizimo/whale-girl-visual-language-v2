#!/usr/bin/env python3
"""下載 Noto Sans TC 和 Noto Sans JP，各做成 Regular、Bold 兩個靜態字重放進 fonts/（不進 git）。
再從 Noto Sans TC 抽出 ♭ ♮ ♯ 三個字，收緊左右空白，做成 WG Accidentals。

用法：
    pip install fonttools      # 第一次需要
    python3 tools/fetch_fonts.py

為什麼要自己做靜態字重：Chrome 輸出 PDF 時，系統的 PingFang、可變字型、CFF 外框的 OpenType
都會被嵌成 Type 3，有些閱讀器和印刷流程會處理不好；TrueType 外框的靜態字重才會以一般的 CID 字型嵌入。
JP 那組補的是 Noto Sans TC 沒有的日文漢字（楽、徴、続、録……）。
Noto 的 ♭ ♮ ♯ 是一個全形字寬，和弦記號會排成「B ♭ 7」；WG Accidentals 只改字寬、不改字形。
來源固定在 google/fonts 的一個提交，下載後先核對 SHA-256 才做。
"""
from __future__ import annotations

import hashlib
import pathlib
import sys
import tempfile
import urllib.request

COMMIT = "3be1884c48c3e45b52ecc725676a08f87776373e"
BASE = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl"
FAMILIES = {
    "NotoSansTC": (f"{BASE}/notosanstc/NotoSansTC%5Bwght%5D.ttf",
                   "864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f", "約 12 MB"),
    "NotoSansJP": (f"{BASE}/notosansjp/NotoSansJP%5Bwght%5D.ttf",
                   "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f", "約 9 MB"),
}
WEIGHTS = {"Regular": 400, "Bold": 700}
ACCIDENTALS = (0x266D, 0x266E, 0x266F)  # ♭ ♮ ♯
SIDE = 40                               # 收緊後左右各留的空白（字身 1000）
DEST = pathlib.Path(__file__).resolve().parent.parent / "fonts"


def main() -> int:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.varLib import instancer
    except ImportError:
        print("需要 fontTools：pip install fonttools", file=sys.stderr)
        return 1

    DEST.mkdir(exist_ok=True)
    for family, (url, sha, size) in FAMILIES.items():
        outs = {name: DEST / f"{family}-{name}.ttf" for name in WEIGHTS}
        if all(p.exists() for p in outs.values()):
            print(f"已存在　{family}")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            vf = pathlib.Path(tmp) / f"{family}-VF.ttf"
            print(f"下載中　{family}（可變字型，{size}）")
            with urllib.request.urlopen(url, timeout=180) as r:
                vf.write_bytes(r.read())
            got = hashlib.sha256(vf.read_bytes()).hexdigest()
            if got != sha:
                print(f"校驗失敗　{family}\n  預期 {sha}\n  實際 {got}", file=sys.stderr)
                return 1
            for name, weight in WEIGHTS.items():
                inst = instancer.instantiateVariableFont(TTFont(vf), {"wght": weight}, updateFontNames=True)
                inst.save(outs[name])
                print(f"完成　{outs[name].name}")
    for name in WEIGHTS:
        out = DEST / f"WGAccidentals-{name}.ttf"
        if out.exists():
            print(f"已存在　{out.name}")
            continue
        accidentals(DEST / f"NotoSansTC-{name}.ttf", out, name)
        print(f"完成　{out.name}")
    print(f"字體在 {DEST}")
    return 0


def accidentals(src: pathlib.Path, dst: pathlib.Path, style: str) -> None:
    """從 Noto Sans TC 的靜態字重抽出 ♭ ♮ ♯，左右空白收到 SIDE，改名成 WG Accidentals。"""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(src)
    opts = subset.Options()
    opts.layout_features = []
    opts.name_IDs = [0, 7, 8, 9, 11, 12, 13, 14]  # 版權、授權這些照原字型留著（OFL）
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=ACCIDENTALS)
    sub.subset(font)
    glyf, hmtx, cmap = font["glyf"], font["hmtx"], font.getBestCmap()
    for cp in ACCIDENTALS:
        name = cmap[cp]
        g = glyf[name]
        g.recalcBounds(glyf)
        dx = SIDE - g.xMin
        if g.isComposite():
            for c in g.components:
                c.x += dx
        else:
            g.coordinates.translate((dx, 0))
        g.recalcBounds(glyf)
        hmtx[name] = (g.xMax - g.xMin + 2 * SIDE, g.xMin)
    names = font["name"]
    family, ps = "WG Accidentals", f"WGAccidentals-{style}"
    for nid, text in {1: family, 2: style, 3: f"{ps};whale-girl-visual-language", 4: f"{family} {style}", 6: ps}.items():
        names.setName(text, nid, 3, 1, 0x409)
        names.setName(text, nid, 1, 0, 0)
    font.save(dst)


if __name__ == "__main__":
    raise SystemExit(main())

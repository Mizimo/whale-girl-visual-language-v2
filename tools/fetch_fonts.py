#!/usr/bin/env python3
"""下載 Noto Sans TC，做成 Regular、Bold 兩個靜態字重放進 fonts/（不進 git）。

用法：
    pip install fonttools      # 第一次需要
    python3 tools/fetch_fonts.py

為什麼要自己做靜態字重：Chrome 輸出 PDF 時，系統的 PingFang、可變字型、CFF 外框的 OpenType
都會被嵌成 Type 3，有些閱讀器和印刷流程會處理不好；TrueType 外框的靜態字重才會以一般的 CID 字型嵌入。
來源固定在 google/fonts 的一個提交，下載後先核對 SHA-256 才做。
"""
from __future__ import annotations

import hashlib
import pathlib
import sys
import tempfile
import urllib.request

COMMIT = "3be1884c48c3e45b52ecc725676a08f87776373e"
URL = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
SHA256 = "864727d210d54f2537bbe23b3a839436c3992af72de9322af5270897246bd44f"
WEIGHTS = {"Regular": 400, "Bold": 700}
DEST = pathlib.Path(__file__).resolve().parent.parent / "fonts"


def main() -> int:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.varLib import instancer
    except ImportError:
        print("需要 fontTools：pip install fonttools", file=sys.stderr)
        return 1

    outs = {name: DEST / f"NotoSansTC-{name}.ttf" for name in WEIGHTS}
    if all(p.exists() for p in outs.values()):
        print(f"已存在　{DEST}")
        return 0

    DEST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        vf = pathlib.Path(tmp) / "NotoSansTC-VF.ttf"
        print("下載中　Noto Sans TC（可變字型，約 12 MB）")
        with urllib.request.urlopen(URL, timeout=180) as r:
            vf.write_bytes(r.read())
        got = hashlib.sha256(vf.read_bytes()).hexdigest()
        if got != SHA256:
            print(f"校驗失敗\n  預期 {SHA256}\n  實際 {got}", file=sys.stderr)
            return 1
        for name, weight in WEIGHTS.items():
            inst = instancer.instantiateVariableFont(TTFont(vf), {"wght": weight}, updateFontNames=True)
            inst.save(outs[name])
            print(f"完成　{outs[name].name}")
    print(f"字體在 {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""重新產生 assets/CHECKSUMS.txt，或只檢查它是否還對得上。

用法：
    python3 tools/checksums.py            重算 assets/ 底下每個檔案的 SHA-256 與位元組數
    python3 tools/checksums.py --check    只檢查，不改檔；有出入就列出來並回傳 1

清單只收 git 追蹤或準備加入的檔案（略過 .DS_Store 這類雜檔），依路徑排序，
每組素材前面加一行註解，方便人眼對照。
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "CHECKSUMS.txt"
SKIP = {".DS_Store", "Thumbs.db", OUT.name}
HEADER = """# 素材校驗清單（本 repo 保存副本）
# 欄位：sha256  位元組  相對路徑
# original-design 一組另有上游自己的 assets.json 可對照
# 由 python3 tools/checksums.py 產生，不要手改
"""


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render() -> str:
    lines = [HEADER]
    group = None
    for p in sorted(q for q in ASSETS.rglob("*") if q.is_file() and q.name not in SKIP):
        rel = p.relative_to(ROOT).as_posix()
        top = p.relative_to(ASSETS).parts[0] if len(p.relative_to(ASSETS).parts) > 1 else "."
        if top != group:
            group = top
            lines.append(f"\n# {top}\n" if top != "." else "\n")
        lines.append(f"{sha256(p)}  {p.stat().st_size:>9}  {rel}\n")
    return "".join(lines)


def main(argv: list[str]) -> int:
    want = render()
    have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if "--check" in argv[1:]:
        if want == have:
            print("校驗清單對得上")
            return 0
        old = {l.split()[-1]: l.split()[0] for l in have.splitlines() if l and not l.startswith("#")}
        new = {l.split()[-1]: l.split()[0] for l in want.splitlines() if l and not l.startswith("#")}
        for rel in sorted(old.keys() | new.keys()):
            if old.get(rel) != new.get(rel):
                tag = "新增" if rel not in old else "已刪" if rel not in new else "已變"
                print(f"✗ {tag}　{rel}", file=sys.stderr)
        print("執行 python3 tools/checksums.py 重新產生", file=sys.stderr)
        return 1
    OUT.write_text(want, encoding="utf-8")
    print(f"更新　{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

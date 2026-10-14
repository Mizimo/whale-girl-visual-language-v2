#!/usr/bin/env python3
"""把 tomidi.py 寫出來的 .mid 讀回來，確認格式站得住。

自己寫檔自己驗聽起來像在自誇，但這裡要擋的是很具體的錯：可變長度編碼有沒有
寫對、delta 時間有沒有累加錯、note on / note off 有沒有成對、每個軌有沒有
正確的 end-of-track。這些錯在 DAW 裡的症狀是「打不開」或「時間全亂」，很難查。

    python3 _lab/checkmidi.py
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def read_vlq(b: bytes, i: int) -> tuple[int, int]:
    v = 0
    while True:
        c = b[i]
        i += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            return v, i


def main() -> int:
    if len(sys.argv) > 1:
        path = pathlib.Path(sys.argv[1])
    else:
        # 預設先找自己旁邊的 .mid——打包出去之後就是這種情形；
        # 找不到才回頭找 repo 裡的範例
        beside = sorted(HERE.glob("*.mid"))
        path = beside[0] if beside else ROOT / "examples" / "deep-etude" / "deep-etude.mid"
    raw = path.read_bytes()

    if raw[:4] != b"MThd":
        print("不是 MIDI：開頭不是 MThd")
        return 1
    hlen = int.from_bytes(raw[4:8], "big")
    fmt, ntrk, div = (int.from_bytes(raw[8:10], "big"),
                      int.from_bytes(raw[10:12], "big"),
                      int.from_bytes(raw[12:14], "big"))
    print(f"{path.name}　{len(raw)} bytes")
    print(f"　format {fmt}　{ntrk} 軌　PPQ {div}　"
          f"{'✓ format 1（多軌同步）' if fmt == 1 else '⚠ 不是 format 1'}")
    if fmt != 1 or div == 0:
        return 1

    pos, total, problems = 8 + hlen, 0, 0
    for k in range(ntrk):
        if raw[pos:pos + 4] != b"MTrk":
            print(f"　軌 {k}: ✗ 找不到 MTrk")
            return 1
        blen = int.from_bytes(raw[pos + 4:pos + 8], "big")
        body = raw[pos + 8:pos + 8 + blen]
        pos += 8 + blen

        i, when, name, notes, on, eot = 0, 0, "", 0, 0, False
        while i < len(body):
            delta, i = read_vlq(body, i)
            when += delta
            st = body[i]
            if st == 0xFF:
                meta, ln = body[i + 1], body[i + 2]
                data = body[i + 3:i + 3 + ln]
                if meta == 0x03:
                    name = data.decode("ascii", "replace")
                elif meta == 0x2F:
                    eot = True
                    break
                elif meta == 0x51:
                    us = int.from_bytes(data, "big")
                    print(f"　　tempo {us} µs/四分音符 = {60_000_000/us:g} BPM")
                i += 3 + ln
            elif (st & 0xF0) in (0x90, 0x80):
                if st & 0xF0 == 0x90 and body[i + 2] > 0:
                    notes += 1
                    on += 1
                i += 3
            elif (st & 0xF0) in (0xC0, 0xD0):
                i += 2
            else:
                i += 3

        if not eot:
            print(f"　軌 {k}: ✗ 沒有 end-of-track，DAW 會拒絕開")
            problems += 1
        secs = when / div * 60 / 96
        print(f"　軌 {k}: {name or '(無名)':26s} {notes:3d} 音　"
              f"最後 tick {when:5d}（{secs:5.2f} 秒）{'✓' if eot else ''}")
        total += notes

    print(f"　總共 {total} 個音　{'✓ 全部通過' if not problems else f'✗ {problems} 個問題'}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())

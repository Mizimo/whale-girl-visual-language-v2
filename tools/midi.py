#!/usr/bin/env python3
"""把樂譜輸出成 Standard MIDI File（.mid）。純標準庫。

跟 synth.py 的分工：synth.py 把樂譜變成**聲音**（WAV），這支把它變成**符號**
（MIDI）。同一份樂譜、兩種輸出，所以改曲子只要改一個檔案。

    python3 tools/synth.py examples/deep-etude/score.py -o examples/deep-etude/bgm.wav
    python3 tools/midi.py  examples/deep-etude/score.py

為什麼要 MIDI：WAV 是死的，音色鎖在波形裡；MIDI 只記「哪個音、什麼時候、多大
力」，音色交給 DAW。要換鋼琴、加弦樂、改旋律都在 GarageBand 裡直接做。

MIDI 格式很單純：一個 MThd header 加每個軌一個 MTrk，每個事件是「距離上一個
事件的 tick 數（可變長度編碼）+ 事件本體」。音色用 General MIDI 編號：

    Pad → 89 warm pad　　Bass → 32 acoustic bass　　旋律 → 0 鋼琴
    鐘聲 → 9  glockenspiel　　泡泡 → 10 music box　　鼓 → 第 10 軌（GM 打擊樂）

前提：樂譜要提供 CHORDS / MELODY / BELLS / BUBBLES 這幾個常數，它們決定各軌
的內容。所以這不是「任何樂譜都能用」的通用工具，是「照這個結構寫的樂譜都能
用」——要接別的結構就改下面的 build()。
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import synth as SY          # noqa: E402  只要它的 hz() 和 load_score()

PPQ = 480                   # 每四分音符的 tick 數


def vlq(n: int) -> bytes:
    """MIDI 的可變長度整數：每 byte 7 位，最高位表示「還有下一個」。"""
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


class Track:
    def __init__(self, name: str, channel: int = 0, program: int | None = None):
        self.name = name
        self.ch = channel
        self.program = program
        self.ev: list[tuple[int, int, bytes]] = []      # (tick, 同 tick 的排序, 位元組)

    def note(self, tick_of, at: float, dur: float, pitch: int, vel: int) -> None:
        t0, t1 = tick_of(at), tick_of(at + dur)
        # 同一個 tick 上要先 off 再 on，否則同音高的音會互相切掉
        self.ev.append((t0, 1, bytes([0x90 | self.ch, pitch, max(1, min(127, vel))])))
        self.ev.append((t1, 0, bytes([0x80 | self.ch, pitch, 64])))

    def body(self) -> bytes:
        # 軌名用 ASCII 送出（DAW 對非 ASCII 的處理不一致）；真的碰到中文時
        # 退成 '?' 而不是讓整個檔案寫不出來
        nm = self.name.encode("ascii", "replace")[:127]
        out = bytearray()
        out += vlq(0) + b"\xff\x03" + bytes([len(nm)]) + nm
        if self.program is not None:
            out += vlq(0) + bytes([0xC0 | self.ch, self.program])
        prev = 0
        for at, _, data in sorted(self.ev, key=lambda e: (e[0], e[1])):
            out += vlq(at - prev) + data
            prev = at
        out += vlq(0) + b"\xff\x2f\x00"                 # end of track
        return b"MTrk" + len(out).to_bytes(4, "big") + bytes(out)

    def __len__(self) -> int:
        """這個軌有幾個音（不含 note off）。"""
        return sum(1 for _, order, _ in self.ev if order == 1)


def build_tracks(S, tick_of) -> list[Track]:
    """把樂譜的常數變成七個軌。第一軌只有速度／拍號／調號，不發聲。"""
    def midi(name: str) -> int:
        """音名 → MIDI 音高編號（C4 = 60、A4 = 69）。"""
        return round(69 + 12 * math.log2(SY.hz(name) / 440))

    # 第一軌：conductor，不發聲。軌名走 ASCII，中文在 DAW 裡常常變亂碼。
    head = Track(S.META.get("title_en") or S.META.get("title", "untitled"))
    us = int(round(60_000_000 / S.BPM))
    head.ev.append((0, 0, b"\xff\x51\x03" + us.to_bytes(3, "big")))   # tempo
    head.ev.append((0, 0, b"\xff\x58\x04\x04\x02\x18\x08"))           # 4/4
    head.ev.append((0, 0, b"\xff\x59\x02\x00\x01"))                   # A 小調（無升降記號）
    tracks = [head]

    pad = Track("Pad", 0, 89)
    for bar, (_, _, notes) in enumerate(S.CHORDS):
        for name in notes:
            pad.note(tick_of, bar * S.BAR, S.BAR * 1.05, midi(name), 45)
    tracks.append(pad)

    bass = Track("Bass", 1, 32)
    for bar, (_, root, _) in enumerate(S.CHORDS):
        for beat in (0, 2):
            bass.note(tick_of, bar * S.BAR + beat * S.BEAT, S.BEAT * 1.7, midi(root), 80)
    tracks.append(bass)

    lead = Track("Melody", 2, 0)
    for bar, beat, name, length in S.MELODY:
        lead.note(tick_of, bar * S.BAR + beat * S.BEAT, length * S.BEAT * 1.4, midi(name), 88)
    tracks.append(lead)

    bell = Track("Bell", 3, 9)
    for bar, beat in S.BELLS:
        bell.note(tick_of, bar * S.BAR + beat * S.BEAT, 1.5,
                  midi("A5" if bar % 4 == 0 else "E5"), 55)
    tracks.append(bell)

    # 泡泡：WAV 版是「頻率往上滑」的，MIDI 的音符滑不了（要滑得用 pitch bend，
    # 那會變成一堆自動化曲線、在 DAW 裡很難編輯），所以改成一個短裝飾音。
    bub = Track("Bubble", 4, 10)
    for t in S.BUBBLES:
        bub.note(tick_of, t, 0.09, 96, 62)              # C7
        bub.note(tick_of, t + 0.05, 0.07, 103, 42)      # G7
    tracks.append(bub)

    dr = Track("Drums", 9)                               # channel 9 = GM 打擊樂
    for bar in range(S.BARS):
        base = bar * S.BAR
        dr.note(tick_of, base, 0.12, 36, 100)            # kick
        dr.note(tick_of, base + 2 * S.BEAT, 0.12, 36, 78)  # kick（弱）
        for eighth in range(8):
            dr.note(tick_of, base + eighth * S.BEAT / 2, 0.05, 42,
                    58 if eighth % 2 else 40)            # closed hihat
    tracks.append(dr)

    return tracks


def main() -> int:
    ap = argparse.ArgumentParser(description="把一份樂譜輸出成 MIDI")
    ap.add_argument("score", type=pathlib.Path,
                    help="樂譜模組，例如 examples/deep-etude/score.py")
    ap.add_argument("-o", "--out", type=pathlib.Path, help="輸出檔（預設跟樂譜同資料夾）")
    a = ap.parse_args()

    S = SY.load_score(a.score)
    tick_of = lambda sec: max(0, round(sec / S.BEAT * PPQ))     # noqa: E731

    tracks = build_tracks(S, tick_of)
    out = a.out or a.score.with_name("deep-etude.mid")
    blob = (b"MThd" + (6).to_bytes(4, "big")
            + (1).to_bytes(2, "big")                            # format 1：多軌同步
            + len(tracks).to_bytes(2, "big")
            + PPQ.to_bytes(2, "big")
            + b"".join(t.body() for t in tracks))
    out.write_bytes(blob)

    notes = sum(len(t) for t in tracks[1:])
    print(f"{out.name}　{len(blob)/1024:.1f} KB　{len(tracks)} 軌　{notes} 個音")
    print(f"　{S.BPM:g} BPM　PPQ {PPQ}　{S.BARS} 小節　{S.DUR:g} 秒")
    for i, t in enumerate(tracks):
        prog = "—" if t.program is None else f"GM {t.program:3d}"
        count = "（不發聲）" if i == 0 else f"{len(t):3d} 個音"
        print(f"　　{t.name:28s} ch{t.ch:<2d} {prog}　{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""樂譜：深海練習曲（Deep Etude）。A 小調、96 BPM、8 小節、20 秒。

這一層只懂音樂——和弦、旋律、配器、力度。它呼叫 synth.py 的 Mix 把音疊上去，
所以想換合成方式就改 synth.py，想改曲子就改這裡。

    python3 _lab/synth.py _lab/scores/deep-etude.py -o _lab/bgm.wav
    python3 _lab/tomidi.py --score _lab/scores/deep-etude.py

和弦：Am7 - Fmaj7 - Cadd9 - G6，走兩輪。刻意寫得簡單——PV 的畫面才是主角，
音樂在這裡的角色是提供節拍和情緒。

四個段落（各兩小節）：intro 鋪底、A 進旋律、B 加鐘聲、outro 收尾。
"""
from __future__ import annotations

BPM = 96.0
BEAT = 60.0 / BPM          # 0.625 秒
BAR = BEAT * 4             # 2.5 秒
BARS = 8
DUR = BAR * BARS           # 20 秒

META = {
    "title": "深海練習曲 Deep Etude",
    # MIDI 的軌名要用 ASCII（DAW 對非 ASCII 的處理不一致），所以另外給一個
    "title_en": "Deep Etude (Whale Girl)",
    "key": "A minor",
    "bpm": BPM,
    "beat": BEAT,
    "bar": BAR,
    "bars": BARS,
    "duration": DUR,
    "sections": [
        {"bar": 0, "name": "intro"},
        {"bar": 2, "name": "A"},
        {"bar": 4, "name": "B"},
        {"bar": 6, "name": "outro"},
    ],
}

# 和弦：(名字, 低音, pad 的四個音)
CHORDS = [
    ("Am7",    "A2", ["A3", "C4", "E4", "G4"]),
    ("Fmaj7",  "F2", ["F3", "A3", "C4", "E4"]),
    ("Cadd9",  "C3", ["C4", "E4", "G4", "D5"]),
    ("G6",     "G2", ["G3", "B3", "D4", "E4"]),
] * 2

# 旋律：(小節, 拍起點, 音, 長度（拍）)
MELODY = [
    (0, 0, "A4", 2), (0, 2, "G4", 1), (0, 3, "E4", 1),
    (1, 0, "F4", 2), (1, 2, "A4", 1), (1, 3, "C5", 1),
    (2, 0, "E5", 2), (2, 2, "D5", 1), (2, 3, "C5", 1),
    (3, 0, "B4", 2), (3, 2, "G4", 1), (3, 3, "A4", 1),
    (4, 0, "A4", 2), (4, 2, "C5", 1), (4, 3, "E5", 1),
    (5, 0, "F5", 2), (5, 2, "E5", 1), (5, 3, "C5", 1),
    (6, 0, "D5", 2), (6, 2, "E5", 1), (6, 3, "G5", 1),
    (7, 0, "A5", 3.5),
]

# 鐘聲：(小節, 拍起點)。音高在 build 裡決定——每四小節換一次。
BELLS = [(0, 0), (1, 2), (2, 1.5), (3, 3), (4, 0), (5, 2), (6, 1.5), (7, 0), (7, 2)]

# 泡泡：絕對秒數
BUBBLES = [0.3, 2.9, 5.4, 7.8, 10.2, 12.6, 15.1, 17.4]


def build(mix, meta):
    """把整首曲子疊進 mix。"""
    from synth import hz

    # Pad：整個和弦鋪滿一小節，慢起音，左右輪流擺位，加一點失諧做出厚度
    for bar, (_, _, notes) in enumerate(CHORDS):
        t0 = bar * BAR
        for k, name in enumerate(notes):
            mix.tone(t0, BAR * 1.05, hz(name), 0.052,
                     [(1, 1.0), (2, 0.3), (3, 0.12)],
                     decay=0.05, attack=0.55, pan=-0.45 + 0.3 * k, detune=0.0016)

    # Bass：每小節第 1、3 拍
    for bar, (_, root, _) in enumerate(CHORDS):
        for beat in (0, 2):
            mix.tone(bar * BAR + beat * BEAT, BEAT * 1.7, hz(root), 0.20,
                     [(1, 1.0), (2, 0.22), (3, 0.06)], decay=1.5, attack=0.012)

    # 旋律：鋼琴感的音色，泛音多、衰減快
    for bar, beat, name, length in MELODY:
        mix.tone(bar * BAR + beat * BEAT, length * BEAT * 1.4, hz(name), 0.115,
                 [(1, 1.0), (2, 0.46), (3, 0.22), (4, 0.13), (5, 0.07), (6, 0.04)],
                 decay=0.95, attack=0.005, pan=-0.12)

    # 鐘聲：高音、短、擺右邊
    for bar, beat in BELLS:
        mix.tone(bar * BAR + beat * BEAT, 1.5,
                 hz("A5" if bar % 4 == 0 else "E5"), 0.045,
                 [(1, 1.0), (2.6, 0.4), (5.4, 0.14)],
                 decay=2.6, attack=0.002, pan=0.42)

    # 泡泡：左右輪流
    for t in BUBBLES:
        mix.bubble(t, 420, 1150, pan=-0.5 + 0.25 * (len(str(t)) % 3))

    # 鼓：第 1、3 拍 kick，八分 hihat（hihat 的 pan 左右交替）
    for bar in range(BARS):
        base = bar * BAR
        mix.kick(base, 0.42)
        mix.kick(base + 2 * BEAT, 0.30)
        for eighth in range(8):
            mix.hat(base + eighth * BEAT / 2,
                    0.075 if eighth % 2 else 0.045,
                    pan=0.3 - 0.6 * (eighth % 2), seed=bar * 8 + eighth)


def beats() -> dict:
    """給 PV 用的時間表（tomidi.py 也會拿來對齊）。"""
    return {
        "bpm": BPM, "beat_sec": round(BEAT, 4), "bar_sec": round(BAR, 4),
        "duration_sec": DUR,
        "beats_sec": [round(i * BEAT, 4) for i in range(int(DUR / BEAT) + 1)],
        "downbeats_sec": [round(b * BAR, 4) for b in range(BARS)],
        "sections": [{"t": s["bar"] * BAR, "name": s["name"], "bar": s["bar"]}
                     for s in META["sections"]],
        "chords": [{"t": round(b * BAR, 4), "name": c[0]} for b, c in enumerate(CHORDS)],
        "melody": [{"t": round(b * BAR + p * BEAT, 4), "note": n,
                    "dur": round(d * BEAT, 4)} for b, p, n, d in MELODY],
        "bells_sec": [round(b * BAR + p * BEAT, 4) for b, p in BELLS],
        "bubbles_sec": BUBBLES,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(beats(), ensure_ascii=False, indent=1))

#!/usr/bin/env python3
"""樂譜：深海練習曲（Deep Etude）。

這一層只懂音樂——和弦、旋律、配器、力度。它呼叫 synth.py 的 Mix 把音疊上去，
所以想換合成方式就改 synth.py，想改曲子就改這裡。

    python3 synth.py score.py -o bgm.wav
    python3 midi.py  score.py

════════════════════════════════════════════════════════════════════
  調這裡就好。改完存檔，雙擊「播放.command」就會重新生成然後播放。
════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

# ════════════════════════════════════════════════════════════════════
#  ① 速度與長度
# ════════════════════════════════════════════════════════════════════

BPM = 96.0            # 速度。60 慢、96 現在這樣、120 快、160 很急
BARS = 8              # 長度，單位是小節。一小節 4 拍。

# ════════════════════════════════════════════════════════════════════
#  ② 每個樂器的音量。0 = 關掉，1 = 現在這樣，2 = 兩倍
#     想單獨聽某一軌就把它留 1、其他全改 0
# ════════════════════════════════════════════════════════════════════

VOL = {
    "pad":    1.0,    # 鋪底的和弦長音——整首的地基
    "bass":   1.0,    # 低音，每小節第 1、3 拍
    "melody": 1.0,    # 主旋律（鋼琴音色）
    "bell":   1.0,    # 高音鐘聲點綴
    "bubble": 1.0,    # 泡泡音「啵」——鯨魚娘的主題音
    "kick":   1.0,    # 大鼓
    "hat":    1.0,    # hihat（擦擦聲）
}

# ════════════════════════════════════════════════════════════════════
#  ③ 和弦進行。四個一組，會自動重複到 BARS 那麼長
#     小調的幾組常見選擇，整組複製貼上就好：
#       Am7 / Fmaj7 / Cadd9 / G6     現在的——溫柔、有點漂流感
#       Am  / F     / C     / G      更單純，兒歌感
#       Am  / Dm    / G     / C      比較亮，收在 C 有解決感
#       Am  / Em    / F     / C      比較沉，往內收
#     每組是（名字, 低音, pad 的四個音）。音名後面那個數字是八度。
# ════════════════════════════════════════════════════════════════════

PROGRESSION = [
    ("Am7",    "A2", ["A3", "C4", "E4", "G4"]),
    ("Fmaj7",  "F2", ["F3", "A3", "C4", "E4"]),
    ("Cadd9",  "C3", ["C4", "E4", "G4", "D5"]),
    ("G6",     "G2", ["G3", "B3", "D4", "E4"]),
]

# ════════════════════════════════════════════════════════════════════
#  ④ 主旋律：(小節, 第幾拍, 音, 長度（拍）)
#     第幾拍從 0 算——0 是第 1 拍、2 是第 3 拍。小節從 0 算。
#     想換成自己哼的：先在小節 0 放幾個音試試，其他的註解掉。
# ════════════════════════════════════════════════════════════════════

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

# 鐘聲：(小節, 第幾拍)。音高跟著段落換，每四小節一次
BELLS = [(0, 0), (1, 2), (2, 1.5), (3, 3), (4, 0), (5, 2), (6, 1.5), (7, 0), (7, 2)]

# 泡泡：絕對秒數
BUBBLES = [0.3, 2.9, 5.4, 7.8, 10.2, 12.6, 15.1, 17.4]

# ════════════════════════════════════════════════════════════════════
#  以下不用改——由上面的參數算出來
# ════════════════════════════════════════════════════════════════════

BEAT = 60.0 / BPM          # 一拍幾秒
BAR = BEAT * 4             # 一小節幾秒
DUR = BAR * BARS           # 整首幾秒

# 和弦自動重複到 BARS 小節那麼長，所以改 BARS 不用動和弦
CHORDS = [PROGRESSION[b % len(PROGRESSION)] for b in range(BARS)]

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
        {"bar": BARS // 4, "name": "A"},
        {"bar": BARS // 2, "name": "B"},
        {"bar": BARS * 3 // 4, "name": "outro"},
    ],
}


def build(mix, meta):
    """把整首曲子疊進 mix。音量都乘上 VOL，所以那七個數字能單獨調每一軌。"""
    from synth import hz

    v = VOL

    # Pad：整個和弦鋪滿一小節，慢起音，左右輪流擺位，加一點失諧做出厚度
    for bar, (_, _, notes) in enumerate(CHORDS):
        t0 = bar * BAR
        for k, name in enumerate(notes):
            mix.tone(t0, BAR * 1.05, hz(name), 0.052 * v["pad"],
                     [(1, 1.0), (2, 0.3), (3, 0.12)],
                     decay=0.05, attack=0.55, pan=-0.45 + 0.3 * k, detune=0.0016)

    # Bass：每小節第 1、3 拍
    for bar, (_, root, _) in enumerate(CHORDS):
        for beat in (0, 2):
            mix.tone(bar * BAR + beat * BEAT, BEAT * 1.7, hz(root), 0.20 * v["bass"],
                     [(1, 1.0), (2, 0.22), (3, 0.06)], decay=1.5, attack=0.012)

    # 旋律：鋼琴感的音色，泛音多、衰減快。小節數超過 BARS 的音就跳過
    for bar, beat, name, length in MELODY:
        if bar >= BARS:
            continue
        mix.tone(bar * BAR + beat * BEAT, length * BEAT * 1.4, hz(name), 0.115 * v["melody"],
                 [(1, 1.0), (2, 0.46), (3, 0.22), (4, 0.13), (5, 0.07), (6, 0.04)],
                 decay=0.95, attack=0.005, pan=-0.12)

    # 鐘聲：高音、短、擺右邊
    for bar, beat in BELLS:
        if bar >= BARS:
            continue
        mix.tone(bar * BAR + beat * BEAT, 1.5,
                 hz("A5" if bar % 4 == 0 else "E5"), 0.045 * v["bell"],
                 [(1, 1.0), (2.6, 0.4), (5.4, 0.14)],
                 decay=2.6, attack=0.002, pan=0.42)

    # 泡泡：左右輪流
    for t in BUBBLES:
        if t < DUR:
            mix.bubble(t, 420, 1150, amp=0.16 * v["bubble"],
                       pan=-0.5 + 0.25 * (len(str(t)) % 3))

    # 鼓：第 1、3 拍 kick，八分 hihat（hihat 的 pan 左右交替）
    for bar in range(BARS):
        base = bar * BAR
        mix.kick(base, 0.42 * v["kick"])
        mix.kick(base + 2 * BEAT, 0.30 * v["kick"])
        for eighth in range(8):
            mix.hat(base + eighth * BEAT / 2,
                    (0.075 if eighth % 2 else 0.045) * v["hat"],
                    pan=0.3 - 0.6 * (eighth % 2), seed=bar * 8 + eighth)


def beats() -> dict:
    """給 PV 用的時間表（midi.py 也會拿來對齊）。"""
    return {
        "bpm": BPM, "beat_sec": round(BEAT, 4), "bar_sec": round(BAR, 4),
        "duration_sec": DUR,
        "beats_sec": [round(i * BEAT, 4) for i in range(int(DUR / BEAT) + 1)],
        "downbeats_sec": [round(b * BAR, 4) for b in range(BARS)],
        "sections": [{"t": s["bar"] * BAR, "name": s["name"], "bar": s["bar"]}
                     for s in META["sections"]],
        "chords": [{"t": round(b * BAR, 4), "name": c[0]} for b, c in enumerate(CHORDS)],
        "melody": [{"t": round(b * BAR + p * BEAT, 4), "note": n,
                    "dur": round(d * BEAT, 4)} for b, p, n, d in MELODY if b < BARS],
        "bells_sec": [round(b * BAR + p * BEAT, 4) for b, p in BELLS if b < BARS],
        "bubbles_sec": [t for t in BUBBLES if t < DUR],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(beats(), ensure_ascii=False, indent=1))

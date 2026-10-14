#!/usr/bin/env python3
"""合成器引擎。純標準庫，不依賴 numpy。

這一層只懂「聲音」——正弦、泛音、包絡、混音、寫檔。它不知道什麼是 BPM、
什麼是和弦、什麼是旋律，那些屬於樂譜（見 scores/）。

    python3 _lab/synth.py _lab/scores/deep-etude.py -o _lab/bgm.wav

樂譜是一個 Python 模組，裡面要有一個 build(mix, meta) 函式：
    meta 是自己定義的常數字典（BPM、拍長…），引擎只負責傳進去，
    並且會用 meta["duration"] 決定緩衝長度。
    build 裡呼叫 mix.tone() / mix.kick() / mix.hat() / mix.bubble() 把音疊上去。

為什麼不用 numpy：這台機器上沒有，而一首 20 秒的曲子只有幾百萬個樣本，
純 Python 夠快（實測四秒半）。引入 numpy 就要多一篇安裝說明，而這套的賣點是
「只要有 Python、Chrome 和 ffmpeg 就能跑」。真的到了幾分鐘的曲子再考慮換。
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import pathlib
import random
import struct
import sys
import wave

SR = 44100

# ── 音名 → 頻率（A4 = 440）─────────────────────────────
STEPS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
_cache: dict[str, float] = {}


def hz(name: str) -> float:
    """把 'A4'、'C#5' 這種音名換成頻率。"""
    if name not in _cache:
        pitch, octave = name[:-1], int(name[-1])
        _cache[name] = 440.0 * 2 ** ((STEPS[pitch] - 9) / 12 + (octave - 4))
    return _cache[name]


class Mix:
    """一條立體聲緩衝，音都疊進去，最後一次寫檔。"""

    def __init__(self, duration: float, sr: int = SR):
        self.sr = sr
        self.duration = duration
        self.n = int(duration * sr)
        self.left = [0.0] * self.n
        self.right = [0.0] * self.n

    # ── 通用音：正弦疊泛音 + 指數衰減 ──────────────────
    def tone(self, at, dur, freq, amp, harmonics, decay,
             attack=0.006, pan=0.0, detune=0.0):
        """harmonics 是 [(倍數, 相對音量), …]。detune 會多疊兩層微失諧的音，
        讓 pad 之類的長音變厚（兩層頻率差一點會產生拍頻）。"""
        n = min(int(dur * self.sr), self.n - int(at * self.sr))
        if n <= 0:
            return
        i0 = int(at * self.sr)
        inv_sr = 1.0 / self.sr
        gl = math.sqrt(0.5 * (1.0 - pan))          # 等功率 panning
        gr = math.sqrt(0.5 * (1.0 + pan))
        layers = ([(1.0, 1.0, harmonics)] if not detune else
                  [(1.0 - detune, 0.7, harmonics), (1.0 + detune, 0.7, harmonics)])
        for mul, gain, harm in layers:
            omega = [2 * math.pi * freq * mul * h * inv_sr for h, _ in harm]
            for i in range(n):
                t = i * inv_sr
                env = math.exp(-decay * t)
                if t < attack:
                    env *= t / attack
                elif t > dur - 0.04:               # 尾巴收乾淨，避免喀噠聲
                    env *= max(0.0, (dur - t) / 0.04)
                if env < 1e-5:
                    continue
                s = 0.0
                for k, (_, ha) in enumerate(harm):
                    s += ha * math.sin(omega[k] * i)
                s *= amp * env * gain
                self.left[i0 + i] += s * gl
                self.right[i0 + i] += s * gr

    # ── 打擊 ───────────────────────────────────────────
    def kick(self, at, amp=0.5, dur=0.22):
        """短促的低頻掃音：從 134Hz 掉到 42Hz。"""
        n = min(int(dur * self.sr), self.n - int(at * self.sr))
        if n <= 0:
            return
        i0, phase = int(at * self.sr), 0.0
        for i in range(n):
            t = i / self.sr
            f = 92.0 * math.exp(-26 * t) + 42.0
            phase += 2 * math.pi * f / self.sr
            s = math.sin(phase) * amp * math.exp(-19 * t)
            self.left[i0 + i] += s
            self.right[i0 + i] += s

    def hat(self, at, amp=0.1, pan=0.35, seed=0, dur=0.035):
        """hihat：短噪音。seed 固定，所以每次跑出來的檔案一模一樣。"""
        n = min(int(dur * self.sr), self.n - int(at * self.sr))
        if n <= 0:
            return
        i0 = int(at * self.sr)
        rnd = random.Random(seed)
        gl, gr = math.sqrt(0.5 * (1 - pan)), math.sqrt(0.5 * (1 + pan))
        for i in range(n):
            s = (rnd.random() * 2 - 1) * amp * math.exp(-95 * i / self.sr)
            self.left[i0 + i] += s * gl
            self.right[i0 + i] += s * gr

    def bubble(self, at, f0=420, f1=1150, dur=0.16, amp=0.16, pan=0.5):
        """泡泡：頻率往上滑的短正弦。鯨魚娘的主題音。"""
        n = min(int(dur * self.sr), self.n - int(at * self.sr))
        if n <= 0:
            return
        i0, phase = int(at * self.sr), 0.0
        gl, gr = math.sqrt(0.5 * (1 - pan)), math.sqrt(0.5 * (1 + pan))
        for i in range(n):
            t = i / self.sr
            u = t / dur
            phase += 2 * math.pi * f0 * (f1 / f0) ** u / self.sr
            env = math.sin(math.pi * min(1.0, u * 1.15)) ** 1.5 * math.exp(-2.2 * t)
            s = math.sin(phase) * amp * env
            self.left[i0 + i] += s * gl
            self.right[i0 + i] += s * gr

    # ── 輸出 ───────────────────────────────────────────
    def write(self, path, peak=0.84, fade_in=0.35, fade_out=2.2) -> float:
        """正規化到 peak 之後淡入淡出，寫 16-bit 立體聲 WAV。回傳實際峰值。"""
        top = max(max(abs(v) for v in self.left), max(abs(v) for v in self.right)) or 1.0
        gain = peak / top
        fi, fo = int(fade_in * self.sr), int(fade_out * self.sr)
        frames = bytearray()
        for i in range(self.n):
            g = gain
            if i < fi:
                g *= i / fi
            if i > self.n - fo:
                g *= (self.n - i) / fo
            l, r = self.left[i] * g, self.right[i] * g
            frames += struct.pack("<hh", int(l * 32767), int(r * 32767))
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(self.sr)
            w.writeframes(bytes(frames))
        return top * gain


def load_score(path: pathlib.Path):
    """把樂譜模組載進來。用 importlib 而不是 import，這樣可以直接吃路徑。

    先把這個檔所在的資料夾插進 sys.path，樂譜裡才能寫 `from synth import hz`
    ——不管樂譜放在 repo 的哪個角落都成立。"""
    here = str(pathlib.Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"讀不到樂譜：{path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise SystemExit(f"{path} 裡沒有 build(mix, meta) 函式")
    if not hasattr(mod, "META"):
        raise SystemExit(f"{path} 裡沒有 META 字典（至少要放 duration）")
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description="把一份樂譜合成成 WAV")
    ap.add_argument("score", type=pathlib.Path, help="樂譜模組，例如 _lab/scores/deep-etude.py")
    ap.add_argument("-o", "--out", type=pathlib.Path, help="輸出檔（預設跟樂譜同名的 .wav）")
    ap.add_argument("--sr", type=int, default=SR, help=f"取樣率（預設 {SR}）")
    a = ap.parse_args()

    mod = load_score(a.score)
    meta = dict(mod.META)
    mix = Mix(float(meta["duration"]), a.sr)
    mod.build(mix, meta)

    out = a.out or a.score.with_suffix(".wav")
    peak = mix.write(out)
    print(f"{out.name}　{meta['duration']:g} 秒　{mix.sr} Hz　"
          f"{meta.get('bpm', '?')} BPM　{out.stat().st_size/1024/1024:.1f} MB　峰值 {peak:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

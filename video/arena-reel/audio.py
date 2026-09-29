"""Synthesize the Reel soundtrack (minimal electro ~110 BPM + sound design) and the .srt file.

No voice-over: this environment has no text-to-speech. The VO text is burned in as captions
and exported to out/arena-reel.srt so a voice can be recorded/generated and dropped in later.
"""
import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
OUT = ROOT / "out"
SR, DUR = 48000, 50.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
t_all = np.arange(N) / SR

BPM = 110
BEAT = 60 / BPM
BAR = 4 * BEAT
SCENE_CUTS = [2, 8, 20, 25, 30, 39, 46]
TYPING = [  # (start, chars per second, chars) — mirrors index.html
    (9.0, 45, 56), (14.0, 45, 35), (20.3, 45, 28), (25.15, 95, 62), (25.15, 95, 41), (34.3, 50, 35),
]
DINGS = [1.1, 5.6, 15.1, 47.5]


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def lowpass(x, k):
    """Cheap one-pole low-pass (k in 0..1, smaller = darker)."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def env(n, attack, release):
    a = np.minimum(1, np.arange(n) / max(1, attack * SR))
    r = np.exp(-np.arange(n) / (release * SR))
    return a * r


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


music = np.zeros(N)
sfx = np.zeros(N)

# --- pad: Am – F – C – G, slow attack, gently detuned ---
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
bar_i = 0
t0 = 0.0
while t0 < DUR:
    chord = CHORDS[bar_i % 4]
    n = int(BAR * SR) + int(0.4 * SR)
    tt = np.arange(n) / SR
    sig = sum(np.sin(2 * np.pi * note(m) * tt) + 0.5 * np.sin(2 * np.pi * note(m) * 1.003 * tt + 1) for m in chord)
    shape = np.minimum(1, tt / 0.5) * np.minimum(1, (n / SR - tt) / 0.5)
    add(music, t0, sig * shape, 0.018)
    # bass on beats 1 and 3 (from the drop)
    if t0 >= 2 - 1e-6:
        for b in (0, 2):
            bn = int(BEAT * 1.6 * SR)
            bt = np.arange(bn) / SR
            f = note(chord[0] - 12)
            bass = (np.sin(2 * np.pi * f * bt) + 0.3 * np.sin(4 * np.pi * f * bt)) * env(bn, 0.005, 0.35)
            add(music, t0 + b * BEAT, bass, 0.16)
    bar_i += 1
    t0 += BAR

# --- drums ---
kn = int(0.35 * SR)
kt = np.arange(kn) / SR
kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-kt / 0.03)) / SR) * env(kn, 0.001, 0.12)
hn = int(0.05 * SR)
hat_src = np.diff(rng.standard_normal(hn + 1)) * env(hn, 0.0005, 0.012)

beat_t = 2.0
k = 0
while beat_t < DUR - 0.05:
    breakdown = 44.0 <= beat_t < 46.0
    if not breakdown:
        add(music, beat_t, kick, 0.55)
    if beat_t >= 8 and not breakdown:
        add(music, beat_t + BEAT / 2, hat_src, 0.09)  # off-beat 8ths
        if beat_t >= 30:  # 16ths build-up
            add(music, beat_t + BEAT / 4, hat_src, 0.045)
            add(music, beat_t + 3 * BEAT / 4, hat_src, 0.045)
    k += 1
    beat_t = 2.0 + k * BEAT

# hook riser 0–2 s
rn = int(2.0 * SR)
riser = lowpass(rng.standard_normal(rn), 0.08) * np.linspace(0, 1, rn) ** 2
add(music, 0, riser, 0.25)

# --- sound design ---
wn = int(0.5 * SR)
whoosh = lowpass(rng.standard_normal(wn), 0.12) * np.sin(np.linspace(0, np.pi, wn)) ** 2
for c in SCENE_CUTS:
    add(sfx, c - 0.12, whoosh, 0.22)

cn = int(0.012 * SR)
for start, cps, chars in TYPING:
    for i in range(chars):
        click = np.diff(rng.standard_normal(cn + 1)) * env(cn, 0.0003, 0.003)
        add(sfx, start + i / cps + rng.uniform(0, 0.008), click, rng.uniform(0.05, 0.09))

dn = int(0.9 * SR)
dt = np.arange(dn) / SR
ding = (np.sin(2 * np.pi * 1318.5 * dt) + 0.5 * np.sin(2 * np.pi * 1975.5 * dt)) * env(dn, 0.002, 0.25)
for d in DINGS:
    add(sfx, d, ding, 0.10)

# --- mix ---
mix = np.tanh(music * 1.2) * 0.9 + sfx
edge = int(0.02 * SR)
mix[:edge] *= np.linspace(0, 1, edge)
mix[-edge:] *= np.linspace(1, 0, edge)
mix /= np.max(np.abs(mix)) / 10 ** (-1 / 20)  # peak −1 dBFS

OUT.mkdir(exist_ok=True)
stereo = np.stack([mix, mix], axis=1)
with wave.open(str(OUT / "audio.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype("<i2").tobytes())

# --- SRT from the same caption timings ---
def ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

caps = json.loads((ROOT / "captions.json").read_text(encoding="utf-8"))
srt = "\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'] + .25)}\n{c['text']}\n" for i, c in enumerate(caps, 1))
(OUT / "arena-reel.srt").write_text(srt, encoding="utf-8")
print("audio + srt written")

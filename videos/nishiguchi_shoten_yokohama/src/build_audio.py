import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
tl = json.load(open("timeline.json"))

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)
def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)
def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)
def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]; buf[i:i + len(x)] += x
def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)

# ---------- narration ----------
voice = np.zeros(N)
for i, st in enumerate(tl["narration"], 1):
    x, sr = sf.read(f"tts/t{i}.wav")
    if sr != SR: x = resample_poly(x, SR // 1000, sr // 1000) if sr % 1000 == 0 else resample_poly(x, SR, sr)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    # gentle presence: slight high-shelf by mixing highpassed copy
    x = x + 0.18 * hp(x, 3500)
    f = int(0.006 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    add(voice, x, st)

# voice activity envelope for ducking
fr = int(0.01 * SR)
act = np.repeat([np.abs(voice[j:j + fr]).max() > 0.02 for j in range(0, N, fr)], fr)[:N].astype(float)
k = int(0.12 * SR)
act = np.convolve(act, np.ones(k) / k, mode="same")
act = np.clip(act * 1.6, 0, 1)

# ---------- BGM ----------
BPM = 120; beat = 60 / BPM; bar = beat * 4
music = np.zeros(N)
def kick():
    n = int(0.32 * SR); t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.11) * 0.9
def clap():
    n = int(0.22 * SR); x = rng.standard_normal(n)
    e = env(n, 0.001, 0.06) + 0.5 * env(n, 0.001, 0.012)
    return bp(x, 900, 5000) * e * 0.5
def hat(open_=False):
    n = int((0.12 if open_ else 0.04) * SR); x = rng.standard_normal(n)
    return hp(x, 7000, 3) * env(n, 0.0005, 0.05 if open_ else 0.012) * 0.22
def ep_note(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t / 0.08)
         + 0.12 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t / 0.04))
    return x * env(n, 0.003, 0.28)
def chord(notes, dur):
    return sum(ep_note(440 * 2 ** ((m - 69) / 12), dur) for m in notes) / len(notes)
def bass_note(midi, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = 440 * 2 ** ((midi - 69) / 12)
    x = 2 * ((f * t) % 1) - 1
    x = lp(x, 420, 2) + 0.6 * np.sin(2 * np.pi * f * t)
    return x * env(n, 0.004, 0.22) * 0.55

prog = [  # C  Am  F  G   (bright, upbeat)
    (48, [64, 67, 71, 74]),  # Cmaj9-ish
    (45, [64, 67, 72, 76]),  # Am7
    (41, [65, 69, 72, 76]),  # Fmaj7
    (43, [62, 67, 71, 74]),  # G
]
nbars = int(np.ceil(DUR / bar))
t0 = 0.0
for b in range(nbars):
    root, ch = prog[b % 4]
    bt = t0 + b * bar
    last = b == nbars - 1
    for i in range(4):
        add(music, kick(), bt + i * beat)
        if i in (1, 3): add(music, clap(), bt + i * beat)
        add(music, hat(), bt + i * beat + beat / 2)
        add(music, hat() * 0.5, bt + i * beat + beat / 4 * 3)
    if b % 2 == 1: add(music, hat(True), bt + 3.5 * beat)
    # syncopated stabs
    for off in (0.0, 1.5, 2.5) if not last else (0.0,):
        add(music, chord(ch, 0.6 if not last else 1.8) * 0.33, bt + off * beat)
    # bass: root on 1, 1.75 octave, 2.5, 3.5
    for off, oc in ((0, 0), (0.75, 12), (1.5, 0), (2.5, 0), (3.25, 12), (3.5, 7)) if not last else ((0, 0),):
        add(music, bass_note(root + oc, 0.3 if not last else 1.5), bt + off * beat)

# stop the groove for a clean ending: keep the last downbeat ring out
music = music / (np.max(np.abs(music)) + 1e-9)

# ---------- SFX ----------
sfx = np.zeros(N)
def whoosh(dur=0.34):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n)
    seg = 512
    for j in range(0, n, seg):
        p = j / n; fc = 600 + 5000 * p ** 1.5
        out[j:j + seg] = bp(x[j:j + seg + 0], fc * 0.7, min(fc * 1.4, 20000))[:len(out[j:j + seg])]
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return out * e * 0.35
def pop():
    n = int(0.25 * SR); t = np.arange(n) / SR
    f = 900 + 700 * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.07) * 0.35
for st in tl["transitions"]:
    add(sfx, whoosh(), st - 0.22)
for st in tl["pops"]:
    add(sfx, pop(), st)

# ---------- mix ----------
duck = 1 - 0.62 * act
mix = voice * 1.0 + music * 0.20 * duck + sfx * 0.7
# fades
fi = int(0.05 * SR); mix[:fi] *= np.linspace(0, 1, fi)
fo = int(0.9 * SR); mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.89
sf.write("mix_raw.wav", np.stack([mix, mix], 1), SR)
sf.write("voice_only.wav", voice, SR)
print("ok")

"""Música de fondo y efectos para el video promocional (40.5 s, 80 BPM, re mayor).

Cada compás dura 3 s, igual que cada beneficio del video, así los cambios de
acorde caen justo cuando aparece un beneficio nuevo.

    python3 musica.py salida.wav
"""
import sys
import wave

import numpy as np

SR = 48000
DUR = 40.5
BEAT = 0.75
BAR = 3.0
N = int(SR * DUR)
rng = np.random.default_rng(3)

music = np.zeros((2, N))  # pad + arpegio + efectos (pasan por la reverberación)
dry = np.zeros((2, N))    # batería y bajo (sin reverberación)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    buf[0, i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 - pan))
    buf[1, i:i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 + pan))


def tt(d):
    return np.arange(int(d * SR)) / SR


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


# Re – La – Si menor – Sol (I–V–vi–IV)
PAD = [[50, 57, 62, 66], [52, 57, 61, 64], [54, 59, 62, 66], [55, 59, 62, 67]]
ARP = [[62, 66, 69, 74], [61, 64, 69, 73], [62, 66, 71, 74], [62, 67, 71, 74]]
BASS = [38, 33, 35, 31]
PATTERN = [0, 1, 2, 3, 2, 1, 2, 1]

N_BARS = 13  # 0–39 s; luego un acorde final hasta 40.5 s


def pad_note(m, d):
    t = tt(d)
    env = np.minimum(t / 0.5, 1) * np.minimum((d - t) / 0.9, 1).clip(0, 1)
    out = np.zeros_like(t)
    for cents in (-6, 0, 6):
        f = midi(m) * 2 ** (cents / 1200)
        out += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return out * env / 3


def pluck(m, d=1.2):
    t = tt(d)
    f = midi(m)
    env = np.minimum(t / 0.004, 1) * np.exp(-t / 0.32)
    tone = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08) \
        + 0.12 * np.sin(2 * np.pi * 3.98 * f * t) * np.exp(-t / 0.04)
    return tone * env


def bass_note(m, d):
    t = tt(d)
    f = midi(m)
    env = np.minimum(t / 0.02, 1) * np.minimum((d - t) / 0.2, 1).clip(0, 1) * (0.6 + 0.4 * np.exp(-t / 0.6))
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)) * env


def kick():
    t = tt(0.45)
    f = 45 + 80 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)


def snare():
    t = tt(0.3)
    noise = np.diff(rng.standard_normal(len(t) + 1)) * 0.5
    return noise * np.exp(-t / 0.07) + 0.4 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05)


def hat():
    t = tt(0.08)
    noise = np.diff(rng.standard_normal(len(t) + 2), 2) * 0.25
    return noise * np.exp(-t / 0.02)


def bell(f, d=1.2, tau=0.35):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.1)) \
        * np.minimum(t / 0.003, 1) * np.exp(-t / tau)


def pop_sfx():
    t = tt(0.15)
    f = 500 + 900 * (t / 0.15)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045)


def whoosh(d=0.6):
    t = tt(d)
    noise = smooth(rng.standard_normal(len(t)), 9) - smooth(rng.standard_normal(len(t)), 60) * 0.5
    env = np.sin(np.pi * (t / d) ** 1.6) ** 2
    return noise * env


def tap_sfx():
    t = tt(0.1)
    return np.sin(2 * np.pi * np.cumsum(260 - 120 * t / 0.1) / SR) * np.exp(-t / 0.025) \
        + rng.standard_normal(len(t)) * np.exp(-t / 0.006) * 0.3


# ---- Música ----
for b in range(N_BARS):
    c = b % 4
    start = b * BAR
    last = b == N_BARS - 1
    length = (DUR - start) if last else BAR + 0.9
    for k, m in enumerate(PAD[c]):
        add(music, start, pad_note(m, length), 0.035, pan=(-0.4, 0.4, -0.2, 0.2)[k])
    calm = start < 6 or 30 <= start < 34.5
    for e in range(8):
        if calm and e % 2:
            continue
        add(music, start + e * BEAT / 2, pluck(ARP[c][PATTERN[e]]), 0.075 if e % 2 else 0.1,
            pan=(-0.35 if e % 2 else 0.35))
    if start >= 6:
        add(dry, start, bass_note(BASS[c], 3.0 if last else length - 0.6), 0.16)

# Final: acorde de Re arpegiado que se deja sonar
END = N_BARS * BAR
for k, m in enumerate(ARP[0] + [78]):
    add(music, END + k * 0.1, pluck(m, DUR - END), 0.08, pan=-0.3 + 0.15 * k)
add(dry, END, bass_note(BASS[0], DUR - END), 0.14)

# Batería: entra con los beneficios, se retira en el agradecimiento y vuelve en el cierre
for b in range(N_BARS):
    start = b * BAR
    if start < 6:
        continue
    for beat in range(4):
        tb = start + beat * BEAT
        if 30 <= tb < 34.5:
            continue
        if beat == 0:
            add(dry, tb, kick(), 0.42)
        if beat == 2:
            add(dry, tb + BEAT / 2, kick(), 0.32)
        if beat in (1, 3):
            add(dry, tb, snare(), 0.12)
        add(dry, tb + BEAT / 2, hat(), 0.05, pan=0.3)
        add(dry, tb, hat(), 0.025, pan=0.3)
add(dry, END, kick(), 0.4)

# ---- Efectos sincronizados con la animación ----
add(music, 0.15, pop_sfx(), 0.12)
for t in (3.6, 5.85, 23.85, 34.35):
    add(music, t, whoosh(), 0.05)
for i in range(6):
    add(music, 6.05 + 3 * i, pop_sfx(), 0.11, pan=(-0.2 if i % 2 else 0.2))
for i in range(6):
    add(music, 24.45 + 0.16 * i, bell(1568 + 120 * i, 0.4, 0.06), 0.05)
add(music, 26.6, bell(midi(86), 1.6, 0.5), 0.07)
add(music, 26.6, bell(midi(90), 1.6, 0.5), 0.05)
add(music, 30.05, pop_sfx(), 0.08)
add(dry, 36.98, tap_sfx(), 0.3)
for k, m in enumerate([86, 88, 90, 93, 95, 98]):
    add(music, 37.05 + 0.045 * k, bell(midi(m), 0.8, 0.18), 0.045, pan=-0.5 + 0.2 * k)

# ---- Reverberación sencilla (convolución con ruido que decae) ----
ir_t = tt(2.2)
ir = np.stack([smooth(rng.standard_normal(len(ir_t)), 6) * np.exp(-ir_t / 0.55) for _ in range(2)])
ir[:, : int(0.018 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
size = 1 << int(np.ceil(np.log2(N + ir.shape[1])))
wet = np.fft.irfft(np.fft.rfft(music, size) * np.fft.rfft(ir, size), size)[:, :N]

mix = music + dry + wet * 0.35
fade_in = np.minimum(np.arange(N) / (0.2 * SR), 1)
fade_out = np.clip((DUR - np.arange(N) / SR) / 1.2, 0, 1)
mix *= fade_in * fade_out
mix = np.tanh(mix * 1.3) / 1.3
mix *= 0.89 / np.abs(mix).max()

out = sys.argv[1] if len(sys.argv) > 1 else "musica.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype("<i2").tobytes())
print("listo:", out)

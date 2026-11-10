"""Procedural sound design (no samples, no copyright issues).

All sounds are synthesised with numpy. A Mixer places events on a stereo
timeline, then adds a shared reverb bus and a gentle master limiter.
"""
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(11)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_ad(n, a, d, curve=4.0):
    """attack (s) then exponential-ish decay to 0 over d (s)."""
    na = max(1, int(a * SR))
    out = np.zeros(n)
    out[:min(na, n)] = np.linspace(0, 1, na)[:n]
    if n > na:
        k = np.arange(n - na) / max(1, int(d * SR))
        out[na:] = np.exp(-curve * k)
    return out


def bandnoise(dur, lo, hi, seed=None):
    """White noise band-limited in the frequency domain."""
    rng = np.random.default_rng(seed) if seed is not None else _rng
    n = int(dur * SR)
    spec = np.fft.rfft(rng.normal(0, 1, n))
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = np.clip((f - lo) / (lo * 0.3 + 1), 0, 1) * np.clip((hi - f) / (hi * 0.3 + 1), 0, 1)
    x = np.fft.irfft(spec * mask, n)
    return x / (np.abs(x).max() + 1e-9)


def sweep(dur, f0, f1, shape="exp"):
    t = t_axis(dur)
    if shape == "exp":
        f = f0 * (f1 / f0) ** (t / dur)
    else:
        f = f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------------------------------------------------------------- one-shots
def step_light(seed=0):
    """Quick sneaker tap (for the runner)."""
    d = 0.09
    n = int(d * SR)
    x = bandnoise(d, 1200, 7000, seed) * env_ad(n, 0.001, 0.025)
    x += 0.5 * np.sin(2 * np.pi * 180 * t_axis(d)) * env_ad(n, 0.001, 0.03)
    return x * 0.5


def step_heavy(seed=0):
    """Deliberate, grounded footstep: low thump + gritty scuff."""
    d = 0.32
    n = int(d * SR)
    t = t_axis(d)
    f = 95 * np.exp(-t * 18) + 48
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.002, 0.13)
    scuff = bandnoise(d, 300, 3500, seed) * env_ad(n, 0.002, 0.05)
    return thump * 0.9 + scuff * 0.35


def tick(freq=2600, amp=0.25):
    d = 0.03
    n = int(d * SR)
    return np.sin(2 * np.pi * freq * t_axis(d)) * env_ad(n, 0.0005, 0.006) * amp


def glitch(seed=0):
    d = 0.12
    n = int(d * SR)
    rng = np.random.default_rng(seed)
    x = bandnoise(d, 2000, 12000, seed) * (rng.random(n) < 0.3)
    x += 0.4 * np.sign(np.sin(2 * np.pi * rng.uniform(60, 140) * t_axis(d)))
    return x * env_ad(n, 0.001, 0.05) * 0.35


def power_down(dur=2.4):
    """Descending electric hum: energy draining out."""
    n = int(dur * SR)
    t = t_axis(dur)
    s = sweep(dur, 340, 38)
    s2 = sweep(dur, 680, 76) * 0.3
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * (14 - 10 * t / dur) * t)
    e = np.minimum(1, t / 0.08) * (1 - t / dur) ** 1.5
    return (s + s2) * trem * e * 0.45


def whoosh(dur=0.9, lo=300, hi=5000, peak=0.65, seed=None):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    e = np.where(t < peak, (t / peak) ** 2.2, ((1 - t) / (1 - peak)) ** 1.6)
    x = bandnoise(dur, lo, hi, seed)
    # moving band feel: crossfade low and high
    xl = bandnoise(dur, lo, lo * 4, None if seed is None else seed + 1)
    mixc = np.clip(t / peak, 0, 1)
    return (xl * (1 - mixc) + x * mixc) * e * 0.6


def heartbeat():
    d = 0.75
    out = np.zeros(int(d * SR))
    for off, a in ((0.0, 1.0), (0.22, 0.7)):
        dd = 0.25
        n = int(dd * SR)
        t = t_axis(dd)
        f = 70 * np.exp(-t * 10) + 38
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.004, 0.1) * a
        i = int(off * SR)
        out[i:i + n] += b
    return out * 0.95


def sparkle(dur=1.8, density=90, seed=5):
    """Granular shimmer for the dissolve into embers."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n + SR)
    count = int(dur * density)
    for _ in range(count):
        st = int(rng.uniform(0, dur) ** 1.3 / dur ** 0.3 * SR)
        f = rng.uniform(2500, 9000)
        dd = rng.uniform(0.02, 0.09)
        m = int(dd * SR)
        g = np.sin(2 * np.pi * f * t_axis(dd)) * env_ad(m, 0.001, dd * 0.5)
        out[st:st + m] += g * rng.uniform(0.05, 0.18) * (1 - st / (n + 1)) ** 0.5
    out[:n] += bandnoise(dur, 4000, 14000, seed) * np.linspace(1, 0, n) ** 2 * 0.08
    return out


def riser(dur=3.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    nz = bandnoise(dur, 400, 9000)
    # sweep a resonance-ish tone up
    tone = sweep(dur, 120, 900) * 0.25 + sweep(dur, 180, 1350) * 0.12
    e = t ** 2.5
    return (nz * 0.5 + tone) * e * 0.55


def boom(dur=3.5):
    n = int(dur * SR)
    t = t_axis(dur)
    f = 110 * np.exp(-t * 6) + 34
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.4)
    crack = bandnoise(dur, 80, 6000) * np.exp(-t * 7)
    tail = bandnoise(dur, 60, 900) * np.exp(-t * 1.2) * 0.25
    x = sub * 1.0 + crack * 0.55 + tail
    x[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return x * 0.9


def text_hit(seed=0):
    d = 1.2
    n = int(d * SR)
    t = t_axis(d)
    f = 70 * np.exp(-t * 9) + 45
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
    snap = bandnoise(d, 1500, 9000, seed) * np.exp(-t * 30)
    ring = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-t * 3) * 0.06
    return low * 0.7 + snap * 0.35 + ring


def drone(dur, rise_at=None, seed=2):
    """Dark pad bed. Slowly thickens; optional pitch rise towards rise_at."""
    n = int(dur * SR)
    t = t_axis(dur)
    base = 55.0
    bend = np.ones(n)
    if rise_at is not None:
        bend = 1 + 0.06 * np.clip((t - (rise_at - 6)) / 6, 0, 1) ** 2
    ph = 2 * np.pi * np.cumsum(base * bend) / SR
    x = (np.sin(ph) + 0.5 * np.sin(ph * 1.5 + 0.3) + 0.25 * np.sin(ph * 2.0)
         + 0.12 * np.sin(ph * 3.01))
    x *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * t)
    air = bandnoise(dur, 150, 1200, seed) * 0.12
    return (x * 0.18 + air)


# ----------------------------------------------------------------- mixer
class Mixer:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.dry = np.zeros((self.n, 2))
        self.wet = np.zeros((self.n, 2))

    def add(self, t, x, gain=1.0, pan=0.0, rev=0.2):
        i = int(t * SR)
        if i >= self.n or i + len(x) <= 0:
            return
        if i < 0:
            x, i = x[-i:], 0
        x = x[:self.n - i] * gain
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        st = np.stack([x * l, x * r], 1) * 1.414
        self.dry[i:i + len(x)] += st
        self.wet[i:i + len(x)] += st * rev

    def add_bed(self, x, gain=1.0, start=0.0, fade_in=1.5, fade_out=None, stop=None):
        x = x.copy()
        fi = int(fade_in * SR)
        x[:fi] *= np.linspace(0, 1, fi)
        if fade_out:
            end = len(x) if stop is None else int((stop - start) * SR)
            fo = int(fade_out * SR)
            x[max(0, end - fo):end] *= np.linspace(1, 0, min(fo, end))
            x[end:] = 0
        self.add(start, x, gain, 0.0, 0.15)

    def reverb(self, ir_len=2.8):
        n = int(ir_len * SR)
        rng = np.random.default_rng(1)
        t = np.arange(n) / SR
        out = np.zeros_like(self.wet)
        m = self.n + n
        for c in range(2):
            ir = rng.normal(0, 1, n) * np.exp(-t * 2.4)
            ir[:int(0.012 * SR)] = 0
            ir /= np.sqrt((ir ** 2).sum())
            y = np.fft.irfft(np.fft.rfft(self.wet[:, c], m) * np.fft.rfft(ir, m), m)
            out[:, c] = y[:self.n]
        return out

    def render(self, path, master=0.9):
        x = self.dry + self.reverb() * 0.6
        # gentle high-pass on master (remove DC / rumble below ~25 Hz)
        for c in range(2):
            X = np.fft.rfft(x[:, c])
            f = np.fft.rfftfreq(self.n, 1 / SR)
            X *= np.clip(f / 25.0, 0, 1)
            x[:, c] = np.fft.irfft(X, self.n)
        peak = np.abs(x).max() + 1e-9
        x = x / peak * master
        x = np.tanh(x * 1.2) / np.tanh(1.2)   # soft limiter
        pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())


def beep(freq=880, dur=0.18, amp=0.4):
    n = int(dur * SR)
    t = t_axis(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    return x * env_ad(n, 0.003, dur * 0.8, 2.0) * amp


def lock_on(seed=0):
    """Tense two-tone 'target acquired' zing for Ego's stare."""
    d = 0.45
    n = int(d * SR)
    t = t_axis(d)
    x = sweep(d, 600, 1900) * 0.5 + np.sin(2 * np.pi * 95 * t) * 0.6
    x *= env_ad(n, 0.005, 0.25, 3.0)
    return x * 0.5 + bandnoise(d, 3000, 10000, seed) * env_ad(n, 0.002, 0.08) * 0.15


def chime(freq=660, amp=0.35):
    d = 1.4
    n = int(d * SR)
    t = t_axis(d)
    x = (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.0 * t)
         + 0.2 * np.sin(2 * np.pi * freq * 3.0 * t))
    return x * env_ad(n, 0.004, 0.6, 4.0) * amp


def body_fall():
    d = 0.9
    n = int(d * SR)
    t = t_axis(d)
    scuff = bandnoise(d, 400, 5000, 4) * np.exp(-t * 9) * 0.5
    f = 80 * np.exp(-t * 12) + 40
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.003, 0.2)
    x = np.zeros(n)
    x += scuff
    i = int(0.18 * SR)
    x[i:] += thud[:n - i] * 1.1
    return x

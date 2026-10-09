"""Genera todos los efectos de sonido del programa (sin archivos externos).

Los sonidos se sintetizan con matemáticas puras: el «clic» de las piezas imita
dos transitorios de plástico (contacto + encaje) filtrados por resonancias
agudas, como cuando un bloque se encaja sobre otro.

Uso:  python generar_sonidos.py      (crea assets/sounds/*.wav)
Si prefieres el sonido real, graba tus propios bloques y reemplaza
assets/sounds/click_1.wav … click_4.wav por tus grabaciones.
"""
import math, random, struct, wave
from pathlib import Path

SR = 44100
OUT = Path(__file__).resolve().parent / "assets" / "sounds"


def save(name, data, sr=SR, gain=0.9):
    peak = max(1e-9, max(abs(x) for x in data))
    k = gain / peak
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * k)) * 32767)) for x in data))


def biquad_bp(x, f, q, sr=SR):
    w0 = 2 * math.pi * f / sr; a = math.sin(w0) / (2 * q); c = math.cos(w0)
    b0, b1, b2, a0, a1, a2 = a, 0, -a, 1 + a, -2 * c, 1 - a
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = [0.0] * len(x); x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        o = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, o; y[i] = o
    return y


def lowpass(x, f, sr=SR):
    a = 1 - math.exp(-2 * math.pi * f / sr); y = []; p = 0.0
    for v in x:
        p += a * (v - p); y.append(p)
    return y


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def silence(sec, sr=SR):
    return [0.0] * int(sec * sr)


def at(track, sec, sr=SR):
    return silence(sec, sr) + track


def tone(f, dur, decay, sr=SR, partials=((1, 1.0),), f_end=None, attack=0.003, vol=1.0):
    n = int(dur * sr); out = []; ph = [0.0] * len(partials)
    for i in range(n):
        t = i / sr
        ff = f if f_end is None else f * (f_end / f) ** (t / dur)
        env = min(1, t / attack) * math.exp(-t / decay)
        s = 0.0
        for j, (m, a) in enumerate(partials):
            ph[j] += 2 * math.pi * ff * m / sr
            s += a * math.sin(ph[j]) * (math.exp(-t / (decay / (1 + j))) if j else 1)
        out.append(s * env * vol)
    return out


def noise(dur, seed, sr=SR):
    r = random.Random(seed)
    return [r.uniform(-1, 1) for _ in range(int(dur * sr))]


def click(seed):
    """Encaje de dos bloques de plástico."""
    r = random.Random(seed)
    def transient(amp, f1, f2, tau):
        n = noise(0.05, r.random())
        n = [v * math.exp(-i / (SR * tau)) for i, v in enumerate(n)]
        return [a + b for a, b in zip([amp * v for v in biquad_bp(n, f1, 7)], [amp * .6 * v for v in biquad_bp(n, f2, 4)])]
    first = transient(0.45, r.uniform(2800, 3400), r.uniform(5200, 6400), 0.0016)
    snap = transient(1.0, r.uniform(3600, 4300), r.uniform(1600, 2000), 0.0022)
    body = tone(r.uniform(1150, 1350), 0.05, 0.007, vol=0.25)
    gap = r.uniform(0.009, 0.016)
    return mix(first, at(snap, gap), at(body, gap)) + silence(0.03)


def main():
    for i in range(1, 5):
        save(f"click_{i}", click(i * 17), gain=0.85)
    save("pop", tone(950, 0.09, 0.03, f_end=520, partials=((1, 1), (2, .2))), gain=.7)
    save("hover", tone(1800, 0.03, 0.006), gain=.25)
    sl = noise(0.16, 3); env = [math.sin(math.pi * i / len(sl)) ** 2 for i in range(len(sl))]
    sl = lowpass([a * b for a, b in zip(sl, env)], 1800)
    save("slide", mix(sl, at(click(99), 0.1)), gain=.55)
    save("stamp", mix(tone(190, 0.14, 0.04, f_end=80, partials=((1, 1), (2, .3))), at(click(7), 0.035)), gain=.85)
    save("state", mix(tone(784, 0.35, 0.12, partials=((1, 1), (3, .15))), at(tone(1047, 0.4, 0.14, partials=((1, 1), (3, .12))), 0.07)), gain=.5)
    th = silence(1.2)
    rr = random.Random(5)
    for k in range(9):
        b = tone(rr.choice([880, 988, 1175, 1319, 1568]), 0.09, 0.025, partials=((1, 1), (2, .25)))
        th = mix(th, at(b, k * 0.13))
    save("think", th, gain=.45)
    marimba = lambda f, d=0.9: tone(f, d, 0.22, partials=((1, 1), (4, .35), (9.9, .08)))
    save("success", mix(*[at(marimba(f), i * 0.09) for i, f in enumerate([523.25, 659.25, 783.99, 1046.5, 1318.5])]), gain=.8)
    save("fail", mix(tone(330, 0.3, 0.12, partials=((1, 1), (3, .3)), f_end=300), at(tone(247, 0.45, 0.18, partials=((1, 1), (3, .3)), f_end=220), 0.2)), gain=.6)
    w = noise(0.45, 11); env = [math.sin(math.pi * i / len(w)) ** 1.5 for i in range(len(w))]
    w = biquad_bp([a * b for a, b in zip(w, env)], 1200, 0.8)
    save("whoosh", w, gain=.4)
    chord = mix(*[marimba(f, 1.4) for f in (392, 523.25, 659.25)])
    save("build_done", mix(chord, at(marimba(783.99), 0.18), at(marimba(1046.5, 1.3), 0.3)), gain=.8)
    music()
    print("Sonidos generados en", OUT)


def music():
    """Música de fondo suave en bucle (pentatónica, 120 bpm, 16 compases)."""
    sr = 22050; beat = 0.5; bars = 16; total = int(bars * 4 * beat * sr)
    buf = [0.0] * total
    def add(sig, t):
        s = int(t * sr)
        for i, v in enumerate(sig):
            j = s + i
            if j < total: buf[j] += v
            else: buf[j - total] += v       # envolver para que el bucle sea continuo
    pl = lambda f, d, v: tone(f, d, d / 3, sr=sr, partials=((1, 1), (4, .25), (2, .1)), vol=v)
    pad = lambda f, d, v: [x * min(1, i / (sr * .3)) * min(1, (len(range(int(d * sr))) - i) / (sr * .4)) for i, x in enumerate(tone(f, d, 99, sr=sr, partials=((1, 1), (2, .3)), vol=v))]
    prog = [(261.63, 329.63, 392.0), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66)]
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    r = random.Random(42)
    for bar in range(bars):
        ch = prog[bar % 4]; t0 = bar * 4 * beat
        for f in ch:
            add(pad(f / 2, 4 * beat, 0.06), t0)
        add(pl(ch[0] / 4, 0.9, 0.22), t0); add(pl(ch[0] / 4, 0.9, 0.16), t0 + 2 * beat)
        for k in range(8):
            if r.random() < 0.62:
                f = r.choice([x for x in scale if any(abs(math.log2(x / c)) % 1 < 0.01 or True for c in ch)])
                add(pl(f, 0.6, 0.11 if k % 2 == 0 else 0.08), t0 + k * beat / 2)
    save("music", lowpass(buf, 5000, sr=sr), sr=sr, gain=.55)


if __name__ == "__main__":
    main()

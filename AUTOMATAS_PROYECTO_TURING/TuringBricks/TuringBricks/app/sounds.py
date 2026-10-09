"""Administrador de sonidos con grupos de reproducción (varios clics a la vez)."""
import random
from ursina import Audio
from .config import SOUNDS


class Sounds:
    def __init__(self):
        self.enabled = True
        self.music_on = True
        self.pools = {}
        self.idx = {}
        self.last = {}
        self.t = 0.0
        for name, n in (("click_1", 3), ("click_2", 3), ("click_3", 3), ("click_4", 3), ("pop", 3), ("hover", 2),
                        ("slide", 3), ("stamp", 3), ("state", 2), ("think", 1), ("success", 1), ("fail", 1),
                        ("whoosh", 2), ("build_done", 1)):
            path = SOUNDS / f"{name}.wav"
            self.pools[name] = [Audio(path, autoplay=False) for _ in range(n)] if path.exists() else []
            self.idx[name] = 0
        mp = SOUNDS / "music.wav"
        self.music = Audio(mp, autoplay=False, loop=True, volume=.32) if mp.exists() else None

    def play(self, name, volume=1.0, pitch=1.0, min_gap=0.0):
        if not self.enabled or not self.pools.get(name):
            return
        if min_gap and self.t - self.last.get(name, -9) < min_gap:
            return
        self.last[name] = self.t
        pool = self.pools[name]
        a = pool[self.idx[name] % len(pool)]; self.idx[name] += 1
        try:
            a.volume = volume; a.pitch = pitch; a.play()
        except Exception:
            pass

    def click(self, volume=.9, min_gap=0.0):
        self.play(f"click_{random.randint(1, 4)}", volume, random.uniform(.92, 1.1), min_gap)

    def stop(self, name):
        for a in self.pools.get(name, []):
            try: a.stop()
            except Exception: pass

    def set_music(self, on):
        self.music_on = on
        if not self.music: return
        try:
            if on: self.music.play()
            else: self.music.stop()
        except Exception:
            pass

    def update(self, dt):
        self.t += dt

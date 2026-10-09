"""Interpolaciones simples controladas por el programa (se pueden completar al instante)."""
import math
from ursina import Vec3, time, color

def out_cubic(t): return 1 - (1 - t) ** 3
def in_out_cubic(t): return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def linear(t): return t
def out_back(t, s=1.9): return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def in_quad(t): return t * t

def out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d: return n * t * t
    if t < 2 / d: t -= 1.5 / d; return n * t * t + .75
    if t < 2.5 / d: t -= 2.25 / d; return n * t * t + .9375
    t -= 2.625 / d; return n * t * t + .984375

EASE = {"out_cubic": out_cubic, "in_out": in_out_cubic, "linear": linear, "out_back": out_back, "out_bounce": out_bounce, "in_quad": in_quad}


def _snap(cur):
    if isinstance(cur, (int, float)):
        return cur
    return tuple(cur)


class Tween:
    __slots__ = ("obj", "attr", "a", "b", "dur", "t", "ease", "done", "delay", "on_start", "started")

    def __init__(self, obj, attr, b, dur, ease="out_cubic", delay=0.0, done=None, a=None, on_start=None):
        self.obj, self.attr, self.b, self.dur = obj, attr, b, max(1e-4, dur)
        self.a, self.t, self.ease, self.done, self.delay = a, 0.0, EASE[ease] if isinstance(ease, str) else ease, done, delay
        self.on_start, self.started = on_start, False


class Tweener:
    def __init__(self):
        self.items: list[Tween] = []
        self.calls: list = []        # (delay_restante, función)

    def to(self, obj, attr, b, dur, ease="out_cubic", delay=0.0, done=None, a=None, on_start=None):
        self.items = [x for x in self.items if not (x.obj is obj and x.attr == attr)] if delay == 0 else self.items
        tw = Tween(obj, attr, b, dur, ease, delay, done, a, on_start)
        self.items.append(tw)
        return tw

    def call(self, delay, fn):
        self.calls.append([delay, fn])

    def cancel(self, obj=None):
        self.items = [x for x in self.items if obj is not None and x.obj is not obj]
        if obj is None:
            self.calls = []

    def _apply(self, tw, k):
        a, b = tw.a, tw.b
        if isinstance(b, (int, float)):
            v = a + (b - a) * k
        elif len(b) == 4:
            v = color.rgba(*(a[i] + (b[i] - a[i]) * k for i in range(4)))
        else:
            v = Vec3(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)
        setattr(tw.obj, tw.attr, v)

    def update(self, dt=None):
        dt = time.dt if dt is None else dt
        for c in self.calls[:]:
            c[0] -= dt
            if c[0] <= 0:
                self.calls.remove(c)
                c[1]()
        for tw in self.items[:]:
            if tw.delay > 0:
                tw.delay -= dt
                if tw.delay > 0:
                    continue
            if not tw.started:
                tw.started = True
                if tw.on_start: tw.on_start()
                if tw.a is None:
                    tw.a = _snap(getattr(tw.obj, tw.attr))
            tw.t += dt
            k = min(1.0, tw.t / tw.dur)
            self._apply(tw, tw.ease(k))
            if k >= 1:
                if tw in self.items:
                    self.items.remove(tw)
                if tw.done: tw.done()

    def finish_all(self):
        """Completa todo de inmediato (para «Saltar»)."""
        guard = 0
        while (self.items or self.calls) and guard < 20:
            guard += 1
            calls, self.calls = self.calls, []
            for c in calls:
                c[1]()
            items, self.items = self.items, []
            for tw in items:
                if not tw.started and tw.on_start: tw.on_start()
                if tw.a is None:
                    tw.a = _snap(getattr(tw.obj, tw.attr))
                self._apply(tw, 1.0)
                if tw.done: tw.done()


tweener = Tweener()

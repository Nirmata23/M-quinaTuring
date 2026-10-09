"""Generación procedural de bloques de construcción tipo «brick».

Unidades: 1 = ancho de un botón (stud).  Altura de bloque = 1.2, placa = 0.4.
Las mallas se generan una sola vez y se reutilizan (caché).
"""
import math
from ursina import Mesh, Vec3, color as ucolor

BRICK_H = 1.2
PLATE_H = 0.4
STUD_R = 0.3
STUD_H = 0.18
SEG = 12

_cache = {}


class MeshBuilder:
    """Acumula geometría (vértices, normales, colores) para crear una sola malla."""

    def __init__(self):
        self.v, self.n, self.c, self.t = [], [], [], []

    def _quad(self, a, b, c, d, nrm, col):
        i = len(self.v)
        self.v += [a, b, c, d]; self.n += [nrm] * 4; self.c += [col] * 4
        self.t += [i, i + 1, i + 2, i, i + 2, i + 3]

    def box(self, x, y, z, w, h, d, col, shade=True, bottom=False):
        """Caja con esquina mínima (x, y, z) y tamaño (w, h, d)."""
        X, Y, Z = x + w, y + h, z + d
        dark = tuple(v * (0.82 if shade else 1) for v in col[:3]) + (col[3],)
        P = Vec3
        self._quad(P(x, Y, z), P(x, Y, Z), P(X, Y, Z), P(X, Y, z), (0, 1, 0), col)          # arriba
        if bottom:
            self._quad(P(x, y, z), P(X, y, z), P(X, y, Z), P(x, y, Z), (0, -1, 0), dark)
        # laterales: arriba con color pleno, abajo un poco más oscuro (oclusión falsa)
        for (a, b, c_, d_, nrm) in (
            (P(x, y, z), P(x, Y, z), P(X, Y, z), P(X, y, z), (0, 0, -1)),
            (P(X, y, Z), P(X, Y, Z), P(x, Y, Z), P(x, y, Z), (0, 0, 1)),
            (P(x, y, Z), P(x, Y, Z), P(x, Y, z), P(x, y, z), (-1, 0, 0)),
            (P(X, y, z), P(X, Y, z), P(X, Y, Z), P(X, y, Z), (1, 0, 0)),
        ):
            i = len(self.v)
            self.v += [a, b, c_, d_]; self.n += [nrm] * 4; self.c += [dark, col, col, dark]
            self.t += [i, i + 1, i + 2, i, i + 2, i + 3]

    def cylinder(self, cx, y, cz, r, h, col, seg=SEG, top=True):
        top_y = y + h
        dark = tuple(v * 0.85 for v in col[:3]) + (col[3],)
        for k in range(seg):
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            p0 = (cx + r * math.cos(a0), cz + r * math.sin(a0)); p1 = (cx + r * math.cos(a1), cz + r * math.sin(a1))
            n0 = (math.cos(a0), 0, math.sin(a0)); n1 = (math.cos(a1), 0, math.sin(a1))
            i = len(self.v)
            self.v += [Vec3(p0[0], y, p0[1]), Vec3(p0[0], top_y, p0[1]), Vec3(p1[0], top_y, p1[1]), Vec3(p1[0], y, p1[1])]
            self.n += [n0, n0, n1, n1]; self.c += [dark, col, col, dark]
            self.t += [i, i + 1, i + 2, i, i + 2, i + 3]
            if top:
                j = len(self.v)
                self.v += [Vec3(cx, top_y, cz), Vec3(p1[0], top_y, p1[1]), Vec3(p0[0], top_y, p0[1])]
                self.n += [(0, 1, 0)] * 3; self.c += [col] * 3
                self.t += [j, j + 1, j + 2]

    def cone(self, cx, y, cz, r, h, col, seg=10):
        for k in range(seg):
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            p0 = Vec3(cx + r * math.cos(a0), y, cz + r * math.sin(a0)); p1 = Vec3(cx + r * math.cos(a1), y, cz + r * math.sin(a1))
            tip = Vec3(cx, y + h, cz)
            am = (a0 + a1) / 2; ny = r / math.hypot(r, h)
            nrm = (math.cos(am) * h / math.hypot(r, h), ny, math.sin(am) * h / math.hypot(r, h))
            i = len(self.v)
            self.v += [p0, tip, p1]; self.n += [nrm] * 3; self.c += [col] * 3
            self.t += [i, i + 2, i + 1]

    def brick(self, x, y, z, w, d, h=BRICK_H, col=(1, 1, 1, 1), studs=True):
        """Bloque w×d botones, con su esquina mínima en (x, y, z)."""
        g = 0.02   # pequeña separación entre bloques vecinos
        self.box(x + g, y, z + g, w - 2 * g, h, d - 2 * g, col)
        if studs:
            for i in range(int(w)):
                for j in range(int(d)):
                    self.cylinder(x + i + .5, y + h, z + j + .5, STUD_R, STUD_H, col)

    def data(self):
        t = []
        for k in range(0, len(self.t), 3):
            t += [self.t[k], self.t[k + 2], self.t[k + 1]]
        return (self.v, t, self.n, [ucolor.rgba(*c) for c in self.c])

    def mesh(self):
        t = []
        for k in range(0, len(self.t), 3):          # orientar caras hacia afuera
            t += [self.t[k], self.t[k + 2], self.t[k + 1]]
        return Mesh(vertices=self.v, triangles=t, normals=self.n, colors=[ucolor.rgba(*c) for c in self.c], static=True)


def brick_mesh(w, d, h=BRICK_H, studs=True, centered=True):
    """Malla de un solo bloque en blanco (se colorea con entity.color)."""
    key = (w, d, h, studs, centered)
    if key not in _cache:
        b = MeshBuilder()
        ox, oz = (-w / 2, -d / 2) if centered else (0, 0)
        b.brick(ox, 0, oz, w, d, h, (1, 1, 1, 1), studs)
        _cache[key] = b.data()
    return _make(_cache[key])


def round_mesh(r=0.5, h=BRICK_H, stud=True):
    key = ("round", r, h, stud)
    if key not in _cache:
        b = MeshBuilder()
        b.cylinder(0, 0, 0, r, h, (1, 1, 1, 1), seg=16)
        if stud:
            b.cylinder(0, h, 0, STUD_R, STUD_H, (1, 1, 1, 1))
        _cache[key] = b.data()
    return _make(_cache[key])


def gear_mesh(r=1.6, teeth=12, thick=0.5):
    """Engranaje tipo «technic» (dientes rectangulares) en el plano XY, eje Z."""
    key = ("gear", r, teeth, thick)
    if key not in _cache:
        b = MeshBuilder()
        col = (1, 1, 1, 1)
        seg = teeth * 2
        for k in range(seg):     # disco frontal y trasero
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            for zz, nz in ((-thick / 2, -1), (thick / 2, 1)):
                i = len(b.v)
                pts = [Vec3(0, 0, zz), Vec3(r * math.cos(a0), r * math.sin(a0), zz), Vec3(r * math.cos(a1), r * math.sin(a1), zz)]
                if nz > 0: pts = [pts[0], pts[2], pts[1]]
                b.v += pts; b.n += [(0, 0, nz)] * 3; b.c += [col] * 3; b.t += [i, i + 1, i + 2]
            i = len(b.v)
            p0 = (r * math.cos(a0), r * math.sin(a0)); p1 = (r * math.cos(a1), r * math.sin(a1))
            nrm = (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0)
            b.v += [Vec3(p0[0], p0[1], -thick / 2), Vec3(p1[0], p1[1], -thick / 2), Vec3(p1[0], p1[1], thick / 2), Vec3(p0[0], p0[1], thick / 2)]
            b.n += [nrm] * 4; b.c += [col] * 4; b.t += [i, i + 1, i + 2, i, i + 2, i + 3]
        tw = 2 * math.pi * r / teeth * 0.45
        for k in range(teeth):    # dientes
            a = 2 * math.pi * k / teeth
            cx, cy = (r + 0.18) * math.cos(a), (r + 0.18) * math.sin(a)
            # caja girada: aproximación con cuatro esquinas
            ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
            hl, hw = 0.24, tw / 2
            corners = [(cx - ux * hl - vx * hw, cy - uy * hl - vy * hw), (cx + ux * hl - vx * hw, cy + uy * hl - vy * hw),
                       (cx + ux * hl + vx * hw, cy + uy * hl + vy * hw), (cx - ux * hl + vx * hw, cy - uy * hl + vy * hw)]
            for zz, nz in ((-thick / 2, -1), (thick / 2, 1)):
                i = len(b.v); pts = [Vec3(px, py, zz) for px, py in corners]
                if nz > 0: pts = pts[::-1]
                b.v += pts; b.n += [(0, 0, nz)] * 4; b.c += [col] * 4; b.t += [i, i + 1, i + 2, i, i + 2, i + 3]
            for e in range(4):
                (x0, y0), (x1, y1) = corners[e], corners[(e + 1) % 4]
                nx, ny = (y1 - y0), -(x1 - x0); L = math.hypot(nx, ny) or 1
                i = len(b.v)
                b.v += [Vec3(x0, y0, -thick / 2), Vec3(x1, y1, -thick / 2), Vec3(x1, y1, thick / 2), Vec3(x0, y0, thick / 2)]
                b.n += [(nx / L, ny / L, 0)] * 4; b.c += [col] * 4; b.t += [i, i + 1, i + 2, i, i + 2, i + 3]
        # eje en cruz
        b.box(-0.12, -0.42, -thick / 2 - 0.05, 0.24, 0.84, thick + 0.1, (0.15, 0.15, 0.15, 1), shade=False)
        b.box(-0.42, -0.12, -thick / 2 - 0.05, 0.84, 0.24, thick + 0.1, (0.15, 0.15, 0.15, 1), shade=False)
        _cache[key] = b.data()
    return _make(_cache[key])


def _make(data):
    v, t, n, c = data
    return Mesh(vertices=v, triangles=t, normals=n, colors=c, static=True)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

"""El mundo de bloques que rodea a la máquina: suelo con botones, camino,
árboles, casas, molino, estanque, autos, nubes y un avión, todo en movimiento."""
import math, random
from PIL import Image, ImageDraw, ImageFilter
from ursina import Entity, Texture, Sky, Vec3, color, time, scene

from .bricks import MeshBuilder, hexc, brick_mesh, round_mesh, BRICK_H, PLATE_H
from ..config import PALETTE as P

H = lambda k, a=1.0: hexc(P[k], a)


def stud_texture(base=(75, 159, 74), size=128, n=4):
    """Textura con botones para el suelo (n×n botones por baldosa)."""
    img = Image.new("RGB", (size, size), base)
    d = ImageDraw.Draw(img)
    cell = size / n; r = cell * 0.31
    light = tuple(min(255, int(c * 1.16)) for c in base)
    dark = tuple(int(c * 0.72) for c in base)
    for i in range(n):
        for j in range(n):
            cx, cy = (i + .5) * cell, (j + .5) * cell
            d.ellipse([cx - r + 2, cy - r + 3, cx + r + 2, cy + r + 3], fill=dark)      # sombra
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=base)
            d.ellipse([cx - r * .82, cy - r * .9, cx + r * .6, cy + r * .5], fill=light)
            d.ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55], fill=base)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    t = Texture(img); t.filtering = "mipmap"
    return t


def sky_texture():
    w, h = 8, 256
    img = Image.new("RGB", (w, h))
    top, mid, hor = (58, 128, 214), (128, 190, 240), (204, 230, 250)
    for y in range(h):
        t = y / (h - 1)       # 0 arriba, 1 abajo
        if t < .5:
            k = t / .5; c = [int(top[i] + (mid[i] - top[i]) * k) for i in range(3)]
        else:
            k = min(1, (t - .5) / .1); c = [int(mid[i] + (hor[i] - mid[i]) * k) for i in range(3)]
        for x in range(w):
            img.putpixel((x, y), tuple(c))
    return Texture(img)


class World:
    def __init__(self, seed=7):
        self.r = random.Random(seed)
        self.t = 0.0
        Sky(texture=sky_texture())
        ground = Entity(model="plane", scale=(900, 1, 900), texture=stud_texture(), texture_scale=(225, 225), y=0, color=color.white)
        ground.set_shader_input("spec_k", 0.04)
        self.static = MeshBuilder()
        self._road()
        self._pond()
        self._trees()
        self._houses()
        self._flowers()
        self._hill_windmill()
        Entity(model=self.static.mesh())
        self._cars()
        self._clouds()
        self._plane()

    # ------------------------------------------------------------ estático
    def _road(self):
        b = self.static
        x0, x1, z0, z1, w = -36, 36, -24, 34, 6
        gray, white = H("dgray"), H("white")
        for (ax, az, bw, bd) in ((x0, z0, x1 - x0, w), (x0, z1 - w, x1 - x0, w), (x0, z0, w, z1 - z0), (x1 - w, z0, w, z1 - z0)):
            b.box(ax, 0, az, bw, 0.16, bd, gray)
        for x in range(x0 + 8, x1 - 8, 4):           # líneas centrales
            b.box(x, 0.16, z0 + w / 2 - .15, 2, 0.04, .3, white)
            b.box(x, 0.16, z1 - w / 2 - .15, 2, 0.04, .3, white)
        for z in range(z0 + 8, z1 - 8, 4):
            b.box(x0 + w / 2 - .15, 0.16, z, .3, 0.04, 2, white)
            b.box(x1 - w / 2 - .15, 0.16, z, .3, 0.04, 2, white)
        self.road = (x0 + w / 2, x1 - w / 2, z0 + w / 2, z1 - w / 2)

    def _pond(self):
        b = self.static
        cx, cz = -58, 6
        for i in range(-6, 7):
            for j in range(-5, 6):
                d = (i / 6.5) ** 2 + (j / 5.5) ** 2
                if d < 1:
                    b.box(cx + i * 2, 0, cz + j * 2, 2, 0.2, 2, H("lblue" if d > .7 else "azure"))
                elif d < 1.25:
                    b.brick(cx + i * 2, 0, cz + j * 2, 2, 2, PLATE_H, H("tan"))
        # patos
        for k, (dx, dz) in enumerate(((-3, 2), (4, -2))):
            b.brick(cx + dx, 0.2, cz + dz, 2, 1, BRICK_H * .7, H("yellow"), studs=False)
            b.brick(cx + dx + 1.4, 0.2 + BRICK_H * .7, cz + dz + .1, .8, .8, .8, H("yellow"), studs=False)
            b.box(cx + dx + 2.15, 0.2 + BRICK_H * .7 + .25, cz + dz + .3, .4, .2, .2, H("orange"))

    def _tree(self, x, z, kind):
        b = self.static
        trunk = H("brown")
        if kind == 0:   # árbol cónico (pino)
            for k in range(2):
                b.brick(x - .5, k * BRICK_H, z - .5, 1, 1, BRICK_H, trunk)
            g = H("dgreen")
            b.cone(x, 2.2, z, 2.6, 3.4, g); b.cone(x, 4.0, z, 2.0, 3.0, g); b.cone(x, 5.6, z, 1.4, 2.6, g)
        elif kind == 1:   # árbol redondo de bloques
            for k in range(3):
                b.brick(x - .5, k * BRICK_H, z - .5, 1, 1, BRICK_H, trunk)
            g = H("green")
            y = 3 * BRICK_H
            for (s, dy) in ((4, 0), (6, BRICK_H), (6, 2 * BRICK_H), (4, 3 * BRICK_H), (2, 4 * BRICK_H)):
                b.brick(x - s / 2, y + dy, z - s / 2, s, s, BRICK_H, g)
        else:             # arbusto
            g = H("lime")
            b.brick(x - 1.5, 0, z - 1, 3, 2, BRICK_H, H("green"))
            b.brick(x - 1, BRICK_H, z - .5, 2, 1, BRICK_H, g)

    def _trees(self):
        placed = []
        rx0, rx1, rz0, rz1 = -42, 42, -30, 40
        while len(placed) < 46:
            x, z = self.r.uniform(-120, 120), self.r.uniform(-60, 120)
            if rx0 - 4 < x < rx1 + 4 and rz0 - 4 < z < rz1 + 4:
                continue
            if abs(x + 58) < 18 and abs(z - 6) < 15:    # estanque
                continue
            if abs(x - 70) < 14 and abs(z - 70) < 14:   # molino
                continue
            if any((x - a) ** 2 + (z - c) ** 2 < 36 for a, c in placed):
                continue
            if z < -40 and abs(x) < 60:    # dejar despejado el frente de la cámara
                continue
            placed.append((x, z))
            self._tree(round(x), round(z), self.r.choice([0, 0, 1, 1, 2]))
        for x in range(-30, 31, 10):        # fila de árboles detrás de la máquina
            self._tree(x, 46 + (x // 10) % 2 * 3, 1 if x % 20 else 0)

    def _house(self, x, z, w, d, wall, roof):
        b = self.static
        for k in range(4):
            for (ax, az, bw, bd) in ((x, z, w, 1), (x, z + d - 1, w, 1), (x, z + 1, 1, d - 2), (x + w - 1, z + 1, 1, d - 2)):
                if k in (1, 2) and bw > 3 and (ax, az) == (x, z):       # ventanas al frente
                    b.brick(ax, k * BRICK_H, az, 1, bd, BRICK_H, wall, studs=False)
                    b.box(ax + 1, k * BRICK_H, az + .3, 1.6, BRICK_H, .4, H("lblue"))
                    b.brick(ax + 2.6, k * BRICK_H, az, bw - 5.2, bd, BRICK_H, wall, studs=False)
                    b.box(ax + bw - 2.6, k * BRICK_H, az + .3, 1.6, BRICK_H, .4, H("lblue"))
                    b.brick(ax + bw - 1, k * BRICK_H, az, 1, bd, BRICK_H, wall, studs=False)
                elif k < 2 and (ax, az) == (x, z) and bw > 3:
                    b.brick(ax, k * BRICK_H, az, bw, bd, BRICK_H, wall, studs=False)
                    b.box(x + w / 2 - .8, 0, z - .05, 1.6, 2 * BRICK_H, .3, H("brown"))      # puerta
                else:
                    b.brick(ax, k * BRICK_H, az, bw, bd, BRICK_H, wall, studs=False)
        y = 4 * BRICK_H
        k = 0
        while w - 2 * k > 1 and d - 2 * k > 1:      # techo escalonado
            b.brick(x - 1 + k, y + k * PLATE_H * 1.5, z - 1 + k, w + 2 - 2 * k, d + 2 - 2 * k, PLATE_H * 1.5, roof, studs=(w - 2 * k <= 3))
            k += 1
        b.brick(x + w - 3, y + k * .6, z + d / 2 - 1, 2, 2, 2.4, H("dgray"))    # chimenea

    def _houses(self):
        specs = [(-26, 54, 10, 8, "white", "red"), (-8, 58, 8, 7, "tan", "dblue"), (14, 55, 11, 8, "yellow", "red"),
                 (34, 52, 9, 7, "lblue", "dgray"), (-52, 44, 8, 8, "white", "green"), (52, 30, 8, 8, "tan", "red"),
                 (-60, -30, 9, 7, "yellow", "dblue"), (62, -26, 8, 7, "white", "red")]
        for (x, z, w, d, wall, roof) in specs:
            self._house(x, z, w, d, H(wall), H(roof))

    def _flowers(self):
        b = self.static
        for _ in range(130):
            x, z = self.r.uniform(-110, 110), self.r.uniform(-50, 110)
            if -44 < x < 44 and -32 < z < 42:
                continue
            c = H(self.r.choice(["red", "yellow", "white", "pink", "orange"]))
            b.cylinder(x, 0, z, .3, .5, H("green"), seg=6)
            b.cylinder(x, .5, z, .55, .25, c, seg=8)

    def _hill_windmill(self):
        b = self.static
        cx, cz = 70, 70
        for k, s in enumerate((20, 15, 10)):
            b.brick(cx - s / 2, k * BRICK_H, cz - s / 2, s, s, BRICK_H, H("grass" if k < 2 else "green"))
        y0 = 3 * BRICK_H
        for k in range(9):
            s = 5 if k < 4 else (4 if k < 7 else 3)
            b.brick(cx - s / 2, y0 + k * BRICK_H, cz - s / 2, s, s, BRICK_H, H("white" if k % 3 else "red"), studs=k == 8)
        b.cone(cx, y0 + 9 * BRICK_H, cz, 2.6, 2.6, H("red"))
        self.mill_hub = Vec3(cx, y0 + 7.4 * BRICK_H, cz - 2.8)
        self.blades = Entity(position=self.mill_hub)
        Entity(parent=self.blades, model=round_mesh(.7, .8, stud=False), color=color.hex(P["dgray"]), rotation_x=-90)
        for k in range(4):
            arm = Entity(parent=self.blades, rotation_z=k * 90)
            Entity(parent=arm, model=brick_mesh(1, 1, 9, studs=False), color=color.hex(P["tan"]), z=-.6)
            Entity(parent=arm, model=brick_mesh(2.2, .4, 6, studs=False), color=color.hex(P["white"]), position=(1.6, 3, -.6))

    # ------------------------------------------------------------ dinámico
    def _car(self, body, top):
        root = Entity()
        b = MeshBuilder()
        for (wx, wz) in ((-1.3, -1.1), (1.3, -1.1), (-1.3, 1.1), (1.3, 1.1)):
            b.box(wx - .45, 0, wz - .25 if wz < 0 else wz - .25, .9, .9, .5, H("black"))
        b.brick(-2, .5, -1, 4, 2, PLATE_H * 1.5, body)
        b.brick(-1, .5 + PLATE_H * 1.5, -1, 2, 2, BRICK_H, H("lblue"), studs=False)
        b.brick(-1, .5 + PLATE_H * 1.5 + BRICK_H, -1, 2, 2, PLATE_H, top)
        b.box(1.95, .7, -.8, .1, .3, .4, H("yellow")); b.box(1.95, .7, .4, .1, .3, .4, H("yellow"))
        Entity(parent=root, model=b.mesh(), rotation_y=-90)     # el frente del auto (+x) apunta hacia +z
        return root

    def _cars(self):
        x0, x1, z0, z1 = self.road
        self.loop = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        self.loop_len = 2 * ((x1 - x0) + (z1 - z0))
        self.cars = []
        for k, (c1, c2) in enumerate((("red", "white"), ("blue", "yellow"), ("yellow", "black"), ("green", "white"))):
            car = self._car(H(c1), H(c2))
            self.cars.append((car, k / 4 * self.loop_len, 9 + k * 1.5, k % 2 == 1))

    def _clouds(self):
        self.clouds = []
        for k in range(12):
            c = Entity()
            b = MeshBuilder()
            w = self.r.randint(6, 10)
            b.brick(-w / 2, 0, -2, w, 4, BRICK_H, H("white"))
            b.brick(-w / 2 + 1, BRICK_H, -1.5, w - 3, 3, BRICK_H, H("white"))
            b.brick(-w / 2 + 2, 2 * BRICK_H, -1, max(2, w - 6), 2, BRICK_H, H("white"))
            e = Entity(parent=c, model=b.mesh(), scale=self.r.uniform(1.0, 1.8))
            e.set_shader_input("glow", 0.45); e.set_shader_input("spec_k", 0.0)
            c.position = Vec3(self.r.uniform(-160, 160), self.r.uniform(34, 58), self.r.uniform(40, 170))
            self.clouds.append((c, self.r.uniform(1.2, 3.0)))

    def _plane(self):
        self.plane = Entity()
        b = MeshBuilder()
        b.brick(-4, 0, -1, 8, 2, BRICK_H, H("white"))            # fuselaje
        b.brick(-1, 0.1, -6, 2, 12, PLATE_H, H("red"))          # alas
        b.brick(-4, BRICK_H, -.5, 1, 1, BRICK_H * 1.5, H("red"))  # cola
        b.brick(-4.2, .3, -2.5, 1.2, 5, PLATE_H, H("red"))
        b.box(4, .2, -.2, .3, .8, .4, H("dgray"))
        b.box(2.2, BRICK_H, -.8, 1.4, .6, 1.6, H("lblue"))
        body = Entity(parent=self.plane, rotation_y=-90)
        Entity(parent=body, model=b.mesh())
        self.prop = Entity(parent=body, position=(4.45, .6, 0))
        Entity(parent=self.prop, model=brick_mesh(.25, .25, 4.4, studs=False), color=color.hex(P["dgray"]), y=-2.2)

    def update(self, busy=0.0):
        dt = time.dt; self.t += dt
        self.blades.rotation_z += dt * (40 + 140 * busy)
        for car, off, speed, rev in self.cars:
            sgn = -1 if rev else 1
            s = (self.t * speed * sgn + off) % self.loop_len
            x, z, _ = self._loop_point(s)
            nx, nz, _ = self._loop_point((s + sgn * 1.5) % self.loop_len)
            car.position = (x, 0.16, z)
            car.look_at(Vec3(nx, 0.16, nz))
        for c, sp in self.clouds:
            c.x += sp * dt
            if c.x > 180:
                c.x = -180
        a = self.t * 0.12
        pos = lambda a: Vec3(math.cos(a) * 95, 48 + math.sin(a * 4) * 2, 60 + math.sin(a) * 70)
        self.plane.position = pos(a)
        self.plane.look_at(pos(a + .02))
        self.plane.rotation_z = 14
        self.prop.rotation_x += dt * 1600

    def _loop_point(self, s):
        x0, x1, z0, z1 = self.road
        legs = [((x0, z0), (x1, z0), 0), ((x1, z0), (x1, z1), -90), ((x1, z1), (x0, z1), 180), ((x0, z1), (x0, z0), 90)]
        for (a, b, hd) in legs:
            L = abs(b[0] - a[0]) + abs(b[1] - a[1])
            if s <= L:
                f = s / L
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, hd
            s -= L
        return x0, z0, 0

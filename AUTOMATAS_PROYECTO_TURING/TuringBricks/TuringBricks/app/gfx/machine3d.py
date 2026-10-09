"""La máquina de Turing construida con bloques: base, cinta, cabezal,
unidad de control, tabla de reglas y operadores.  Se arma pieza por pieza."""
import math, random
from ursina import Entity, Text, Vec3, color, time, destroy, camera

from .bricks import MeshBuilder, brick_mesh, round_mesh, gear_mesh, hexc, BRICK_H, PLATE_H
from .tween import tweener
from ..config import PALETTE as P, symbol_style, FONT_MONO, FONT_TITLE, FONT_BOLD

C = lambda k, a=1: color.hex(P[k]) if a == 1 else color.rgba(*hexc(P[k], a))
SLOTS = 8                 # celdas visibles a cada lado del cabezal
SP = 2.2                  # separación entre celdas
CELL_Y = 0.8
GREEN_TXT = color.hex("#62f0a0")


class Piece(Entity):
    """Una pieza que cae desde arriba y encaja en su lugar."""

    def __init__(self, target, **kw):
        super().__init__(**kw)
        self.target = Vec3(target)
        self.position = self.target
        self.final_scale = Vec3(self.scale)


class Cell(Entity):
    def __init__(self, parent, slot):
        super().__init__(parent=parent, model=brick_mesh(2, 3, BRICK_H), position=(slot * SP, CELL_Y, 0))
        self.slot = slot
        self.pop = 1.0
        self.sym = None
        self.label = Text(parent=self, text="", font=FONT_MONO, position=(0, .62, -1.53), origin=(0, 0), scale=36, color=color.white)
        self.ix = Text(parent=self, text="", font=FONT_MONO, position=(0, -.78, -1.75), rotation_x=90, origin=(0, 0), scale=14, color=color.hex("#3b4250"))

    def show(self, sym, blank, index=None):
        self.sym = sym
        body, txt = symbol_style(sym, blank)
        self.color = C(body)
        self.label.text = "" if sym == blank else sym
        self.label.color = C(txt) if txt in P else color.white
        if index is not None:
            self.ix.text = str(index)


class Minifig(Entity):
    def __init__(self, parent, pos, shirt, pants, helmet, rot=0):
        super().__init__(parent=parent, position=pos, rotation_y=rot)
        self.parts = []
        def part(builder, col=None, y=0):
            e = Piece(target=Vec3(0, y, 0), parent=self, model=builder.mesh())
            if col: e.color = col
            self.parts.append(e); return e
        legs = MeshBuilder(); legs.box(-.85, 0, -.45, .8, 1.4, .9, hexc(P[pants])); legs.box(.05, 0, -.45, .8, 1.4, .9, hexc(P[pants]))
        legs.box(-.9, 1.4, -.5, 1.8, .3, 1.0, hexc(P[pants]))
        part(legs)
        torso = MeshBuilder(); torso.box(-.9, 0, -.5, 1.8, 1.5, 1.0, hexc(P[shirt]))
        torso.box(-1.35, -.1, -.35, .45, 1.35, .7, hexc(P[shirt])); torso.box(.9, -.1, -.35, .45, 1.35, .7, hexc(P[shirt]))
        torso.cylinder(-1.12, -.35, 0, .2, .3, hexc(P["yellow"])); torso.cylinder(1.12, -.35, 0, .2, .3, hexc(P["yellow"]))
        torso.box(-.2, .7, -.53, .4, .5, .05, hexc(P["white"]))
        self.torso = part(torso, y=1.7)
        head = MeshBuilder(); head.cylinder(0, 0, 0, .58, .95, hexc(P["yellow"]), seg=16); head.cylinder(0, .95, 0, .3, .2, hexc(P["yellow"]))
        head.box(-.3, .55, -.6, .12, .14, .05, hexc(P["black"])); head.box(.18, .55, -.6, .12, .14, .05, hexc(P["black"]))
        head.box(-.25, .28, -.6, .5, .07, .05, hexc(P["black"]))
        self.head = part(head, y=3.25)
        hat = MeshBuilder(); hat.cylinder(0, 0, 0, .72, .55, hexc(P[helmet]), seg=16); hat.cylinder(0, 0, -.2, .8, .1, hexc(P[helmet]), seg=16)
        self.hat = part(hat, y=4.05)
        self.bob = random.random() * 6


class Machine3D:
    def __init__(self):
        self.root = Entity()
        self.blank = "_"
        self.groups = []          # [(título, descripción, [piezas])]
        self.busy = 0.0           # 0 = reposo, 1 = pensando a tope
        self.offset = 0.0         # desplazamiento animado de la cinta
        self.t = 0.0
        self.confetti = []
        self.flash = None
        self.lamp_entities = {}
        self._build()

    # ================================================================ construcción
    def _piece(self, group, model, target, col=None, **kw):
        e = Piece(target=target, parent=self.root, model=model, **kw)
        if col is not None:
            e.color = col
        group.append(e)
        return e

    def _build(self):
        g = []
        for i in range(5):
            self._piece(g, brick_mesh(8, 16, PLATE_H, centered=False), (-20 + 8 * i, 0, -6), C("lgray"))
        for i in range(5):
            self._piece(g, brick_mesh(8, 4, PLATE_H, studs=False, centered=False), (-20 + 8 * i, PLATE_H, -2), C("dgray"))
        self.groups.append(("La base", "Una plataforma sostiene todas las piezas de la máquina.", g))

        g = []
        self.cell_root = Entity(parent=self.root)
        self.cells = []
        for k in range(-SLOTS, SLOTS + 1):
            c = Cell(self.cell_root, k)
            c.target = Vec3(c.position); c.final_scale = Vec3(1, 1, 1)
            self.cells.append(c); g.append(c)
        self.groups.append(("La cinta", "Una fila infinita de celdas: cada bloque guarda un símbolo.", g))

        g = []
        for k in range(5):
            self._piece(g, brick_mesh(2, 2), (0, PLATE_H + k * BRICK_H, 4.2), C("yellow" if k % 2 == 0 else "black"))
        self._piece(g, brick_mesh(2, 6), (0, PLATE_H + 5 * BRICK_H, 1.6), C("yellow"))
        self.head = Entity(parent=self.root, position=(0, 0, 0))
        self.piston = self._piece(g, round_mesh(.35, 1.6, stud=False), (0, 4.8, 0), C("lgray"))
        self.carriage = self._piece(g, brick_mesh(2, 2), (0, 3.6, 0), C("black"))
        self.lens = self._piece(g, round_mesh(.75, .32, stud=False), (0, 3.28, 0), C("trans_red", .9))
        self.badge = self._piece(g, brick_mesh(1.8, .2, .9, studs=False), (0, 6.55, -1.5), C("white"))
        self.badge_txt = Text(parent=self.badge, text="q0", font=FONT_MONO, position=(0, .46, -.12), origin=(0, 0), scale=26, color=C("black"))
        self.beam = Entity(parent=self.root, model=round_mesh(1.05, 1.1, stud=False), color=color.rgba(1, .85, .2, .0), position=(0, 2.18, 0))
        self.beam.set_shader_input("glow", 1.0)
        self.groups.append(("El cabezal", "Lee la celda que tiene debajo, escribe un símbolo y mueve la cinta.", g))

        g = []
        for k in range(4):
            col = C("white") if k == 3 else C("blue")
            self._piece(g, brick_mesh(5, 5), (9.5, PLATE_H + k * BRICK_H, 6.5), col)
            self._piece(g, brick_mesh(5, 5), (14.5, PLATE_H + k * BRICK_H, 6.5), col)
        self.screen = self._piece(g, brick_mesh(5.8, .25, 3.0, studs=False), (10.4, 1.5, 3.95), C("black"))
        self.scr_title = Text(parent=self.screen, text="ESTADO", font=FONT_MONO, position=(-2.6, 2.6, -.15), origin=(-.5, 0), scale=13, color=color.hex("#2f8f5a"))
        self.scr_state = Text(parent=self.screen, text="q0", font=FONT_MONO, position=(-2.6, 1.55, -.15), origin=(-.5, 0), scale=42, color=GREEN_TXT)
        self.scr_steps = Text(parent=self.screen, text="PASO 0", font=FONT_MONO, position=(-2.6, .45, -.15), origin=(-.5, 0), scale=14, color=color.hex("#3fbf7f"))
        self.gear1 = self._piece(g, gear_mesh(1.25, 12, .45), (15.3, 3.5, 3.75), C("lgray"))
        self.gear2 = self._piece(g, gear_mesh(.78, 8, .45), (14.25, 1.55, 3.75), C("red"))
        self.gear3 = self._piece(g, gear_mesh(.78, 8, .45), (16.4, 1.45, 3.75), C("yellow"))
        self._piece(g, round_mesh(.14, 3.2, stud=False), (16.2, 5.2, 8.3), C("dgray"))
        self.antenna = self._piece(g, round_mesh(.38, .5, stud=False), (16.2, 8.4, 8.3), C("trans_red"))
        self.lamp_root = Entity(parent=self.root)
        self.groups.append(("La unidad de control", "Recuerda el estado actual. Cada luz es un estado posible.", g))

        g = []
        for k in range(5):
            self._piece(g, brick_mesh(1, 2), (-16.5, PLATE_H + k * BRICK_H, 5.5), C("dgray"))
            self._piece(g, brick_mesh(1, 2), (-7.5, PLATE_H + k * BRICK_H, 5.5), C("dgray"))
        self.board = self._piece(g, brick_mesh(8, .3, 4.0, studs=False), (-12, 2.2, 4.7), C("black"))
        self._piece(g, brick_mesh(10, 2), (-12, PLATE_H + 5 * BRICK_H, 5.5), C("red"))
        Text(parent=self.board, text="TABLA δ", font=FONT_MONO, position=(-3.6, 3.55, -.17), origin=(-.5, 0), scale=13, color=color.hex("#ffd24a"))
        self.rule_txt = Text(parent=self.board, text="δ(q, s) = (p, s', m)", font=FONT_MONO, position=(-3.6, 2.35, -.17), origin=(-.5, 0), scale=17, color=color.white)
        self.rule_sub = Text(parent=self.board, text="Esperando un cálculo", font=FONT_MONO, position=(-3.6, 1.05, -.17), origin=(-.5, 0), scale=12, color=color.hex("#9fb3c8"))
        self.groups.append(("La tabla de reglas", "El programa: para cada estado y símbolo dice qué hacer.", g))

        g = []
        self.figs = [Minifig(self.root, (-18.6, PLATE_H, -4.2), "red", "blue", "yellow", 0),
                     Minifig(self.root, (18.6, PLATE_H, -4.2), "azure", "dgray", "white", 0)]
        for f in self.figs:
            g += f.parts
        self.groups.append(("Los operadores", "¡Todo listo para calcular!", g))

        self.all_pieces = [p for _, _, grp in self.groups for p in grp]
        self.set_states(["q0", "q1", "qf"], {"qf"})
        self.set_tape({0: "1", 1: "0", 2: "1", 3: "1"}, 0, "_")

    # ================================================================ armado
    def hide_all(self):
        for p in self.all_pieces:
            p.enabled = False
        for e in self.lamp_entities.values():
            e[0].enabled = False; e[1].enabled = False
        self.beam.enabled = False

    def assemble(self, sound, on_group=None, on_piece=None, on_done=None, speed=1.0):
        """Programa la caída de todas las piezas.  Devuelve la duración total."""
        self.hide_all()
        t = 0.6
        idx = 0
        total = len(self.all_pieces)
        for gi, (title, desc, grp) in enumerate(self.groups):
            tweener.call(t, lambda gi=gi, title=title, desc=desc: on_group and on_group(gi, title, desc))
            t += 0.55 * speed
            step = (0.07 if len(grp) > 12 else 0.12) * speed
            for p in grp:
                idx += 1
                self._drop(p, t, sound, idx, total, on_piece)
                t += step
            if gi == 3:     # luces de estados
                for k, (lamp, lbl) in enumerate(self.lamp_entities.values()):
                    self._drop(lamp, t, sound, idx, total, None, small=True); self._drop(lbl, t, None, idx, total, None, small=True)
                    t += .06 * speed
            t += 0.35 * speed
        tweener.call(t + .35, lambda: (self.beam.__setattr__("enabled", True), on_done and on_done()))
        return t + .35

    def _drop(self, p, delay, sound, idx, total, on_piece, small=False):
        h = 9 if small else 14
        def start():
            p.enabled = True
            p.position = p.target + Vec3(0, h, 0)
            if not isinstance(p, Cell):
                p.scale = p.final_scale * .9
        tweener.to(p, "position", p.target, .5, "out_bounce", delay=delay, on_start=start, a=p.target + Vec3(0, h, 0))
        if isinstance(p, Cell):
            tweener.to(p, "pop", 1.0, .5, "out_back", delay=delay, a=.9)
        else:
            tweener.to(p, "scale", p.final_scale, .5, "out_back", delay=delay, a=p.final_scale * .9)
        if sound:
            tweener.call(delay + .18, lambda: sound())
        if on_piece:
            tweener.call(delay + .18, lambda: on_piece(idx, total))

    def finish_assembly(self):
        tweener.finish_all()
        for p in self.all_pieces:
            p.enabled = True; p.position = p.target
            if isinstance(p, Cell): p.pop = 1.0
            else: p.scale = p.final_scale
        for lamp, lbl in self.lamp_entities.values():
            lamp.enabled = lbl.enabled = True; lamp.position = lamp.target; lbl.position = lbl.target
        self.beam.enabled = True

    # ================================================================ estados / luces
    def set_states(self, states, accept):
        for lamp, lbl in self.lamp_entities.values():
            destroy(lamp); destroy(lbl)
        self.lamp_entities = {}
        shown = states[:16]
        per_row = 8
        for k, q in enumerate(shown):
            row, col = divmod(k, per_row)
            n_in_row = min(per_row, len(shown) - row * per_row)
            x = 12 - (n_in_row - 1) * 1.15 / 2 + col * 1.15 if n_in_row < per_row else 7.95 + col * 1.15
            pos = Vec3(x, PLATE_H + 4 * BRICK_H, 4.9 + row * 1.6)
            lamp = Piece(target=pos, parent=self.lamp_root, model=round_mesh(.45, .55), color=C("lgray"))
            lbl = Text(parent=self.lamp_root, text=q, font=FONT_MONO, origin=(0, 0), scale=13, billboard=True, color=C("black"))
            lbl.target = pos + Vec3(0, 1.35, 0); lbl.position = lbl.target; lbl.final_scale = Vec3(lbl.scale)
            lamp.is_accept = q in accept
            self.lamp_entities[q] = (lamp, lbl)
        self.light_state(states[0] if states else None)

    def light_state(self, state, mode="run"):
        for q, (lamp, lbl) in self.lamp_entities.items():
            on = q == state
            if mode == "accept" and on:
                lamp.color = C("lime"); lamp.set_shader_input("glow", .9)
            elif mode == "reject" and on:
                lamp.color = C("red"); lamp.set_shader_input("glow", .9)
            elif on:
                lamp.color = C("yellow"); lamp.set_shader_input("glow", .85)
            else:
                lamp.color = C("dgreen") if lamp.is_accept else C("lgray"); lamp.set_shader_input("glow", 0)

    # ================================================================ cinta
    def set_tape(self, tape: dict, head: int, blank: str):
        self.blank = blank
        self.tape_view = (dict(tape), head)
        for c in self.cells:
            i = head + c.slot
            c.show(tape.get(i, blank), blank, i)

    def refresh_from(self, tm):
        self.set_tape(tm.tape, tm.head, tm.m.blank)

    def write_center(self, sym, animate=True):
        c = self.cells[SLOTS]
        c.show(sym, self.blank)
        if animate:
            c.pop = 1.45
            tweener.to(c, "pop", 1.0, .35, "out_back")

    def reload_wave(self, tm, sound, dur=1.1):
        """Animación de recarga: las celdas salen y vuelven con la nueva entrada."""
        n = len(self.cells)
        for k, c in enumerate(self.cells):
            d = k / n * dur * .45
            tweener.to(c, "pop", 0.0, .22, "in_quad", delay=d)
            i = tm.head + c.slot
            def back(c=c, i=i):
                c.show(tm.tape.get(i, tm.m.blank), tm.m.blank, i)
                tweener.to(c, "pop", 1.0, .3, "out_back")
                if sound and c.sym != tm.m.blank: sound()
            tweener.call(d + .26 + dur * .25, back)

    def move_tape(self, direction, dur, done):
        """direction: 'R' el cabezal avanza a la derecha (la cinta se desplaza a la izquierda)."""
        if direction == "S" or dur <= 0:
            done(); return
        target = -SP if direction == "R" else SP
        self.offset = 0.0
        def fin():
            self.offset = 0.0
            done()
        tweener.to(self, "offset", target, dur, "in_out", done=fin, a=0.0)

    # ================================================================ cabezal y tablero
    def show_rule(self, rule, blank):
        if rule is None:
            self.rule_txt.text = "Sin regla: se detiene"
            self.rule_sub.text = ""
            return
        d = lambda s: "□" if s == blank else s
        self.rule_txt.text = f"δ({rule.state}, {d(rule.read)}) = ({rule.to}, {d(rule.write)}, {rule.move})"
        arrow = {"L": "←", "R": "→", "S": "·"}[rule.move]
        self.rule_sub.text = f"lee {d(rule.read)}   escribe {d(rule.write)}   mueve {arrow}"

    def read_pulse(self, dur):
        self.lens.set_shader_input("glow", 1.0)
        self.beam.color = color.rgba(1, .85, .25, .35)
        tweener.to(self.beam, "color", color.rgba(1, .85, .25, .0), max(.12, dur * 2.2), "linear")
        tweener.call(max(.1, dur * 2), lambda: self.lens.set_shader_input("glow", 0.25))

    def stamp(self, dur):
        if dur <= 0:
            return
        down = Vec3(0, 2.75, 0)
        tweener.to(self.carriage, "position", down, dur * .45, "in_quad")
        tweener.to(self.lens, "position", down + Vec3(0, -.32, 0), dur * .45, "in_quad")
        tweener.to(self.piston, "scale_y", 1 + .85 / 1.6, dur * .45, "in_quad")
        tweener.to(self.piston, "y", 4.8 - .85, dur * .45, "in_quad")
        def up():
            tweener.to(self.carriage, "position", self.carriage.target, dur * .55, "out_back")
            tweener.to(self.lens, "position", self.lens.target, dur * .55, "out_back")
            tweener.to(self.piston, "scale_y", 1.0, dur * .55, "out_back")
            tweener.to(self.piston, "y", 4.8, dur * .55, "out_back")
        tweener.call(dur * .45, up)

    def show_status(self, state, steps, label="ESTADO"):
        self.scr_title.text = label
        self.scr_state.text = state
        self.scr_steps.text = f"PASO {steps}"
        self.badge_txt.text = state

    # ================================================================ celebración
    def celebrate(self, ok, sound=None):
        self.flash = ("accept" if ok else "reject", 2.4)
        if not ok:
            return
        cols = ["red", "yellow", "blue", "green", "orange", "azure", "white", "lime", "magenta"]
        for _ in range(46):
            e = Entity(parent=self.root, model=brick_mesh(1, random.choice([1, 2]), random.choice([PLATE_H, BRICK_H])),
                       color=C(random.choice(cols)), position=(random.uniform(-6, 6), 9, random.uniform(-1, 4)),
                       rotation=(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)))
            v = Vec3(random.uniform(-9, 9), random.uniform(10, 18), random.uniform(-7, 3))
            w = Vec3(random.uniform(-400, 400), random.uniform(-400, 400), random.uniform(-400, 400))
            self.confetti.append([e, v, w, 3.2])

    # ================================================================ cada cuadro
    def update(self):
        dt = time.dt
        self.t += dt
        busy = self.busy
        self.gear1.rotation_z += dt * (25 + 260 * busy)
        self.gear2.rotation_z -= dt * (25 + 260 * busy) * 1.25 / .78
        self.gear3.rotation_z -= dt * (25 + 260 * busy) * 1.25 / .78
        blink = (math.sin(self.t * (3 + 14 * busy)) > 0)
        self.antenna.set_shader_input("glow", 1.0 if blink else 0.1)
        # cinta: posición y desvanecido en los extremos
        lim = (SLOTS + .55) * SP
        for c in self.cells:
            x = c.slot * SP + self.offset
            c.x = x
            edge = max(0.0, min(1.0, (lim - abs(x)) / (1.3 * SP)))
            s = max(0.0001, edge * c.pop)
            c.scale = Vec3(s, s, s)
        # luces «pensando»
        if busy > .5 and self.flash is None:
            k = int(self.t * 10) % max(1, len(self.lamp_entities))
            for i, (lamp, _) in enumerate(self.lamp_entities.values()):
                if getattr(self, "_chase", False):
                    lamp.set_shader_input("glow", .9 if i == k else 0)
        if self.flash:
            mode, left = self.flash
            left -= dt
            on = int(left * 6) % 2 == 0
            for lamp, _ in self.lamp_entities.values():
                lamp.color = (C("lime") if mode == "accept" else C("red")) if on else C("lgray")
                lamp.set_shader_input("glow", .9 if on else 0)
            self.flash = (mode, left) if left > 0 else None
            if self.flash is None:
                self.light_state(self._last_state, "accept" if mode == "accept" else "reject")
        # operadores
        for f in self.figs:
            f.bob += dt * (2 + 8 * busy)
            f.head.rotation_y = math.sin(f.bob * .7) * (12 + 25 * busy)
            if f.head.enabled:
                f.hat.rotation_y = f.head.rotation_y
        # confeti
        for item in self.confetti[:]:
            e, v, w, life = item
            v.y -= 26 * dt
            e.position += v * dt
            e.rotation += w * dt
            if e.y < PLATE_H + .3:
                e.y = PLATE_H + .3; v.y *= -.35; v.x *= .6; v.z *= .6; w *= .5
            item[3] -= dt
            if item[3] < .5:
                e.scale = Vec3(1, 1, 1) * max(0.001, item[3] / .5)
            if item[3] <= 0:
                destroy(e); self.confetti.remove(item)

    _last_state = None

    def remember_state(self, state):
        self._last_state = state

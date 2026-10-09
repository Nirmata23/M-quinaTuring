"""Componentes de interfaz con estilo de bloques: paneles, botones, campos,
selector de velocidad y avisos."""
from ursina import Entity, Text, Quad, color, camera, InputField, Vec3, mouse, destroy, time
from ..config import FONT_TITLE, FONT_BODY, FONT_BOLD, FONT_MONO, FONT_MONO_REG, PALETTE as P
from ..gfx.tween import tweener
from ursina.shaders import unlit_shader

INK = color.hex("#1b2a34")
MUTED = color.hex("#5b6b7a")
LINE = color.hex("#dfe5ea")
WHITE = color.white
BG = color.rgba(1, 1, 1, .97)

def C(k): return color.hex(P[k]) if k in P else color.hex(k)

def darker(c, k=.78): return color.rgba(c[0] * k, c[1] * k, c[2] * k, c[3])
def lighter(c, k=.18): return color.rgba(c[0] + (1 - c[0]) * k, c[1] + (1 - c[1]) * k, c[2] + (1 - c[2]) * k, c[3])

SOUND = {"click": None, "hover": None}


def _wrap(text, n):
    out = []
    for line in text.split("\n"):
        cur = ""
        for word in line.split(" "):
            if cur and len(cur) + 1 + len(word) > n:
                out.append(cur); cur = word
            else:
                cur = (cur + " " + word) if cur else word
        out.append(cur)
    return "\n".join(out)


_orig_setter = Text.text_setter


def _text_setter(self, text):
    n = getattr(self, "wrap_chars", None)
    if n and text:
        text = _wrap(text, n)
    _orig_setter(self, text)


Text.text = property(Text.text_getter, _text_setter)


def label(parent, text, x, y, size=1.0, font=FONT_BODY, col=INK, origin=(-.5, .5), wrap=None, z=-.02):
    t = Text(text="", parent=parent, position=(x, y, z), scale=size, font=font, color=col, origin=origin)
    t.wrap_chars = wrap
    t.text = text
    return t


class Box(Entity):
    """Rectángulo redondeado posicionado por su esquina superior izquierda."""
    def __init__(self, parent, x, y, w, h, col=WHITE, radius=.012, z=0, **kw):
        r = min(.5, radius / max(1e-6, min(w, h)))
        super().__init__(parent=parent, model=Quad(radius=r, aspect=w / h), scale=(w, h), position=(x + w / 2, y - h / 2, z), color=col, shader=unlit_shader, **kw)


class Panel(Entity):
    """Tarjeta blanca con encabezado de color y botones (studs) como un bloque."""
    def __init__(self, x, y, w, h, title="", accent="red", parent=camera.ui, z=0.0):
        super().__init__(parent=parent, position=(x, y, z))
        self.w, self.h = w, h
        Box(self, .006, -.009, w, h, color.rgba(0, 0, 0, .22), radius=.022, z=.03)
        self.body = Box(self, 0, 0, w, h, BG, radius=.022, z=.02, collider="box")
        ac = C(accent)
        hh = .062
        Box(self, 0, 0, w, hh, ac, radius=.022, z=.015)
        Box(self, 0, -hh * .5, w, hh * .5, ac, radius=0.0001, z=.015)
        n = max(2, int(w / .06))
        for i in range(n):
            Entity(parent=self, model=Quad(radius=.5), scale=(.026, .013), position=(.03 + i * (w - .06) / (n - 1), .004, .016), color=lighter(ac, .25), shader=unlit_shader)
        self.title = label(self, title, .022, -.016, 1.25, FONT_TITLE, WHITE)
        self.content_top = -hh - .018

    def set_title(self, t):
        self.title.text = t


class Btn(Entity):
    """Botón con «labio» inferior, como un bloque que se hunde al presionarlo."""
    def __init__(self, parent, text, x, y, w, h, col="yellow", text_col=None, on_click=None, size=.95, font=FONT_BOLD, radius=.012, z=-.01, sub=None):
        super().__init__(parent=parent, position=(x, y, z))
        self.w, self.h = w, h
        self.base_col = C(col) if isinstance(col, str) else col
        self.lip = Box(self, -w / 2, h / 2 - .007, w, h, darker(self.base_col, .7), radius=radius, z=.004)
        self.face = Box(self, -w / 2, h / 2, w, h, self.base_col, radius=radius, z=0, collider="box")
        tc = text_col if text_col is not None else (INK if (self.base_col[0] + self.base_col[1] + self.base_col[2]) > 1.9 else WHITE)
        self.txt = label(self, text, 0, .002 if not sub else .012, size, font, tc, origin=(0, 0), z=-.006)
        self.sub = label(self, sub, 0, -.016, size * .62, FONT_BODY, tc, origin=(0, 0), z=-.006) if sub else None
        self.action = on_click
        self.disabled = False
        self.selected = False
        self.face.on_mouse_enter = self._enter
        self.face.on_mouse_exit = self._exit
        self.face.on_click = self._click

    def _enter(self):
        if self.disabled: return
        self.face.color = lighter(self.base_col, .16)
        if SOUND["hover"]: SOUND["hover"]()

    def _exit(self):
        self.face.color = self.base_col if not self.selected else self.base_col

    def _click(self):
        if self.disabled: return
        self.face.y -= .005; self.txt.y -= .005
        if self.sub: self.sub.y -= .005
        def up():
            self.face.y += .005; self.txt.y += .005
            if self.sub: self.sub.y += .005
        tweener.call(.09, up)
        if SOUND["click"]: SOUND["click"]()
        if self.action: self.action()

    def set_color(self, col):
        self.base_col = C(col) if isinstance(col, str) else col
        self.face.color = self.base_col
        self.lip.color = darker(self.base_col, .7)

    def set_text(self, t):
        self.txt.text = t

    def set_width(self, w):
        self.w = w
        self.face.scale_x = w; self.lip.scale_x = w

    def set_disabled(self, v):
        self.disabled = v
        self.alpha_all(.45 if v else 1)

    def alpha_all(self, a):
        for e in (self.face, self.lip):
            c = e.color; e.color = color.rgba(c[0], c[1], c[2], a)
        c = self.txt.color; self.txt.color = color.rgba(c[0], c[1], c[2], a)


class Field(Entity):
    """Etiqueta + campo de texto."""
    def __init__(self, parent, label_text, x, y, w, value="", lines=1, limit=24, hint=""):
        super().__init__(parent=parent, position=(x, y, -.01))
        self.lbl = label(self, label_text, 0, 0, .78, FONT_BOLD, MUTED)
        h = .042 if lines == 1 else .026 * lines + .02
        Box(self, -.003, -.026 + .003, w + .006, h + .006, color.hex("#c9d3dc"), radius=.01, z=.002)
        self.input = InputField(parent=self, default_value=value, max_lines=lines, character_limit=limit,
                                position=(w / 2, -.026 - h / 2, 0), scale=(w, h), color=WHITE, radius=.18 if lines == 1 else .02)
        tf = self.input.text_field
        k = .82 if lines == 1 else .74           # tamaño del texto escrito
        tf.scale = Vec3(k / w, k / h, 1)
        top = (h - .025 * k * 1.1) / 2 if lines == 1 else .012
        tf.position = Vec3(-.5 + .012 / w, .5 - top / h, -.01)
        self.input.text_field.text_entity.color = INK
        self.input.highlight_color = color.hex("#f7fbff")
        self.input.text_field.cursor.color = C("blue")
        try:
            self.input.text_field.cursor.animations.clear()
        except Exception:
            pass
        self.lines = lines
        if lines > 1:      # editor de varias líneas con desplazamiento
            tf.max_lines = 500
            def render(tf=tf, n=lines):
                ls = tf.text.split("\n")
                sc = int(tf.scroll)
                tf.text_entity.text = "\n" * sc + "\n".join(ls[sc:sc + n])
            tf.render = render
            self.scroll_hint = label(self, "", w, -.004, .58, FONT_BOLD, C("blue"), origin=(.5, .5))
        self.hint = label(self, hint, 0, -.026 - h - .006, .62, FONT_BODY, MUTED) if hint else None
        self.height = .026 + h + (.026 if hint else .008)

    @property
    def value(self):
        return self.input.text

    @value.setter
    def value(self, v):
        self.input.text = v
        if self.lines > 1:
            tf = self.input.text_field
            tf.cursor.position = (0, 0)
            tf.set_scroll(0)

    def update(self):
        if self.lines > 1:
            tf = self.input.text_field
            n = len(tf.text.split("\n"))
            if tf.active:
                cy = int(tf.cursor.y)
                if cy >= tf.scroll + self.lines:
                    tf.set_scroll(cy - self.lines + 1)
                elif cy < tf.scroll:
                    tf.set_scroll(cy)
            if tf.scroll > max(0, n - self.lines):
                tf.set_scroll(max(0, n - self.lines))
            self.scroll_hint.text = (f"líneas {int(tf.scroll) + 1}-{min(n, int(tf.scroll) + self.lines)} de {n}, usa la rueda"
                                     if n > self.lines else "")

    @property
    def active(self):
        return self.input.active


class BrickSlider(Entity):
    """Selector de velocidad hecho con 10 bloquecitos."""
    def __init__(self, parent, x, y, n=10, value=5, on_change=None):
        super().__init__(parent=parent, position=(x, y, -.01))
        self.n, self.value, self.on_change = n, value, on_change
        self.bricks = []
        cols = ["green", "green", "lime", "lime", "yellow", "yellow", "orange", "orange", "red", "red"]
        for i in range(n):
            b = Box(self, i * .022, 0, .019, .026, C(cols[i]), radius=.004, z=0, collider="box")
            b.on_click = lambda i=i: self.set(i + 1, True)
            self.bricks.append((b, C(cols[i])))
        self.set(value)

    def set(self, v, user=False):
        self.value = max(1, min(self.n, v))
        for i, (b, c) in enumerate(self.bricks):
            b.color = c if i < self.value else color.hex("#d5dbe0")
            b.scale_y = .026 if i < self.value else .02
        if user:
            if SOUND["click"]: SOUND["click"]()
            if self.on_change: self.on_change(self.value)


class Toast(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, position=(0, -.39, -.3))
        self.bg = Box(self, -.3, .025, .6, .05, color.rgba(.1, .16, .22, .92), radius=.025)
        self.t = label(self, "", 0, .0, .85, FONT_BOLD, WHITE, origin=(0, 0))
        self.enabled = False
        self.time_left = 0

    def show(self, text, secs=2.6):
        self.t.text = text
        w = max(.25, self.t.width * .85 + .06)
        self.bg.scale_x = w; self.bg.x = 0
        self.enabled = True; self.time_left = secs

    def update(self):
        if self.time_left > 0:
            self.time_left -= time.dt
            if self.time_left <= 0:
                self.enabled = False

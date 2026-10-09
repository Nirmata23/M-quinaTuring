"""Controlador principal de Turing Bricks: une el mundo 3D, la máquina de
bloques, el motor de Turing y la interfaz."""
import math
from ursina import Entity, Text, camera, color, time, mouse, held_keys, window, scene, Vec3, destroy, application

from .config import FONT_TITLE, FONT_BODY, FONT_BOLD, FONT_MONO, FONT_MONO_REG, APP_NAME, PALETTE as P
from .engine import parse, TuringMachine, Definition, ACCEPT, REJECT, LIMIT
from .machines import SPECS, CATEGORIES, custom_spec, validate_values
from . import storage
from .sounds import Sounds
from .gfx.world import World
from .gfx.machine3d import Machine3D
from .gfx.camera_rig import CameraRig
from .gfx.tween import tweener
from .ui.widgets import (Panel, Btn, Box, Field, BrickSlider, Toast, label, SOUND, INK, MUTED, WHITE, C, lighter, darker)

STEP_TIME = {1: 1.6, 2: 1.15, 3: .85, 4: .6, 5: .42, 6: .28, 7: .17, 8: .09, 9: .045, 10: 0.0}
ROWS = 12

LEARN = [
    ("¿Qué es una máquina de Turing?",
     "Es un modelo matemático de computación que Alan Turing propuso en 1936. Tiene una cinta infinita dividida en celdas, "
     "un cabezal que lee y escribe una celda a la vez, un número finito de estados y una tabla de reglas de transición. "
     "Con esas piezas tan simples puede calcular todo lo que cualquier computadora puede calcular."),
    ("¿Cómo funciona?",
     "En cada paso la máquina lee el símbolo que está bajo el cabezal y busca en la tabla la regla para el par (estado, símbolo). "
     "La regla le dice qué escribir, hacia dónde moverse (izquierda o derecha) y a qué estado pasar. "
     "Si llega a un estado final se detiene y acepta; si no existe regla para la situación, se detiene y rechaza."),
    ("¿Cómo se crea?",
     "1. Define qué debe calcular o reconocer.  2. Elige los alfabetos: Σ para la entrada y el de la cinta (que incluye el blanco).  "
     "3. Piensa la estrategia en palabras.  4. Asigna un estado a cada fase de la estrategia.  "
     "5. Escribe las reglas de transición.  6. Pruébala con varias entradas.  En la pestaña «Crear máquina» puedes hacer todo esto."),
    ("Cómo usar el programa",
     "Elige un cálculo a la izquierda, escribe los datos y pulsa «Calcular». La máquina pensará y luego ejecutará cada regla "
     "sobre la cinta de bloques.  Barra inferior: pausar, avanzar paso a paso, velocidad y saltar al resultado.  "
     "Cámara: arrastra con el botón derecho para girar y usa la rueda para acercar.  Teclas: Espacio pausa, flecha derecha avanza un paso, F11 pantalla completa."),
]


def fmt_sym(s, blank):
    return "□" if s == blank else s


class TuringBricksApp(Entity):
    def __init__(self):
        super().__init__()
        self.snd = Sounds()
        SOUND["click"] = lambda: self.snd.play("pop", .45)
        SOUND["hover"] = lambda: self.snd.play("hover", .2, min_gap=.06)
        self.world = World()
        self.machine = Machine3D()
        self.rig = CameraRig()
        self.toast = Toast()
        self.mode = "intro"
        self.phase = None           # thinking | running | done
        self.paused = False
        self.cur = None
        self.speed = 5
        self.tm = None
        self.spec = SPECS[0]
        self.category = "Aritmética"
        self.custom = [custom_spec(d) for d in storage.load_all()]
        self.example_i = 0
        self.confirm_delete = False
        self.aspect = camera.aspect_ratio
        self.L = Entity(parent=camera.ui, x=-self.aspect / 2)
        self.R = Entity(parent=camera.ui, x=self.aspect / 2)
        self._build_topbar()
        self._build_calc()
        self._build_editor()
        self._build_runbar()
        self._build_result()
        self._build_learn()
        self._build_intro()
        self.select_category("Aritmética")
        self.show_main(False)
        self.start_intro()

    # ================================================================== utilidades UI
    def specs_in(self, cat):
        return self.custom if cat == "Mis máquinas" else [s for s in SPECS if s.category == cat]

    def any_typing(self):
        return any(f.active for f in self.all_fields)

    def show_main(self, v):
        for e in (self.topbar_l, self.topbar_c, self.topbar_r):
            e.enabled = v
        self.calc.enabled = v and self.mode != "editor"
        self.editor.enabled = v and self.mode == "editor"

    # ================================================================== barra superior
    def _build_topbar(self):
        self.topbar_l = Entity(parent=self.L, position=(.02, .485))
        Box(self.topbar_l, 0, .006, .29, .062, color.rgba(1, 1, 1, .96), radius=.031)
        for i, k in enumerate(("red", "yellow", "blue")):
            Box(self.topbar_l, .02 + i * .021, -.012, .018, .026, C(k), radius=.003, z=-.01)
        label(self.topbar_l, APP_NAME, .09, -.002, 1.05, FONT_TITLE, INK)
        label(self.topbar_l, "máquina de Turing de bloques", .091, -.03, .58, FONT_BODY, MUTED)

        self.topbar_c = Entity(parent=camera.ui, position=(0, .457))
        self.nav = {}
        for i, (key, txt, col) in enumerate((("calc", "Calcular", "red"), ("editor", "Crear máquina", "yellow"), ("learn", "Aprender", "blue"))):
            b = Btn(self.topbar_c, txt, (i - 1) * .175, 0, .165, .046, col, on_click=lambda k=key: self.nav_to(k), size=.88)
            self.nav[key] = b

        self.topbar_r = Entity(parent=self.R, position=(-.02, .457))
        self.btn_music = Btn(self.topbar_r, "Música: sí", -.06, 0, .12, .042, "white", on_click=self.toggle_music, size=.72)
        self.btn_sound = Btn(self.topbar_r, "Sonido: sí", -.19, 0, .12, .042, "white", on_click=self.toggle_sound, size=.72)
        Btn(self.topbar_r, "Vista", -.3, 0, .08, .042, "white", on_click=self.reset_view, size=.72)
        Btn(self.topbar_r, "Rearmar", -.4, 0, .1, .042, "white", on_click=self.start_intro, size=.72)

    def nav_to(self, key):
        if key == "learn":
            self.open_learn(); return
        if key == "editor":
            self.mode = "editor"
            self.calc.enabled = False; self.editor.enabled = True
            if not self.ed_fields["name"].value:
                self.editor_template()
        else:
            self.mode = "calc"
            self.calc.enabled = True; self.editor.enabled = False
        self.layout_camera()

    def toggle_music(self):
        self.snd.set_music(not self.snd.music_on)
        self.btn_music.set_text("Música: sí" if self.snd.music_on else "Música: no")

    def toggle_sound(self):
        self.snd.enabled = not self.snd.enabled
        self.btn_sound.set_text("Sonido: sí" if self.snd.enabled else "Sonido: no")

    def reset_view(self):
        self.rig.working_view(); self.layout_camera()

    # ================================================================== panel «Calcular»
    def _build_calc(self):
        W, H = .5, .895
        self.calc = Panel(.02, .425, W, H, "Calcular", "red", parent=self.L)
        p = self.calc
        y = p.content_top
        label(p, "1   Elige un cálculo", .022, y, .92, FONT_BOLD, INK)
        self.cat_btns = {}
        cw = (W - .044 - .018) / 4
        for i, cat in enumerate(CATEGORIES):
            short = {"Mis máquinas": "Mis máquinas"}.get(cat, cat)
            b = Btn(p, short, .022 + cw / 2 + i * (cw + .006), y - .052, cw, .036, "white", on_click=lambda c=cat: self.select_category(c), size=.66)
            self.cat_btns[cat] = b
        self.list_y = y - .1
        self.list_btns = []
        for i in range(4):
            b = Btn(p, "", W / 2, self.list_y - i * .066 - .03, W - .044, .058, "white", on_click=lambda i=i: self.pick_from_list(i), size=.86, sub=" ")
            self.list_btns.append(b)
        self.empty_lbl = label(p, "Aún no tienes máquinas guardadas.\nCréalas en la pestaña «Crear máquina».", W / 2, self.list_y - .05, .78, FONT_BODY, MUTED, origin=(0, .5))
        y2 = self.list_y - 4 * .066 - .025
        label(p, "2   Escribe los datos", .022, y2, .92, FONT_BOLD, INK)
        self.fields_y = y2 - .04
        self.calc_fields = [Field(p, "", .022, self.fields_y, (W - .058) / 2), Field(p, "", .022 + (W - .058) / 2 + .014, self.fields_y, (W - .058) / 2)]
        self.wide_field = Field(p, "", .022, self.fields_y, W - .044, limit=26)
        self.err_lbl = label(p, "", .022, self.fields_y - .1, .72, FONT_BOLD, C("red"), wrap=48)
        sy = self.fields_y - .145
        Box(p, .022, sy, W - .044, .15, color.hex("#f1f5f8"), radius=.012, z=.01)
        label(p, "Cómo lo resolverá la máquina", .036, sy - .014, .74, FONT_BOLD, C("blue"))
        self.strategy_lbl = label(p, "", .036, sy - .042, .7, FONT_BODY, INK, wrap=50)
        self.calc_btn = Btn(p, "Calcular", W / 2 - .07, -H + .055, W - .044 - .14, .07, "yellow", on_click=self.start_run, size=1.4, font=FONT_TITLE)
        self.edit_btn = Btn(p, "Editar", W - .022 - .06, -H + .074, .12, .032, "white", on_click=self.edit_selected, size=.68)
        self.del_btn = Btn(p, "Borrar", W - .022 - .06, -H + .034, .12, .032, "white", on_click=self.delete_selected, size=.68)

    def select_category(self, cat):
        self.category = cat
        for c, b in self.cat_btns.items():
            b.set_color("blue" if c == cat else "white")
            b.txt.color = WHITE if c == cat else INK
        items = self.specs_in(cat)
        for i, b in enumerate(self.list_btns):
            if i < len(items):
                b.enabled = True
                b.set_text(items[i].title)
                s = items[i].summary
                b.sub.text = s if len(s) < 62 else s[:59] + "…"
            else:
                b.enabled = False
        self.empty_lbl.enabled = (cat == "Mis máquinas" and not items)
        if items:
            self.select_spec(items[0] if self.spec not in items else self.spec)
        else:
            self._refresh_list_marks()

    def pick_from_list(self, i):
        items = self.specs_in(self.category)
        if i < len(items):
            self.select_spec(items[i])

    def _refresh_list_marks(self):
        items = self.specs_in(self.category)
        for i, b in enumerate(self.list_btns):
            sel = i < len(items) and items[i] is self.spec
            b.set_color(color.hex("#fff3c4") if sel else WHITE)
            b.lip.color = C("yellow") if sel else color.hex("#cfd8df")

    def select_spec(self, spec):
        self.spec = spec
        self._refresh_list_marks()
        for f in self.calc_fields + [self.wide_field]:
            f.enabled = False
        fs = spec.fields
        if len(fs) == 1 and fs[0].kind == "str":
            use = [(self.wide_field, fs[0])]
        else:
            use = list(zip(self.calc_fields, fs))
        for fw, fd in use:
            fw.enabled = True
            fw.lbl.text = fd.label
            # primero las restricciones, después el valor (si no, el filtro anterior borra el texto)
            fw.input.text_field.character_limit = fd.max_len if fd.kind == "str" else 4
            if fd.kind == "int":
                fw.input.limit_content_to = "0123456789"
            else:
                fw.input.limit_content_to = fd.allowed or None
            fw.value = fd.default
            fw.spec_field = fd
        self.active_fields = [fw for fw, _ in use]
        hint = "  ".join(f"{fd.label}: {fd.min} a {fd.max}" if fd.kind == "int" else f"Símbolos: {' '.join(fd.allowed) if fd.allowed else 'libres'} (máx. {fd.max_len})" for _, fd in use)
        self.err_lbl.text = hint
        self.err_lbl.color = MUTED
        self.strategy_lbl.text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(spec.strategy))
        is_custom = spec.custom
        self.edit_btn.enabled = self.del_btn.enabled = is_custom
        self.calc_btn.x = (.5 / 2 - .07) if is_custom else .25
        self.calc_btn.set_width(.5 - .044 - .14 if is_custom else .5 - .044)
        self.del_btn.set_text("Borrar"); self.confirm_delete = False
        m = parse(spec.definition)
        if not m.errors and self.phase not in ("thinking", "running"):
            self.machine.set_states(m.states, m.accept)

    def edit_selected(self):
        self.load_into_editor(self.spec.definition)
        self.nav_to("editor")

    def delete_selected(self):
        if not self.spec.custom: return
        if not self.confirm_delete:
            self.confirm_delete = True; self.del_btn.set_text("¿Seguro?"); return
        storage.delete(self.spec.definition.name)
        self.custom = [custom_spec(d) for d in storage.load_all()]
        self.toast.show("Máquina borrada")
        self.select_category("Mis máquinas")

    # ================================================================== editor
    def _build_editor(self):
        W, H = .56, .895
        self.editor = Panel(.02, .425, W, H, "Crear máquina", "yellow", parent=self.L)
        e = self.editor
        e.title.color = INK
        y = e.content_top
        f = {}
        f["name"] = Field(e, "Nombre", .022, y, .3, limit=28)
        f["input"] = Field(e, "Entrada de prueba", .34, y, W - .362, limit=24)
        y -= .085
        f["start"] = Field(e, "Estado inicial", .022, y, .12, limit=8)
        f["accept"] = Field(e, "Estados finales", .154, y, .16, limit=20)
        f["blank"] = Field(e, "Blanco", .326, y, .07, limit=1)
        f["sigma"] = Field(e, "Alfabeto Σ", .408, y, W - .43, limit=14)
        y -= .085
        f["rules"] = Field(e, "Reglas (una por línea)", .022, y, W - .044, lines=14, limit=44,
                           hint="Formato:  estado, lee -> nuevo, escribe, mueve    Mueve: R derecha, L izquierda, S quieto.  # = comentario")
        self.ed_fields = f
        y -= f["rules"].height + .006
        bw = (W - .044 - .03) / 4
        acts = (("Probar", "yellow", self.editor_test), ("Guardar", "green", self.editor_save),
                ("Nueva", "white", self.editor_template), ("Ejemplo", "white", self.editor_example))
        for i, (t, c, fn) in enumerate(acts):
            Btn(e, t, .022 + bw / 2 + i * (bw + .01), y - .024, bw, .048, c, on_click=fn, size=.95 if i < 2 else .82, font=FONT_TITLE if i < 2 else FONT_BOLD)
        self.ed_msg = label(e, "", .022, y - .062, .68, FONT_BOLD, MUTED, wrap=58)

    def load_into_editor(self, d: Definition):
        f = self.ed_fields
        f["name"].value = d.name; f["start"].value = d.start; f["accept"].value = d.accept
        f["blank"].value = d.blank; f["sigma"].value = d.sigma; f["input"].value = d.input
        f["rules"].value = d.rules.replace("_", d.blank) if d.blank != "_" else d.rules

    def editor_def(self):
        f = self.ed_fields
        return Definition(name=f["name"].value.strip() or "Mi máquina", start=f["start"].value.strip(), accept=f["accept"].value.strip(),
                          blank=(f["blank"].value.strip() or "_"), sigma=f["sigma"].value.strip(), rules=f["rules"].value,
                          input=f["input"].value.strip(), description="Máquina creada en el editor.")

    def editor_template(self):
        self.load_into_editor(Definition(name="Mi máquina", start="q0", accept="qf", blank="_", sigma="0,1", input="0110",
                                         rules="# Recorre la cadena y se detiene al final\nq0, 0 -> q0, 0, R\nq0, 1 -> q0, 1, R\nq0, _ -> qf, _, L"))
        self._ed_msg("Plantilla lista. Modifica las reglas y pulsa «Probar».", MUTED)

    def editor_example(self):
        s = SPECS[self.example_i % len(SPECS)]; self.example_i += 1
        d = s.definition
        self.load_into_editor(Definition(name=f"Copia de {s.title}", start=d.start, accept=d.accept, blank=d.blank, sigma=d.sigma,
                                         rules=d.rules, input=s.encode({k.key: (int(k.default) if k.kind == "int" else k.default) for k in s.fields})))
        self._ed_msg(f"Cargué la máquina «{s.title}». Puedes estudiarla o modificarla.", MUTED)

    def _ed_msg(self, text, col):
        self.ed_msg.text = text; self.ed_msg.color = col

    def _editor_check(self):
        d = self.editor_def()
        m = parse(d)
        if m.errors:
            self._ed_msg("  ".join(m.errors[:3]) + ("  …" if len(m.errors) > 3 else ""), C("red"))
            self.snd.play("fail", .4)
            return None, None
        bad = [c for c in d.input if c not in m.sigma]
        if bad:
            self._ed_msg(f"La entrada usa «{bad[0]}», que no está en Σ = {{{', '.join(m.sigma)}}}.", C("red")); return None, None
        return d, m

    def editor_test(self):
        d, m = self._editor_check()
        if not d: return
        self._ed_msg(f"Máquina válida: {len(m.states)} estados y {len(m.rules)} reglas. ¡Ejecutando!", C("green"))
        spec = custom_spec(d)
        self.spec = spec
        self.start_run(values={"w": d.input}, spec=spec)

    def editor_save(self):
        d, m = self._editor_check()
        if not d: return
        storage.save(d)
        self.custom = [custom_spec(x) for x in storage.load_all()]
        self._ed_msg("Guardada. La encontrarás en Calcular, pestaña «Mis máquinas».", C("green"))
        self.toast.show(f"«{d.name}» guardada en Mis máquinas")
        self.snd.play("success", .5)

    # ================================================================== barra de ejecución
    def _build_runbar(self):
        self.runbar = Entity(parent=camera.ui, position=(0, -.4))
        W = .74
        Box(self.runbar, -W / 2 + .005, .05 - .007, W, .1, color.rgba(0, 0, 0, .22), radius=.02, z=.02)
        Box(self.runbar, -W / 2, .05, W, .1, color.rgba(1, 1, 1, .97), radius=.02, z=.01)
        self.run_info = label(self.runbar, "", 0, .031, .78, FONT_BOLD, INK, origin=(0, 0))
        y = -.014
        self.btn_pause = Btn(self.runbar, "Pausar", -W / 2 + .065, y, .1, .042, "blue", on_click=self.toggle_pause, size=.8)
        Btn(self.runbar, "Paso", -W / 2 + .165, y, .08, .042, "white", on_click=self.single_step, size=.8)
        label(self.runbar, "Velocidad", -W / 2 + .218, y, .7, FONT_BOLD, MUTED, origin=(-.5, 0))
        self.slider = BrickSlider(self.runbar, -W / 2 + .295, y + .013, value=5, on_change=self.set_speed)
        Btn(self.runbar, "Saltar al resultado", W / 2 - .093, y, .16, .042, "yellow", on_click=self.skip_to_end, size=.74)
        self.runbar.enabled = False

        self.status = Entity(parent=camera.ui, position=(0, .385))
        self.status_bg = Box(self.status, -.27, .028, .54, .056, color.rgba(.08, .14, .22, .9), radius=.028)
        self.status_txt = label(self.status, "", 0, .001, .95, FONT_MONO, WHITE, origin=(0, 0))
        self.status.enabled = False

    def set_speed(self, v):
        self.speed = v

    def toggle_pause(self):
        if self.phase != "running": return
        self.paused = not self.paused
        self.btn_pause.set_text("Continuar" if self.paused else "Pausar")
        self.btn_pause.set_color("green" if self.paused else "blue")

    def single_step(self):
        if self.phase != "running" or self.tm is None or self.tm.halted: return
        if not self.paused:
            self.toggle_pause()
        if self.cur is None:
            self.begin_step(max(.6, STEP_TIME[self.speed]))

    def skip_to_end(self):
        if self.phase == "thinking":
            self.think_left = 0
        if self.phase not in ("running", "thinking") or self.tm is None: return
        tweener.finish_all()
        self.cur = None
        self.machine.offset = 0
        while not self.tm.halted:
            self.tm.step()
        self.machine.refresh_from(self.tm)
        self.finish()

    # ================================================================== panel de resultado
    def _build_result(self):
        W, H = .5, .895
        self.result = Panel(-.02 - W, .425, W, H, "Resultado", "blue", parent=self.R)
        r = self.result
        y = r.content_top
        self.res_badge = Box(r, .022, y + .002, .13, .034, C("green"), radius=.017, z=.01)
        self.res_badge_t = label(r, "Aceptada", .022 + .065, y - .015, .72, FONT_BOLD, WHITE, origin=(0, 0))
        self.res_head = label(r, "", .022, y - .045, 2.0, FONT_TITLE, INK)
        self.res_detail = label(r, "", .022, y - .108, .78, FONT_BODY, MUTED, wrap=54)
        cy = y - .165
        self.chips = []
        for i in range(3):
            b = Box(r, .022 + i * .154, cy, .146, .052, color.hex("#f1f5f8"), radius=.012, z=.01)
            v = label(r, "", .022 + i * .154 + .073, cy - .018, 1.05, FONT_TITLE, C("blue"), origin=(0, 0))
            k = label(r, "", .022 + i * .154 + .073, cy - .039, .6, FONT_BODY, MUTED, origin=(0, 0))
            self.chips.append((v, k))
        ty = cy - .075
        self.tab_rules = Btn(r, "Procedimiento", .022 + .07, ty - .018, .14, .036, "blue", on_click=lambda: self.set_res_tab("rules"), size=.7)
        self.tab_cfg = Btn(r, "Configuraciones", .022 + .222, ty - .018, .15, .036, "white", on_click=lambda: self.set_res_tab("cfg"), size=.7)
        self.res_head_row = label(r, "", .022, ty - .05, .66, FONT_MONO, MUTED)
        self.rows = [label(r, "", .022, ty - .078 - i * .0285, .66, FONT_MONO_REG, INK) for i in range(ROWS)]
        py = ty - .078 - ROWS * .0285 - .012
        Btn(r, "Inicio", .06, py - .02, .076, .036, "white", on_click=lambda: self.page_to(0), size=.66)
        Btn(r, "Anterior", .155, py - .02, .1, .036, "white", on_click=lambda: self.page_to(self.page - 1), size=.66)
        self.page_lbl = label(r, "", W / 2, py - .02, .68, FONT_BOLD, MUTED, origin=(0, 0))
        Btn(r, "Siguiente", W - .155, py - .02, .1, .036, "white", on_click=lambda: self.page_to(self.page + 1), size=.66)
        Btn(r, "Final", W - .06, py - .02, .076, .036, "white", on_click=lambda: self.page_to(10 ** 9), size=.66)
        label(r, "Usa la rueda del ratón sobre la lista para pasar páginas", W / 2, py - .05, .56, FONT_BODY, MUTED, origin=(0, 0))
        Btn(r, "Ver de nuevo", .022 + .11, -H + .045, .22, .052, "yellow", on_click=self.replay, size=.9, font=FONT_TITLE)
        Btn(r, "Cerrar", W - .022 - .11, -H + .045, .22, .052, "white", on_click=self.close_result, size=.9, font=FONT_TITLE)
        self.res_tab = "rules"
        self.page = 0
        self.trace = []
        self.result.enabled = False

    def set_res_tab(self, t):
        self.res_tab = t
        self.tab_rules.set_color("blue" if t == "rules" else "white"); self.tab_rules.txt.color = WHITE if t == "rules" else INK
        self.tab_cfg.set_color("blue" if t == "cfg" else "white"); self.tab_cfg.txt.color = WHITE if t == "cfg" else INK
        self.page_to(self.page)

    def page_to(self, p):
        n = max(1, math.ceil(len(self.trace) / ROWS))
        self.page = max(0, min(n - 1, p))
        blank = self.run_machine.blank if self.trace else "_"
        rows = self.trace[self.page * ROWS:(self.page + 1) * ROWS]
        if self.res_tab == "rules":
            self.res_head_row.text = "  paso  estado lee  escribe mueve  nuevo"
            for i, lbl in enumerate(self.rows):
                if i < len(rows):
                    s = rows[i]; r = s.rule
                    lbl.text = f"{s.n:>6}  {r.state[:6]:<6} {fmt_sym(r.read, blank):^3}  {fmt_sym(r.write, blank):^7} {r.move:^5}  {r.to[:7]}"
                else:
                    lbl.text = ""
        else:
            self.res_head_row.text = "  paso  configuración  (estado entre corchetes)"
            for i, lbl in enumerate(self.rows):
                if i < len(rows):
                    s = rows[i]; cfg = s.config or "(no registrada)"
                    if len(cfg) > 40:
                        k = cfg.find("[")
                        a = max(0, min(len(cfg) - 38, k - 16))
                        cfg = ("…" if a > 0 else "") + cfg[a:a + 38] + ("…" if a + 38 < len(cfg) else "")
                    lbl.text = f"{s.n:>6}  {cfg}"
                else:
                    lbl.text = ""
        self.page_lbl.text = f"{self.page + 1} / {n}"

    def close_result(self):
        self.result.enabled = False
        self.layout_camera()

    def replay(self):
        if self.last_run:
            spec, vals = self.last_run
            self.start_run(values=vals, spec=spec)

    # ================================================================== aprender
    def _build_learn(self):
        self.learn = Entity(parent=camera.ui, z=-.5)
        self.learn_shade = Box(self.learn, -2, 1, 4, 2, color.rgba(0, .05, .1, .45), radius=0, z=.05, collider="box")
        W, H = .92, .56
        self.learn_panel = Panel(-W / 2, H / 2, W, H, "Aprender", "blue", parent=self.learn, z=0)
        lp = self.learn_panel
        self.learn_title = label(lp, "", .04, lp.content_top - .01, 1.9, FONT_TITLE, INK)
        self.learn_text = label(lp, "", .04, lp.content_top - .09, 1.0, FONT_BODY, INK, wrap=70)
        self.learn_dots = [Box(lp, W / 2 - .05 + i * .03, -H + .07, .018, .018, C("blue"), radius=.009, z=.01) for i in range(len(LEARN))]
        Btn(lp, "Anterior", .12, -H + .055, .16, .05, "white", on_click=lambda: self.learn_page(self.learn_i - 1), size=.85)
        self.learn_next = Btn(lp, "Siguiente", W - .12, -H + .055, .16, .05, "yellow", on_click=lambda: self.learn_page(self.learn_i + 1), size=.85)
        Btn(lp, "Cerrar", W - .06, -.02, .08, .034, "white", on_click=self.close_learn, size=.68)
        self.learn_i = 0
        self.learn.enabled = False

    def open_learn(self):
        self.learn.enabled = True; self.learn_page(0); self.snd.play("whoosh", .4)

    def close_learn(self):
        self.learn.enabled = False

    def learn_page(self, i):
        if i >= len(LEARN):
            self.close_learn(); return
        self.learn_i = max(0, i)
        t, body = LEARN[self.learn_i]
        self.learn_title.text = t; self.learn_text.text = body
        for k, d in enumerate(self.learn_dots):
            d.color = C("blue") if k == self.learn_i else color.hex("#cfd8df")
        self.learn_next.set_text("Listo" if self.learn_i == len(LEARN) - 1 else "Siguiente")

    # ================================================================== introducción (armado)
    def _build_intro(self):
        self.intro = Entity(parent=camera.ui, z=-.2)
        self.intro_title = label(self.intro, APP_NAME, 0, .39, 4.2, FONT_TITLE, WHITE, origin=(0, 0))
        self.intro_title_sh = label(self.intro, APP_NAME, .004, .385, 4.2, FONT_TITLE, color.rgba(0, .1, .25, .35), origin=(0, 0), z=-.01)
        self.intro_title.z = -.02
        Box(self.intro, -.33, .335, .66, .05, color.rgba(.05, .12, .22, .55), radius=.025, z=.01)
        self.intro_sub = label(self.intro, "Una máquina de Turing real, construida pieza por pieza", 0, .31, 1.1, FONT_BOLD, WHITE, origin=(0, 0))
        card = Entity(parent=self.intro, position=(0, -.31))
        Box(card, -.36 + .006, .085 - .008, .72, .19, color.rgba(0, 0, 0, .22), radius=.025, z=.02)
        Box(card, -.36, .085, .72, .19, color.rgba(1, 1, 1, .95), radius=.025, z=.01)
        self.cap_step = label(card, "", -.33, .065, .72, FONT_BOLD, C("red"))
        self.cap_title = label(card, "", -.33, .04, 1.6, FONT_TITLE, INK)
        self.cap_desc = label(card, "", -.33, -.005, .85, FONT_BODY, MUTED, wrap=64)
        self.prog = []
        cols = ["red", "yellow", "blue", "green", "orange", "azure"]
        for i in range(30):
            self.prog.append(Box(card, -.33 + i * .0148, -.052, .0128, .022, C(cols[i % 6]), radius=.003, z=0))
        self.cap_count = label(card, "", .2, -.063, .66, FONT_BOLD, MUTED, origin=(.5, 0))
        Btn(card, "Saltar", .29, -.063, .1, .036, "white", on_click=self.skip_intro, size=.72)
        self.intro.enabled = False

    def start_intro(self):
        if self.phase in ("thinking", "running"):
            self.skip_to_end()
        self.mode = "intro"
        self.show_main(False)
        self.result.enabled = False; self.runbar.enabled = False; self.status.enabled = False; self.learn.enabled = False
        self.intro.enabled = True
        for b in self.prog:
            b.color = color.hex("#dfe5ea")
        self.cap_title.text = "Preparando las piezas…"; self.cap_desc.text = ""; self.cap_step.text = ""; self.cap_count.text = ""
        tweener.finish_all()
        self.machine.finish_assembly()
        self.machine.set_states(["q0", "q1", "qf"], {"qf"})
        self.machine.set_tape({0: "1", 1: "0", 2: "1", 3: "1"}, 0, "_")
        self.machine.show_status("q0", 0)
        self.rig.film_goal = type(self.rig.film)(0, 0)
        self.rig.set_goal(target=(0, 3, 3), yaw=-48, pitch=34, dist=66); self.rig.snap()
        self.rig.set_goal(dist=54, pitch=27)
        self.rig.auto_orbit = 5.5
        self.rig.user = False
        ng = len(self.machine.groups)
        def on_group(gi, title, desc):
            self.cap_step.text = f"Paso {gi + 1} de {ng}"
            self.cap_title.text = title; self.cap_desc.text = desc
            self.snd.play("whoosh", .25)
        def on_piece(i, total):
            k = int(i / total * len(self.prog))
            for j, b in enumerate(self.prog):
                if j < k:
                    b.color = C(["red", "yellow", "blue", "green", "orange", "azure"][j % 6])
            self.cap_count.text = f"{i} / {total} piezas"
        self.intro_t = self.machine.assemble(lambda: self.snd.click(.9), on_group, on_piece, self.end_intro)

    def skip_intro(self):
        if self.mode != "intro": return
        self.machine.finish_assembly()
        tweener.finish_all()

    def end_intro(self):
        if self.mode != "intro": return
        self.snd.play("build_done", .8)
        self.machine.light_state("q0")
        self.cap_title.text = "¡Máquina lista!"; self.cap_desc.text = "Elige un cálculo a la izquierda y pulsa «Calcular»."
        self.cap_step.text = ""
        tweener.call(1.6, self.enter_main)

    def enter_main(self):
        if self.mode != "intro": return
        self.intro.enabled = False
        self.mode = "calc"
        self.show_main(True)
        self.rig.auto_orbit = 0
        self.rig.working_view()
        self.layout_camera()
        self.select_category(self.category)
        self.snd.play("whoosh", .4)
        if self.snd.music_on and self.snd.music:
            try: self.snd.music.play()
            except Exception: pass
        self.toast.show("¡Lista! Elige un cálculo y pulsa «Calcular».", 3.5)

    # ================================================================== cámara
    def layout_camera(self):
        left = self.calc.enabled or self.editor.enabled
        right = self.result.enabled
        fx, dist = 0.0, 50
        if left and right: dist = 64
        elif left: fx, dist = -.15, 54
        elif right: fx, dist = .15, 54
        self.rig.film_goal = type(self.rig.film)(fx, -.02)
        if not self.rig.user:
            self.rig.set_goal(dist=dist)

    # ================================================================== ejecución
    def start_run(self, values=None, spec=None):
        if self.mode == "intro": return
        spec = spec or self.spec
        if values is None:
            raw = {}
            for fw in self.active_fields:
                raw[fw.spec_field.key] = fw.value
            values, err = validate_values(spec, raw)
            if err:
                self.err_lbl.text = err; self.err_lbl.color = C("red")
                self.snd.play("fail", .45); return
            self.err_lbl.color = MUTED
        m = parse(spec.definition)
        if m.errors:
            self.toast.show("La máquina tiene errores: revisa el editor."); return
        word = spec.encode(values)
        # cálculo completo (procedimiento) por adelantado
        full = TuringMachine(m)
        full.load(word)
        self.trace = full.run()
        self.result_obj = spec.decode(values, full)
        self.full = full
        self.run_machine = m
        self.last_run = (spec, values)
        # máquina visual
        self.tm = TuringMachine(m); self.tm.load(word)
        tweener.finish_all()
        self.machine.offset = 0
        self.machine.flash = None
        self.machine.set_states(m.states, m.accept)
        self.machine.light_state(m.start)
        self.machine.remember_state(m.start)
        self.machine.show_status("...", 0, "PENSANDO")
        self.machine.rule_txt.text = "Analizando la entrada…"
        self.machine.rule_sub.text = f"Cinta: {word or 'vacía'}"
        self.machine.reload_wave(self.tm, lambda: self.snd.click(.7, min_gap=.03))
        n = len(self.trace)
        target = 26.0 if n > 6 else 12.0
        lvl = 10
        for k in range(1, 11):
            if STEP_TIME[k] * n <= target or k == 10:
                lvl = k; break
        self.speed = lvl; self.slider.set(lvl)
        self.phase = "thinking"; self.think_left = 1.9; self.paused = False; self.cur = None
        self.btn_pause.set_text("Pausar"); self.btn_pause.set_color("blue")
        self.machine.busy = 1.0; self.machine._chase = True
        self.snd.play("think", .55)
        self.result.enabled = False
        self.runbar.enabled = True; self.status.enabled = True
        self.rig.working_view(); self.layout_camera()
        self._dots = 0.0

    def begin_step(self, dur):
        r = self.tm.next_rule()
        self.cur = {"rule": r, "t": 0.0, "dur": dur, "fired": set(), "prev": self.tm.state, "move_done": False}

    def tick_step(self, dt):
        c = self.cur; c["t"] += dt; d = c["dur"]; r = c["rule"]; f = c["fired"]
        blank = self.tm.m.blank
        if "read" not in f:
            f.add("read")
            self.machine.show_rule(r, blank)
            self.machine.read_pulse(d * .25)
            self.status_txt.text = r.text(blank)
            if d >= .3: self.snd.play("hover", .5)
        if "stamp" not in f and c["t"] >= .2 * d:
            f.add("stamp"); self.machine.stamp(d * .3)
        if "write" not in f and c["t"] >= .34 * d:
            f.add("write")
            changed = self.tm.read() != r.write
            self.tm.step()
            self.machine.write_center(r.write, animate=d > .06)
            if changed: self.snd.play("stamp", .75, min_gap=.05)
            else: self.snd.click(.45, min_gap=.05)
        if "move" not in f and c["t"] >= .48 * d:
            f.add("move")
            def done():
                self.machine.refresh_from(self.tm); c["move_done"] = True
            if r.move != "S" and d >= .12: self.snd.play("slide", .45, min_gap=.08)
            self.machine.move_tape(r.move, d * .34 if d > .06 else 0, done)
        if "state" not in f and c["t"] >= .84 * d:
            f.add("state")
            self.machine.light_state(self.tm.state); self.machine.remember_state(self.tm.state)
            self.machine.show_status(self.tm.state, self.tm.steps)
            if self.tm.state != c["prev"] and d >= .25: self.snd.play("state", .4)
        if c["t"] >= d and c["move_done"]:
            self.cur = None
            self.update_runinfo()
            if self.tm.halted:
                self.finish()

    def turbo(self, dt):
        n = max(1, int(1500 * min(dt, .05)))
        for _ in range(n):
            if self.tm.halted: break
            self.tm.step()
        self.machine.refresh_from(self.tm)
        self.machine.light_state(self.tm.state); self.machine.remember_state(self.tm.state)
        self.machine.show_status(self.tm.state, self.tm.steps)
        if self.tm.last:
            self.machine.show_rule(self.tm.last, self.tm.m.blank)
            self.status_txt.text = self.tm.last.text(self.tm.m.blank)
        self.snd.click(.35, min_gap=.07)
        self.update_runinfo()
        if self.tm.halted:
            self.finish()

    def update_runinfo(self):
        tot = len(self.trace)
        self.run_info.text = f"Paso {self.tm.steps} de {tot}     Estado actual: {self.tm.state}     Velocidad {self.speed}/10"

    def finish(self):
        if self.phase == "done": return
        self.phase = "done"; self.cur = None
        self.machine.busy = 0.0; self.machine._chase = False
        res = self.result_obj
        ok = res.ok and self.tm.status != LIMIT
        self.machine.light_state(self.tm.state, "accept" if ok else "reject"); self.machine.remember_state(self.tm.state)
        self.machine.show_status(self.tm.state, self.tm.steps, "ACEPTA" if ok else "RECHAZA")
        self.machine.rule_txt.text = res.headline
        self.machine.rule_sub.text = "La máquina se detuvo"
        self.machine.celebrate(ok)
        self.snd.stop("think")
        self.snd.play("success" if ok else "fail", .8)
        self.status_txt.text = res.headline
        self.run_info.text = f"Terminó en {self.tm.steps} pasos.  Estado final: {self.tm.state}"
        tweener.call(.7, self.show_result)

    def show_result(self):
        res = self.result_obj; ok = res.ok and self.full.status != LIMIT
        self.res_badge.color = C("green") if ok else C("red")
        if self.full.status == LIMIT:
            badge, head = "Límite", "Sin terminar"
            detail = f"Se alcanzó el límite de {self.full.limit:,} pasos: la máquina podría estar en un ciclo infinito."
        else:
            badge = "Aceptada" if self.full.status == ACCEPT else "Rechazada"
            head, detail = res.headline, res.detail
        self.res_badge_t.text = badge
        self.res_head.text = head
        self.res_head.color = INK
        self.res_detail.text = detail
        cells = len(range(self.full.min_pos, self.full.max_pos + 1))
        for (v, k), (val, key) in zip(self.chips, ((len(self.trace), "pasos"), (len(self.full.visited), "estados usados"), (cells, "celdas visitadas"))):
            v.text = f"{val:,}".replace(",", " "); k.text = key
        self.page = 0
        self.set_res_tab("rules")
        self.result.enabled = True
        self.runbar.enabled = False
        self.layout_camera()
        self.snd.play("whoosh", .4)

    # ================================================================== bucle principal
    def update(self):
        dt = time.dt
        self.snd.update(dt)
        tweener.update()
        self.machine.update()
        self.world.update(self.machine.busy)
        self.rig.update()
        self.toast.update()
        scene.set_shader_input("cam_pos", camera.world_position)
        if abs(camera.aspect_ratio - self.aspect) > 1e-3:
            self.aspect = camera.aspect_ratio
            self.L.x = -self.aspect / 2; self.R.x = self.aspect / 2
        if self.phase == "thinking":
            self.think_left -= dt
            self._dots += dt
            self.status_txt.text = "La máquina está pensando" + "." * (int(self._dots * 3) % 4)
            self.run_info.text = "Cargando la entrada en la cinta…"
            if self.think_left <= 0:
                self.phase = "running"; self.machine._chase = False; self.machine.busy = .45
                self.machine.light_state(self.tm.state)
                self.machine.show_status(self.tm.state, 0)
                self.snd.stop("think")
                self.update_runinfo()
                if self.tm.halted:
                    self.finish()
        elif self.phase == "running":
            if self.cur is not None:
                self.tick_step(dt)
            elif not self.paused:
                if self.speed >= 10:
                    self.turbo(dt)
                else:
                    self.begin_step(STEP_TIME[self.speed])
                    self.tick_step(0)
        # cámara con el mouse
        if mouse.right and not self._over_ui():
            self.rig.drag(mouse.velocity[0], mouse.velocity[1])

    def _over_ui(self):
        h = mouse.hovered_entity
        return h is not None and h.has_ancestor(camera.ui)

    def input(self, key):
        if key in ("scroll up", "scroll down"):
            h = mouse.hovered_entity
            if self.result.enabled and h is not None and h.has_ancestor(self.result):
                self.page_to(self.page + (-1 if key == "scroll up" else 1)); return
            if not self._over_ui():
                self.rig.zoom(.9 if key == "scroll up" else 1.1)
            return
        if key == "f11":
            window.fullscreen = not window.fullscreen; return
        if key == "escape":
            if self.learn.enabled: self.close_learn()
            return
        if self.any_typing():
            return
        if key == "space":
            if self.mode == "intro": self.skip_intro()
            else: self.toggle_pause()
        elif key == "right arrow":
            self.single_step()

    @property
    def all_fields(self):
        return self.calc_fields + [self.wide_field] + list(self.ed_fields.values())

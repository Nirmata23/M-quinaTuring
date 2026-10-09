"""Motor de la máquina de Turing.

Implementa una máquina de Turing determinista de una sola cinta, infinita en
ambas direcciones:  M = (Q, Σ, Γ, δ, q0, □, F).

- La función de transición δ puede ser parcial: si no hay regla para el par
  (estado, símbolo) la máquina se detiene y RECHAZA.
- Si la máquina entra a un estado de F se detiene y ACEPTA.
- Se impone un límite de pasos para detectar posibles ciclos infinitos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MOVES = {"L": "L", "R": "R", "S": "S", "I": "L", "D": "R", "N": "S"}
RULE_RE = re.compile(r"^\s*([^\s,]+)\s*,\s*(\S)\s*(?:->|→)\s*([^\s,]+)\s*,\s*(\S)\s*,\s*([A-Za-z])\s*$")

READY, RUNNING, ACCEPT, REJECT, LIMIT = "ready", "running", "accept", "reject", "limit"


@dataclass(frozen=True)
class Rule:
    state: str
    read: str
    to: str
    write: str
    move: str
    line: int = 0

    def text(self, blank: str = "_") -> str:
        d = lambda s: "□" if s == blank else s
        return f"δ({self.state}, {d(self.read)}) = ({self.to}, {d(self.write)}, {self.move})"


@dataclass
class Definition:
    """Definición textual de una máquina (lo que escribe el usuario)."""
    name: str = "Mi máquina"
    start: str = "q0"
    accept: str = "qf"
    blank: str = "_"
    sigma: str = ""
    rules: str = ""
    input: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return dict(name=self.name, start=self.start, accept=self.accept, blank=self.blank,
                    sigma=self.sigma, rules=self.rules, input=self.input, description=self.description)

    @staticmethod
    def from_dict(d: dict) -> "Definition":
        return Definition(**{k: str(d.get(k, "")) for k in Definition().to_dict().keys()})


@dataclass
class Machine:
    name: str
    blank: str
    start: str
    accept: set
    states: list
    rules: dict            # (estado, símbolo) -> Rule
    gamma: list
    sigma: list
    errors: list = field(default_factory=list)

    def rule(self, state: str, sym: str):
        return self.rules.get((state, sym))


def _natural_key(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def parse(defn: Definition) -> Machine:
    """Convierte el texto de las reglas en una máquina validada."""
    errors: list[str] = []
    rules: dict = {}
    states: list[str] = []

    def add_state(q):
        if q not in states:
            states.append(q)

    blank = (defn.blank or "_").strip() or "_"
    if len(blank) != 1:
        errors.append("El símbolo blanco debe ser un solo carácter.")
    start = (defn.start or "").strip()
    if not start:
        errors.append("Indica el estado inicial.")
    else:
        add_state(start)
    accept = [s for s in re.split(r"[\s,]+", defn.accept or "") if s]
    gamma = {blank}

    for i, raw in enumerate((defn.rules or "").splitlines(), start=1):
        line = re.sub(r"//.*$", "", raw).strip()
        if line.startswith("#"):
            continue
        if not line:
            continue
        m = RULE_RE.match(line)
        if not m:
            errors.append(f"Línea {i}: formato no válido. Usa: estado, símbolo -> nuevo, escribe, movimiento")
            continue
        q, s, p, w, mv = m.groups()
        move = MOVES.get(mv.upper())
        if not move:
            errors.append(f"Línea {i}: el movimiento «{mv}» no existe. Usa L, R o S (también I, D o N).")
            continue
        if (q, s) in rules:
            errors.append(f"Línea {i}: ya existe una regla para δ({q}, {s}). Una máquina determinista solo admite una.")
            continue
        rules[(q, s)] = Rule(q, s, p, w, move, i)
        add_state(q); add_state(p); gamma.add(s); gamma.add(w)

    for a in accept:
        add_state(a)
    if not errors and not rules:
        errors.append("Agrega al menos una transición.")

    sigma = [s for s in re.split(r"[\s,]+", defn.sigma or "") if s]
    if not sigma:
        sigma = sorted(g for g in gamma if g != blank)
    bad_sigma = [s for s in sigma if len(s) != 1]
    if bad_sigma:
        errors.append("Cada símbolo de Σ debe ser un solo carácter.")
    if blank in sigma:
        errors.append("El símbolo blanco no puede formar parte de Σ.")
    gamma.update(sigma)

    acc = set(accept)
    rank = lambda q: 0 if q == start else (2 if q in acc else 1)
    states.sort(key=lambda q: (rank(q), _natural_key(q)))
    gamma_list = sorted(gamma, key=lambda s: (s == blank, s not in sigma, s))
    return Machine(defn.name or "Mi máquina", blank, start, acc, states, rules, gamma_list, sigma, errors)


@dataclass
class Step:
    n: int            # número de paso (1, 2, 3…)
    rule: Rule
    head: int         # posición del cabezal ANTES del paso
    config: str       # descripción instantánea DESPUÉS del paso (puede ser '')


class TuringMachine:
    def __init__(self, machine: Machine, limit: int = 200_000):
        self.m = machine
        self.limit = limit
        self.load("")

    # ---------- carga y lectura ----------
    def load(self, word: str):
        self.input = word
        self.tape: dict[int, str] = {i: c for i, c in enumerate(word) if c != self.m.blank}
        self.head = 0
        self.state = self.m.start
        self.steps = 0
        self.history: list = []
        self.last: Rule | None = None
        self.last_pos: int | None = None
        self.status = READY
        self.visited = {self.state}
        self.min_pos, self.max_pos = 0, max(0, len(word) - 1)
        self._check_halt()

    def read(self, i: int | None = None) -> str:
        return self.tape.get(self.head if i is None else i, self.m.blank)

    def next_rule(self):
        return self.m.rule(self.state, self.read())

    @property
    def halted(self) -> bool:
        return self.status in (ACCEPT, REJECT, LIMIT)

    def _check_halt(self):
        if self.state in self.m.accept:
            self.status = ACCEPT
        elif self.next_rule() is None:
            self.status = REJECT
        elif self.steps >= self.limit:
            self.status = LIMIT
        elif self.steps > 0:
            self.status = RUNNING

    # ---------- ejecución ----------
    def step(self):
        """Ejecuta un paso. Devuelve la regla aplicada o None si ya se detuvo."""
        if self.halted:
            return None
        r = self.next_rule()
        self.history.append((self.head, self.state, self.read(), self.status, self.last, self.last_pos))
        pos = self.head
        if r.write == self.m.blank:
            self.tape.pop(pos, None)
        else:
            self.tape[pos] = r.write
        self.head += -1 if r.move == "L" else (1 if r.move == "R" else 0)
        self.min_pos = min(self.min_pos, self.head)
        self.max_pos = max(self.max_pos, self.head)
        self.state = r.to
        self.visited.add(self.state)
        self.steps += 1
        self.last, self.last_pos = r, pos
        self._check_halt()
        return r

    def back(self) -> bool:
        if not self.history:
            return False
        head, state, sym, status, last, last_pos = self.history.pop()
        self.head, self.state, self.status, self.last, self.last_pos = head, state, status, last, last_pos
        if sym == self.m.blank:
            self.tape.pop(head, None)
        else:
            self.tape[head] = sym
        self.steps -= 1
        return True

    def run(self, record_configs: int = 4000) -> list[Step]:
        """Ejecuta hasta detenerse y devuelve el procedimiento completo."""
        trace: list[Step] = []
        while not self.halted:
            pos = self.head
            r = self.step()
            cfg = self.config_text() if self.steps <= record_configs else ""
            trace.append(Step(self.steps, r, pos, cfg))
        return trace

    # ---------- representación ----------
    def output(self) -> str:
        if not self.tape:
            return ""
        a, b = min(self.tape), max(self.tape)
        return "".join(self.read(i) for i in range(a, b + 1))

    def config_parts(self):
        """Descripción instantánea α q β como lista de (tipo, texto)."""
        keys = list(self.tape) + [self.head]
        a, b = min(keys), max(keys)
        parts = []
        for i in range(a, b + 1):
            if i == self.head:
                parts.append(("q", self.state))
            parts.append(("s", self.read(i)))
        return parts

    def config_text(self) -> str:
        d = lambda s: "□" if s == self.m.blank else s
        return " ".join(f"[{t}]" if k == "q" else d(t) for k, t in self.config_parts())

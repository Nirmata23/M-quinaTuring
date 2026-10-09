"""Biblioteca de máquinas de Turing incluidas en el programa.

Cada máquina tiene:
- su definición formal (estados, reglas δ, blanco, Σ),
- los campos que el usuario llena en la interfaz,
- cómo se codifican esos datos en la cinta (encode),
- cómo se interpreta la cinta al terminar (decode),
- una explicación breve de su estrategia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .engine import ACCEPT, Definition, TuringMachine


@dataclass
class Field:
    key: str
    label: str
    kind: str = "int"          # int | str
    default: str = ""
    min: int = 0
    max: int = 255
    allowed: str = ""          # caracteres permitidos para kind="str"
    max_len: int = 16
    hint: str = ""


@dataclass
class Result:
    ok: bool                    # aceptada / cálculo válido
    headline: str               # respuesta principal, p. ej. "13 + 6 = 19"
    detail: str = ""            # explicación secundaria


@dataclass
class Spec:
    key: str
    category: str
    title: str
    summary: str
    strategy: list
    fields: list
    definition: Definition
    encode: Callable[[dict], str]
    decode: Callable[[dict, TuringMachine], Result]
    validate: Callable[[dict], str | None] = lambda v: None
    custom: bool = False
    extra: dict = field(default_factory=dict)


CATEGORIES = ["Aritmética", "Lenguajes", "Utilidades", "Mis máquinas"]

b2 = lambda n: format(int(n), "b")


def _num(tm: TuringMachine) -> int:
    out = tm.output().replace(tm.m.blank, "")
    digits = "".join(c for c in out if c in "01")
    return int(digits, 2) if digits else 0


def _ones(tm: TuringMachine) -> int:
    return tm.output().count("1")


# --------------------------------------------------------------------------- aritmética
SUMA = Definition(
    name="Suma binaria", start="q0", accept="qf", blank="_", sigma="0,1,+",
    rules="""# Ir al final del segundo número
q0, 0 -> q0, 0, R
q0, 1 -> q0, 1, R
q0, + -> q0, +, R
q0, _ -> dec, _, L
# Restar 1 al segundo número (con préstamo)
dec, 0 -> dec, 1, L
dec, 1 -> izq, 0, L
dec, + -> borra, _, R
# Volver al primer número
izq, 0 -> izq, 0, L
izq, 1 -> izq, 1, L
izq, + -> inc, +, L
# Sumar 1 al primer número (con acarreo)
inc, 1 -> inc, 0, L
inc, 0 -> q0, 1, R
inc, _ -> q0, 1, R
# El segundo número llegó a 0: limpiar la cinta
borra, 1 -> borra, _, R
borra, _ -> casa, _, L
casa, _ -> casa, _, L
casa, 0 -> ini, 0, L
casa, 1 -> ini, 1, L
ini, 0 -> ini, 0, L
ini, 1 -> ini, 1, L
ini, _ -> qf, _, R""")

RESTA = Definition(
    name="Resta binaria", start="q0", accept="qf", blank="_", sigma="0,1,-",
    rules="""# Ir al final del sustraendo
q0, 0 -> q0, 0, R
q0, 1 -> q0, 1, R
q0, - -> q0, -, R
q0, _ -> dec, _, L
# Restar 1 al sustraendo
dec, 0 -> dec, 1, L
dec, 1 -> izq, 0, L
dec, - -> borra, _, R
# Ir al minuendo
izq, 0 -> izq, 0, L
izq, 1 -> izq, 1, L
izq, - -> resA, -, L
# Restar 1 al minuendo
resA, 0 -> resA, 1, L
resA, 1 -> q0, 0, R
# Limpiar y quitar ceros a la izquierda
borra, 1 -> borra, _, R
borra, _ -> casa, _, L
casa, _ -> casa, _, L
casa, 0 -> ini, 0, L
casa, 1 -> ini, 1, L
ini, 0 -> ini, 0, L
ini, 1 -> ini, 1, L
ini, _ -> cero, _, R
cero, 0 -> sig, _, R
cero, 1 -> qf, 1, S
sig, 0 -> sig, _, R
sig, 1 -> qf, 1, S
sig, _ -> qf, 0, S""")

MULT = Definition(
    name="Multiplicación (unaria)", start="s0", accept="qf", blank="_", sigma="1,*,=",
    rules="""# Marcar un 1 del primer número (A)
s0, 1 -> s1, A, R
s0, * -> c1, _, L
# Ir al segundo número
s1, 1 -> s1, 1, R
s1, * -> s2, *, R
# Marcar un 1 del segundo número (B)
s2, B -> s2, B, R
s2, 1 -> s3, B, R
s2, = -> s5, =, L
# Copiar un 1 al resultado
s3, 1 -> s3, 1, R
s3, = -> s3, =, R
s3, _ -> s4, 1, L
# Regresar a la última B
s4, 1 -> s4, 1, L
s4, = -> s4, =, L
s4, B -> s2, B, R
# Segundo número agotado: restaurar las B
s5, B -> s5, 1, L
s5, * -> s6, *, L
s6, 1 -> s6, 1, L
s6, A -> s0, A, R
# Limpiar: borrar A, *, segundo número e =
c1, A -> c1, _, L
c1, _ -> c2, _, R
c2, _ -> c2, _, R
c2, 1 -> c2, _, R
c2, = -> qf, _, R""")

# --------------------------------------------------------------------------- lenguajes
PALINDROMO = Definition(
    name="Palíndromos", start="q0", accept="qa", blank="_", sigma="a,b",
    rules="""# Leer y borrar el primer símbolo
q0, a -> q1, _, R
q0, b -> q4, _, R
q0, _ -> qa, _, R
# Recordé una a: ir al final y comprobar
q1, a -> q1, a, R
q1, b -> q1, b, R
q1, _ -> q2, _, L
q2, a -> q3, _, L
q2, _ -> qa, _, R
# Recordé una b: ir al final y comprobar
q4, a -> q4, a, R
q4, b -> q4, b, R
q4, _ -> q5, _, L
q5, b -> q3, _, L
q5, _ -> qa, _, R
# Volver al inicio
q3, a -> q3, a, L
q3, b -> q3, b, L
q3, _ -> q0, _, R""")

ANBN = Definition(
    name="a^n b^n", start="q0", accept="q4", blank="_", sigma="a,b",
    rules="""# Marcar una a con X
q0, a -> q1, X, R
q0, Y -> q3, Y, R
# Buscar la primera b libre y marcarla con Y
q1, a -> q1, a, R
q1, Y -> q1, Y, R
q1, b -> q2, Y, L
# Regresar hasta la última X
q2, a -> q2, a, L
q2, Y -> q2, Y, L
q2, X -> q0, X, R
# Comprobar que no sobra nada
q3, Y -> q3, Y, R
q3, _ -> q4, _, R""")

PARENTESIS = Definition(
    name="Paréntesis balanceados", start="p0", accept="ok", blank="_", sigma="(,)",
    rules="""# Buscar el primer ) sin marcar
p0, ( -> p0, (, R
p0, X -> p0, X, R
p0, ) -> p1, X, L
p0, _ -> p2, _, L
# Buscar su ( correspondiente a la izquierda
p1, X -> p1, X, L
p1, ( -> p0, X, R
# Ya no hay ): verificar que no quede ningún (
p2, X -> p2, X, L
p2, _ -> ok, _, R""")

# --------------------------------------------------------------------------- utilidades
INCREMENTO = Definition(
    name="Incremento binario", start="q0", accept="qf", blank="_", sigma="0,1",
    rules="""# Ir al final del número
q0, 0 -> q0, 0, R
q0, 1 -> q0, 1, R
q0, _ -> q1, _, L
# Sumar 1 con acarreo
q1, 1 -> q1, 0, L
q1, 0 -> qf, 1, L
q1, _ -> qf, 1, L""")

COMPLEMENTO = Definition(
    name="Complemento a uno", start="q0", accept="qf", blank="_", sigma="0,1",
    rules="""q0, 0 -> q0, 1, R
q0, 1 -> q0, 0, R
q0, _ -> qf, _, L""")

COPIAR = Definition(
    name="Copiar cadena", start="k0", accept="kf", blank="_", sigma="0,1",
    rules="""# Escribir # al final
k0, 0 -> k0, 0, R
k0, 1 -> k0, 1, R
k0, _ -> k1, #, L
k1, 0 -> k1, 0, L
k1, 1 -> k1, 1, L
k1, _ -> k2, _, R
# Tomar el siguiente símbolo (marcarlo con X o Y)
k2, 0 -> c0, X, R
k2, 1 -> c1, Y, R
k2, # -> k5, #, L
# Llevar un 0 al final
c0, 0 -> c0, 0, R
c0, 1 -> c0, 1, R
c0, # -> c0, #, R
c0, _ -> k3, 0, L
# Llevar un 1 al final
c1, 0 -> c1, 0, R
c1, 1 -> c1, 1, R
c1, # -> c1, #, R
c1, _ -> k3, 1, L
# Volver a la última marca
k3, 0 -> k3, 0, L
k3, 1 -> k3, 1, L
k3, # -> k3, #, L
k3, X -> k2, X, R
k3, Y -> k2, Y, R
# Quitar las marcas
k5, X -> k5, 0, L
k5, Y -> k5, 1, L
k5, _ -> kf, _, R""")


def _lang_result(word: str, tm: TuringMachine, yes: str, no: str) -> Result:
    w = word or "cadena vacía"
    if tm.status == ACCEPT:
        return Result(True, "Aceptada", f"«{w}» {yes}.")
    return Result(False, "Rechazada", f"«{w}» {no}.")


def _binstr(v: dict) -> str | None:
    return None


SPECS: list[Spec] = [
    Spec("suma", "Aritmética", "Suma", "Suma dos números naturales usando aritmética binaria.",
         ["Convierte los números a binario: a+b.", "Resta 1 al segundo número y suma 1 al primero.",
          "Repite hasta que el segundo llegue a 0; lo que queda es a + b."],
         [Field("a", "Primer número", default="13", max=255), Field("b", "Segundo número", default="6", max=255)],
         SUMA, lambda v: f"{b2(v['a'])}+{b2(v['b'])}",
         lambda v, tm: Result(tm.status == ACCEPT, f"{v['a']} + {v['b']} = {_num(tm)}",
                              f"En binario: {b2(v['a'])} + {b2(v['b'])} = {tm.output()}")),
    Spec("resta", "Aritmética", "Resta", "Resta dos números naturales (el primero debe ser mayor o igual).",
         ["Convierte los números a binario: a-b.", "Resta 1 a cada número a la vez.",
          "Cuando el segundo llega a 0, borra todo y quita los ceros sobrantes."],
         [Field("a", "Minuendo", default="25", max=255), Field("b", "Sustraendo", default="9", max=255)],
         RESTA, lambda v: f"{b2(v['a'])}-{b2(v['b'])}",
         lambda v, tm: Result(tm.status == ACCEPT, f"{v['a']} − {v['b']} = {_num(tm)}",
                              f"En binario: {b2(v['a'])} − {b2(v['b'])} = {tm.output()}"),
         validate=lambda v: "El minuendo debe ser mayor o igual que el sustraendo: la máquina trabaja con números naturales."
         if int(v["a"]) < int(v["b"]) else None),
    Spec("mult", "Aritmética", "Multiplicación", "Multiplica dos números en notación unaria (cada número es una fila de unos).",
         ["Escribe a y b como unos: 3 × 2 queda 111*11=.", "Por cada 1 de a, copia todos los unos de b después del =.",
          "Al final borra los datos y deja solo el resultado."],
         [Field("a", "Primer número", default="3", max=9), Field("b", "Segundo número", default="4", max=9)],
         MULT, lambda v: "1" * int(v["a"]) + "*" + "1" * int(v["b"]) + "=",
         lambda v, tm: Result(tm.status == ACCEPT, f"{v['a']} × {v['b']} = {_ones(tm)}",
                              f"En unario: {'1' * int(v['a']) or '∅'} × {'1' * int(v['b']) or '∅'} = {tm.output() or '∅'}")),
    Spec("palindromo", "Lenguajes", "Palíndromos", "Decide si una cadena de a y b se lee igual al derecho y al revés.",
         ["Borra el primer símbolo y lo recuerda en su estado.", "Va al final y comprueba que el último sea igual.",
          "Si coinciden lo borra y repite; si no, se detiene y rechaza."],
         [Field("w", "Cadena (a y b)", kind="str", default="abba", allowed="ab", max_len=14)],
         PALINDROMO, lambda v: v["w"],
         lambda v, tm: _lang_result(v["w"], tm, "es un palíndromo", "no es un palíndromo")),
    Spec("anbn", "Lenguajes", "a^n b^n", "Acepta cadenas con n letras a seguidas de exactamente n letras b.",
         ["Marca una a con X.", "Busca la primera b libre y la marca con Y.",
          "Repite; al final solo deben quedar Y."],
         [Field("w", "Cadena (a y b)", kind="str", default="aaabbb", allowed="ab", max_len=16)],
         ANBN, lambda v: v["w"],
         lambda v, tm: _lang_result(v["w"], tm, "tiene tantas a como b, en orden", "no tiene la forma a^n b^n")),
    Spec("parentesis", "Lenguajes", "Paréntesis", "Comprueba que los paréntesis estén bien balanceados.",
         ["Busca el primer ) y lo marca con X.", "Retrocede hasta su ( y también lo marca.",
          "Al final no debe quedar ningún ( sin pareja."],
         [Field("w", "Paréntesis", kind="str", default="(()())", allowed="()", max_len=16)],
         PARENTESIS, lambda v: v["w"],
         lambda v, tm: _lang_result(v["w"], tm, "está balanceada", "no está balanceada")),
    Spec("incremento", "Utilidades", "Incremento", "Suma 1 a un número escrito en binario.",
         ["Avanza hasta el final del número.", "Desde la derecha cambia los 1 por 0 (acarreo).",
          "El primer 0 o blanco se convierte en 1."],
         [Field("n", "Número", default="11", max=4095)],
         INCREMENTO, lambda v: b2(v["n"]),
         lambda v, tm: Result(True, f"{v['n']} + 1 = {_num(tm)}", f"En binario: {b2(v['n'])} + 1 = {tm.output()}")),
    Spec("complemento", "Utilidades", "Complemento", "Invierte cada bit de una cadena binaria (complemento a uno).",
         ["Recorre la cadena de izquierda a derecha.", "Cambia cada 0 por 1 y cada 1 por 0.",
          "Se detiene al encontrar el blanco."],
         [Field("w", "Cadena binaria", kind="str", default="100110", allowed="01", max_len=16)],
         COMPLEMENTO, lambda v: v["w"],
         lambda v, tm: Result(True, tm.output() or "vacía", f"Entrada {v['w'] or 'vacía'}: cada 0 pasó a 1 y cada 1 pasó a 0.")),
    Spec("copiar", "Utilidades", "Copiar", "Duplica una cadena binaria: w se convierte en w#w.",
         ["Escribe # al final.", "Marca cada símbolo, lo lleva al final y vuelve.",
          "Al terminar quita las marcas."],
         [Field("w", "Cadena binaria", kind="str", default="1011", allowed="01", max_len=8)],
         COPIAR, lambda v: v["w"],
         lambda v, tm: Result(True, tm.output(), f"La cadena «{v['w'] or 'vacía'}», un # y su copia exacta.")),
]


def custom_spec(defn: Definition) -> Spec:
    """Crea una Spec a partir de una máquina hecha en el editor."""
    allowed = "".join(s for s in defn.sigma.replace(",", " ").split())

    def decode(v, tm):
        out = tm.output() or "vacía"
        if tm.status == ACCEPT:
            return Result(True, "Aceptada", f"Se detuvo en {tm.state}. Cinta final: {out}")
        return Result(False, "Rechazada", f"Se detuvo en {tm.state} sin regla para «{tm.read()}». Cinta final: {out}")

    return Spec("custom:" + defn.name, "Mis máquinas", defn.name, defn.description or "Máquina creada en el editor.",
                ["Definida por ti en el editor.", "Revisa la tabla de reglas en el panel de resultados."],
                [Field("w", "Entrada", kind="str", default=defn.input, allowed=allowed, max_len=24)],
                defn, lambda v: v["w"], decode, custom=True)


def validate_values(spec: Spec, raw: dict) -> tuple[dict, str | None]:
    """Valida y normaliza los datos escritos por el usuario."""
    vals = {}
    for f in spec.fields:
        txt = (raw.get(f.key) or "").strip()
        if f.kind == "int":
            if not txt.isdigit():
                return vals, f"«{f.label}» debe ser un número entero entre {f.min} y {f.max}."
            n = int(txt)
            if not f.min <= n <= f.max:
                return vals, f"«{f.label}» debe estar entre {f.min} y {f.max}."
            vals[f.key] = n
        else:
            if len(txt) > f.max_len:
                return vals, f"«{f.label}» admite como máximo {f.max_len} símbolos."
            if f.allowed:
                bad = [c for c in txt if c not in f.allowed]
                if bad:
                    return vals, f"El símbolo «{bad[0]}» no está permitido. Usa solo: {' '.join(f.allowed)}"
            vals[f.key] = txt
    err = spec.validate(vals)
    return vals, err

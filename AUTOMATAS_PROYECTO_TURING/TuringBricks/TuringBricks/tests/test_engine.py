"""Pruebas del motor y de todas las máquinas incluidas.  Ejecutar:  python -m tests.test_engine"""
import itertools, random, sys
from app.engine import parse, TuringMachine, ACCEPT, REJECT, Definition
from app.machines import SPECS, validate_values

def run(spec, vals):
    m = parse(spec.definition)
    assert not m.errors, (spec.key, m.errors)
    tm = TuringMachine(m)
    tm.load(spec.encode(vals))
    trace = tm.run()
    return tm, trace, spec.decode(vals, tm)

S = {s.key: s for s in SPECS}
fails = 0
def check(cond, msg):
    global fails
    if not cond:
        fails += 1; print('FALLA:', msg)

maxsteps = {}
for a in range(0, 41):
    for b in range(0, 41):
        tm, tr, r = run(S['suma'], {'a': a, 'b': b})
        check(tm.status == ACCEPT and int(tm.output(), 2) == a + b, f'suma {a}+{b} -> {tm.output()}')
        if a >= b:
            tm, tr, r = run(S['resta'], {'a': a, 'b': b})
            check(tm.status == ACCEPT and tm.output() == format(a - b, 'b'), f'resta {a}-{b} -> {tm.output()!r}')
for a, b in [(255, 255), (200, 37), (255, 0), (0, 255)]:
    tm, tr, r = run(S['suma'], {'a': a, 'b': b}); maxsteps['suma'] = max(maxsteps.get('suma', 0), tm.steps)
    check(int(tm.output(), 2) == a + b, f'suma grande {a}+{b}')
    if a >= b:
        tm, tr, r = run(S['resta'], {'a': a, 'b': b}); maxsteps['resta'] = max(maxsteps.get('resta', 0), tm.steps)
        check(tm.output() == format(a - b, 'b'), f'resta grande {a}-{b}')
for a in range(0, 10):
    for b in range(0, 10):
        tm, tr, r = run(S['mult'], {'a': a, 'b': b})
        check(tm.status == ACCEPT and tm.output() == '1' * (a * b), f'mult {a}x{b} -> {tm.output()!r}')
        maxsteps['mult'] = max(maxsteps.get('mult', 0), tm.steps)
for n in range(0, 300):
    tm, tr, r = run(S['incremento'], {'n': n})
    check(int(tm.output(), 2) == n + 1, f'inc {n}')
for L in range(0, 9):
    for w in map(''.join, itertools.product('ab', repeat=L)):
        tm, tr, r = run(S['palindromo'], {'w': w})
        check((tm.status == ACCEPT) == (w == w[::-1]), f'pal {w}')
        tm, tr, r = run(S['anbn'], {'w': w})
        n = len(w) // 2
        check((tm.status == ACCEPT) == (L > 0 and w == 'a' * n + 'b' * n), f'anbn {w}')
    for w in map(''.join, itertools.product('()', repeat=L)):
        d, ok = 0, True
        for c in w:
            d += 1 if c == '(' else -1
            if d < 0: ok = False
        ok = ok and d == 0
        tm, tr, r = run(S['parentesis'], {'w': w})
        check((tm.status == ACCEPT) == ok, f'par {w}')
    for w in map(''.join, itertools.product('01', repeat=min(L, 8))):
        tm, tr, r = run(S['complemento'], {'w': w})
        check(tm.output().strip('_') == ''.join('1' if c == '0' else '0' for c in w).lstrip('_') or w == '', f'comp {w} {tm.output()}')
        tm, tr, r = run(S['copiar'], {'w': w})
        check(tm.status == ACCEPT and tm.output() == w + '#' + w, f'copiar {w} -> {tm.output()}')
# complemento exacto (los 0 iniciales del resultado se conservan)
tm, tr, r = run(S['complemento'], {'w': '100110'}); check(tm.output() == '011001', 'comp exacto')
# validaciones
v, e = validate_values(S['resta'], {'a': '3', 'b': '9'}); check(e is not None, 'valida resta')
v, e = validate_values(S['suma'], {'a': '3x', 'b': '9'}); check(e is not None, 'valida entero')
v, e = validate_values(S['palindromo'], {'w': 'abc'}); check(e is not None, 'valida simbolos')
# errores del parser
m = parse(Definition(start='q0', rules='q0, a -> q1, b, X\nq0 a q1\nq0, a -> q1, b, R\nq0, a -> q2, b, L'))
check(len(m.errors) == 3, m.errors)
# retroceso
m = parse(S['anbn'].definition); tm = TuringMachine(m); tm.load('aabb')
for _ in range(5): tm.step()
snap = (dict(tm.tape), tm.head, tm.state); tm.step(); tm.back()
check(snap == (dict(tm.tape), tm.head, tm.state), 'back')
print('pasos máximos:', maxsteps)
print('OK' if not fails else f'{fails} fallas')
sys.exit(1 if fails else 0)

"""Guardar y cargar máquinas creadas por el usuario (archivos .json)."""
import json, re
from .config import MACHINES_DIR
from .engine import Definition


def _slug(name):
    s = re.sub(r"[^A-Za-z0-9áéíóúñÁÉÍÓÚÑ_-]+", "_", name.strip()) or "maquina"
    return s[:40]


def save(defn: Definition):
    MACHINES_DIR.mkdir(parents=True, exist_ok=True)
    path = MACHINES_DIR / f"{_slug(defn.name)}.json"
    path.write_text(json.dumps(defn.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_all():
    out = []
    if MACHINES_DIR.exists():
        for p in sorted(MACHINES_DIR.glob("*.json")):
            try:
                out.append(Definition.from_dict(json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                pass
    return out


def delete(name):
    p = MACHINES_DIR / f"{_slug(name)}.json"
    if p.exists():
        p.unlink()

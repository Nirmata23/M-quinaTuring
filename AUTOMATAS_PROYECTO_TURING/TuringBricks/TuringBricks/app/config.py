"""Rutas, colores y fuentes compartidas."""
import os, sys
from pathlib import Path

# Carpeta base (funciona tanto con Python como con el .exe de PyInstaller)
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
ASSETS = BASE / "assets"
SOUNDS = ASSETS / "sounds"
FONTS = ASSETS / "fonts"

# Carpeta del usuario para guardar máquinas propias
USER_DIR = Path(os.environ.get("APPDATA", Path.home())) / "TuringBricks"
MACHINES_DIR = USER_DIR / "maquinas"

APP_NAME = "Turing Bricks"

# Fuentes (archivos dentro de assets/fonts)
FONT_TITLE = "Fredoka-SemiBold.ttf"
FONT_BODY = "Nunito-Regular.ttf"
FONT_BOLD = "Nunito-Bold.ttf"
FONT_MONO = "JetBrainsMono-Bold.ttf"
FONT_MONO_REG = "JetBrainsMono-Regular.ttf"

# Paleta inspirada en los colores clásicos de los bloques de juguete
PALETTE = {
    "red": "#c91a09", "yellow": "#f2cd37", "blue": "#0055bf", "green": "#237841", "lime": "#bbe90b",
    "orange": "#fe8a18", "azure": "#36aebf", "purple": "#81007b", "magenta": "#c870a0", "tan": "#e4cd9e",
    "brown": "#583927", "white": "#f4f4f4", "lgray": "#a0a5a9", "dgray": "#6c6e68", "black": "#1b2a34",
    "dtan": "#958a73", "sand": "#a0bcac", "pink": "#fc97ac", "dblue": "#0a3463", "lblue": "#9fc3e9",
    "grass": "#4b9f4a", "dgreen": "#184632", "trans_red": "#c91a09", "trans_yel": "#f5cd2f",
}

# Color de cada símbolo de la cinta (bloque, texto)
SYMBOL_COLORS = {
    "0": ("blue", "white"), "1": ("yellow", "black"), "a": ("red", "white"), "b": ("green", "white"),
    "X": ("orange", "black"), "Y": ("purple", "white"), "A": ("orange", "black"), "B": ("purple", "white"),
    "+": ("dgray", "white"), "-": ("dgray", "white"), "*": ("dgray", "white"), "=": ("dgray", "white"),
    "#": ("black", "yellow"), "(": ("azure", "black"), ")": ("magenta", "black"),
}
EXTRA_SYMBOL_PALETTE = ["lime", "tan", "pink", "sand", "dtan", "lblue", "brown", "dblue"]


def symbol_style(sym: str, blank: str):
    if sym == blank:
        return "white", "lgray"
    if sym in SYMBOL_COLORS:
        return SYMBOL_COLORS[sym]
    k = EXTRA_SYMBOL_PALETTE[sum(map(ord, sym)) % len(EXTRA_SYMBOL_PALETTE)]
    return k, "black"

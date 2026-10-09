"""Turing Bricks: una máquina de Turing real construida con bloques en 3D.

Ejecutar:   python main.py
"""
import sys
from pathlib import Path

from ursina import Ursina, Entity, Text, application, window, color, camera

from app.config import BASE, FONTS, APP_NAME, FONT_BODY, FONT_MONO_REG, ASSETS


def main():
    application.asset_folder = BASE
    application.fonts_folder = FONTS
    kw = dict(title=APP_NAME, development_mode=False, borderless=False, vsync=True)
    icon = ASSETS / "icon.ico"
    if icon.exists():
        kw["icon"] = str(icon)
    if "--ventana" in sys.argv:
        kw["size"] = (1600, 900)
    app = Ursina(**kw)
    window.color = color.rgb(.62, .8, .95)
    for name in ("fps_counter", "entity_counter", "collider_counter", "cog_button", "exit_button"):
        e = getattr(window, name, None)
        if e is not None:
            e.enabled = False
    Text.default_font = FONT_BODY
    Text.default_monospace_font = FONT_MONO_REG
    Text.default_resolution = 1080 * Text.size * 2

    from app.gfx.shader import plastic_shader
    Entity.default_shader = plastic_shader

    from app.app import TuringBricksApp
    TuringBricksApp()
    app.run()


if __name__ == "__main__":
    main()

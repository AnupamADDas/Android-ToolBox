"""Locally bundled Lucide icons, rasterized at 3x for crisp Windows scaling."""

from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image

ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"


@lru_cache(maxsize=128)
def icon(name, color="#a2b2c9", size=20):
    with Image.open(ICON_DIR / f"ui-{name}.png") as source:
        image = Image.new("RGBA", source.size, color)
        image.putalpha(source.getchannel("A"))
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))

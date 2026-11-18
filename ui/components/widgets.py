"""Small explicit widget extensions; no global CustomTkinter monkey-patching."""

from customtkinter import (
    CTk, CTkImage, CTkLabel, CTkCheckBox, CTkProgressBar, CTkTextbox,
    CTkSegmentedButton, set_appearance_mode,
    get_appearance_mode, set_default_color_theme,
)
import customtkinter as _ctk
from PIL import Image, ImageDraw, ImageFilter

from ui.components.icons import icon
from utils.constants import (
    THEME_ACCENT, THEME_ACCENT_HOVER, THEME_BG_DARK, THEME_CARD_BORDER_DARK,
    THEME_SURFACE, THEME_SURFACE_HOVER, THEME_TEXT_PRIMARY_DARK,
)


class CTkFont(_ctk.CTkFont):
    def __init__(self, family=None, size=13, **kwargs):
        super().__init__(family=family or "Segoe UI", size=max(size, 12), **kwargs)


class CTkFrame(_ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        if kwargs.get("fg_color") != "transparent":
            radius = kwargs.get("corner_radius", 18)
            kwargs["corner_radius"] = max(radius, 18) if radius else 0
            kwargs.setdefault("border_width", 1)
            kwargs.setdefault("border_color", THEME_CARD_BORDER_DARK)
        super().__init__(master, **kwargs)


class CTkScrollableFrame(_ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        kwargs["corner_radius"] = 18
        super().__init__(master, **kwargs)


class CTkButton(_ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs["height"] = max(kwargs.get("height", 38), 34)
        kwargs.setdefault("corner_radius", 10)
        if kwargs.get("fg_color") == "#374151":
            kwargs["fg_color"] = THEME_SURFACE
        kwargs.setdefault("hover_color", THEME_SURFACE_HOVER)
        kwargs.setdefault("border_color", THEME_ACCENT)
        super().__init__(master, **kwargs)
        self._canvas.configure(takefocus=1)
        self._canvas.bind("<FocusIn>", lambda event: self.configure(border_width=2))
        self._canvas.bind("<FocusOut>", lambda event: self.configure(border_width=0))
        self._canvas.bind("<Return>", lambda event: self.invoke())
        self._canvas.bind("<space>", lambda event: self.invoke())
        self.bind("<ButtonPress-1>", self._press, add="+")
        self.bind("<ButtonRelease-1>", self._release, add="+")

    def _press(self, event):
        if self.cget("state") != "disabled":
            self.configure(border_width=2)

    def _release(self, event):
        self.configure(border_width=2 if self._canvas == self.focus_get() else 0)


class CTkEntry(_ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("height", 38)
        super().__init__(master, **kwargs)
        self.bind("<FocusIn>", lambda event: self.configure(border_color=THEME_ACCENT), add="+")
        self.bind("<FocusOut>", lambda event: self.configure(border_color=THEME_CARD_BORDER_DARK), add="+")


class CTkOptionMenu(_ctk.CTkOptionMenu):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("height", 38)
        super().__init__(master, **kwargs)


class CTkComboBox(_ctk.CTkComboBox):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("height", 38)
        super().__init__(master, **kwargs)


def primary(button, name=None):
    button.configure(
        fg_color=THEME_ACCENT, hover_color=THEME_ACCENT_HOVER,
        text_color=THEME_BG_DARK,
    )
    if name:
        button.configure(image=icon(name, THEME_BG_DARK, 18))
    return button


def button_icon(button, name, color=THEME_TEXT_PRIMARY_DARK):
    button.configure(image=icon(name, color, 18))
    return button


class GlowArt(CTkLabel):
    """A static blurred accent, not transparency over the user's desktop.

    The small Pillow image is generated once. It costs no animation timer,
    GPU context, network access or additional runtime dependency.
    """
    def __init__(self, master, bg="#152536", **kwargs):
        width, height = 260, 120
        base = Image.new("RGBA", (width, height), bg)
        glow = Image.new("RGBA", base.size)
        draw = ImageDraw.Draw(glow)
        draw.ellipse((62, 8, 164, 110), fill=(35, 194, 179, 110))
        draw.ellipse((146, 0, 226, 88), fill=(62, 132, 241, 115))
        base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(28)))
        # This is the same Lucide smartphone glyph used by navigation.
        from ui.components.icons import ICON_DIR
        with Image.open(ICON_DIR / "ui-smartphone.png") as source:
            glyph = Image.new("RGBA", source.size, "#b4eee8")
            glyph.putalpha(source.getchannel("A"))
        glyph = glyph.resize((64, 64), Image.Resampling.LANCZOS)
        base.alpha_composite(glyph, (118, 28))
        self.art = CTkImage(light_image=base, dark_image=base, size=(width, height))
        super().__init__(master, text="", image=self.art, width=width, height=height, **kwargs)

"""Native desktop interpretation of the shared design system."""

import ctypes
import os

import customtkinter as ctk

from utils.constants import (
    THEME_ACCENT, THEME_ACCENT_HOVER, THEME_BG_DARK, THEME_CARD_DARK,
    THEME_CARD_BORDER_DARK, THEME_INPUT_DARK, THEME_TEXT_PRIMARY_DARK,
    THEME_TEXT_SECONDARY_DARK, THEME_SURFACE, THEME_SURFACE_HOVER,
)


def configure_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    theme = ctk.ThemeManager.theme
    for name in ("CTk", "CTkToplevel"):
        theme[name]["fg_color"] = THEME_BG_DARK
    for values in theme.values():
        for key in ("text_color",):
            if key in values:
                values[key] = THEME_TEXT_PRIMARY_DARK
        if "text_color_disabled" in values:
            values["text_color_disabled"] = "#74859e"
        if "border_color" in values:
            values["border_color"] = THEME_CARD_BORDER_DARK
    theme["CTkFont"].update(family="Segoe UI", size=13)
    theme["CTkFrame"].update(
        corner_radius=18, border_width=0, fg_color=THEME_CARD_DARK,
        top_fg_color=THEME_CARD_DARK,
    )
    theme["CTkButton"].update(
        corner_radius=10, fg_color=THEME_SURFACE,
        hover_color=THEME_SURFACE_HOVER,
    )
    theme["CTkEntry"].update(
        corner_radius=10, border_width=1, fg_color=THEME_INPUT_DARK,
        placeholder_text_color=THEME_TEXT_SECONDARY_DARK,
    )
    theme["CTkTextbox"].update(
        corner_radius=12, fg_color=THEME_INPUT_DARK,
        scrollbar_button_color=THEME_SURFACE_HOVER,
    )
    theme["CTkOptionMenu"].update(
        corner_radius=10, fg_color=THEME_SURFACE,
        button_color=THEME_SURFACE, button_hover_color=THEME_SURFACE_HOVER,
    )
    theme["CTkComboBox"].update(
        corner_radius=10, border_width=1, fg_color=THEME_INPUT_DARK,
        button_color=THEME_SURFACE, button_hover_color=THEME_SURFACE_HOVER,
    )
    theme["CTkCheckBox"].update(
        corner_radius=5, border_width=2, fg_color=THEME_ACCENT,
        hover_color=THEME_ACCENT_HOVER, checkmark_color=THEME_BG_DARK,
    )
    theme["CTkProgressBar"].update(
        fg_color=THEME_SURFACE, progress_color=THEME_ACCENT,
    )
    theme["CTkSegmentedButton"].update(
        corner_radius=10, border_width=4, fg_color=THEME_INPUT_DARK,
        selected_color="#29485a", selected_hover_color="#345a6d",
        unselected_color=THEME_INPUT_DARK, unselected_hover_color=THEME_SURFACE,
    )
    theme["CTkScrollbar"].update(
        button_color=THEME_SURFACE, button_hover_color=THEME_SURFACE_HOVER,
    )
    theme["DropdownMenu"].update(
        fg_color=THEME_CARD_DARK, hover_color=THEME_SURFACE_HOVER,
    )


def style_window(window):
    """Use Windows' dark title bar and rounded window corners when available."""
    if os.name != "nt":
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        for attribute, value in ((20, 1), (33, 2), (35, 0x1D120C)):
            setting = ctypes.c_int(value)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(setting), ctypes.sizeof(setting)
            )
    except (AttributeError, OSError):
        pass  # The opaque theme also works on older Windows versions.

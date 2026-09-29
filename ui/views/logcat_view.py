import customtkinter as ctk
from tkinter import filedialog
from typing import Optional
from core.device_manager import device_manager
from core.logcat_streamer import logcat_streamer, LogEntry, LOG_LEVELS
from utils.constants import (
    MODE_DEVICE, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)

class LogcatView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self.min_level = 1
        self.auto_scroll = True
        self._build_ui()
        logcat_streamer.add_listener(self._on_log_entry)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Filter and Control Bar
        self.ctrl_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.ctrl_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 6))
        self.ctrl_card.grid_columnconfigure(1, weight=1)

        # Level selector
        self.cmb_level = ctk.CTkComboBox(
            self.ctrl_card, values=["Verbose", "Debug", "Info", "Warn", "Error"],
            width=100, command=self._on_level_changed
        )
        self.cmb_level.grid(row=0, column=0, padx=(15, 6), pady=8, sticky="w")
        self.cmb_level.set("Verbose")

        # Search filter
        self.entry_search = ctk.CTkEntry(self.ctrl_card, placeholder_text="Filter by tag or message text...")
        self.entry_search.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        # Action buttons
        self.btn_toggle_stream = ctk.CTkButton(
            self.ctrl_card, text="Start", width=75, command=self._toggle_stream
        )
        self.btn_toggle_stream.grid(row=0, column=2, padx=4, pady=8)

        self.btn_pause = ctk.CTkButton(
            self.ctrl_card, text="Pause", width=65, fg_color="#374151", command=self._toggle_pause
        )
        self.btn_pause.grid(row=0, column=3, padx=4, pady=8)

        self.btn_clear = ctk.CTkButton(
            self.ctrl_card, text="Clear", width=65, fg_color="#374151", command=self._clear_logs
        )
        self.btn_clear.grid(row=0, column=4, padx=4, pady=8)

        self.btn_export = ctk.CTkButton(
            self.ctrl_card, text="Export", width=70, fg_color="#374151", command=self._export_logs
        )
        self.btn_export.grid(row=0, column=5, padx=(4, 15), pady=8)

        # 2. Log Stream Text Display
        self.display_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.display_card.grid(row=1, column=0, sticky="nsew", padx=15, pady=(4, 15))
        self.display_card.grid_columnconfigure(0, weight=1)
        self.display_card.grid_rowconfigure(0, weight=1)

        self.txt_logs = ctk.CTkTextbox(
            self.display_card, font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none", fg_color="#18181b"
        )
        self.txt_logs.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # Configure color tags
        self.txt_logs.tag_config("V", foreground="#9ca3af")
        self.txt_logs.tag_config("D", foreground="#60a5fa")
        self.txt_logs.tag_config("I", foreground="#34d399")
        self.txt_logs.tag_config("W", foreground="#fbbf24")
        self.txt_logs.tag_config("E", foreground="#f87171")
        self.txt_logs.tag_config("F", foreground="#ef4444")

    def update_device(self, device):
        self.device = device
        if not device or device.mode != MODE_DEVICE:
            if logcat_streamer.is_running:
                logcat_streamer.stop()
            self.btn_toggle_stream.configure(text="Start", fg_color="#2563eb")
            return

    def _toggle_stream(self):
        if not self.device or self.device.mode != MODE_DEVICE:
            return

        if logcat_streamer.is_running:
            logcat_streamer.stop()
            self.btn_toggle_stream.configure(text="Start", fg_color="#2563eb")
        else:
            logcat_streamer.start(self.device.serial)
            self.btn_toggle_stream.configure(text="Stop", fg_color=COLOR_DANGER)

    def _toggle_pause(self):
        is_paused = logcat_streamer.toggle_pause()
        self.btn_pause.configure(text="Resume" if is_paused else "Pause")

    def _clear_logs(self):
        self.txt_logs.delete("1.0", "end")
        logcat_streamer.clear(self.device.serial if self.device else None)

    def _on_level_changed(self, value):
        lvl_map = {"Verbose": 1, "Debug": 2, "Info": 3, "Warn": 4, "Error": 5}
        self.min_level = lvl_map.get(value, 1)

    def _on_log_entry(self, entry: LogEntry):
        # Filter by level
        lvl_val = LOG_LEVELS.get(entry.level, 1)
        if lvl_val < self.min_level:
            return

        # Filter by text search
        query = self.entry_search.get().strip().lower()
        if query:
            if query not in entry.tag.lower() and query not in entry.message.lower():
                return

        def _append():
            tag = entry.level if entry.level in ["V", "D", "I", "W", "E", "F"] else "I"
            line = f"{entry.timestamp} {entry.level}/{entry.tag}({entry.pid}): {entry.message}\n"
            self.txt_logs.insert("end", line, tag)
            self.txt_logs.see("end")

        self.after(0, _append)

    def _export_logs(self):
        f = filedialog.asksaveasfilename(title="Save Logcat Output", defaultextension=".log", filetypes=[("Log Files", "*.log")])
        if f:
            logcat_streamer.export(f)

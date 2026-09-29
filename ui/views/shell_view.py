import threading
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional, List
from core.device_manager import device_manager
from core.adb_wrapper import adb_wrapper
from utils.constants import (
    MODE_DEVICE, MODE_RECOVERY, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    SHELL_PRESETS
)

class ShellView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self.history: List[str] = []
        self.history_index: int = -1
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Preset Toolbar
        self.preset_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.preset_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 6))

        ctk.CTkLabel(self.preset_card, text="Quick Commands:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, padx=(15, 8), pady=8, sticky="w"
        )

        preset_row = ctk.CTkFrame(self.preset_card, fg_color="transparent")
        preset_row.grid(row=0, column=1, padx=4, pady=8, sticky="w")

        for idx, (label, cmd) in enumerate(SHELL_PRESETS):
            ctk.CTkButton(
                preset_row, text=label, height=26, font=ctk.CTkFont(size=11),
                fg_color="#374151", command=lambda c=cmd: self._run_command(c)
            ).grid(row=0, column=idx, padx=3)

        # 2. Command Prompt Input
        self.cmd_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.cmd_card.grid(row=1, column=0, sticky="ew", padx=15, pady=4)
        self.cmd_card.grid_columnconfigure(0, weight=1)

        input_row = ctk.CTkFrame(self.cmd_card, fg_color="transparent")
        input_row.grid(row=0, column=0, padx=15, pady=(8, 4), sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        self.entry_cmd = ctk.CTkEntry(input_row, placeholder_text="Enter ADB shell command (e.g., pm list packages, ls -l /)...")
        self.entry_cmd.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.entry_cmd.bind("<Return>", lambda e: self._on_enter_pressed())
        self.entry_cmd.bind("<Up>", self._on_history_up)
        self.entry_cmd.bind("<Down>", self._on_history_down)

        self.btn_run = ctk.CTkButton(input_row, text="Execute", width=90, command=self._on_enter_pressed)
        self.btn_run.grid(row=0, column=1, sticky="e")

        # Options below input
        opts_row = ctk.CTkFrame(self.cmd_card, fg_color="transparent")
        opts_row.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="ew")
        opts_row.grid_columnconfigure(2, weight=1)

        self.chk_root = ctk.CTkCheckBox(opts_row, text="Prefix with su -c (Root)", height=18, checkbox_width=16, checkbox_height=16)
        self.chk_root.grid(row=0, column=0, padx=(0, 15))

        self.btn_clear = ctk.CTkButton(opts_row, text="Clear", width=65, height=22, font=ctk.CTkFont(size=11), fg_color="#374151", command=self._clear_terminal)
        self.btn_clear.grid(row=0, column=1, padx=4)

        self.btn_export = ctk.CTkButton(opts_row, text="Export Output", width=95, height=22, font=ctk.CTkFont(size=11), fg_color="#374151", command=self._export_output)
        self.btn_export.grid(row=0, column=2, padx=4, sticky="e")

        # 3. Output Terminal
        self.terminal_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.terminal_card.grid(row=2, column=0, sticky="nsew", padx=15, pady=(4, 15))
        self.terminal_card.grid_columnconfigure(0, weight=1)
        self.terminal_card.grid_rowconfigure(0, weight=1)

        self.txt_output = ctk.CTkTextbox(
            self.terminal_card, font=ctk.CTkFont(family="Consolas", size=12),
            wrap="char", fg_color="#18181b"
        )
        self.txt_output.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.txt_output.insert("end", "$ ADB Shell Terminal Ready.\n$ Connect device and enter command above.\n\n")

    def update_device(self, device):
        self.device = device
        if device:
            if device.mode == MODE_RECOVERY:
                self.chk_root.select()
                self._append_text(f"Device connected in RECOVERY mode ({device.serial}). Root shell active by default.\n\n")
            else:
                self._append_text(f"Device connected ({device.model} - {device.serial}).\n\n")
        else:
            self._append_text("No device connected.\n\n")

    def _on_enter_pressed(self):
        cmd = self.entry_cmd.get().strip()
        if not cmd:
            return
        self.history.append(cmd)
        self.history_index = len(self.history)
        self.entry_cmd.delete(0, "end")
        self._run_command(cmd)

    def _on_history_up(self, event):
        if not self.history:
            return "break"
        if self.history_index > 0:
            self.history_index -= 1
        elif self.history_index == -1:
            self.history_index = len(self.history) - 1

        self.entry_cmd.delete(0, "end")
        self.entry_cmd.insert(0, self.history[self.history_index])
        return "break"

    def _on_history_down(self, event):
        if not self.history or self.history_index == -1:
            return "break"
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry_cmd.delete(0, "end")
            self.entry_cmd.insert(0, self.history[self.history_index])
        else:
            self.history_index = -1
            self.entry_cmd.delete(0, "end")
        return "break"

    def _run_command(self, cmd_text: str):
        if not self.device:
            self._append_text("[Error] No device connected.\n\n")
            return

        final_cmd = cmd_text
        if bool(self.chk_root.get()) and self.device.mode == MODE_DEVICE:
            final_cmd = f"su -c '{cmd_text}'"

        prompt = "# " if (bool(self.chk_root.get()) or self.device.mode == MODE_RECOVERY) else "$ "
        self._append_text(f"{prompt}{cmd_text}\n")

        def _worker():
            c, out, err = adb_wrapper.shell(final_cmd, device_serial=self.device.serial, timeout=30)
            res = (out + "\n" + err).strip()
            self.after(0, lambda: self._append_text(f"{res}\n\n" if res else "[No output]\n\n"))

        threading.Thread(target=_worker, daemon=True).start()

    def _append_text(self, text: str):
        self.txt_output.insert("end", text)
        self.txt_output.see("end")

    def _clear_terminal(self):
        self.txt_output.delete("1.0", "end")

    def _export_output(self):
        f = filedialog.asksaveasfilename(title="Export Terminal Log", defaultextension=".txt", filetypes=[("Text File", "*.txt")])
        if f:
            try:
                with open(f, "w", encoding="utf-8") as file:
                    file.write(self.txt_output.get("1.0", "end"))
            except Exception:
                pass

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
from core.device_manager import device_manager
from core.sideload_manager import sideload_manager
from core.fastboot_wrapper import fastboot_wrapper
from utils.constants import (
    MODE_SIDELOAD, MODE_RECOVERY, MODE_FASTBOOT,
    THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO, COLOR_DANGER,
    FASTBOOT_PARTITIONS
)

class FlashingView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Top Section: ADB Sideload (ROM / Kernel / Magisk ZIP)
        self.sideload_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.sideload_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.sideload_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.sideload_card, text="ADB Sideload (Custom ROM / Kernel / ZIP)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            self.sideload_card,
            text="Flash recovery-flashable packages (.zip) when device is in Sideload or Recovery mode.",
            text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # ZIP File Selector
        zip_picker_frame = ctk.CTkFrame(self.sideload_card, fg_color="transparent")
        zip_picker_frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        zip_picker_frame.grid_columnconfigure(0, weight=1)

        self.entry_zip = ctk.CTkEntry(zip_picker_frame, placeholder_text="Select a .zip file (ROM, Kernel, Magisk, OTA)...")
        self.entry_zip.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_browse_zip = ctk.CTkButton(
            zip_picker_frame, text="Browse ZIP", width=110, command=self._browse_zip
        )
        self.btn_browse_zip.grid(row=0, column=1, sticky="e")

        # Action Buttons & Helpers
        zip_action_frame = ctk.CTkFrame(self.sideload_card, fg_color="transparent")
        zip_action_frame.grid(row=3, column=0, padx=15, pady=(8, 12), sticky="ew")
        zip_action_frame.grid_columnconfigure(2, weight=1)

        self.btn_start_sideload = ctk.CTkButton(
            zip_action_frame, text="Start Sideload", width=140, command=self._start_sideload
        )
        self.btn_start_sideload.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.btn_reboot_sideload = ctk.CTkButton(
            zip_action_frame, text="Reboot to Sideload", width=150, fg_color="#374151",
            command=lambda: self._reboot("sideload")
        )
        self.btn_reboot_sideload.grid(row=0, column=1, padx=(0, 8), sticky="w")

        self.btn_cancel_sideload = ctk.CTkButton(
            zip_action_frame, text="Cancel", width=90, fg_color=COLOR_DANGER,
            command=self._cancel_sideload, state="disabled"
        )
        self.btn_cancel_sideload.grid(row=0, column=2, sticky="e")

        # Sideload Progress Bar & Status Text
        self.progress_sideload = ctk.CTkProgressBar(self.sideload_card, height=10)
        self.progress_sideload.grid(row=4, column=0, padx=15, pady=(0, 4), sticky="ew")
        self.progress_sideload.set(0)

        self.lbl_sideload_status = ctk.CTkLabel(
            self.sideload_card, text="Ready", font=ctk.CTkFont(size=12),
            text_color=THEME_TEXT_SECONDARY_DARK
        )
        self.lbl_sideload_status.grid(row=5, column=0, padx=15, pady=(0, 12), sticky="w")

        # 2. Bottom Section: Fastboot Flasher (Bootloader Mode)
        self.fastboot_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.fastboot_card.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.fastboot_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.fastboot_card, text="Fastboot Partition Flasher",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            self.fastboot_card,
            text="Flash partition image files (.img) directly when device is in Fastboot / Bootloader mode.",
            text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Partition Selector & File Picker
        fb_pick_frame = ctk.CTkFrame(self.fastboot_card, fg_color="transparent")
        fb_pick_frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        fb_pick_frame.grid_columnconfigure(1, weight=1)

        self.cmb_partition = ctk.CTkComboBox(
            fb_pick_frame, values=FASTBOOT_PARTITIONS, width=140
        )
        self.cmb_partition.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.cmb_partition.set("boot")

        self.entry_img = ctk.CTkEntry(fb_pick_frame, placeholder_text="Select a partition image (.img)...")
        self.entry_img.grid(row=0, column=1, padx=(0, 8), sticky="ew")

        self.btn_browse_img = ctk.CTkButton(
            fb_pick_frame, text="Browse IMG", width=110, command=self._browse_img
        )
        self.btn_browse_img.grid(row=0, column=2, sticky="e")

        # Fastboot Actions
        fb_actions_frame = ctk.CTkFrame(self.fastboot_card, fg_color="transparent")
        fb_actions_frame.grid(row=3, column=0, padx=15, pady=(8, 12), sticky="ew")

        self.btn_flash_partition = ctk.CTkButton(
            fb_actions_frame, text="Flash Partition", width=140, command=self._flash_partition
        )
        self.btn_flash_partition.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.btn_erase_partition = ctk.CTkButton(
            fb_actions_frame, text="Erase Partition", width=130, fg_color="#374151",
            command=self._erase_partition
        )
        self.btn_erase_partition.grid(row=0, column=1, padx=(0, 8), sticky="w")

        self.btn_fb_reboot_sys = ctk.CTkButton(
            fb_actions_frame, text="Reboot to System", width=130, fg_color="#374151",
            command=lambda: self._reboot("system")
        )
        self.btn_fb_reboot_sys.grid(row=0, column=2, padx=(0, 8), sticky="w")

        self.btn_fb_reboot_rec = ctk.CTkButton(
            fb_actions_frame, text="Reboot to Recovery", width=140, fg_color="#374151",
            command=lambda: self._reboot("recovery")
        )
        self.btn_fb_reboot_rec.grid(row=0, column=3, padx=(0, 8), sticky="w")

        # Fastboot Output Text
        self.txt_fb_log = ctk.CTkTextbox(self.fastboot_card, height=110, font=ctk.CTkFont(family="Consolas", size=11))
        self.txt_fb_log.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.txt_fb_log.insert("end", "Fastboot log will appear here.\n")
        self.txt_fb_log.configure(state="disabled")

    def update_device(self, device):
        self.device = device
        if not device:
            self.lbl_sideload_status.configure(text="No device connected.")
            return

        if device.mode == MODE_SIDELOAD:
            self.lbl_sideload_status.configure(text="🟢 Device is ready in Sideload Mode.", text_color=COLOR_SUCCESS)
        elif device.mode == MODE_RECOVERY:
            self.lbl_sideload_status.configure(text="Device in Recovery Mode. You can start sideload or use 'Reboot to Sideload'.")
        elif device.mode == MODE_FASTBOOT:
            self.lbl_sideload_status.configure(text="Device in Fastboot Mode. Sideload requires Recovery Mode.")
        else:
            self.lbl_sideload_status.configure(text="Device in Android OS. Click 'Reboot to Sideload' to prepare.")

    def _browse_zip(self):
        f = filedialog.askopenfilename(
            title="Select ZIP Package",
            filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")]
        )
        if f:
            self.entry_zip.delete(0, "end")
            self.entry_zip.insert(0, f)

    def _browse_img(self):
        f = filedialog.askopenfilename(
            title="Select Partition Image",
            filetypes=[("IMG Files", "*.img"), ("All Files", "*.*")]
        )
        if f:
            self.entry_img.delete(0, "end")
            self.entry_img.insert(0, f)

    def _start_sideload(self):
        zip_path = self.entry_zip.get().strip()
        if not zip_path or not os.path.isfile(zip_path):
            messagebox.showwarning("Sideload", "Please select a valid .zip file first.")
            return

        if not self.device:
            messagebox.showwarning("Sideload", "No device connected.")
            return

        self.btn_start_sideload.configure(state="disabled")
        self.btn_cancel_sideload.configure(state="normal")
        self.progress_sideload.set(0)
        self.lbl_sideload_status.configure(text="Starting sideload transfer...", text_color=COLOR_INFO)

        def _on_progress(pct: float, line: str):
            def _update():
                if pct >= 0:
                    self.progress_sideload.set(pct)
                self.lbl_sideload_status.configure(text=line)
            self.after(0, _update)

        def _on_finish(code: int, msg: str):
            def _done():
                self.btn_start_sideload.configure(state="normal")
                self.btn_cancel_sideload.configure(state="disabled")
                if code == 0:
                    self.progress_sideload.set(1.0)
                    self.lbl_sideload_status.configure(text="Sideload completed successfully!", text_color=COLOR_SUCCESS)
                    messagebox.showinfo("Sideload Finished", "Package installed successfully via sideload.")
                else:
                    self.lbl_sideload_status.configure(text=f"Failed (Code {code})", text_color=COLOR_DANGER)
                    messagebox.showerror("Sideload Error", msg)
            self.after(0, _done)

        sideload_manager.start_sideload(
            zip_path=zip_path,
            on_progress=_on_progress,
            on_finish=_on_finish,
            serial=self.device.serial
        )

    def _cancel_sideload(self):
        sideload_manager.cancel_sideload()
        self.btn_cancel_sideload.configure(state="disabled")
        self.btn_start_sideload.configure(state="normal")
        self.lbl_sideload_status.configure(text="Sideload cancelled by user.", text_color=COLOR_WARNING)

    def _flash_partition(self):
        img_path = self.entry_img.get().strip()
        partition = self.cmb_partition.get().strip()

        if not img_path or not os.path.isfile(img_path):
            messagebox.showwarning("Fastboot Flash", "Please select a valid partition image (.img) file.")
            return

        if not partition:
            messagebox.showwarning("Fastboot Flash", "Please specify a partition.")
            return

        if not self.device or self.device.mode != MODE_FASTBOOT:
            proceed = messagebox.askyesno(
                "Device Check",
                "Device is not detected in Fastboot mode. Do you want to attempt flashing anyway?"
            )
            if not proceed:
                return

        self._log_fb(f"Flashing partition '{partition}' with '{os.path.basename(img_path)}'...\n")

        def _worker():
            def _stream_line(line):
                self.after(0, lambda: self._log_fb(line))

            code, log = fastboot_wrapper.flash(
                partition=partition,
                image_path=img_path,
                device_serial=self.device.serial if self.device else None,
                on_output=_stream_line
            )

            if code == 0:
                self.after(0, lambda: messagebox.showinfo("Fastboot Flash", f"Partition '{partition}' flashed successfully!"))
            else:
                self.after(0, lambda: messagebox.showerror("Fastboot Flash Failed", f"Flashing failed with code {code}."))

        threading.Thread(target=_worker, daemon=True).start()

    def _erase_partition(self):
        partition = self.cmb_partition.get().strip()
        if not partition:
            return

        confirm = messagebox.askyesno("Confirm Erase", f"Are you sure you want to erase partition '{partition}'?")
        if not confirm:
            return

        def _worker():
            c, o, e = fastboot_wrapper.run(
                ["erase", partition],
                device_serial=self.device.serial if self.device else None
            )
            out = (o + "\n" + e).strip()
            self.after(0, lambda: self._log_fb(f"Erase {partition}: {out}\n"))

        threading.Thread(target=_worker, daemon=True).start()

    def _reboot(self, target: str):
        if not self.device:
            messagebox.showwarning("Reboot", "No device connected.")
            return

        def _worker():
            c, out = device_manager.reboot(target)
            self.after(0, lambda: self._log_fb(f"Reboot {target}: {out or 'Sent'}\n"))

        threading.Thread(target=_worker, daemon=True).start()

    def _log_fb(self, text: str):
        self.txt_fb_log.configure(state="normal")
        self.txt_fb_log.insert("end", text)
        self.txt_fb_log.see("end")
        self.txt_fb_log.configure(state="disabled")

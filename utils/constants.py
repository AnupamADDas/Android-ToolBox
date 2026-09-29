import os
import sys

APP_NAME = "Android Toolbox"
APP_VERSION = "1.0.0"

# Colors for modern minimalist theme (Windows 11 Fluent inspired)
THEME_ACCENT = "#2563eb"         # Modern Indigo/Blue
THEME_ACCENT_HOVER = "#1d4ed8"
THEME_BG_DARK = "#18181b"        # Zinc 900
THEME_CARD_DARK = "#27272a"      # Zinc 800
THEME_CARD_BORDER_DARK = "#3f3f46"# Zinc 700
THEME_INPUT_DARK = "#1f1f23"
THEME_TEXT_PRIMARY_DARK = "#f4f4f5"
THEME_TEXT_SECONDARY_DARK = "#a1a1aa"

COLOR_SUCCESS = "#10b981"        # Emerald
COLOR_WARNING = "#f59e0b"        # Amber
COLOR_INFO = "#3b82f6"           # Blue
COLOR_DANGER = "#ef4444"         # Rose / Red
COLOR_MUTED = "#71717a"          # Zinc 500

# Device Modes
MODE_DEVICE = "device"
MODE_RECOVERY = "recovery"
MODE_SIDELOAD = "sideload"
MODE_FASTBOOT = "fastboot"
MODE_UNAUTHORIZED = "unauthorized"
MODE_OFFLINE = "offline"
MODE_UNKNOWN = "unknown"

# Common Fastboot partitions
FASTBOOT_PARTITIONS = [
    "boot",
    "recovery",
    "init_boot",
    "vendor_boot",
    "vbmeta",
    "dtbo",
    "system",
    "vendor",
    "product"
]

# Quick diagnostic shell commands
SHELL_PRESETS = [
    ("Disk Usage", "df -h"),
    ("Memory Info", "dumpsys meminfo"),
    ("Top Processes", "top -n 1"),
    ("Network Interfaces", "ip addr show"),
    ("Props (Filtered)", "getprop | grep -E 'model|version|brand'"),
    ("Battery Dumpsys", "dumpsys battery")
]

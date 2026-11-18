import os
import sys

APP_NAME = "Android Toolbox"
APP_VERSION = "1.2.0"

# Shared midnight palette. Colour identifies actions, tools, and device state.
THEME_ACCENT = "#53d9cf"
THEME_ACCENT_HOVER = "#80e8df"
THEME_BG_DARK = "#0c121d"
THEME_CARD_DARK = "#151f2e"
THEME_CARD_BORDER_DARK = "#28364a"
THEME_INPUT_DARK = "#101926"
THEME_TEXT_PRIMARY_DARK = "#edf3fc"
THEME_TEXT_SECONDARY_DARK = "#a2b2c9"
THEME_SIDEBAR = "#101925"
THEME_SURFACE = "#1e2d41"
THEME_SURFACE_HOVER = "#2c4058"

COLOR_SUCCESS = "#66dfb0"
COLOR_WARNING = "#f6c177"
COLOR_INFO = "#79b8ff"
COLOR_DANGER = "#ff8196"
COLOR_MUTED = "#8293ad"

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

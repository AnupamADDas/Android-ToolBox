"""Development-only: rasterize the checked-in Lucide SVGs (pip install resvg-py).

Runtime uses Pillow and the bundled PNGs, including in PyInstaller builds.
"""
from pathlib import Path
import resvg_py


def main():
    folder = Path(__file__).resolve().parents[1] / "assets" / "icons"
    for path in folder.glob("ui-*.svg"):
        svg = path.read_text(encoding="utf-8").replace("currentColor", "#ffffff")
        path.with_suffix(".png").write_bytes(
            resvg_py.svg_to_bytes(svg_string=svg, width=96, height=96)
        )


if __name__ == "__main__":
    main()

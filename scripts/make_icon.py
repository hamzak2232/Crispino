# Create assets/icon.ico without Cairo.
# It tries ImageMagick if available for SVG input; otherwise uses Pillow on a PNG.
# Usage:
#   python scripts/make_icon.py                 # uses app/static/logo.svg if 'magick' is installed
#   python scripts/make_icon.py --png path\to\logo.png
#
from __future__ import annotations

import argparse
import shutil
import subprocess
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from PIL import Image  # pip install pillow

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SVG = REPO / "app" / "static" / "logo.svg"
DEFAULT_PNG = REPO / "app" / "static" / "logo.png"
ASSETS_DIR = REPO / "assets"
OUT_ICO = ASSETS_DIR / "icon.ico"
SIZES = [256, 128, 64, 48, 32, 16]


def run_magick(svg: Path, out_ico: Path) -> None:
    magick = shutil.which("magick")
    if not magick:
        raise RuntimeError("ImageMagick ('magick') not found in PATH.")
    out_ico.parent.mkdir(parents=True, exist_ok=True)
    # Build ICO with multiple sizes from SVG
    cmd = [
        magick,
        str(svg),
        "-background",
        "none",
        "-resize",
        "256x256",
        "-define",
        "icon:auto-resize=256,128,64,48,32,16",
        str(out_ico),
    ]
    subprocess.run(cmd, check=True)
    print(f"Created {out_ico} via ImageMagick from {svg}")


def make_ico_from_png(png: Path, out_ico: Path, sizes: List[int]) -> None:
    out_ico.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png).convert("RGBA")
    img.save(out_ico, sizes=[(s, s) for s in sizes], format="ICO")
    print(f"Created {out_ico} from PNG {png} with sizes {sizes}")


def main():
    parser = argparse.ArgumentParser(description="Create assets/icon.ico without Cairo")
    parser.add_argument("--png", type=str, help="Path to a PNG to use instead of SVG")
    parser.add_argument("--svg", type=str, help="Path to an SVG (requires ImageMagick)")
    args = parser.parse_args()

    svg = Path(args.svg) if args.svg else DEFAULT_SVG
    png = Path(args.png) if args.png else None

    # Prefer user-provided PNG, else default PNG, else SVG via ImageMagick
    if png and png.exists():
        make_ico_from_png(png, OUT_ICO, SIZES)
        return

    if DEFAULT_PNG.exists():
        make_ico_from_png(DEFAULT_PNG, OUT_ICO, SIZES)
        return

    if svg.exists():
        try:
            run_magick(svg, OUT_ICO)
            return
        except Exception as e:
            raise SystemExit(
                f"Failed to convert SVG via ImageMagick: {e}\n"
                f"Options:\n"
                f"  1) Install ImageMagick and re-run (see instructions), or\n"
                f"  2) Export logo.svg to a PNG (e.g., logo-512.png) and run:\n"
                f"     python scripts/make_icon.py --png app\\static\\logo-512.png"
            )
    raise SystemExit(
        f"No input found.\n"
        f"Provide a PNG via --png, or place app/static/logo.png, or place app/static/logo.svg and install ImageMagick."
    )


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""PNG/BMP/TIFF -> FGL ASCII-hex graphics for BOCA Lemur / Ghostwriter printers.

Algorithm (matches BOCA FGL Programming Guide, p.37 + rsmck.co.uk/blog/boca-image):
  1. Greyscale + threshold (or Floyd-Steinberg dither + threshold).
  2. Pad height to a multiple of 8.
  3. For each 8-row strip, pack column-major MSB-top into one byte.
  4. Emit `<RC{row0+8s},{col0}><g{2W}>HEX...` per strip.

Optional --logo-id wraps output in `<IDn>` + ESC (0x1B) brackets so the result
is a downloadable logo recallable via `<SPr,c><LDn>`.

Validation of generated FGL is handled by the plugin's PostToolUse hook, which
runs `python -m fgl_validator <path>`. Run that directly if you want to lint a
file outside Claude Code.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ESC = "\x1b"


def require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "Pillow is required for image conversion. Install with:\n"
            "    python3 -m pip install pillow\n"
        )
        sys.exit(2)


def convert_image(args: argparse.Namespace) -> str:
    require_pillow()
    from PIL import Image

    img = Image.open(args.input).convert("L")
    if args.max_width and img.width > args.max_width:
        new_h = round(img.height * args.max_width / img.width)
        img = img.resize((args.max_width, new_h))

    if args.dither:
        bw = img.convert("1")  # Pillow's default convert("1") uses Floyd-Steinberg
    else:
        bw = img.point(lambda p: 0 if p < args.threshold else 255, mode="1")

    w, h = bw.size
    pad = (-h) % 8
    if pad:
        from PIL import ImageOps
        bw = ImageOps.expand(bw, border=(0, 0, 0, pad), fill=255)
        h += pad

    pixels = bw.load()  # 0 = black, 255 = white in mode "1"
    strips = h // 8
    lines: list[str] = []
    for s in range(strips):
        row_anchor = args.row + s * 8
        hex_bytes: list[str] = []
        for c in range(w):
            byte = 0
            for bit in range(8):
                y = s * 8 + bit
                if pixels[c, y] == 0:  # black
                    byte |= 1 << (7 - bit)
            hex_bytes.append(f"{byte:02X}")
        lines.append(f"<RC{row_anchor},{args.col}><g{2 * w}>" + "".join(hex_bytes))

    body = "\n".join(lines) + "\n"

    if args.logo_id is not None:
        body = f"<ID{args.logo_id}>{ESC}\n{body}{ESC}\n"

    return body


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="image path (PNG/BMP/TIFF)")
    p.add_argument("--threshold", type=int, default=128, help="0..255 (default 128)")
    p.add_argument("--dither", action="store_true", help="Floyd-Steinberg dither before threshold")
    p.add_argument("--max-width", type=int, default=0, help="resize so width <= N dots")
    p.add_argument("--row", type=int, default=0, help="anchor row")
    p.add_argument("--col", type=int, default=0, help="anchor column")
    p.add_argument("--logo-id", type=int, default=None, help="wrap as downloadable logo with this ID")
    p.add_argument("--output", default="-", help="output path (default stdout)")

    args = p.parse_args()

    fgl = convert_image(args)
    if args.output == "-":
        sys.stdout.write(fgl)
    else:
        Path(args.output).write_text(fgl)
    return 0


if __name__ == "__main__":
    sys.exit(main())

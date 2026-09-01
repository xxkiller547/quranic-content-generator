#!/usr/bin/env python3
from pathlib import Path
import argparse
import io

from PIL import Image, ImageColor
import cairosvg


def render_svg_fitted(svg_path: Path, max_width: int, max_height: int, render_scale: int = 3) -> Image.Image:
    """
    Rasterize an SVG, then downscale (preserving aspect ratio) so it fits
    entirely within (max_width, max_height). Renders at a higher resolution
    first (render_scale) so the downscale stays crisp.
    """
    png_bytes = cairosvg.svg2png(url=str(svg_path), output_width=max(1, int(max_width * render_scale)))
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    return img


def recolor(img: Image.Image, hex_color: str) -> Image.Image:
    """Replace all opaque pixels with a solid color, keeping the original alpha (shape)."""
    rgb = ImageColor.getrgb(hex_color)
    alpha = img.split()[3]
    solid = Image.new("RGBA", img.size, rgb + (0,))
    solid.putalpha(alpha)
    return solid


def compose_surah_page(
    base_path: Path,
    surah_number: int,
    svg_dir: Path,
    output_path: Path,
    max_width_frac: float = 0.55,
    max_height_frac: float = 0.16,
    gap: int = 20,
    color: str = "#FFFFFF",
) -> Path:
    """
    Paste 000.svg (the word "سورة") and NNN.svg (the surah name) centered
    in the middle of the base image, stacked vertically, each capped to
    max_width_frac x max_height_frac of the base image's size, and
    recolored to `color`.
    """
    base_path = Path(base_path)
    svg_dir = Path(svg_dir)
    output_path = Path(output_path)

    word_svg = svg_dir / "000.svg"
    name_svg = svg_dir / f"{surah_number:03d}.svg"

    for p in (base_path, word_svg, name_svg):
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")

    base_img = Image.open(base_path).convert("RGBA")
    max_w = int(base_img.width * max_width_frac)
    max_h = int(base_img.height * max_height_frac)

    word_png = recolor(render_svg_fitted(word_svg, max_w, max_h), color)
    name_png = recolor(render_svg_fitted(name_svg, max_w, max_h), color)

    total_height = word_png.height + gap + name_png.height
    start_y = (base_img.height - total_height) // 2

    word_x = (base_img.width - word_png.width) // 2
    base_img.alpha_composite(word_png, (word_x, start_y))

    name_x = (base_img.width - name_png.width) // 2
    name_y = start_y + word_png.height + gap
    base_img.alpha_composite(name_png, (name_x, name_y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_img.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Compose a surah title page from a base image and two SVGs."
    )
    parser.add_argument("--base", required=True, type=Path, help="Path to the base page image (png/jpg).")
    parser.add_argument("--surah", required=True, type=int, help="Surah number, e.g. 1 for الفاتحة.")
    parser.add_argument("--svg-dir", required=True, type=Path, help="Folder containing 000.svg and NNN.svg files.")
    parser.add_argument("--out", required=True, type=Path, help="Output image path.")
    parser.add_argument("--max-width-frac", type=float, default=0.55, help="Max overlay width as a fraction of base width (default 0.55).")
    parser.add_argument("--max-height-frac", type=float, default=0.16, help="Max overlay height as a fraction of base height (default 0.16).")
    parser.add_argument("--gap", type=int, default=20, help="Vertical gap in pixels between the two overlays.")
    parser.add_argument("--color", type=str, default="#fcda84", help="Hex color to recolor overlays to (default white).")
    args = parser.parse_args()

    result = compose_surah_page(
        args.base, args.surah, args.svg_dir, args.out,
        args.max_width_frac, args.max_height_frac, args.gap, args.color,
    )
    print(f"Saved: {result}")


if __name__ == "__main__":
    main()

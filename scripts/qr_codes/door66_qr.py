#!/usr/bin/env python3
"""
Generate a 3×3 inch Door66 promotional QR graphic.

Creates a square image with:
  - Dark green (#080d08) background with radial vignette
  - Gold (#c9b896) diamond QR code → door66.events
  - "door66.events" text beneath the QR diamond

Uses the existing qr_generator module for QR rendering.

Usage:
    python door66_qr.py
    python door66_qr.py --dpi 600
    python door66_qr.py -o door66_promo.png
"""

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Import our existing generator
sys.path.insert(0, str(Path(__file__).parent))
from qr_generator import generate_qr, parse_color, _find_font, _render_keyhole


BG_COLOR = "#1a2e1a"
FG_COLOR = "#d4c69e"


def _make_vignette(size, bg_rgba):
    """Create a vignette layer: brighter center fading to darker edges."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    # Draw concentric semi-transparent black rings from outside in,
    # with decreasing opacity toward center → natural vignette
    steps = 80
    max_radius = size * 0.75  # vignette outer reach
    for i in range(steps):
        t = i / steps  # 0 = outermost ring, 1 = center
        r = max_radius * (1.0 - t)
        # Opacity: strong at edges, zero at center
        alpha = int(120 * (1.0 - t) ** 1.8)
        if alpha < 1:
            continue
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(0, 0, 0, alpha),
        )

    # Slight Gaussian blur for smoothness
    img = img.filter(ImageFilter.GaussianBlur(radius=size * 0.03))

    # Add a subtle bright glow at center
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_r = size * 0.30
    glow_steps = 40
    for i in range(glow_steps):
        t = i / glow_steps
        r = glow_r * (1.0 - t)
        # Lighten the background color slightly at center
        alpha = int(30 * (1.0 - t) ** 2)
        if alpha < 1:
            continue
        glow_draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(200, 200, 180, alpha),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=size * 0.05))

    return img, glow


def _find_bold_font(size):
    """Try bold readable fonts, fall back gracefully."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Palatino Bold.ttc",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_door66_graphic(output_path="door66_diamond_qr.png", dpi=300):
    """Generate the Door66 promotional QR graphic."""
    size = int(3 * dpi)  # 3 inches
    bg_rgba = parse_color(BG_COLOR)
    fg_rgba = parse_color(FG_COLOR)

    # ── Background with vignette ─────────────────────────────────────────
    canvas = Image.new("RGBA", (size, size), bg_rgba)
    vignette_dark, vignette_glow = _make_vignette(size, bg_rgba)

    # Apply glow first (brightens center), then darken edges
    canvas = Image.alpha_composite(canvas, vignette_glow)
    canvas = Image.alpha_composite(canvas, vignette_dark)

    # ── QR code (diamond) ────────────────────────────────────────────────
    # Reserve bottom ~15% for text, use upper ~85% for QR
    text_zone_ratio = 0.13
    qr_zone = int(size * (1.0 - text_zone_ratio))
    qr_size = int(qr_zone * 0.92)  # leave breathing room

    # Generate QR with transparent bg (no visible square) and no overlay
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    generate_qr(
        url="https://door66.events",
        output_path=tmp_path,
        size=qr_size,
        label=None,
        corner_radius=0.35,
        overlay=None,
        fg_color=fg_rgba,
        bg_color=(0, 0, 0, 0),  # transparent — blends into vignette
        margin=0.02,
        rotate=True,  # diamond orientation
    )

    qr_img = Image.open(tmp_path).convert("RGBA")
    Path(tmp_path).unlink()

    # Center QR in the upper zone
    qr_x = (size - qr_img.width) // 2
    qr_y = (qr_zone - qr_img.height) // 2
    canvas.paste(qr_img, (qr_x, qr_y), qr_img)

    # Render keyhole separately with green bg so it blends into the vignette
    inner_size = int(qr_size / math.sqrt(2) * 0.98)
    qr_side = inner_size - 2 * int(inner_size * 0.02)
    ov_size = int(qr_side * 0.35)
    ov_img = _render_keyhole(ov_size, fg_rgba, bg_rgba)
    ov_x = (size - ov_img.width) // 2
    ov_y = qr_y + (qr_img.height - ov_img.height) // 2
    canvas.paste(ov_img, (ov_x, ov_y), ov_img)

    # ── Text: "door66.events" ────────────────────────────────────────────
    draw = ImageDraw.Draw(canvas)
    text = "door66.events"
    text_area_top = qr_zone - int(size * 0.02)
    text_area_bottom = size

    # Find good font size — slightly larger and bold for readability
    font_size = int(size * 0.055)
    font = _find_bold_font(font_size)
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Letter-space the text for elegance
    spaced_text = "  ".join(text)  # subtle spacing
    bbox_s = font.getbbox(spaced_text)
    spaced_w = bbox_s[2] - bbox_s[0]

    # Position centered
    text_x = (size - spaced_w) // 2
    text_y = text_area_top + (text_area_bottom - text_area_top - text_h) // 2 - bbox[1]

    draw.text((text_x, text_y), spaced_text, fill=fg_rgba, font=font)

    # ── Save ─────────────────────────────────────────────────────────────
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Embed DPI metadata
    final_rgb = canvas.convert("RGB")
    final_rgb.save(str(output_path), dpi=(dpi, dpi), quality=95)
    print(f"✓ {output_path}  ({size}×{size} px, {dpi} DPI, 3×3 in)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate Door66 promotional QR graphic")
    parser.add_argument("-o", "--output", default="door66_diamond_qr.png",
                        help="Output file path (default: door66_diamond_qr.png)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="Resolution in DPI (default: 300)")
    args = parser.parse_args()

    generate_door66_graphic(output_path=args.output, dpi=args.dpi)


if __name__ == "__main__":
    main()

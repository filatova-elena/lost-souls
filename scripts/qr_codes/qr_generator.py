#!/usr/bin/env python3
"""
Stylized QR Code Generator
Creates labeled QR codes with keyhole emblem, optimized for print + cut.

Output is a square image. Use --no-rotate for print sheets (square grid),
default mode rotates 45° for diamond placement on cards.

Usage:
    python generate_qr.py --url "https://filatova-elena.github.io/lost-souls/clues/AO78/" --label "AO78"
    python generate_qr.py --url "https://filatova-elena.github.io/lost-souls/clues/AO78/" --label "AO78" --no-rotate
    python generate_qr.py --url "https://filatova-elena.github.io/lost-souls/clues/AO78/" --label "AO78" --fg "#4a148c" --bg transparent
"""

import argparse
import math
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageColor, ImageFont


# ── Color parsing ────────────────────────────────────────────────────────────

def parse_color(color_str, allow_transparent=False):
    """Parse hex (#rgb, #rrggbb, #rrggbbaa), named colors, or 'transparent' → RGBA tuple."""
    if allow_transparent and color_str.lower() == "transparent":
        return (0, 0, 0, 0)

    raw = color_str.lstrip("#")

    if color_str.startswith("#") and len(raw) == 8:
        return tuple(int(raw[i:i+2], 16) for i in (0, 2, 4, 6))

    if color_str.startswith("#") and len(raw) == 4:
        return tuple(int(c, 16) * 17 for c in raw)

    try:
        rgb = ImageColor.getrgb(color_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Unknown color '{color_str}'. Use hex (#ff0000) or a named color (red, navy, etc.)"
        )
    return rgb + (255,) if len(rgb) == 3 else rgb


# ── Smart rounded modules ────────────────────────────────────────────────────

def _draw_smart_rounded_rect(draw, x, y, size, radius, neighbors, fill):
    """Draw a module with corners rounded only where no neighbor is adjacent."""
    top, right, bottom, left = neighbors
    round_tl = not top and not left
    round_tr = not top and not right
    round_br = not bottom and not right
    round_bl = not bottom and not left
    corners = (round_tl, round_tr, round_br, round_bl)

    if all(corners):
        draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill)
    elif not any(corners):
        draw.rectangle([x, y, x + size, y + size], fill=fill)
    else:
        draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill)
        r = radius
        if not round_tl: draw.rectangle([x, y, x + r, y + r], fill=fill)
        if not round_tr: draw.rectangle([x + size - r, y, x + size, y + r], fill=fill)
        if not round_br: draw.rectangle([x + size - r, y + size - r, x + size, y + size], fill=fill)
        if not round_bl: draw.rectangle([x, y + size - r, x + r, y + size], fill=fill)


def _render_modules(matrix, box_size, border, corner_radius_ratio, fg, bg):
    """Render QR matrix into an RGBA image with smart rounded modules."""
    n = len(matrix)
    total = n + 2 * border
    img = Image.new("RGBA", (total * box_size,) * 2, bg)
    draw = ImageDraw.Draw(img)
    radius = box_size * corner_radius_ratio

    def filled(r, c):
        return 0 <= r < n and 0 <= c < n and matrix[r][c]

    for r in range(n):
        for c in range(n):
            if not matrix[r][c]:
                continue
            x = (c + border) * box_size
            y = (r + border) * box_size
            neighbors = (filled(r-1, c), filled(r, c+1), filled(r+1, c), filled(r, c-1))
            _draw_smart_rounded_rect(draw, x, y, box_size, radius, neighbors, fg)

    return img


# ── Center overlays ──────────────────────────────────────────────────────────

def _render_keyhole(size, fg, bg, label=None):
    """Render a keyhole overlay with optional curved label inside the circle."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2
    keyhole_bg = (255, 255, 255, 255)

    bg_r = size * 0.45
    outline_w = max(6, int(size * 0.05))
    draw.ellipse([cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r],
                 fill=keyhole_bg, outline=fg, width=outline_w)

    # Keyhole icon — classic keyhole: circle on top, narrow slot below
    # Position: centered in the space between label arc and bottom of circle,
    # sitting close under the text with breathing room from all edges.
    top_margin = size * 0.17 if label else size * 0.15  # closer to text
    bottom_margin = size * 0.16
    icon_top = cy - bg_r + top_margin
    icon_bottom = cy + bg_r - bottom_margin
    icon_h = icon_bottom - icon_top
    icon_cy = icon_top + icon_h * 0.30  # circle sits in upper third

    # Circle (the peephole)
    cr = icon_h * 0.22
    draw.ellipse([cx - cr, icon_cy - cr, cx + cr, icon_cy + cr], fill=fg)

    # Slot below circle — wider taper
    slot_top = icon_cy + cr * 0.6
    slot_bottom = icon_bottom
    slot_top_w = cr * 0.70
    slot_bot_w = cr * 1.3
    draw.polygon([
        (cx - slot_top_w, slot_top), (cx + slot_top_w, slot_top),
        (cx + slot_bot_w, slot_bottom), (cx - slot_bot_w, slot_bottom),
    ], fill=fg)

    # Curved label along top arc
    if label:
        text = label.upper()
        font_size = max(10, int(bg_r * 0.3))
        font = _find_font(font_size)
        # Conrols how far the label is from the center of the circle
        arc_r = bg_r * 0.645

        char_widths = []
        for ch in text:
            bb = font.getbbox(ch)
            char_widths.append(bb[2] - bb[0])
        total_w = sum(char_widths)

        total_angle = total_w / arc_r
        total_angle = min(total_angle, math.pi * 0.85)

        start_angle = -math.pi / 2 - total_angle / 2
        current_angle = start_angle

        for i, ch in enumerate(text):
            cw = char_widths[i]
            char_angle_span = (cw / total_w) * total_angle
            mid_angle = current_angle + char_angle_span / 2

            tx = cx + arc_r * math.cos(mid_angle)
            ty_pos = cy + arc_r * math.sin(mid_angle)

            char_img = Image.new("RGBA", (cw + 4, font_size + 4), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            bb = font.getbbox(ch)
            char_draw.text((-bb[0] + 2, -bb[1] + 2), ch, fill=fg, font=font)

            rot_deg = math.degrees(mid_angle) + 90
            char_img = char_img.rotate(-rot_deg, expand=True,
                                       resample=Image.Resampling.BICUBIC,
                                       fillcolor=(0, 0, 0, 0))

            px = int(tx - char_img.width / 2)
            py = int(ty_pos - char_img.height / 2)
            img.paste(char_img, (px, py), char_img)

            current_angle += char_angle_span

    return img


def _render_circle(size, fg, bg, label=None):
    """Render a circle overlay as a standalone RGBA image.
    Circle background is always opaque white."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2
    keyhole_bg = (255, 255, 255, 255)
    r = size * 0.40
    outline_w = max(4, int(size * 0.04))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=keyhole_bg, outline=fg, width=outline_w)
    return img


OVERLAYS = {"keyhole": _render_keyhole, "circle": _render_circle}


# ── Label rendering ──────────────────────────────────────────────────────────

def _find_font(size):
    """Try to load a serif font, fall back to default."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_label_block(img, label, fg_color, area_top, area_bottom, center_x):
    """
    Draw a label with decorative rules:
        ── thin rule ──
           LABEL TEXT
        ── thin rule ──
    """
    draw = ImageDraw.Draw(img)
    area_h = area_bottom - area_top

    font_size = max(12, int(area_h * 0.35))
    font = _find_font(font_size)
    text = label.upper()
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Shrink if too wide
    max_w = img.width * 0.65
    if text_w > max_w:
        font_size = int(font_size * max_w / text_w)
        font = _find_font(font_size)
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    rule_w = max(1, font_size // 14)
    gap = max(2, int(area_h * 0.07))
    block_h = rule_w + gap + text_h + gap + rule_w
    block_top = area_top + (area_h - block_h) // 2

    rule_half = max(text_w, font_size * 2) // 2 + font_size // 3

    y = block_top
    draw.line([(center_x - rule_half, y), (center_x + rule_half, y)],
              fill=fg_color, width=rule_w)
    y += rule_w + gap
    draw.text((center_x - text_w // 2, y - bbox[1]), text, fill=fg_color, font=font)
    y += text_h + gap
    draw.line([(center_x - rule_half, y), (center_x + rule_half, y)],
              fill=fg_color, width=rule_w)


# ── Main generation ──────────────────────────────────────────────────────────

def generate_qr(url, output_path="stylized_qr.png", size=600, label=None,
                corner_radius=0.35, overlay="keyhole", overlay_ratio=0.35,
                fg_color=(0,0,0,255), bg_color=(255,255,255,255), margin=0.01,
                rotate=True):
    """
    Generate a styled QR code image.

    Args:
        rotate=True:  Diamond output — label+QR composed upright then rotated
                      45°. Keyhole pre-rotated so it's upright in diamond.
        rotate=False: Square output — label on top, QR below, keyhole upright.
                      Use this for print sheets.
    """
    # ── Render QR modules ────────────────────────────────────────────────
    box_size = 12
    border = 0
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=1, border=0)
    qr.add_data(url)
    qr.make(fit=True)

    if rotate:
        # Diamond mode: build on inner square, rotate 45°
        inner_size = int(size / math.sqrt(2) * 0.98)
        inner = Image.new("RGBA", (inner_size, inner_size), (0, 0, 0, 0))
        m = int(inner_size * margin)
        qr_top = m
        qr_side = inner_size - 2 * m

        qr_img = _render_modules(qr.get_matrix(), box_size, border, corner_radius, fg_color, (0, 0, 0, 0))
        qr_img = qr_img.resize((qr_side, qr_side), Image.Resampling.LANCZOS)
        qr_left = (inner_size - qr_side) // 2
        inner.paste(qr_img, (qr_left, qr_top), qr_img)

        # Overlay: pre-rotate +45° so it's upright after the -45° rotation
        if overlay and overlay in OVERLAYS:
            ov_size = int(qr_side * overlay_ratio)
            ov_img = OVERLAYS[overlay](ov_size, fg_color, bg_color, label=label)
            ov_img = ov_img.rotate(45, expand=True, resample=Image.Resampling.BICUBIC,
                                   fillcolor=(0, 0, 0, 0))
            inner.paste(ov_img,
                        (inner_size // 2 - ov_img.width // 2,
                         qr_top + qr_side // 2 - ov_img.height // 2),
                        ov_img)

        # Rotate → diamond
        rotated = inner.rotate(-45, expand=True, fillcolor=(0, 0, 0, 0))
        final = Image.new("RGBA", (size, size), bg_color)
        final.paste(rotated,
                    ((size - rotated.width) // 2, (size - rotated.height) // 2),
                    rotated)

    else:
        # Square mode: QR fills the square, label inside keyhole
        m = int(size * margin)
        qr_top = m
        qr_side = size - 2 * m

        final = Image.new("RGBA", (size, size), bg_color)

        qr_img = _render_modules(qr.get_matrix(), box_size, border, corner_radius, fg_color, (0, 0, 0, 0))
        qr_img = qr_img.resize((qr_side, qr_side), Image.Resampling.LANCZOS)
        qr_left = (size - qr_side) // 2
        final.paste(qr_img, (qr_left, qr_top), qr_img)

        # Overlay: pre-rotate +45° so when this square is cut and placed
        # as a diamond on the card, the keyhole appears upright
        if overlay and overlay in OVERLAYS:
            ov_size = int(qr_side * overlay_ratio)
            ov_img = OVERLAYS[overlay](ov_size, fg_color, bg_color, label=label)
            ov_img = ov_img.rotate(45, expand=True, resample=Image.Resampling.BICUBIC,
                                   fillcolor=(0, 0, 0, 0))
            final.paste(ov_img,
                        (size // 2 - ov_img.width // 2,
                         qr_top + qr_side // 2 - ov_img.height // 2),
                        ov_img)

    # ── Save ─────────────────────────────────────────────────────────────
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        if bg_color[3] < 255:
            white = Image.new("RGB", final.size, (255, 255, 255))
            white.paste(final, mask=final.split()[3])
            final = white
        else:
            final = final.convert("RGB")

    final.save(str(output_path), quality=95)
    print(f"✓ {output_path}  label={label or '—'}  overlay={overlay or 'none'}")
    return output_path


# ── Print sheet generator ────────────────────────────────────────────────────

def generate_print_sheet(qr_paths, output_path="print_sheet.png",
                         cols=4, cell_size=600, page_margin=20,
                         bg_color=(255, 255, 255, 255)):
    """
    Arrange diamond QR images in a simple square grid for printing.
    Each image is already a square with the diamond inside — just tile them
    in a straight grid so they're easy to cut out.
    """
    rows = math.ceil(len(qr_paths) / cols)
    sheet_w = cols * cell_size + 2 * page_margin
    sheet_h = rows * cell_size + 2 * page_margin

    sheet = Image.new("RGBA", (sheet_w, sheet_h), bg_color)

    for i, qr_path in enumerate(qr_paths):
        r, c = divmod(i, cols)
        x = page_margin + c * cell_size
        y = page_margin + r * cell_size
        qr_img = Image.open(qr_path).convert("RGBA")
        if qr_img.size != (cell_size, cell_size):
            qr_img = qr_img.resize((cell_size, cell_size), Image.Resampling.LANCZOS)
        sheet.paste(qr_img, (x, y), qr_img)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(output_path), quality=95)
    print(f"✓ Print sheet: {output_path}  ({cols}×{rows}, {len(qr_paths)} codes)")
    return output_path


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate labeled diamond QR codes for print + cut",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_qr.py --url https://filatova-elena.github.io/lost-souls/clues/AO78/ --label AO78\n"
            "  python generate_qr.py --url https://filatova-elena.github.io/lost-souls/clues/AO78/ --label AO78 --no-rotate\n"
            "  python generate_qr.py --url https://filatova-elena.github.io/lost-souls/clues/AO78/ --label AO78 --fg '#4a148c' --bg transparent\n"
            "  python generate_qr.py --url https://filatova-elena.github.io/lost-souls/clues/AO78/ --label AO78 --no-overlay\n"
        ),
    )
    parser.add_argument("--url", required=True, help="URL or text to encode")
    parser.add_argument("--label", help="Text label for the QR code")
    parser.add_argument("--output", "-o", default="stylized_qr.png", help="Output path")
    parser.add_argument("--size", type=int, default=600, help="Image size in px (default: 600)")
    parser.add_argument("--radius", type=float, default=0.35, help="Corner radius 0–0.5 (default: 0.35)")
    parser.add_argument("--overlay", choices=["keyhole", "circle"], default="keyhole", help="Center overlay (default: keyhole)")
    parser.add_argument("--no-overlay", action="store_true", help="Disable center overlay")
    parser.add_argument("--overlay-ratio", type=float, default=0.35, help="Overlay size ratio (default: 0.35)")
    parser.add_argument("--fg", default="black", help="Foreground color (default: black)")
    parser.add_argument("--bg", default="white", help="Background color or 'transparent' (default: white)")
    parser.add_argument("--no-rotate", action="store_true", help="Output as straight square (for print sheets) instead of diamond")
    parser.add_argument("--margin", type=float, default=0.01, help="Inner margin ratio (default: 0.01)")
    args = parser.parse_args()

    generate_qr(
        url=args.url,
        output_path=args.output,
        size=args.size,
        label=args.label,
        corner_radius=args.radius,
        overlay=None if args.no_overlay else args.overlay,
        overlay_ratio=args.overlay_ratio,
        fg_color=parse_color(args.fg),
        bg_color=parse_color(args.bg, allow_transparent=True),
        margin=args.margin,
        rotate=not args.no_rotate,
    )


if __name__ == "__main__":
    main()
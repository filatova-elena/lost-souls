#!/usr/bin/env python3
"""
Stylized QR Code Generator for Lost Souls / Door 66
Creates scannable QR codes with smart rounded corners, rotated 45° with keyhole center
"""

import qrcode
from PIL import Image, ImageDraw, ImageColor
from pathlib import Path
import argparse
import math


def parse_color(color_str, allow_transparent=False):
    """
    Parse a color string into an RGBA tuple.
    Supports: hex (#000000, #000000ff, #000), named colors (black, red, navy),
    and 'transparent' keyword.
    
    Uses Pillow's ImageColor which handles ~150 named colors + hex formats.
    """
    if allow_transparent and color_str.lower() == 'transparent':
        return (0, 0, 0, 0)
    
    # Handle 8-character hex (RGBA) — ImageColor doesn't support this
    if color_str.startswith('#') and len(color_str.lstrip('#')) == 8:
        h = color_str.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4, 6))
    
    # Handle 4-character short hex (RGBA)
    if color_str.startswith('#') and len(color_str.lstrip('#')) == 4:
        h = color_str.lstrip('#')
        return tuple(int(h[i], 16) * 17 for i in range(4))
    
    # Use ImageColor for named colors and standard hex (3/6 chars)
    try:
        rgb = ImageColor.getrgb(color_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Unknown color '{color_str}'. Use hex (#ff0000, #ff0000ff) or a named color (red, navy, etc.)"
        )
    
    if len(rgb) == 3:
        return rgb + (255,)
    return rgb


def draw_keyhole(draw, cx, cy, size, fg_color, bg_color):
    """Draw a keyhole icon — small circle top, trapezoid bottom."""
    bg_radius = size * 0.55
    outline_width = max(6, int(size * 0.06))
    
    draw.ellipse(
        [cx - bg_radius, cy - bg_radius, cx + bg_radius, cy + bg_radius],
        fill=bg_color, outline=fg_color, width=outline_width
    )
    
    circle_radius = size * 0.15
    circle_cy = cy - size * 0.15
    
    draw.ellipse(
        [cx - circle_radius, circle_cy - circle_radius,
         cx + circle_radius, circle_cy + circle_radius],
        fill=fg_color
    )
    
    trap_top_w = size * 0.10
    trap_bot_w = size * 0.22
    trap_top_y = circle_cy + circle_radius * 0.7
    trap_bot_y = cy + size * 0.35
    
    draw.polygon([
        (cx - trap_top_w, trap_top_y), (cx + trap_top_w, trap_top_y),
        (cx + trap_bot_w, trap_bot_y), (cx - trap_bot_w, trap_bot_y),
    ], fill=fg_color)


def draw_smart_rounded_rect(draw, x, y, size, radius, neighbors, fill_color):
    """
    Draw a module with corners rounded only where no neighbor is adjacent.
    neighbors: (top, right, bottom, left) — True if that neighbor is filled.
    """
    top, right, bottom, left = neighbors
    
    corners_to_round = (
        not top and not left,   # TL
        not top and not right,  # TR
        not bottom and not right,  # BR
        not bottom and not left,   # BL
    )
    
    if all(corners_to_round):
        draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill_color)
        return
    
    if not any(corners_to_round):
        draw.rectangle([x, y, x + size, y + size], fill=fill_color)
        return
    
    # Draw fully rounded, then square off the corners that shouldn't be rounded
    draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill_color)
    
    r = radius
    if not corners_to_round[0]:  # TL
        draw.rectangle([x, y, x + r, y + r], fill=fill_color)
    if not corners_to_round[1]:  # TR
        draw.rectangle([x + size - r, y, x + size, y + r], fill=fill_color)
    if not corners_to_round[2]:  # BR
        draw.rectangle([x + size - r, y + size - r, x + size, y + size], fill=fill_color)
    if not corners_to_round[3]:  # BL
        draw.rectangle([x, y + size - r, x + r, y + size], fill=fill_color)


def generate_qr_matrix(url):
    """Generate QR matrix data for a URL using high error correction."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.get_matrix()


def render_qr_modules(matrix, box_size, border, corner_radius_ratio, fg_color, bg_color):
    """Render QR matrix into an RGBA image with smart rounded modules."""
    matrix_size = len(matrix)
    total_modules = matrix_size + 2 * border
    img_size = total_modules * box_size
    
    img = Image.new('RGBA', (img_size, img_size), bg_color)
    draw = ImageDraw.Draw(img)
    radius = box_size * corner_radius_ratio
    
    def is_filled(row, col):
        return 0 <= row < matrix_size and 0 <= col < matrix_size and matrix[row][col]
    
    for row in range(matrix_size):
        for col in range(matrix_size):
            if not matrix[row][col]:
                continue
            x = (col + border) * box_size
            y = (row + border) * box_size
            neighbors = (
                is_filled(row - 1, col),
                is_filled(row, col + 1),
                is_filled(row + 1, col),
                is_filled(row, col - 1),
            )
            draw_smart_rounded_rect(draw, x, y, box_size, radius, neighbors, fg_color)
    
    return img


def create_stylized_qr(url, output_path, size=600, keyhole_size_ratio=0.22,
                       rotate=True, corner_radius=0.35,
                       fg_color=(0, 0, 0, 255), bg_color=(255, 255, 255, 255)):
    """
    Create a scannable QR code with smart rounded corners,
    optional 45° rotation, keyhole overlay, and transparent background support.
    """
    box_size = 12
    border = 4
    transparent_bg = (bg_color[3] == 0)
    
    # Render the raw QR modules
    matrix = generate_qr_matrix(url)
    qr_img = render_qr_modules(matrix, box_size, border, corner_radius, fg_color, bg_color)
    
    if rotate:
        inner_size = int(size / math.sqrt(2) * 0.85)
        qr_img = qr_img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
        
        # Rotate with transparent fill so corners don't show artifacts
        qr_img = qr_img.rotate(-45, expand=True, fillcolor=(0, 0, 0, 0))
        
        # Composite onto final canvas
        final = Image.new('RGBA', (size, size), bg_color)
        offset_x = (size - qr_img.width) // 2
        offset_y = (size - qr_img.height) // 2
        final.paste(qr_img, (offset_x, offset_y), qr_img)
    else:
        final = qr_img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Draw keyhole overlay
    draw = ImageDraw.Draw(final)
    keyhole_size = size * keyhole_size_ratio
    draw_keyhole(draw, size / 2, size / 2, keyhole_size, fg_color, bg_color)
    
    # Save — keep RGBA for PNG (supports transparency), convert for JPEG
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix.lower() in ('.jpg', '.jpeg'):
        if transparent_bg:
            print("  ⚠ JPEG doesn't support transparency — compositing onto white")
            white = Image.new('RGB', final.size, (255, 255, 255))
            white.paste(final, mask=final.split()[3])
            final = white
        else:
            final = final.convert('RGB')
    
    final.save(str(output_path), quality=95)
    
    if transparent_bg:
        bg_label = 'transparent'
    elif bg_color[3] < 255:
        bg_label = f'#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}{bg_color[3]:02x}'
    else:
        bg_label = f'#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}'
    
    if fg_color[3] < 255:
        fg_label = f'#{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}{fg_color[3]:02x}'
    else:
        fg_label = f'#{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}'
    
    print(f"✓ Created scannable QR: {output_path}")
    print(f"  URL: {url}")
    print(f"  Rotated: {rotate}")
    print(f"  Corner radius: {corner_radius * 100:.0f}%")
    print(f"  Keyhole size: {keyhole_size_ratio * 100:.0f}%")
    print(f"  FG: {fg_label}")
    print(f"  BG: {bg_label}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate QR codes with smart rounded corners")
    parser.add_argument("--url", required=True, help="URL to encode")
    parser.add_argument("--output", default="stylized_qr.png", help="Output path")
    parser.add_argument("--size", type=int, default=600, help="Image size (default: 600)")
    parser.add_argument("--keyhole", type=float, default=0.22,
                        help="Keyhole size ratio (default: 0.22)")
    parser.add_argument("--radius", type=float, default=0.35,
                        help="Corner radius ratio 0-0.5 (default: 0.35)")
    parser.add_argument("--no-rotate", action="store_true", help="Don't rotate 45°")
    parser.add_argument("--fg", "--foreground", default="black",
                        help="Foreground color: hex (#ff0000 or #ff0000ff) or name (red, navy, etc.)")
    parser.add_argument("--bg", "--background", default="white",
                        help="Background color: hex (#ffffff or #ffffff00), name, or 'transparent'")
    
    args = parser.parse_args()
    
    fg_color = parse_color(args.fg)
    bg_color = parse_color(args.bg, allow_transparent=True)
    
    create_stylized_qr(
        url=args.url,
        output_path=args.output,
        size=args.size,
        keyhole_size_ratio=args.keyhole,
        rotate=not args.no_rotate,
        corner_radius=args.radius,
        fg_color=fg_color,
        bg_color=bg_color,
    )


if __name__ == "__main__":
    main()

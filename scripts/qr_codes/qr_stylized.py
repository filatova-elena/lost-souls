#!/usr/bin/env python3
"""
Stylized QR Code Generator for Lost Souls / Door 66
Creates scannable QR codes with smart rounded corners, rotated 45° with keyhole center
"""

import qrcode
from PIL import Image, ImageDraw
from pathlib import Path
import argparse
import math


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_keyhole(draw, cx, cy, size, fg_color, bg_color):
    """Draw a proper keyhole - small circle top, wider bottom"""
    bg_radius = size * 0.55
    # Outline thickness matches QR module lines
    outline_width = max(6, int(size * 0.06))
    draw.ellipse([
        cx - bg_radius, cy - bg_radius,
        cx + bg_radius, cy + bg_radius
    ], fill=bg_color, outline=fg_color, width=outline_width)
    
    circle_radius = size * 0.15
    circle_center_y = cy - size * 0.15
    
    trap_top_width = size * 0.10
    trap_bottom_width = size * 0.22
    trap_top_y = circle_center_y + circle_radius * 0.7
    trap_bottom_y = cy + size * 0.35
    
    draw.ellipse([
        cx - circle_radius, circle_center_y - circle_radius,
        cx + circle_radius, circle_center_y + circle_radius
    ], fill=fg_color)
    
    points = [
        (cx - trap_top_width, trap_top_y),
        (cx + trap_top_width, trap_top_y),
        (cx + trap_bottom_width, trap_bottom_y),
        (cx - trap_bottom_width, trap_bottom_y),
    ]
    draw.polygon(points, fill=fg_color)


def draw_smart_rounded_rect(draw, x, y, size, radius, neighbors, fill_color):
    """
    Draw a rectangle with selectively rounded corners based on neighbors.
    """
    top, right, bottom, left = neighbors
    
    round_tl = not top and not left
    round_tr = not top and not right
    round_br = not bottom and not right
    round_bl = not bottom and not left
    
    if round_tl and round_tr and round_br and round_bl:
        draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill_color)
        return
    
    if not round_tl and not round_tr and not round_br and not round_bl:
        draw.rectangle([x, y, x + size, y + size], fill=fill_color)
        return
    
    draw.rounded_rectangle([x, y, x + size, y + size], radius=radius, fill=fill_color)
    
    corner_cover = radius
    
    if not round_tl:
        draw.rectangle([x, y, x + corner_cover, y + corner_cover], fill=fill_color)
    if not round_tr:
        draw.rectangle([x + size - corner_cover, y, x + size, y + corner_cover], fill=fill_color)
    if not round_br:
        draw.rectangle([x + size - corner_cover, y + size - corner_cover, x + size, y + size], fill=fill_color)
    if not round_bl:
        draw.rectangle([x, y + size - corner_cover, x + corner_cover, y + size], fill=fill_color)


def create_rounded_qr(url, size, box_size=10, border=4, corner_radius_ratio=0.35, 
                      fg_color=(0, 0, 0), bg_color=(255, 255, 255)):
    """
    Create a QR code with smart rounded corner modules.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    matrix_size = len(matrix)
    
    total_modules = matrix_size + 2 * border
    img_size = total_modules * box_size
    
    # Create image with background color
    img = Image.new('RGBA', (img_size, img_size), bg_color + (255,))
    draw = ImageDraw.Draw(img)
    
    corner_radius = box_size * corner_radius_ratio
    
    def is_filled(row, col):
        if 0 <= row < matrix_size and 0 <= col < matrix_size:
            return matrix[row][col]
        return False
    
    for row in range(matrix_size):
        for col in range(matrix_size):
            if matrix[row][col]:
                x = (col + border) * box_size
                y = (row + border) * box_size
                
                neighbors = (
                    is_filled(row - 1, col),
                    is_filled(row, col + 1),
                    is_filled(row + 1, col),
                    is_filled(row, col - 1),
                )
                
                draw_smart_rounded_rect(draw, x, y, box_size, corner_radius, neighbors, fg_color)
    
    return img


def create_stylized_qr(url, output_path, size=600, keyhole_size_ratio=0.22, 
                       rotate=True, corner_radius=0.35,
                       fg_color=(0, 0, 0), bg_color=(255, 255, 255)):
    """
    Create a scannable QR code with smart rounded corners, rotated 45° with keyhole overlay.
    """
    box_size = 12
    border = 4
    
    qr_img = create_rounded_qr(url, size, box_size=box_size, border=border, 
                                corner_radius_ratio=corner_radius,
                                fg_color=fg_color, bg_color=bg_color)
    
    if rotate:
        inner_size = int(size / math.sqrt(2) * 0.85)
        qr_img = qr_img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
        
        # Rotate with transparent background (-45° / 315° for balanced left/right)
        qr_img = qr_img.rotate(-45, expand=True, fillcolor=bg_color + (0,))
        
        # Create final image with background color
        final = Image.new('RGBA', (size, size), bg_color + (255,))
        
        offset_x = (size - qr_img.size[0]) // 2
        offset_y = (size - qr_img.size[1]) // 2
        final.paste(qr_img, (offset_x, offset_y), qr_img)
        
        result = Image.new('RGB', (size, size), bg_color)
        result.paste(final, mask=final.split()[3])
    else:
        result = qr_img.resize((size, size), Image.Resampling.LANCZOS)
        result = result.convert('RGB')
    
    # Draw keyhole overlay in center
    draw = ImageDraw.Draw(result)
    keyhole_size = size * keyhole_size_ratio
    draw_keyhole(draw, size / 2, size / 2, keyhole_size, fg_color, bg_color)
    
    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(str(output_path), quality=95)
    
    print(f"✓ Created scannable QR: {output_path}")
    print(f"  URL: {url}")
    print(f"  Rotated: {rotate}")
    print(f"  Corner radius: {corner_radius * 100:.0f}%")
    print(f"  Keyhole size: {keyhole_size_ratio * 100:.0f}%")
    print(f"  FG color: #{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}")
    print(f"  BG color: #{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate QR codes with smart rounded corners")
    parser.add_argument("--url", required=True, help="URL to encode")
    parser.add_argument("--output", default="stylized_qr.png", help="Output path")
    parser.add_argument("--size", type=int, default=600, help="Image size (default: 600)")
    parser.add_argument("--keyhole", type=float, default=0.22, 
                        help="Keyhole size ratio (default: 0.22)")
    parser.add_argument("--radius", type=float, default=0.5,
                        help="Corner radius ratio 0-0.5 (default: 0.5)")
    parser.add_argument("--no-rotate", action="store_true", help="Don't rotate 45°")
    parser.add_argument("--fg", "--foreground", default="#000000",
                        help="Foreground/QR color in hex (default: #000000)")
    parser.add_argument("--bg", "--background", default="#ffffff",
                        help="Background color in hex (default: #ffffff)")
    
    args = parser.parse_args()
    
    fg_color = hex_to_rgb(args.fg)
    bg_color = hex_to_rgb(args.bg)
    
    create_stylized_qr(
        args.url, 
        args.output, 
        args.size, 
        keyhole_size_ratio=args.keyhole,
        rotate=not args.no_rotate,
        corner_radius=args.radius,
        fg_color=fg_color,
        bg_color=bg_color
    )


if __name__ == "__main__":
    main()

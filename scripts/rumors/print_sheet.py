#!/usr/bin/env python3
"""
Rumor Card Print Sheet Generator
Creates high-resolution PNG print sheets of rumor cards, optimized for 8.5x11" printing.

Generates rumor cards on the fly from YAML files using generate_rumor_card.py,
then tiles them in a grid. Each card is 2.5×3.5 inches (standard playing card size).

Usage:
    python print_sheet.py
    python print_sheet.py --output sheet.png
    python print_sheet.py --dpi 300 --page-width 8.5 --page-height 11.0
"""

import argparse
import math
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image

# Import generate_rumor_card functions
sys.path.insert(0, str(Path(__file__).parent))
from generate_rumor_card import (
    build_html, render_card, get_act_roman_numeral, BASE_URL
)

# Defaults for 8.5×11" letter
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
CARD_WIDTH_IN = 2.5
CARD_HEIGHT_IN = 3.5
DPI = 300
# 9 cards per page: 3 columns × 3 rows
COLS = 3
ROWS = 3
PER_PAGE = COLS * ROWS


def find_rumor_yamls(rumors_dir):
    """Find all rumor YAML files recursively."""
    rumors_path = Path(rumors_dir)
    if not rumors_path.exists():
        raise FileNotFoundError(f"Rumors directory not found: {rumors_path}")
    
    yaml_files = sorted(rumors_path.rglob("*.yaml")) + sorted(rumors_path.rglob("*.yml"))
    # Filter to only rumor files (check if they have type field with "Rumor")
    rumor_files = []
    for yaml_file in yaml_files:
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if data and data.get("type", "").startswith("Rumor"):
                rumor_files.append(yaml_file)
        except Exception:
            continue
    
    return rumor_files


def generate_card_image(rumor_file, project_root, gossiper_image_path, scale=3):
    """Generate a single rumor card as a PIL Image."""
    rumor_file = Path(rumor_file)
    rumor_data = yaml.safe_load(rumor_file.read_text(encoding="utf-8"))
    
    # Build HTML
    html_content = build_html(rumor_data, gossiper_image_path, scale)
    
    # Render to temporary PNG
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        render_card(html_content, tmp.name, scale)
        img = Image.open(tmp.name).convert("RGBA")
        return img
    finally:
        Path(tmp.name).unlink()


def make_print_sheet(
    rumor_files,
    project_root,
    gossiper_image_path,
    output_path="to_print/rumor_cards/rumor_cards_sheet.png",
    dpi=DPI,
    page_size=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN),
    card_size=(CARD_WIDTH_IN, CARD_HEIGHT_IN),
    cols=COLS,
    rows=ROWS,
    scale=3,
    margin_in=0.25,
    gap_in=0.1,
):
    """
    Generate a high-res PNG print sheet of rumor cards.

    Args:
        rumor_files: List of Path objects to rumor YAML files.
        project_root: Project root directory.
        gossiper_image_path: Path to gossiper.png image.
        output_path: Output PNG path.
        dpi: Dots per inch (300 = standard print quality).
        page_size: (width, height) in inches.
        card_size: (width, height) in inches.
        cols/rows: Grid size (default: 3×3 = 9 per page).
        scale: Render scale for card generation.
        margin_in: Page margin in inches.
        gap_in: Gap between cards in inches.

    Returns:
        List of output file paths (one per page).
    """
    page_w = int(page_size[0] * dpi)
    page_h = int(page_size[1] * dpi)
    card_w = int(card_size[0] * dpi)
    card_h = int(card_size[1] * dpi)
    margin = int(margin_in * dpi)
    gap = int(gap_in * dpi)

    per_page = cols * rows
    num_pages = math.ceil(len(rumor_files) / per_page)

    # Calculate available space for cards
    available_w = page_w - (2 * margin)
    available_h = page_h - (2 * margin)

    # Calculate card grid dimensions
    grid_w = (cols * card_w) + ((cols - 1) * gap)
    grid_h = (rows * card_h) + ((rows - 1) * gap)

    # Center the grid on the page
    offset_x = margin + (available_w - grid_w) // 2
    offset_y = margin + (available_h - grid_h) // 2

    print(f"Sheet: {page_size[0]}×{page_size[1]}\" @ {dpi} DPI = {page_w}×{page_h}px")
    print(f"Grid:  {cols}×{rows} ({per_page}/page)  |  Card: {card_w}×{card_h}px ({card_size[0]}×{card_size[1]}\")")
    print(f"Cards: {len(rumor_files)}  |  Pages: {num_pages}")
    print()

    output_paths = []
    idx = 0

    for page_num in range(num_pages):
        page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

        for slot in range(per_page):
            if idx >= len(rumor_files):
                break

            rumor_file = rumor_files[idx]
            r, c = divmod(slot, cols)
            x = offset_x + c * (card_w + gap)
            y = offset_y + r * (card_h + gap)

            # Load rumor data for display
            rumor_data = yaml.safe_load(rumor_file.read_text(encoding="utf-8"))
            rumor_id = rumor_data.get("id", rumor_file.stem)
            
            # Format title with act number for display
            act_id = rumor_data.get("act")
            act_numeral = get_act_roman_numeral(act_id)
            if act_numeral:
                display_title = f"{act_numeral}. Rumor"
            else:
                display_title = "Rumor"
            
            print(f"  [{idx + 1}/{len(rumor_files)}] {rumor_id}: {display_title}")

            # Generate card image
            card_img = generate_card_image(rumor_file, project_root, gossiper_image_path, scale)
            
            # Resize to exact card size if needed
            if card_img.size != (card_w, card_h):
                card_img = card_img.resize((card_w, card_h), Image.Resampling.LANCZOS)
            
            # Convert to RGB for pasting onto white background
            card_rgb = Image.new("RGB", card_img.size, (255, 255, 255))
            card_rgb.paste(card_img, mask=card_img.split()[3] if card_img.mode == "RGBA" else None)
            
            page.paste(card_rgb, (x, y))
            idx += 1

        # Determine output filename
        if num_pages == 1:
            out = Path(output_path)
        else:
            stem = Path(output_path).stem
            suffix = Path(output_path).suffix
            out = Path(output_path).parent / f"{stem}_page{page_num + 1}{suffix}"

        # Create parent directory if it doesn't exist
        out.parent.mkdir(parents=True, exist_ok=True)

        page.save(str(out), quality=95, dpi=(dpi, dpi))
        output_paths.append(str(out))
        print(f"  → Saved: {out}")

    return output_paths


def main():
    parser = argparse.ArgumentParser(description="Generate rumor card print sheet")
    parser.add_argument("--output", "-o", default="to_print/rumor_cards/rumor_cards_sheet.png")
    parser.add_argument("--dpi", type=int, default=DPI)
    parser.add_argument("--page-width", type=float, default=PAGE_WIDTH_IN)
    parser.add_argument("--page-height", type=float, default=PAGE_HEIGHT_IN)
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--rumors-dir", default="src/_data/rumors")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    rumors_dir = project_root / args.rumors_dir

    # Find gossiper image
    gossiper_image_path = project_root / "src" / "assets" / "images" / "gossip" / "gossiper.png"
    if not gossiper_image_path.exists():
        raise FileNotFoundError(f"Gossiper image not found: {gossiper_image_path}")

    # Find all rumor files
    rumor_files = find_rumor_yamls(rumors_dir)
    
    if not rumor_files:
        print("No rumor files found!")
        return

    # Generate print sheet
    output_paths = make_print_sheet(
        rumor_files,
        project_root,
        gossiper_image_path,
        output_path=args.output,
        dpi=args.dpi,
        page_size=(args.page_width, args.page_height),
        scale=args.scale,
    )

    print(f"\n✅ Generated {len(output_paths)} print sheet(s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Vision Card Print Sheet Generator
Creates high-resolution PNG print sheets of vision cards, optimized for 8.5x11" printing.

Generates vision cards on the fly from YAML files using generate_vision_card.py,
then tiles them in a 2×2 grid (4 per page) at 300 DPI. Each card is 3.5×4.5 inches.

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

# Import generate_vision_card functions
sys.path.insert(0, str(Path(__file__).parent))
from generate_vision_card import (
    build_html, render_card, extract_ghost_name, load_ghost_data, BASE_URL
)

# Defaults for 8.5×11" letter
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
CARD_WIDTH_IN = 3.5
CARD_HEIGHT_IN = 4.5
DPI = 300
COLS = 2
ROWS = 2
PER_PAGE = COLS * ROWS


def find_vision_yamls(visions_dir):
    """Find all vision YAML files recursively."""
    visions_path = Path(visions_dir)
    if not visions_path.exists():
        raise FileNotFoundError(f"Visions directory not found: {visions_path}")
    
    yaml_files = sorted(visions_path.rglob("*.yaml")) + sorted(visions_path.rglob("*.yml"))
    # Filter to only vision files (check if they have type field with "Vision")
    vision_files = []
    for yaml_file in yaml_files:
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if data and data.get("type", "").startswith("Vision"):
                vision_files.append(yaml_file)
        except Exception:
            continue
    
    return vision_files


def generate_card_image(vision_file, project_root, scale=3, base_url=BASE_URL):
    """Generate a single vision card as a PIL Image."""
    vision_file = Path(vision_file)
    vision_data = yaml.safe_load(vision_file.read_text(encoding="utf-8"))
    
    # Extract ghost name
    vision_type = vision_data.get("type", "")
    ghost_name = extract_ghost_name(vision_type)
    if not ghost_name:
        raise ValueError(f"Could not extract ghost name from type: {vision_type}")
    
    # Load ghost data
    ghost_data = load_ghost_data(ghost_name, project_root)
    
    # Build HTML
    html_content = build_html(vision_data, ghost_data, str(vision_file.parent), scale, base_url)
    
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
    vision_files,
    project_root,
    output_path="to_print/vision_cards/vision_cards_sheet.png",
    dpi=DPI,
    page_size=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN),
    card_size=(CARD_WIDTH_IN, CARD_HEIGHT_IN),
    cols=COLS,
    rows=ROWS,
    scale=3,
    base_url=BASE_URL,
    margin_in=0.25,
    gap_in=0.1,
):
    """
    Generate a high-res PNG print sheet of vision cards.

    Args:
        vision_files: List of Path objects to vision YAML files.
        project_root: Project root directory.
        output_path: Output PNG path.
        dpi: Dots per inch (300 = standard print quality).
        page_size: (width, height) in inches.
        card_size: (width, height) in inches.
        cols/rows: Grid size (default: 2×2 = 4 per page).
        scale: Render scale for card generation.
        base_url: Base URL for QR codes.
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
    num_pages = math.ceil(len(vision_files) / per_page)

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
    print(f"Cards: {len(vision_files)}  |  Pages: {num_pages}")
    print()

    output_paths = []
    idx = 0

    for page_num in range(num_pages):
        page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

        for slot in range(per_page):
            if idx >= len(vision_files):
                break

            vision_file = vision_files[idx]
            r, c = divmod(slot, cols)
            x = offset_x + c * (card_w + gap)
            y = offset_y + r * (card_h + gap)

            # Load vision data for display
            vision_data = yaml.safe_load(vision_file.read_text(encoding="utf-8"))
            clue_id = vision_data.get("id", vision_file.stem)
            title = vision_data.get("title", clue_id)
            print(f"  [{idx + 1}/{len(vision_files)}] {clue_id}: {title}")

            # Generate card image
            card_img = generate_card_image(vision_file, project_root, scale, base_url)
            
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
    parser = argparse.ArgumentParser(description="Generate vision card print sheet")
    parser.add_argument("--output", "-o", default="to_print/vision_cards/vision_cards_sheet.png")
    parser.add_argument("--dpi", type=int, default=DPI)
    parser.add_argument("--page-width", type=float, default=PAGE_WIDTH_IN)
    parser.add_argument("--page-height", type=float, default=PAGE_HEIGHT_IN)
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--visions-dir", default="src/_data/clues/visions")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    visions_dir = project_root / args.visions_dir

    # Find all vision files
    vision_files = find_vision_yamls(visions_dir)
    
    if not vision_files:
        print("No vision files found!")
        return

    # Generate print sheet
    output_paths = make_print_sheet(
        vision_files,
        project_root,
        output_path=args.output,
        dpi=args.dpi,
        page_size=(args.page_width, args.page_height),
        scale=args.scale,
        base_url=args.base_url,
    )

    print(f"\n✅ Generated {len(output_paths)} print sheet(s)")


if __name__ == "__main__":
    main()

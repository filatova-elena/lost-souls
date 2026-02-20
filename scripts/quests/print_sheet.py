#!/usr/bin/env python3
"""
Quest Answer Card Print Sheet Generator
Creates high-resolution PNG print sheets of quest answer cards, optimized for 8.5x11" printing.

Generates quest answer cards on the fly from character YAML files using generate_answer_card.py,
then tiles them in a 2×2 grid (4 per page) at 300 DPI. Each card is 3×4 inches.

Usage:
    python print_sheet.py
    python print_sheet.py --quest-type main
    python print_sheet.py --quest-type private --output sheet.png
    python print_sheet.py --dpi 300 --page-width 8.5 --page-height 11.0
"""

import argparse
import math
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image

# Import generate_answer_card functions
sys.path.insert(0, str(Path(__file__).parent))
from generate_answer_card import build_html, render_card, find_image, BASE_URL, load_skills_data, load_quest_data

# Defaults for 8.5×11" letter
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
CARD_WIDTH_IN = 3.0
CARD_HEIGHT_IN = 4.0
DPI = 300
COLS = 2
ROWS = 2
PER_PAGE = COLS * ROWS


def find_character_yamls(characters_dir):
    """Find all character YAML files."""
    chars_dir = Path(characters_dir)
    if not chars_dir.exists():
        raise FileNotFoundError(f"Characters directory not found: {characters_dir}")
    
    yaml_files = sorted(chars_dir.glob("*.yaml")) + sorted(chars_dir.glob("*.yml"))
    return yaml_files


def generate_answer_card_image(character_data, quest_data, yaml_dir, scale=3, base_url=BASE_URL, skills_data=None):
    """Generate a single quest answer card as a PIL Image."""
    # Build HTML
    html_content = build_html(character_data, quest_data, yaml_dir, scale, base_url, skills_data)
    
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
    character_yamls,
    quest_type="main",
    output_path="to_print/quest_answer_cards_sheet.png",
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
    Generate a high-res PNG print sheet of quest answer cards.

    Args:
        character_yamls: List of Path objects to character YAML files.
        quest_type: "main" or "private" - which quest type to generate cards for.
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
    margin = int(margin_in * dpi)
    gap = int(gap_in * dpi)
    
    card_w = int(card_size[0] * dpi)
    card_h = int(card_size[1] * dpi)

    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    # Calculate grid dimensions
    grid_w = cols * card_w + (cols - 1) * gap
    grid_h = rows * card_h + (rows - 1) * gap
    
    # Center the grid
    offset_x = margin + (usable_w - grid_w) // 2
    offset_y = margin + (usable_h - grid_h) // 2

    per_page = cols * rows
    
    # Filter characters that have the requested quest type
    valid_characters = []
    project_root = character_yamls[0] if character_yamls else Path.cwd()
    for _ in range(10):
        if (project_root / "src" / "_data" / "refs" / "skills.yaml").exists():
            break
        project_root = project_root.parent
    
    for yaml_path in character_yamls:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        objectives = data.get("objectives", {})
        quest_id = objectives.get(quest_type)
        if quest_id:
            valid_characters.append((yaml_path, data, quest_id))
    
    num_pages = math.ceil(len(valid_characters) / per_page)

    print(f"Sheet: {page_size[0]}×{page_size[1]}\" @ {dpi} DPI = {page_w}×{page_h}px")
    print(f"Grid:  {cols}×{rows} ({per_page}/page)  |  Card: {card_w}×{card_h}px ({card_size[0]}×{card_size[1]}\")")
    print(f"Quest Type: {quest_type}")
    print(f"Cards: {len(valid_characters)}  |  Pages: {num_pages}")
    print()

    # Load skills data once
    skills_data = load_skills_data(project_root)

    output_paths = []
    idx = 0

    for page_num in range(num_pages):
        page = Image.new("RGB", (page_w, page_h), (255, 255, 255))

        for slot in range(per_page):
            if idx >= len(valid_characters):
                break

            yaml_path, character_data, quest_id = valid_characters[idx]
            r, c = divmod(slot, cols)
            x = offset_x + c * (card_w + gap)
            y = offset_y + r * (card_h + gap)

            # Load quest data
            quest_data = load_quest_data(project_root, quest_id)
            
            char_name = character_data.get("title", yaml_path.stem)
            quest_title = quest_data.get("title", quest_id)
            print(f"  [{idx + 1}/{len(valid_characters)}] {char_name} - {quest_title}")

            # Generate card image
            card_img = generate_answer_card_image(
                character_data, quest_data, str(yaml_path.parent), scale, base_url, skills_data
            )
            
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
        print(f"  ✓ {out}")

    print(f"\nDone: {len(output_paths)} page(s), {len(valid_characters)} cards")
    return output_paths


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate high-res PNG print sheets of quest answer cards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python print_sheet.py\n"
            "  python print_sheet.py --quest-type main\n"
            "  python print_sheet.py --quest-type private --output sheet.png\n"
            "  python print_sheet.py --dpi 300 --page-width 8.5 --page-height 11.0\n"
        ),
    )

    parser.add_argument(
        "--characters-dir",
        default="src/_data/characters",
        help="Directory containing character YAML files (default: src/_data/characters)",
    )
    parser.add_argument(
        "--quest-type",
        choices=["main", "private"],
        default="main",
        help="Quest type to generate cards for (default: main)",
    )
    parser.add_argument(
        "--output", "-o",
        default="to_print/quest_answer_cards_sheet.png",
        help="Output PNG path (default: to_print/quest_answer_cards_sheet.png)",
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"Base URL for QR codes (default: {BASE_URL})",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DPI,
        help=f"Resolution (default: {DPI})",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=3,
        help="Render scale for card generation (default: 3)",
    )
    parser.add_argument(
        "--page-width",
        type=float,
        default=PAGE_WIDTH_IN,
        help=f"Page width in inches (default: {PAGE_WIDTH_IN})",
    )
    parser.add_argument(
        "--page-height",
        type=float,
        default=PAGE_HEIGHT_IN,
        help=f"Page height in inches (default: {PAGE_HEIGHT_IN})",
    )
    parser.add_argument(
        "--card-width",
        type=float,
        default=CARD_WIDTH_IN,
        help=f"Card width in inches (default: {CARD_WIDTH_IN})",
    )
    parser.add_argument(
        "--card-height",
        type=float,
        default=CARD_HEIGHT_IN,
        help=f"Card height in inches (default: {CARD_HEIGHT_IN})",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.25,
        help="Page margin in inches (default: 0.25)",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=0.1,
        help="Gap between cards in inches (default: 0.1)",
    )

    args = parser.parse_args()

    # Find all character YAML files
    project_root = Path(__file__).parent.parent.parent
    characters_dir = project_root / args.characters_dir
    character_yamls = find_character_yamls(characters_dir)

    if not character_yamls:
        print(f"No character YAML files found in {characters_dir}")
        return

    print(f"Found {len(character_yamls)} character(s)\n")

    make_print_sheet(
        character_yamls=character_yamls,
        quest_type=args.quest_type,
        output_path=args.output,
        dpi=args.dpi,
        page_size=(args.page_width, args.page_height),
        card_size=(args.card_width, args.card_height),
        cols=COLS,
        rows=ROWS,
        scale=args.scale,
        base_url=args.base_url,
        margin_in=args.margin,
        gap_in=args.gap,
    )


if __name__ == "__main__":
    main()

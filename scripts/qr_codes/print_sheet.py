#!/usr/bin/env python3
"""
Print Sheet Generator
Creates high-resolution PNG print sheets of QR codes, optimized for 8.5x11" printing.

Generates QR codes on the fly from (url, label) pairs using generate_qr.py,
then tiles them in a 4×5 grid at 300 DPI.

Usage:
    # From a YAML file of clues:
    python print_sheet.py --yaml clues.yaml --output sheet.png

    # From explicit url/label pairs:
    python print_sheet.py --codes "https://example.com/AO78|AO78" "https://example.com/DL01|DL01"

    # Customize:
    python print_sheet.py --yaml clues.yaml --dpi 300 --fg "#4a148c" --cols 4 --rows 5
"""

import argparse
import math
import sys
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from qr_generator import generate_qr, parse_color

# Defaults for 8.5×11" letter
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
MARGIN_IN = 0.25
GAP_IN = 0.05
QR_SIZE_RATIO = 0.85  # QR code size as ratio of cell size (85% = 15% margin around each QR)
DPI = 300
BASE_URL = "https://lostsouls.door66.events/clues"  # Full base URL for QR codes


def make_print_sheet(
    codes,
    output_path="print_sheet.png",
    dpi=DPI,
    page_size=(PAGE_WIDTH_IN, PAGE_HEIGHT_IN),
    margin_in=MARGIN_IN,
    gap_in=GAP_IN,
    cols=None,
    rows=None,
    fg_color=(74, 20, 140, 255),
    bg_color=(255, 255, 255, 255),
    qr_size_ratio=QR_SIZE_RATIO,
):
    """
    Generate a high-res PNG print sheet of QR codes.

    Args:
        codes:       List of (url, label) tuples.
        output_path: Output PNG path.
        dpi:         Dots per inch (300 = standard print quality).
        page_size:   (width, height) in inches.
        margin_in:   Page margin in inches.
        gap_in:      Gap between codes in inches.
        cols/rows:   Force grid size, or None to auto-calculate.
        fg_color:    RGBA tuple for QR foreground.
        bg_color:    RGBA tuple for QR/page background.

    Returns:
        List of output file paths (one per page).
    """
    page_w = int(page_size[0] * dpi)
    page_h = int(page_size[1] * dpi)
    margin = int(margin_in * dpi)
    gap = int(gap_in * dpi)

    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    # Auto-fit grid if not specified
    if cols is None or rows is None:
        # Find largest square cell that fits at least 4×5
        # Start with 4×5 and compute cell size
        c = cols or 4
        r = rows or 5
        cell_w = (usable_w - (c - 1) * gap) // c
        cell_h = (usable_h - (r - 1) * gap) // r
        cell = min(cell_w, cell_h)
        cols = c
        rows = r
    else:
        cell_w = (usable_w - (cols - 1) * gap) // cols
        cell_h = (usable_h - (rows - 1) * gap) // rows
        cell = min(cell_w, cell_h)

    per_page = cols * rows
    num_pages = math.ceil(len(codes) / per_page)

    # Center the grid
    grid_w = cols * cell + (cols - 1) * gap
    grid_h = rows * cell + (rows - 1) * gap
    offset_x = margin + (usable_w - grid_w) // 2
    offset_y = margin + (usable_h - grid_h) // 2

    print(f"Sheet: {page_size[0]}×{page_size[1]}\" @ {dpi} DPI = {page_w}×{page_h}px")
    print(f"Grid:  {cols}×{rows} ({per_page}/page)  |  Cell: {cell}px ({cell/dpi:.2f}\")")
    print(f"Codes: {len(codes)}  |  Pages: {num_pages}")
    print()

    output_paths = []
    idx = 0

    for page_num in range(num_pages):
        page = Image.new("RGBA", (page_w, page_h), bg_color)

        for slot in range(per_page):
            if idx >= len(codes):
                break

            r, c = divmod(slot, cols)
            x = offset_x + c * (cell + gap)
            y = offset_y + r * (cell + gap)

            url, label = codes[idx]
            print(f"  [{idx + 1}/{len(codes)}] {label}")

            # Generate QR code smaller than cell to create margins
            qr_size = int(cell * qr_size_ratio)
            qr_img = _generate_qr_image(
                url, label, qr_size, fg_color, bg_color
            )
            
            # Center the QR code within the cell
            qr_x = x + (cell - qr_size) // 2
            qr_y = y + (cell - qr_size) // 2
            page.paste(qr_img, (qr_x, qr_y), qr_img)
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

        page_rgb = Image.new("RGB", page.size, (255, 255, 255))
        page_rgb.paste(page, mask=page.split()[3])
        page_rgb.save(str(out), quality=95, dpi=(dpi, dpi))
        output_paths.append(str(out))
        print(f"  ✓ {out}")

    print(f"\nDone: {len(output_paths)} page(s), {len(codes)} codes")
    return output_paths


def _generate_qr_image(url, label, size, fg_color, bg_color):
    """Generate a QR code as a PIL Image (no temp file needed)."""
    import tempfile, os

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        generate_qr(
            url=url,
            output_path=tmp.name,
            size=size,
            label=label,
            fg_color=fg_color,
            bg_color=bg_color,
            rotate=False,
        )
        return Image.open(tmp.name).convert("RGBA")
    finally:
        os.unlink(tmp.name)


def _load_yaml(yaml_path, base_url=BASE_URL):
    """
    Load codes from a YAML file, filtering to only first clues in chains.

    Supports two formats:

    1. Single clue file (has 'id' field):
        id: AO78
        title: Silver Candle Holder
        ...

    2. List of clues:
        - id: AO78
          title: Silver Candle Holder
        - id: DL01
          title: Torn Letter
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if isinstance(data, dict) and "id" in data:
        # Single clue
        data = [data]
    elif isinstance(data, dict) and "clues" in data:
        data = data["clues"]

    codes = []
    for item in data:
        # Only include clues that are the first in a chain (no previous_id)
        if "previous_id" in item:
            continue
            
        clue_id = item.get("id", "")
        # Construct URL: if base_url is empty or just "clues", use relative path; otherwise use full URL
        if not base_url or base_url == "clues":
            url = f"clues/{clue_id}/"
        else:
            # Ensure base_url ends with /clues, then append clue_id
            if base_url.endswith("/clues"):
                url = f"{base_url}/{clue_id}/"
            elif base_url.endswith("/clues/"):
                url = f"{base_url}{clue_id}/"
            else:
                url = f"{base_url}/clues/{clue_id}/"
        codes.append((url, str(clue_id)))

    return codes


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate high-res PNG print sheets of QR codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python print_sheet.py --yaml clues.yaml\n"
            "  python print_sheet.py --yaml clues.yaml --dpi 300 --fg '#4a148c'\n"
            "  python print_sheet.py --codes 'https://example.com/AO78|AO78' 'https://example.com/DL01|DL01'\n"
            "  python print_sheet.py --yaml clues.yaml --cols 3 --rows 4 --output big_codes.png\n"
        ),
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--yaml", help="YAML file with clue definitions (has 'id' field)")
    source.add_argument("--codes", nargs="+", metavar="URL|LABEL",
                        help="Explicit url|label pairs")

    parser.add_argument("--output", "-o", default="to_print/qr_codes/print_sheet.png", help="Output PNG path")
    parser.add_argument("--base-url", default=BASE_URL,
                        help=f"Base URL for YAML clues (default: {BASE_URL})")
    parser.add_argument("--dpi", type=int, default=DPI, help=f"Resolution (default: {DPI})")
    parser.add_argument("--cols", type=int, default=None, help="Grid columns (default: auto)")
    parser.add_argument("--rows", type=int, default=None, help="Grid rows (default: auto)")
    parser.add_argument("--fg", default="#4a148c", help="Foreground color (default: #4a148c)")
    parser.add_argument("--bg", default="white", help="Background color (default: white)")
    parser.add_argument("--page-width", type=float, default=PAGE_WIDTH_IN, help="Page width in inches")
    parser.add_argument("--page-height", type=float, default=PAGE_HEIGHT_IN, help="Page height in inches")
    parser.add_argument("--qr-size-ratio", type=float, default=QR_SIZE_RATIO,
                        help=f"QR code size as ratio of cell size (default: {QR_SIZE_RATIO}, e.g., 0.85 = 85%% of cell)")

    args = parser.parse_args()

    # Load codes
    if args.yaml:
        codes = _load_yaml(args.yaml, base_url=args.base_url)
    else:
        codes = []
        for pair in args.codes:
            if "|" in pair:
                url, label = pair.split("|", 1)
            else:
                url, label = pair, Path(pair).stem
            codes.append((url, label))

    if not codes:
        print("No codes to generate.")
        return

    make_print_sheet(
        codes=codes,
        output_path=args.output,
        dpi=args.dpi,
        page_size=(args.page_width, args.page_height),
        cols=args.cols,
        rows=args.rows,
        fg_color=parse_color(args.fg),
        bg_color=parse_color(args.bg, allow_transparent=True),
        qr_size_ratio=args.qr_size_ratio,
    )


if __name__ == "__main__":
    main()
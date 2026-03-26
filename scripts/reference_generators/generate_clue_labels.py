#!/usr/bin/env python3
"""
Generate print sheets of 2x2 inch sticky labels for clues in PDF format.

Each label displays:
- ID (prominent and bold)
- Title
- Appearance (short description)
- Act
- Image (if present, fitted into remaining space)

Labels have a thin border for cutting guides and 0.15" padding.

Usage:
    python scripts/reference_generators/generate_clue_labels.py
    python scripts/reference_generators/generate_clue_labels.py --output to_print/clue_labels.pdf
"""

import argparse
import sys
import yaml
from pathlib import Path
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ── Label & page specifications ───────────────────────────────────
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11.0 * inch

LABEL_WIDTH = 2.0 * inch
LABEL_HEIGHT = 2.0 * inch
PADDING = 0.15 * inch

# Grid layout — fit as many as we can on a letter page
# With 2" labels: 4 columns x 5 rows = 20 per page
COLS = 4
ROWS = 5
LABELS_PER_PAGE = COLS * ROWS

# Center the grid on the page
GRID_WIDTH = COLS * LABEL_WIDTH
GRID_HEIGHT = ROWS * LABEL_HEIGHT
LEFT_MARGIN = (PAGE_WIDTH - GRID_WIDTH) / 2
TOP_MARGIN = (PAGE_HEIGHT - GRID_HEIGHT) / 2

# Content area inside each label
CONTENT_WIDTH = LABEL_WIDTH - 2 * PADDING
CONTENT_HEIGHT = LABEL_HEIGHT - 2 * PADDING


def load_all_clues(clues_dir):
    """Load all clue YAML files recursively, filtering to only first clues in chains."""
    clues = []
    clues_path = project_root / clues_dir

    if not clues_path.exists():
        print(f"Error: Clues directory not found: {clues_path}", file=sys.stderr)
        return clues

    for yaml_file in sorted(clues_path.rglob("*.yaml")):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                clue_data = yaml.safe_load(f)
                if clue_data and 'id' in clue_data:
                    # Only include clues that are the first in a chain (no previous_id)
                    if 'previous_id' not in clue_data:
                        clues.append(clue_data)
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}", file=sys.stderr)

    return clues


def format_act_name(act):
    """Format act name for display."""
    if not act:
        return ""
    act_map = {
        'act_prologue': 'Prologue',
        'act_i_setting': 'Act I',
        'act_ii_mystery_emerges': 'Act II',
        'act_iii_investigation': 'Act III',
        'act_iv_revelation': 'Act IV'
    }
    return act_map.get(act, act.replace('_', ' ').title())


def truncate_text(text, max_length=80):
    """Truncate text to max_length characters, adding ellipsis."""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_label_origin(idx):
    """
    Get the top-left corner of the label at index idx.
    Returns (x, y_top) in ReportLab coords (origin at bottom-left).
    """
    col = idx % COLS
    row = idx // COLS

    x = LEFT_MARGIN + col * LABEL_WIDTH
    y_from_top = TOP_MARGIN + row * LABEL_HEIGHT
    y_top = PAGE_HEIGHT - y_from_top

    return x, y_top


def resolve_image_path(image_field):
    """Resolve an image path from the YAML field to an absolute path."""
    if not image_field:
        return None
    # Image paths in YAML are relative to src/, e.g. "assets/images/bembridge/foo.png"
    img_path = project_root / "src" / image_field
    if img_path.exists():
        return img_path
    return None


def draw_label(c, idx, clue, label_style, act_style):
    """Draw a single label at position idx on the current page."""
    label_x, label_y_top = get_label_origin(idx)

    # Draw cut border
    c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
    c.setLineWidth(0.5)
    c.rect(label_x, label_y_top - LABEL_HEIGHT, LABEL_WIDTH, LABEL_HEIGHT)

    # Content area
    cx = label_x + PADDING
    cy_top = label_y_top - PADDING

    clue_id = clue.get('id', 'N/A')
    title = clue.get('title', 'Untitled')
    appearance = clue.get('appearance', '')
    act = clue.get('act', '')
    image_field = clue.get('image', None)

    # Format appearance
    appearance_text = ""
    if appearance:
        appearance_clean = str(appearance).strip().replace('**', '').replace('*', '')
        lines = appearance_clean.split('\n')
        appearance_text = lines[0] if lines else ""
        appearance_text = truncate_text(appearance_text, max_length=80)

    act_display = format_act_name(act)

    # Resolve image
    img_path = resolve_image_path(image_field)

    # ── Layout: text on the left, image on the right (if present) ──
    if img_path:
        # Reserve right side for image
        img_area_width = CONTENT_WIDTH * 0.4
        text_width = CONTENT_WIDTH - img_area_width - 0.05 * inch  # small gap
    else:
        text_width = CONTENT_WIDTH
        img_area_width = 0

    # Build text content
    html = f'<b><font size="11">{clue_id}</font></b><br/>'
    html += f'<b><font size="7">{title}</font></b><br/>'
    if appearance_text:
        html += f'<i><font size="5.5">{appearance_text}</font></i><br/>'

    para = Paragraph(html, label_style)
    w, h = para.wrap(text_width, CONTENT_HEIGHT - 12)  # reserve space for act at bottom
    para.drawOn(c, cx, cy_top - h)

    # Draw act at bottom left
    if act_display:
        act_para = Paragraph(f'<font size="6" color="#666666">{act_display}</font>', act_style)
        aw, ah = act_para.wrap(text_width, 12)
        act_para.drawOn(c, cx, label_y_top - LABEL_HEIGHT + PADDING)

    # Draw image on the right
    if img_path:
        try:
            img = ImageReader(str(img_path))
            iw, ih = img.getSize()
            aspect = iw / ih

            # Available space for image
            max_img_w = img_area_width
            max_img_h = CONTENT_HEIGHT

            # Fit image maintaining aspect ratio
            if aspect > (max_img_w / max_img_h):
                draw_w = max_img_w
                draw_h = draw_w / aspect
            else:
                draw_h = max_img_h
                draw_w = draw_h * aspect

            # Position: right-aligned, vertically centered
            img_x = cx + text_width + 0.05 * inch + (max_img_w - draw_w) / 2
            img_y = cy_top - CONTENT_HEIGHT / 2 - draw_h / 2

            c.drawImage(str(img_path), img_x, img_y, draw_w, draw_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Warning: Could not load image for {clue_id}: {e}", file=sys.stderr)


def create_label_pdf(clues, output_path):
    """Create PDF with labels for all clues."""
    num_pages = (len(clues) + LABELS_PER_PAGE - 1) // LABELS_PER_PAGE

    print(f"Page size: {PAGE_WIDTH/inch:.1f}\" x {PAGE_HEIGHT/inch:.1f}\"")
    print(f"Label size: {LABEL_WIDTH/inch:.1f}\" x {LABEL_HEIGHT/inch:.1f}\"")
    print(f"Grid: {COLS} cols x {ROWS} rows = {LABELS_PER_PAGE} per page")
    print(f"Content padding: {PADDING/inch:.2f}\"")
    print(f"Margins: left={LEFT_MARGIN/inch:.2f}\" top={TOP_MARGIN/inch:.2f}\"")
    print(f"Total clues: {len(clues)}")
    print(f"Total pages: {num_pages}\n")

    label_style = ParagraphStyle(
        'Label',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=7,
        leading=9,
        leftIndent=0,
        rightIndent=0,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=1,
        textColor=colors.black,
        fontName='Helvetica',
    )

    act_style = ParagraphStyle(
        'Act',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=6,
        leading=7,
        alignment=TA_LEFT,
        textColor=colors.Color(0.4, 0.4, 0.4),
        fontName='Helvetica',
    )

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for page_num in range(num_pages):
        start = page_num * LABELS_PER_PAGE
        page_clues = clues[start:start + LABELS_PER_PAGE]

        for idx, clue in enumerate(page_clues):
            draw_label(c, idx, clue, label_style, act_style)

        if page_num < num_pages - 1:
            c.showPage()

    c.save()
    print(f"Label PDF generated: {output_path}")

    # Count how many had images
    with_images = sum(1 for cl in clues if cl.get('image'))
    print(f"Labels with images: {with_images}/{len(clues)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate 2x2 inch print labels for clues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--clues-dir',
        type=str,
        default='src/_data/clues',
        help='Directory containing clue YAML files (default: src/_data/clues)',
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='to_print/clue_labels.pdf',
        help='Output PDF file path (default: to_print/clue_labels.pdf)',
    )

    args = parser.parse_args()

    clues_dir = project_root / args.clues_dir
    output_path = project_root / args.output

    if not clues_dir.exists():
        print(f"Error: Clues directory not found: {clues_dir}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading clues from {clues_dir}...")
    clues = load_all_clues(args.clues_dir)

    if not clues:
        print("Error: No clues found", file=sys.stderr)
        return 1

    print(f"Found {len(clues)} clues\n")
    create_label_pdf(clues, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

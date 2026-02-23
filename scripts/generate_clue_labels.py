#!/usr/bin/env python3
"""
Generate print sheets of labels for clues in PDF format.

Creates a single PDF with all clue labels formatted for Avery 5163 sticky paper:
- Label size: 4" wide x 2" tall
- Layout: 2 columns x 5 rows = 10 labels per page
- Page: 8.5" x 11"
- Top margin: 0.5"
- Bottom margin: 0.5"
- Left margin: 0.17"
- Right margin: 0.17"
- Horizontal gutter (between columns): 0.16"
- Vertical gutter (between rows): 0" (no gap)

Each label displays:
- ID (prominent and bold)
- Title
- Type
- Appearance
- Act | Location

Usage:
    python scripts/generate_clue_labels.py
    python scripts/generate_clue_labels.py --output to_print/clue_labels.pdf
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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ── Avery 5163 specifications ──────────────────────────────────────
# Labels are 4" x 2", arranged 2 columns x 5 rows = 10 per page
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11.0 * inch

TOP_MARGIN = 0.5 * inch
LEFT_MARGIN = 0.17 * inch

LABEL_WIDTH = 4.0 * inch
LABEL_HEIGHT = 2.0 * inch
H_GUTTER = 0.17 * inch       # gap between the two columns
PADDING = 0.25 * inch        # content inset from label edge

COLS = 2
ROWS = 5
LABELS_PER_PAGE = COLS * ROWS  # 10

# Content area inside each label
CONTENT_WIDTH = LABEL_WIDTH - 2 * PADDING
CONTENT_HEIGHT = LABEL_HEIGHT - 2 * PADDING


def load_all_clues(clues_dir):
    """Load all clue YAML files recursively."""
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
                    clues.append(clue_data)
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}", file=sys.stderr)

    return clues


def format_act_name(act):
    """Format act name for display."""
    if not act:
        return "N/A"
    act_map = {
        'act_prologue': 'Prologue',
        'act_i_setting': 'Act I: Setting',
        'act_ii_mystery_emerges': 'Act II: Mystery Emerges',
        'act_iii_investigation': 'Act III: Investigation',
        'act_iv_revelation': 'Act IV: Revelation'
    }
    return act_map.get(act, act.replace('_', ' ').title())


def truncate_text(text, max_length=100):
    """Truncate text to max_length characters, adding ellipsis."""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_content_origin(idx):
    """
    Get the top-left corner of the CONTENT area for label at index idx.

    Positions are absolute — computed directly from margins, not relative
    to other labels.

    Returns (x, y_top) where:
      x     = left edge of content area
      y_top = top edge of content area (in ReportLab coords, from page bottom)

    From top of page:
      y_from_top = TOP_MARGIN + row * LABEL_HEIGHT + PADDING
      x          = LEFT_MARGIN + col * (LABEL_WIDTH + H_GUTTER) + PADDING
    """
    col = idx % COLS
    row = idx // COLS

    x = LEFT_MARGIN + col * (LABEL_WIDTH + H_GUTTER) + PADDING

    # Distance from top of page to top of content
    y_from_top = TOP_MARGIN + row * LABEL_HEIGHT + PADDING
    # Convert to ReportLab coords (origin at bottom-left)
    y_top = PAGE_HEIGHT - y_from_top

    return x, y_top


def create_label_content(clue):
    """Create formatted HTML content for a single label."""
    clue_id = clue.get('id', 'N/A')
    title = clue.get('title', 'Untitled')
    clue_type = clue.get('type', '')
    appearance = clue.get('appearance', '')
    act = clue.get('act', '')
    location = clue.get('location', '')

    # Format appearance - truncate if too long
    appearance_text = ""
    if appearance:
        appearance_clean = str(appearance).strip()
        appearance_clean = appearance_clean.replace('**', '').replace('*', '')
        lines = appearance_clean.split('\n')
        appearance_text = lines[0] if lines else ""
        appearance_text = truncate_text(appearance_text, max_length=120)

    # Format act and location
    act_display = format_act_name(act)
    location_display = location if location else "N/A"
    act_location = f"{act_display} | {location_display}"

    # Build label content as HTML for Paragraph
    content = f'<b><font size="14">{clue_id}</font></b><br/>'
    content += f'<b>{title}</b><br/>'
    if clue_type:
        content += f'{clue_type}<br/>'
    if appearance_text:
        content += f'<i>{appearance_text}</i><br/>'
    content += f'<font size="7">{act_location}</font>'

    return content


def create_label_pdf(clues, output_path):
    """Create PDF with labels for all clues."""
    print(f"Page size: {PAGE_WIDTH/inch:.1f}\" x {PAGE_HEIGHT/inch:.1f}\"")
    print(f"Label size: {LABEL_WIDTH/inch:.2f}\" x {LABEL_HEIGHT/inch:.2f}\"")
    print(f"Grid: {COLS} cols x {ROWS} rows = {LABELS_PER_PAGE} per page")
    print(f"Content area: {CONTENT_WIDTH/inch:.2f}\" x {CONTENT_HEIGHT/inch:.2f}\"")
    print(f"Left margin: {LEFT_MARGIN/inch:.3f}\"  H gutter: {H_GUTTER/inch:.3f}\"")
    print(f"Total clues: {len(clues)}")
    num_pages = (len(clues) + LABELS_PER_PAGE - 1) // LABELS_PER_PAGE
    print(f"Total pages: {num_pages}\n")

    # Text style
    label_style = ParagraphStyle(
        'Label',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=9,
        leading=11,
        leftIndent=0,
        rightIndent=0,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=1,
        textColor=colors.black,
        fontName='Helvetica',
    )

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for page_num in range(num_pages):
        start = page_num * LABELS_PER_PAGE
        page_clues = clues[start:start + LABELS_PER_PAGE]

        for idx, clue in enumerate(page_clues):
            x, y_top = get_content_origin(idx)

            # Optional: draw label border for alignment verification
            # label_col = idx % COLS
            # label_row = idx // COLS
            # label_x = LEFT_MARGIN + label_col * (LABEL_WIDTH + H_GUTTER)
            # label_y_top = PAGE_HEIGHT - (TOP_MARGIN + label_row * LABEL_HEIGHT)
            # c.setStrokeColor(colors.Color(0.85, 0.85, 0.85))
            # c.setLineWidth(0.25)
            # c.rect(label_x, label_y_top - LABEL_HEIGHT, LABEL_WIDTH, LABEL_HEIGHT)

            # Build and draw paragraph
            html = create_label_content(clue)
            para = Paragraph(html, label_style)
            w, h = para.wrap(CONTENT_WIDTH, CONTENT_HEIGHT)

            # drawOn expects the bottom-left of the paragraph block
            # y_top is top of content, so draw at y_top - paragraph_height
            para.drawOn(c, x, y_top - h)

        if page_num < num_pages - 1:
            c.showPage()

    c.save()
    print(f"✅ Label PDF generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate print sheets of labels for clues',
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
        print(f"❌ Error: Clues directory not found: {clues_dir}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading clues from {clues_dir}...")
    clues = load_all_clues(args.clues_dir)

    if not clues:
        print("❌ Error: No clues found", file=sys.stderr)
        return 1

    print(f"Found {len(clues)} clues\n")
    create_label_pdf(clues, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

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


def load_locations():
    """Load the locations reference: room_key -> {id, name, color}."""
    path = project_root / 'src/_data/refs/locations.yaml'
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def hex_to_rgb01(hex_color):
    """Convert '#RRGGBB' to (r, g, b) floats in 0..1."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def draw_key_icon(c, x, y, size, fill_color):
    """
    Draw a stylized key. (x, y) = bottom-left of bounding box. `size` = total width in points.
    Rendered horizontally with the bow (ring) on the left and teeth on the right.
    """
    h = size * 0.55            # height of icon
    bow_r = h * 0.5            # bow outer radius
    bow_cx = x + bow_r
    bow_cy = y + h / 2
    shaft_h = h * 0.28
    shaft_y = bow_cy - shaft_h / 2
    shaft_start = bow_cx + bow_r * 0.85
    shaft_end = x + size
    shaft_w = shaft_end - shaft_start

    c.saveState()
    c.setFillColor(fill_color)
    c.setStrokeColor(fill_color)
    # Bow
    c.circle(bow_cx, bow_cy, bow_r, stroke=0, fill=1)
    # Inner hole (punched with white; reader sees page white through it)
    c.setFillColor(colors.white)
    c.circle(bow_cx, bow_cy, bow_r * 0.42, stroke=0, fill=1)
    c.setFillColor(fill_color)
    # Shaft
    c.rect(shaft_start, shaft_y, shaft_w, shaft_h, fill=1, stroke=0)
    # Two teeth at the tip (pointing down)
    tooth_w = h * 0.16
    tooth_h = h * 0.28
    c.rect(shaft_end - tooth_w, shaft_y - tooth_h, tooth_w, tooth_h, fill=1, stroke=0)
    c.rect(shaft_end - tooth_w * 3, shaft_y - tooth_h * 0.7, tooth_w, tooth_h * 0.7, fill=1, stroke=0)
    c.restoreState()


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


def draw_label(c, idx, clue, label_style, act_style, locations):
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

    # Location lookup
    loc_field = clue.get('location')
    room_key = loc_field.get('room') if isinstance(loc_field, dict) else loc_field if isinstance(loc_field, str) else None
    loc_info = locations.get(room_key) if room_key else None
    loc_note = loc_field.get('description') if isinstance(loc_field, dict) else None

    skills = clue.get('skills') or []
    is_key = clue.get('is_key') or []
    if isinstance(skills, str): skills = [skills]
    if isinstance(is_key, str): is_key = [is_key]

    # Format appearance
    appearance_text = ""
    if appearance:
        appearance_clean = str(appearance).strip().replace('**', '').replace('*', '')
        lines = appearance_clean.split('\n')
        appearance_text = lines[0] if lines else ""
        appearance_text = truncate_text(appearance_text, max_length=80)

    act_display = format_act_name(act)

    # ── Location badge (colored circle with code) — top-right corner ──
    badge_radius = 0.14 * inch
    badge_cx = label_x + LABEL_WIDTH - PADDING - badge_radius
    badge_cy = label_y_top - PADDING - badge_radius
    if loc_info:
        r, g, b = hex_to_rgb01(loc_info.get('color', '#888888'))
        c.setFillColor(colors.Color(r, g, b))
        c.setStrokeColor(colors.Color(r * 0.6, g * 0.6, b * 0.6))
        c.setLineWidth(0.4)
        c.circle(badge_cx, badge_cy, badge_radius, stroke=1, fill=1)
        code = str(loc_info.get('id', '?'))
        # Pick text color based on background luminance
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        c.setFillColor(colors.white if lum < 0.6 else colors.black)
        fs = 7 if len(code) <= 2 else 6
        c.setFont('Helvetica-Bold', fs)
        text_w = c.stringWidth(code, 'Helvetica-Bold', fs)
        c.drawString(badge_cx - text_w / 2, badge_cy - fs / 3, code)

    # Reserve horizontal space so the ID doesn't overlap the badge
    id_right_reserve = (2 * badge_radius) + 0.06 * inch if loc_info else 0

    # ── Layout: text on the left, image on the right (if present) ──
    if image_field:
        img_path = resolve_image_path(image_field)
    else:
        img_path = None

    if img_path:
        img_area_width = CONTENT_WIDTH * 0.35
        text_width = CONTENT_WIDTH - img_area_width - 0.05 * inch
    else:
        text_width = CONTENT_WIDTH
        img_area_width = 0

    # ── Build main text block: ID, title, appearance ──
    head_width = max(text_width - id_right_reserve, text_width * 0.5) if not img_path else text_width
    head_html = f'<b><font size="11">{clue_id}</font></b>'
    head_para = Paragraph(head_html, label_style)
    hw, hh = head_para.wrap(head_width, 18)
    head_para.drawOn(c, cx, cy_top - hh)

    # Ensure next row clears both the ID block and the location badge
    badge_bottom_gap = (2 * badge_radius + 3) if loc_info else 0
    top_block_h = max(hh, badge_bottom_gap)
    cursor_y = cy_top - top_block_h - 2  # running y-cursor (top edge of next block)

    # ── KEY row (prominent, right below ID) ──
    if is_key:
        tracks = ", ".join(str(k).replace('_', ' ').title() for k in is_key)
        key_color = colors.Color(0.70, 0.48, 0.10)  # amber/gold
        key_row_h = 10
        icon_size = 10
        icon_y = cursor_y - key_row_h + 1
        draw_key_icon(c, cx, icon_y, icon_size, key_color)
        # Track name, bold, slightly larger
        track_style = ParagraphStyle(
            'KeyTrack', parent=label_style,
            fontName='Helvetica-Bold', fontSize=7, leading=9,
            textColor=key_color,
        )
        track_para = Paragraph(f'<b>{tracks}</b>', track_style)
        tw, th = track_para.wrap(text_width - icon_size - 3, 12)
        track_para.drawOn(c, cx + icon_size + 3, cursor_y - th)
        cursor_y -= max(key_row_h, th) + 2

    # ── Location note (★ bold red) ──
    if loc_note:
        note_style = ParagraphStyle(
            'LocNote', parent=label_style,
            fontName='Helvetica-Bold', fontSize=6.5, leading=8,
            textColor=colors.Color(0.78, 0.10, 0.10),
        )
        note_html = f'<b>&#9733; {loc_note}</b>'
        note_para = Paragraph(note_html, note_style)
        nw, nh = note_para.wrap(text_width, 20)
        note_para.drawOn(c, cx, cursor_y - nh)
        cursor_y -= nh + 2

    # Title + appearance
    body_html = f'<b><font size="7">{title}</font></b>'
    if appearance_text:
        body_html += f'<br/><i><font size="5.5">{appearance_text}</font></i>'

    body_para = Paragraph(body_html, label_style)
    body_max_h = cursor_y - (label_y_top - LABEL_HEIGHT + PADDING) - 18  # reserve bottom for skills + act row
    bw, bh = body_para.wrap(text_width, max(body_max_h, 10))
    body_para.drawOn(c, cx, cursor_y - bh)

    # ── Skills — small grey row above the bottom (act + location) ──
    bottom_line_y = label_y_top - LABEL_HEIGHT + PADDING
    meta_y = bottom_line_y + 10

    if skills:
        pretty = ", ".join(str(s).replace('_', ' ') for s in skills)
        skills_html = f'<font size="5" color="#444444">{pretty}</font>'
        skills_para = Paragraph(skills_html, label_style)
        mw, mh = skills_para.wrap(text_width, 12)
        skills_para.drawOn(c, cx, meta_y - mh + 4)

    # ── Bottom line: act (left) + location full name (right) ──
    if act_display:
        act_para = Paragraph(f'<font size="6" color="#666666">{act_display}</font>', act_style)
        aw, ah = act_para.wrap(text_width * 0.6, 12)
        act_para.drawOn(c, cx, bottom_line_y)

    if loc_info:
        loc_name = loc_info.get('name', room_key)
        loc_html = f'<font size="6" color="#666666">{loc_name}</font>'
        loc_para = Paragraph(loc_html, act_style)
        # right-align within text column
        lw, lh = loc_para.wrap(text_width, 12)
        # draw right-aligned by recomputing with right alignment style
        right_style = ParagraphStyle('LocRight', parent=act_style, alignment=2)
        loc_para = Paragraph(loc_html, right_style)
        loc_para.wrap(text_width, 12)
        loc_para.drawOn(c, cx, bottom_line_y)

    # ── Draw image on the right ──
    if img_path:
        try:
            img = ImageReader(str(img_path))
            iw, ih = img.getSize()
            aspect = iw / ih

            max_img_w = img_area_width
            max_img_h = CONTENT_HEIGHT - 0.3 * inch  # leave top for badge, bottom for meta/act

            if aspect > (max_img_w / max_img_h):
                draw_w = max_img_w
                draw_h = draw_w / aspect
            else:
                draw_h = max_img_h
                draw_w = draw_h * aspect

            img_x = cx + text_width + 0.05 * inch + (max_img_w - draw_w) / 2
            img_y = (cy_top - 0.15 * inch) - CONTENT_HEIGHT / 2 - draw_h / 2

            c.drawImage(str(img_path), img_x, img_y, draw_w, draw_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Warning: Could not load image for {clue_id}: {e}", file=sys.stderr)


def create_label_pdf(clues, output_path, locations=None):
    """Create PDF with labels for all clues."""
    locations = locations or {}
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
            draw_label(c, idx, clue, label_style, act_style, locations)

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
    locations = load_locations()
    create_label_pdf(clues, output_path, locations=locations)

    return 0


if __name__ == "__main__":
    sys.exit(main())

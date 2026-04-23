#!/usr/bin/env python3
"""
Generate per-location Jar/Prop packing labels in a 3-column PDF layout.

For each location, up to two labels are produced (only if items exist):
  - "<Location Name> (<CODE>) - Jars"  for botanical jars/dried herbs
  - "<Location Name> (<CODE>) - Props" for artifact objects/paintings that have
    an explicit `prop:` field

Labels are laid out in 3 fixed-width columns. Each label's height is
content-driven (depends on its item count); rows pack using the tallest label
in each row.

Each label shows a colored header banner with the location name and code,
then a bulleted list of items: the bullet is a filled disk (J) for jars or
an outlined circle (P) for props, followed by the clue ID, title, and a
short appearance description in parentheses.

Usage:
    python scripts/reference_generators/generate_jar_prop_labels.py
    python scripts/reference_generators/generate_jar_prop_labels.py --output to_print/jar_prop_labels.pdf
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict

import yaml
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT

project_root = Path(__file__).parent.parent.parent

# ── Page & grid ───────────────────────────────────────────────────
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11.0 * inch

COLS = 3
LABEL_WIDTH = 2.7 * inch
PADDING = 0.12 * inch
COL_GAP = 0.1 * inch
ROW_GAP = 0.12 * inch

GRID_WIDTH = COLS * LABEL_WIDTH + (COLS - 1) * COL_GAP
LEFT_MARGIN = (PAGE_WIDTH - GRID_WIDTH) / 2
TOP_MARGIN = 0.4 * inch
BOTTOM_MARGIN = 0.4 * inch

HEADER_HEIGHT = 0.45 * inch
BODY_TOP_GAP = 0.08 * inch
ITEM_GAP = 4  # points between items
BODY_BOTTOM_PAD = 0.1 * inch

# ── Classification (mirrors generate_location_bin_labels.py) ──────
JAR_TYPES = {"Botanical (Dried Herb)", "Botanical (Jar)"}
PROP_CANDIDATE_TYPES = {
    "Artifact (Object)",
    "Artifact (Painting)",
    "Document (Administrative)",
}


def hex_to_rgb01(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def contrast_text_color(r, g, b):
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return colors.white if lum < 0.6 else colors.black


def load_locations():
    path = project_root / "src/_data/refs/locations.yaml"
    return yaml.safe_load(path.read_text()) or {}


def load_jars_and_props():
    """Walk all clues; return {room_key: {"jars": [clue, ...], "props": [clue, ...]}}."""
    by_room = defaultdict(lambda: {"jars": [], "props": []})

    for yaml_file in sorted((project_root / "src/_data/clues").rglob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text())
        except Exception as e:
            print(f"[skip] {yaml_file.relative_to(project_root)}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue
        if "previous_id" in data:
            continue

        loc = data.get("location")
        room = loc.get("room") if isinstance(loc, dict) else loc if isinstance(loc, str) else None
        if not room or room == "N/A":
            continue

        t = data.get("type", "")
        if t in JAR_TYPES:
            by_room[room]["jars"].append(data)
        elif t in PROP_CANDIDATE_TYPES and data.get("prop"):
            by_room[room]["props"].append(data)

    for room in by_room:
        by_room[room]["jars"].sort(key=lambda d: d["id"])
        by_room[room]["props"].sort(key=lambda d: d["id"])

    return by_room


def short_appearance(text, max_chars=80):
    if not text:
        return ""
    clean = str(text).strip().replace("**", "").replace("*", "")
    first = clean.split("\n")[0].strip()
    if len(first) <= max_chars:
        return first
    return first[:max_chars - 1].rstrip() + "…"


def item_html(item):
    clue_id = item.get("id", "?")
    title = str(item.get("title", "")).strip()
    appearance = short_appearance(item.get("appearance", ""), max_chars=90)
    html = (
        f'<b><font size="8">{clue_id}</font></b>'
        f' <font size="7" color="#333333">- {title}'
    )
    if appearance:
        html += f' <i>({appearance})</i>'
    html += '</font>'
    return html


def measure_label_height(items, body_style):
    """Return the content-driven height of a label in points."""
    bullet_radius = 0.08 * inch
    bullet_gap = 0.06 * inch
    body_width = LABEL_WIDTH - 2 * PADDING
    text_width = body_width - 2 * bullet_radius - bullet_gap

    body_h = 0
    for i, item in enumerate(items):
        p = Paragraph(item_html(item), body_style)
        _, ph = p.wrap(text_width, 10 * inch)
        body_h += ph
        if i < len(items) - 1:
            body_h += ITEM_GAP

    return HEADER_HEIGHT + BODY_TOP_GAP + body_h + BODY_BOTTOM_PAD


def draw_bullet_jar(c, cx, cy, radius, fill_color):
    c.saveState()
    c.setFillColor(fill_color)
    c.setStrokeColor(fill_color)
    c.circle(cx, cy, radius, stroke=0, fill=1)
    r, g, b = fill_color.red, fill_color.green, fill_color.blue
    c.setFillColor(contrast_text_color(r, g, b))
    font_size = radius * 1.4
    c.setFont("Helvetica-Bold", font_size)
    tw = c.stringWidth("J", "Helvetica-Bold", font_size)
    c.drawString(cx - tw / 2, cy - font_size / 3, "J")
    c.restoreState()


def draw_bullet_prop(c, cx, cy, radius, stroke_color):
    c.saveState()
    c.setFillColor(colors.white)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(1.2)
    c.circle(cx, cy, radius, stroke=1, fill=1)
    c.setFillColor(stroke_color)
    font_size = radius * 1.4
    c.setFont("Helvetica-Bold", font_size)
    tw = c.stringWidth("P", "Helvetica-Bold", font_size)
    c.drawString(cx - tw / 2, cy - font_size / 3, "P")
    c.restoreState()


def draw_label(c, label_x, label_y_top, label_h, loc_info, kind, items, body_style):
    label_y_bot = label_y_top - label_h

    c.setStrokeColor(colors.Color(0.75, 0.75, 0.75))
    c.setLineWidth(0.5)
    c.rect(label_x, label_y_bot, LABEL_WIDTH, label_h, stroke=1, fill=0)

    # Header banner
    hex_color = loc_info.get("color", "#888888")
    r, g, b = hex_to_rgb01(hex_color)
    header_bg = colors.Color(r, g, b)
    c.setFillColor(header_bg)
    c.rect(label_x, label_y_top - HEADER_HEIGHT, LABEL_WIDTH, HEADER_HEIGHT, stroke=0, fill=1)

    name = loc_info.get("name", "?")
    code = loc_info.get("id", "?")
    kind_label = "Jars" if kind == "jars" else "Props"
    header_str = f"{name} ({code}) - {kind_label}"

    c.setFillColor(contrast_text_color(r, g, b))
    font_size = 14
    while font_size > 8:
        c.setFont("Helvetica-Bold", font_size)
        if c.stringWidth(header_str, "Helvetica-Bold", font_size) < LABEL_WIDTH - 2 * PADDING:
            break
        font_size -= 1
    c.setFont("Helvetica-Bold", font_size)
    tw = c.stringWidth(header_str, "Helvetica-Bold", font_size)
    c.drawString(label_x + (LABEL_WIDTH - tw) / 2,
                 label_y_top - HEADER_HEIGHT / 2 - font_size / 3,
                 header_str)

    # Body
    body_top = label_y_top - HEADER_HEIGHT - BODY_TOP_GAP
    body_x = label_x + PADDING
    body_width = LABEL_WIDTH - 2 * PADDING

    bullet_radius = 0.08 * inch
    bullet_gap = 0.06 * inch
    text_x = body_x + 2 * bullet_radius + bullet_gap
    text_width = body_width - (text_x - body_x)

    jar_color = colors.Color(r * 0.85, g * 0.85, b * 0.85)
    prop_color = colors.Color(0.15, 0.15, 0.15)

    y = body_top
    for item in items:
        p = Paragraph(item_html(item), body_style)
        _, ph = p.wrap(text_width, 10 * inch)

        bullet_cy = y - bullet_radius - 1
        bullet_cx = body_x + bullet_radius
        if kind == "jars":
            draw_bullet_jar(c, bullet_cx, bullet_cy, bullet_radius, jar_color)
        else:
            draw_bullet_prop(c, bullet_cx, bullet_cy, bullet_radius, prop_color)

        p.drawOn(c, text_x, y - ph)
        y -= ph + ITEM_GAP


def build_label_queue(locations, by_room):
    """Return list of (loc_info, kind, items) tuples in stable order."""
    queue = []
    for room_key in sorted(locations.keys()):
        entry = by_room.get(room_key)
        if not entry:
            continue
        loc_info = locations[room_key]
        if entry["jars"]:
            queue.append((loc_info, "jars", entry["jars"]))
        if entry["props"]:
            queue.append((loc_info, "props", entry["props"]))
    return queue


def pack_rows(labels_with_heights):
    """Pack labels into rows of up to COLS items. Returns list of rows."""
    rows = []
    for i in range(0, len(labels_with_heights), COLS):
        rows.append(labels_with_heights[i:i + COLS])
    return rows


def create_pdf(queue, output_path, body_style):
    # Measure each label
    labels_with_heights = [
        (loc_info, kind, items, measure_label_height(items, body_style))
        for loc_info, kind, items in queue
    ]
    rows = pack_rows(labels_with_heights)

    print(f"Page: {PAGE_WIDTH/inch:.1f}\" x {PAGE_HEIGHT/inch:.1f}\"")
    print(f"Columns: {COLS}  Label width: {LABEL_WIDTH/inch:.2f}\"")
    print(f"Labels: {len(queue)}  Rows: {len(rows)}\n")

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    page_top = PAGE_HEIGHT - TOP_MARGIN
    bottom_limit = BOTTOM_MARGIN
    cursor_y = page_top

    for row in rows:
        row_height = max(h for _, _, _, h in row)
        # New page if this row doesn't fit
        if cursor_y - row_height < bottom_limit:
            c.showPage()
            cursor_y = page_top

        for col_idx, (loc_info, kind, items, h) in enumerate(row):
            x = LEFT_MARGIN + col_idx * (LABEL_WIDTH + COL_GAP)
            draw_label(c, x, cursor_y, h, loc_info, kind, items, body_style)
            print(f"  {loc_info.get('name', '?'):22s} {kind:5s} "
                  f"({len(items)}) h={h:.0f}pt  "
                  f"{', '.join(it['id'] for it in items)}")

        cursor_y -= row_height + ROW_GAP

    c.save()
    print(f"\nSaved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate 3-column jar/prop packing labels per location.")
    parser.add_argument("--output", "-o", default="to_print/jar_prop_labels.pdf",
                        help="Output PDF path (default: to_print/jar_prop_labels.pdf)")
    args = parser.parse_args()

    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    body_style = ParagraphStyle(
        "Body",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=7,
        leading=9,
        leftIndent=0,
        rightIndent=0,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        fontName="Helvetica",
        textColor=colors.black,
    )

    locations = load_locations()
    by_room = load_jars_and_props()
    queue = build_label_queue(locations, by_room)

    if not queue:
        print("No jars or props found — nothing to generate.", file=sys.stderr)
        return 1

    create_pdf(queue, output_path, body_style)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Generate 4x5 inch location-bin labels, 4 per letter sheet, one per location.

Each label contains:
  - Big location name + code (e.g., "Pantry (P)") with the location's color
    used as a banner background.
  - Total clue count in the room (sum across all physical-type bins).
  - Per-bin breakdown (Jar / Object / Paper / Photo / Document / Newspaper /
    Rumor / Vision) for that room, showing the bin name + count + comma-
    separated clue IDs.

Bins are physical types — derived from the clue YAML `type` field (not the id
prefix, which collides for Paintings/Paper and Sebastian/Silas). See
`PHYSICAL_TYPE_MAP` below.

Usage:
    python scripts/reference_generators/generate_location_bin_labels.py
    python scripts/reference_generators/generate_location_bin_labels.py --output to_print/location_bins.pdf
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
from reportlab.lib.enums import TA_LEFT, TA_CENTER

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ── Page & label specs ─────────────────────────────────────────────
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11.0 * inch

LABEL_WIDTH = 4.0 * inch
LABEL_HEIGHT = 5.0 * inch
PADDING = 0.2 * inch

COLS = 2
ROWS = 2
LABELS_PER_PAGE = COLS * ROWS

GRID_WIDTH = COLS * LABEL_WIDTH
GRID_HEIGHT = ROWS * LABEL_HEIGHT
LEFT_MARGIN = (PAGE_WIDTH - GRID_WIDTH) / 2
TOP_MARGIN = (PAGE_HEIGHT - GRID_HEIGHT) / 2

HEADER_HEIGHT = 0.9 * inch  # colored banner at the top

# ── Physical-type buckets ──────────────────────────────────────────
# Keys are bin display names; values are sets of matching `type` field values.
PHYSICAL_TYPE_MAP = {
    "Jar": {"Botanical (Dried Herb)", "Botanical (Jar)"},
    "Plant": {"Botanical (Garden Herb)", "Botanical (Garden Tree)"},
    # "Object" and "Prop" both draw from the same set of types; split by presence
    # of the `prop` field on the clue. See classify().
    "Object": {
        "Artifact (Object)",
        "Artifact (Painting)",
        "Document (Administrative)",
    },
    "Paper": {"Artifact (Paper)"},  # Writing(…) added dynamically below
    "Photo": {"Artifact (Photo)"},
    "Document": {
        "Document (Business)",
        "Document (Financial)",
        "Document (Legal)",
        "Document (Medical)",
    },
    "Newspaper": {"Newspaper Article"},
    "Rumor": {"Rumor"},
    "Vision": set(),  # Vision(…) added dynamically below
}

BIN_ORDER = ["Jar", "Plant", "Prop", "Object", "Paper", "Diary", "Photo", "Document", "Newspaper", "Rumor", "Vision"]


def hex_to_rgb01(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def classify(clue_data: dict) -> str | None:
    """Return the physical bin for a clue, or None to skip/unclassified.

    Chain logic:
      - chain head  (has next_id, no previous_id)        → "Diary"
      - chain body  (has previous_id)                    → None (part of the head's diary)
      - standalone  (neither chain link)                 → map by `type`
    """
    if "previous_id" in clue_data:
        return None  # mid/tail of a chain — same physical object as the head
    if "next_id" in clue_data:
        return "Diary"

    clue_type = clue_data.get("type")
    if not clue_type:
        return None

    # Object → Prop when a physical item is explicitly provided via the `prop:` field.
    if clue_type in PHYSICAL_TYPE_MAP["Object"]:
        return "Prop" if clue_data.get("prop") else "Object"

    for bin_name, types in PHYSICAL_TYPE_MAP.items():
        if clue_type in types:
            return bin_name
    if clue_type.startswith("Writing ("):
        return "Paper"
    if clue_type.startswith("Vision ("):
        return "Vision"
    return None


def load_locations():
    path = project_root / "src/_data/refs/locations.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def load_clues_by_room():
    """Walk all clues; return {room_key: {bin_name: [clue_id, ...]}}."""
    by_room = defaultdict(lambda: defaultdict(list))
    unclassified = []
    no_room = []

    for yaml_file in sorted((project_root / "src/_data/clues").rglob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text())
        except Exception as e:
            print(f"[skip] {yaml_file.relative_to(project_root)}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue

        clue_id = str(data["id"])
        clue_type = data.get("type", "")
        loc = data.get("location")
        room = loc.get("room") if isinstance(loc, dict) else loc if isinstance(loc, str) else None

        bin_name = classify(data)
        if bin_name is None:
            # Chain middles/tails are silently absorbed by the head; only flag truly unknown types.
            if "previous_id" not in data:
                unclassified.append((clue_id, clue_type))
            continue
        if not room or room == "N/A":
            no_room.append((clue_id, clue_type))
            continue

        by_room[room][bin_name].append(clue_id)

    return by_room, unclassified, no_room


def get_label_origin(idx):
    col = idx % COLS
    row = idx // COLS
    x = LEFT_MARGIN + col * LABEL_WIDTH
    y_from_top = TOP_MARGIN + row * LABEL_HEIGHT
    y_top = PAGE_HEIGHT - y_from_top
    return x, y_top


def contrast_text_color(r, g, b):
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return colors.white if lum < 0.6 else colors.black


def draw_label(c, idx, room_key, loc_info, bins):
    label_x, label_y_top = get_label_origin(idx)
    label_y_bot = label_y_top - LABEL_HEIGHT

    # Cut border (thin grey)
    c.setStrokeColor(colors.Color(0.75, 0.75, 0.75))
    c.setLineWidth(0.5)
    c.rect(label_x, label_y_bot, LABEL_WIDTH, LABEL_HEIGHT, stroke=1, fill=0)

    # ── Header banner (colored) ──
    hex_color = loc_info.get("color", "#888888") if loc_info else "#888888"
    r, g, b = hex_to_rgb01(hex_color)
    c.setFillColor(colors.Color(r, g, b))
    c.rect(label_x, label_y_top - HEADER_HEIGHT, LABEL_WIDTH, HEADER_HEIGHT, stroke=0, fill=1)

    # Header text
    text_color = contrast_text_color(r, g, b)
    name = loc_info.get("name", room_key) if loc_info else room_key
    code = loc_info.get("id", "?") if loc_info else "?"
    header_str = f"{name} ({code})"

    # Fit header text — shrink if wide
    c.setFillColor(text_color)
    font_size = 28
    while font_size > 14:
        c.setFont("Helvetica-Bold", font_size)
        if c.stringWidth(header_str, "Helvetica-Bold", font_size) < LABEL_WIDTH - 2 * PADDING:
            break
        font_size -= 2
    c.setFont("Helvetica-Bold", font_size)
    tw = c.stringWidth(header_str, "Helvetica-Bold", font_size)
    c.drawString(label_x + (LABEL_WIDTH - tw) / 2,
                 label_y_top - HEADER_HEIGHT / 2 - font_size / 3,
                 header_str)

    # ── Body ──
    body_x = label_x + PADDING
    body_top = label_y_top - HEADER_HEIGHT - PADDING * 0.6
    body_width = LABEL_WIDTH - 2 * PADDING

    # Total count
    total = sum(len(v) for v in bins.values())
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    total_str = f"Total clues: {total}"
    c.drawString(body_x, body_top - 12, total_str)

    # Per-bin breakdown
    section_style = ParagraphStyle(
        "BinSection",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName="Helvetica",
    )

    y = body_top - 22
    for bin_name in BIN_ORDER:
        ids = sorted(bins.get(bin_name, []))
        if not ids:
            continue
        id_str = ", ".join(ids)
        html = (
            f'<b><font size="9">{bin_name} ({len(ids)})</font></b>'
            f'<br/><font size="7" color="#444444">{id_str}</font>'
        )
        p = Paragraph(html, section_style)
        pw, ph = p.wrap(body_width, LABEL_HEIGHT)
        if y - ph < label_y_bot + PADDING * 0.5:
            # ran out of vertical space
            c.setFillColor(colors.Color(0.5, 0.0, 0.0))
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(body_x, label_y_bot + PADDING * 0.5, "…more")
            break
        p.drawOn(c, body_x, y - ph)
        y = y - ph - 3


def create_pdf(locations, by_room, output_path):
    rooms = sorted(locations.keys())
    num_pages = (len(rooms) + LABELS_PER_PAGE - 1) // LABELS_PER_PAGE

    print(f"Page: {PAGE_WIDTH/inch:.1f}\" x {PAGE_HEIGHT/inch:.1f}\"")
    print(f"Label: {LABEL_WIDTH/inch:.1f}\" x {LABEL_HEIGHT/inch:.1f}\"   grid {COLS}x{ROWS} = {LABELS_PER_PAGE}/page")
    print(f"Rooms: {len(rooms)}  →  Pages: {num_pages}\n")

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    for page_num in range(num_pages):
        start = page_num * LABELS_PER_PAGE
        page_rooms = rooms[start:start + LABELS_PER_PAGE]
        for idx, room_key in enumerate(page_rooms):
            loc_info = locations.get(room_key, {})
            bins = by_room.get(room_key, {})
            draw_label(c, idx, room_key, loc_info, bins)
            total = sum(len(v) for v in bins.values())
            print(f"  {room_key:24s} {loc_info.get('id','?'):4s} total={total}")
        if page_num < num_pages - 1:
            c.showPage()
    c.save()
    print(f"\nSaved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate 4x5\" location-bin labels (4 per letter sheet).")
    parser.add_argument("--output", "-o", default="to_print/location_bins.pdf",
                        help="Output PDF path (default: to_print/location_bins.pdf)")
    args = parser.parse_args()

    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    locations = load_locations()
    by_room, unclassified, no_room = load_clues_by_room()

    if unclassified:
        print(f"⚠ {len(unclassified)} clue(s) had unrecognized `type`:", file=sys.stderr)
        for cid, t in unclassified:
            print(f"    {cid:10s} type={t!r}", file=sys.stderr)
    if no_room:
        print(f"ℹ {len(no_room)} clue(s) have no room (skipped): "
              f"{', '.join(cid for cid, _ in no_room[:10])}"
              f"{'…' if len(no_room) > 10 else ''}")

    # Detect any rooms in data that are missing from locations.yaml
    missing_loc_info = [r for r in by_room if r not in locations]
    if missing_loc_info:
        print(f"⚠ Rooms found in clue data but not in locations.yaml: {missing_loc_info}", file=sys.stderr)

    create_pdf(locations, by_room, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

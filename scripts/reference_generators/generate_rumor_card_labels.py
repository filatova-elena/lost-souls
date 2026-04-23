#!/usr/bin/env python3
"""
Generate 2"-wide rumor card labels in PDF format.

Each label is a single colored banner showing: "R<id> - <RUMORS_...>"

Banner color is a lightened shade of the room color from
src/_data/refs/locations.yaml (looked up via the collection's room).
Collections sharing a room get progressively lighter shades so they
stay visually distinct.

Usage:
    python scripts/reference_generators/generate_rumor_card_labels.py
    python scripts/reference_generators/generate_rumor_card_labels.py --output to_print/rumor_card_labels.pdf
"""

import argparse
import sys
from pathlib import Path

import yaml
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11.0 * inch

LABEL_WIDTH = 2.0 * inch
LABEL_HEIGHT = 0.5 * inch

COLS = 4
ROWS = 20
LABELS_PER_PAGE = COLS * ROWS

GRID_WIDTH = COLS * LABEL_WIDTH
GRID_HEIGHT = ROWS * LABEL_HEIGHT
LEFT_MARGIN = (PAGE_WIDTH - GRID_WIDTH) / 2
TOP_MARGIN = (PAGE_HEIGHT - GRID_HEIGHT) / 2

UNASSIGNED_COLOR = "#BBBBBB"


def hex_to_rgb01(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lighten(hex_color, amount):
    """Mix with white. amount=0 → original, amount=1 → white."""
    r, g, b = hex_to_rgb01(hex_color)
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def contrast_text_color(r, g, b):
    return colors.white if (0.299 * r + 0.587 * g + 0.114 * b) < 0.6 else colors.black


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_locations():
    return load_yaml(project_root / "src/_data/refs/locations.yaml") or {}


def load_collections():
    """collection_id -> room_key"""
    out = {}
    for f in sorted((project_root / "src/_data/clues/rumors").glob("*.yaml")):
        d = load_yaml(f)
        if not d or not str(d.get("id", "")).startswith("RUMORS_"):
            continue
        loc = d.get("location")
        room = loc.get("room") if isinstance(loc, dict) else loc if isinstance(loc, str) else None
        out[d["id"]] = room
    return out


def load_rumors():
    rumors = []
    for f in sorted((project_root / "src/_data/rumors").rglob("*.yaml")):
        d = load_yaml(f)
        if d and str(d.get("type", "")).startswith("Rumor"):
            rumors.append(d)
    # Sort numerically by R-id (R1, R2, ..., R74)
    rumors.sort(key=lambda d: int(str(d["id"]).lstrip("R")))
    return rumors


def build_collection_shade_map(collection_to_room):
    """
    For each collection, pick a lightness amount so that collections sharing
    a room get progressively lighter shades (alphabetical order → lightest last).
    Returns: collection_id -> lighten amount (0..1).
    """
    by_room = {}
    for coll, room in collection_to_room.items():
        by_room.setdefault(room, []).append(coll)
    amounts = {}
    for room, colls in by_room.items():
        colls_sorted = sorted(colls)
        n = len(colls_sorted)
        # Base 0.40 (light) → up to 0.65 (very light) as we go down the list.
        for i, coll in enumerate(colls_sorted):
            amounts[coll] = 0.40 if n == 1 else 0.40 + (0.25 * i / (n - 1))
    return amounts


def get_label_origin(idx):
    col = idx % COLS
    row = idx // COLS
    x = LEFT_MARGIN + col * LABEL_WIDTH
    y_from_top = TOP_MARGIN + row * LABEL_HEIGHT
    y_top = PAGE_HEIGHT - y_from_top
    return x, y_top


def fit_text(c, text, max_width, font_name, max_size, min_size=6):
    """Shrink font until text fits the given width. Returns chosen size."""
    size = max_size
    while size > min_size:
        if c.stringWidth(text, font_name, size) <= max_width:
            return size
        size -= 0.5
    return min_size


def draw_label(c, idx, rumor, locations, collection_to_room, shade_amounts):
    label_x, label_y_top = get_label_origin(idx)
    label_y_bot = label_y_top - LABEL_HEIGHT

    rumor_id = rumor["id"]
    coll_id = rumor.get("collection") or "unassigned"
    room = collection_to_room.get(coll_id)
    loc_info = locations.get(room) if room else None
    loc_hex = loc_info.get("color", UNASSIGNED_COLOR) if loc_info else UNASSIGNED_COLOR

    amount = shade_amounts.get(coll_id, 0.40)
    r, g, b = lighten(loc_hex, amount)
    c.setFillColor(colors.Color(r, g, b))
    c.rect(label_x, label_y_bot, LABEL_WIDTH, LABEL_HEIGHT, stroke=0, fill=1)

    text = f"{rumor_id} - {coll_id}"
    pad_x = 0.08 * inch
    size = fit_text(c, text, LABEL_WIDTH - 2 * pad_x, "Helvetica-Bold", 11)
    c.setFillColor(contrast_text_color(r, g, b))
    c.setFont("Helvetica-Bold", size)
    tw = c.stringWidth(text, "Helvetica-Bold", size)
    c.drawString(label_x + (LABEL_WIDTH - tw) / 2,
                 label_y_bot + LABEL_HEIGHT / 2 - size / 3, text)

    c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
    c.setLineWidth(0.4)
    c.rect(label_x, label_y_bot, LABEL_WIDTH, LABEL_HEIGHT, stroke=1, fill=0)


def create_pdf(rumors, locations, collection_to_room, output_path):
    shade_amounts = build_collection_shade_map(collection_to_room)
    num_pages = (len(rumors) + LABELS_PER_PAGE - 1) // LABELS_PER_PAGE

    print(f"Page: {PAGE_WIDTH/inch:.1f}\" x {PAGE_HEIGHT/inch:.1f}\"")
    print(f"Label: {LABEL_WIDTH/inch:.1f}\" x {LABEL_HEIGHT/inch:.2f}\"   grid {COLS}x{ROWS} = {LABELS_PER_PAGE}/page")
    print(f"Rumors: {len(rumors)}  →  Pages: {num_pages}\n")

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    for page_num in range(num_pages):
        start = page_num * LABELS_PER_PAGE
        page_rumors = rumors[start:start + LABELS_PER_PAGE]
        for idx, rumor in enumerate(page_rumors):
            draw_label(c, idx, rumor, locations, collection_to_room, shade_amounts)
        if page_num < num_pages - 1:
            c.showPage()
    c.save()
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate 2\"-wide rumor card labels.")
    parser.add_argument("--output", "-o", default="to_print/rumor_card_labels.pdf")
    args = parser.parse_args()

    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    locations = load_locations()
    collection_to_room = load_collections()
    rumors = load_rumors()

    unassigned = [r["id"] for r in rumors if not r.get("collection") or r.get("collection") == "unassigned"]
    if unassigned:
        print(f"ℹ {len(unassigned)} rumor(s) with `unassigned` collection (grey label): {', '.join(unassigned)}\n", file=sys.stderr)

    create_pdf(rumors, locations, collection_to_room, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

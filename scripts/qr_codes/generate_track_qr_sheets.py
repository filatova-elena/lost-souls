#!/usr/bin/env python3
"""
Generate two print sheets of QR codes:

1. Track key-clue sheet  — one column per quest track, each column holding the
   QR codes for that track's clue chain (the "key" clues), in order.
2. Story gates sheet     — one column per story gate, holding the QR codes for
   the clues that unlock that gate/act.

Reuses generate_qr() from qr_generator.py. Output is a single-page PNG (and PDF)
per sheet, sized for 8.5x11" letter printing.

Usage:
    python generate_track_qr_sheets.py
    python generate_track_qr_sheets.py --dpi 300 --fg "#4a148c"
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from qr_generator import generate_qr, parse_color

ROOT = Path(__file__).parent.parent.parent
QUESTS_DIR = ROOT / "src/_data/quests"
GATES_FILE = ROOT / "src/_data/refs/story_gates.yaml"

TRACK_FILES = [
    "track_dirty_dealings.yaml",
    "track_secret_baby.yaml",
    "track_magic_elixir.yaml",
    "track_psychics_burden.yaml",
]

BASE_URL = "https://lostsouls.door66.events/clues"

# Page / layout (inches)
PAGE_W_IN = 8.5
PAGE_H_IN = 11.0
MARGIN_IN = 0.35
COL_GAP_IN = 0.12
QR_GAP_IN = 0.10
CAPTION_H_IN = 0.26
TITLE_H_IN = 0.55
HEADER_H_IN = 0.75


def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def qr_image(url, label, size, fg_color, bg_color):
    """Render one labeled QR code as a PIL RGBA image (square, upright)."""
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


def clue_url(clue_id):
    return f"{BASE_URL}/{clue_id}/"


def _draw_centered(draw, cx, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def make_sheet(columns, output_stem, sheet_title, dpi, fg_color, bg_color):
    """
    columns: list of dicts with keys:
        title    -> str (column header, drawn bold)
        subtitle -> str | None (drawn under title, lighter)
        codes    -> list of (url, label)
    """
    page_w = int(PAGE_W_IN * dpi)
    page_h = int(PAGE_H_IN * dpi)
    margin = int(MARGIN_IN * dpi)
    col_gap = int(COL_GAP_IN * dpi)
    qr_gap = int(QR_GAP_IN * dpi)
    caption_h = int(CAPTION_H_IN * dpi)
    title_h = int(TITLE_H_IN * dpi)
    header_h = int(HEADER_H_IN * dpi)

    n_cols = len(columns)
    usable_w = page_w - 2 * margin
    col_w = (usable_w - (n_cols - 1) * col_gap) // n_cols

    # QR size: fit the column width, but cap so the tallest column fits vertically.
    # Each cell is qr_size + caption_h tall.
    max_codes = max(len(c["codes"]) for c in columns)
    avail_h = page_h - 2 * margin - title_h - header_h
    qr_by_h = (avail_h - (max_codes - 1) * qr_gap - max_codes * caption_h) // max_codes
    qr_size = min(col_w, qr_by_h)

    fg = parse_color(fg_color)
    bg = parse_color(bg_color, allow_transparent=True)

    page = Image.new("RGBA", (page_w, page_h), bg)
    draw = ImageDraw.Draw(page)

    title_font = _font(int(0.30 * dpi))
    header_font = _font(int(0.16 * dpi))
    sub_font = _font(int(0.11 * dpi))
    caption_font = _font(int(0.15 * dpi))

    # Sheet title
    _draw_centered(draw, page_w / 2, margin, sheet_title, title_font, fg)

    grid_top = margin + title_h
    for i, col in enumerate(columns):
        col_x = margin + i * (col_w + col_gap)
        cx = col_x + col_w / 2

        # Column header
        _draw_centered(draw, cx, grid_top, col["title"], header_font, fg)
        if col.get("subtitle"):
            _draw_centered(draw, cx, grid_top + int(0.22 * dpi), col["subtitle"], sub_font, (90, 90, 90, 255))

        # QR codes stacked, each with a readable clue-ID caption below
        y = grid_top + header_h
        for url, label in col["codes"]:
            img = qr_image(url, label, qr_size, fg, bg)
            qx = int(col_x + (col_w - qr_size) / 2)
            page.paste(img, (qx, int(y)), img)
            _draw_centered(draw, cx, y + qr_size + int(0.03 * dpi), label, caption_font, fg)
            y += qr_size + caption_h + qr_gap

    # Flatten to white-backed RGB and save PNG + PDF
    out_dir = ROOT / "to_print" / "qr_codes"
    out_dir.mkdir(parents=True, exist_ok=True)
    flat = Image.new("RGB", page.size, (255, 255, 255))
    flat.paste(page, mask=page.split()[3])

    png_path = out_dir / f"{output_stem}.png"
    pdf_path = out_dir / f"{output_stem}.pdf"
    flat.save(str(png_path), dpi=(dpi, dpi))
    flat.save(str(pdf_path), "PDF", resolution=float(dpi))
    print(f"  ✓ {png_path}")
    print(f"  ✓ {pdf_path}")


def load_track_columns():
    columns = []
    for fn in TRACK_FILES:
        data = yaml.safe_load((QUESTS_DIR / fn).read_text())
        codes = [(clue_url(c), str(c)) for c in data.get("clue_chain", [])]
        columns.append({
            "title": data["title"],
            "subtitle": data["aspect"].upper(),
            "codes": codes,
        })
    return columns


def load_gate_columns():
    gates = yaml.safe_load(GATES_FILE.read_text())
    columns = []
    for gate in gates.values():
        codes = [(clue_url(c), str(c)) for c in gate.get("clues", [])]
        columns.append({
            "title": gate["name"],
            "subtitle": None,
            "codes": codes,
        })
    return columns


def main():
    parser = argparse.ArgumentParser(description="Generate track + story-gate QR sheets")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--fg", default="#4a148c")
    parser.add_argument("--bg", default="white")
    args = parser.parse_args()

    print("Track key-clue sheet:")
    make_sheet(
        load_track_columns(),
        "track_key_clues",
        "Key Clue QR Codes by Track",
        args.dpi, args.fg, args.bg,
    )

    print("Story gates sheet:")
    make_sheet(
        load_gate_columns(),
        "story_gate_clues",
        "Story Gate QR Codes",
        args.dpi, args.fg, args.bg,
    )


if __name__ == "__main__":
    main()

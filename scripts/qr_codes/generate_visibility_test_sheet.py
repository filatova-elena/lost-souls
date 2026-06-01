#!/usr/bin/env python3
"""
Generate a QR test sheet for visibility-rule (skill-gated) testing.

Sections:
  1. Test QR
  2. Sign-in QR
  3. A few Act I botanical clues
  4. A few Act I writings
  5. A few Act I visions
  6. A few writings (any act)
  7. A few artifacts

Every clue picked has visibility rules (non-empty `skills`). For each clue the
sheet prints the required skills (OR logic) and the player characters who can
read it — computed the same way the app does (see src/lib/skills.js).

Output: to_print/qr_codes/visibility_test_sheet.pdf (+ first page PNG preview).

Usage:
    python generate_visibility_test_sheet.py
"""

import re
import sys
import tempfile
import os
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from qr_generator import generate_qr, parse_color

ROOT = Path(__file__).parent.parent.parent
CLUES_DIR = ROOT / "src/_data/clues"
CHARS_DIR = ROOT / "src/_data/characters"
SKILLS_FILE = ROOT / "src/_data/refs/skills.yaml"

BASE_URL = "https://lostsouls.door66.events"
FG = "#4a148c"

# Curated selection — (section, [clue_id, ...]). TEST/SIGN_IN have no YAML.
SECTIONS = [
    ("1. Test QR",                 ["TEST001"]),
    ("2. Sign-In QR",              ["SIGN_IN"]),
    ("3. Botanical — Act I",       ["BH108", "BG185", "BJ113"]),
    ("4. Writings — Act I",        ["WEI20", "WJF01"]),
    ("5. Visions — Act I",         ["VC151", "VC152", "VC153"]),
    ("6. Writings — later acts",   ["WTAS48", "WTPN74", "WF25a"]),
    ("7. Artifacts",               ["AO105", "AO78", "AO84", "APH89"]),
]

SPECIAL_LABELS = {"TEST001": "Test QR", "SIGN_IN": "Player Sign-In"}


# ── Skill-access logic (port of src/lib/skills.js) ───────────────────────────

def parse_skill(skill):
    m = re.match(r"^(.+?)(?:_(\d+))?$", skill or "")
    if not m:
        return None
    return {"base": m.group(1), "level": int(m.group(2)) if m.group(2) else 0}


def has_skill_access(required, user_skills):
    if not required:
        return True
    for req in required:
        rp = parse_skill(req)
        if not rp:
            continue
        for us in user_skills:
            up = parse_skill(us)
            if up and up["base"] == rp["base"] and up["level"] >= rp["level"]:
                return True
    return False


def characters_with_access(clue_skills, characters):
    out = []
    for ch in characters:
        if ch.get("is_player") is False or not ch.get("skills"):
            continue
        if has_skill_access(clue_skills, ch["skills"]):
            out.append((ch.get("title") or ch["id"]).replace("The ", "", 1))
    return out


# ── Data ─────────────────────────────────────────────────────────────────────

def load_clue_index():
    idx = {}
    for f in CLUES_DIR.rglob("*.yaml"):
        try:
            d = yaml.safe_load(f.read_text())
        except Exception:
            continue
        if d and d.get("id"):
            idx[str(d["id"])] = d
    return idx


def load_characters():
    chars = []
    for f in sorted(CHARS_DIR.glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        if d:
            chars.append(d)
    return chars


def skill_label(skill_id, skills_data):
    """Readable label for a required skill id."""
    if skill_id.startswith("is_character_"):
        who = skill_id.replace("is_character_", "")
        return f"only {who}"
    lvl_m = re.search(r"_(1|2)$", skill_id)
    level = lvl_m.group(1) if lvl_m else "1"
    base = re.sub(r"_(1|2)$", "", skill_id)
    info = skills_data.get(base)
    if info:
        icon = f"{info['icon']} " if info.get("icon") else ""
        lvl_txt = (info.get("level") or {}).get(level, info.get("title", base))
        return f"{icon}{lvl_txt}"
    return skill_id.replace("_", " ")


# ── Rendering ────────────────────────────────────────────────────────────────

DPI = 300
PAGE_W, PAGE_H = int(8.5 * DPI), int(11 * DPI)
MARGIN = int(0.4 * DPI)
QR_SIZE = int(0.72 * DPI)          # small QR for compact table rows
ROW_PAD = int(0.07 * DPI)          # vertical padding inside a row

# Table columns (x offset, width) in pixels, left to right
COL_QR_W = QR_SIZE
COL_ID_W = int(0.95 * DPI)
COL_SKILL_W = int(2.05 * DPI)
COL_GUTTER = int(0.12 * DPI)


def _font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def qr_image(clue_id):
    url = f"{BASE_URL}/clues/{clue_id}/"
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        generate_qr(url=url, output_path=tmp.name, size=QR_SIZE, label=clue_id,
                    fg_color=parse_color(FG), bg_color=(255, 255, 255, 255), rotate=False)
        return Image.open(tmp.name).convert("RGBA")
    finally:
        os.unlink(tmp.name)


def strip_emoji(text):
    """Drop symbol/emoji codepoints Arial can't render, collapse leftover spaces."""
    cleaned = "".join(c for c in text if ord(c) < 0x2190 or c == "·")
    return re.sub(r"\s+", " ", cleaned).strip()


def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_rows(clue_idx, characters, skills_data):
    """Return list of ('header', text) or ('row', dict) items."""
    items = []
    for header, ids in SECTIONS:
        items.append(("header", header))
        for cid in ids:
            clue = clue_idx.get(cid)
            if cid in SPECIAL_LABELS:
                items.append(("row", {
                    "id": cid, "title": SPECIAL_LABELS[cid],
                    "skills": None, "readers": None,
                }))
                continue
            if not clue:
                print(f"  ⚠️  {cid} not found, skipping")
                continue
            req = clue.get("skills") or []
            skill_txt = " · ".join(skill_label(s, skills_data) for s in req) or "(no restriction)"
            readers = characters_with_access(req, characters)
            items.append(("row", {
                "id": cid,
                "title": clue.get("title", ""),
                "type": clue.get("type", ""),
                "skills": skill_txt,
                "readers": ", ".join(readers) if readers else "— none —",
            }))
    return items


def render(items, out_pdf, out_png):
    title_font = _font(int(0.24 * DPI), bold=True)
    header_font = _font(int(0.13 * DPI), bold=True)
    colhdr_font = _font(int(0.095 * DPI), bold=True)
    id_font = _font(int(0.115 * DPI), bold=True)
    title_font2 = _font(int(0.085 * DPI))
    body_font = _font(int(0.10 * DPI))

    fg = (74, 20, 140)
    grey = (110, 110, 110)
    line_h = int(0.135 * DPI)

    # Column x positions
    x_qr = MARGIN
    x_id = x_qr + COL_QR_W + COL_GUTTER
    x_skill = x_id + COL_ID_W + COL_GUTTER
    x_readers = x_skill + COL_SKILL_W + COL_GUTTER
    w_skill = COL_SKILL_W
    w_readers = PAGE_W - MARGIN - x_readers

    pages = []
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)
    y = MARGIN
    draw.text((MARGIN, y), "QR Visibility Test Sheet — Who Can Read What", font=title_font, fill=fg)
    y += int(0.42 * DPI)

    def new_page():
        nonlocal page, draw, y
        pages.append(page)
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        draw = ImageDraw.Draw(page)
        y = MARGIN

    def column_headers():
        nonlocal y
        draw.text((x_id, y), "CLUE", font=colhdr_font, fill=grey)
        draw.text((x_skill, y), "REQUIRED SKILLS (any one)", font=colhdr_font, fill=grey)
        draw.text((x_readers, y), "WHO CAN READ", font=colhdr_font, fill=grey)
        y += int(0.16 * DPI)

    for kind, payload in items:
        if kind == "header":
            if y + int(0.5 * DPI) > PAGE_H - MARGIN:
                new_page()
            y += int(0.06 * DPI)
            draw.text((MARGIN, y), payload, font=header_font, fill=fg)
            y += int(0.22 * DPI)
            column_headers()
            continue

        d = payload
        # Wrap the variable-width columns
        skill_lines = wrap(draw, strip_emoji(d["skills"]), body_font, w_skill) if d["skills"] is not None else []
        reader_lines = wrap(draw, d["readers"], body_font, w_readers) if d["readers"] is not None else []
        id_block = 2  # ID line + title line
        text_h = max(id_block, len(skill_lines), len(reader_lines)) * line_h
        row_h = max(QR_SIZE, text_h) + 2 * ROW_PAD

        if y + row_h > PAGE_H - MARGIN:
            new_page()
            column_headers()

        row_top = y
        # QR (vertically centered)
        qr_y = row_top + (row_h - QR_SIZE) // 2
        page.paste(qr_image(d["id"]), (x_qr, qr_y))

        # ID + title column
        ty = row_top + ROW_PAD
        draw.text((x_id, ty), d["id"], font=id_font, fill=fg)
        if d.get("title"):
            for wl in wrap(draw, d["title"], title_font2, COL_ID_W)[:3]:
                ty += int(0.13 * DPI)
                draw.text((x_id, ty), wl, font=title_font2, fill=grey)

        # Skills column
        sy = row_top + ROW_PAD
        for wl in (skill_lines or ["(no restriction)"]):
            draw.text((x_skill, sy), wl, font=body_font, fill=(0, 0, 0))
            sy += line_h

        # Readers column
        ry = row_top + ROW_PAD
        for wl in (reader_lines or ["—"]):
            draw.text((x_readers, ry), wl, font=body_font, fill=(0, 0, 0))
            ry += line_h

        y += row_h
        draw.line([(MARGIN, y), (PAGE_W - MARGIN, y)], fill=(225, 225, 225), width=1)
        y += int(0.05 * DPI)

    pages.append(page)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(str(out_pdf), save_all=True, append_images=pages[1:], format="PDF", resolution=float(DPI))
    pages[0].save(str(out_png), dpi=(DPI, DPI))
    print(f"\n  ✓ {out_pdf}  ({len(pages)} page(s))")
    print(f"  ✓ {out_png}  (page 1 preview)")


def main():
    clue_idx = load_clue_index()
    characters = load_characters()
    skills_data = yaml.safe_load(SKILLS_FILE.read_text())

    items = build_rows(clue_idx, characters, skills_data)

    # Print the who-can-read summary to the terminal too
    print("Who can read each clue:")
    for kind, p in items:
        if kind == "header":
            print(f"\n{p}")
        elif p["skills"] is not None:
            print(f"  {p['id']:8} [{p['skills']}]")
            print(f"           → {p['readers']}")
        else:
            print(f"  {p['id']:8} ({p['title']})")

    out_dir = ROOT / "to_print" / "qr_codes"
    render(items, out_dir / "visibility_test_sheet.pdf", out_dir / "visibility_test_sheet.png")


if __name__ == "__main__":
    main()

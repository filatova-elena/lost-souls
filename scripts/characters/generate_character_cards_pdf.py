#!/usr/bin/env python3
"""
Generate a combined character-cards PDF for double-sided printing.

Renders every player character (from src/_data/characters/*.yaml) as a 3"×4"
card using the design in designs/character-card.html. Pages are 8.5×11 letter,
2×2 = 4 cards per page. The PDF alternates fronts and backs so it duplex-prints
cleanly; backs are column-mirrored for "flip on long edge" (the default for
most printers on portrait letter paper).

Usage:
    python scripts/characters/generate_character_cards_pdf.py
    python scripts/characters/generate_character_cards_pdf.py --output to_print/character_cards.pdf
    python scripts/characters/generate_character_cards_pdf.py --short-edge   # if your printer flips on short edge
"""

import argparse
import base64
import html as html_mod
import math
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import qrcode
import yaml

ROOT = Path(__file__).parent.parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SITE_URL = "https://lostsouls.door66.events"

ASPECT_COLORS = {
    "gossip":     "#a0365b",
    "paranormal": "#4a148c",
    "alchemical": "#2f6b4a",
    "adventure":  "#b8742c",
}

ASPECT_ICONS = {
    "adventure":  "item_bottle.svg",
    "paranormal": "item_crystal_ball.svg",
    "gossip":     "item_wedding_dress.svg",
    "alchemical": "item_ginseng_root.svg",
}


def load_aspect_icon(aspect):
    icon_file = ASPECT_ICONS.get(aspect)
    if not icon_file:
        return ""
    path = ROOT / "src/assets/icons" / icon_file
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def character_qr_data_uri(char_id):
    """Return a data: URI PNG for the character's page URL."""
    url = f"{SITE_URL}/characters/{char_id}/"
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#4a148c", back_color="#ffffff")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def load_yaml(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def md_to_html(s):
    if not s:
        return ""
    s = html_mod.escape(str(s).strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def load_refs():
    skills = load_yaml(ROOT / "src/_data/refs/skills.yaml") or {}
    tracks = {}
    for f in (ROOT / "src/_data/quests").rglob("*.yaml"):
        d = load_yaml(f)
        if d and d.get("type") == "track":
            tracks[d["id"]] = d
    clues = {}
    for f in (ROOT / "src/_data/clues").rglob("*.yaml"):
        try:
            d = load_yaml(f)
            if d and "id" in d:
                clues[d["id"]] = d.get("title", d["id"])
        except Exception:
            pass
    return skills, tracks, clues


def load_player_characters():
    chars = []
    for f in sorted((ROOT / "src/_data/characters").glob("*.yaml")):
        d = load_yaml(f)
        if not d:
            continue
        if not d.get("is_player", True) or d.get("is_special_character"):
            continue
        chars.append(d)
    return chars


def render_skill(sid, skills_ref):
    if str(sid).startswith("is_character"):
        return None
    base = re.sub(r"_\d+$", "", str(sid))
    s = skills_ref.get(base)
    if not s:
        return None
    icon = s.get("icon", "·")
    title = s.get("title", base)
    return f'<div class="skill"><span class="sk-icon">{icon}</span><span class="sk-name">{html_mod.escape(title)}</span></div>'


CARD_BG_SVG = """
<svg class="card-bg" viewBox="0 0 336 432" xmlns="http://www.w3.org/2000/svg">
  <rect width="336" height="432" fill="#f2ecda"/>
  <rect x="5" y="5" width="326" height="422" rx="2" fill="none" stroke="#4a148c" stroke-width="1.8"/>
  <rect x="9" y="9" width="318" height="414" rx="1" fill="none" stroke="#4a148c" stroke-width="0.5"/>
  <g opacity="0.6">
    <line x1="168" y1="5" x2="168" y2="12" stroke="#4a148c" stroke-width="0.5"/>
    <line x1="156" y1="5" x2="160" y2="12" stroke="#4a148c" stroke-width="0.4"/>
    <line x1="180" y1="5" x2="176" y2="12" stroke="#4a148c" stroke-width="0.4"/>
    <line x1="146" y1="5" x2="153" y2="11" stroke="#4a148c" stroke-width="0.3"/>
    <line x1="190" y1="5" x2="183" y2="11" stroke="#4a148c" stroke-width="0.3"/>
  </g>
  <g opacity="0.6">
    <line x1="168" y1="427" x2="168" y2="420" stroke="#4a148c" stroke-width="0.5"/>
    <line x1="156" y1="427" x2="160" y2="420" stroke="#4a148c" stroke-width="0.4"/>
    <line x1="180" y1="427" x2="176" y2="420" stroke="#4a148c" stroke-width="0.4"/>
    <line x1="146" y1="427" x2="153" y2="421" stroke="#4a148c" stroke-width="0.3"/>
    <line x1="190" y1="427" x2="183" y2="421" stroke="#4a148c" stroke-width="0.3"/>
  </g>
  <path d="M5 28 L5 5 L28 5" stroke="#4a148c" stroke-width="2.5" fill="none"/>
  <path d="M9 22 L9 9 L22 9" stroke="#4a148c" stroke-width="0.6" fill="none"/>
  <rect x="5" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
  <path d="M331 28 L331 5 L308 5" stroke="#4a148c" stroke-width="2.5" fill="none"/>
  <path d="M327 22 L327 9 L314 9" stroke="#4a148c" stroke-width="0.6" fill="none"/>
  <rect x="325" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
  <path d="M5 404 L5 427 L28 427" stroke="#4a148c" stroke-width="2.5" fill="none"/>
  <path d="M9 410 L9 423 L22 423" stroke="#4a148c" stroke-width="0.6" fill="none"/>
  <rect x="5" y="421" width="6" height="6" fill="#4a148c" opacity="0.12"/>
  <path d="M331 404 L331 427 L308 427" stroke="#4a148c" stroke-width="2.5" fill="none"/>
  <path d="M327 410 L327 423 L314 423" stroke="#4a148c" stroke-width="0.6" fill="none"/>
  <rect x="325" y="421" width="6" height="6" fill="#4a148c" opacity="0.12"/>
</svg>
"""


def render_front(c, tracks):
    aspect = (c.get("objectives", {}) or {}).get("aspect", "")
    track_class = f"track-{aspect}"
    track_name = aspect.capitalize() if aspect else ""
    img_path = c.get("image", "")
    img_src = f"file://{ROOT / 'src' / img_path}" if img_path else ""
    track_id = (c.get("objectives", {}) or {}).get("track")
    track = tracks.get(track_id, {})
    objective = md_to_html(track.get("objective", ""))
    short = md_to_html(c.get("personality_short", ""))
    title = html_mod.escape(c.get("title", ""))

    qr_uri = character_qr_data_uri(c["id"])
    icon_svg = load_aspect_icon(aspect)

    objective_block = (
        f'<hr class="section-hr">'
        f'<p class="para"><span class="inline-label">OBJECTIVE:</span>{objective}</p>'
        if objective.strip() else ""
    )

    return f"""
    <div class="card">
      {CARD_BG_SVG}
      <div class="card-content">
        <div class="title-area">
          <div class="char-name">{title}</div>
        </div>
        <div class="hero {track_class}">
          <div class="hero-image"><img src="{img_src}" alt=""></div>
          <div class="hero-fill"></div>
          <div class="qr-diamond"><img class="qr-code" src="{qr_uri}" alt=""></div>
          <div class="track-label">{html_mod.escape(track_name)}</div>
          <div class="item-icon">{icon_svg}</div>
        </div>
        <div class="body-area">
          <p class="para italic">{short}</p>
          {objective_block}
        </div>
      </div>
    </div>
    """


def render_back(c, skills_ref, clues):
    title = html_mod.escape(c.get("title", ""))
    skills_html = "".join(
        s for s in (render_skill(sid, skills_ref) for sid in (c.get("skills") or [])) if s
    )
    bio = md_to_html(c.get("background", ""))
    iq = (c.get("objectives", {}) or {}).get("initial_quest")
    iq_title = clues.get(iq, iq) if iq else ""
    return f"""
    <div class="card">
      {CARD_BG_SVG}
      <div class="card-content">
        <div class="back-title"><div class="char-name">{title}</div></div>
        <div class="back-body">
          <div class="section-label">
            <div class="line"></div><div class="lbl">SKILLS</div><div class="line"></div>
          </div>
          <div class="skills-row">{skills_html}</div>
          <hr class="section-hr">
          <p class="bio quest"><span class="inline-label">INITIAL QUEST:</span>Find the <em>{html_mod.escape(iq_title)}</em></p>
          <hr class="section-hr">
          <p class="bio"><span class="inline-label">YOUR STORY:</span>{bio}</p>
        </div>
      </div>
    </div>
    """


def compose_pages(chars, skills_ref, tracks, clues, short_edge_flip=False):
    """Pair up fronts and backs into 2×2 grids, alternating pages."""
    per_page = 4
    pages_html = []
    for i in range(0, len(chars), per_page):
        group = chars[i:i + per_page]
        # pad group to 4 with empty cards so grid stays consistent
        while len(group) < per_page:
            group.append(None)

        # Fronts: natural order (row-major)
        front_cards = [render_front(c, tracks) if c else '<div class="card"></div>' for c in group]

        # Backs: mirror for duplex
        back_cards_raw = [render_back(c, skills_ref, clues) if c else '<div class="card"></div>' for c in group]
        if short_edge_flip:
            # Top-bottom mirror: swap rows (row1 <-> row2)
            back_order = [2, 3, 0, 1]
        else:
            # Long-edge flip (default): left-right mirror within each row
            back_order = [1, 0, 3, 2]
        back_cards = [back_cards_raw[k] for k in back_order]

        pages_html.append(f'<div class="print-page">{"".join(front_cards)}</div>')
        pages_html.append(f'<div class="print-page back">{"".join(back_cards)}</div>')

    return "\n".join(pages_html)


_UNITS_IN_INCHES = {
    "in": 1.0, "mm": 1 / 25.4, "cm": 1 / 2.54, "pt": 1 / 72.0, "px": 1 / 96.0,
}


def parse_inches(s):
    """Parse a CSS length ('0.25in', '-6mm', '0') to inches (float)."""
    s = (s or "0").strip().lower()
    if s in ("0", ""):
        return 0.0
    m = re.fullmatch(r'([+-]?\d*\.?\d+)\s*(in|mm|cm|pt|px)?', s)
    if not m:
        raise ValueError(f"Can't parse CSS length: {s!r}")
    return float(m.group(1)) * _UNITS_IN_INCHES[m.group(2) or "in"]


def resolve_pdf_offsets(left_in, right_in, short_edge):
    """Map paper-space offsets (from front view of paper) to PDF back-page space.

    Long-edge flip (default): paper's left ↔ PDF-back's right (horizontal swap).
    Short-edge flip: paper's top ↔ PDF-back's bottom (vertical direction flips).
    """
    if short_edge:
        return -left_in, -right_in
    return right_in, left_in


def back_transform_css(pdf_left_in, pdf_right_in):
    """CSS rule for .print-page.back: translate by the average, rotate around center.

    With origin at 50% 50% and page width 8.5in, a rotation of θ moves the left
    edge up by 4.25·sinθ and the right edge down by the same amount. So to land
    at target offsets (L, R) on the two edges, we translate by (L+R)/2 and
    rotate by atan((R - L) / 8.5).
    """
    t = (pdf_left_in + pdf_right_in) / 2.0
    theta_deg = math.degrees(math.atan((pdf_right_in - pdf_left_in) / 8.5))
    if abs(t) < 1e-6 and abs(theta_deg) < 1e-6:
        return ""
    return (
        ".print-page.back { "
        f"transform: translateY({t:.4f}in) rotate({theta_deg:.4f}deg); "
        "transform-origin: 50% 50%; }"
    )


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400;0,400;0,700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
@page { size: letter; margin: 0; }
html, body { background: #fff; }
body { margin: 0; padding: 0; }

.print-page {
  width: 8.5in;
  height: 11in;
  page-break-after: always;
  break-after: page;
  display: grid;
  grid-template-columns: 3.5in 3.5in;
  grid-template-rows: 4.5in 4.5in;
  justify-content: center;
  align-content: center;
  gap: 0;
  position: relative;
}
.print-page:last-child { page-break-after: auto; break-after: auto; }

.card {
  width: 3.5in;
  height: 4.5in;
  position: relative;
  overflow: hidden;
}
.card-bg { position: absolute; inset: 0; z-index: 0; width: 100%; height: 100%; }
.card-content {
  position: absolute; inset: 0; z-index: 1;
  display: flex; flex-direction: column; align-items: center;
}

/* Track color vars */
.track-gossip     { --track-color: #a0365b; }
.track-paranormal { --track-color: #4a148c; }
.track-alchemical { --track-color: #2f6b4a; }
.track-adventure  { --track-color: #b8742c; }
.track-choose     { --track-color: #6a5c56; }

/* Title */
.title-area { padding: 10px 14px 0; text-align: center; width: 100%; }
.char-name {
  font-family: 'Playfair Display SC', serif;
  font-weight: 900;
  font-size: 28px;
  color: #4a148c;
  letter-spacing: 3px;
  line-height: 1;
}

/* Hero */
.hero {
  position: relative;
  width: calc(100% - 20px);
  height: 204px;
  margin: 6px 10px 0;
  overflow: visible;
  border: 1px solid #4a148c;
}
.hero-image, .hero-fill {
  position: absolute; top: 0; bottom: 0; width: 50%;
}
.hero-image { left: 0; overflow: hidden; }
.hero-image img {
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: 100% 25%;
}
.hero-fill { right: 0; background: var(--track-color); }

.qr-diamond {
  position: absolute; left: 50%; top: 50%;
  width: 144px; height: 144px;
  transform: translate(-50%, -50%) rotate(45deg);
  background: #fff;
  border: 1.5px solid #4a148c;
  z-index: 2;
}
.qr-code {
  position: absolute;
  inset: 4px;
  width: calc(100% - 8px);
  height: calc(100% - 8px);
  image-rendering: pixelated;  /* keep QR modules crisp */
}

.track-label {
  position: absolute; z-index: 3;
  left: calc(50% + 65px); top: calc(50% - 51px);
  transform: translate(-50%, -50%) rotate(45deg);
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #fff;
  white-space: nowrap;
}

.item-icon {
  position: absolute; z-index: 3;
  right: 12px; bottom: 10px;
  width: 36px; height: 36px;
  color: #fff;
}
.item-icon svg { width: 100%; height: 100%; display: block; }

/* Body */
.body-area {
  flex: 1; width: 100%;
  padding: 6px 18px 12px;
  display: flex; flex-direction: column; gap: 6px;
}

.section-label { display: flex; align-items: center; gap: 6px; }
.section-label .line { flex: 1; border-top: 0.6px solid rgba(74,20,140,0.4); }
.section-label .lbl {
  font-family: 'Playfair Display SC', serif;
  font-weight: 700; font-size: 12px; letter-spacing: 3px; color: #4a148c;
}

.inline-label {
  font-family: 'Crimson Text', serif;
  font-weight: 700; font-size: 12px;
  color: #4a148c; text-decoration: underline;
  letter-spacing: 0.5px; margin-right: 4px;
}

.section-hr {
  border: 0;
  border-top: 0.6px solid rgba(74,20,140,0.35);
  margin: 2px 0;
}

.para {
  font-family: 'Crimson Text', serif;
  font-size: 15px; line-height: 1.3;
  color: #2a1a0e; text-align: left;
}
.para.italic { font-style: italic; font-size: 17px; text-align: center; }
.para strong { color: #4a148c; font-weight: 600; }

/* Back */
.back-title { padding: 10px 16px 4px; text-align: center; width: 100%; }
.back-title .char-name { font-size: 22px; letter-spacing: 3px; }
.back-body {
  flex: 1; width: 100%;
  padding: 4px 18px 14px;
  display: flex; flex-direction: column; gap: 6px;
  overflow: hidden;
}
.skills-row {
  display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;
}
.skill { display: flex; align-items: center; gap: 4px; }
.skill .sk-icon { font-size: 15px; line-height: 1; }
.skill .sk-name {
  font-family: 'Crimson Text', serif;
  font-weight: 600; font-size: 12px;
  color: #2a1a0e; letter-spacing: 0.3px;
}
.bio {
  font-family: 'Crimson Text', serif;
  font-size: 11px; line-height: 1.28;
  color: #2a1a0e; text-align: justify; hyphens: auto;
}
.bio strong { color: #4a148c; font-weight: 600; }
.bio.quest { font-size: 15px; text-align: left; }
"""


def build_html(chars, skills_ref, tracks, clues, short_edge_flip=False,
               back_left_in=0.0, back_right_in=0.0):
    pages = compose_pages(chars, skills_ref, tracks, clues, short_edge_flip=short_edge_flip)
    back_css = back_transform_css(back_left_in, back_right_in)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Character Cards</title>
<style>{CSS}
{back_css}</style>
</head>
<body>
{pages}
</body>
</html>
"""


def html_to_pdf(html_path, pdf_path):
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--no-margins",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("Chrome print-to-pdf failed")


def main():
    parser = argparse.ArgumentParser(description="Generate character cards PDF for duplex printing.")
    parser.add_argument("--output", "-o", default=None,
                        help="Output PDF path (default: to_print/character_cards.pdf, or to_print/<id>_cards.pdf with --character)")
    parser.add_argument("--character", default=None,
                        help="Single character ID (e.g. 'townsperson'). Produces a sheet of 4 copies.")
    parser.add_argument("--short-edge", action="store_true",
                        help="Arrange backs for 'flip on short edge' duplex (default is long edge).")
    parser.add_argument("--back-offset", default="0in",
                        help="Uniform vertical shift for back pages, as seen on the printed paper "
                             "from the front. Positive = push back DOWN on paper. Overridden per-edge "
                             "by --back-offset-left / --back-offset-right. Accepts any CSS length "
                             "(e.g. '0.25in', '-6mm'). Default: 0in.")
    parser.add_argument("--back-offset-left", default=None,
                        help="Vertical shift at the LEFT edge of the paper (front view). "
                             "Differs from --back-offset-right → rotational correction.")
    parser.add_argument("--back-offset-right", default=None,
                        help="Vertical shift at the RIGHT edge of the paper (front view).")
    parser.add_argument("--keep-html", action="store_true",
                        help="Also keep the generated HTML alongside the PDF.")
    args = parser.parse_args()

    skills_ref, tracks, clues = load_refs()

    if args.character:
        path = ROOT / "src/_data/characters" / f"{args.character}.yaml"
        if not path.exists():
            print(f"No such character: {path}", file=sys.stderr)
            return 1
        one = load_yaml(path)
        chars = [one] * 4  # 4 copies on a single sheet
        if args.output is None:
            args.output = f"to_print/{args.character}_cards.pdf"
        print(f"Single-character sheet: {one.get('title','?')} ×4")
    else:
        chars = load_player_characters()
        if args.output is None:
            args.output = "to_print/character_cards.pdf"
        print(f"Characters: {len(chars)}  "
              f"({sum(1 for c in chars if (c.get('objectives',{}) or {}).get('aspect')=='alchemical')}"
              f" alch / {sum(1 for c in chars if (c.get('objectives',{}) or {}).get('aspect')=='paranormal')}"
              f" para / {sum(1 for c in chars if (c.get('objectives',{}) or {}).get('aspect')=='gossip')}"
              f" goss / {sum(1 for c in chars if (c.get('objectives',{}) or {}).get('aspect')=='adventure')} adv)")

    default_off = args.back_offset
    left_in = parse_inches(args.back_offset_left if args.back_offset_left is not None else default_off)
    right_in = parse_inches(args.back_offset_right if args.back_offset_right is not None else default_off)
    pdf_left, pdf_right = resolve_pdf_offsets(left_in, right_in, args.short_edge)

    html = build_html(chars, skills_ref, tracks, clues,
                      short_edge_flip=args.short_edge,
                      back_left_in=pdf_left, back_right_in=pdf_right)

    out_pdf = ROOT / args.output
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    html_path = out_pdf.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    print(f"Rendering PDF: {out_pdf}")
    html_to_pdf(html_path, out_pdf)

    if not args.keep_html:
        html_path.unlink(missing_ok=True)

    flip_kind = "short-edge" if args.short_edge else "long-edge"
    print(f"Saved: {out_pdf}")
    print(f"Pages: {2 * ((len(chars) + 3) // 4)} (alternating fronts/backs, duplex {flip_kind} flip)")


if __name__ == "__main__":
    main()

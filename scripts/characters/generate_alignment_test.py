#!/usr/bin/env python3
"""
Low-ink duplex alignment test sheet for character cards.

Prints a 2-page PDF (front + back) at the same 2×2 card geometry as
generate_character_cards_pdf.py, but each "card" is just a dashed outline,
a crosshair, and a full-height + full-width ruler with 1/16" ticks.

Workflow:
  1. python scripts/characters/generate_alignment_test.py
  2. Print to_print/alignment_test.pdf duplex (same flip mode you use for cards).
  3. Hold a page up to light. Where the FRONT and BACK rulers don't line up,
     count the tick offset — that's your printer's duplex shift.
  4. Re-run generate_character_cards_pdf.py with --back-offset <amount>.

Usage:
    python scripts/characters/generate_alignment_test.py
    python scripts/characters/generate_alignment_test.py --short-edge
    python scripts/characters/generate_alignment_test.py --back-offset 0.25in  # verify a fix
"""

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Card geometry matches generate_character_cards_pdf.py
CARD_W = 336   # 3.5in at 96dpi
CARD_H = 432   # 4.5in at 96dpi
PX_PER_16 = 6  # 1/16" at 96dpi


def _ticks(center, offset_range, axis):
    """Yield tick <line> elements on one axis.

    axis='v': vertical ruler (ticks are horizontal segments stacked vertically)
    axis='h': horizontal ruler (ticks are vertical segments side-by-side)
    """
    cx, cy = center
    for i in range(1, offset_range + 1):
        if i % 16 == 0:
            length, stroke = 18, 0.6
        elif i % 8 == 0:
            length, stroke = 13, 0.45
        elif i % 4 == 0:
            length, stroke = 9, 0.35
        elif i % 2 == 0:
            length, stroke = 5, 0.3
        else:
            length, stroke = 3, 0.25
        for sign in (-1, 1):
            pos = sign * i * PX_PER_16
            if axis == "v":
                y = cy + pos
                if y < 18 or y > CARD_H - 18:
                    continue
                yield f'<line x1="{cx - length}" y1="{y}" x2="{cx + length}" y2="{y}" stroke="#000" stroke-width="{stroke}"/>'
            else:
                x = cx + pos
                if x < 18 or x > CARD_W - 18:
                    continue
                yield f'<line x1="{x}" y1="{cy - length}" x2="{x}" y2="{cy + length}" stroke="#000" stroke-width="{stroke}"/>'


def test_card(label):
    cx, cy = CARD_W / 2, CARD_H / 2
    ticks = list(_ticks((cx, cy), 36, "v")) + list(_ticks((cx, cy), 28, "h"))
    return f'''
<svg class="test-card" viewBox="0 0 {CARD_W} {CARD_H}" xmlns="http://www.w3.org/2000/svg">
  <rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}"
        fill="none" stroke="#888" stroke-width="0.5" stroke-dasharray="4 3"/>
  <line x1="{cx}" y1="22" x2="{cx}" y2="{CARD_H - 22}" stroke="#000" stroke-width="0.35"/>
  <line x1="22" y1="{cy}" x2="{CARD_W - 22}" y2="{cy}" stroke="#000" stroke-width="0.35"/>
  {"".join(ticks)}
  <circle cx="{cx}" cy="{cy}" r="3" fill="none" stroke="#000" stroke-width="0.5"/>
  <text x="{cx}" y="18" text-anchor="middle" font-family="monospace"
        font-size="12" font-weight="bold" fill="#333">{label}</text>
</svg>
'''


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
@page { size: letter; margin: 0; }
html, body { background: #fff; }

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
}
.print-page:last-child { page-break-after: auto; break-after: auto; }

.test-card { width: 3.5in; height: 4.5in; display: block; }
"""


_UNITS_IN_INCHES = {
    "in": 1.0, "mm": 1 / 25.4, "cm": 1 / 2.54, "pt": 1 / 72.0, "px": 1 / 96.0,
}


def parse_inches(s):
    s = (s or "0").strip().lower()
    if s in ("0", ""):
        return 0.0
    m = re.fullmatch(r'([+-]?\d*\.?\d+)\s*(in|mm|cm|pt|px)?', s)
    if not m:
        raise ValueError(f"Can't parse CSS length: {s!r}")
    return float(m.group(1)) * _UNITS_IN_INCHES[m.group(2) or "in"]


def resolve_pdf_offsets(left_in, right_in, short_edge):
    if short_edge:
        return -left_in, -right_in
    return right_in, left_in


def back_transform_css(pdf_left_in, pdf_right_in):
    t = (pdf_left_in + pdf_right_in) / 2.0
    theta_deg = math.degrees(math.atan((pdf_right_in - pdf_left_in) / 8.5))
    if abs(t) < 1e-6 and abs(theta_deg) < 1e-6:
        return ""
    return (
        ".print-page.back { "
        f"transform: translateY({t:.4f}in) rotate({theta_deg:.4f}deg); "
        "transform-origin: 50% 50%; }"
    )


def build_html(short_edge_flip=False, back_left_in=0.0, back_right_in=0.0):
    fronts = [test_card("FRONT") for _ in range(4)]
    backs = [test_card("BACK") for _ in range(4)]
    if short_edge_flip:
        back_order = [2, 3, 0, 1]
    else:
        back_order = [1, 0, 3, 2]
    backs = [backs[k] for k in back_order]

    back_css = back_transform_css(back_left_in, back_right_in)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Alignment Test</title>
<style>{CSS}
{back_css}</style></head>
<body>
<div class="print-page">{"".join(fronts)}</div>
<div class="print-page back">{"".join(backs)}</div>
</body></html>
"""


def html_to_pdf(html_path, pdf_path):
    cmd = [
        CHROME, "--headless", "--disable-gpu",
        "--no-pdf-header-footer", "--no-margins",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError("Chrome print-to-pdf failed")


def main():
    p = argparse.ArgumentParser(description="Low-ink duplex alignment test sheet.")
    p.add_argument("--output", "-o", default="to_print/alignment_test.pdf")
    p.add_argument("--short-edge", action="store_true",
                   help="Match 'flip on short edge' duplex mode (default is long edge).")
    p.add_argument("--back-offset", default="0in",
                   help="Uniform trial offset (default for both edges). Paper-space (front view).")
    p.add_argument("--back-offset-left", default=None,
                   help="Trial offset at LEFT edge of paper (front view).")
    p.add_argument("--back-offset-right", default=None,
                   help="Trial offset at RIGHT edge of paper (front view).")
    p.add_argument("--keep-html", action="store_true")
    args = p.parse_args()

    default_off = args.back_offset
    left_in = parse_inches(args.back_offset_left if args.back_offset_left is not None else default_off)
    right_in = parse_inches(args.back_offset_right if args.back_offset_right is not None else default_off)
    pdf_left, pdf_right = resolve_pdf_offsets(left_in, right_in, args.short_edge)

    html = build_html(short_edge_flip=args.short_edge,
                      back_left_in=pdf_left, back_right_in=pdf_right)
    out_pdf = ROOT / args.output
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    html_path = out_pdf.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    print(f"Rendering: {out_pdf}")
    html_to_pdf(html_path, out_pdf)

    if not args.keep_html:
        html_path.unlink(missing_ok=True)

    flip = "short-edge" if args.short_edge else "long-edge"
    print(f"Saved: {out_pdf}")
    print(f"Print duplex ({flip} flip), hold to light, read offset in 1/16\" ticks.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Marketing poster for the Lost Souls Murder Mystery.

Outputs two files:
  to_print/marketing_poster.pdf   8.5x11 portrait, printable
  to_print/marketing_poster.png   1080x1080 square for sharing

Usage:
    python scripts/marketing/generate_poster.py
    python scripts/marketing/generate_poster.py --keep-html
"""

import argparse
import base64
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERO_IMAGE = ROOT / "src/assets/images/bembridge/Bembridge_House_Old.png"

EVENT = {
    "title": "The Lost Souls",
    "subtitle": "Murder Mystery",
    "tagline": "A 1920s Investigation",
    "date_line": "Thursday · July 16",
    "time_line": "7:00 – 8:30 PM",
    "venue": "The Bembridge House",
    "dress": "1920s attire encouraged",
    "blurb": (
        "The Montrose mansion sat empty for decades. "
        "Doors open by themselves. Footsteps echo in empty halls. "
        "A psychic medium says the spirits trapped here remember "
        "<em>something terrible</em> from a century ago."
        "<br/><br/>"
        "Tonight, the investigation begins."
    ),
}


def _encode_image(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


# Shared art-deco styling. The two layouts (portrait / square) share fonts and
# colors but use different page geometry.
SHARED_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Cinzel+Decorative:wght@700;900&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: #0d0a08; }

.poster {
  position: relative;
  background:
    radial-gradient(ellipse at 50% 30%, rgba(150, 110, 60, 0.18) 0%, transparent 60%),
    radial-gradient(ellipse at 50% 90%, rgba(10, 6, 4, 0.9) 0%, transparent 70%),
    linear-gradient(180deg, #1a120b 0%, #0a0604 100%);
  color: #e8dcc0;
  overflow: hidden;
  font-family: 'Cormorant Garamond', 'Times New Roman', serif;
}

/* Subtle grain over everything */
.poster::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    repeating-linear-gradient(0deg, rgba(255, 220, 160, 0.025) 0px, rgba(255, 220, 160, 0.025) 1px, transparent 1px, transparent 3px);
  mix-blend-mode: overlay;
  opacity: 0.4;
}

/* Art-deco gold accents */
.gold { color: #d4af6a; }
.cream { color: #f3e7c8; }

.hero {
  position: relative;
  overflow: hidden;
}
.hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: sepia(0.35) contrast(1.05) brightness(0.85);
}
.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(10, 6, 4, 0.15) 0%, rgba(10, 6, 4, 0.45) 70%, #0a0604 100%);
}

.eyebrow {
  font-family: 'Cinzel', serif;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: #d4af6a;
  font-weight: 600;
}

.title {
  font-family: 'Cinzel Decorative', 'Cinzel', serif;
  font-weight: 900;
  color: #f3e7c8;
  letter-spacing: 0.04em;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  line-height: 0.95;
}

.subtitle {
  font-family: 'Cinzel Decorative', 'Cinzel', serif;
  font-weight: 700;
  color: #d4af6a;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.tagline {
  font-style: italic;
  color: #c9b58a;
}

.blurb {
  color: #e8dcc0;
  text-align: center;
}

.details {
  text-align: center;
}
.details .date {
  font-family: 'Cinzel', serif;
  font-weight: 600;
  color: #f3e7c8;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
.details .time {
  font-family: 'Cinzel', serif;
  color: #d4af6a;
  letter-spacing: 0.2em;
}
.details .venue {
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  color: #e8dcc0;
}
.details .dress {
  font-family: 'Cinzel', serif;
  color: #c9b58a;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

/* Art-deco divider: two thin gold rules around a small diamond */
.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6em;
  color: #d4af6a;
}
.divider .rule {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #d4af6a, transparent);
}
.divider .diamond {
  width: 0.5em;
  height: 0.5em;
  background: #d4af6a;
  transform: rotate(45deg);
}

/* Decorative corner sunbursts (very faint) */
.sunburst {
  position: absolute;
  width: 40%;
  aspect-ratio: 1;
  opacity: 0.18;
  pointer-events: none;
}
.sunburst.tl { top: -10%; left: -10%; }
.sunburst.br { bottom: -10%; right: -10%; transform: rotate(180deg); }
"""


def sunburst_svg():
    """A faint art-deco sunburst used for corner decoration."""
    rays = []
    for i in range(24):
        angle = i * (360 / 24)
        rays.append(
            f'<line x1="50" y1="50" x2="50" y2="0" stroke="#d4af6a" '
            f'stroke-width="0.5" transform="rotate({angle} 50 50)"/>'
        )
    return (
        '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(rays)}'
        '<circle cx="50" cy="50" r="3" fill="none" stroke="#d4af6a" stroke-width="0.6"/>'
        "</svg>"
    )


PORTRAIT_CSS = """
@page { size: 8.5in 11in; margin: 0; }

.poster.portrait {
  width: 8.5in;
  height: 11in;
  padding: 0.55in 0.7in 0.6in;
  display: grid;
  grid-template-rows: auto auto 4.2in auto auto auto;
  row-gap: 0.18in;
}

.portrait .frame {
  position: absolute;
  inset: 0.32in;
  border: 1px solid #6b5230;
  pointer-events: none;
}
.portrait .frame::before,
.portrait .frame::after {
  content: "";
  position: absolute;
  left: 0.06in;
  right: 0.06in;
  height: 1px;
  background: #6b5230;
}
.portrait .frame::before { top: 0.06in; }
.portrait .frame::after  { bottom: 0.06in; }

.portrait .eyebrow { font-size: 11pt; text-align: center; }
.portrait .title { font-size: 60pt; text-align: center; }
.portrait .subtitle { font-size: 38pt; text-align: center; margin-top: 0.08in; }
.portrait .tagline { font-size: 14pt; text-align: center; margin-top: 0.1in; }

.portrait .hero {
  height: 4.2in;
  margin: 0 0.05in;
  border: 1px solid #6b5230;
  box-shadow: 0 0 0 4px #0a0604, 0 0 0 5px #6b5230;
}

.portrait .blurb { font-size: 13pt; line-height: 1.45; padding: 0 0.2in; }

.portrait .details .date { font-size: 18pt; }
.portrait .details .time { font-size: 14pt; margin-top: 0.05in; }
.portrait .details .venue {
  font-family: 'Cinzel Decorative', 'Cinzel', serif;
  font-weight: 700;
  font-style: normal;
  font-size: 28pt;
  letter-spacing: 0.06em;
  color: #f3e7c8;
  margin-top: 0.14in;
}
.portrait .details .dress { font-size: 10pt; margin-top: 0.1in; }

.portrait .divider { font-size: 10pt; margin: 0.04in 0; }
"""


SQUARE_CSS = """
@page { size: 1080px 1080px; margin: 0; }

.poster.square {
  width: 1080px;
  height: 1080px;
  padding: 60px 70px;
  display: grid;
  grid-template-columns: 1fr 1.05fr;
  column-gap: 50px;
  align-items: stretch;
}

.square .left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.square .right {
  display: flex;
  align-items: center;
}

.square .hero {
  width: 100%;
  height: 100%;
  border: 1px solid #6b5230;
  box-shadow: 0 0 0 6px #0a0604, 0 0 0 7px #6b5230;
}

.square .eyebrow { font-size: 14px; margin-bottom: 18px; }
.square .title { font-size: 72px; text-align: center; }
.square .subtitle { font-size: 44px; text-align: center; margin-top: 10px; }
.square .tagline { font-size: 18px; text-align: center; margin-top: 16px; padding: 0 10px; }
.square .divider { font-size: 12px; margin: 22px 0; width: 80%; }

.square .details .date { font-size: 24px; }
.square .details .time { font-size: 18px; margin-top: 6px; }
.square .details .venue {
  font-family: 'Cinzel Decorative', 'Cinzel', serif;
  font-weight: 700;
  font-style: normal;
  font-size: 32px;
  letter-spacing: 0.06em;
  color: #f3e7c8;
  margin-top: 18px;
}
.square .details .dress { font-size: 13px; margin-top: 14px; }
"""


def render_portrait(hero_data_uri: str, sunburst: str) -> str:
    e = EVENT
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Lost Souls — Poster</title>
<style>{SHARED_CSS}{PORTRAIT_CSS}</style></head>
<body>
<div class="poster portrait">
  <div class="sunburst tl">{sunburst}</div>
  <div class="sunburst br">{sunburst}</div>
  <div class="frame"></div>

  <div>
    <div class="eyebrow">You are cordially invited</div>
    <div class="title">{e["title"]}</div>
    <div class="subtitle">{e["subtitle"]}</div>
    <div class="tagline">{e["tagline"]}</div>
  </div>

  <div class="divider"><span class="rule"></span><span class="diamond"></span><span class="rule"></span></div>

  <div class="hero"><img src="{hero_data_uri}" alt=""/></div>

  <div class="blurb">{e["blurb"]}</div>

  <div class="divider"><span class="rule"></span><span class="diamond"></span><span class="rule"></span></div>

  <div class="details">
    <div class="date">{e["date_line"]}</div>
    <div class="time">{e["time_line"]}</div>
    <div class="venue">{e["venue"]}</div>
    <div class="dress">— {e["dress"]} —</div>
  </div>
</div>
</body></html>
"""


def render_square(hero_data_uri: str, sunburst: str) -> str:
    e = EVENT
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Lost Souls — Square</title>
<style>{SHARED_CSS}{SQUARE_CSS}</style></head>
<body>
<div class="poster square">
  <div class="sunburst tl">{sunburst}</div>
  <div class="sunburst br">{sunburst}</div>

  <div class="left">
    <div class="eyebrow">You are invited</div>
    <div class="title">{e["title"]}</div>
    <div class="subtitle">{e["subtitle"]}</div>
    <div class="tagline">{e["tagline"]}</div>

    <div class="divider"><span class="rule"></span><span class="diamond"></span><span class="rule"></span></div>

    <div class="details">
      <div class="date">{e["date_line"]}</div>
      <div class="time">{e["time_line"]}</div>
      <div class="venue">{e["venue"]}</div>
      <div class="dress">— {e["dress"]} —</div>
    </div>
  </div>

  <div class="right">
    <div class="hero"><img src="{hero_data_uri}" alt=""/></div>
  </div>
</div>
</body></html>
"""


def html_to_pdf(html_path: Path, pdf_path: Path):
    cmd = [
        CHROME, "--headless", "--disable-gpu",
        "--no-pdf-header-footer", "--no-margins",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError("Chrome print-to-pdf failed")


def html_to_png(html_path: Path, png_path: Path, size: int = 1080):
    cmd = [
        CHROME, "--headless", "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={size},{size}",
        "--default-background-color=00000000",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--screenshot={png_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError("Chrome screenshot failed")


def main():
    p = argparse.ArgumentParser(description="Marketing poster generator.")
    p.add_argument("--pdf-out", default="to_print/marketing_poster.pdf")
    p.add_argument("--png-out", default="to_print/marketing_poster.png")
    p.add_argument("--keep-html", action="store_true")
    args = p.parse_args()

    if not HERO_IMAGE.exists():
        sys.exit(f"Missing hero image: {HERO_IMAGE}")

    hero = _encode_image(HERO_IMAGE)
    sb = sunburst_svg()

    pdf_out = ROOT / args.pdf_out
    png_out = ROOT / args.png_out
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    png_out.parent.mkdir(parents=True, exist_ok=True)

    portrait_html = pdf_out.with_name(pdf_out.stem + "_portrait.html")
    square_html = png_out.with_name(png_out.stem + "_square.html")

    portrait_html.write_text(render_portrait(hero, sb), encoding="utf-8")
    square_html.write_text(render_square(hero, sb), encoding="utf-8")

    print(f"Rendering PDF: {pdf_out}")
    html_to_pdf(portrait_html, pdf_out)
    print(f"Rendering PNG: {png_out}")
    html_to_png(square_html, png_out, size=1080)

    if not args.keep_html:
        portrait_html.unlink(missing_ok=True)
        square_html.unlink(missing_ok=True)

    print(f"Saved: {pdf_out}")
    print(f"Saved: {png_out}")


if __name__ == "__main__":
    main()

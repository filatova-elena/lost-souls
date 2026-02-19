#!/usr/bin/env python3
"""
Character Card Generator
========================
Generates a 3×4 inch character card image from a YAML definition file.
Includes character photo and stylized QR code.

Usage:
    python generate_card.py <yaml_file> [--output <output_path>] [--scale <factor>] [--base-url <url>]

Examples:
    python generate_card.py src/_data/characters/doctor.yaml
    python generate_card.py src/_data/characters/doctor.yaml --output card.png --scale 3
    python generate_card.py src/_data/characters/doctor.yaml --base-url https://example.com
"""

import argparse
import base64
import html
import os
import re
import sys
import tempfile
import textwrap
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

# Import QR code generator
sys.path.insert(0, str(Path(__file__).parent / "qr_codes"))
from qr_generator import generate_qr


# ── Skill display mappings ──────────────────────────────────────────────────
# Maps skill id prefixes to readable labels and icon glyphs
SKILL_MAP = {
    "art":       {"label": "Art",        "icon": "✦"},
    "personal":  {"label": "Personal",   "icon": "⚜"},
    "history":   {"label": "History",    "icon": "◈"},
    "spiritual": {"label": "Spiritual",  "icon": "☽"},
    "science":   {"label": "Science",    "icon": "⚗"},
    "medical":   {"label": "Medical",    "icon": "✚"},
    "nature":    {"label": "Nature",     "icon": "❧"},
    "explore":   {"label": "Explore",    "icon": "✧"},
    "social":    {"label": "Social",     "icon": "♔"},
    "trade":     {"label": "Trade",      "icon": "⚖"},
    "craft":     {"label": "Craft",      "icon": "⚒"},
    "music":     {"label": "Music",      "icon": "♪"},
    "combat":    {"label": "Combat",     "icon": "⚔"},
    "stealth":   {"label": "Stealth",    "icon": "◆"},
    "magic":     {"label": "Magic",      "icon": "★"},
    "legal":     {"label": "Legal",      "icon": "⚖"},
}


def parse_skill(skill_id: str) -> dict:
    """Parse a skill ID like 'art_2' into display info."""
    parts = skill_id.split("_")
    prefix = parts[0].lower()
    info = SKILL_MAP.get(prefix, {"label": prefix.title(), "icon": "◇"})
    return {
        "id": skill_id,
        "label": info["label"],
        "icon": info["icon"],
    }


def markdown_bold_to_html(text: str) -> str:
    """Convert **bold** markdown to <strong> tags, and escape HTML."""
    # First escape HTML entities (but preserve ** markers)
    # We'll do a two-pass: split on **, escape segments, re-wrap
    segments = text.split("**")
    result = []
    for i, seg in enumerate(segments):
        escaped = html.escape(seg)
        if i % 2 == 1:  # odd segments are bold
            result.append(f"<strong>{escaped}</strong>")
        else:
            result.append(escaped)
    return "".join(result)


def image_to_data_uri(image_path: str) -> str:
    """Convert an image file to a base64 data URI."""
    path = Path(image_path)
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}
    mime = mime_map.get(suffix, "image/png")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def extract_tagline(background: str) -> str:
    """Extract a short tagline from the background text (first sentence, shortened)."""
    # Try to grab first sentence
    first = background.split(".")[0].strip()
    # Remove markdown bold
    first = re.sub(r"\*\*(.+?)\*\*", r"\1", first)
    # Truncate if needed
    if len(first) > 60:
        first = first[:57].rsplit(" ", 1)[0] + "…"
    return first


def build_skill_icon_html(skill: dict) -> str:
    return f'''<div class="skill-icon">
          <svg class="icon-shape" viewBox="0 0 26 26"><polygon points="13,0 26,13 13,26 0,13" fill="none" stroke="#4a148c" stroke-width="0.8" opacity="0.3"/></svg>
          <span class="icon-label">{skill["icon"]}</span>
        </div>'''


def build_skills_text_html(skills: list) -> str:
    parts = []
    for i, s in enumerate(skills):
        if i > 0:
            parts.append('<span class="sep">◆</span>')
        parts.append(f'<span>{html.escape(s["label"])}</span>')
    return "".join(parts)


def generate_qr_code_data_uri(character_id: str, base_url: str, yaml_dir: str) -> str:
    """Generate a stylized QR code and return it as a data URI."""
    # Construct character URL
    character_url = f"{base_url.rstrip('/')}/characters/{character_id}/"
    
    # Create temporary file for QR code
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Generate QR code (96px size for card, rotated 45°, white background)
        generate_qr(
            url=character_url,
            output_path=tmp_path,
            size=96,
            label=None,
            corner_radius=0.35,
            overlay="keyhole",
            overlay_ratio=0.32,
            fg_color=(74, 20, 140, 255),  # #4a148c
            bg_color=(255, 255, 255, 255),  # white
            margin=0.01,
            rotate=True,  # 45° rotation for diamond placement
        )
        
        # Convert to data URI
        qr_uri = image_to_data_uri(tmp_path)
        if not qr_uri:
            print(f"Warning: Failed to generate QR code for {character_id}", file=sys.stderr)
        return qr_uri
    except Exception as e:
        print(f"Warning: Error generating QR code: {e}", file=sys.stderr)
        return ""
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def generate_html(data: dict, yaml_dir: str, base_url: str) -> str:
    """Generate the complete HTML for the character card."""

    title = data.get("title", "Unknown Character")
    character_id = data.get("id", "character")
    background = data.get("background", "")
    personality = data.get("personality", "")
    image_rel = data.get("image", "")
    raw_skills = data.get("skills", [])

    # Resolve image path relative to YAML file location
    image_uri = ""
    if image_rel:
        image_path = os.path.join(yaml_dir, image_rel)
        if os.path.exists(image_path):
            image_uri = image_to_data_uri(image_path)

    # Generate QR code
    qr_uri = generate_qr_code_data_uri(character_id, base_url, yaml_dir)

    # Parse skills (filter out 'is_character_*' meta skills)
    skills = [parse_skill(s) for s in raw_skills if not s.startswith("is_character")]

    # Pad to 4 skill icons for layout (left 2, right 2)
    while len(skills) < 4:
        skills.append({"id": "", "label": "", "icon": "◇"})

    left_skills = skills[:2]
    right_skills = skills[2:4]

    # Display skills for text ribbon (non-empty only)
    display_skills = [s for s in skills if s["label"]]

    # Tagline from personality or background
    tagline = personality if personality else extract_tagline(background)
    if len(tagline) > 80:
        tagline = tagline[:77].rsplit(" ", 1)[0] + "…"

    # Background text → HTML
    bg_html = markdown_bold_to_html(background)

    # Portrait HTML
    if image_uri:
        portrait_inner = f'<img src="{image_uri}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    else:
        portrait_inner = '<span class="ph">Character<br/>Portrait</span>'

    # Build skill icons
    left_icons = "\n        ".join(build_skill_icon_html(s) for s in left_skills)
    right_icons = "\n        ".join(build_skill_icon_html(s) for s in right_skills)
    skills_text = build_skills_text_html(display_skills) if display_skills else ""

    # QR code HTML
    if qr_uri:
        qr_inner = f'<img src="{qr_uri}" style="width:100%;height:100%;object-fit:contain;" />'
    else:
        qr_inner = '<span>QR Code</span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Character Card — {html.escape(title)}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: #444;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 30px;
    }}

    .card {{
      width: 3in;
      height: 4in;
      position: relative;
      overflow: hidden;
    }}

    .card-bg {{
      position: absolute;
      inset: 0;
      z-index: 0;
    }}

    .card-content {{
      position: absolute;
      inset: 0;
      z-index: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}

    /* ═══ TITLE ═══ */
    .title-area {{
      padding: 14px 20px 0;
      text-align: center;
      width: 100%;
    }}
    .char-name {{
      font-family: 'Playfair Display SC', serif;
      font-weight: 900;
      font-size: 18px;
      color: #4a148c;
      letter-spacing: 5px;
      line-height: 1;
    }}
    .char-tagline {{
      font-family: 'Playfair Display', serif;
      font-style: italic;
      font-size: 7.5px;
      color: #6a4a8a;
      margin-top: 2px;
      line-height: 1.2;
    }}

    /* ═══ PORTRAIT FRAME ═══ */
    .portrait-area {{
      position: relative;
      width: 180px;
      height: 105px;
      margin-top: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .portrait-img {{
      width: 82px;
      height: 82px;
      border-radius: 50%;
      background: #e4dcc8;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }}
    .portrait-img .ph {{
      font-family: 'Crimson Text', serif;
      font-size: 6px;
      color: #a0967e;
      text-transform: uppercase;
      letter-spacing: 1px;
      text-align: center;
    }}

    /* Skill icons flanking portrait */
    .skill-left, .skill-right {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 2;
    }}
    .skill-left {{ left: 0; align-items: center; }}
    .skill-right {{ right: 0; align-items: center; }}

    .skill-icon {{
      width: 26px;
      height: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }}
    .skill-icon .icon-shape {{ position: absolute; inset: 0; }}
    .skill-icon .icon-label {{
      font-family: 'Crimson Text', serif;
      font-size: 8px;
      color: #4a148c;
      z-index: 1;
      line-height: 1;
    }}

    /* ═══ QR — large diamond ═══ */
    .qr-area {{
      margin-top: -30px;
      z-index: 2;
      position: relative;
    }}
    .qr-outer {{
      width: 96px;
      height: 96px;
      transform: rotate(45deg);
      border: 1.5px solid #4a148c;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }}
    .qr-outer::before {{
      content: '';
      position: absolute;
      inset: 3px;
      border: 0.5px solid rgba(74,20,140,0.2);
    }}
    .qr-outer img {{
      transform: rotate(-45deg);
      width: 100%;
      height: 100%;
    }}
    .qr-outer span {{
      transform: rotate(-45deg);
      font-family: 'Crimson Text', serif;
      font-size: 7px;
      color: #b0a8c0;
      letter-spacing: 1px;
      text-transform: uppercase;
    }}

    /* ═══ TEXT AREA ═══ */
    .text-area {{
      flex: 1;
      width: 100%;
      padding: 2px 16px 12px;
      overflow: hidden;
      margin-top: 8px;
    }}

    .text-rule {{
      display: flex;
      align-items: center;
      gap: 5px;
      margin-bottom: 2px;
    }}
    .text-rule .line {{ flex: 1; border-top: 0.6px solid #4a148c; }}
    .text-rule .dia {{ width: 3px; height: 3px; background: #4a148c; transform: rotate(45deg); }}

    .skills-text {{
      text-align: center;
      margin-bottom: 2px;
    }}
    .skills-text span {{
      font-family: 'Playfair Display SC', serif;
      font-size: 5px;
      letter-spacing: 1.5px;
      color: #4a148c;
    }}
    .skills-text .sep {{ opacity: 0.3; margin: 0 3px; }}

    .story p {{
      font-family: 'Crimson Text', serif;
      font-size: 6.2px;
      line-height: 1.34;
      color: #2a1a0e;
      text-align: justify;
      hyphens: auto;
    }}
    .story strong {{ font-weight: 600; color: #4a148c; }}

    @media print {{
      body {{ background: none; padding: 0; margin: 0; }}
      @page {{ size: 3in 4in; margin: 0; }}
    }}
  </style>
</head>
<body>

<div class="card">

  <svg class="card-bg" viewBox="0 0 288 384" xmlns="http://www.w3.org/2000/svg">
    <rect width="288" height="384" fill="#f2ecda"/>

    <!-- Borders -->
    <rect x="5" y="5" width="278" height="374" rx="2" fill="none" stroke="#4a148c" stroke-width="1.8"/>
    <rect x="9" y="9" width="270" height="366" rx="1" fill="none" stroke="#4a148c" stroke-width="0.5"/>

    <!-- Top deco fan -->
    <g opacity="0.6">
      <line x1="144" y1="5" x2="144" y2="12" stroke="#4a148c" stroke-width="0.5"/>
      <line x1="132" y1="5" x2="136" y2="12" stroke="#4a148c" stroke-width="0.4"/>
      <line x1="156" y1="5" x2="152" y2="12" stroke="#4a148c" stroke-width="0.4"/>
      <line x1="122" y1="5" x2="129" y2="11" stroke="#4a148c" stroke-width="0.3"/>
      <line x1="166" y1="5" x2="159" y2="11" stroke="#4a148c" stroke-width="0.3"/>
    </g>

    <!-- Bottom deco fan -->
    <g opacity="0.6">
      <line x1="144" y1="379" x2="144" y2="372" stroke="#4a148c" stroke-width="0.5"/>
      <line x1="132" y1="379" x2="136" y2="372" stroke="#4a148c" stroke-width="0.4"/>
      <line x1="156" y1="379" x2="152" y2="372" stroke="#4a148c" stroke-width="0.4"/>
      <line x1="122" y1="379" x2="129" y2="373" stroke="#4a148c" stroke-width="0.3"/>
      <line x1="166" y1="379" x2="159" y2="373" stroke="#4a148c" stroke-width="0.3"/>
    </g>

    <!-- Corners -->
    <path d="M5 28 L5 5 L28 5" stroke="#4a148c" stroke-width="2.5" fill="none"/>
    <path d="M9 22 L9 9 L22 9" stroke="#4a148c" stroke-width="0.6" fill="none"/>
    <rect x="5" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>

    <path d="M283 28 L283 5 L260 5" stroke="#4a148c" stroke-width="2.5" fill="none"/>
    <path d="M279 22 L279 9 L266 9" stroke="#4a148c" stroke-width="0.6" fill="none"/>
    <rect x="277" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>

    <path d="M5 356 L5 379 L28 379" stroke="#4a148c" stroke-width="2.5" fill="none"/>
    <path d="M9 362 L9 375 L22 375" stroke="#4a148c" stroke-width="0.6" fill="none"/>
    <rect x="5" y="373" width="6" height="6" fill="#4a148c" opacity="0.12"/>

    <path d="M283 356 L283 379 L260 379" stroke="#4a148c" stroke-width="2.5" fill="none"/>
    <path d="M279 362 L279 375 L266 375" stroke="#4a148c" stroke-width="0.6" fill="none"/>
    <rect x="277" y="373" width="6" height="6" fill="#4a148c" opacity="0.12"/>

    <!-- Portrait circle frame -->
    <circle cx="144" cy="138" r="47" fill="none" stroke="#4a148c" stroke-width="1.2"/>
    <circle cx="144" cy="138" r="51" fill="none" stroke="#4a148c" stroke-width="0.4" stroke-dasharray="2 3"/>

    <!-- Rays behind portrait -->
    <g opacity="0.07" stroke="#4a148c" stroke-width="0.5">
      <line x1="144" y1="82" x2="144" y2="66"/>
      <line x1="174" y1="92" x2="186" y2="80"/>
      <line x1="196" y1="118" x2="212" y2="112"/>
      <line x1="196" y1="158" x2="212" y2="164"/>
      <line x1="174" y1="184" x2="186" y2="196"/>
      <line x1="114" y1="92" x2="102" y2="80"/>
      <line x1="92" y1="118" x2="76" y2="112"/>
      <line x1="92" y1="158" x2="76" y2="164"/>
      <line x1="114" y1="184" x2="102" y2="196"/>
    </g>

    <!-- Side accents -->
    <line x1="16" y1="116" x2="16" y2="160" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/>
    <line x1="19" y1="122" x2="19" y2="154" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
    <line x1="272" y1="116" x2="272" y2="160" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/>
    <line x1="269" y1="122" x2="269" y2="154" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
  </svg>

  <div class="card-content">

    <div class="title-area">
      <div class="char-name">{html.escape(title)}</div>
      <div class="char-tagline">{html.escape(tagline)}</div>
    </div>

    <!-- Portrait with flanking skill icons -->
    <div class="portrait-area">
      <div class="skill-left">
        {left_icons}
      </div>

      <div class="portrait-img">
        {portrait_inner}
      </div>

      <div class="skill-right">
        {right_icons}
      </div>
    </div>

    <!-- QR diamond -->
    <div class="qr-area">
      <div class="qr-outer">
        {qr_inner}
      </div>
    </div>

    <!-- Text -->
    <div class="text-area">
      <div class="text-rule">
        <div class="line"></div>
        <div class="dia"></div>
        <div class="line"></div>
      </div>

      <div class="skills-text">
        {skills_text}
      </div>

      <div class="story">
        <p>{bg_html}</p>
      </div>
    </div>

  </div>
</div>

</body>
</html>'''


def render_card(html_content: str, output_path: str, scale: int = 3):
    """Render the HTML card to a PNG image using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 800, "height": 600},
            device_scale_factor=scale,
        )
        page.set_content(html_content, wait_until="networkidle")

        # Wait for fonts to load
        page.wait_for_timeout(1500)

        # Screenshot just the card element
        card = page.locator(".card")
        card.screenshot(path=output_path, type="png")
        browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a character card image from a YAML file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python generate_card.py src/_data/characters/doctor.yaml
              python generate_card.py src/_data/characters/doctor.yaml --output card.png
              python generate_card.py src/_data/characters/doctor.yaml --scale 4
              python generate_card.py src/_data/characters/doctor.yaml --html-only
              python generate_card.py src/_data/characters/doctor.yaml --base-url https://example.com
        """),
    )
    parser.add_argument("yaml_file", help="Path to the character YAML file")
    parser.add_argument(
        "--output", "-o",
        help="Output PNG path (default: <id>_card.png)",
    )
    parser.add_argument(
        "--scale", "-s",
        type=int, default=3,
        help="Render scale factor for DPI (default: 3 → ~288 DPI)",
    )
    parser.add_argument(
        "--base-url",
        default="https://elenafilatova.github.io/murder_mystery",
        help="Base URL for character links (default: https://elenafilatova.github.io/murder_mystery)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Output the intermediate HTML file instead of rendering to PNG",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml_file).resolve()
    if not yaml_path.exists():
        print(f"Error: YAML file not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    yaml_dir = str(yaml_path.parent)

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    card_id = data.get("id", "character")
    html_content = generate_html(data, yaml_dir, args.base_url)

    if args.html_only:
        out = args.output or f"{card_id}_card.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML written to: {out}")
    else:
        out = args.output or f"{card_id}_card.png"
        print(f"Rendering card for '{data.get('title', card_id)}'...")
        render_card(html_content, out, scale=args.scale)
        print(f"Card saved to: {out}")


if __name__ == "__main__":
    main()

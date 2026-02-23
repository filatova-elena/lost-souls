#!/usr/bin/env python3
"""
Vision Card Generator — YAML → PNG via HTML template + Playwright.

Generates vision cards for each vision clue with:
- QR code that opens the clue page
- Ghost image (corresponding to the vision type)
- Title (clue title)
- Narrative text at the bottom

Usage:
    python generate_vision_card.py src/_data/clues/visions/alice/vision_alice_143_message_for_cordelia.yaml
    python generate_vision_card.py src/_data/clues/visions/alice/vision_alice_143_message_for_cordelia.yaml -o card.png
    python generate_vision_card.py src/_data/clues/visions/alice/vision_alice_143_message_for_cordelia.yaml --html-only
"""

import argparse
import base64
import html
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent.parent / "qr_codes"))
from qr_generator import generate_qr

BASE_URL = "https://lostsouls.door66.events"  # Base URL for QR codes


def to_data_uri(path):
    p = Path(path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp"}.get(p.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def find_image(image_rel, yaml_dir):
    path = Path(yaml_dir) / image_rel
    if path.exists():
        return path
    p = Path(yaml_dir).resolve()
    for _ in range(6):
        if (p / image_rel).exists():
            return p / image_rel
        p = p.parent
    raise FileNotFoundError(f"Image not found: {image_rel}")


def extract_ghost_name(vision_type):
    """Extract ghost name from vision type like 'Vision (Alice)' -> 'alice'."""
    match = re.search(r'Vision\s*\(([^)]+)\)', vision_type)
    if match:
        return match.group(1).lower().strip()
    return None


def get_act_roman_numeral(act_id):
    """Extract Roman numeral from act ID like 'act_ii_mystery_emerges' -> 'II'."""
    if not act_id:
        return None
    
    # Map act IDs to Roman numerals
    act_map = {
        'act_prologue': None,  # Prologue doesn't get a number
        'act_i_setting': 'I',
        'act_ii_mystery_emerges': 'II',
        'act_iii_investigation': 'III',
        'act_iv_revelation': 'IV',
        'act_v_conclusions': 'V',
        'act_v_aftermath': 'V',
    }
    
    return act_map.get(act_id)


def load_ghost_data(ghost_name, project_root):
    """Load ghost YAML data to get image path."""
    ghost_path = project_root / "src" / "_data" / "ghosts" / f"{ghost_name}.yaml"
    if not ghost_path.exists():
        raise FileNotFoundError(f"Ghost file not found: {ghost_path}")
    return yaml.safe_load(ghost_path.read_text(encoding="utf-8"))


def make_qr_uri(clue_id, base_url, scale):
    """Generate QR code for clue URL."""
    tmp = tempfile.mktemp(suffix=".png")
    # Construct URL: if base_url is empty, use relative path; otherwise use base_url
    url = f"clues/{clue_id}/" if not base_url else f"{base_url}/clues/{clue_id}/"
    generate_qr(url=url,
                output_path=tmp, size=120 * scale,
                overlay="keyhole", fg_color=(74, 20, 140, 255),
                bg_color=(255, 255, 255, 255), rotate=False, margin=0)
    from PIL import Image, ImageChops, ImageOps
    img = Image.open(tmp)
    bg = Image.new(img.mode, img.size, (255, 255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        img = img.crop(bbox)
        pad = max(4, img.width // 20)
        img = ImageOps.expand(img, pad, (255, 255, 255, 255))
        img.save(tmp)
    uri = to_data_uri(tmp)
    os.unlink(tmp)
    return uri


def build_html(vision_data, ghost_data, yaml_dir, scale=3, base_url=BASE_URL):
    """Build HTML for vision card."""
    clue_id = vision_data["id"]
    title = vision_data.get("title", "")
    
    # Add act number before title if available
    act_id = vision_data.get("act")
    act_numeral = get_act_roman_numeral(act_id)
    if act_numeral:
        title = f"{act_numeral}. {title}"
    
    narrative = vision_data.get("narrative", "").strip()

    # Get ghost image — use to_data_uri directly like the character card does.
    # Let CSS handle cropping/circular clipping via object-fit:cover + border-radius.
    ghost_image_rel = ghost_data.get("image")
    if not ghost_image_rel:
        raise ValueError(f"Ghost {ghost_data.get('ghost')} has no image field")

    portrait_uri = to_data_uri(str(find_image(ghost_image_rel, yaml_dir)))

    # Generate QR code
    qr_uri = make_qr_uri(clue_id, base_url, scale)

    # Format narrative text (remove markdown bold, clean up)
    narrative_text = narrative
    while "**" in narrative_text:
        narrative_text = narrative_text.replace("**", "", 2)
    narrative_text = narrative_text.strip()

    portrait = f'<img src="{portrait_uri}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    qr = f'<img src="{qr_uri}" style="width:100%;height:100%;object-fit:contain;" />'

    return (TEMPLATE
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{GHOST_IMAGE}}", portrait)
        .replace("{{QR}}", qr)
        .replace("{{NARRATIVE}}", html.escape(narrative_text)))


def render_card(html_content, output_path, scale=3):
    """Render HTML card to PNG using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 600},
                                device_scale_factor=scale)
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.locator(".card").screenshot(path=output_path, type="png")
        browser.close()


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Vision Card — {{TITLE}}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #444; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 30px; }
    .card { width: 3.5in; height: 4.5in; position: relative; overflow: hidden; }
    .card-bg { position: absolute; inset: 0; z-index: 0; }
    .card-content { position: absolute; inset: 0; z-index: 1; display: flex; flex-direction: column; align-items: center; }

    .title-area { padding: 12px 20px 0; text-align: center; width: 100%; }
    .vision-title { font-family: 'Playfair Display SC', serif; font-weight: 900; font-size: 18px; color: #4a148c; letter-spacing: 5px; line-height: 1; }

    .portrait-area { position: relative; width: 180px; height: 100px; margin-top: 4px; display: flex; align-items: center; justify-content: center; }
    .portrait-img {
      width: 82px; height: 82px; border-radius: 50%;
      background: #e4dcc8; z-index: 1;
      display: flex; align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }

    .qr-area { margin-top: -28px; z-index: 2; position: relative; }
    .qr-outer {
      width: 120px; height: 120px;
      transform: rotate(45deg);
      border: 1.5px solid #4a148c; background: #fff;
      display: flex; align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }
    .qr-outer img { width: 100%; height: 100%; }

    .bottom-area { flex: 1; width: 100%; padding: 6px 20px 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .text-rule { width: 100%; display: flex; align-items: center; gap: 5px; margin-bottom: 6px; }
    .text-rule .line { flex: 1; border-top: 0.6px solid #4a148c; }
    .text-rule .dia { width: 3px; height: 3px; background: #4a148c; transform: rotate(45deg); }

    .narrative { font-family: 'Playfair Display', serif; font-style: italic; font-size: 13px; line-height: 1.4; color: #6a4a8a; text-align: center; padding: 0 8px; }

    @media print { body { background: none; padding: 0; margin: 0; } @page { size: 3.5in 4.5in; margin: 0; } }
  </style>
</head>
<body>
<div class="card">
  <svg class="card-bg" viewBox="0 0 336 432" xmlns="http://www.w3.org/2000/svg">
    <rect width="336" height="432" fill="#f2ecda"/>
    <rect x="5" y="5" width="326" height="422" rx="2" fill="none" stroke="#4a148c" stroke-width="1.8"/>
    <rect x="9" y="9" width="318" height="414" rx="1" fill="none" stroke="#4a148c" stroke-width="0.5"/>
    <g opacity="0.6"><line x1="144" y1="5" x2="144" y2="12" stroke="#4a148c" stroke-width="0.5"/><line x1="132" y1="5" x2="136" y2="12" stroke="#4a148c" stroke-width="0.4"/><line x1="156" y1="5" x2="152" y2="12" stroke="#4a148c" stroke-width="0.4"/><line x1="122" y1="5" x2="129" y2="11" stroke="#4a148c" stroke-width="0.3"/><line x1="166" y1="5" x2="159" y2="11" stroke="#4a148c" stroke-width="0.3"/></g>
    <g opacity="0.6"><line x1="168" y1="427" x2="168" y2="420" stroke="#4a148c" stroke-width="0.5"/><line x1="156" y1="427" x2="160" y2="420" stroke="#4a148c" stroke-width="0.4"/><line x1="180" y1="427" x2="176" y2="420" stroke="#4a148c" stroke-width="0.4"/><line x1="146" y1="427" x2="153" y2="421" stroke="#4a148c" stroke-width="0.3"/><line x1="190" y1="427" x2="183" y2="421" stroke="#4a148c" stroke-width="0.3"/></g>
    <path d="M5 28 L5 5 L28 5" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M9 22 L9 9 L22 9" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="5" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M331 28 L331 5 L308 5" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M327 22 L327 9 L314 9" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="325" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M5 404 L5 427 L28 427" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M9 410 L9 423 L22 423" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="5" y="421" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M331 404 L331 427 L308 427" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M327 410 L327 423 L314 423" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="325" y="421" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <circle cx="168" cy="146" r="47" fill="none" stroke="#4a148c" stroke-width="1.2"/><circle cx="168" cy="146" r="51" fill="none" stroke="#4a148c" stroke-width="0.4" stroke-dasharray="2 3"/>
    <g opacity="0.07" stroke="#4a148c" stroke-width="0.5"><line x1="168" y1="90" x2="168" y2="74"/><line x1="198" y1="100" x2="210" y2="88"/><line x1="220" y1="126" x2="236" y2="120"/><line x1="220" y1="166" x2="236" y2="172"/><line x1="198" y1="192" x2="210" y2="204"/><line x1="138" y1="100" x2="126" y2="88"/><line x1="116" y1="126" x2="100" y2="120"/><line x1="116" y1="166" x2="100" y2="172"/><line x1="138" y1="192" x2="126" y2="204"/></g>
    <line x1="16" y1="124" x2="16" y2="168" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/><line x1="19" y1="130" x2="19" y2="162" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
    <line x1="320" y1="124" x2="320" y2="168" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/><line x1="317" y1="130" x2="317" y2="162" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
  </svg>
  <div class="card-content">
    <div class="title-area">
      <div class="vision-title">{{TITLE}}</div>
    </div>
    <div class="portrait-area">
      <div class="portrait-img">{{GHOST_IMAGE}}</div>
    </div>
    <div class="qr-area"><div class="qr-outer">{{QR}}</div></div>
    <div class="bottom-area">
      <div class="text-rule"><div class="line"></div><div class="dia"></div><div class="line"></div></div>
      <div class="narrative">{{NARRATIVE}}</div>
    </div>
  </div>
</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate vision card from YAML")
    parser.add_argument("yaml_file")
    parser.add_argument("--output", "-o")
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    yaml_path = Path(args.yaml_file).resolve()
    vision_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # Find project root (go up from scripts/visions/)
    project_root = yaml_path
    for _ in range(10):
        if (project_root / "src" / "_data" / "ghosts").exists():
            break
        project_root = project_root.parent
    else:
        raise FileNotFoundError("Could not find project root with ghosts directory")

    # Extract ghost name from vision type
    vision_type = vision_data.get("type", "")
    ghost_name = extract_ghost_name(vision_type)
    if not ghost_name:
        raise ValueError(f"Could not extract ghost name from vision type: {vision_type}")

    # Load ghost data
    ghost_data = load_ghost_data(ghost_name, project_root)

    clue_id = vision_data["id"]
    
    # Format title with act number for display
    title = vision_data.get("title", clue_id)
    act_id = vision_data.get("act")
    act_numeral = get_act_roman_numeral(act_id)
    if act_numeral:
        display_title = f"{act_numeral}. {title}"
    else:
        display_title = title
    
    h = build_html(vision_data, ghost_data, str(yaml_path.parent), args.scale, args.base_url)

    # Output
    suffix = ".html" if args.html_only else ".png"
    out = args.output or f"to_print/vision_cards/{clue_id}_card{suffix}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    if args.html_only:
        Path(out).write_text(h, encoding="utf-8")
    else:
        print(f"Rendering {display_title}...")
        render_card(h, out, args.scale)
    print(f"→ {out}")


if __name__ == "__main__":
    main()

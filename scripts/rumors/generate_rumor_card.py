#!/usr/bin/env python3
"""
Rumor Card Generator — YAML → PNG via HTML template + Playwright.

Generates rumor cards for each rumor clue with:
- Title with act Roman numeral (e.g., "II. Rumor")
- Gossiper image
- Rumor content text

Usage:
    python generate_rumor_card.py src/_data/rumors/rumor_01_sebastian_romano_alchemist.yaml
    python generate_rumor_card.py src/_data/rumors/rumor_01_sebastian_romano_alchemist.yaml -o card.png
    python generate_rumor_card.py src/_data/rumors/rumor_01_sebastian_romano_alchemist.yaml --html-only
"""

import argparse
import base64
import html
import os
import sys
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

BASE_URL = "https://lostsouls.door66.events"  # Base URL (not used for rumors, but kept for consistency)


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


def build_html(rumor_data, gossiper_image_path, scale=3):
    """Build HTML for rumor card.
    
    Card size: 2.5x3.5 inches (standard playing card size)
    """
    rumor_id = rumor_data["id"]
    
    # Title format: Roman numeral + "Rumor"
    act_id = rumor_data.get("act")
    act_numeral = get_act_roman_numeral(act_id)
    if act_numeral:
        title = f"{act_numeral}. Rumor"
    else:
        title = "Rumor"
    
    content = rumor_data.get("content", "").strip()

    # Get gossiper image
    gossiper_uri = to_data_uri(str(gossiper_image_path))

    # Format content text (remove markdown bold, clean up)
    content_text = content
    while "**" in content_text:
        content_text = content_text.replace("**", "", 2)
    content_text = content_text.strip()

    gossiper_img = f'<img src="{gossiper_uri}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'

    # Determine if content is long (more than ~120 characters or 18 words)
    is_long_content = len(content_text) > 120 or len(content_text.split()) > 18
    gossiper_class = ' small' if is_long_content else ''
    # Normal: image ends at 150px (40px + 110px), line at 150px (touching)
    # Small: image ends at 125px (35px + 90px), line at 125px (touching)
    bottom_padding = '125px' if is_long_content else '150px'

    return (TEMPLATE
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{GOSSIPER_IMAGE}}", gossiper_img)
        .replace("{{CONTENT}}", html.escape(content_text))
        .replace("{{RUMOR_ID}}", html.escape(rumor_id))
        .replace("{{GOSSIPER_CLASS}}", gossiper_class)
        .replace("{{BOTTOM_PADDING}}", bottom_padding))


def render_card(html_content, output_path, scale=3):
    """Render HTML card to PNG using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 840},
                                device_scale_factor=scale)
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.locator(".card").screenshot(path=output_path, type="png")
        browser.close()


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Rumor Card — {{TITLE}}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #444; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 30px; }
    .card { width: 2.5in; height: 3.5in; position: relative; overflow: hidden; }
    .card-bg { position: absolute; inset: 0; z-index: 0; }
    .card-content { position: absolute; inset: 0; z-index: 1; display: flex; flex-direction: column; align-items: center; }

    .title-area { padding: 10px 16px 0; text-align: center; width: 100%; }
    .rumor-title { font-family: 'Playfair Display SC', serif; font-weight: 900; font-size: 16px; color: #4a148c; letter-spacing: 4px; line-height: 1; }

    .gossiper-area { position: absolute; top: 40px; left: 50%; transform: translateX(-50%); width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; }
    .gossiper-img {
      width: 110px; height: 110px; border-radius: 50%;
      background: #e4dcc8; z-index: 1;
      display: flex; align-items: center; justify-content: center;
      position: relative; overflow: hidden;
      transition: all 0.3s ease;
    }
    .gossiper-area.small { top: 35px; width: 100px; height: 100px; }
    .gossiper-area.small .gossiper-img { width: 90px; height: 90px; }

    .bottom-area { flex: 1; width: 100%; padding-left: 16px; padding-right: 16px; padding-bottom: 20px; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
    .text-rule { width: 100%; display: flex; align-items: center; gap: 4px; margin-bottom: 6px; }
    .text-rule .line { flex: 1; border-top: 0.6px solid #4a148c; }
    .text-rule .dia { width: 3px; height: 3px; background: #4a148c; transform: rotate(45deg); }

    .content { font-family: 'Playfair Display', serif; font-style: italic; font-size: 13px; line-height: 1.5; color: #6a4a8a; text-align: center; padding: 0 6px; }

    .rumor-id { font-family: 'Crimson Text', serif; font-size: 10px; color: #8a7a9a; text-align: center; margin-top: 4px; opacity: 0.8; }

    @media print { body { background: none; padding: 0; margin: 0; } @page { size: 2.5in 3.5in; margin: 0; } }
  </style>
</head>
<body>
<div class="card">
  <svg class="card-bg" viewBox="0 0 240 336" xmlns="http://www.w3.org/2000/svg">
    <rect width="240" height="336" fill="#f2ecda"/>
    <rect x="3.5" y="3.5" width="233" height="329" rx="1.5" fill="none" stroke="#4a148c" stroke-width="1.3"/>
    <rect x="6.5" y="6.5" width="227" height="323" rx="0.7" fill="none" stroke="#4a148c" stroke-width="0.4"/>
    <g opacity="0.6"><line x1="103" y1="3.5" x2="103" y2="8.5" stroke="#4a148c" stroke-width="0.4"/><line x1="94" y1="3.5" x2="97" y2="8.5" stroke="#4a148c" stroke-width="0.3"/><line x1="112" y1="3.5" x2="109" y2="8.5" stroke="#4a148c" stroke-width="0.3"/><line x1="87" y1="3.5" x2="92" y2="8" stroke="#4a148c" stroke-width="0.2"/><line x1="119" y1="3.5" x2="114" y2="8" stroke="#4a148c" stroke-width="0.2"/></g>
    <g opacity="0.6"><line x1="120" y1="332.5" x2="120" y2="327.5" stroke="#4a148c" stroke-width="0.4"/><line x1="111" y1="332.5" x2="114" y2="327.5" stroke="#4a148c" stroke-width="0.3"/><line x1="129" y1="332.5" x2="126" y2="327.5" stroke="#4a148c" stroke-width="0.3"/><line x1="104" y1="332.5" x2="109" y2="328" stroke="#4a148c" stroke-width="0.2"/><line x1="136" y1="332.5" x2="131" y2="328" stroke="#4a148c" stroke-width="0.2"/></g>
    <path d="M3.5 20 L3.5 3.5 L20 3.5" stroke="#4a148c" stroke-width="1.8" fill="none"/><path d="M6.5 16 L6.5 6.5 L16 6.5" stroke="#4a148c" stroke-width="0.4" fill="none"/><rect x="3.5" y="3.5" width="4.5" height="4.5" fill="#4a148c" opacity="0.12"/>
    <path d="M236.5 20 L236.5 3.5 L220 3.5" stroke="#4a148c" stroke-width="1.8" fill="none"/><path d="M233.5 16 L233.5 6.5 L224 6.5" stroke="#4a148c" stroke-width="0.4" fill="none"/><rect x="232" y="3.5" width="4.5" height="4.5" fill="#4a148c" opacity="0.12"/>
    <path d="M3.5 316 L3.5 332.5 L20 332.5" stroke="#4a148c" stroke-width="1.8" fill="none"/><path d="M6.5 320 L6.5 329.5 L16 329.5" stroke="#4a148c" stroke-width="0.4" fill="none"/><rect x="3.5" y="328" width="4.5" height="4.5" fill="#4a148c" opacity="0.12"/>
    <path d="M236.5 316 L236.5 332.5 L220 332.5" stroke="#4a148c" stroke-width="1.8" fill="none"/><path d="M233.5 320 L233.5 329.5 L224 329.5" stroke="#4a148c" stroke-width="0.4" fill="none"/><rect x="232" y="328" width="4.5" height="4.5" fill="#4a148c" opacity="0.12"/>
    <g opacity="0.07" stroke="#4a148c" stroke-width="0.4"><line x1="120" y1="65" x2="120" y2="54"/><line x1="142" y1="72" x2="150" y2="63"/><line x1="157" y1="90" x2="169" y2="86"/><line x1="157" y1="130" x2="169" y2="123"/><line x1="142" y1="148" x2="150" y2="146"/><line x1="98" y1="72" x2="90" y2="63"/><line x1="83" y1="90" x2="71" y2="86"/><line x1="83" y1="130" x2="71" y2="123"/><line x1="98" y1="148" x2="90" y2="146"/></g>
    <line x1="11.5" y1="89" x2="11.5" y2="131" stroke="#4a148c" stroke-width="0.4" opacity="0.15"/><line x1="13.5" y1="93" x2="13.5" y2="127" stroke="#4a148c" stroke-width="0.2" opacity="0.1"/>
    <line x1="228.5" y1="89" x2="228.5" y2="131" stroke="#4a148c" stroke-width="0.4" opacity="0.15"/><line x1="226.5" y1="93" x2="226.5" y2="127" stroke="#4a148c" stroke-width="0.2" opacity="0.1"/>
  </svg>
  <div class="card-content">
    <div class="title-area">
      <div class="rumor-title">{{TITLE}}</div>
    </div>
    <div class="gossiper-area{{GOSSIPER_CLASS}}">
      <div class="gossiper-img">{{GOSSIPER_IMAGE}}</div>
    </div>
    <div class="bottom-area" style="padding-top: {{BOTTOM_PADDING}};">
      <div class="text-rule"><div class="line"></div><div class="dia"></div><div class="line"></div></div>
      <div class="content">{{CONTENT}}</div>
      <div class="rumor-id">{{RUMOR_ID}}</div>
    </div>
  </div>
</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate rumor card from YAML")
    parser.add_argument("yaml_file")
    parser.add_argument("--output", "-o")
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    yaml_path = Path(args.yaml_file).resolve()
    rumor_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # Find project root (go up from scripts/rumors/)
    project_root = yaml_path
    for _ in range(10):
        if (project_root / "src" / "_data" / "rumors").exists():
            break
        project_root = project_root.parent
    else:
        raise FileNotFoundError("Could not find project root with rumors directory")

    # Find gossiper image
    gossiper_image_path = project_root / "src" / "assets" / "images" / "gossip" / "gossiper.png"
    if not gossiper_image_path.exists():
        raise FileNotFoundError(f"Gossiper image not found: {gossiper_image_path}")

    rumor_id = rumor_data["id"]
    
    # Format title with act number for display
    act_id = rumor_data.get("act")
    act_numeral = get_act_roman_numeral(act_id)
    if act_numeral:
        display_title = f"{act_numeral}. Rumor"
    else:
        display_title = "Rumor"
    
    h = build_html(rumor_data, gossiper_image_path, args.scale)

    # Output
    suffix = ".html" if args.html_only else ".png"
    out = args.output or f"to_print/rumor_cards/{rumor_id}_card{suffix}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    if args.html_only:
        Path(out).write_text(h, encoding="utf-8")
    else:
        print(f"Rendering {display_title} ({rumor_id})...")
        render_card(h, out, args.scale)
    print(f"→ {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Character Card Generator — YAML → PNG via HTML template + Playwright.

Usage:
    python generate_card.py src/_data/characters/doctor.yaml
    python generate_card.py src/_data/characters/doctor.yaml -o card.png
    python generate_card.py src/_data/characters/doctor.yaml --html-only
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

BASE_URL = ""  # Use relative paths by default

SKILL_ICON = (
    '<div class="skill-icon">'
    '<svg class="icon-shape" viewBox="0 0 26 26"><polygon points="13,0 26,13 13,26 0,13" '
    'fill="none" stroke="#4a148c" stroke-width="0.8" opacity="0.3"/></svg>'
    '<span class="icon-label">{icon}</span></div>'
)


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


def load_skills_data(project_root):
    """Load skills.yaml data."""
    skills_path = project_root / "src" / "_data" / "refs" / "skills.yaml"
    if not skills_path.exists():
        raise FileNotFoundError(f"Skills file not found: {skills_path}")
    return yaml.safe_load(skills_path.read_text(encoding="utf-8"))


def format_character_skills(skills, skills_data):
    """
    Format character skills using the same logic as the Eleventy filter.
    Returns list of formatted skill strings like "Art expert 🎨"
    """
    if not skills or not skills_data:
        return []
    
    # Handle both flat array and nested object formats
    skill_ids = []
    if isinstance(skills, list):
        skill_ids = skills
    elif isinstance(skills, dict):
        # Nested format: combine all levels
        skill_ids = (
            (skills.get("expert") or []) +
            (skills.get("basic") or []) +
            (skills.get("personal") or [])
        )
    
    formatted = []
    
    for skill_id in skill_ids:
        # Skip meta skills
        if skill_id and skill_id.startswith("is_character_"):
            continue
        
        # Extract level from skill ID (e.g., "art_2" -> level "2", "personal_romano" -> level "1")
        level = "1"  # Default to level 1
        base_skill_id = skill_id
        
        # Check if skill has level suffix
        level_match = re.match(r".*_(1|2)$", skill_id)
        if level_match:
            level = level_match.group(1)
            base_skill_id = re.sub(r"_[12]$", "", skill_id)
        elif skill_id.startswith("personal_"):
            # Personal skills without suffix are always level 1
            level = "1"
            base_skill_id = skill_id
        
        # Look up the skill in skills.yaml
        skill_info = skills_data.get(base_skill_id)
        
        # For personal skills, try without level suffix if not found
        if not skill_info and skill_id.startswith("personal_") and level_match:
            base_skill_id = re.sub(r"_[12]$", "", skill_id)
            skill_info = skills_data.get(base_skill_id)
        
        if skill_info and skill_info.get("level") and skill_info["level"].get(level):
            level_text = skill_info["level"][level]
            icon = skill_info.get("icon", "")
            formatted.append(f"{level_text} {icon}".strip())
        elif skill_info and skill_info.get("title"):
            # Fallback to title if level not found
            icon = skill_info.get("icon", "")
            formatted.append(f"{skill_info['title']} {icon}".strip())
        else:
            # Fallback: format the ID
            formatted_text = skill_id.replace("_", " ").title()
            formatted.append(formatted_text)
    
    return formatted


def make_qr_uri(character_id, base_url, scale):
    tmp = tempfile.mktemp(suffix=".png")
    # Construct URL: if base_url is empty, use relative path; otherwise use base_url
    url = f"characters/{character_id}/" if not base_url else f"{base_url}/characters/{character_id}/"
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


def build_html(data, yaml_dir, scale=3, base_url=BASE_URL, skills_data=None):
    title = data["title"]
    char_id = data["id"]
    image_rel = data["image"]

    # Personality short for bottom text
    personality = data.get("personality_short") or data.get("personality") or ""
    while "**" in personality:
        personality = personality.replace("**", "", 2)

    # Skills — use same logic as character page
    formatted_skills = format_character_skills(data.get("skills", []), skills_data or {})
    
    # Extract icons from formatted skills (they're at the end after a space)
    # Format is like "Art expert 🎨" or "Montrose Family 👥"
    skill_icons = []
    for skill_text in formatted_skills[:4]:
        # Extract emoji/icon (usually at the end)
        parts = skill_text.rsplit(" ", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:  # Likely an emoji/icon
            skill_icons.append(parts[1])
        else:
            skill_icons.append("◇")
    
    # Pad to 4 skills
    while len(skill_icons) < 4:
        skill_icons.append("◇")
    
    # Get skill titles (without icons) for text display
    skill_titles = []
    for skill_text in formatted_skills:
        # Remove icon if present
        parts = skill_text.rsplit(" ", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:  # Likely an emoji/icon
            skill_titles.append(parts[0])
        else:
            skill_titles.append(skill_text)

    portrait_uri = to_data_uri(str(find_image(image_rel, yaml_dir)))
    qr_uri = make_qr_uri(char_id, base_url, scale)

    portrait = f'<img src="{portrait_uri}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    qr = f'<img src="{qr_uri}" style="width:100%;height:100%;object-fit:contain;" />'

    skill_left = "\n".join(SKILL_ICON.format(icon=skill_icons[i]) for i in range(min(2, len(skill_icons))))
    skill_right = "\n".join(SKILL_ICON.format(icon=skill_icons[i]) for i in range(2, min(4, len(skill_icons))))

    skills_text = '<span class="sep">◆</span>'.join(f'<span>{html.escape(t)}</span>' for t in skill_titles)

    return (TEMPLATE
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{PORTRAIT}}", portrait)
        .replace("{{QR}}", qr)
        .replace("{{SKILL_LEFT}}", skill_left)
        .replace("{{SKILL_RIGHT}}", skill_right)
        .replace("{{SKILLS_TEXT}}", skills_text)
        .replace("{{PERSONALITY}}", html.escape(personality)))


def render_card(html_content, output_path, scale=3):
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
  <title>Character Card — {{TITLE}}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #444; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 30px; }
    .card { width: 3.5in; height: 4.5in; position: relative; overflow: hidden; }
    .card-bg { position: absolute; inset: 0; z-index: 0; }
    .card-content { position: absolute; inset: 0; z-index: 1; display: flex; flex-direction: column; align-items: center; }

    .title-area { padding: 12px 20px 0; text-align: center; width: 100%; }
    .char-name { font-family: 'Playfair Display SC', serif; font-weight: 900; font-size: 18px; color: #4a148c; letter-spacing: 5px; line-height: 1; }

    .portrait-area { position: relative; width: 180px; height: 100px; margin-top: 4px; display: flex; align-items: center; justify-content: center; }
    .portrait-img { width: 82px; height: 82px; border-radius: 50%; background: #e4dcc8; z-index: 1; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }

    .skill-left, .skill-right { position: absolute; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 8px; z-index: 2; }
    .skill-left { left: 0; align-items: center; }
    .skill-right { right: 0; align-items: center; }
    .skill-icon { width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; position: relative; }
    .skill-icon .icon-shape { position: absolute; inset: 0; }
    .skill-icon .icon-label { font-family: 'Crimson Text', serif; font-size: 8px; color: #4a148c; z-index: 1; line-height: 1; }

    .qr-area { margin-top: -28px; z-index: 2; position: relative; }
    .qr-outer { width: 120px; height: 120px; transform: rotate(45deg); border: 1.5px solid #4a148c; background: #fff; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
    .qr-outer img { width: 100%; height: 100%; }

    .bottom-area { flex: 1; width: 100%; padding: 6px 20px 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .text-rule { width: 100%; display: flex; align-items: center; gap: 5px; margin-bottom: 6px; }
    .text-rule .line { flex: 1; border-top: 0.6px solid #4a148c; }
    .text-rule .dia { width: 3px; height: 3px; background: #4a148c; transform: rotate(45deg); }

    .skills-text { text-align: center; margin-bottom: 6px; }
    .skills-text span { font-family: 'Playfair Display SC', serif; font-size: 11px; letter-spacing: 2px; color: #4a148c; }
    .skills-text .sep { opacity: 0.3; margin: 0 5px; }

    .personality { font-family: 'Playfair Display', serif; font-style: italic; font-size: 13px; line-height: 1.4; color: #6a4a8a; text-align: center; padding: 0 8px; }

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
      <div class="char-name">{{TITLE}}</div>
    </div>
    <div class="portrait-area">
      <div class="skill-left">{{SKILL_LEFT}}</div>
      <div class="portrait-img">{{PORTRAIT}}</div>
      <div class="skill-right">{{SKILL_RIGHT}}</div>
    </div>
    <div class="qr-area"><div class="qr-outer">{{QR}}</div></div>
    <div class="bottom-area">
      <div class="text-rule"><div class="line"></div><div class="dia"></div><div class="line"></div></div>
      <div class="skills-text">{{SKILLS_TEXT}}</div>
      <div class="personality">{{PERSONALITY}}</div>
    </div>
  </div>
</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate character card from YAML")
    parser.add_argument("yaml_file")
    parser.add_argument("--output", "-o")
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    yaml_path = Path(args.yaml_file).resolve()
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # Find project root (go up from scripts/characters/)
    project_root = yaml_path
    for _ in range(10):
        if (project_root / "src" / "_data" / "refs" / "skills.yaml").exists():
            break
        project_root = project_root.parent
    else:
        raise FileNotFoundError("Could not find project root with skills.yaml")
    
    skills_data = load_skills_data(project_root)

    card_id = data["id"]
    h = build_html(data, str(yaml_path.parent), args.scale, args.base_url, skills_data)

    suffix = ".html" if args.html_only else ".png"
    out = args.output or f"to_print/character_cards/{card_id}_card{suffix}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    if args.html_only:
        Path(out).write_text(h, encoding="utf-8")
    else:
        print(f"Rendering {data['title']}...")
        render_card(h, out, args.scale)
    print(f"→ {out}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quest Answer Card Generator — YAML → PNG via HTML template + Playwright.

Creates answer cards for character quests. These cards show:
- Character name and image
- Character skills
- Quest objective (instead of personality)
- QR code linking to the quest page

Usage:
    python generate_answer_card.py src/_data/characters/artcollector.yaml main
    python generate_answer_card.py src/_data/characters/artcollector.yaml private -o card.png
    python generate_answer_card.py src/_data/characters/artcollector.yaml main --html-only
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

# Import shared functions from character card generator
sys.path.insert(0, str(Path(__file__).parent.parent / "characters"))
from generate_card import (
    to_data_uri,
    find_image,
    load_skills_data,
    format_character_skills,
    SKILL_ICON,
)

BASE_URL = ""  # Use relative paths by default


def load_quest_data(project_root, quest_id):
    """Load quest YAML data by ID."""
    quests_dir = project_root / "src" / "_data" / "quests"
    quest_path = quests_dir / f"{quest_id}.yaml"
    
    if not quest_path.exists():
        raise FileNotFoundError(f"Quest file not found: {quest_path}")
    
    return yaml.safe_load(quest_path.read_text(encoding="utf-8"))


def make_qr_uri(quest_id, base_url, scale):
    """Generate QR code URI for quest page."""
    tmp = tempfile.mktemp(suffix=".png")
    # Construct URL: if base_url is empty, use relative path; otherwise use base_url
    url = f"quests/{quest_id}/" if not base_url else f"{base_url}/quests/{quest_id}/"
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


def build_html(character_data, quest_data, yaml_dir, scale=3, base_url=BASE_URL, skills_data=None):
    """Build HTML for quest answer card."""
    title = character_data["title"]
    char_id = character_data["id"]
    image_rel = character_data["image"]

    # Quest objective for bottom text (instead of personality)
    objective = quest_data.get("objective", "")
    # Clean up markdown formatting
    while "**" in objective:
        objective = objective.replace("**", "", 2)

    # Skills — use same logic as character page
    formatted_skills = format_character_skills(character_data.get("skills", []), skills_data or {})
    
    # Extract icons from formatted skills
    skill_icons = []
    for skill_text in formatted_skills[:4]:
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
        parts = skill_text.rsplit(" ", 1)
        if len(parts) == 2 and len(parts[1]) <= 2:  # Likely an emoji/icon
            skill_titles.append(parts[0])
        else:
            skill_titles.append(skill_text)

    portrait_uri = to_data_uri(str(find_image(image_rel, yaml_dir)))
    quest_id = quest_data["id"]
    qr_uri = make_qr_uri(quest_id, base_url, scale)

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
        .replace("{{OBJECTIVE}}", html.escape(objective)))


def render_card(html_content, output_path, scale=3):
    """Render HTML card to PNG."""
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
  <title>Quest Answer Card — {{TITLE}}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display+SC:wght@400;700;900&family=Playfair+Display:ital,wght@1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #444; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 30px; }
    .card { width: 3in; height: 4in; position: relative; overflow: hidden; }
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

    .objective { font-family: 'Playfair Display', serif; font-style: italic; font-size: 13px; line-height: 1.4; color: #6a4a8a; text-align: center; padding: 0 8px; }

    @media print { body { background: none; padding: 0; margin: 0; } @page { size: 3in 4in; margin: 0; } }
  </style>
</head>
<body>
<div class="card">
  <svg class="card-bg" viewBox="0 0 288 384" xmlns="http://www.w3.org/2000/svg">
    <rect width="288" height="384" fill="#f2ecda"/>
    <rect x="5" y="5" width="278" height="374" rx="2" fill="none" stroke="#4a148c" stroke-width="1.8"/>
    <rect x="9" y="9" width="270" height="366" rx="1" fill="none" stroke="#4a148c" stroke-width="0.5"/>
    <g opacity="0.6"><line x1="144" y1="5" x2="144" y2="12" stroke="#4a148c" stroke-width="0.5"/><line x1="132" y1="5" x2="136" y2="12" stroke="#4a148c" stroke-width="0.4"/><line x1="156" y1="5" x2="152" y2="12" stroke="#4a148c" stroke-width="0.4"/><line x1="122" y1="5" x2="129" y2="11" stroke="#4a148c" stroke-width="0.3"/><line x1="166" y1="5" x2="159" y2="11" stroke="#4a148c" stroke-width="0.3"/></g>
    <g opacity="0.6"><line x1="144" y1="379" x2="144" y2="372" stroke="#4a148c" stroke-width="0.5"/><line x1="132" y1="379" x2="136" y2="372" stroke="#4a148c" stroke-width="0.4"/><line x1="156" y1="379" x2="152" y2="372" stroke="#4a148c" stroke-width="0.4"/><line x1="122" y1="379" x2="129" y2="373" stroke="#4a148c" stroke-width="0.3"/><line x1="166" y1="379" x2="159" y2="373" stroke="#4a148c" stroke-width="0.3"/></g>
    <path d="M5 28 L5 5 L28 5" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M9 22 L9 9 L22 9" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="5" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M283 28 L283 5 L260 5" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M279 22 L279 9 L266 9" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="277" y="5" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M5 356 L5 379 L28 379" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M9 362 L9 375 L22 375" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="5" y="373" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <path d="M283 356 L283 379 L260 379" stroke="#4a148c" stroke-width="2.5" fill="none"/><path d="M279 362 L279 375 L266 375" stroke="#4a148c" stroke-width="0.6" fill="none"/><rect x="277" y="373" width="6" height="6" fill="#4a148c" opacity="0.12"/>
    <circle cx="144" cy="130" r="47" fill="none" stroke="#4a148c" stroke-width="1.2"/><circle cx="144" cy="130" r="51" fill="none" stroke="#4a148c" stroke-width="0.4" stroke-dasharray="2 3"/>
    <g opacity="0.07" stroke="#4a148c" stroke-width="0.5"><line x1="144" y1="74" x2="144" y2="58"/><line x1="174" y1="84" x2="186" y2="72"/><line x1="196" y1="110" x2="212" y2="104"/><line x1="196" y1="150" x2="212" y2="156"/><line x1="174" y1="176" x2="186" y2="188"/><line x1="114" y1="84" x2="102" y2="72"/><line x1="92" y1="110" x2="76" y2="104"/><line x1="92" y1="150" x2="76" y2="156"/><line x1="114" y1="176" x2="102" y2="188"/></g>
    <line x1="16" y1="108" x2="16" y2="152" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/><line x1="19" y1="114" x2="19" y2="146" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
    <line x1="272" y1="108" x2="272" y2="152" stroke="#4a148c" stroke-width="0.5" opacity="0.15"/><line x1="269" y1="114" x2="269" y2="146" stroke="#4a148c" stroke-width="0.3" opacity="0.1"/>
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
      <div class="objective">{{OBJECTIVE}}</div>
    </div>
  </div>
</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate quest answer card from character YAML")
    parser.add_argument("yaml_file", help="Path to character YAML file")
    parser.add_argument("quest_type", choices=["main", "private"], help="Quest type: main or private")
    parser.add_argument("--output", "-o", help="Output PNG path")
    parser.add_argument("--scale", "-s", type=int, default=3, help="Render scale (default: 3)")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for QR codes")
    parser.add_argument("--html-only", action="store_true", help="Output HTML instead of PNG")
    args = parser.parse_args()

    yaml_path = Path(args.yaml_file).resolve()
    character_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # Find project root
    project_root = yaml_path
    for _ in range(10):
        if (project_root / "src" / "_data" / "refs" / "skills.yaml").exists():
            break
        project_root = project_root.parent
    else:
        raise FileNotFoundError("Could not find project root with skills.yaml")
    
    # Load skills data
    skills_data = load_skills_data(project_root)
    
    # Get quest ID from character objectives
    objectives = character_data.get("objectives", {})
    quest_id = objectives.get(args.quest_type)
    
    if not quest_id:
        raise ValueError(f"Character {character_data.get('id')} does not have a {args.quest_type} quest")
    
    # Load quest data
    quest_data = load_quest_data(project_root, quest_id)
    
    # Build HTML
    h = build_html(character_data, quest_data, str(yaml_path.parent), args.scale, args.base_url, skills_data)

    # Determine output path
    char_id = character_data["id"]
    suffix = ".html" if args.html_only else ".png"
    out = args.output or f"to_print/quest_answer_cards/{char_id}_{args.quest_type}_answer{suffix}"
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    if args.html_only:
        Path(out).write_text(h, encoding="utf-8")
    else:
        print(f"Rendering {character_data['title']} - {quest_data.get('title', quest_id)} ({args.quest_type})...")
        render_card(h, out, args.scale)
    print(f"→ {out}")


if __name__ == "__main__":
    main()

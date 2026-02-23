#!/usr/bin/env python3
"""
Generate all rumor cards from rumor YAML files.

Finds all rumor YAML files in src/_data/rumors/ and generates
a card for each one.

Usage:
    python generate_all_rumor_cards.py
    python generate_all_rumor_cards.py --output-dir to_print/rumor_cards
    python generate_all_rumor_cards.py --scale 3
"""

import argparse
import sys
from pathlib import Path

# Import generate_rumor_card functions
sys.path.insert(0, str(Path(__file__).parent))
from generate_rumor_card import (
    build_html,
    render_card,
    get_act_roman_numeral,
    BASE_URL,
)

import yaml


def find_all_rumor_yamls(rumors_dir):
    """Find all rumor YAML files recursively."""
    rumors_path = Path(rumors_dir)
    if not rumors_path.exists():
        raise FileNotFoundError(f"Rumors directory not found: {rumors_path}")
    
    yaml_files = sorted(rumors_path.rglob("*.yaml")) + sorted(rumors_path.rglob("*.yml"))
    # Filter to only rumor files (check if they have type field with "Rumor")
    rumor_files = []
    for yaml_file in yaml_files:
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if data and data.get("type", "").startswith("Rumor"):
                rumor_files.append(yaml_file)
        except Exception as e:
            print(f"Warning: Could not read {yaml_file}: {e}")
            continue
    
    return rumor_files


def main():
    parser = argparse.ArgumentParser(description="Generate all rumor cards")
    parser.add_argument("--output-dir", "-o", default="to_print/rumor_cards")
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--rumors-dir", default="src/_data/rumors")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    rumors_dir = project_root / args.rumors_dir

    # Find all rumor files
    rumor_files = find_all_rumor_yamls(rumors_dir)
    print(f"Found {len(rumor_files)} rumor files\n")

    if not rumor_files:
        print("No rumor files found!")
        return

    # Find gossiper image
    gossiper_image_path = project_root / "src" / "assets" / "images" / "gossip" / "gossiper.png"
    if not gossiper_image_path.exists():
        raise FileNotFoundError(f"Gossiper image not found: {gossiper_image_path}")

    # Generate cards
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    error_count = 0

    for i, rumor_file in enumerate(rumor_files, 1):
        try:
            rumor_data = yaml.safe_load(rumor_file.read_text(encoding="utf-8"))
            rumor_id = rumor_data.get("id", rumor_file.stem)
            
            # Format title with act number for display
            act_id = rumor_data.get("act")
            act_numeral = get_act_roman_numeral(act_id)
            if act_numeral:
                display_title = f"{act_numeral}. Rumor"
            else:
                display_title = "Rumor"
            
            print(f"[{i}/{len(rumor_files)}] {rumor_id}: {display_title}")

            # Build HTML
            html_content = build_html(rumor_data, gossiper_image_path, args.scale)

            # Output
            suffix = ".html" if args.html_only else ".png"
            output_path = output_dir / f"{rumor_id}_card{suffix}"

            if args.html_only:
                output_path.write_text(html_content, encoding="utf-8")
            else:
                render_card(html_content, str(output_path), args.scale)
            
            print(f"  ✅ {output_path}")
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
            import traceback
            traceback.print_exc()

    print(f"\n✅ Generated {success_count}/{len(rumor_files)} cards")
    if error_count > 0:
        print(f"❌ {error_count} errors")


if __name__ == "__main__":
    main()

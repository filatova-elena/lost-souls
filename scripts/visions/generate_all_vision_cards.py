#!/usr/bin/env python3
"""
Generate all vision cards from vision clue YAML files.

Finds all vision YAML files in src/_data/clues/visions/ and generates
a card for each one.

Usage:
    python generate_all_vision_cards.py
    python generate_all_vision_cards.py --output-dir to_print/vision_cards
    python generate_all_vision_cards.py --scale 3
"""

import argparse
import sys
from pathlib import Path

# Import generate_vision_card functions
sys.path.insert(0, str(Path(__file__).parent))
from generate_vision_card import (
    main as generate_single_card,
    extract_ghost_name,
    load_ghost_data,
    build_html,
    render_card,
    find_image,
    BASE_URL,
)

import yaml


def find_all_vision_yamls(visions_dir):
    """Find all vision YAML files recursively."""
    visions_path = Path(visions_dir)
    if not visions_path.exists():
        raise FileNotFoundError(f"Visions directory not found: {visions_path}")
    
    yaml_files = sorted(visions_path.rglob("*.yaml")) + sorted(visions_path.rglob("*.yml"))
    # Filter to only vision files (check if they have type field with "Vision")
    vision_files = []
    for yaml_file in yaml_files:
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if data and data.get("type", "").startswith("Vision"):
                vision_files.append(yaml_file)
        except Exception as e:
            print(f"Warning: Could not read {yaml_file}: {e}")
            continue
    
    return vision_files


def main():
    parser = argparse.ArgumentParser(description="Generate all vision cards")
    parser.add_argument("--output-dir", "-o", default="to_print/visions")
    parser.add_argument("--scale", "-s", type=int, default=3)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--html-only", action="store_true")
    parser.add_argument("--visions-dir", default="src/_data/clues/visions")
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    visions_dir = project_root / args.visions_dir

    # Find all vision files
    vision_files = find_all_vision_yamls(visions_dir)
    print(f"Found {len(vision_files)} vision files\n")

    if not vision_files:
        print("No vision files found!")
        return

    # Generate cards
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    error_count = 0

    for i, vision_file in enumerate(vision_files, 1):
        try:
            vision_data = yaml.safe_load(vision_file.read_text(encoding="utf-8"))
            clue_id = vision_data.get("id", vision_file.stem)
            title = vision_data.get("title", clue_id)
            
            print(f"[{i}/{len(vision_files)}] {clue_id}: {title}")

            # Extract ghost name
            vision_type = vision_data.get("type", "")
            ghost_name = extract_ghost_name(vision_type)
            if not ghost_name:
                print(f"  ⚠️  Skipping: Could not extract ghost name from type '{vision_type}'")
                error_count += 1
                continue

            # Load ghost data
            try:
                ghost_data = load_ghost_data(ghost_name, project_root)
            except Exception as e:
                print(f"  ❌ Error loading ghost data: {e}")
                error_count += 1
                continue

            # Build HTML
            html_content = build_html(vision_data, ghost_data, project_root, args.scale, args.base_url)

            # Output
            suffix = ".html" if args.html_only else ".png"
            output_path = output_dir / f"{clue_id}_card{suffix}"

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

    print(f"\n✅ Generated {success_count}/{len(vision_files)} cards")
    if error_count > 0:
        print(f"❌ {error_count} errors")


if __name__ == "__main__":
    main()

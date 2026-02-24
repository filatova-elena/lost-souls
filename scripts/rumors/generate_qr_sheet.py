#!/usr/bin/env python3
"""
Simple helper to generate QR code print sheets for all rumors.
Uses the existing scripts/qr_codes/print_sheet.py functionality.
"""

import sys
from pathlib import Path
import yaml

# Add qr_codes to path to use existing print_sheet functionality
sys.path.insert(0, str(Path(__file__).parent.parent / "qr_codes"))
from print_sheet import make_print_sheet, parse_color, BASE_URL

# Find project root
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
rumors_dir = project_root / "src" / "_data" / "clues" / "rumors"

# Find all rumor YAML files
rumor_files = sorted(rumors_dir.glob("*.yaml")) + sorted(rumors_dir.glob("*.yml"))

# Load rumor IDs and create (url, label) pairs
codes = []
for rumor_file in rumor_files:
    try:
        data = yaml.safe_load(rumor_file.read_text(encoding="utf-8"))
        if data and data.get("type", "").startswith("Rumor"):
            rumor_id = data.get("id", rumor_file.stem)
            url = f"{BASE_URL}/{rumor_id}/" if BASE_URL.endswith("/clues") else f"{BASE_URL}/clues/{rumor_id}/"
            codes.append((url, str(rumor_id)))
    except Exception:
        continue

if not codes:
    print("No rumor codes found!")
    sys.exit(1)

# Generate print sheet using existing functionality
output_path = project_root / "to_print" / "rumor_qr_codes" / "rumor_qr_sheet.png"
make_print_sheet(
    codes=codes,
    output_path=str(output_path),
    fg_color=parse_color("#4a148c"),
    bg_color=parse_color("white", allow_transparent=True),
)

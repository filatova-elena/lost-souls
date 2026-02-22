#!/usr/bin/env python3
"""
Get list of clue IDs that need QR codes generated.

Rules:
1. Visions don't need separate QR codes (they get vision cards instead)
2. Chains only need the first item in chain to have a QR code

Usage:
    python scripts/get_qr_code_clues.py
    python scripts/get_qr_code_clues.py --output ids.txt
"""

import os
import sys
import yaml
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_all_clues(clues_dir):
    """Load all clue YAML files recursively."""
    clues = {}
    clues_path = project_root / clues_dir
    
    if not clues_path.exists():
        print(f"Error: Clues directory not found: {clues_path}", file=sys.stderr)
        return clues
    
    for yaml_file in clues_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                clue_data = yaml.safe_load(f)
                if clue_data and 'id' in clue_data:
                    clue_id = clue_data['id']
                    clues[clue_id] = {
                        'id': clue_id,
                        'type': clue_data.get('type', ''),
                        'previous_id': clue_data.get('previous_id'),
                        'next_id': clue_data.get('next_id'),
                    }
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}", file=sys.stderr)
    
    return clues

def is_vision(clue):
    """Check if clue is a vision (doesn't need QR code)."""
    clue_type = clue.get('type', '')
    return 'Vision' in clue_type

def is_chain_start(clue):
    """Check if clue is the start of a chain (no previous_id)."""
    return not clue.get('previous_id')

def get_qr_code_clues(clues):
    """Get list of clue IDs that need QR codes."""
    qr_clue_ids = []
    
    for clue_id, clue in clues.items():
        # Rule 1: Skip visions (they get vision cards)
        if is_vision(clue):
            continue
        
        # Rule 2: For chains, only include the first item (no previous_id)
        # If it has a previous_id, it's part of a chain and not the first item
        if clue.get('previous_id'):
            continue
        
        # This clue needs a QR code
        qr_clue_ids.append(clue_id)
    
    return sorted(qr_clue_ids)

def main():
    parser = argparse.ArgumentParser(description='Get list of clue IDs that need QR codes')
    parser.add_argument('--output', '-o', type=str, help='Output file path (default: stdout)')
    args = parser.parse_args()
    
    clues_dir = "src/_data/clues"
    clues = load_all_clues(clues_dir)
    
    if not clues:
        print("No clues found!", file=sys.stderr)
        return 1
    
    qr_clue_ids = get_qr_code_clues(clues)
    
    output_text = '\n'.join(qr_clue_ids)
    
    if args.output:
        output_path = project_root / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"Wrote {len(qr_clue_ids)} clue IDs to {output_path}")
    else:
        print(output_text)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

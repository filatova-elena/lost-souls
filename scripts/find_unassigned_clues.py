#!/usr/bin/env python3
"""
Find clue files that don't have an 'act:' field assigned.

This script scans all clue files and reports which ones are missing the act field.
"""

import os
import sys
import yaml
from pathlib import Path
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CLUES_DIR = PROJECT_ROOT / "src" / "_data" / "clues"


def find_unassigned_clues(clues_dir: Path):
    """
    Find all clue files that don't have an 'act:' field.
    Returns a dict organized by clue type/category.
    """
    unassigned = defaultdict(list)
    
    # Walk through all YAML files in clues directory
    for clue_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            # Read the clue file
            with open(clue_file, 'r', encoding='utf-8') as f:
                content = f.read()
                clue_data = yaml.safe_load(content)
            
            if not clue_data:
                continue
            
            # Check if 'act' field exists
            if 'act' not in clue_data:
                clue_id = clue_data.get('id', 'NO_ID')
                relative_path = clue_file.relative_to(PROJECT_ROOT)
                
                # Determine category from path
                parts = relative_path.parts
                if len(parts) >= 4:
                    category = f"{parts[2]}/{parts[3]}"
                else:
                    category = "unknown"
                
                unassigned[category].append({
                    'id': clue_id,
                    'path': str(relative_path),
                    'type': clue_data.get('type', 'Unknown'),
                    'title': clue_data.get('title') or clue_data.get('name', 'No title')
                })
        
        except Exception as e:
            print(f"Error processing {clue_file.relative_to(PROJECT_ROOT)}: {e}", file=sys.stderr)
    
    return unassigned


def main():
    """Main entry point"""
    print("Scanning clue files for unassigned acts...\n")
    
    unassigned = find_unassigned_clues(CLUES_DIR)
    
    if not unassigned:
        print("✓ All clue files have act assignments!")
        return
    
    total = sum(len(clues) for clues in unassigned.values())
    print(f"Found {total} unassigned clue(s):\n")
    print("="*80)
    
    # Group by category
    for category in sorted(unassigned.keys()):
        clues = unassigned[category]
        print(f"\n{category.upper()} ({len(clues)} unassigned):")
        print("-" * 80)
        
        for clue in clues:
            print(f"  ID: {clue['id']}")
            print(f"  Path: {clue['path']}")
            print(f"  Type: {clue['type']}")
            print(f"  Title: {clue['title']}")
            print()
    
    # Summary by category
    print("\n" + "="*80)
    print("SUMMARY BY CATEGORY:")
    print("="*80)
    for category in sorted(unassigned.keys()):
        print(f"  {category}: {len(unassigned[category])} unassigned")
    
    print(f"\nTotal: {total} unassigned clue(s)")


if __name__ == '__main__':
    main()

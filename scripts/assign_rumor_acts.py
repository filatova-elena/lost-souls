#!/usr/bin/env python3
"""
Assign act fields to rumor files based on clue_organization.yaml

This script:
1. Reads clue_organization.yaml to build a reverse index (rumor_id -> act_key)
2. Scans all rumor files in the rumors directory
3. For each rumor file, checks if its ID is in the index
4. If found, adds an 'act:' field after the 'id:' field
5. Preserves all other fields and formatting
6. If a rumor appears in multiple acts, assigns it to the earliest act (first occurrence)
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RUMORS_DIR = PROJECT_ROOT / "src" / "_data" / "rumors"
ORGANIZATION_FILE = PROJECT_ROOT / "src" / "_data" / "refs" / "clue_organization.yaml"

# Act order for determining earliest appearance
ACT_ORDER = [
    'act_i_setting',
    'act_ii_mystery_emerges',
    'act_iii_investigation',
    'act_iv_revelation',
    'act_v_conclusions'
]


def build_rumor_to_act_index(org_file: Path) -> Dict[str, str]:
    """
    Build a reverse index mapping rumor_id -> act_key from clue_organization.yaml
    If a rumor appears in multiple acts, assign it to the earliest one.
    """
    with open(org_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    index = {}
    
    # Iterate through all acts in order
    for act_key in ACT_ORDER:
        if act_key not in data:
            continue
        
        act_data = data[act_key]
        
        # Iterate through all sections in the act
        for section_key, section_data in act_data.items():
            # Skip metadata fields
            if section_key in ['name', 'purpose', 'constraints', 'notes']:
                continue
            
            # Handle atmospheric section (doesn't have rumors, skip)
            if section_key == 'atmospheric':
                continue
            
            # Handle regular sections (list of plot points)
            if isinstance(section_data, list):
                for plot_point in section_data:
                    if isinstance(plot_point, dict) and 'rumors' in plot_point:
                        for rumor_id in plot_point['rumors']:
                            # Only assign if not already assigned (earliest act wins)
                            if rumor_id not in index:
                                index[rumor_id] = act_key
    
    return index


def find_insertion_point(lines: list) -> int:
    """
    Find where to insert the 'act:' field.
    For rumors, insert after 'id:' field.
    Returns the line index after which to insert.
    """
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('id:'):
            return i
    
    # Fallback: insert after first line
    return 0


def add_act_to_rumor_file(rumor_file: Path, act_key: str, dry_run: bool = False) -> bool:
    """
    Add 'act:' field to a rumor file.
    Returns True if the file was modified (or would be modified in dry_run).
    """
    with open(rumor_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check if act field already exists
    for line in lines:
        if line.strip().startswith('act:'):
            # Already has act field, check if it matches
            existing_act = line.strip().split(':', 1)[1].strip()
            if existing_act == act_key:
                return False  # Already correct, no change needed
            else:
                # Act field exists but is different - we'll update it
                break
    
    # Find insertion point (after id:)
    insert_after = find_insertion_point(lines)
    
    # Determine indentation (match the line we're inserting after)
    if insert_after < len(lines):
        base_line = lines[insert_after]
        # Count leading spaces
        indent = len(base_line) - len(base_line.lstrip())
    else:
        indent = 0
    
    # Create the act line
    act_line = ' ' * indent + f'act: {act_key}\n'
    
    # Insert the line
    lines.insert(insert_after + 1, act_line)
    
    if not dry_run:
        with open(rumor_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return True


def update_existing_act_field(rumor_file: Path, act_key: str, dry_run: bool = False) -> bool:
    """
    Update an existing 'act:' field in a rumor file.
    Returns True if the file was modified.
    """
    with open(rumor_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        if line.strip().startswith('act:'):
            # Update the act field
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + f'act: {act_key}\n'
            modified = True
            break
    
    if modified and not dry_run:
        with open(rumor_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return modified


def process_rumor_files(rumors_dir: Path, index: Dict[str, str], dry_run: bool = False):
    """
    Process all rumor files and assign acts based on the index.
    """
    stats = {
        'processed': 0,
        'assigned': 0,
        'updated': 0,
        'not_found': 0,
        'errors': 0
    }
    
    not_found_rumors = []
    
    # Walk through all YAML files in rumors directory
    for rumor_file in sorted(rumors_dir.glob('rumor_*.yaml')):
        try:
            # Read the rumor file to get its ID
            with open(rumor_file, 'r', encoding='utf-8') as f:
                rumor_data = yaml.safe_load(f)
            
            if not rumor_data or 'id' not in rumor_data:
                continue
            
            rumor_id = rumor_data['id']
            stats['processed'] += 1
            
            # Check if this rumor ID is in our index
            if rumor_id in index:
                act_key = index[rumor_id]
                
                # Check if act field already exists
                has_act = 'act' in rumor_data
                
                if has_act:
                    # Update existing act field
                    if update_existing_act_field(rumor_file, act_key, dry_run):
                        stats['updated'] += 1
                        if not dry_run:
                            print(f"Updated: {rumor_file.name} -> {act_key}")
                else:
                    # Add new act field
                    if add_act_to_rumor_file(rumor_file, act_key, dry_run):
                        stats['assigned'] += 1
                        if not dry_run:
                            print(f"Assigned: {rumor_file.name} -> {act_key}")
            else:
                stats['not_found'] += 1
                not_found_rumors.append((rumor_id, rumor_file.name))
        
        except Exception as e:
            stats['errors'] += 1
            print(f"Error processing {rumor_file.name}: {e}", file=sys.stderr)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total rumor files processed: {stats['processed']}")
    print(f"New act fields assigned: {stats['assigned']}")
    print(f"Existing act fields updated: {stats['updated']}")
    print(f"Rumors not found in organization file: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")
    
    if not_found_rumors:
        print(f"\nRumors not found in organization file ({len(not_found_rumors)}):")
        for rumor_id, file_name in sorted(not_found_rumors):
            print(f"  - {rumor_id} ({file_name})")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Assign act fields to rumor files based on clue_organization.yaml'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually modifying files'
    )
    parser.add_argument(
        '--rumors-dir',
        type=Path,
        default=RUMORS_DIR,
        help=f'Path to rumors directory (default: {RUMORS_DIR})'
    )
    parser.add_argument(
        '--org-file',
        type=Path,
        default=ORGANIZATION_FILE,
        help=f'Path to clue_organization.yaml (default: {ORGANIZATION_FILE})'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.org_file.exists():
        print(f"Error: Organization file not found: {args.org_file}", file=sys.stderr)
        sys.exit(1)
    
    if not args.rumors_dir.exists():
        print(f"Error: Rumors directory not found: {args.rumors_dir}", file=sys.stderr)
        sys.exit(1)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")
    
    # Build index
    print(f"Reading organization file: {args.org_file}")
    index = build_rumor_to_act_index(args.org_file)
    print(f"Built index with {len(index)} rumor IDs\n")
    
    # Process files
    print(f"Processing rumor files in: {args.rumors_dir}\n")
    process_rumor_files(args.rumors_dir, index, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

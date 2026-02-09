#!/usr/bin/env python3
"""
Assign act fields to clue files based on clue_organization.yaml

This script:
1. Reads clue_organization.yaml to build a reverse index (clue_id -> act_key)
2. Scans all clue files in the clues directory
3. For each clue file, checks if its ID is in the index
4. If found, adds an 'act:' field after the 'id:' field (or after 'name:' if present)
5. Preserves all other fields and formatting
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CLUES_DIR = PROJECT_ROOT / "src" / "_data" / "clues"
ORGANIZATION_FILE = PROJECT_ROOT / "src" / "_data" / "refs" / "clue_organization.yaml"


def build_clue_to_act_index(org_file: Path) -> Dict[str, str]:
    """
    Build a reverse index mapping clue_id -> act_key from clue_organization.yaml
    """
    with open(org_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    index = {}
    
    # Iterate through all acts
    for act_key, act_data in data.items():
        if not act_key.startswith('act_'):
            continue
        
        # Iterate through all sections in the act
        for section_key, section_data in act_data.items():
            # Skip metadata fields
            if section_key in ['name', 'purpose', 'constraints', 'notes']:
                continue
            
            # Handle atmospheric section (has direct clues array)
            if section_key == 'atmospheric' and isinstance(section_data, dict):
                if 'clues' in section_data:
                    for clue_id in section_data['clues']:
                        index[clue_id] = act_key
                continue
            
            # Handle regular sections (list of plot points)
            if isinstance(section_data, list):
                for plot_point in section_data:
                    if isinstance(plot_point, dict) and 'clues' in plot_point:
                        for clue_id in plot_point['clues']:
                            index[clue_id] = act_key
    
    return index


def find_insertion_point(lines: list) -> int:
    """
    Find where to insert the 'act:' field.
    Prefers after 'name:', then 'title:', then 'id:'.
    Returns the line index after which to insert.
    """
    id_line = None
    name_line = None
    title_line = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('id:'):
            id_line = i
        elif stripped.startswith('name:'):
            name_line = i
        elif stripped.startswith('title:'):
            title_line = i
    
    # Prefer name, then title, then id
    if name_line is not None:
        return name_line
    elif title_line is not None:
        return title_line
    elif id_line is not None:
        return id_line
    
    # Fallback: insert after first line
    return 0


def add_act_to_clue_file(clue_file: Path, act_key: str, dry_run: bool = False) -> bool:
    """
    Add 'act:' field to a clue file.
    Returns True if the file was modified (or would be modified in dry_run).
    """
    with open(clue_file, 'r', encoding='utf-8') as f:
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
    
    # Find insertion point
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
        with open(clue_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return True


def update_existing_act_field(clue_file: Path, act_key: str, dry_run: bool = False) -> bool:
    """
    Update an existing 'act:' field in a clue file.
    Returns True if the file was modified.
    """
    with open(clue_file, 'r', encoding='utf-8') as f:
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
        with open(clue_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return modified


def process_clue_files(clues_dir: Path, index: Dict[str, str], dry_run: bool = False):
    """
    Process all clue files and assign acts based on the index.
    """
    stats = {
        'processed': 0,
        'assigned': 0,
        'updated': 0,
        'not_found': 0,
        'errors': 0
    }
    
    not_found_clues = []
    
    # Walk through all YAML files in clues directory
    for clue_file in clues_dir.rglob('*.yaml'):
        try:
            # Read the clue file to get its ID
            with open(clue_file, 'r', encoding='utf-8') as f:
                clue_data = yaml.safe_load(f)
            
            if not clue_data or 'id' not in clue_data:
                continue
            
            clue_id = clue_data['id']
            stats['processed'] += 1
            
            # Check if this clue ID is in our index
            if clue_id in index:
                act_key = index[clue_id]
                
                # Check if act field already exists
                has_act = 'act' in clue_data
                
                if has_act:
                    # Update existing act field
                    if update_existing_act_field(clue_file, act_key, dry_run):
                        stats['updated'] += 1
                        if not dry_run:
                            print(f"Updated: {clue_file.relative_to(PROJECT_ROOT)} -> {act_key}")
                else:
                    # Add new act field
                    if add_act_to_clue_file(clue_file, act_key, dry_run):
                        stats['assigned'] += 1
                        if not dry_run:
                            print(f"Assigned: {clue_file.relative_to(PROJECT_ROOT)} -> {act_key}")
            else:
                stats['not_found'] += 1
                not_found_clues.append((clue_id, clue_file.relative_to(PROJECT_ROOT)))
        
        except Exception as e:
            stats['errors'] += 1
            print(f"Error processing {clue_file.relative_to(PROJECT_ROOT)}: {e}", file=sys.stderr)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total clue files processed: {stats['processed']}")
    print(f"New act fields assigned: {stats['assigned']}")
    print(f"Existing act fields updated: {stats['updated']}")
    print(f"Clues not found in organization file: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")
    
    if not_found_clues:
        print(f"\nClues not found in organization file ({len(not_found_clues)}):")
        for clue_id, file_path in sorted(not_found_clues)[:20]:  # Show first 20
            print(f"  - {clue_id} ({file_path})")
        if len(not_found_clues) > 20:
            print(f"  ... and {len(not_found_clues) - 20} more")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Assign act fields to clue files based on clue_organization.yaml'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without actually modifying files'
    )
    parser.add_argument(
        '--clues-dir',
        type=Path,
        default=CLUES_DIR,
        help=f'Path to clues directory (default: {CLUES_DIR})'
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
    
    if not args.clues_dir.exists():
        print(f"Error: Clues directory not found: {args.clues_dir}", file=sys.stderr)
        sys.exit(1)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")
    
    # Build index
    print(f"Reading organization file: {args.org_file}")
    index = build_clue_to_act_index(args.org_file)
    print(f"Built index with {len(index)} clue IDs\n")
    
    # Process files
    print(f"Processing clue files in: {args.clues_dir}\n")
    process_clue_files(args.clues_dir, index, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

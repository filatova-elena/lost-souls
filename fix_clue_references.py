#!/usr/bin/env python3
"""
Script to fix clue references in clue_organization.yaml.
Maps old clue names (like 1925_08_15_sebastian_2_2_2_2_2_2_2) to new IDs (like WC2).
"""

import re
from pathlib import Path

def build_writing_lookup():
    """Build a lookup table: (date, number) -> ID"""
    lookup = {}
    writings_dir = Path('src/_data/clues/writings')
    
    for filepath in writings_dir.rglob('*.yaml'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                id_match = re.search(r'^id:\s*(\S+)', content, re.MULTILINE)
                if not id_match:
                    continue
                
                clue_id = id_match.group(1)
                filename = filepath.name
                
                # Extract date and number from filename
                # Pattern: writings_*_NUMBER_DATE_title.yaml
                # Example: writings_cordelia_2_1925_08_15_sebastian.yaml
                num_match = re.search(r'_(\d+)_(\d{4}(?:_\d{2}(?:_\d{2})?)?)', filename)
                if num_match:
                    number = num_match.group(1)
                    date = num_match.group(2)
                    key = (date, number)
                    lookup[key] = clue_id
        except Exception as e:
            print(f"  Error processing {filepath}: {e}")
    
    return lookup

def extract_date_and_number(old_name):
    """Extract date and number from old clue name.
    Examples:
    - 1925_08_15_sebastian_2_2_2_2_2_2_2 -> (1925_08_15, 2)
    - 1920_03_15_first_principles_32_32_32_32_32_32_32 -> (1920_03_15, 32)
    """
    # Remove repeated number pattern at end: _N_N_N -> _N
    cleaned = re.sub(r'_(\d+)(?:_\1)+$', r'_\1', old_name)
    
    # Extract date (YYYY_MM_DD or YYYY)
    date_match = re.match(r'^(\d{4}(?:_\d{2}(?:_\d{2})?)?)', cleaned)
    if not date_match:
        return None, None
    
    date = date_match.group(1)
    remaining = cleaned[len(date):]
    
    # Extract number from end
    num_match = re.search(r'_(\d+)$', remaining)
    if not num_match:
        return None, None
    
    number = num_match.group(1)
    return date, number

def fix_clue_organization():
    """Fix clue references in clue_organization.yaml."""
    org_file = Path('src/_data/refs/clue_organization.yaml')
    
    # Build lookup
    print("Building lookup from writing files...")
    lookup = build_writing_lookup()
    print(f"Found {len(lookup)} writing files with IDs\n")
    
    # Read the organization file
    with open(org_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and replace old-style references
    pattern = r'(\d{4}(?:_\d{2}(?:_\d{2})?)?)_[^:\n]+_(\d+)(?:_\2)+'
    replacements = {}
    
    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            old_name = match.group(0)
            date, number = extract_date_and_number(old_name)
            
            if date and number:
                key = (date, number)
                new_id = lookup.get(key)
                
                if new_id:
                    # Replace the old name with new ID
                    new_line = re.sub(re.escape(old_name), new_id, line)
                    lines[i] = new_line
                    replacements[old_name] = new_id
                    print(f"  {old_name} -> {new_id}")
                else:
                    print(f"  ⚠️  No match for: {old_name} (date={date}, number={number})")
    
    # Write back if we made changes
    if replacements:
        print(f"\nApplied {len(replacements)} replacements")
        with open(org_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Done!")
    else:
        print("No replacements to apply.")

if __name__ == '__main__':
    fix_clue_organization()

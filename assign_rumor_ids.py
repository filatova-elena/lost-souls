#!/usr/bin/env python3
"""
Script to assign IDs (R1, R2, R3, etc.) to all rumor files.
"""

import os
import re
import yaml
from pathlib import Path

def extract_number(filename):
    """Extract the number from rumor filename (e.g., rumor_01 -> 1, rumor_74 -> 74)"""
    match = re.search(r'rumor_(\d+)', filename)
    if match:
        return int(match.group(1))
    return None

def update_rumor_file(filepath, rumor_id):
    """Update a rumor file with the given ID."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check if id already exists
    id_exists = False
    id_line_index = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('id:'):
            id_exists = True
            id_line_index = i
            break
    
    new_id_line = f"id: {rumor_id}\n"
    
    if id_exists:
        # Replace existing id line
        lines[id_line_index] = new_id_line
    else:
        # Add id at the beginning
        lines.insert(0, new_id_line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return id_exists

def main():
    rumors_dir = Path('src/_data/rumors')
    
    # Get all rumor files
    rumor_files = list(rumors_dir.glob('rumor_*.yaml'))
    
    # Sort by number in filename
    rumor_files.sort(key=lambda f: extract_number(f.name) or 0)
    
    print(f"Found {len(rumor_files)} rumor files")
    print("Assigning IDs...\n")
    
    updated_count = 0
    added_count = 0
    
    for filepath in rumor_files:
        file_number = extract_number(filepath.name)
        if file_number is None:
            print(f"Warning: Could not extract number from {filepath.name}, skipping")
            continue
        rumor_id = f"R{file_number}"
        had_id = update_rumor_file(filepath, rumor_id)
        
        if had_id:
            updated_count += 1
            print(f"Updated {filepath.name}: {rumor_id}")
        else:
            added_count += 1
            print(f"Added {filepath.name}: {rumor_id}")
    
    print(f"\nDone! Added {added_count} IDs, updated {updated_count} IDs.")

if __name__ == '__main__':
    main()

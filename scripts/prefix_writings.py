#!/usr/bin/env python3
"""
Add folder-based prefixes to writings files and move number after prefix.
Example: writings/cordelia/1925_08_15_sebastian_2.yaml 
  -> writings_cordelia_2_1925_08_15_sebastian.yaml
Example: writings/thaddeus/diary/1924_07_02_alice_52.yaml
  -> writings_thaddeus_diary_52_1924_07_02_alice.yaml
"""

import os
import re
import shutil
from pathlib import Path

def extract_number_and_base(filename):
    """Extract number from end and base name.
    Returns (number, base_name)
    Example: '1925_08_15_sebastian_2.yaml' -> ('2', '1925_08_15_sebastian')
    """
    name, ext = os.path.splitext(filename)
    
    # Find number at the end: _number
    match = re.search(r'_(\d+)$', name)
    if match:
        number = match.group(1)
        base = name[:match.start()]
        return number, base
    
    # No number found
    return None, name

def get_folder_prefix(filepath, writings_dir):
    """Get prefix from folder structure.
    Example: writings/cordelia/file.yaml -> 'writings_cordelia_'
    Example: writings/thaddeus/diary/file.yaml -> 'writings_thaddeus_diary_'
    """
    # Get relative path from writings directory
    rel_path = os.path.relpath(os.path.dirname(filepath), writings_dir)
    
    # If file is directly in writings/, no subfolder
    if rel_path == '.':
        return 'writings_'
    
    # Replace path separators with underscores
    folder_path = rel_path.replace(os.sep, '_')
    return f'writings_{folder_path}_'

def process_writings_directory(base_dir):
    """Process all writing files."""
    writings_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'writings')
    
    if not os.path.exists(writings_dir):
        print(f"Writings directory not found: {writings_dir}")
        return []
    
    renamed = []
    
    # Walk through all files
    for root, dirs, files in os.walk(writings_dir):
        for file in files:
            if not file.endswith(('.yaml', '.yml')):
                continue
            
            filepath = os.path.join(root, file)
            
            # Extract number and base name
            number, base = extract_number_and_base(file)
            
            if not number:
                print(f"  ⚠️  Skipping {file} (no number found)")
                continue
            
            # Get folder prefix
            prefix = get_folder_prefix(filepath, writings_dir)
            
            # Build new filename: prefix + number + base
            new_filename = f'{prefix}{number}_{base}.yaml'
            new_path = os.path.join(root, new_filename)
            
            # Skip if already correct
            if file == new_filename:
                print(f"  ✓ {file} (already correct)")
                continue
            
            print(f"  → {file} → {new_filename}")
            shutil.move(filepath, new_path)
            renamed.append((filepath, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Prefix Writings Files")
    print("=" * 70)
    print()
    
    renamed = process_writings_directory(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

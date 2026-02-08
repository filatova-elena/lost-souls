#!/usr/bin/env python3
"""
Fix filenames with duplicate numbers like _32_32_32 to just _32
"""

import os
import re
import shutil

def fix_filename(filename):
    """Remove duplicate number patterns from filename."""
    # Remove extension
    name, ext = os.path.splitext(filename)
    
    # Pattern to match: _number_number_number... at the end
    # Replace with just the last _number
    # This handles cases like: name_32_32_32_32 -> name_32
    pattern = r'(_\d+)(\1)+$'
    new_name = re.sub(pattern, r'\1', name)
    
    if new_name != name:
        return f'{new_name}{ext}'
    return filename

def process_directory(directory, recursive=True):
    """Process all YAML files in directory."""
    renamed = []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    old_path = os.path.join(root, file)
                    new_filename = fix_filename(file)
                    if new_filename != file:
                        new_path = os.path.join(root, new_filename)
                        print(f"  → {file} → {new_filename}")
                        shutil.move(old_path, new_path)
                        renamed.append((old_path, new_path))
    else:
        for file in os.listdir(directory):
            if file.endswith(('.yaml', '.yml')):
                old_path = os.path.join(directory, file)
                new_filename = fix_filename(file)
                if new_filename != file:
                    new_path = os.path.join(directory, new_filename)
                    print(f"  → {file} → {new_filename}")
                    shutil.move(old_path, new_path)
                    renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    clues_dir = os.path.join(project_root, 'src', '_data', 'clues')
    
    print("=" * 70)
    print("Fix Duplicate Numbers in Filenames")
    print("=" * 70)
    print()
    
    print(f"Processing clues directory...")
    renamed = process_directory(clues_dir, recursive=True)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

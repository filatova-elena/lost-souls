#!/usr/bin/env python3
"""
Remove id: fields from all clue and rumor YAML files.
"""

import os
import yaml
import re

def remove_id_field(filepath):
    """Remove id: field from a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove lines that start with 'id:' (with optional whitespace)
        new_lines = []
        removed = False
        for line in lines:
            # Match 'id:' at start of line (with optional whitespace)
            if re.match(r'^\s*id\s*:', line):
                removed = True
                continue
            new_lines.append(line)
        
        if removed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def process_directory(directory, recursive=True):
    """Process all YAML files in a directory."""
    removed_count = 0
    file_count = 0
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    filepath = os.path.join(root, file)
                    file_count += 1
                    if remove_id_field(filepath):
                        removed_count += 1
    else:
        for file in os.listdir(directory):
            if file.endswith(('.yaml', '.yml')):
                filepath = os.path.join(directory, file)
                file_count += 1
                if remove_id_field(filepath):
                    removed_count += 1
    
    return file_count, removed_count

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    clues_dir = os.path.join(project_root, 'src', '_data', 'clues')
    rumors_dir = os.path.join(project_root, 'src', '_data', 'rumors')
    
    print("=" * 70)
    print("Remove id: Fields from YAML Files")
    print("=" * 70)
    print()
    
    total_files = 0
    total_removed = 0
    
    # Process clues
    if os.path.exists(clues_dir):
        print(f"Processing clues directory...")
        file_count, removed_count = process_directory(clues_dir, recursive=True)
        total_files += file_count
        total_removed += removed_count
        print(f"  Processed {file_count} files, removed id: from {removed_count} files")
    
    # Process rumors
    if os.path.exists(rumors_dir):
        print(f"\nProcessing rumors directory...")
        file_count, removed_count = process_directory(rumors_dir, recursive=False)
        total_files += file_count
        total_removed += removed_count
        print(f"  Processed {file_count} files, removed id: from {removed_count} files")
    
    print()
    print("=" * 70)
    print(f"✅ Done! Processed {total_files} files, removed id: from {total_removed} files")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

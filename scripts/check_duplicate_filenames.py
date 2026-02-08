#!/usr/bin/env python3
"""
Check for duplicate filenames across clues and rumors directories.
Identifies potential conflicts if we switch to filename-based IDs.
"""

import os
from pathlib import Path
from collections import defaultdict

def get_all_yaml_files(directory):
    """Recursively get all YAML files in a directory."""
    yaml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                full_path = os.path.join(root, file)
                yaml_files.append(full_path)
    return yaml_files

def get_filename_without_extension(filepath):
    """Get filename without extension."""
    return os.path.splitext(os.path.basename(filepath))[0]

def check_duplicates(base_dir):
    """Check for duplicate filenames in clues and rumors."""
    clues_dir = os.path.join(base_dir, 'src', '_data', 'clues')
    rumors_dir = os.path.join(base_dir, 'src', '_data', 'rumors')
    
    # Track filenames and their paths
    filename_to_paths = defaultdict(list)
    
    # Check clues directory
    if os.path.exists(clues_dir):
        print(f"Scanning clues directory: {clues_dir}")
        clue_files = get_all_yaml_files(clues_dir)
        for filepath in clue_files:
            filename = get_filename_without_extension(filepath)
            relative_path = os.path.relpath(filepath, clues_dir)
            filename_to_paths[filename].append(('clues', relative_path))
    
    # Check rumors directory
    if os.path.exists(rumors_dir):
        print(f"Scanning rumors directory: {rumors_dir}")
        rumor_files = get_all_yaml_files(rumors_dir)
        for filepath in rumor_files:
            filename = get_filename_without_extension(filepath)
            relative_path = os.path.relpath(filepath, rumors_dir)
            filename_to_paths[filename].append(('rumors', relative_path))
    
    # Find duplicates
    duplicates = {name: paths for name, paths in filename_to_paths.items() if len(paths) > 1}
    
    return duplicates, len(clue_files) if os.path.exists(clues_dir) else 0, len(rumor_files) if os.path.exists(rumors_dir) else 0

def main():
    # Get project root (assuming script is in scripts/ directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Duplicate Filename Checker")
    print("=" * 70)
    print()
    
    duplicates, clue_count, rumor_count = check_duplicates(project_root)
    
    print(f"Total clue files scanned: {clue_count}")
    print(f"Total rumor files scanned: {rumor_count}")
    print(f"Total unique filenames: {len(set(get_filename_without_extension(f) for f in get_all_yaml_files(os.path.join(project_root, 'src', '_data', 'clues')) + get_all_yaml_files(os.path.join(project_root, 'src', '_data', 'rumors'))))}")
    print()
    
    if duplicates:
        print(f"⚠️  Found {len(duplicates)} duplicate filename(s):")
        print("=" * 70)
        print()
        
        for filename, paths in sorted(duplicates.items()):
            print(f"Filename: {filename}")
            print(f"  Found in {len(paths)} location(s):")
            for category, relative_path in paths:
                print(f"    - {category}/{relative_path}")
            print()
        
        print("=" * 70)
        print(f"❌ CONFLICT: {len(duplicates)} duplicate filename(s) found!")
        print("   Using filename-only IDs would cause conflicts.")
        print("   Recommendation: Use path-based IDs instead.")
        return 1
    else:
        print("=" * 70)
        print("✅ No duplicate filenames found!")
        print("   Filename-based IDs would work without conflicts.")
        return 0

if __name__ == '__main__':
    exit(main())

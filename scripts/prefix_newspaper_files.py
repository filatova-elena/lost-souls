#!/usr/bin/env python3
"""
Prefix all newspaper files with newspaper_
"""

import os
import shutil
from pathlib import Path

def rename_newspaper_files(base_dir):
    """Rename all newspaper files with newspaper_ prefix."""
    newspaper_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'newspaper')
    
    if not os.path.exists(newspaper_dir):
        print(f"Newspaper directory not found: {newspaper_dir}")
        return []
    
    renamed = []
    
    print(f"Processing newspaper/...")
    
    # Get all YAML files in newspaper directory
    for filename in os.listdir(newspaper_dir):
        if not filename.endswith(('.yaml', '.yml')):
            continue
        
        # Skip if already prefixed
        if filename.startswith('newspaper_'):
            print(f"  ✓ {filename} (already prefixed)")
            continue
        
        old_path = os.path.join(newspaper_dir, filename)
        new_filename = f'newspaper_{filename}'
        new_path = os.path.join(newspaper_dir, new_filename)
        
        # Rename the file
        print(f"  → {filename} → {new_filename}")
        shutil.move(old_path, new_path)
        renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Newspaper File Prefix Renamer")
    print("=" * 70)
    print()
    
    renamed = rename_newspaper_files(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

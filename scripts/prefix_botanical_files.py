#!/usr/bin/env python3
"""
Prefix all botanical files with botanical_
"""

import os
import shutil
from pathlib import Path

def rename_botanical_files(base_dir):
    """Rename all botanical files with botanical_ prefix."""
    botanical_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'botanical')
    
    if not os.path.exists(botanical_dir):
        print(f"Botanical directory not found: {botanical_dir}")
        return []
    
    renamed = []
    
    print(f"Processing botanical/...")
    
    # Get all YAML files in botanical directory
    for filename in os.listdir(botanical_dir):
        if not filename.endswith(('.yaml', '.yml')):
            continue
        
        # Skip if already prefixed
        if filename.startswith('botanical_'):
            print(f"  ✓ {filename} (already prefixed)")
            continue
        
        old_path = os.path.join(botanical_dir, filename)
        new_filename = f'botanical_{filename}'
        new_path = os.path.join(botanical_dir, new_filename)
        
        # Rename the file
        print(f"  → {filename} → {new_filename}")
        shutil.move(old_path, new_path)
        renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Botanical File Prefix Renamer")
    print("=" * 70)
    print()
    
    renamed = rename_botanical_files(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

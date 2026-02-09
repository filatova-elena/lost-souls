#!/usr/bin/env python3
"""
Prefix all vision files with vision_{character}_ pattern.
Files already prefixed with character name just get vision_ added.
"""

import os
import shutil
from pathlib import Path

def get_character_from_path(filepath):
    """Extract character name from path like visions/cordelia/file.yaml"""
    parts = Path(filepath).parts
    if 'visions' in parts:
        idx = parts.index('visions')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None

def get_new_filename(old_filename, character):
    """Generate new filename with vision_{character}_ prefix."""
    # Remove extension
    name, ext = os.path.splitext(old_filename)
    
    # Check if filename already starts with character name
    if name.startswith(f'{character}_'):
        # Just add vision_ prefix
        new_name = f'vision_{name}'
    else:
        # Add vision_{character}_ prefix
        new_name = f'vision_{character}_{name}'
    
    return f'{new_name}{ext}'

def rename_vision_files(base_dir):
    """Rename all vision files with appropriate prefix."""
    visions_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'visions')
    
    if not os.path.exists(visions_dir):
        print(f"Visions directory not found: {visions_dir}")
        return []
    
    renamed = []
    
    # Process each character subdirectory
    for character_dir in os.listdir(visions_dir):
        character_path = os.path.join(visions_dir, character_dir)
        
        if not os.path.isdir(character_path):
            continue
        
        print(f"Processing {character_dir}/...")
        
        # Get all YAML files in this character's directory
        for filename in os.listdir(character_path):
            if not filename.endswith(('.yaml', '.yml')):
                continue
            
            old_path = os.path.join(character_path, filename)
            new_filename = get_new_filename(filename, character_dir)
            new_path = os.path.join(character_path, new_filename)
            
            # Skip if already renamed
            if filename == new_filename:
                print(f"  ✓ {filename} (already correct)")
                continue
            
            # Rename the file
            print(f"  → {filename} → {new_filename}")
            shutil.move(old_path, new_path)
            renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Vision File Prefix Renamer")
    print("=" * 70)
    print()
    
    renamed = rename_vision_files(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""
Prefix all artifact files with artifact_
Handles both root artifacts/ directory and legacy/ subdirectory.
"""

import os
import shutil
from pathlib import Path

def rename_artifact_files(base_dir):
    """Rename all artifact files with artifact_ prefix."""
    artifacts_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'artifacts')
    
    if not os.path.exists(artifacts_dir):
        print(f"Artifacts directory not found: {artifacts_dir}")
        return []
    
    renamed = []
    
    def process_directory(directory, prefix=""):
        """Recursively process directory and subdirectories."""
        print(f"Processing {prefix}artifacts/...")
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                # Recursively process subdirectories
                process_directory(item_path, prefix=f"{prefix}{item}/")
            elif item.endswith(('.yaml', '.yml')):
                # Skip if already prefixed
                if item.startswith('artifact_'):
                    print(f"  ✓ {prefix}{item} (already prefixed)")
                    continue
                
                new_filename = f'artifact_{item}'
                new_path = os.path.join(directory, new_filename)
                
                # Rename the file
                print(f"  → {prefix}{item} → {prefix}{new_filename}")
                shutil.move(item_path, new_path)
                renamed.append((item_path, new_path))
    
    process_directory(artifacts_dir)
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Artifact File Prefix Renamer")
    print("=" * 70)
    print()
    
    renamed = rename_artifact_files(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

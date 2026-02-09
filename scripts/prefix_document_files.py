#!/usr/bin/env python3
"""
Prefix all document files with document_
"""

import os
import shutil
from pathlib import Path

def rename_document_files(base_dir):
    """Rename all document files with document_ prefix."""
    documents_dir = os.path.join(base_dir, 'src', '_data', 'clues', 'documents')
    
    if not os.path.exists(documents_dir):
        print(f"Documents directory not found: {documents_dir}")
        return []
    
    renamed = []
    
    print(f"Processing documents/...")
    
    # Get all YAML files in documents directory
    for filename in os.listdir(documents_dir):
        if not filename.endswith(('.yaml', '.yml')):
            continue
        
        # Skip if already prefixed
        if filename.startswith('document_'):
            print(f"  ✓ {filename} (already prefixed)")
            continue
        
        old_path = os.path.join(documents_dir, filename)
        new_filename = f'document_{filename}'
        new_path = os.path.join(documents_dir, new_filename)
        
        # Rename the file
        print(f"  → {filename} → {new_filename}")
        shutil.move(old_path, new_path)
        renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("Document File Prefix Renamer")
    print("=" * 70)
    print()
    
    renamed = rename_document_files(project_root)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

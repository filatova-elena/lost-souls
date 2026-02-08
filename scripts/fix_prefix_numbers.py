#!/usr/bin/env python3
"""
Fix filenames to move number after the full prefix.
Examples:
- document_122_legal_birth_cert_sebastian.yaml -> document_legal_122_birth_cert_sebastian.yaml
- vision_151_cordelia_character_doctor.yaml -> vision_cordelia_151_character_doctor.yaml
- botanical_114_jar_vanilla.yaml -> botanical_jar_114_vanilla.yaml
"""

import os
import re
import shutil

def fix_document_filename(filename):
    """Fix document filename format.
    Current: document_NUMBER_TYPE_rest.yaml
    Target: document_TYPE_NUMBER_rest.yaml
    Document types are single words: business, financial, legal, medical
    """
    name, ext = os.path.splitext(filename)
    
    # Pattern: document_NUMBER_TYPE_rest
    # Type is a single word (business, financial, legal, medical)
    match = re.match(r'^document_(\d+)_([a-z]+)_(.+)$', name)
    if match:
        number = match.group(1)
        doc_type = match.group(2)
        rest = match.group(3)
        new_name = f'document_{doc_type}_{number}_{rest}'
        return f'{new_name}{ext}'
    
    return filename

def fix_vision_filename(filename):
    """Fix vision filename format.
    Current: vision_NUMBER_character_rest.yaml
    Target: vision_character_NUMBER_rest.yaml
    """
    name, ext = os.path.splitext(filename)
    
    # Pattern: vision_NUMBER_character_rest
    match = re.match(r'^vision_(\d+)_([a-z]+)_(.+)$', name)
    if match:
        number = match.group(1)
        character = match.group(2)
        rest = match.group(3)
        new_name = f'vision_{character}_{number}_{rest}'
        return f'{new_name}{ext}'
    
    return filename

def fix_botanical_filename(filename):
    """Fix botanical filename format.
    Current: botanical_NUMBER_type_rest.yaml
    Target: botanical_type_NUMBER_rest.yaml
    """
    name, ext = os.path.splitext(filename)
    
    # Pattern: botanical_NUMBER_type_rest
    # Types could be: jar, ingredient, etc.
    match = re.match(r'^botanical_(\d+)_([a-z_]+)_(.+)$', name)
    if match:
        number = match.group(1)
        bot_type = match.group(2)
        rest = match.group(3)
        new_name = f'botanical_{bot_type}_{number}_{rest}'
        return f'{new_name}{ext}'
    
    return filename

def process_directory(directory, fix_func, dir_name):
    """Process all files in directory."""
    renamed = []
    
    if not os.path.exists(directory):
        print(f"  ⚠️  Directory not found: {directory}")
        return renamed
    
    for file in os.listdir(directory):
        if not file.endswith(('.yaml', '.yml')):
            continue
        
        old_path = os.path.join(directory, file)
        new_filename = fix_func(file)
        
        if new_filename != file:
            new_path = os.path.join(directory, new_filename)
            print(f"  → {file} → {new_filename}")
            shutil.move(old_path, new_path)
            renamed.append((old_path, new_path))
    
    return renamed

def process_visions_recursive(directory):
    """Process vision files recursively (they're in subdirectories)."""
    renamed = []
    
    if not os.path.exists(directory):
        print(f"  ⚠️  Directory not found: {directory}")
        return renamed
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith(('.yaml', '.yml')):
                continue
            
            filepath = os.path.join(root, file)
            new_filename = fix_vision_filename(file)
            
            if new_filename != file:
                new_path = os.path.join(root, new_filename)
                print(f"  → {file} → {new_filename}")
                shutil.move(filepath, new_path)
                renamed.append((filepath, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    clues_dir = os.path.join(project_root, 'src', '_data', 'clues')
    
    print("=" * 70)
    print("Fix Prefix Numbers (Documents, Visions, Botanical)")
    print("=" * 70)
    print()
    
    total_renamed = 0
    
    # Documents
    print("Processing documents...")
    docs_dir = os.path.join(clues_dir, 'documents')
    renamed = process_directory(docs_dir, fix_document_filename, 'documents')
    total_renamed += len(renamed)
    print(f"  ✅ Renamed {len(renamed)} document file(s)")
    print()
    
    # Visions (recursive)
    print("Processing visions...")
    visions_dir = os.path.join(clues_dir, 'visions')
    renamed = process_visions_recursive(visions_dir)
    total_renamed += len(renamed)
    print(f"  ✅ Renamed {len(renamed)} vision file(s)")
    print()
    
    # Botanical
    print("Processing botanical...")
    botanical_dir = os.path.join(clues_dir, 'botanical')
    renamed = process_directory(botanical_dir, fix_botanical_filename, 'botanical')
    total_renamed += len(renamed)
    print(f"  ✅ Renamed {len(renamed)} botanical file(s)")
    print()
    
    print("=" * 70)
    print(f"✅ Total: Renamed {total_renamed} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

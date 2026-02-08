#!/usr/bin/env python3
"""
Fix artifact filenames to move number after type prefix.
Example: artifact_78_object_blood_specs.yaml -> artifact_object_78_blood_specs.yaml
"""

import os
import re
import shutil

def fix_artifact_filename(filename):
    """Fix artifact filename format.
    Current: artifact_78_object_blood_specs.yaml
    Target: artifact_object_78_blood_specs.yaml
    """
    name, ext = os.path.splitext(filename)
    
    # Pattern: artifact_NUMBER_TYPE_rest
    # We want: artifact_TYPE_NUMBER_rest
    match = re.match(r'^artifact_(\d+)_(object|photo|painting)_(.+)$', name)
    if match:
        number = match.group(1)
        artifact_type = match.group(2)
        rest = match.group(3)
        new_name = f'artifact_{artifact_type}_{number}_{rest}'
        return f'{new_name}{ext}'
    
    # If it doesn't match, return as is
    return filename

def process_directory(directory):
    """Process all artifact files."""
    renamed = []
    
    for file in os.listdir(directory):
        if not file.endswith(('.yaml', '.yml')):
            continue
        
        old_path = os.path.join(directory, file)
        new_filename = fix_artifact_filename(file)
        
        if new_filename != file:
            new_path = os.path.join(directory, new_filename)
            print(f"  → {file} → {new_filename}")
            shutil.move(old_path, new_path)
            renamed.append((old_path, new_path))
    
    return renamed

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    artifacts_dir = os.path.join(project_root, 'src', '_data', 'clues', 'artifacts')
    
    if not os.path.exists(artifacts_dir):
        print(f"Artifacts directory not found: {artifacts_dir}")
        return 1
    
    print("=" * 70)
    print("Fix Artifact Filenames")
    print("=" * 70)
    print()
    
    print(f"Processing artifacts directory...")
    renamed = process_directory(artifacts_dir)
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

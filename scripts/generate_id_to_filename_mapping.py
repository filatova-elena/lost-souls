#!/usr/bin/env python3
"""
Generate mapping from old id fields to new fileName (filename without extension).
This helps update clue_organization.yaml and quest files.
"""

import os
import yaml
from pathlib import Path

def get_all_yaml_files(directory):
    """Recursively get all YAML files."""
    yaml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def generate_mapping(base_dir):
    """Generate id -> fileName mapping."""
    clues_dir = os.path.join(base_dir, 'src', '_data', 'clues')
    rumors_dir = os.path.join(base_dir, 'src', '_data', 'rumors')
    
    mapping = {
        'clues': {},
        'rumors': {}
    }
    
    # Process clues
    if os.path.exists(clues_dir):
        for filepath in get_all_yaml_files(clues_dir):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'id' in data:
                        old_id = data['id']
                        fileName = os.path.splitext(os.path.basename(filepath))[0]
                        mapping['clues'][old_id] = fileName
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    # Process rumors
    if os.path.exists(rumors_dir):
        for filepath in get_all_yaml_files(rumors_dir):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'id' in data:
                        old_id = data['id']
                        fileName = os.path.splitext(os.path.basename(filepath))[0]
                        mapping['rumors'][old_id] = fileName
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    return mapping

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print("=" * 70)
    print("ID to fileName Mapping Generator")
    print("=" * 70)
    print()
    
    mapping = generate_mapping(project_root)
    
    # Save to file
    output_file = os.path.join(project_root, 'scripts', 'id_to_filename_mapping.yaml')
    with open(output_file, 'w') as f:
        yaml.dump(mapping, f, default_flow_style=False, sort_keys=True)
    
    print(f"✅ Generated mapping:")
    print(f"   Clues: {len(mapping['clues'])} mappings")
    print(f"   Rumors: {len(mapping['rumors'])} mappings")
    print(f"   Saved to: {output_file}")
    print()
    
    # Show some examples
    print("Sample clue mappings:")
    for i, (old_id, fileName) in enumerate(list(mapping['clues'].items())[:5]):
        print(f"  {old_id} → {fileName}")
    if len(mapping['clues']) > 5:
        print(f"  ... and {len(mapping['clues']) - 5} more")
    
    return 0

if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""
Update clue references in clue_organization.yaml and quest files.
Replaces old id values with fileName values from the mapping.
"""

import os
import yaml
import re
from pathlib import Path

def load_mapping(mapping_file):
    """Load the id to fileName mapping."""
    with open(mapping_file, 'r') as f:
        return yaml.safe_load(f)

def update_yaml_file(filepath, mapping):
    """Update clue references in a YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        original_content = content
    
    # Load YAML to preserve structure
    data = yaml.safe_load(content)
    if not data:
        return False, 0
    
    updated = False
    count = 0
    
    def replace_in_value(value, mapping):
        """Recursively replace clue IDs in YAML values."""
        nonlocal updated, count
        
        if isinstance(value, dict):
            for k, v in value.items():
                if k == 'clues' and isinstance(v, list):
                    # Replace clue IDs in clues array
                    new_list = []
                    for item in v:
                        if isinstance(item, str) and item in mapping['clues']:
                            new_list.append(mapping['clues'][item])
                            updated = True
                            count += 1
                        else:
                            new_list.append(item)
                    value[k] = new_list
                elif k == 'rumors' and isinstance(v, list):
                    # Replace rumor IDs in rumors array
                    new_list = []
                    for item in v:
                        if isinstance(item, str) and item in mapping['rumors']:
                            new_list.append(mapping['rumors'][item])
                            updated = True
                            count += 1
                        else:
                            new_list.append(item)
                    value[k] = new_list
                else:
                    replace_in_value(v, mapping)
        elif isinstance(value, list):
            for item in value:
                replace_in_value(item, mapping)
    
    replace_in_value(data, mapping)
    
    if updated:
        # Write back with preserved formatting where possible
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return True, count
    
    return False, 0

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    mapping_file = os.path.join(script_dir, 'id_to_filename_mapping.yaml')
    if not os.path.exists(mapping_file):
        print(f"Error: Mapping file not found: {mapping_file}")
        print("Run generate_id_to_filename_mapping.py first")
        return 1
    
    mapping = load_mapping(mapping_file)
    
    print("=" * 70)
    print("Update Clue References")
    print("=" * 70)
    print()
    
    # Update clue_organization.yaml
    org_file = os.path.join(project_root, 'src', '_data', 'refs', 'clue_organization.yaml')
    if os.path.exists(org_file):
        print(f"Updating {org_file}...")
        updated, count = update_yaml_file(org_file, mapping)
        if updated:
            print(f"  ✅ Updated {count} clue/rumor references")
        else:
            print(f"  ℹ️  No updates needed")
    else:
        print(f"  ⚠️  File not found: {org_file}")
    
    # Update quest files
    quests_dir = os.path.join(project_root, 'src', '_data', 'quests')
    if os.path.exists(quests_dir):
        print(f"\nUpdating quest files in {quests_dir}...")
        quest_count = 0
        total_updates = 0
        for filename in os.listdir(quests_dir):
            if filename.endswith(('.yaml', '.yml')):
                quest_file = os.path.join(quests_dir, filename)
                updated, count = update_yaml_file(quest_file, mapping)
                if updated:
                    quest_count += 1
                    total_updates += count
                    print(f"  ✅ {filename}: {count} references updated")
        
        if quest_count > 0:
            print(f"\n  ✅ Updated {quest_count} quest file(s) with {total_updates} total references")
        else:
            print(f"  ℹ️  No quest files needed updates")
    
    print()
    print("=" * 70)
    print("✅ Done!")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

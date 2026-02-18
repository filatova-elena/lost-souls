#!/usr/bin/env python3
"""Check for duplicate clue IDs across all clue YAML files."""

import yaml
from pathlib import Path
from collections import defaultdict

def check_duplicate_clue_ids():
    clues_dir = Path('src/_data/clues')
    clue_ids = defaultdict(list)
    
    for yaml_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'id' not in data:
                continue
            
            clue_id = data['id']
            clue_ids[clue_id].append(yaml_file)
        
        except Exception as e:
            print(f"❌ Error reading {yaml_file}: {e}")
    
    duplicates = {clue_id: files for clue_id, files in clue_ids.items() if len(files) > 1}
    
    if duplicates:
        print("❌ Found duplicate clue IDs:")
        for clue_id, files in sorted(duplicates.items()):
            print(f"\n  ID: {clue_id} (appears {len(files)} times)")
            for file in files:
                print(f"    - {file}")
        return False
    else:
        print(f"✅ All clue IDs are unique ({len(clue_ids)} clues checked)")
        return True

if __name__ == '__main__':
    success = check_duplicate_clue_ids()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""Check that all clue YAML files have is_key as an array (even if empty)."""

import yaml
from pathlib import Path

def check_clue_is_key():
    clues_dir = Path('src/_data/clues')
    issues = []
    
    for yaml_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            # Check if is_key field exists
            if 'is_key' not in data:
                # is_key is optional, so missing is okay
                continue
            
            # Check if is_key is an array
            if not isinstance(data['is_key'], list):
                issues.append(f"{yaml_file}: 'is_key' is not an array (type: {type(data['is_key']).__name__}, value: {data['is_key']})")
        
        except Exception as e:
            issues.append(f"{yaml_file}: Error reading file - {e}")
    
    if issues:
        print("❌ Found issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ All clue files with 'is_key' have it as an array")
        return True

if __name__ == '__main__':
    success = check_clue_is_key()
    exit(0 if success else 1)

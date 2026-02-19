#!/usr/bin/env python3
"""Check that all clues have valid act names."""

import yaml
from pathlib import Path

# Valid act names
VALID_ACTS = {
    'act_prologue',
    'act_i_setting',
    'act_ii_mystery_emerges',
    'act_iii_investigation',
    'act_iv_revelation'
}

def check_clue_acts():
    clues_dir = Path('src/_data/clues')
    issues = []
    
    for yaml_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            clue_id = data.get('id', 'Unknown')
            clue_act = data.get('act')
            
            if clue_act is None:
                issues.append(f"{yaml_file}: Clue '{clue_id}' is missing 'act' field")
            elif clue_act not in VALID_ACTS:
                issues.append(
                    f"{yaml_file}: Clue '{clue_id}' has invalid act '{clue_act}' "
                    f"(valid acts: {', '.join(sorted(VALID_ACTS))})"
                )
        
        except Exception as e:
            issues.append(f"{yaml_file}: Error reading file - {e}")
    
    if issues:
        print("❌ Found clues with invalid or missing act names:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        clue_count = len(list(clues_dir.rglob('*.yaml')))
        print(f"✅ All clues have valid act names ({clue_count} clues checked)")
        return True

if __name__ == '__main__':
    success = check_clue_acts()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""Check that all clue YAML files have skills as an array (even if empty).
   Automatically adds 'skills: []' after 'hashtags' if missing."""

import yaml
import re
from pathlib import Path

def add_skills_field(file_path):
    """Add skills: [] field after hashtags in a YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find hashtags section
    hashtags_idx = None
    hashtags_end_idx = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('hashtags:'):
            hashtags_idx = i
            # Find where hashtags list ends (next non-indented line or empty line followed by non-indented)
            j = i + 1
            while j < len(lines):
                stripped = lines[j].strip()
                if not stripped:  # Empty line
                    j += 1
                    continue
                if stripped.startswith('-') or (stripped.startswith('#') and j == i + 1):
                    # Still in hashtags list or comment right after hashtags:
                    j += 1
                else:
                    # Found next field
                    break
            hashtags_end_idx = j
            break
    
    if hashtags_idx is None:
        # No hashtags field - find a good place to add skills
        # Look for common fields before content
        insert_after_fields = ['act', 'date', 'appearance', 'location']
        insert_idx = None
        
        for field in insert_after_fields:
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{field}:'):
                    # Find end of this field (could be single line or multi-line)
                    j = i + 1
                    while j < len(lines):
                        stripped = lines[j].strip()
                        if not stripped or stripped.startswith('#'):
                            j += 1
                            continue
                        # Check if next line is indented (continues this field) or starts new field
                        if lines[j].startswith(' ') and not lines[j].startswith('  '):
                            # Single space indent - continuation of this field
                            j += 1
                        else:
                            break
                    insert_idx = j
                    break
            if insert_idx is not None:
                break
        
        if insert_idx is None:
            # Fallback: insert after 'act' field or at line 5
            for i, line in enumerate(lines):
                if line.strip().startswith('act:'):
                    insert_idx = i + 1
                    break
            if insert_idx is None:
                insert_idx = min(5, len(lines))
    else:
        # Insert after hashtags section
        insert_idx = hashtags_end_idx
    
    # Insert skills: [] with proper formatting
    indent = '  ' if insert_idx > 0 and lines[insert_idx - 1].startswith('  ') else ''
    skills_line = f"{indent}skills: []\n"
    
    # Make sure there's a blank line before if the previous line isn't empty
    if insert_idx > 0 and lines[insert_idx - 1].strip() and not lines[insert_idx - 1].strip().startswith('#'):
        lines.insert(insert_idx, skills_line)
    else:
        lines.insert(insert_idx, skills_line)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def check_and_fix_clue_skills():
    clues_dir = Path('src/_data/clues')
    issues = []
    fixed = []
    
    for yaml_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            # Check if skills field exists
            if 'skills' not in data:
                print(f"Adding skills: [] to {yaml_file}")
                add_skills_field(yaml_file)
                fixed.append(yaml_file)
                continue
            
            # Check if skills is an array
            if not isinstance(data['skills'], list):
                issues.append(f"{yaml_file}: 'skills' is not an array (type: {type(data['skills']).__name__}, value: {data['skills']})")
        
        except Exception as e:
            issues.append(f"{yaml_file}: Error reading file - {e}")
    
    if fixed:
        print(f"\n✅ Fixed {len(fixed)} files by adding 'skills: []'")
    
    if issues:
        print("\n❌ Found issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ All clue files have 'skills' as an array")
        return True

if __name__ == '__main__':
    success = check_and_fix_clue_skills()
    exit(0 if success else 1)

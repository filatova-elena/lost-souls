#!/usr/bin/env python3
"""Check that clue content fields are multiline (YAML block scalars)."""

import re
import yaml
from pathlib import Path

# Fields that should be multiline
CONTENT_FIELDS = ['content', 'narrative', 'narration', 'appearance']

def check_multiline_in_yaml(yaml_file):
    """Check if content fields are multiline block scalars in the raw YAML."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines(True)
    
    issues = []
    
    # Find all content field definitions using regex
    for field in CONTENT_FIELDS:
        # Pattern to find field definition line
        pattern = rf'^{re.escape(field)}:\s*(.*)$'
        
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                value_part = match.group(1).strip()
                
                # Check if it uses block scalar syntax (| or >)
                if value_part.startswith('|') or value_part.startswith('>'):
                    continue  # It's a block scalar, good
                
                # Check if it's a quoted string (single or double quotes)
                if value_part.startswith('"') or value_part.startswith("'"):
                    issues.append((field, i + 1, "quoted string (should use block scalar | or >)"))
                    continue
                
                # Check if value is on the same line (not a block scalar)
                if value_part and not value_part.startswith('|') and not value_part.startswith('>'):
                    # Check if next line is a block scalar indicator
                    if i + 1 < len(lines):
                        next_line_stripped = lines[i + 1].strip()
                        if next_line_stripped.startswith('|') or next_line_stripped.startswith('>'):
                            continue  # Next line is block scalar, good
                    
                    # If value is on same line and not empty, it's likely single-line
                    if value_part:
                        issues.append((field, i + 1, "single-line value (should use block scalar | or >)"))
                else:
                    # Field defined but value on next line - check if it's a block scalar
                    if i + 1 < len(lines):
                        next_line_stripped = lines[i + 1].strip()
                        if not (next_line_stripped.startswith('|') or next_line_stripped.startswith('>')):
                            # Check if it's indented content (multiline but not block scalar)
                            if lines[i + 1].startswith('  ') and not lines[i + 1].strip().startswith('-'):
                                issues.append((field, i + 1, "multiline but not using block scalar syntax (| or >)"))
    
    return issues

def check_clue_multiline_content():
    """Check all clues for multiline content fields."""
    clues_dir = Path('src/_data/clues')
    all_issues = []
    
    for yaml_file in sorted(clues_dir.rglob('*.yaml')):
        try:
            # First load to see if field exists
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            clue_id = data.get('id', 'Unknown')
            
            # Check which content fields exist
            has_content_fields = any(field in data for field in CONTENT_FIELDS)
            if not has_content_fields:
                continue  # Skip clues without content fields
            
            # Check multiline formatting
            issues = check_multiline_in_yaml(yaml_file)
            
            if issues:
                for field, line_num, reason in issues:
                    all_issues.append((yaml_file, clue_id, field, line_num, reason))
        
        except Exception as e:
            all_issues.append((yaml_file, 'Unknown', 'ERROR', 0, f"Error reading file: {e}"))
    
    if all_issues:
        print("❌ Found clues with non-multiline content fields:")
        for yaml_file, clue_id, field, line_num, reason in all_issues:
            if field == 'ERROR':
                print(f"  {yaml_file}: {reason}")
            else:
                print(f"  {yaml_file}: Clue '{clue_id}' - {field} field (line {line_num}): {reason}")
        return False
    else:
        clue_count = len(list(clues_dir.rglob('*.yaml')))
        print(f"✅ All clue content fields are multiline ({clue_count} clues checked)")
        return True

if __name__ == '__main__':
    success = check_clue_multiline_content()
    exit(0 if success else 1)

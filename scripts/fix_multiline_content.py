#!/usr/bin/env python3
"""Convert clue content fields to multiline block scalar format."""

import re
from pathlib import Path

# Fields that should be multiline
CONTENT_FIELDS = ['content', 'narrative', 'narration', 'appearance']

def extract_quoted_string(lines, start_idx, quote_char):
    """Extract a quoted string that may span multiple lines."""
    # Get the first line
    first_line = lines[start_idx]
    field_match = re.match(rf'^(\w+):\s*{re.escape(quote_char)}(.*)$', first_line)
    if not field_match:
        return None, start_idx
    
    field_name = field_match.group(1)
    value_start = field_match.group(2)
    
    # Check if quote closes on same line
    if value_start.endswith(quote_char):
        # Single line
        content = value_start[:-1]  # Remove closing quote
        # Unescape
        if quote_char == '"':
            content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
        else:
            content = content.replace("''", "'")
        return content, start_idx + 1
    
    # Multi-line - collect until we find closing quote
    content_parts = [value_start]
    i = start_idx + 1
    
    while i < len(lines):
        line = lines[i]
        content_parts.append(line)
        
        # Check if this line has the closing quote
        if quote_char in line:
            # Find the last quote (not escaped)
            for j in range(len(line) - 1, -1, -1):
                if line[j] == quote_char and (j == 0 or line[j-1] != '\\'):
                    # Found closing quote
                    # Remove everything after the quote
                    content_parts[-1] = line[:j]
                    # Join and unescape
                    full_content = ''.join(content_parts)
                    if quote_char == '"':
                        full_content = full_content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                    else:
                        full_content = full_content.replace("''", "'")
                    return full_content, i + 1
        i += 1
    
    # Quote never closed - return what we have
    full_content = ''.join(content_parts)
    if quote_char == '"':
        full_content = full_content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
    else:
        full_content = full_content.replace("''", "'")
    return full_content, i

def extract_indented_value(lines, start_idx):
    """Extract an indented value that spans multiple lines."""
    content_lines = []
    i = start_idx
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Stop if we hit a non-indented line that's not empty
        if not line.startswith('  ') and stripped:
            break
        # Stop if we hit a list item
        if stripped.startswith('-'):
            break
        # Stop if we hit another field definition
        if re.match(r'^[a-z_]+:', stripped):
            break
        
        # Add the content (remove the 2-space indent)
        if line.startswith('  '):
            content_lines.append(line[2:].rstrip('\n'))
        elif stripped == '':
            content_lines.append('')
        
        i += 1
    
    return '\n'.join(content_lines), i

def fix_yaml_file(yaml_file_path, dry_run=True):
    """Fix a single YAML file by converting content fields to block scalars."""
    # Read the file
    with open(yaml_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changes_made = []
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        matched = False
        
        # Check if this line defines a content field
        for field in CONTENT_FIELDS:
            pattern = rf'^{re.escape(field)}:\s*(.*)$'
            match = re.match(pattern, line)
            
            if match:
                value_part = match.group(1).strip()
                
                # Check if it's already a block scalar
                if value_part.startswith('|') or value_part.startswith('>'):
                    new_lines.append(line)
                    i += 1
                    matched = True
                    break
                
                # Extract the actual content based on format
                content = None
                next_idx = i + 1
                
                # Check if it's a quoted string
                if value_part.startswith('"') or value_part.startswith("'"):
                    quote_char = value_part[0]
                    content, next_idx = extract_quoted_string(lines, i, quote_char)
                elif value_part:
                    # Value on same line
                    content = value_part
                    # Check if it continues on next lines
                    if next_idx < len(lines) and lines[next_idx].startswith('  ') and not lines[next_idx].strip().startswith('-'):
                        # Multi-line value
                        continuation, next_idx = extract_indented_value(lines, next_idx)
                        content = content + '\n' + continuation
                else:
                    # Value on next lines
                    content, next_idx = extract_indented_value(lines, next_idx)
                
                if content is not None:
                    # Convert to block scalar
                    new_lines.append(f"{field}: |\n")
                    
                    # Write the content with proper indentation
                    if content:
                        for content_line in content.split('\n'):
                            new_lines.append(f"  {content_line}\n")
                    else:
                        new_lines.append(f"  \n")
                    
                    i = next_idx
                    matched = True
                    changes_made.append(f"  {field}: converted to block scalar")
                    break
        
        if not matched:
            new_lines.append(line)
            i += 1
    
    new_content = ''.join(new_lines)
    
    if dry_run:
        return new_content, changes_made
    else:
        # Write the file
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return None, changes_made

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 fix_multiline_content.py <yaml_file> [--apply]")
        print("  --apply: Actually modify the file (default is dry-run)")
        sys.exit(1)
    
    yaml_file = Path(sys.argv[1])
    apply_changes = '--apply' in sys.argv
    
    if not yaml_file.exists():
        print(f"Error: File not found: {yaml_file}")
        sys.exit(1)
    
    print(f"{'DRY RUN - ' if not apply_changes else ''}Processing: {yaml_file}")
    print("-" * 60)
    
    if apply_changes:
        _, changes = fix_yaml_file(yaml_file, dry_run=False)
    else:
        new_content, changes = fix_yaml_file(yaml_file, dry_run=True)
        print("NEW CONTENT:")
        print("=" * 60)
        print(new_content)
        print("=" * 60)
    
    if changes:
        print("\nChanges that would be made:")
        for change in changes:
            print(change)
    else:
        print("\nNo changes needed - file already uses block scalars")

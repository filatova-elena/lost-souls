#!/usr/bin/env python3
"""Add location to artifact and writing clues that don't have one."""

import yaml
import hashlib
from pathlib import Path

# Location assignment rules:
# - Act 1: always 1st Floor
# - Act 2: 70% on 1st Floor, but if key clue then 100% on 1st Floor
# - Act 3: 70% on 2nd Floor, 30% on 1st Floor

def is_key_clue(clue_data):
    """Check if a clue is a key clue (has is_key field with values)."""
    is_key = clue_data.get('is_key')
    if isinstance(is_key, list):
        return len(is_key) > 0
    elif is_key:
        return True
    return False

def get_location_for_clue(clue_data, clue_id):
    """Determine location based on act and key status."""
    act = clue_data.get('act', '')
    is_key = is_key_clue(clue_data)
    
    # Act 1: always 1st Floor
    if act == 'act_i_setting':
        return '1st Floor'
    
    # Act 2: 70% on 1st Floor, but if key clue then 100% on 1st Floor
    elif act == 'act_ii_mystery_emerges':
        if is_key:
            return '1st Floor'
        else:
            # Use hash of clue ID for deterministic 70/30 split
            hash_val = int(hashlib.md5(clue_id.encode()).hexdigest(), 16)
            if (hash_val % 10) < 7:  # 70% chance
                return '1st Floor'
            else:
                return '2nd Floor'
    
    # Act 3: 70% on 2nd Floor, 30% on 1st Floor
    elif act == 'act_iii_investigation':
        # Use hash of clue ID for deterministic 70/30 split
        hash_val = int(hashlib.md5(clue_id.encode()).hexdigest(), 16)
        if (hash_val % 10) < 7:  # 70% chance
            return '2nd Floor'
        else:
            return '1st Floor'
    
    # For other acts, don't assign (shouldn't happen based on requirements)
    return None

def add_locations_to_clues():
    """Add locations to artifact and writing clues missing them."""
    clues_dir = Path('src/_data/clues')
    
    # Find all artifact and writing clue files
    artifact_files = list(clues_dir.glob('artifacts/*.yaml'))
    writing_files = list(clues_dir.glob('writings/**/*.yaml'))
    
    all_files = artifact_files + writing_files
    updated_count = 0
    
    for yaml_file in sorted(all_files):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)
            
            if not data:
                continue
            
            clue_id = data.get('id', 'Unknown')
            
            # Skip if location already exists
            if 'location' in data and data['location']:
                continue
            
            # Get location based on act and key status
            location = get_location_for_clue(data, clue_id)
            
            if location:
                # Add location field after the 'act' field
                lines = content.split('\n')
                new_lines = []
                location_added = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    # Look for 'act:' line and add location after it
                    if not location_added and line.strip().startswith('act:'):
                        # Add location on next line with same indentation
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + f'location: {location}')
                        location_added = True
                
                # If act field not found, try to add after other fields
                if not location_added:
                    new_lines = []
                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        # Try to add after 'type:' or 'id:' (but only near the top)
                        if not location_added and i < 10:
                            if line.strip().startswith('type:'):
                                indent = len(line) - len(line.lstrip())
                                new_lines.append(' ' * indent + f'location: {location}')
                                location_added = True
                            elif line.strip().startswith('id:') and i < 3:
                                indent = len(line) - len(line.lstrip())
                                new_lines.append(' ' * indent + f'location: {location}')
                                location_added = True
                
                if location_added:
                    # Write back
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                
                print(f"✅ Added location '{location}' to {yaml_file.name} (ID: {clue_id}, Act: {data.get('act')}, Key: {is_key_clue(data)})")
                updated_count += 1
        
        except Exception as e:
            print(f"❌ Error processing {yaml_file}: {e}")
    
    print(f"\n✅ Updated {updated_count} clue files with locations")
    return updated_count

if __name__ == '__main__':
    add_locations_to_clues()

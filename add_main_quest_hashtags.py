#!/usr/bin/env python3
"""
Add main_quest to hashtags for all clues that have main_quest in is_key.
This ensures data consistency.
"""

import os
import yaml
from pathlib import Path

def process_clue_file(filepath):
    """Process a single clue YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False
        
        # Check if main_quest is in is_key
        is_key = data.get('is_key', [])
        if not is_key:
            return False
        
        # Handle both array and single value
        if isinstance(is_key, str):
            has_main_quest = is_key == 'main_quest'
        elif isinstance(is_key, list):
            has_main_quest = 'main_quest' in is_key
        else:
            return False
        
        if not has_main_quest:
            return False
        
        # Get or create hashtags
        hashtags = data.get('hashtags', [])
        if not isinstance(hashtags, list):
            hashtags = [hashtags] if hashtags else []
        
        # Add main_quest if not already present
        if 'main_quest' not in hashtags:
            hashtags.append('main_quest')
            data['hashtags'] = hashtags
            
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            return True
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False
    
    return False

def main():
    clues_dir = Path('src/_data/clues')
    if not clues_dir.exists():
        print(f"Error: {clues_dir} does not exist")
        return
    
    updated_count = 0
    total_files = 0
    
    # Walk through all YAML files in clues directory
    for root, dirs, files in os.walk(clues_dir):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                filepath = Path(root) / file
                total_files += 1
                
                if process_clue_file(filepath):
                    updated_count += 1
                    print(f"Updated: {filepath.relative_to(clues_dir)}")
    
    print(f"\nDone! Updated {updated_count} out of {total_files} clue files.")

if __name__ == '__main__':
    main()

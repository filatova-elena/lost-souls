#!/usr/bin/env python3
"""
Fix old-style clue references in quest files.
Maps patterns like "1925_08_01_cordelia_34_34_34_34_34_34_34" to "writings_sebastian_34_1925_08_01_cordelia"
"""

import os
import re
import yaml
from pathlib import Path

def build_clue_lookup(clues_dir):
    """Build a lookup from old-style references to new filenames."""
    lookup = {}
    
    # Pattern: {date}_{title}_{number}_{number}... -> writings_{character}_{number}_{date}_{title}
    # Also handle: sebastian_elixir_formula_42_42_42... -> writings_sebastian_42_sebastian_elixir_formula
    
    for filepath in Path(clues_dir).rglob('*.yaml'):
        filename_stem = filepath.stem
        
        # Extract number from filename
        number_match = re.search(r'_(\d+)_', filename_stem)
        if not number_match:
            continue
        number = number_match.group(1)
        
        # For writings, extract character and date/title
        if '/writings/' in str(filepath):
            path_parts = filepath.parts
            writings_idx = None
            for i, part in enumerate(path_parts):
                if part == 'writings':
                    writings_idx = i
                    break
            
            if writings_idx is not None and writings_idx + 1 < len(path_parts):
                character = path_parts[writings_idx + 1]
                
                # Check for subfolder (diary, patient_notes, etc.)
                has_subfolder = writings_idx + 2 < len(path_parts) - 1
                
                # Build old-style reference patterns
                # Pattern 1: {date}_{title}_{number}_{number}... (for files with subfolders like diary, patient_notes)
                # writings_thaddeus_diary_52_1924_07_02_alice -> 1924_07_02_alice_52_52_52_52_52_52_52
                if has_subfolder:
                    subfolder = path_parts[writings_idx + 2]
                    match = re.match(rf'writings_{character}_{subfolder}_{number}_(.+)$', filename_stem)
                    if match:
                        date_title = match.group(1)
                        old_ref = f"{date_title}_{number}_{number}_{number}_{number}_{number}_{number}_{number}"
                        lookup[old_ref] = filename_stem
                
                # Pattern 2: {date}_{title}_{number}_{number}... (for files without subfolders)
                # writings_sebastian_34_1925_08_01_cordelia -> 1925_08_01_cordelia_34_34_34_34_34_34_34
                if not has_subfolder:
                    match = re.match(rf'writings_{character}_{number}_(.+)$', filename_stem)
                    if match:
                        date_title = match.group(1)
                        old_ref = f"{date_title}_{number}_{number}_{number}_{number}_{number}_{number}_{number}"
                        lookup[old_ref] = filename_stem
                
                # Pattern 3: {title}_{number}_{number}... (for files like sebastian_elixir_formula_42)
                # writings_sebastian_42_sebastian_elixir_formula -> sebastian_elixir_formula_42_42_42_42_42_42_42
                match = re.match(rf'writings_{character}_{number}_(.+)$', filename_stem)
                if match:
                    title_part = match.group(1)
                    # If it doesn't start with a date, it's a title-only pattern
                    if not re.match(r'\d{4}_\d{2}_\d{2}', title_part):
                        old_ref = f"{title_part}_{number}_{number}_{number}_{number}_{number}_{number}_{number}"
                        lookup[old_ref] = filename_stem
                
                # Special cases
                if filename_stem == "writings_sebastian_42_sebastian_elixir_formula":
                    lookup["sebastian_elixir_formula_42_42_42_42_42_42_42"] = filename_stem
                
                if filename_stem == "writings_thaddeus_notes_71_thaddeus_foxglove_request":
                    lookup["thaddeus_foxglove_request_71_71_71_71_71_71_71"] = filename_stem
    
    return lookup

def update_quest_file(quest_filepath, lookup):
    """Update a quest file with correct clue references."""
    with open(quest_filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacements = 0
    
    # Find all old-style references
    for old_ref, new_ref in lookup.items():
        # Replace in YAML list format: "    - old_ref"
        pattern = re.compile(r'^(\s+)-\s+' + re.escape(old_ref) + r'$', re.MULTILINE)
        matches = pattern.findall(content)
        if matches:
            content = pattern.sub(r'\1- ' + new_ref, content)
            replacements += len(matches)
            print(f"  {old_ref} -> {new_ref} ({len(matches)} replacements)")
    
    if content != original_content:
        with open(quest_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return replacements
    return 0

def main():
    base_dir = Path(__file__).parent
    clues_dir = base_dir / 'src' / '_data' / 'clues'
    quests_dir = base_dir / 'src' / '_data' / 'quests'
    
    print("Building clue lookup...")
    lookup = build_clue_lookup(clues_dir)
    print(f"Found {len(lookup)} clue mappings\n")
    
    print("Updating quest files...")
    total_replacements = 0
    for quest_file in sorted(quests_dir.glob('*.yaml')):
        print(f"\n{quest_file.name}:")
        replacements = update_quest_file(quest_file, lookup)
        total_replacements += replacements
        if replacements == 0:
            print("  No changes needed")
    
    print(f"\nDone! Made {total_replacements} total replacements.")

if __name__ == '__main__':
    main()

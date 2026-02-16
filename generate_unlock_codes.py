#!/usr/bin/env python3
"""
Generate random unlock codes for all clues.
Each unlock code is a string of 4 unique symbol indices (0-7) that players must select
to unlock shared clues.
"""

import os
import secrets
import yaml
from pathlib import Path


def generate_unlock_code():
    """
    Generate a random unlock code: 4 unique indices from 0-7.
    Uses cryptographically secure randomness.
    Returns a string like "0257".
    """
    # Generate 4 unique random indices from 0-7, sorted for consistency
    indices = sorted(secrets.SystemRandom().sample(range(8), 4))
    # Convert to string like "0257"
    return ''.join(str(i) for i in indices)


def process_clue_file(filepath, force_regenerate=False):
    """
    Process a single clue YAML file.
    Adds or updates the unlock_code field.
    
    Args:
        filepath: Path to the clue YAML file
        force_regenerate: If True, regenerate even if unlock_code already exists
    
    Returns:
        tuple: (updated: bool, clue_id: str or None)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False, None
        
        clue_id = data.get('id', 'UNKNOWN')
        
        # Check if unlock_code already exists
        if 'unlock_code' in data and not force_regenerate:
            return False, clue_id
        
        # Generate new unlock code
        unlock_code = generate_unlock_code()
        data['unlock_code'] = unlock_code
        
        # Write back to file, preserving formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True, clue_id
    
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return False, None


def main():
    clues_dir = Path('src/_data/clues')
    if not clues_dir.exists():
        print(f"Error: {clues_dir} does not exist")
        return
    
    updated_count = 0
    skipped_count = 0
    total_files = 0
    errors = []
    
    print("Generating unlock codes for all clues...")
    print("=" * 60)
    
    # Walk through all YAML files in clues directory
    for root, dirs, files in os.walk(clues_dir):
        for file in sorted(files):
            if file.endswith(('.yaml', '.yml')):
                filepath = Path(root) / file
                total_files += 1
                
                updated, clue_id = process_clue_file(filepath)
                
                if updated:
                    updated_count += 1
                    rel_path = filepath.relative_to(clues_dir)
                    print(f"✓ {clue_id:8s} | {rel_path}")
                elif clue_id:
                    skipped_count += 1
                else:
                    errors.append(str(filepath.relative_to(clues_dir)))
    
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Total clue files: {total_files}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped (already has code): {skipped_count}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors:
            print(f"    - {err}")
    
    if updated_count > 0:
        print(f"\n✓ Successfully generated unlock codes for {updated_count} clues!")
    else:
        print("\nNo files were updated. All clues already have unlock codes.")
        print("Use --force flag to regenerate all codes.")


if __name__ == '__main__':
    import sys
    
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if force:
        print("WARNING: --force flag detected. This will regenerate ALL unlock codes.")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
        
        # Update process_clue_file calls to use force_regenerate
        clues_dir = Path('src/_data/clues')
        updated_count = 0
        
        for root, dirs, files in os.walk(clues_dir):
            for file in sorted(files):
                if file.endswith(('.yaml', '.yml')):
                    filepath = Path(root) / file
                    updated, clue_id = process_clue_file(filepath, force_regenerate=True)
                    if updated:
                        updated_count += 1
                        rel_path = filepath.relative_to(clues_dir)
                        print(f"✓ Regenerated: {clue_id:8s} | {rel_path}")
        
        print(f"\n✓ Regenerated unlock codes for {updated_count} clues!")
    else:
        main()

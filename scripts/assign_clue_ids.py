#!/usr/bin/env python3
"""
Assign IDs to all clue files based on the established pattern:
- Artifacts: A + type (O/P/PH) + number
- Botanical: B + type (G/H/J) + number  
- Newspaper: N + number
- Documents: D + type (B/F/L/M) + number
- Visions: V + character (A/C/S) + number
- Writings: W + folder prefix letters + number (handling conflicts)
"""

import os
import re
from pathlib import Path

def extract_number_from_filename(filename, filepath=''):
    """Extract number from filename.
    Pattern: prefix_{number}_rest
    For writings: writings_{character}_{subfolder?}_{number}_{date}...
    For others: type_{subtype}_{number}_rest
    """
    # For writings, the number comes after the character/subfolder name
    if '/writings/' in filepath:
        # Get the folder structure to determine prefix length
        path_parts = Path(filepath).parts
        writings_idx = None
        for i, part in enumerate(path_parts):
            if part == 'writings':
                writings_idx = i
                break
        
        if writings_idx is not None:
            # Build the expected prefix from folder structure
            # writings/cordelia/ -> writings_cordelia_
            # writings/thaddeus/patient_notes/ -> writings_thaddeus_patient_notes_
            folder_parts = []
            for i in range(writings_idx + 1, len(path_parts) - 1):  # Exclude filename
                folder_parts.append(path_parts[i])
            prefix = 'writings_' + '_'.join(folder_parts) + '_'
            
            # Remove prefix from filename to get remaining part
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext.startswith(prefix):
                remaining = name_without_ext[len(prefix):]
                # First number should be the clue number
                match = re.match(r'^(\d+)_', remaining)
                if match:
                    return match.group(1)
    
    # For other types, find number after type prefix
    # artifact_object_78_... -> 78
    # botanical_garden_103_... -> 103
    # document_legal_122_... -> 122
    match = re.search(r'_(\d+)_', filename)
    if match:
        return match.group(1)
    return None

def get_artifact_id(filename, number):
    """Get artifact ID: AO83, AP87, APH88"""
    if '_object_' in filename:
        return f'AO{number}'
    elif '_painting_' in filename:
        return f'AP{number}'
    elif '_photo_' in filename:
        return f'APH{number}'
    return None

def get_botanical_id(filename, number):
    """Get botanical ID: BG103, BH107, BJ110"""
    if '_garden_' in filename:
        return f'BG{number}'
    elif '_herb_' in filename:
        return f'BH{number}'
    elif '_jar_' in filename:
        return f'BJ{number}'
    return None

def get_newspaper_id(filename, number):
    """Get newspaper ID: N133"""
    return f'N{number}'

def get_document_id(filename, number):
    """Get document ID: DB115, DF118, DL122, DM126"""
    if '_business_' in filename:
        return f'DB{number}'
    elif '_financial_' in filename:
        return f'DF{number}'
    elif '_legal_' in filename:
        return f'DL{number}'
    elif '_medical_' in filename:
        return f'DM{number}'
    elif filename.startswith('document_prenup_'):
        return f'DL{number}'  # Prenup is legal
    return None

def get_vision_id(filename, number):
    """Get vision ID: VA136, VC150, VS..."""
    if filename.startswith('vision_alice_'):
        return f'VA{number}'
    elif filename.startswith('vision_cordelia_'):
        return f'VC{number}'
    elif filename.startswith('vision_sebastian_'):
        return f'VS{number}'
    return None

def get_writing_id(filepath, filename, number):
    """Get writing ID based on folder structure.
    Examples:
    - writings/cordelia/writings_cordelia_2_... -> WC2
    - writings/sebastian/writings_sebastian_32_... -> WSB32
    - writings/thaddeus/patient_notes/writings_thaddeus_patient_notes_77_... -> WTPN77
    - writings/eleanor/writings_eleanor_13_... -> WEL13 (to avoid conflict with Elias)
    - writings/elias/writings_elias_20_... -> WEI20 (to avoid conflict with Eleanor)
    - writings/silas/writings_silas_... -> WSI... (to avoid conflict with Sebastian)
    """
    # Extract path parts
    path_parts = Path(filepath).parts if isinstance(filepath, Path) else Path(filepath).parts
    
    writings_idx = None
    for i, part in enumerate(path_parts):
        if part == 'writings':
            writings_idx = i
            break
    
    if writings_idx is None or writings_idx + 1 >= len(path_parts):
        return None
    
    # Get character folder (the folder directly under 'writings')
    character = path_parts[writings_idx + 1]
    
    # Handle conflicts by using more letters
    if character == 'eleanor':
        char_code = 'EL'
    elif character == 'elias':
        char_code = 'EI'
    elif character == 'sebastian':
        char_code = 'SB'
    elif character == 'silas':
        char_code = 'SI'
    else:
        # Use first letter of character name
        char_code = character[0].upper()
    
    # Check for subfolder (folder under character folder)
    if writings_idx + 2 < len(path_parts) - 1:  # -1 to exclude filename
        subfolder = path_parts[writings_idx + 2]
        # Get first letter of each word in subfolder name
        sub_code = ''.join([word[0].upper() for word in subfolder.split('_')])
        return f'W{char_code}{sub_code}{number}'
    else:
        # No subfolder, just character
        return f'W{char_code}{number}'

def process_clue_file(filepath):
    """Process a single clue file and add ID if missing."""
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Check if already has ID and if it's correct
    expected_id = None
    has_id = False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            id_match = re.search(r'^id:\s*(\S+)', content, re.MULTILINE)
            if id_match:
                has_id = True
                existing_id = id_match.group(1)
                # We'll calculate expected_id later and compare
    except Exception as e:
        print(f"  ⚠️  Error reading {filepath}: {e}")
        return None
    
    # Extract number from filename
    number = extract_number_from_filename(name_without_ext, filepath)
    if not number:
        print(f"  ⚠️  Could not extract number from {filename}")
        return None
    
    # Determine ID based on file location
    clue_id = None
    if '/artifacts/' in filepath:
        clue_id = get_artifact_id(name_without_ext, number)
    elif '/botanical/' in filepath:
        clue_id = get_botanical_id(name_without_ext, number)
    elif '/newspaper/' in filepath:
        clue_id = get_newspaper_id(name_without_ext, number)
    elif '/documents/' in filepath:
        clue_id = get_document_id(name_without_ext, number)
    elif '/visions/' in filepath:
        clue_id = get_vision_id(name_without_ext, number)
    elif '/writings/' in filepath:
        clue_id = get_writing_id(filepath, name_without_ext, number)
    
    if not clue_id:
        print(f"  ⚠️  Could not determine ID for {filename}")
        return None
    
    # Check if ID already exists and is correct
    if has_id:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            id_match = re.search(r'^id:\s*(\S+)', content, re.MULTILINE)
            if id_match and id_match.group(1) == clue_id:
                return None  # Already has correct ID
        except:
            pass
    
    # Add or replace ID in file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check if ID line exists and replace it
        id_replaced = False
        for i, line in enumerate(lines):
            if re.match(r'^id:', line):
                lines[i] = f'id: {clue_id}\n'
                id_replaced = True
                break
        
        if not id_replaced:
            # Find where to insert ID (after first non-empty, non-comment line or at top)
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    insert_pos = i
                    break
            
            # Insert ID
            lines.insert(insert_pos, f'id: {clue_id}\n')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return clue_id
    except Exception as e:
        print(f"  ⚠️  Error writing {filepath}: {e}")
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    clues_dir = os.path.join(project_root, 'src', '_data', 'clues')
    
    print("=" * 70)
    print("Assign IDs to Clue Files")
    print("=" * 70)
    print()
    
    assigned = []
    skipped = []
    errors = []
    
    for root, dirs, files in os.walk(clues_dir):
        for file in files:
            if not file.endswith(('.yaml', '.yml')):
                continue
            
            filepath = os.path.join(root, file)
            clue_id = process_clue_file(filepath)
            
            if clue_id:
                print(f"  ✓ {file} → {clue_id}")
                assigned.append((file, clue_id))
            elif clue_id is None and 'Could not' in str(clue_id):
                errors.append(file)
            else:
                skipped.append(file)
    
    print()
    print("=" * 70)
    print(f"✅ Assigned {len(assigned)} ID(s)")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} file(s) (already had IDs)")
    if errors:
        print(f"❌ Errors: {len(errors)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

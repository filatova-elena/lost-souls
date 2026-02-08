#!/usr/bin/env python3
"""
Fix document filenames that were incorrectly renamed.
Current wrong format: document_financial_bank_118_statements.yaml
Correct format: document_financial_118_bank_statements.yaml
"""

import os
import re
import shutil

def fix_incorrect_document_filename(filename):
    """Fix incorrectly formatted document filenames.
    Wrong: document_TYPE_word_NUMBER_rest.yaml
    Correct: document_TYPE_NUMBER_word_rest.yaml
    """
    name, ext = os.path.splitext(filename)
    
    # Pattern: document_TYPE_word_NUMBER_rest (wrong format)
    # Types: business, financial, legal, medical
    match = re.match(r'^document_(business|financial|legal|medical)_([a-z_]+)_(\d+)_(.+)$', name)
    if match:
        doc_type = match.group(1)
        word = match.group(2)
        number = match.group(3)
        rest = match.group(4)
        new_name = f'document_{doc_type}_{number}_{word}_{rest}'
        return f'{new_name}{ext}'
    
    return filename

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    docs_dir = os.path.join(project_root, 'src', '_data', 'clues', 'documents')
    
    print("=" * 70)
    print("Fix Incorrectly Formatted Document Filenames")
    print("=" * 70)
    print()
    
    renamed = []
    for file in os.listdir(docs_dir):
        if not file.endswith(('.yaml', '.yml')):
            continue
        
        old_path = os.path.join(docs_dir, file)
        new_filename = fix_incorrect_document_filename(file)
        
        if new_filename != file:
            new_path = os.path.join(docs_dir, new_filename)
            print(f"  → {file} → {new_filename}")
            shutil.move(old_path, new_path)
            renamed.append((old_path, new_path))
    
    print()
    print("=" * 70)
    print(f"✅ Renamed {len(renamed)} file(s)")
    print("=" * 70)
    
    return 0

if __name__ == '__main__':
    exit(main())

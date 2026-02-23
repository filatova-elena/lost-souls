#!/usr/bin/env python3
"""Check that story gate clues exist and are valid."""

import yaml
from pathlib import Path

def load_all_clues():
    """Load all clues and index by ID."""
    clues_dir = Path('src/_data/clues')
    clues_by_id = {}
    
    for yaml_file in clues_dir.rglob('*.yaml'):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'id' not in data:
                continue
            
            clue_id = data['id']
            clues_by_id[clue_id] = data
        except Exception as e:
            print(f"⚠️  Error reading {yaml_file}: {e}")
    
    return clues_by_id

def check_story_gates():
    """Check that all story gate clues exist and are valid."""
    # Load story gates
    story_gates_file = Path('src/_data/refs/story_gates.yaml')
    with open(story_gates_file, 'r', encoding='utf-8') as f:
        story_gates = yaml.safe_load(f)
    
    # Load all clues
    clues_by_id = load_all_clues()
    
    issues = []
    
    for gate_key, gate_data in story_gates.items():
        gate_name = gate_data.get('name', gate_key)
        gate_clues = gate_data.get('clues', [])
        
        if not gate_clues:
            issues.append(f"Gate '{gate_name}' ({gate_key}) has no clues listed")
            continue
        
        for clue_id in gate_clues:
            # Check if clue exists
            if clue_id not in clues_by_id:
                issues.append(f"Gate '{gate_name}' ({gate_key}): Clue ID '{clue_id}' does not exist")
                continue
            
            clue = clues_by_id[clue_id]
            clue_title = clue.get('title', 'Unknown')
            clue_act = clue.get('act', 'Unknown')
            
            # Note: Gate clues are typically in earlier acts, so we don't check act match
            # Just verify the clue exists and log its details for reference
            print(f"  ✓ Gate '{gate_name}': Clue '{clue_id}' ({clue_title}) exists (act: {clue_act})")
    
    if issues:
        print("❌ Found issues with story gates:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ All story gate clues are valid")
        print(f"   Checked {len(story_gates)} gates with {sum(len(g.get('clues', [])) for g in story_gates.values())} clue references")
        return True

if __name__ == '__main__':
    success = check_story_gates()
    exit(0 if success else 1)

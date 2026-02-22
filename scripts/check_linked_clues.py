#!/usr/bin/env python3
"""
Check that all linked clues (with previous_id/next_id) are in the same act
and have the same set of skills.

Usage:
    python scripts/check_linked_clues.py
"""

import os
import sys
import yaml
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_all_clues(clues_dir):
    """Load all clue YAML files recursively."""
    clues = {}
    clues_path = project_root / clues_dir
    
    if not clues_path.exists():
        print(f"Error: Clues directory not found: {clues_path}")
        return clues
    
    for yaml_file in clues_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                clue_data = yaml.safe_load(f)
                if clue_data and 'id' in clue_data:
                    clue_id = clue_data['id']
                    clues[clue_id] = {
                        'id': clue_id,
                        'file': str(yaml_file.relative_to(project_root)),
                        'act': clue_data.get('act'),
                        'skills': set(clue_data.get('skills', [])),
                        'previous_id': clue_data.get('previous_id'),
                        'next_id': clue_data.get('next_id'),
                        'type': clue_data.get('type', ''),
                        'title': clue_data.get('title', ''),
                    }
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}")
    
    return clues

def find_linked_chains(clues):
    """Find all chains of linked clues."""
    chains = []
    processed = set()
    
    # Find all clues that are linked (have previous_id or next_id)
    linked_clue_ids = set()
    for clue_id, clue in clues.items():
        if clue.get('previous_id') or clue.get('next_id'):
            linked_clue_ids.add(clue_id)
    
    # Build chains starting from clues with no previous_id
    for clue_id in linked_clue_ids:
        if clue_id in processed:
            continue
        
        # Check if this is a chain start (no previous_id)
        clue = clues.get(clue_id)
        if not clue:
            continue
        
        if clue.get('previous_id'):
            # Not a chain start, skip
            continue
        
        # Build chain from this starting point
        chain = []
        current_id = clue_id
        
        while current_id and current_id in clues:
            if current_id in processed:
                # Circular reference or already processed
                break
            
            processed.add(current_id)
            current_clue = clues[current_id]
            chain.append(current_id)
            
            # Move to next
            current_id = current_clue.get('next_id')
        
        if chain:
            chains.append(chain)
    
    # Check for orphaned clues (have previous_id but previous doesn't exist, or have next_id but next doesn't exist)
    orphaned = []
    for clue_id, clue in clues.items():
        if clue.get('previous_id') and clue['previous_id'] not in clues:
            orphaned.append((clue_id, f"previous_id {clue['previous_id']} not found"))
        if clue.get('next_id') and clue['next_id'] not in clues:
            orphaned.append((clue_id, f"next_id {clue['next_id']} not found"))
    
    return chains, orphaned

def check_chain_consistency(clues, chain):
    """Check that all clues in a chain have the same act and skills."""
    if len(chain) < 2:
        return None, None  # Single clue chains are fine
    
    acts = set()
    skills_sets = []
    
    for clue_id in chain:
        clue = clues.get(clue_id)
        if not clue:
            continue
        
        if clue.get('act'):
            acts.add(clue['act'])
        
        skills_sets.append(clue.get('skills', set()))
    
    # Check if all acts are the same
    act_issue = None
    if len(acts) > 1:
        act_issue = f"Multiple acts found: {sorted(acts)}"
    
    # Check if all skills sets are the same
    skills_issue = None
    if skills_sets:
        first_skills = skills_sets[0]
        for i, skills in enumerate(skills_sets[1:], 1):
            if skills != first_skills:
                skills_issue = f"Skills mismatch: {chain[0]} has {sorted(first_skills)}, {chain[i]} has {sorted(skills)}"
                break
    
    return act_issue, skills_issue

def main():
    clues_dir = "src/_data/clues"
    clues = load_all_clues(clues_dir)
    
    if not clues:
        print("No clues found!")
        return 1
    
    print(f"Loaded {len(clues)} clues\n")
    
    # Find linked chains
    chains, orphaned = find_linked_chains(clues)
    
    print(f"Found {len(chains)} linked chains\n")
    
    # Check each chain
    issues = []
    for chain in chains:
        if len(chain) < 2:
            continue
        
        act_issue, skills_issue = check_chain_consistency(clues, chain)
        
        if act_issue or skills_issue:
            chain_info = []
            for clue_id in chain:
                clue = clues[clue_id]
                chain_info.append(f"  {clue_id} ({clue.get('act', 'no act')}) - {clue['file']}")
            
            issue_msg = f"Chain: {' → '.join(chain)}\n"
            issue_msg += "\n".join(chain_info)
            
            if act_issue:
                issue_msg += f"\n  ❌ ACT ISSUE: {act_issue}"
            if skills_issue:
                issue_msg += f"\n  ❌ SKILLS ISSUE: {skills_issue}"
            
            issues.append(issue_msg)
    
    # Report orphaned clues
    if orphaned:
        print("⚠️  ORPHANED CLUES (broken links):")
        for clue_id, reason in orphaned:
            clue = clues.get(clue_id)
            file_path = clue['file'] if clue else 'unknown'
            print(f"  {clue_id} ({file_path}): {reason}")
        print()
    
    # Report issues
    if issues:
        print("❌ ISSUES FOUND:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}\n")
        return 1
    else:
        print("✅ All linked clue chains are consistent!")
        print(f"   - All clues in each chain have the same act")
        print(f"   - All clues in each chain have the same skills")
        return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Rebuild the `is_key` field across all clue YAML files based on track definitions.

For each clue in src/_data/quests/track_*.yaml `clue_chain`, set its `is_key`
to the list of track IDs it appears in. Remove `is_key` from every other clue.

Preserves line-level formatting by editing the text rather than re-dumping YAML.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
QUESTS_DIR = ROOT / "src/_data/quests"
CLUES_DIR = ROOT / "src/_data/clues"
TRACK_FILES = [
    "track_magic_elixir.yaml",
    "track_dirty_dealings.yaml",
    "track_psychics_burden.yaml",
    "track_secret_baby.yaml",
]


def build_key_map():
    """Return {clue_id: [track_id, ...]} from track yaml files."""
    mapping = {}
    for fn in TRACK_FILES:
        path = QUESTS_DIR / fn
        data = yaml.safe_load(path.read_text())
        track_id = data["id"]
        for clue_id in data.get("clue_chain", []):
            mapping.setdefault(str(clue_id), []).append(track_id)
    return mapping


# Matches: a line starting with "is_key:" at column 0 (top-level YAML key)
IS_KEY_LINE = re.compile(r"^is_key\s*:", re.MULTILINE)


def strip_is_key_block(text):
    """Remove the existing top-level is_key field (inline or block-list)."""
    m = IS_KEY_LINE.search(text)
    if not m:
        return text, False

    start = m.start()
    # Everything after "is_key:" on that line
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    rest_of_line = text[m.end(): line_end].strip()

    end = line_end + 1  # include the newline
    if rest_of_line == "" or rest_of_line.startswith("#"):
        # Block form: swallow subsequent "- ..." lines (possibly with blank lines)
        i = end
        while i < len(text):
            nl = text.find("\n", i)
            line = text[i:nl] if nl != -1 else text[i:]
            stripped = line.strip()
            if stripped.startswith("-") or stripped == "":
                end = (nl + 1) if nl != -1 else len(text)
                i = end
                continue
            break
    # else: inline form (e.g., "is_key: []" or "is_key: magic_elixir") — just drop the line

    return text[:start] + text[end:], True


def insert_is_key(text, tracks):
    """Insert a new is_key block. Prefer placing after `skills:` block, else before `content:`, else at end of header."""
    block_lines = ["is_key:"] + [f"- {t}" for t in tracks]
    new_block = "\n".join(block_lines) + "\n"

    # Try after skills block
    m = re.search(r"^skills\s*:", text, re.MULTILINE)
    if m:
        # Find end of skills block
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        rest = text[m.end():line_end].strip()
        insert_at = line_end + 1
        if rest == "" or rest.startswith("#"):
            # Block form — consume list items
            i = insert_at
            while i < len(text):
                nl = text.find("\n", i)
                line = text[i:nl] if nl != -1 else text[i:]
                if line.strip().startswith("-") or line.strip() == "":
                    insert_at = (nl + 1) if nl != -1 else len(text)
                    i = insert_at
                    continue
                break
        return text[:insert_at] + new_block + text[insert_at:]

    # Else insert before `content:`
    m = re.search(r"^content\s*:", text, re.MULTILINE)
    if m:
        return text[:m.start()] + new_block + text[m.start():]

    # Else append at end
    if not text.endswith("\n"):
        text += "\n"
    return text + new_block


def main():
    key_map = build_key_map()
    print(f"Key map: {len(key_map)} clues across {len(TRACK_FILES)} tracks\n")

    stats = {"removed": 0, "added": 0, "updated": 0, "unchanged": 0, "missing_clue": []}
    key_ids_seen = set()

    for yaml_file in sorted(CLUES_DIR.rglob("*.yaml")):
        text = yaml_file.read_text()
        try:
            data = yaml.safe_load(text)
        except Exception as e:
            print(f"[skip] {yaml_file.relative_to(ROOT)}: {e}")
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue

        clue_id = str(data["id"])
        wanted = key_map.get(clue_id)
        had = "is_key" in data

        new_text, stripped = strip_is_key_block(text)

        if wanted:
            key_ids_seen.add(clue_id)
            new_text = insert_is_key(new_text, wanted)
            if not had:
                stats["added"] += 1
                action = "added"
            elif data.get("is_key") != wanted:
                stats["updated"] += 1
                action = "updated"
            else:
                stats["unchanged"] += 1
                action = "unchanged"
        else:
            if had:
                stats["removed"] += 1
                action = "removed"
            else:
                stats["unchanged"] += 1
                action = "unchanged"

        if new_text != text:
            yaml_file.write_text(new_text)
            print(f"[{action:8s}] {clue_id:10s} {yaml_file.relative_to(ROOT)}")

    # Report on any track clues that didn't match a file
    for clue_id in sorted(set(key_map) - key_ids_seen):
        stats["missing_clue"].append(clue_id)

    print()
    print("Summary:")
    for k in ("added", "updated", "removed", "unchanged"):
        print(f"  {k:10s} {stats[k]}")
    if stats["missing_clue"]:
        print(f"\n  ⚠ Clues referenced in track chains but not found in {CLUES_DIR}:")
        for cid in stats["missing_clue"]:
            print(f"     {cid}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

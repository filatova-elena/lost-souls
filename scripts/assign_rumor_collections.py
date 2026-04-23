#!/usr/bin/env python3
"""One-shot script: assign each rumor YAML a `collection:` field.

Inserts `collection: RUMORS_X_Y` right after the `act:` line (or replaces an
existing `collection:` line). Leaves the rest of the file untouched.
"""
import re
import sys
from pathlib import Path

UNASSIGNED = "unassigned"

MAPPING = {
    # Act I — piano I_A kept juicy & short
    "R1": "RUMORS_I_A", "R4": "RUMORS_I_A",
    "R18": "RUMORS_I_A", "R21": "RUMORS_I_A",
    "R17": UNASSIGNED, "R70": UNASSIGNED,

    "R15": "RUMORS_I_B", "R16": "RUMORS_I_B",
    "R61": "RUMORS_I_B", "R71": "RUMORS_I_B",
    "R5": UNASSIGNED, "R50": UNASSIGNED,

    "R12": "RUMORS_I_C", "R19": "RUMORS_I_C",
    "R25": "RUMORS_I_C", "R39": "RUMORS_I_C",
    "R66": UNASSIGNED, "R68": UNASSIGNED,

    # Act II — foyer II_F kept juicy & short (4 rival murder theories)
    "R7": "RUMORS_II_A", "R43": "RUMORS_II_A",
    "R45": "RUMORS_II_A", "R59": "RUMORS_II_A",
    "R51": UNASSIGNED,

    "R10": "RUMORS_II_B", "R11": "RUMORS_II_B",
    "R40": "RUMORS_II_B", "R58": "RUMORS_II_B",
    "R47": UNASSIGNED,

    "R2": "RUMORS_II_C", "R41": "RUMORS_II_C",
    "R60": "RUMORS_II_C", "R62": "RUMORS_II_C",
    "R49": UNASSIGNED,

    "R14": "RUMORS_II_D", "R42": "RUMORS_II_D",
    "R46": "RUMORS_II_D", "R52": "RUMORS_II_D",
    "R73": UNASSIGNED,

    "R54": "RUMORS_II_E", "R63": "RUMORS_II_E",
    "R65": "RUMORS_II_E", "R67": "RUMORS_II_E",
    "R74": UNASSIGNED,

    "R9": "RUMORS_II_F", "R13": "RUMORS_II_F",
    "R22": "RUMORS_II_F", "R23": "RUMORS_II_F",
    "R8": UNASSIGNED,

    # Act III
    "R6": "RUMORS_III_A", "R44": "RUMORS_III_A",
    "R48": "RUMORS_III_A", "R56": "RUMORS_III_A",
    "R69": UNASSIGNED,

    "R3": "RUMORS_III_B", "R20": "RUMORS_III_B",
    "R57": "RUMORS_III_B", "R64": "RUMORS_III_B",

    # Act IV
    "R24": "RUMORS_IV_A", "R55": "RUMORS_IV_A",
    "R53": "RUMORS_IV_B", "R72": "RUMORS_IV_B",
}


def update_file(path: Path) -> tuple[str, str] | None:
    text = path.read_text()
    m = re.search(r"^id: (R\d+)\s*$", text, re.MULTILINE)
    if not m:
        return None
    rid = m.group(1)
    coll = MAPPING.get(rid)
    if not coll:
        print(f"  [skip] {path.name}: {rid} has no assignment", file=sys.stderr)
        return None

    if re.search(r"^collection:", text, re.MULTILINE):
        new_text = re.sub(r"^collection: .*$", f"collection: {coll}", text, flags=re.MULTILINE)
    else:
        new_text, n = re.subn(
            r"(^act: [^\n]+\n)",
            rf"\1collection: {coll}\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if n == 0:
            print(f"  [skip] {path.name}: no `act:` line to insert after", file=sys.stderr)
            return None

    if new_text != text:
        path.write_text(new_text)
    return rid, coll


def main():
    root = Path(__file__).parent.parent
    rumors_dir = root / "src/_data/rumors"
    updated = []
    for f in sorted(rumors_dir.glob("*.yaml")):
        result = update_file(f)
        if result:
            updated.append(result)
    print(f"\nUpdated {len(updated)} rumor files.")
    # Sanity: confirm each collection got its expected count
    from collections import Counter
    counts = Counter(c for _, c in updated)
    for c in sorted(counts):
        print(f"  {c}: {counts[c]}")


if __name__ == "__main__":
    main()

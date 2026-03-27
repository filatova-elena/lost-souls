#!/usr/bin/env python3
"""
List all clues grouped by room and category (artifacts, props, writings, rumors, visions).
Only shows first items in chains (excludes clues with previous_id).

Usage:
    python scripts/reference_generators/list_clues_by_room.py
"""

import yaml
from pathlib import Path

project_root = Path(__file__).parent.parent.parent


def main():
    clues = []
    for f in sorted((project_root / "src/_data/clues").rglob("*.yaml")):
        try:
            with open(f) as fh:
                d = yaml.safe_load(fh)
                if d and "id" in d and "previous_id" not in d:
                    clues.append(d)
        except Exception:
            pass

    rooms = {}
    for c in clues:
        loc = c.get("location", {})
        room = loc.get("room", "UNASSIGNED") if isinstance(loc, dict) else "OLD_FORMAT"
        rooms.setdefault(room, []).append(c)

    def category(c):
        t = c.get("type", "")
        cid = c.get("id", "")
        if cid.startswith("V"):
            return "visions"
        if t.startswith("Rumor"):
            return "rumors"
        if t.startswith("Newspaper"):
            return "newspapers"
        if t.startswith(("Writing", "Document")):
            return "writings"
        if "prop" in c:
            return "props"
        if t.startswith(("Artifact", "Botanical")):
            return "artifacts"
        return "writings"

    cat_order = ["artifacts", "props", "writings", "newspapers", "rumors", "visions"]

    for room in sorted(rooms.keys()):
        cats = {cat: [] for cat in cat_order}
        for c in rooms[room]:
            cat = category(c)
            desc = (
                c.get("location", {}).get("description", "")
                if isinstance(c.get("location"), dict)
                else ""
            )
            prop_text = c.get("prop", "")
            title = c.get("title", "")
            cid = c.get("id", "")
            cats[cat].append((cid, title, desc, prop_text))

        room_total = sum(len(v) for v in cats.values())
        print(f"\n## {room} ({room_total})")

        for cat_name in cat_order:
            items = cats[cat_name]
            if items:
                print(f"  {cat_name} ({len(items)}):")
                for cid, title, desc, prop_text in sorted(items):
                    extra = ""
                    if prop_text:
                        extra = f" [prop: {prop_text}]"
                    if desc:
                        extra += f" ({desc})"
                    print(f"    {cid} - {title}{extra}")


if __name__ == "__main__":
    main()

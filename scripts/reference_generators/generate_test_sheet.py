#!/usr/bin/env python3
"""
Generate Test Sheet (PDF)

Creates a compact, print-optimized PDF test sheet with scannable QR codes
organized by act. Only includes:
- Prologue: Sign-in and test QR codes
- Per act: One sample clue per level-2 skill, then all key clues grouped by quest
- Story gate clues shown before the act they unlock

Layout:
- 4 QR codes per row (each 1.5" wide with label below)
- Section headers separate acts
- Quest subsections with key emoji
- Black & white for clean laser printing
"""

import argparse
import sys
import yaml
import tempfile
from pathlib import Path
from collections import defaultdict

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from PIL import Image
except ImportError:
    print("Error: reportlab and Pillow are required. Install with: pip install reportlab Pillow", file=sys.stderr)
    sys.exit(1)


def find_project_root():
    """Walk up from cwd to find project root (directory containing package.json)."""
    current = Path.cwd()
    while current != current.parent:
        if (current / 'package.json').exists():
            return current
        current = current.parent
    # Fallback to cwd if not found
    return Path.cwd()


# Add project root to path
project_root = find_project_root()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "qr_codes"))

from qr_generator import generate_qr

BASE_URL = "https://lostsouls.door66.events"

# ── Layout constants ────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = letter  # 8.5" x 11"
MARGIN = 0.4 * inch

# QR grid: 4 columns, 1.5" QR codes
COLS = 4
QR_SIZE = 1.5 * inch
LABEL_HEIGHT = 0.3 * inch
CELL_PADDING = 0.1 * inch
CELL_WIDTH = (PAGE_WIDTH - 2 * MARGIN) / COLS
CELL_HEIGHT = QR_SIZE + LABEL_HEIGHT + CELL_PADDING

SECTION_HEADER_HEIGHT = 0.35 * inch
SUBSECTION_HEADER_HEIGHT = 0.28 * inch


# ── Data loading ────────────────────────────────────────────────────

def load_all_clues(clues_dir):
    """Load all clue YAML files recursively."""
    clues = {}
    clues_path = project_root / clues_dir
    if not clues_path.exists():
        print(f"Error: Clues directory not found: {clues_path}", file=sys.stderr)
        return clues
    for yaml_file in clues_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                clue_data = yaml.safe_load(f)
                if clue_data and 'id' in clue_data:
                    clues[clue_data['id']] = clue_data
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}", file=sys.stderr)
    return clues


def load_quests(quests_dir):
    """Load all quest YAML files."""
    quests = {}
    quests_path = project_root / quests_dir
    if not quests_path.exists():
        return quests
    for yaml_file in quests_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                quest_data = yaml.safe_load(f)
                if quest_data and 'id' in quest_data:
                    hashtag = quest_data.get('hashtag', quest_data['id'])
                    quests[hashtag] = {
                        'id': quest_data['id'],
                        'title': quest_data.get('title', quest_data['id']),
                        'hashtag': hashtag,
                    }
        except Exception as e:
            print(f"Warning: Error loading {yaml_file}: {e}", file=sys.stderr)
    return quests


def load_story_gates(story_gates_file):
    """Load story gates configuration."""
    gates_path = project_root / story_gates_file
    if not gates_path.exists():
        return {}
    with open(gates_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def get_quest_name(hashtag, quests):
    """Get quest title from hashtag."""
    if hashtag in quests:
        return quests[hashtag]['title']
    for quest in quests.values():
        if quest['id'] == hashtag:
            return quest['title']
    return hashtag.replace('_', ' ').title()


# ── Clue selection logic ────────────────────────────────────────────

def extract_skill_base_and_level(skill_id):
    """Parse a skill ID like 'art_2' into ('art', 2)."""
    import re
    match = re.match(r'^(.+?)_(\d+)$', skill_id)
    if match:
        return match.group(1), int(match.group(2))
    return skill_id, 0


def select_clues_for_act(act_clues, quests, story_gates_clue_ids):
    """
    Select which clues to include for an act:
    - One sample clue per level-2 skill (for skill testing)
    - All key clues, grouped by quest
    
    Returns: {
        'skill_samples': [(clue_id, clue_data, skill_name), ...],
        'quest_groups': [(quest_name, [(clue_id, clue_data), ...]), ...],
        'gate_clues': [(clue_id, clue_data), ...],
    }
    """
    skill_samples = {}  # skill_base -> (clue_id, clue_data)
    quest_clues = defaultdict(list)  # quest_hashtag -> [(clue_id, clue_data)]
    gate_clues = []

    for clue_id, clue_data in act_clues:
        # Check if this is a story gate clue
        if clue_data.get('story_gate_for'):
            gate_clues.append((clue_id, clue_data))

        # Collect one sample per level-2 skill
        skills = clue_data.get('skills', [])
        for skill in skills:
            base, level = extract_skill_base_and_level(skill)
            if level == 2 and base not in skill_samples:
                skill_samples[base] = (clue_id, clue_data, base)

        # Collect key clues by quest
        is_key = clue_data.get('is_key', [])
        if is_key:
            if not isinstance(is_key, list):
                is_key = [is_key]
            for hashtag in is_key:
                quest_clues[hashtag].append((clue_id, clue_data))

    # Format skill samples
    skill_sample_list = sorted(skill_samples.values(), key=lambda x: x[2])

    # Format quest groups with names
    quest_groups = []
    for hashtag, clues in sorted(quest_clues.items()):
        quest_name = get_quest_name(hashtag, quests)
        quest_groups.append((quest_name, hashtag, clues))

    return {
        'skill_samples': skill_sample_list,
        'quest_groups': quest_groups,
        'gate_clues': gate_clues,
    }


# ── QR generation ───────────────────────────────────────────────────

def generate_qr_image(url, label, size_px=300):
    """Generate a QR code and return as PIL Image."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        generate_qr(
            url=url, output_path=tmp.name, size=size_px, label=label,
            overlay="keyhole", fg_color=(0, 0, 0, 255),
            bg_color=(255, 255, 255, 255), rotate=False,
        )
        img = Image.open(tmp.name)
        img_copy = img.copy()
        img.close()
        Path(tmp.name).unlink()
    return img_copy


# ── PDF rendering ───────────────────────────────────────────────────

class TestSheetRenderer:
    """Renders a test sheet PDF with a grid of QR codes."""

    def __init__(self, output_path, base_url=BASE_URL):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url
        self.c = canvas.Canvas(str(self.output_path), pagesize=letter)
        self.y = PAGE_HEIGHT - MARGIN
        self.col = 0

    def _ensure_space(self, needed):
        """Start a new page if not enough vertical space remains."""
        if self.y - needed < MARGIN:
            self._flush_row()
            self.c.showPage()
            self.y = PAGE_HEIGHT - MARGIN

    def _flush_row(self):
        """Reset column to 0 and move Y down past the current row."""
        if self.col > 0:
            self.y -= CELL_HEIGHT
            self.col = 0

    def draw_title(self, text):
        """Draw page title."""
        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= 0.35 * inch

    def draw_section_header(self, text):
        """Draw act section header with underline."""
        self._flush_row()
        self._ensure_space(SECTION_HEADER_HEIGHT + CELL_HEIGHT)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(MARGIN, self.y, text)
        self.c.setStrokeColorRGB(0.3, 0.3, 0.3)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN, self.y - 3, PAGE_WIDTH - MARGIN, self.y - 3)
        self.y -= SECTION_HEADER_HEIGHT

    def draw_subsection_header(self, text):
        """Draw a quest or category subsection label."""
        self._flush_row()
        self._ensure_space(SUBSECTION_HEADER_HEIGHT + CELL_HEIGHT)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(MARGIN + 0.1 * inch, self.y, text)
        self.y -= SUBSECTION_HEADER_HEIGHT

    def draw_qr_cell(self, clue_id, label_line2=None, tag=None):
        """
        Draw one QR code cell in the current grid position.
        
        Each cell contains:
        - QR code image (centered in cell)
        - Clue ID below (bold)
        - Optional second line (title or quest info)
        """
        if self.col >= COLS:
            self._flush_row()

        self._ensure_space(CELL_HEIGHT)

        cell_x = MARGIN + self.col * CELL_WIDTH
        cell_top = self.y

        # Center QR in cell
        qr_x = cell_x + (CELL_WIDTH - QR_SIZE) / 2
        qr_bottom = cell_top - QR_SIZE

        # Generate and draw QR code
        url = f"{self.base_url}/clues/{clue_id}/"
        qr_img = generate_qr_image(url, clue_id, size_px=300)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            qr_img.save(tmp.name)
            self.c.drawImage(tmp.name, qr_x, qr_bottom, width=QR_SIZE, height=QR_SIZE)
            Path(tmp.name).unlink()

        # Label below QR, centered
        label_x = cell_x + CELL_WIDTH / 2

        # Line 1: clue ID + optional tag
        line1 = clue_id
        if tag:
            line1 += f"  [{tag}]"
        self.c.setFont("Helvetica-Bold", 7)
        self.c.drawCentredString(label_x, qr_bottom - 0.12 * inch, line1)

        # Line 2: extra info
        if label_line2:
            max_chars = int(CELL_WIDTH / 3.5)
            display = label_line2[:max_chars] + "..." if len(label_line2) > max_chars else label_line2
            self.c.setFont("Helvetica", 6)
            self.c.drawCentredString(label_x, qr_bottom - 0.22 * inch, display)

        self.col += 1

    def save(self):
        """Finalize and save the PDF."""
        self.c.save()
        print(f"\n✅ Test sheet generated: {self.output_path}")


# ── Main generation logic ───────────────────────────────────────────

def generate_test_sheet(clues, quests, story_gates, output_path, base_url=BASE_URL):
    """Generate the test sheet PDF."""
    r = TestSheetRenderer(output_path, base_url)

    r.draw_title("Test Sheet — Lost Souls Investigation")

    # ── Prologue ────────────────────────────────────────────────────
    r.draw_section_header("Prologue")
    print("  Generating prologue QR codes...")
    r.draw_qr_cell("SIGN_IN", "Player Sign-In")
    if "TEST001" in clues:
        r.draw_qr_cell("TEST001", "Test QR")

    # ── Acts ────────────────────────────────────────────────────────
    act_sequence = [
        ('act_i_setting',           'Act I: The Setting'),
        ('act_ii_mystery_emerges',  'Act II: The Mystery Emerges'),
        ('act_iii_investigation',   'Act III: The Investigation'),
        ('act_iv_revelation',       'Act IV: The Revelation'),
    ]

    # Organize clues by act
    clues_by_act = defaultdict(list)
    for clue_id, clue_data in clues.items():
        act = clue_data.get('act', 'unknown')
        clues_by_act[act].append((clue_id, clue_data))
    for act in clues_by_act:
        clues_by_act[act].sort(key=lambda x: x[0])

    for act_key, act_name in act_sequence:
        act_clues = clues_by_act.get(act_key, [])
        if not act_clues:
            continue

        # Determine which clue IDs are story gate clues (from story_gates.yaml)
        gate_clue_ids = set()
        for gate_key, gate_data in story_gates.items():
            for cid in gate_data.get('clues', []):
                gate_clue_ids.add(cid)

        selection = select_clues_for_act(act_clues, quests, gate_clue_ids)

        r.draw_section_header(act_name)
        count = len(selection['skill_samples']) + sum(len(g[2]) for g in selection['quest_groups']) + len(selection['gate_clues'])
        print(f"  {act_name}: {count} clues selected")

        # Story gate clues for this act
        if selection['gate_clues']:
            r.draw_subsection_header("🚪 Story Gate")
            for clue_id, clue_data in selection['gate_clues']:
                gate_target = clue_data.get('story_gate_for', '')
                r.draw_qr_cell(clue_id, f"Unlocks: {gate_target}", tag="GATE")

        # Skill sample clues
        if selection['skill_samples']:
            r.draw_subsection_header("🔒 Skill Checks (one per level-2 skill)")
            for clue_id, clue_data, skill_base in selection['skill_samples']:
                title = clue_data.get('title', '')
                r.draw_qr_cell(clue_id, f"{skill_base}_2: {title}", tag=f"{skill_base.upper()}")

        # Key clues by quest
        for quest_name, quest_hashtag, key_clues in selection['quest_groups']:
            r.draw_subsection_header(f"🔑 {quest_name}")
            for clue_id, clue_data in key_clues:
                title = clue_data.get('title', '')
                r.draw_qr_cell(clue_id, title, tag="KEY")

    r.save()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a test sheet PDF with scannable QR codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--output', '-o', default='to_print/test_sheet.pdf',
                        help='Output PDF file path (default: to_print/test_sheet.pdf)')
    parser.add_argument('--base-url', default=BASE_URL,
                        help=f'Base URL for clue links (default: {BASE_URL})')
    parser.add_argument('--clues-dir', default='src/_data/clues',
                        help='Directory containing clue YAML files')
    parser.add_argument('--quests-dir', default='src/_data/quests',
                        help='Directory containing quest YAML files')
    parser.add_argument('--story-gates', default='src/_data/refs/story_gates.yaml',
                        help='Path to story gates YAML file')

    args = parser.parse_args()

    # Resolve output path relative to project root if it's a relative path
    project_root = find_project_root()
    if not Path(args.output).is_absolute():
        output_path = project_root / args.output
    else:
        output_path = Path(args.output)

    print("Loading clues...")
    clues = load_all_clues(args.clues_dir)
    print(f"  Loaded {len(clues)} clues")

    print("Loading quests...")
    quests = load_quests(args.quests_dir)
    print(f"  Loaded {len(quests)} quests")

    print("Loading story gates...")
    story_gates = load_story_gates(args.story_gates)
    print(f"  Loaded {len(story_gates)} story gates")

    print("\nGenerating test sheet...")
    generate_test_sheet(clues, quests, story_gates, str(output_path), args.base_url)

    print("Done!")


if __name__ == '__main__':
    main()

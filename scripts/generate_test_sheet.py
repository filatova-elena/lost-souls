#!/usr/bin/env python3
"""
Generate Test Sheet (PDF)

Creates a compact, print-optimized PDF test sheet with scannable QR codes
organized by act. Simple grid layout: QR code with label underneath, arranged
in rows across the page.

Layout:
- 5 QR codes per row (each ~1.2" wide with label below)
- Section headers separate acts and story gates
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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts" / "qr_codes"))

from qr_generator import generate_qr

BASE_URL = "https://lostsouls.door66.events"

# ── Layout constants ────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = letter  # 8.5" x 11"
MARGIN = 0.5 * inch

# QR grid: 5 columns across the page
COLS = 5
QR_SIZE = 1.0 * inch          # QR code image size (scannable at this size)
LABEL_HEIGHT = 0.35 * inch     # Space for 2-3 lines of text below QR
CELL_WIDTH = (PAGE_WIDTH - 2 * MARGIN) / COLS
CELL_HEIGHT = QR_SIZE + LABEL_HEIGHT + 0.1 * inch  # total height per cell

SECTION_HEADER_HEIGHT = 0.35 * inch
SUBSECTION_HEADER_HEIGHT = 0.25 * inch


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


def organize_clues_by_act(clues):
    """Organize clues by act, sorted by ID within each act."""
    by_act = defaultdict(list)
    for clue_id, clue_data in clues.items():
        act = clue_data.get('act', 'unknown')
        by_act[act].append((clue_id, clue_data))
    for act in by_act:
        by_act[act].sort(key=lambda x: x[0])
    return by_act


def get_quest_name(hashtag, quests):
    """Get quest title from hashtag."""
    if hashtag in quests:
        return quests[hashtag]['title']
    for quest in quests.values():
        if quest['id'] == hashtag:
            return quest['title']
    return hashtag.replace('_', ' ').title()


# ── QR generation ───────────────────────────────────────────────────

def generate_qr_image(url, label, size_px=200):
    """Generate a QR code and return as PIL Image."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        generate_qr(
            url=url, output_path=tmp.name, size=size_px, label=label,
            overlay="keyhole", fg_color=(0, 0, 0, 255),
            bg_color=(255, 255, 255, 255), rotate=False,
        )
        img = Image.open(tmp.name)
        # Make a copy so we can delete the temp file
        img_copy = img.copy()
        img.close()
        Path(tmp.name).unlink()
    return img_copy


# ── PDF rendering ───────────────────────────────────────────────────

class TestSheetRenderer:
    """Renders a test sheet PDF with a simple grid of QR codes."""

    def __init__(self, output_path, base_url=BASE_URL):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url
        self.c = canvas.Canvas(str(self.output_path), pagesize=letter)
        self.y = PAGE_HEIGHT - MARGIN  # current Y position (top of next element)
        self.col = 0                   # current column in the grid row

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
        self.y -= 0.3 * inch

    def draw_section_header(self, text):
        """Draw a section header with underline."""
        self._flush_row()
        self._ensure_space(SECTION_HEADER_HEIGHT + CELL_HEIGHT)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(MARGIN, self.y, text)
        self.c.setStrokeColorRGB(0, 0, 0)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN, self.y - 3, PAGE_WIDTH - MARGIN, self.y - 3)
        self.y -= SECTION_HEADER_HEIGHT

    def draw_subsection_header(self, text):
        """Draw a smaller subsection label."""
        self._flush_row()
        self._ensure_space(SUBSECTION_HEADER_HEIGHT + CELL_HEIGHT)
        self.c.setFont("Helvetica-BoldOblique", 8)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= SUBSECTION_HEADER_HEIGHT

    def draw_text_line(self, text, font="Helvetica", size=8):
        """Draw a simple line of text."""
        self._flush_row()
        self._ensure_space(0.2 * inch)
        self.c.setFont(font, size)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= 0.18 * inch

    def draw_qr_cell(self, clue_id, label_line1, label_line2=None, tag=None):
        """
        Draw one QR code cell in the current grid position.
        
        Each cell contains:
        - QR code image (centered in cell)
        - label_line1 below (clue ID, bold)
        - label_line2 below that (optional, e.g. title)
        - tag in brackets if provided (e.g. [KEY], [GATE])
        """
        # Wrap to next row if needed
        if self.col >= COLS:
            self._flush_row()

        self._ensure_space(CELL_HEIGHT)

        # Cell position
        cell_x = MARGIN + self.col * CELL_WIDTH
        cell_top = self.y

        # Center QR in cell horizontally
        qr_x = cell_x + (CELL_WIDTH - QR_SIZE) / 2
        qr_top = cell_top
        qr_bottom = qr_top - QR_SIZE

        # Generate and draw QR code
        url = f"{self.base_url}/clues/{clue_id}/"
        qr_img = generate_qr_image(url, clue_id, size_px=200)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            qr_img.save(tmp.name)
            self.c.drawImage(tmp.name, qr_x, qr_bottom, width=QR_SIZE, height=QR_SIZE)
            Path(tmp.name).unlink()

        # Labels below QR, centered in cell
        label_x = cell_x + CELL_WIDTH / 2  # center point

        # Line 1: clue ID (bold) + optional tag
        line1 = clue_id
        if tag:
            line1 += f"  [{tag}]"
        self.c.setFont("Helvetica-Bold", 7)
        self.c.drawCentredString(label_x, qr_bottom - 0.1 * inch, line1)

        # Line 2: title or extra info
        if label_line2:
            # Truncate if too long for cell
            max_chars = int(CELL_WIDTH / (3.5))  # rough estimate
            display = label_line2[:max_chars] + "..." if len(label_line2) > max_chars else label_line2
            self.c.setFont("Helvetica", 6)
            self.c.drawCentredString(label_x, qr_bottom - 0.2 * inch, display)

        self.col += 1

    def save(self):
        """Finalize and save the PDF."""
        self.c.save()
        print(f"\n✅ Test sheet generated: {self.output_path}")


# ── Main generation logic ───────────────────────────────────────────

def generate_test_sheet(clues, quests, story_gates, output_path, base_url=BASE_URL):
    """Generate the test sheet PDF."""
    clues_by_act = organize_clues_by_act(clues)
    r = TestSheetRenderer(output_path, base_url)

    # Title
    r.draw_title("Test Sheet — Lost Souls Investigation")

    # ── Setup & Admin ───────────────────────────────────────────────
    r.draw_section_header("Setup & Administration")
    print("  Generating setup QR codes...")
    r.draw_qr_cell("TEST001", "TEST001", "Test QR", tag="TEST")
    r.draw_qr_cell("SIGN_IN", "SIGN_IN", "Player Sign-In", tag="ADMIN")

    # ── Acts ────────────────────────────────────────────────────────
    act_sequence = [
        ('act_i_setting',           'Act I: The Setting'),
        ('act_ii_mystery_emerges',  'Act II: The Mystery Emerges'),
        ('act_iii_investigation',   'Act III: The Investigation'),
        ('act_iv_revelation',       'Act IV: The Revelation'),
    ]

    # Story gates: keyed by the act they unlock
    gate_names = {
        'act_ii_mystery_emerges': 'Story Gate: Act I → Act II',
        'act_iii_investigation':  'Story Gate: Act II → Act III',
        'act_iv_revelation':      'Story Gate: Act III → Act IV',
    }

    for act_key, act_name in act_sequence:
        # Story gate before this act (if any)
        if act_key in gate_names:
            gate_clue_ids = story_gates.get(act_key, {}).get('clues', [])
            if gate_clue_ids:
                r.draw_section_header(gate_names[act_key])
                print(f"  Story gate → {act_key}...")
                for cid in gate_clue_ids:
                    if cid in clues:
                        cdata = clues[cid]
                        title = cdata.get('title', '')
                        r.draw_qr_cell(cid, cid, title, tag="GATE")

        # Act section
        act_clues = clues_by_act.get(act_key, [])
        if not act_clues:
            continue

        r.draw_section_header(act_name)
        print(f"  Processing {act_name} ({len(act_clues)} clues)...")

        # Separate key clues from regular clues
        key_clues = []
        regular_clues = []
        for cid, cdata in act_clues:
            is_key = cdata.get('is_key', [])
            if is_key:
                # Determine which quest(s) this is key for
                if isinstance(is_key, list):
                    quest_names = [get_quest_name(h, quests) for h in is_key]
                else:
                    quest_names = [get_quest_name(is_key, quests)]
                key_clues.append((cid, cdata, quest_names))
            else:
                regular_clues.append((cid, cdata))

        # Key clues first (with QR codes)
        if key_clues:
            r.draw_subsection_header("Key Clues:")
            for cid, cdata, quest_names in key_clues:
                quest_str = ", ".join(quest_names)
                title = cdata.get('title', '')
                # Show quest name as the second line
                line2 = f"{title}" if not quest_str else f"{quest_str}"
                r.draw_qr_cell(cid, cid, line2, tag="KEY")

        # Regular clues (with QR codes too — they all need to be scannable)
        if regular_clues:
            r.draw_subsection_header("Clues:")
            for cid, cdata in regular_clues:
                title = cdata.get('title', '')
                r.draw_qr_cell(cid, cid, title)

    r.save()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a test sheet PDF with scannable QR codes for all clues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--output', '-o', default='test_sheet.pdf',
                        help='Output PDF file path (default: test_sheet.pdf)')
    parser.add_argument('--base-url', default=BASE_URL,
                        help=f'Base URL for clue links (default: {BASE_URL})')
    parser.add_argument('--clues-dir', default='src/_data/clues',
                        help='Directory containing clue YAML files')
    parser.add_argument('--quests-dir', default='src/_data/quests',
                        help='Directory containing quest YAML files')
    parser.add_argument('--story-gates', default='src/_data/refs/story_gates.yaml',
                        help='Path to story gates YAML file')

    args = parser.parse_args()

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
    generate_test_sheet(clues, quests, story_gates, args.output, args.base_url)

    print("Done!")


if __name__ == '__main__':
    main()

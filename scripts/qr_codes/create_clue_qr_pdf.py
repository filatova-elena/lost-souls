#!/usr/bin/env python3
"""
Create a PDF with all clue QR codes arranged in a compact grid.
QR codes are smaller and more densely packed on an 8.5x11 inch page.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import math
import sys
import yaml

# Page settings
PAGE_WIDTH = 8.5  # inches
PAGE_HEIGHT = 11.0  # inches
QR_SIZE = 2.6  # inches (large QR codes, sized to fit 12 per page)
MARGIN = 0.15  # inches (very minimal margins)
LABEL_HEIGHT = 0.25  # inches for clue ID above QR code
SPACING = 0.05  # inches (very tight spacing between QR codes)
DPI = 150  # dots per inch

def calculate_grid_layout():
    """
    Calculate how many QR codes fit on a page.
    Returns: (cols, rows, qr_codes_per_page)
    """
    # Target: 12 QR codes per page (3 columns × 4 rows)
    # Calculate usable space (accounting for margins, title, and label space)
    usable_width = PAGE_WIDTH - 2 * MARGIN
    usable_height = PAGE_HEIGHT - 2 * MARGIN - 0.15  # Minimal space for title (closer)
    
    # Account for label height above each QR code
    cell_height = QR_SIZE + LABEL_HEIGHT
    
    # Calculate how many fit
    cols = int(usable_width / (QR_SIZE + SPACING))
    rows = int(usable_height / (cell_height + SPACING))
    
    # Ensure we have at least 1 column and row
    cols = max(1, cols)
    rows = max(1, rows)
    
    # Target 12 per page - prefer 3×4 or 4×3
    if cols * rows < 12:
        # Try to get closer to 12
        if cols < 3:
            cols = 3
        if rows < 4:
            rows = 4
        # If still not enough, adjust
        while cols * rows < 12 and cols < 4:
            cols += 1
        while cols * rows < 12 and rows < 4:
            rows += 1
    
    qr_codes_per_page = cols * rows
    
    return cols, rows, qr_codes_per_page

def load_clue_ids(clues_dir):
    """
    Load clue IDs from YAML files, filtering to only first clues in chains.
    
    Args:
        clues_dir: Path to clues directory
        
    Returns:
        Dictionary mapping filename to clue ID
    """
    clue_ids = {}
    clues_path = Path(clues_dir)
    
    if not clues_path.exists():
        print(f"⚠️  Warning: Clues directory not found: {clues_dir}, IDs will not be shown")
        return clue_ids
    
    # Recursively find all YAML files
    for yaml_file in clues_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                clue = yaml.safe_load(f)
                if clue:
                    # Only include clues that are the first in a chain (no previous_id)
                    if 'previous_id' in clue:
                        continue
                    filename = yaml_file.stem
                    clue_id = clue.get('id', '')
                    if clue_id:
                        clue_ids[filename] = clue_id
        except Exception as e:
            continue
    
    return clue_ids

def load_qr_codes(qr_dir, clue_ids):
    """
    Load all PNG QR code images from a directory.
    
    Args:
        qr_dir: Path to directory containing QR code PNG files
        clue_ids: Dictionary mapping filename to clue ID
        
    Returns:
        List of (image_path, filename, clue_id) tuples, sorted by filename
    """
    qr_path = Path(qr_dir)
    
    if not qr_path.exists():
        raise FileNotFoundError(f"QR codes directory not found: {qr_dir}")
    
    qr_files = sorted([f for f in qr_path.glob("*.png") if f.is_file()])
    
    return [(str(f), f.stem, clue_ids.get(f.stem, '')) for f in qr_files]

def create_pdf(qr_items, output_file, title="Clue QR Codes"):
    """
    Create a PDF with QR codes arranged in a compact grid.
    
    Args:
        qr_items: List of (image_path, filename, clue_id) tuples
        output_file: Output PDF filename
        title: Title for the PDF pages
    """
    cols, rows, qr_codes_per_page = calculate_grid_layout()
    
    # Convert to pixels
    page_width_px = int(PAGE_WIDTH * DPI)
    page_height_px = int(PAGE_HEIGHT * DPI)
    margin_px = int(MARGIN * DPI)
    qr_size_px = int(QR_SIZE * DPI)
    label_height_px = int(LABEL_HEIGHT * DPI)
    title_height_px = int(0.15 * DPI)
    
    # Calculate number of pages needed
    num_pages = math.ceil(len(qr_items) / qr_codes_per_page)
    
    print(f"\n{'='*60}")
    print(f"Clue QR Code PDF Generator (Compact)")
    print(f"{'='*60}")
    print(f"QR codes: {len(qr_items)}")
    print(f"Grid: {cols} columns × {rows} rows = {qr_codes_per_page} per page")
    print(f"QR size: {QR_SIZE}\" × {QR_SIZE}\"")
    print(f"Page size: {PAGE_WIDTH}\" × {PAGE_HEIGHT}\"")
    print(f"Total pages: {num_pages}")
    print(f"{'='*60}\n")
    
    # Load fonts
    try:
        # Try to use system fonts
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        id_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)  # BIG clue IDs!
    except:
        try:
            # Fallback to other common fonts
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            id_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            # Use default font
            title_font = ImageFont.load_default()
            id_font = ImageFont.load_default()
    
    # Create pages
    pages = []
    qr_index = 0
    
    for page_num in range(1, num_pages + 1):
        # Create a new page
        page_img = Image.new('RGB', (page_width_px, page_height_px), color='white')
        draw = ImageDraw.Draw(page_img)
        
        # Draw page title (closer to QR codes)
        page_title = f"{title} - Page {page_num} of {num_pages}"
        title_y = margin_px // 4
        draw.text((margin_px, title_y), page_title, fill='black', font=title_font)
        
        # Calculate grid spacing
        usable_width = page_width_px - 2 * margin_px
        usable_height = page_height_px - 2 * margin_px - title_height_px
        
        # Calculate spacing between QR codes (including label space)
        cell_height = qr_size_px + label_height_px
        spacing_px = int(SPACING * DPI)
        
        # Use fixed minimal spacing instead of dividing evenly
        total_qr_width = cols * qr_size_px + (cols - 1) * spacing_px
        total_cell_height = rows * cell_height + (rows - 1) * spacing_px
        
        # Center the grid if there's extra space
        col_spacing = (usable_width - total_qr_width) / 2 if cols > 1 else (usable_width - qr_size_px) / 2
        row_spacing = (usable_height - total_cell_height) / 2 if rows > 1 else (usable_height - cell_height) / 2
        
        # Draw QR codes in grid
        for row in range(rows):
            if qr_index >= len(qr_items):
                break
            for col in range(cols):
                if qr_index >= len(qr_items):
                    break
                
                image_path, filename, clue_id = qr_items[qr_index]
                
                # Calculate position with fixed minimal spacing
                x = margin_px + col_spacing + col * (qr_size_px + spacing_px)
                cell_y = margin_px + title_height_px + row_spacing + row * (cell_height + spacing_px)
                
                try:
                    # Draw clue ID above QR code
                    if clue_id:
                        id_bbox = draw.textbbox((0, 0), clue_id, font=id_font)
                        id_width = id_bbox[2] - id_bbox[0]
                        id_x = x + (qr_size_px - id_width) // 2
                        id_y = cell_y
                        draw.text((id_x, id_y), clue_id, fill='black', font=id_font)
                    
                    # Load and resize QR code image
                    qr_img = Image.open(image_path).convert('RGB')
                    qr_img = qr_img.resize((qr_size_px, qr_size_px), Image.Resampling.LANCZOS)
                    
                    # Paste QR code below the ID
                    qr_y = cell_y + label_height_px
                    page_img.paste(qr_img, (int(x), int(qr_y)))
                    
                    qr_index += 1
                except Exception as e:
                    print(f"⚠️  Warning: Could not process {filename}: {e}")
                    qr_index += 1
        
        pages.append(page_img)
        print(f"📄 Created page {page_num}/{num_pages}")
    
    # Save as PDF
    if pages:
        pages[0].save(output_file, save_all=True, append_images=pages[1:], format='PDF')
        
        print(f"\n{'='*60}")
        print(f"✅ PDF successfully created!")
        print(f"{'='*60}")
        print(f"📄 Filename: {output_file}")
        print(f"📊 Total pages: {len(pages)}")
        print(f"📦 Total QR codes: {len(qr_items)}")
        print(f"{'='*60}\n")
        
        return True
    else:
        print("❌ Error: No pages created")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Create a compact PDF with clue QR codes and IDs"
    )
    parser.add_argument(
        "--qr-dir",
        default="qr_codes/clues",
        help="Directory containing QR code PNG files (default: qr_codes/clues)"
    )
    parser.add_argument(
        "--clues-dir",
        default="src/_data/clues",
        help="Directory containing clue YAML files (default: src/_data/clues)"
    )
    parser.add_argument(
        "--output",
        default="clue_qr_codes.pdf",
        help="Output PDF filename (default: clue_qr_codes.pdf)"
    )
    parser.add_argument(
        "--title",
        default="Clue QR Codes",
        help="Title for PDF pages (default: Clue QR Codes)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    qr_dir = project_root / args.qr_dir
    clues_dir = project_root / args.clues_dir
    output_file = project_root / args.output
    
    # Load clue IDs
    print("Loading clue IDs...")
    clue_ids = load_clue_ids(clues_dir)
    print(f"Found {len(clue_ids)} clue IDs\n")
    
    # Load QR codes
    try:
        qr_items = load_qr_codes(qr_dir, clue_ids)
        if not qr_items:
            print(f"❌ Error: No QR code PNG files found in {qr_dir}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading QR codes: {e}")
        sys.exit(1)
    
    # Create PDF
    success = create_pdf(qr_items, str(output_file), args.title)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

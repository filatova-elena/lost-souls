#!/usr/bin/env python3
"""
Unified QR Code PDF Generator for Murder Mystery Game
Creates printable PDFs with QR codes in various layouts
Supports: grid, vertical, custom layouts
Can use existing PNG files or generate QR codes on-the-fly
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import math
import qrcode
import os

# Base URL for generating QR codes on-the-fly
BASE_URL = "https://elenafilatova.github.io/murder_mystery"

def generate_qr_code(url, size=300):
    """Generate a QR code image for the given URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img

def create_qr_pdf(
    qr_sources,
    layout="grid",
    output_file="qr_codes.pdf",
    title="QR Codes",
    qr_size=2.5,
    cols=3,
    rows=4,
    base_url=BASE_URL
):
    """
    Create a PDF with QR codes in specified layout.
    
    Args:
        qr_sources: Can be:
            - Directory path (str) - uses all PNG files
            - List of PNG file paths
            - List of (url, name, label) tuples - generates on-the-fly
        layout: "grid", "vertical", or "custom"
        output_file: Output PDF filename
        title: Page title
        qr_size: QR code size in inches
        cols: Number of columns (for grid layout)
        rows: Number of rows per page (for grid layout)
        base_url: Base URL for generating QR codes on-the-fly
    """
    
    # Page settings
    page_width = 8.5
    page_height = 11.0
    margin = 0.5
    dpi = 150
    
    # Convert to pixels
    page_width_px = int(page_width * dpi)
    page_height_px = int(page_height * dpi)
    margin_px = int(margin * dpi)
    qr_size_px = int(qr_size * dpi)
    
    # Parse qr_sources
    qr_items = []
    
    if isinstance(qr_sources, str):
        # Directory path - resolve relative to project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        
        if qr_sources == "generate":
            # Special case handled in main()
            pass
        else:
            qr_path = Path(qr_sources)
            if not qr_path.is_absolute():
                qr_path = project_root / qr_path
            
            if qr_path.is_dir():
                qr_files = sorted([f for f in qr_path.glob("*.png") if f.is_file()])
                qr_items = [(str(f), f.stem, f.stem) for f in qr_files]
            else:
                print(f"❌ Error: Directory not found: {qr_sources}")
                return False
    elif isinstance(qr_sources, list):
        if qr_sources and isinstance(qr_sources[0], (tuple, list)):
            # List of (url, name, label) tuples
            qr_items = qr_sources
        else:
            # List of file paths
            qr_items = [(str(f), Path(f).stem, Path(f).stem) for f in qr_sources]
    
    if not qr_items:
        print(f"❌ Error: No QR codes found")
        return False
    
    print(f"\n{'='*60}")
    print(f"QR Code PDF Generator")
    print(f"{'='*60}")
    print(f"Layout: {layout}")
    print(f"QR codes: {len(qr_items)}")
    print(f"QR size: {qr_size}\" x {qr_size}\"")
    print(f"{'='*60}\n")
    
    # Create pages
    pages = []
    
    if layout == "grid":
        # Grid layout
        qr_codes_per_page = cols * rows
        num_pages = math.ceil(len(qr_items) / qr_codes_per_page)
        
        qr_index = 0
        for page_num in range(1, num_pages + 1):
            page_img = Image.new('RGB', (page_width_px, page_height_px), color='white')
            draw = ImageDraw.Draw(page_img)
            
            # Load fonts
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
                label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
            
            # Page title
            page_title = f"{title} - Page {page_num}"
            draw.text((margin_px, margin_px // 2), page_title, fill='black', font=title_font)
            
            # Calculate grid spacing
            usable_width = page_width_px - 2 * margin_px
            usable_height = page_height_px - 2 * margin_px - 30
            col_spacing = (usable_width - (cols * qr_size_px)) / (cols + 1)
            row_spacing = (usable_height - (rows * qr_size_px)) / (rows + 1)
            
            # Draw QR codes
            for row in range(rows):
                if qr_index >= len(qr_items):
                    break
                for col in range(cols):
                    if qr_index >= len(qr_items):
                        break
                    
                    source, name, label = qr_items[qr_index]
                    
                    # Calculate position
                    x = margin_px + col_spacing + col * (qr_size_px + col_spacing)
                    y = margin_px + 30 + row * (qr_size_px + row_spacing)
                    
                    # Load or generate QR code
                    try:
                        if source.startswith("http"):
                            # Generate on-the-fly
                            qr_img = generate_qr_code(source, qr_size_px)
                        else:
                            # Load from file
                            qr_img = Image.open(source).convert('RGB')
                            qr_img = qr_img.resize((qr_size_px, qr_size_px), Image.Resampling.LANCZOS)
                        
                        page_img.paste(qr_img, (int(x), int(y)))
                        
                        # Add label
                        if label:
                            label_bbox = draw.textbbox((0, 0), label, font=label_font)
                            label_width = label_bbox[2] - label_bbox[0]
                            label_x = x + (qr_size_px - label_width) // 2
                            draw.text((label_x, y + qr_size_px + 5), label, fill='black', font=label_font)
                        
                        qr_index += 1
                    except Exception as e:
                        print(f"⚠️  Warning: Could not process {name}: {e}")
                        qr_index += 1
            
            pages.append(page_img)
    
    elif layout == "vertical":
        # Vertical layout (centered, one per row)
        spacing = 0.4 * dpi
        qr_codes_per_page = int((page_height_px - 2 * margin_px - 30) / (qr_size_px + spacing))
        num_pages = math.ceil(len(qr_items) / qr_codes_per_page)
        
        qr_index = 0
        for page_num in range(1, num_pages + 1):
            page_img = Image.new('RGB', (page_width_px, page_height_px), color='white')
            draw = ImageDraw.Draw(page_img)
            
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Georgia.ttf", 16)
                label_font = ImageFont.truetype("/System/Library/Fonts/Georgia.ttf", 11)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
            
            # Page title
            draw.text((page_width_px / 2, margin_px + 0.25 * dpi), title,
                     fill='#8B7355', font=title_font, anchor="mm")
            
            start_y = margin_px + 0.6 * dpi
            x_center = (page_width_px - qr_size_px) / 2
            
            for i in range(qr_codes_per_page):
                if qr_index >= len(qr_items):
                    break
                
                source, name, label = qr_items[qr_index]
                y = start_y + (qr_size_px + spacing) * i
                
                try:
                    if source.startswith("http"):
                        qr_img = generate_qr_code(source, qr_size_px)
                    else:
                        qr_img = Image.open(source).convert('RGB')
                        qr_img = qr_img.resize((qr_size_px, qr_size_px), Image.Resampling.LANCZOS)
                    
                    page_img.paste(qr_img, (int(x_center), int(y)))
                    
                    if label:
                        label_y = y + qr_size_px + 0.15 * dpi
                        draw.text((page_width_px / 2, label_y), label,
                                 fill='#8B7355', font=label_font, anchor="mm")
                    
                    qr_index += 1
                except Exception as e:
                    print(f"⚠️  Warning: Could not process {name}: {e}")
                    qr_index += 1
            
            pages.append(page_img)
    
    # Save as PDF
    if pages:
        pages[0].save(output_file, save_all=True, append_images=pages[1:])
        
        print(f"{'='*60}")
        print(f"✅ PDF successfully created!")
        print(f"{'='*60}")
        print(f"📄 Filename: {output_file}")
        print(f"📊 Total pages: {len(pages)}")
        print(f"📦 Total QR codes: {len(qr_items)}")
        print(f"{'='*60}\n")
        
        return True
    else:
        print(f"❌ Error: No pages created")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate PDF with QR codes in various layouts"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="QR code source: directory path, or 'generate' for on-the-fly"
    )
    parser.add_argument(
        "--layout",
        choices=["grid", "vertical"],
        default="grid",
        help="Layout type (default: grid)"
    )
    parser.add_argument(
        "--output",
        default="qr_codes.pdf",
        help="Output PDF filename (default: qr_codes.pdf)"
    )
    parser.add_argument(
        "--title",
        default="QR Codes",
        help="Page title (default: QR Codes)"
    )
    parser.add_argument(
        "--qr-size",
        type=float,
        default=2.5,
        help="QR code size in inches (default: 2.5)"
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=3,
        help="Number of columns for grid layout (default: 3)"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=4,
        help="Number of rows per page for grid layout (default: 4)"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"Base URL for generating QR codes (default: {BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # Handle special "generate" source for predefined sets
    if args.source == "generate":
        # Generate main sections on-the-fly
        qr_sources = [
            (f"{args.base_url}/character/characters.html", "characters", "CHARACTERS"),
            (f"{args.base_url}/clue/clues.html", "clues", "CLUES"),
            (f"{args.base_url}/index.html", "rumors", "RUMORS & FACTS"),
            (f"{args.base_url}/book/book_index.html", "book", "STORY BOOK"),
        ]
    else:
        qr_sources = args.source
    
    success = create_qr_pdf(
        qr_sources,
        args.layout,
        args.output,
        args.title,
        args.qr_size,
        args.cols,
        args.rows,
        args.base_url
    )
    exit(0 if success else 1)

if __name__ == "__main__":
    main()

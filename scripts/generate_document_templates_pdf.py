#!/usr/bin/env python3
"""
Generate a PDF with multiple copies of document templates based on checklist quantities.
"""

import yaml
import argparse
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image
import sys


def load_checklist(checklist_path):
    """Load the checklist YAML file."""
    with open(checklist_path, 'r') as f:
        return yaml.safe_load(f)


def get_document_templates(checklist_data):
    """Extract document templates and their quantities from checklist."""
    templates = checklist_data.get('document_templates', {})
    return templates


def convert_key_to_filename(key):
    """Convert YAML key (snake_case) to PNG filename (kebab-case)."""
    return key.replace('_', '-') + '.png'


def get_image_size(image_path):
    """Get the size of an image in points (1/72 inch)."""
    with Image.open(image_path) as img:
        # Convert pixels to points (assuming 72 DPI)
        width_pt = img.width * 72 / img.info.get('dpi', (72, 72))[0]
        height_pt = img.height * 72 / img.info.get('dpi', (72, 72))[0]
        return width_pt, height_pt


def create_templates_pdf(templates, templates_dir, output_path):
    """Create a PDF with multiple copies of each template."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    
    page_width, page_height = letter
    
    for template_key, template_info in templates.items():
        quantity = template_info.get('quantity', 0)
        if quantity == 0:
            continue
        
        # Convert key to filename
        png_filename = convert_key_to_filename(template_key)
        png_path = templates_dir / png_filename
        
        if not png_path.exists():
            print(f"⚠️  Warning: {png_filename} not found, skipping...")
            continue
        
        print(f"Adding {quantity} copies of {template_key} ({png_filename})...")
        
        # Get image dimensions
        img_width_pt, img_height_pt = get_image_size(png_path)
        
        # Scale to fit page (with margins)
        margin = 0.5 * inch
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin
        
        # Calculate scale to fit page
        scale_x = available_width / img_width_pt
        scale_y = available_height / img_height_pt
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up
        
        scaled_width = img_width_pt * scale
        scaled_height = img_height_pt * scale
        
        # Center on page
        x = (page_width - scaled_width) / 2
        y = (page_height - scaled_height) / 2
        
        # Add the image the specified number of times
        for i in range(quantity):
            c.drawImage(str(png_path), x, y, width=scaled_width, height=scaled_height)
            c.showPage()
    
    c.save()
    print(f"\n✅ PDF generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF with document templates based on checklist quantities"
    )
    parser.add_argument(
        '--checklist',
        type=str,
        default='src/_data/refs/pre_mystery_checklist.yaml',
        help='Path to checklist YAML file'
    )
    parser.add_argument(
        '--templates-dir',
        type=str,
        default='to_print/document_templates',
        help='Directory containing PNG template files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='to_print/document_templates/document_templates.pdf',
        help='Output PDF file path'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent
    checklist_path = project_root / args.checklist
    templates_dir = project_root / args.templates_dir
    output_path = project_root / args.output
    
    # Validate paths
    if not checklist_path.exists():
        print(f"❌ Error: Checklist file not found: {checklist_path}")
        sys.exit(1)
    
    if not templates_dir.exists():
        print(f"❌ Error: Templates directory not found: {templates_dir}")
        sys.exit(1)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load checklist
    print(f"Loading checklist from {checklist_path}...")
    checklist_data = load_checklist(checklist_path)
    
    # Get document templates
    templates = get_document_templates(checklist_data)
    
    if not templates:
        print("❌ Error: No document templates found in checklist")
        sys.exit(1)
    
    print(f"Found {len(templates)} document template types\n")
    
    # Generate PDF
    create_templates_pdf(templates, templates_dir, output_path)
    
    # Print summary
    total_pages = sum(t.get('quantity', 0) for t in templates.values())
    print(f"\n📄 Summary:")
    print(f"   Total template types: {len(templates)}")
    print(f"   Total pages: {total_pages}")


if __name__ == "__main__":
    main()

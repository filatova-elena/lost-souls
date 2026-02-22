#!/usr/bin/env python3
"""
Generate a PDF checklist from the pre-mystery checklist YAML file.

Usage:
    python scripts/generate_checklist_pdf.py
    python scripts/generate_checklist_pdf.py --output checklist.pdf
"""

import argparse
import sys
import yaml
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    print("Error: reportlab is required. Install with: pip install reportlab", file=sys.stderr)
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_checklist(checklist_path):
    """Load the checklist YAML file."""
    with open(checklist_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def format_quantity(quantity):
    """Format quantity for display."""
    if quantity is None:
        return "TBD"
    return str(quantity)

def format_item_name(name):
    """Format item name for display (replace underscores with spaces, title case)."""
    return name.replace('_', ' ').title()

def extract_items(data, parent_name="", items=None):
    """
    Recursively extract all items from the nested YAML structure.
    Returns a list of (category, item_name, quantity, description, notes, status) tuples.
    """
    if items is None:
        items = []
    
    if not isinstance(data, dict):
        return items
    
    for key, value in data.items():
        if key in ['title', 'description', 'notes']:
            continue
        
        if isinstance(value, dict):
            # Check if this is an item with quantity/description/status
            if 'quantity' in value or 'description' in value or 'status' in value:
                # This is an item
                quantity = value.get('quantity')
                description = value.get('description', '')
                notes = value.get('notes', '')
                status = value.get('status', 'pending')
                
                # Use parent_name as category, or the key if no parent
                category = parent_name if parent_name else format_item_name(key)
                item_name = format_item_name(key)
                
                items.append((category, item_name, quantity, description, notes, status))
            else:
                # This is a nested category (like jars, dried_herbs)
                # Use the parent name as category, or create a new category name
                if parent_name:
                    category_name = f"{parent_name} - {format_item_name(key)}"
                else:
                    category_name = format_item_name(key)
                extract_items(value, category_name, items)
        elif isinstance(value, list):
            # Handle lists
            for item in value:
                if isinstance(item, dict):
                    extract_items(item, parent_name, items)
    
    return items

def create_checklist_pdf(checklist_data, output_path):
    """Create a PDF checklist from the YAML data."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4a148c'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=24,
        alignment=1  # Center
    )
    
    category_style = ParagraphStyle(
        'Category',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4a148c'),
        spaceBefore=18,
        spaceAfter=12,
        leftIndent=0
    )
    
    item_style = ParagraphStyle(
        'Item',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leftIndent=20
    )
    
    desc_style = ParagraphStyle(
        'Description',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=6,
        leftIndent=40,
        fontName='Helvetica-Oblique'
    )
    
    # Title
    title = checklist_data.get('title', 'Pre-Mystery Setup Checklist')
    story.append(Paragraph(title, title_style))
    
    desc = checklist_data.get('description', '')
    if desc:
        story.append(Paragraph(desc, subtitle_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Extract all items
    all_items = extract_items(checklist_data)
    
    # Group items by category
    categories = {}
    for category, item_name, quantity, description, notes, status in all_items:
        if category not in categories:
            categories[category] = []
        categories[category].append((item_name, quantity, description, notes, status))
    
    # Generate checklist items
    for category in sorted(categories.keys()):
        # Category header
        story.append(Paragraph(f"<b>{category}</b>", category_style))
        
        # Items in this category
        for item_name, quantity, description, notes, status in categories[category]:
            # Checkbox and item name with quantity
            qty_text = f" (Qty: {format_quantity(quantity)})" if quantity else ""
            checkbox = "☐"  # Empty checkbox
            item_text = f"{checkbox} <b>{item_name}</b>{qty_text}"
            
            if notes:
                item_text += f" <i>({notes})</i>"
            
            story.append(Paragraph(item_text, item_style))
            
            # Description
            if description:
                story.append(Paragraph(description, desc_style))
        
        story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Checklist PDF generated: {output_path}")
    print(f"   Total items: {len(all_items)}")
    print(f"   Categories: {len(categories)}")

def main():
    parser = argparse.ArgumentParser(description='Generate PDF checklist from YAML')
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='src/_data/refs/pre_mystery_checklist.yaml',
        help='Input YAML checklist file'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='to_print/pre_mystery_checklist.pdf',
        help='Output PDF file path'
    )
    args = parser.parse_args()
    
    checklist_path = project_root / args.input
    if not checklist_path.exists():
        print(f"Error: Checklist file not found: {checklist_path}", file=sys.stderr)
        return 1
    
    output_path = project_root / args.output
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load checklist
    checklist_data = load_checklist(checklist_path)
    
    # Generate PDF
    create_checklist_pdf(checklist_data, output_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

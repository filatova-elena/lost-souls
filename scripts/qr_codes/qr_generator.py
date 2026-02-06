#!/usr/bin/env python3
"""
QR Code Generator for Murder Mystery Game
Generates individual QR code PNG files from URL and filename
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import json

# Base URL for the hosted game (optional, can be overridden)
BASE_URL = "https://elenafilatova.github.io/murder_mystery"

def create_qr_code(url, filename, output_dir=None, add_text=True):
    """
    Create a QR code for a given URL and save it as an image file.
    
    Args:
        url (str): The URL to encode in the QR code
        filename (str): Name of the output file (without extension)
        output_dir (str or Path): Directory to save QR codes (default: qr_codes/ in project root)
        add_text (bool): Whether to add URL text above QR code
    """
    # Default output directory (relative to project root)
    if output_dir is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        output_dir = project_root / "qr_codes"
    else:
        output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create an image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to RGB if necessary
    if qr_img.mode != 'RGB':
        qr_img = qr_img.convert('RGB')
    
    # Add URL text on top if requested
    if add_text:
        text_height = 40
        new_width = qr_img.width
        new_height = qr_img.height + text_height
        
        img = Image.new('RGB', (new_width, new_height), color='white')
        img.paste(qr_img, (0, text_height))
        
        try:
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), url, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (new_width - text_width) // 2
            draw.text((text_x, 10), url, font=font, fill="black")
        except Exception as e:
            print(f"Warning: Could not add text to QR code: {e}")
    else:
        img = qr_img
    
    # Save the image
    output_path = output_dir / f"{filename}.png"
    img.save(str(output_path))
    print(f"✓ Generated: {filename}.png -> {url}")
    return output_path

def generate_multiple(items, output_dir=None, add_text=True):
    """
    Generate multiple QR codes from a list of URL/filename pairs.
    
    Args:
        items (list): List of dicts with 'url' and 'name' keys, or list of (url, filename) tuples
        output_dir (str or Path): Directory to save QR codes (default: qr_codes/ in project root)
        add_text (bool): Whether to add URL text above QR code
    """
    results = []
    total = len(items)
    
    print(f"📦 Generating {total} QR codes...\n")
    
    for i, item in enumerate(items, 1):
        # Handle both dict and tuple formats
        if isinstance(item, dict):
            url = item.get('url') or item.get('URL')
            filename = item.get('name') or item.get('filename') or item.get('Name')
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            url, filename = item[0], item[1]
        else:
            print(f"⚠️  Skipping invalid item {i}: {item}")
            continue
        
        if not url or not filename:
            print(f"⚠️  Skipping item {i}: missing url or filename")
            continue
        
        try:
            result = create_qr_code(url, filename, output_dir, add_text)
            results.append(result)
        except Exception as e:
            print(f"❌ Error generating QR code {i}/{total} ({filename}): {e}")
    
    print(f"\n✅ Generated {len(results)}/{total} QR codes successfully!")
    return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate QR code PNG file(s) from URL and filename"
    )
    parser.add_argument(
        "--url",
        help="Full URL to encode in the QR code (for single QR code)"
    )
    parser.add_argument(
        "--name",
        help="Output filename (without extension, for single QR code)"
    )
    parser.add_argument(
        "--batch",
        help="JSON file with list of QR codes to generate. Format: [{\"url\": \"...\", \"name\": \"...\"}, ...]"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: qr_codes/ in project root)"
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Don't add URL text above QR code"
    )
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        if args.url or args.name:
            print("⚠️  Warning: --url and --name are ignored when using --batch")
        
        batch_file = Path(args.batch)
        if not batch_file.exists():
            print(f"❌ Error: Batch file not found: {args.batch}")
            return
        
        try:
            with open(batch_file, 'r') as f:
                items = json.load(f)
            
            if not isinstance(items, list):
                print("❌ Error: Batch file must contain a JSON array")
                return
            
            generate_multiple(items, args.output, add_text=not args.no_text)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in batch file: {e}")
            return
        except Exception as e:
            print(f"❌ Error reading batch file: {e}")
            return
    
    # Single QR code mode
    elif args.url and args.name:
        create_qr_code(args.url, args.name, args.output, add_text=not args.no_text)
    else:
        parser.error("Either (--url and --name) or --batch must be provided")

if __name__ == "__main__":
    main()

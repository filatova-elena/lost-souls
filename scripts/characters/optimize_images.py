#!/usr/bin/env python3
"""
Optimize Character Images
Creates web-optimized 300x300 WebP versions of character photos while keeping originals.

Usage:
    python optimize_images.py
    python optimize_images.py --input-dir src/assets/images/characters --output-dir src/assets/images/characters/webp
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def optimize_character_image(input_path, output_path, size=(300, 300), quality=85):
    """
    Convert a character image to optimized WebP format.
    
    Args:
        input_path: Path to source image (PNG, JPG, etc.)
        output_path: Path to save WebP output
        size: Target size as (width, height) tuple
        quality: WebP quality (0-100, default 85)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open and process image
        img = Image.open(input_path)
        
        # Convert RGBA to RGB if needed (WebP supports transparency but we'll use RGB for consistency)
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to target size with high-quality resampling
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        # Save as WebP
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, 'WEBP', quality=quality, method=6)
        
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create web-optimized 300x300 WebP versions of character images"
    )
    parser.add_argument(
        "--input-dir",
        default="src/assets/images/characters",
        help="Directory containing original character images"
    )
    parser.add_argument(
        "--output-dir",
        default="src/assets/images/characters/webp",
        help="Directory to save optimized WebP images"
    )
    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        default=[300, 300],
        metavar=("WIDTH", "HEIGHT"),
        help="Target size (default: 300 300)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="WebP quality 0-100 (default: 85)"
    )
    
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    input_dir = project_root / args.input_dir
    output_dir = project_root / args.output_dir
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
    image_files = [f for f in input_dir.iterdir() 
                   if f.is_file() and f.suffix in image_extensions]
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} image(s) to optimize")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Size: {args.size[0]}x{args.size[1]}")
    print(f"Quality: {args.quality}")
    print()
    
    success_count = 0
    for img_file in sorted(image_files):
        # Create output filename: change extension to .webp
        output_file = output_dir / f"{img_file.stem}.webp"
        
        print(f"Processing {img_file.name}...", end=" ")
        if optimize_character_image(img_file, output_file, tuple(args.size), args.quality):
            # Get file sizes for comparison
            original_size = img_file.stat().st_size
            optimized_size = output_file.stat().st_size
            reduction = (1 - optimized_size / original_size) * 100
            
            print(f"✓ {output_file.name} ({optimized_size:,} bytes, {reduction:.1f}% smaller)")
            success_count += 1
        else:
            print("✗ Failed")
    
    print(f"\n✅ Optimized {success_count}/{len(image_files)} image(s)")


if __name__ == "__main__":
    main()

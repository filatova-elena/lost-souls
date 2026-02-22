#!/usr/bin/env python3
"""
Unified Image Generator using Gemini API
Generates images from prompts and saves to assets directory
Supports single images or batch generation from JSON
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Error: google-generativeai not installed. Run: pip install google-generativeai")

def generate_image(prompt, output_path, model_name='gemini-2.5-flash-image'):
    """Generate a single image using Gemini API"""
    if not HAS_GENAI:
        print("❌ Error: google-generativeai not installed")
        return None
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("❌ Error: GEMINI_API_KEY not set in .env file")
        return None
    
    genai.configure(api_key=api_key)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"🎨 Generating: {output_path.name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt])
        
        if response and response.parts:
            for part in reversed(response.parts):
                if hasattr(part, 'inline_data') and part.inline_data.data:
                    with open(output_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    print(f"✅ Saved: {output_path}")
                    return str(output_path)
        
        print("❌ No image data in response")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generate_batch(batch_file):
    """Generate multiple images from JSON batch file"""
    with open(batch_file, 'r') as f:
        batch = json.load(f)
    
    items = batch.get('items', [])
    output_dir = Path(batch.get('output_dir', 'assets'))
    model_name = batch.get('model', 'gemini-2.5-flash-image')
    
    print(f"📦 Generating {len(items)} images...\n")
    
    results = []
    for item in items:
        prompt = item.get('prompt')
        filename = item.get('filename') or item.get('output')
        if not prompt or not filename:
            print(f"⚠️  Skipping item: missing prompt or filename")
            continue
        
        output_path = output_dir / filename
        result = generate_image(prompt, output_path, model_name)
        if result:
            results.append(result)
    
    print(f"\n✅ Generated {len(results)}/{len(items)} images")
    return results

def main():
    parser = argparse.ArgumentParser(description="Generate images using Gemini API")
    parser.add_argument("--prompt", help="Image generation prompt")
    parser.add_argument("--output", help="Output filename (e.g., assets/image.png)")
    parser.add_argument("--batch", help="JSON file with batch of images to generate")
    parser.add_argument("--model", default="gemini-2.5-flash-image", help="Gemini model name")
    
    args = parser.parse_args()
    
    if args.batch:
        generate_batch(args.batch)
    elif args.prompt and args.output:
        generate_image(args.prompt, args.output, args.model)
    else:
        parser.error("Either --batch or (--prompt and --output) required")

if __name__ == "__main__":
    main()

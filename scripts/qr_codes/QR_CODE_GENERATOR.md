# QR Code Generator - Quick Reference

## Installation
```bash
pip install -r qr_requirements.txt
```

## Generate QR Code PNG(s)

### Single QR Code

#### Basic Usage
```bash
python qr_generator.py --url "https://elenafilatova.github.io/murder_mystery/clue/botanicals/foxglove.html" --name "botanical_foxglove"
```

#### Options
- `--url`: Full URL to encode in QR code (required for single mode)
- `--name`: Output filename without extension (required for single mode)
- `--output`: Output directory (default: `qr_codes/` in project root)
- `--no-text`: Don't add URL text above QR code

#### Examples
```bash
# Generate QR for a botanical clue
python qr_generator.py --url "https://elenafilatova.github.io/murder_mystery/clue/botanicals/foxglove.html" --name "botanical_foxglove"

# Generate QR for a character
python qr_generator.py --url "https://elenafilatova.github.io/murder_mystery/character/professor.html" --name "character_professor"

# Generate QR without URL text
python qr_generator.py --url "https://example.com" --name "my_qr" --no-text
```

### Batch Generation (Multiple QR Codes)

Generate multiple QR codes from a JSON file.

#### JSON File Format
Create a JSON file with an array of objects, each with `url` and `name`:
```json
[
  {
    "url": "https://elenafilatova.github.io/murder_mystery/clue/botanicals/foxglove.html",
    "name": "botanical_foxglove"
  },
  {
    "url": "https://elenafilatova.github.io/murder_mystery/character/professor.html",
    "name": "character_professor"
  }
]
```

#### Usage
```bash
python qr_generator.py --batch qr_list.json
```

#### Options
- `--batch`: Path to JSON file with list of QR codes (required for batch mode)
- `--output`: Output directory (default: `qr_codes/` in project root)
- `--no-text`: Don't add URL text above QR codes

#### Example
```bash
# Generate multiple QR codes from JSON file
python qr_generator.py --batch clues.json --output qr_codes
```

## Generate PDF with QR Codes

### From Existing PNG Files (Directory)
```bash
python qr_pdf_generator.py --source qr_codes --layout grid --output qr_codes_grid.pdf
```

### Grid Layout (Default)
```bash
python qr_pdf_generator.py --source qr_codes --layout grid --cols 3 --rows 4
```

### Vertical Layout
```bash
python qr_pdf_generator.py --source qr_codes --layout vertical
```

### Generate QR Codes On-the-Fly
```bash
python qr_pdf_generator.py --source generate --layout grid --output main_qr_codes.pdf
```

### Options
- `--source`: Directory path with PNG files, or `generate` for predefined sets
- `--layout`: `grid` or `vertical` (default: `grid`)
- `--output`: Output PDF filename (default: `qr_codes.pdf`)
- `--title`: Page title (default: `QR Codes`)
- `--qr-size`: QR code size in inches (default: `2.5`)
- `--cols`: Number of columns for grid (default: `3`)
- `--rows`: Number of rows per page (default: `4`)
- `--base-url`: Base URL for generating QR codes (default: `https://elenafilatova.github.io/murder_mystery`)

## File Naming Convention
- `botanical_{name}.png` - Botanical clues
- `document_{name}.png` - Document clues  
- `character_{name}.png` - Character pages
- `artifact_{name}.png` - Artifact clues
- `journal_{name}.png` - Journal entries
- `vision_{name}.png` - Ghost visions

## Output
- PNG files saved to `qr_codes/` directory (or `--output` path)
- PDF files saved to current directory (or `--output` path)

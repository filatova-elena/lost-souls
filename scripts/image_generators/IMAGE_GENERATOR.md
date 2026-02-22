# Image Generator - Quick Reference

## Installation
```bash
pip install google-generativeai python-dotenv
```

## Single Image
```bash
python image_generator.py --prompt "A 1920s physician in his office" --output assets/doctors_office.png
```

## Batch Generation
```bash
python image_generator.py --batch batch.json
```

## Batch JSON Format
```json
{
  "items": [
    {"prompt": "...", "filename": "image.png"}
  ],
  "output_dir": "assets"
}
```

## Environment
Set `GEMINI_API_KEY` in `.env` file.
